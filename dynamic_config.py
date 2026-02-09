"""
Dynamic Configuration Manager
Loads and saves scanner configuration from JSON file for runtime updates.
"""

import json
import os
from typing import Dict, List, Any

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "scanner_config.json")


def load_config() -> Dict[str, Any]:
    """Load configuration from JSON file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return get_default_config()


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to JSON file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_default_config() -> Dict[str, Any]:
    """Return default configuration if file doesn't exist."""
    return {
        "keywords": ["interview"],
        "relevant_signals": [],
        "irrelevant_signals": [],
        "subreddits": {},
        "companies": [],
        "resources": {},
        "max_post_age_hours": 48,
        "posts_per_subreddit": 25,
        "subreddits_per_scan": 3
    }


def get_keywords() -> List[str]:
    """Get list of keywords to search for."""
    return load_config().get("keywords", [])


def get_relevant_signals() -> List[str]:
    """Get list of relevant signals for filtering."""
    return load_config().get("relevant_signals", [])


def get_irrelevant_signals() -> List[str]:
    """Get list of irrelevant signals for filtering."""
    return load_config().get("irrelevant_signals", [])


def get_subreddits() -> Dict[str, List[str]]:
    """Get subreddits organized by persona."""
    return load_config().get("subreddits", {})


def get_all_subreddits() -> List[str]:
    """Get flattened list of all unique subreddits."""
    subreddits = get_subreddits()
    return list(set(sub for subs in subreddits.values() for sub in subs))


def get_companies() -> List[str]:
    """Get list of company names."""
    return load_config().get("companies", [])


def get_resources() -> Dict[str, str]:
    """Get Interview Query resources mapping."""
    return load_config().get("resources", {})


def get_max_post_age_hours() -> int:
    """Get maximum post age in hours."""
    return load_config().get("max_post_age_hours", 48)


def get_posts_per_subreddit() -> int:
    """Get number of posts to fetch per subreddit."""
    return load_config().get("posts_per_subreddit", 25)


def get_subreddits_per_scan() -> int:
    """Get number of subreddits to scan per batch."""
    return load_config().get("subreddits_per_scan", 3)


# Config update functions for AI recommendations

def add_keyword(keyword: str) -> bool:
    """Add a new keyword to the list."""
    config = load_config()
    if keyword.lower() not in [k.lower() for k in config["keywords"]]:
        config["keywords"].append(keyword)
        save_config(config)
        return True
    return False


def remove_keyword(keyword: str) -> bool:
    """Remove a keyword from the list."""
    config = load_config()
    keywords_lower = [k.lower() for k in config["keywords"]]
    if keyword.lower() in keywords_lower:
        idx = keywords_lower.index(keyword.lower())
        config["keywords"].pop(idx)
        save_config(config)
        return True
    return False


def add_subreddit(subreddit: str, persona: str = "warmeggnog") -> bool:
    """Add a new subreddit to a persona's list."""
    config = load_config()
    if persona not in config["subreddits"]:
        config["subreddits"][persona] = []
    if subreddit not in config["subreddits"][persona]:
        config["subreddits"][persona].append(subreddit)
        save_config(config)
        return True
    return False


def remove_subreddit(subreddit: str) -> bool:
    """Remove a subreddit from all personas."""
    config = load_config()
    removed = False
    for persona in config["subreddits"]:
        if subreddit in config["subreddits"][persona]:
            config["subreddits"][persona].remove(subreddit)
            removed = True
    if removed:
        save_config(config)
    return removed


def add_irrelevant_signal(signal: str) -> bool:
    """Add a new irrelevant signal."""
    config = load_config()
    if signal.lower() not in [s.lower() for s in config["irrelevant_signals"]]:
        config["irrelevant_signals"].append(signal)
        save_config(config)
        return True
    return False


def add_relevant_signal(signal: str) -> bool:
    """Add a new relevant signal."""
    config = load_config()
    if signal.lower() not in [s.lower() for s in config["relevant_signals"]]:
        config["relevant_signals"].append(signal)
        save_config(config)
        return True
    return False


def get_config_summary() -> Dict[str, Any]:
    """Get a summary of current configuration for AI context."""
    config = load_config()
    all_subs = get_all_subreddits()
    return {
        "total_keywords": len(config.get("keywords", [])),
        "total_subreddits": len(all_subs),
        "total_relevant_signals": len(config.get("relevant_signals", [])),
        "total_irrelevant_signals": len(config.get("irrelevant_signals", [])),
        "personas": list(config.get("subreddits", {}).keys()),
        "max_post_age_hours": config.get("max_post_age_hours", 48),
        "posts_per_subreddit": config.get("posts_per_subreddit", 25)
    }
