"""
Local JSON storage for opportunities - avoids Google Sheets rate limits
"""

import json
import os
from datetime import datetime
import hashlib

DATA_FILE = os.path.join(os.path.dirname(__file__), "opportunities.json")
SCAN_STATE_FILE = os.path.join(os.path.dirname(__file__), "scan_state.json")


def _load_data():
    """Load data from JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"opportunities": []}


def _save_data(data):
    """Save data to JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def generate_id(url: str) -> str:
    """Generate unique ID from URL."""
    return hashlib.md5(url.encode()).hexdigest()[:12]


def get_all_opportunities():
    """Get all opportunities."""
    data = _load_data()
    return data.get("opportunities", [])


def get_existing_urls():
    """Get set of existing URLs to avoid duplicates."""
    opportunities = get_all_opportunities()
    return {o.get("url") for o in opportunities}


def append_opportunities(new_opportunities: list):
    """Add new opportunities."""
    data = _load_data()
    
    for opp in new_opportunities:
        opp["id"] = generate_id(opp["url"])
        opp["scan_time"] = datetime.now().isoformat()
        if "status" not in opp:
            opp["status"] = "pending"
        if "reply_url" not in opp:
            opp["reply_url"] = ""
        data["opportunities"].append(opp)
    
    _save_data(data)


def update_opportunity_status(opportunity_id: str, status: str):
    """Update status of an opportunity."""
    data = _load_data()
    
    for opp in data["opportunities"]:
        if opp.get("id") == opportunity_id:
            opp["status"] = status
            break
    
    _save_data(data)


def save_reply_url(opportunity_id: str, reply_url: str):
    """Save reply URL and mark as replied."""
    data = _load_data()
    
    for opp in data["opportunities"]:
        if opp.get("id") == opportunity_id:
            opp["reply_url"] = reply_url
            opp["status"] = "replied"
            opp["reply_timestamp"] = datetime.now().isoformat()
            break
    
    _save_data(data)


def get_tracked_replies():
    """Get opportunities that have been replied to."""
    opportunities = get_all_opportunities()
    return [o for o in opportunities if o.get("reply_url")]


def save_feedback(opportunity_id: str, feedback: str):
    """Save feedback for an opportunity."""
    data = _load_data()
    
    for opp in data["opportunities"]:
        if opp.get("id") == opportunity_id:
            opp["feedback"] = feedback
            opp["status"] = "skipped"
            break
    
    _save_data(data)


def _load_scan_state():
    """Load scan state from JSON file."""
    if os.path.exists(SCAN_STATE_FILE):
        with open(SCAN_STATE_FILE, "r") as f:
            return json.load(f)
    return {"next_index": 0, "scanned_subreddits": []}


def reset_scan_state():
    """Reset scan state to start fresh."""
    state = {"next_index": 0, "scanned_subreddits": []}
    _save_scan_state(state)
    return state


def _save_scan_state(state):
    """Save scan state to JSON file."""
    with open(SCAN_STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_current_batch_number(total_subreddits: int, batch_size: int = 3) -> int:
    """Get the current batch number (1-indexed) based on scan state."""
    state = _load_scan_state()
    next_index = state.get("next_index", 0)
    
    # Calculate which batch we just completed
    if next_index == 0:
        # We just wrapped around, so we completed the last batch
        total_batches = (total_subreddits + batch_size - 1) // batch_size
        return total_batches
    else:
        # Current batch is based on next_index
        return (next_index + batch_size - 1) // batch_size


def get_next_subreddits(all_subreddits: list, batch_size: int = 3) -> list:
    """Get next batch of subreddits to scan, rotating through the list."""
    state = _load_scan_state()
    next_index = state.get("next_index", 0)
    
    # Get next batch
    total = len(all_subreddits)
    if next_index >= total:
        next_index = 0
    
    end_index = min(next_index + batch_size, total)
    batch = all_subreddits[next_index:end_index]
    
    # If we need more to fill the batch, wrap around
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
