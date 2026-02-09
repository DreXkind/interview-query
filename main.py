"""
FastAPI Backend for Reddit Automation Dashboard
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv

from reddit_scanner import RedditScanner
from comment_generator import CommentGenerator
import local_storage

load_dotenv()

app = FastAPI(title="Reddit Automation API", version="1.0.0")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
scanner = None
generator = None


def get_scanner():
    global scanner
    if scanner is None:
        scanner = RedditScanner()
    return scanner


def get_generator():
    global generator
    if generator is None:
        generator = CommentGenerator()
    return generator


# Pydantic models
class Opportunity(BaseModel):
    id: str
    type: str
    intent: str
    subreddit: str
    title: str
    text_snippet: str
    url: str
    author: str
    score: int
    num_comments: int
    created_utc: str
    matched_keywords: str
    companies_mentioned: str
    recommended_persona: str
    suggested_resource: str
    links_allowed: str
    self_promo_allowed: str
    subreddit_rules: str
    comment_suggestion: str
    status: str = "pending"
    reply_url: Optional[str] = None


class StatusUpdate(BaseModel):
    status: str


class ReplyUpdate(BaseModel):
    reply_url: str


class FeedbackUpdate(BaseModel):
    feedback: str


class TrackedReply(BaseModel):
    opportunity_id: str
    opportunity_url: str
    reply_url: str
    reply_timestamp: str
    initial_score: int
    current_score: int
    subreddit: str
    title: str


@app.get("/")
async def root():
    return {"message": "Reddit Automation API", "status": "running"}


@app.get("/api/opportunities", response_model=List[dict])
async def get_opportunities():
    """Fetch all opportunities from local storage."""
    try:
        opportunities = local_storage.get_all_opportunities()
        return opportunities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/opportunities/{opportunity_id}/status")
async def update_opportunity_status(opportunity_id: str, update: StatusUpdate):
    """Update the status of an opportunity."""
    try:
        local_storage.update_opportunity_status(opportunity_id, update.status)
        return {"success": True, "id": opportunity_id, "status": update.status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/opportunities/{opportunity_id}/reply")
async def save_reply_url(opportunity_id: str, update: ReplyUpdate):
    """Save the reply URL for an opportunity."""
    try:
        local_storage.save_reply_url(opportunity_id, update.reply_url)
        return {"success": True, "id": opportunity_id, "reply_url": update.reply_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/opportunities/{opportunity_id}/feedback")
async def save_feedback(opportunity_id: str, update: FeedbackUpdate):
    """Save feedback for an opportunity and mark as skipped."""
    try:
        local_storage.save_feedback(opportunity_id, update.feedback)
        return {"success": True, "id": opportunity_id, "feedback": update.feedback}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/replies", response_model=List[dict])
async def get_tracked_replies():
    """Get all tracked replies with performance metrics."""
    try:
        scanner = get_scanner()
        replies = local_storage.get_tracked_replies()
        
        # Fetch current scores from Reddit
        for reply in replies:
            if reply.get("reply_url"):
                try:
                    current_score = scanner.get_comment_score(reply["reply_url"])
                    reply["current_score"] = current_score
                except:
                    pass
        
        return replies
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scan")
async def trigger_scan():
    """Trigger a fast Reddit scan - rotates through subreddits."""
    try:
        scanner = get_scanner()
        generator = get_generator()
        
        # Get existing URLs to avoid duplicates
        existing_urls = local_storage.get_existing_urls()
        
        # Get next batch of subreddits to scan (rotates through all)
        import dynamic_config
        all_subreddits = dynamic_config.get_all_subreddits()
        batch_size = dynamic_config.get_subreddits_per_scan()
        posts_per_sub = dynamic_config.get_posts_per_subreddit()
        next_subs = local_storage.get_next_subreddits(all_subreddits, batch_size=batch_size)
        
        results = []
        for sub in next_subs:
            sub_results = scanner.scan_subreddit(sub, limit=posts_per_sub)
            results.extend(sub_results)
        
        # Filter out duplicates
        new_results = [r for r in results if r["url"] not in existing_urls]
        
        # Get scan progress info
        total_subreddits = len(all_subreddits)
        total_batches = (total_subreddits + batch_size - 1) // batch_size  # Ceiling division
        current_batch = local_storage.get_current_batch_number(total_subreddits, batch_size)
        
        if not new_results:
            return {
                "success": True, 
                "new_opportunities": 0, 
                "message": "No new opportunities found",
                "subreddits_scanned": next_subs,
                "scan_progress": f"{current_batch} of {total_batches}",
                "total_subreddits": total_subreddits
            }
        
        # Generate comment suggestions
        for result in new_results:
            suggestion = generator.generate_suggestion(result)
            result["comment_suggestion"] = suggestion
            result["status"] = "pending"
            result["reply_url"] = ""
        
        # Save to local storage
        local_storage.append_opportunities(new_results)
        
        return {
            "success": True,
            "new_opportunities": len(new_results),
            "total_scanned": len(results),
            "duplicates_skipped": len(results) - len(new_results),
            "subreddits_scanned": next_subs,
            "scan_progress": f"{current_batch} of {total_batches}",
            "total_subreddits": total_subreddits
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reset")
async def reset_scan():
    """Reset scan state to start fresh."""
    try:
        local_storage.reset_scan_state()
        # Also reset the scanner's seen_posts
        scanner = get_scanner()
        scanner.seen_posts.clear()
        return {"success": True, "message": "Scan state reset. Next scan will start from batch 1."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """Get dashboard statistics."""
    try:
        opportunities = local_storage.get_all_opportunities()
        
        total = len(opportunities)
        pending = sum(1 for o in opportunities if o.get("status") == "pending")
        in_progress = sum(1 for o in opportunities if o.get("status") == "in_progress")
        replied = sum(1 for o in opportunities if o.get("status") == "replied")
        high_intent = sum(1 for o in opportunities if o.get("intent") == "HIGH")
        
        return {
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "replied": replied,
            "high_intent": high_intent,
            "low_intent": total - high_intent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============== ADMIN ENDPOINTS ==============

class ChatMessage(BaseModel):
    message: str
    conversation_history: Optional[List[dict]] = None


class ApplyChanges(BaseModel):
    changes_text: str


@app.get("/api/admin/skipped")
async def get_skipped_posts():
    """Get all skipped posts with feedback for admin review."""
    try:
        import ai_recommendations
        skipped = ai_recommendations.get_skipped_opportunities()
        return {
            "success": True,
            "skipped_posts": skipped,
            "count": len(skipped)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/recommendations")
async def get_ai_recommendations():
    """Generate AI recommendations based on skipped posts."""
    try:
        import ai_recommendations
        result = ai_recommendations.generate_recommendations()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/chat")
async def chat_with_ai(chat: ChatMessage):
    """Chat with AI about recommendations."""
    try:
        import ai_recommendations
        result = ai_recommendations.chat_with_ai(
            chat.message, 
            chat.conversation_history
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/admin/apply-changes")
async def apply_ai_changes(changes: ApplyChanges):
    """Parse and apply AI-recommended changes to configuration."""
    try:
        import ai_recommendations
        result = ai_recommendations.parse_and_apply_changes(changes.changes_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/config")
async def get_current_config():
    """Get current scanner configuration."""
    try:
        import dynamic_config
        config = dynamic_config.load_config()
        summary = dynamic_config.get_config_summary()
        return {
            "success": True,
            "config": config,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
