"""
Supabase storage for opportunities - persistent cloud database
Replaces local_storage.py for production deployment
"""

import os
import hashlib
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

_supabase_client: Client = None


def get_client() -> Client:
    """Get or create Supabase client."""
    global _supabase_client
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client


def generate_id(url: str) -> str:
    """Generate unique ID from URL."""
    return hashlib.md5(url.encode()).hexdigest()[:12]


def get_all_opportunities():
    """Get all opportunities from Supabase."""
    client = get_client()
    response = client.table("opportunities").select("*").order("created_at", desc=True).execute()
    return response.data or []


def get_existing_urls():
    """Get set of existing URLs to avoid duplicates."""
    client = get_client()
    response = client.table("opportunities").select("url").execute()
    return {item["url"] for item in (response.data or [])}


def append_opportunities(new_opportunities: list):
    """Add new opportunities to Supabase."""
    client = get_client()
    
    for opp in new_opportunities:
        opp["id"] = generate_id(opp["url"])
        opp["scan_time"] = datetime.now().isoformat()
        if "status" not in opp:
            opp["status"] = "pending"
        if "reply_url" not in opp:
            opp["reply_url"] = ""
    
    if new_opportunities:
        client.table("opportunities").upsert(new_opportunities, on_conflict="id").execute()


def update_opportunity_status(opportunity_id: str, status: str):
    """Update status of an opportunity."""
    client = get_client()
    client.table("opportunities").update({"status": status}).eq("id", opportunity_id).execute()


def save_reply_url(opportunity_id: str, reply_url: str):
    """Save reply URL and mark as replied."""
    client = get_client()
    client.table("opportunities").update({
        "reply_url": reply_url,
        "status": "replied",
        "reply_timestamp": datetime.now().isoformat()
    }).eq("id", opportunity_id).execute()


def get_tracked_replies():
    """Get opportunities that have been replied to."""
    client = get_client()
    response = client.table("opportunities").select("*").neq("reply_url", "").execute()
    return response.data or []


def save_feedback(opportunity_id: str, feedback: str):
    """Save feedback for an opportunity and mark as skipped."""
    client = get_client()
    client.table("opportunities").update({
        "feedback": feedback,
        "status": "skipped"
    }).eq("id", opportunity_id).execute()


def _load_scan_state():
    """Load scan state from Supabase."""
    client = get_client()
    response = client.table("scan_state").select("*").eq("id", 1).execute()
    if response.data:
        return response.data[0]
    return {"id": 1, "next_index": 0, "last_batch": None}


def _save_scan_state(state):
    """Save scan state to Supabase."""
    client = get_client()
    client.table("scan_state").upsert(state, on_conflict="id").execute()


def reset_scan_state():
    """Reset scan state to start fresh."""
    state = {"id": 1, "next_index": 0, "last_batch": None}
    _save_scan_state(state)
    return state


def get_current_batch_number(total_subreddits: int, batch_size: int = 3) -> int:
    """Get the current batch number (1-indexed) based on scan state."""
    state = _load_scan_state()
    next_index = state.get("next_index", 0)
    
    if next_index == 0:
        total_batches = (total_subreddits + batch_size - 1) // batch_size
        return total_batches
    else:
        return (next_index + batch_size - 1) // batch_size


def get_next_subreddits(all_subreddits: list, batch_size: int = 3) -> list:
    """Get next batch of subreddits to scan, rotating through the list."""
    state = _load_scan_state()
    next_index = state.get("next_index", 0)
    
    total = len(all_subreddits)
    if next_index >= total:
        next_index = 0
    
    end_index = min(next_index + batch_size, total)
    batch = all_subreddits[next_index:end_index]
    
    if len(batch) < batch_size and next_index > 0:
        remaining = batch_size - len(batch)
        batch.extend(all_subreddits[:remaining])
        state["next_index"] = remaining
    else:
        state["next_index"] = end_index if end_index < total else 0
    
    state["last_scan"] = datetime.now().isoformat()
    state["last_batch"] = batch
    _save_scan_state(state)
    
    return batch


# ============== Comment Metrics Functions ==============

def save_comment_metric(opportunity_id: str, reply_url: str, subreddit: str, persona: str, initial_score: int):
    """Save initial metrics when a reply URL is saved."""
    client = get_client()
    client.table("comment_metrics").upsert({
        "opportunity_id": opportunity_id,
        "reply_url": reply_url,
        "subreddit": subreddit,
        "persona": persona,
        "initial_score": initial_score,
        "current_score": initial_score,
        "last_updated": datetime.now().isoformat()
    }, on_conflict="opportunity_id").execute()


def update_comment_score(opportunity_id: str, current_score: int):
    """Update the current score for a tracked comment."""
    client = get_client()
    client.table("comment_metrics").update({
        "current_score": current_score,
        "last_updated": datetime.now().isoformat()
    }).eq("opportunity_id", opportunity_id).execute()


def get_all_comment_metrics():
    """Get all comment metrics for analytics."""
    client = get_client()
    response = client.table("comment_metrics").select("*").order("created_at", desc=True).execute()
    return response.data or []


def get_analytics_summary():
    """Get aggregated analytics data."""
    metrics = get_all_comment_metrics()
    
    if not metrics:
        return {
            "total_replies": 0,
            "total_upvotes": 0,
            "avg_upvotes": 0,
            "best_subreddits": [],
            "best_personas": []
        }
    
    total_replies = len(metrics)
    total_upvotes = sum(m.get("current_score", 0) for m in metrics)
    avg_upvotes = total_upvotes / total_replies if total_replies > 0 else 0
    
    # Group by subreddit
    subreddit_stats = {}
    for m in metrics:
        sub = m.get("subreddit", "unknown")
        if sub not in subreddit_stats:
            subreddit_stats[sub] = {"count": 0, "total_score": 0}
        subreddit_stats[sub]["count"] += 1
        subreddit_stats[sub]["total_score"] += m.get("current_score", 0)
    
    best_subreddits = [
        {"subreddit": k, "replies": v["count"], "avg_score": round(v["total_score"] / v["count"], 1)}
        for k, v in subreddit_stats.items()
    ]
    best_subreddits.sort(key=lambda x: x["avg_score"], reverse=True)
    
    # Group by persona
    persona_stats = {}
    for m in metrics:
        persona = m.get("persona", "unknown")
        if persona not in persona_stats:
            persona_stats[persona] = {"count": 0, "total_score": 0}
        persona_stats[persona]["count"] += 1
        persona_stats[persona]["total_score"] += m.get("current_score", 0)
    
    best_personas = [
        {"persona": k, "replies": v["count"], "avg_score": round(v["total_score"] / v["count"], 1)}
        for k, v in persona_stats.items()
    ]
    best_personas.sort(key=lambda x: x["avg_score"], reverse=True)
    
    return {
        "total_replies": total_replies,
        "total_upvotes": total_upvotes,
        "avg_upvotes": round(avg_upvotes, 1),
        "best_subreddits": best_subreddits[:10],
        "best_personas": best_personas[:10]
    }
