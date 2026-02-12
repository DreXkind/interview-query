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
