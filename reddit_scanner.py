"""
Reddit Scanner for Interview Query
Scans designated subreddits for posts and comments matching interview-related keywords.
"""

import os
import re
import praw
from datetime import datetime, timezone
from dotenv import load_dotenv
import dynamic_config

load_dotenv()


class RedditScanner:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            username=os.getenv("REDDIT_USERNAME"),
            password=os.getenv("REDDIT_PASSWORD"),
            user_agent="InterviewQueryScanner/1.0 by u/DreXkind"
        )
        self.subreddit_rules_cache = {}
        self.last_scan_timestamp = None
        self.seen_posts = set()  # Track post IDs to avoid duplicates
    
    def get_subreddit_rules(self, subreddit_name: str) -> dict:
        """Fetch and cache subreddit rules to check if linking is allowed."""
        if subreddit_name in self.subreddit_rules_cache:
            return self.subreddit_rules_cache[subreddit_name]
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            rules = []
            links_allowed = True
            self_promo_allowed = True
            
            for rule in subreddit.rules:
                rule_text = f"{rule.short_name}: {rule.description}"
                rules.append(rule_text)
                
                rule_lower = rule_text.lower()
                if any(term in rule_lower for term in ["no link", "no url", "no self-promotion", "no spam", "no advertising"]):
                    if "link" in rule_lower or "url" in rule_lower:
                        links_allowed = False
                    if "self-promotion" in rule_lower or "advertising" in rule_lower:
                        self_promo_allowed = False
            
            result = {
                "rules_summary": rules[:5],  # First 5 rules
                "links_allowed": links_allowed,
                "self_promo_allowed": self_promo_allowed,
            }
            self.subreddit_rules_cache[subreddit_name] = result
            return result
        except Exception as e:
            return {
                "rules_summary": [f"Could not fetch rules: {str(e)}"],
                "links_allowed": True,  # Assume allowed if can't fetch
                "self_promo_allowed": True,
            }
    
    def matches_keywords(self, text: str) -> list:
        """Check if text matches any keywords. Returns list of matched keywords."""
        if not text:
            return []
        
        text_lower = text.lower()
        matched = []
        keywords = dynamic_config.get_keywords()
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matched.append(keyword)
        
        return matched
    
    def is_relevant_to_interview_query(self, text: str) -> bool:
        """
        Check if post is relevant to Interview Query's services.
        Used when 'interview' is matched broadly to filter out irrelevant posts.
        Returns True if post is about interview prep/process, False otherwise.
        
        Interview Query helps with: interview preparation, practice questions,
        what to expect in interviews, coding/technical/behavioral interview prep.
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Strong disqualifiers - if present, definitely not relevant
        strong_disqualifiers = [
            "focus group", "market research", "paid study", "cat food", "dog food",
            "scam", "legitimacy", "fake job", "pyramid scheme",
            "resume review", "cover letter", "job application form",
            "salary negotiation", "offer letter", "signing bonus", "counter offer",
            "quit my job", "toxic boss", "work life balance", "layoff", "fired",
        ]
        for disqualifier in strong_disqualifiers:
            if disqualifier in text_lower:
                return False
        
        # Strong qualifiers - if present, definitely relevant
        strong_qualifiers = [
            "interview prep", "preparing for interview", "interview tips",
            "coding interview", "technical interview", "behavioral interview",
            "system design interview", "case study interview",
            "how to prepare", "practice questions", "mock interview",
            "interview coming up", "have an interview", "got an interview",
            "interview next week", "interview tomorrow", "upcoming interview",
            "what to expect in interview", "interview process at",
            "data science interview", "data analyst interview", "sql interview",
            "python interview", "machine learning interview",
            "leetcode", "hackerrank", "codesignal", "online assessment",
        ]
        for qualifier in strong_qualifiers:
            if qualifier in text_lower:
                return True
        
        # Check for relevant signals (need at least 2 for weaker matches)
        relevant_signals = dynamic_config.get_relevant_signals()
        relevant_count = sum(1 for signal in relevant_signals if signal in text_lower)
        
        # Must have at least 2 relevant signals for posts that only matched "interview"
        return relevant_count >= 2
    
    def detect_companies(self, text: str) -> list:
        """Detect company names mentioned in text."""
        if not text:
            return []
        
        text_lower = text.lower()
        companies = dynamic_config.get_companies()
        return [company for company in companies if company in text_lower]
    
    def get_intent_level(self, text: str, matched_keywords: list) -> str:
        """Determine if post/comment is HIGH or LOW intent."""
        text_lower = text.lower() if text else ""
        
        high_intent_signals = [
            "interview questions",
            "interview process",
            "interview prep",
            "preparing for interview",
            "got an interview",
            "have an interview",
            "interview coming up",
            "technical interview",
            "coding interview",
            "failed interview",
            "flunked interview",
        ]
        
        for signal in high_intent_signals:
            if signal in text_lower:
                return "HIGH"
        
        if any("interview" in kw.lower() for kw in matched_keywords):
            return "HIGH"
        
        return "LOW"
    
    def get_recommended_persona(self, subreddit_name: str) -> str:
        """Get recommended persona based on subreddit."""
        subreddits = dynamic_config.get_subreddits()
        for persona, subs in subreddits.items():
            if subreddit_name.lower() in [s.lower() for s in subs]:
                return persona
        return "warmeggnog"  # Default
    
    def get_suggested_resource(self, text: str, matched_keywords: list) -> str:
        """Suggest an Interview Query resource based on content."""
        text_lower = text.lower() if text else ""
        keywords_lower = " ".join(matched_keywords).lower()
        combined = text_lower + " " + keywords_lower
        resources = dynamic_config.get_resources()
        
        for topic, url in resources.items():
            if topic in combined:
                return url
        
        # Default to company guides if company mentioned
        if self.detect_companies(text):
            return resources.get("company guides", "")
        
        return ""
    
    def scan_subreddit(self, subreddit_name: str, limit: int = 50) -> list:
        """Scan a subreddit for matching posts and comments."""
        results = []
        
        # Max age for posts from config
        max_age_hours = dynamic_config.get_max_post_age_hours()
        cutoff_timestamp = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
        
        try:
            subreddit = self.reddit.subreddit(subreddit_name)
            rules = self.get_subreddit_rules(subreddit_name)
            
            # Get persona for this subreddit once
            persona = self.get_recommended_persona(subreddit_name)
            
            # Scan new posts (limit controls how many to fetch)
            for post in subreddit.new(limit=limit):
                # Skip posts older than 48 hours
                if post.created_utc < cutoff_timestamp:
                    continue
                    
                # Skip if we've already processed this post (for incremental scans)
                if self.last_scan_timestamp and post.created_utc <= self.last_scan_timestamp:
                    continue
                if post.id in self.seen_posts:
                    continue
                    
                self.seen_posts.add(post.id)
                post_text = f"{post.title} {post.selftext}"
                matched_keywords = self.matches_keywords(post_text)
                
                if matched_keywords:
                    # If only "interview" matched, check relevance to Interview Query
                    if matched_keywords == ["interview"] and not self.is_relevant_to_interview_query(post_text):
                        continue  # Skip irrelevant posts that only matched "interview"
                    
                    companies = self.detect_companies(post_text)
                    intent = self.get_intent_level(post_text, matched_keywords)
                    resource = self.get_suggested_resource(post_text, matched_keywords)
                    
                    results.append({
                        "type": "post",
                        "subreddit": subreddit_name,
                        "title": post.title[:200],
                        "text_snippet": post.selftext[:300] if post.selftext else "",
                        "url": f"https://reddit.com{post.permalink}",
                        "author": str(post.author) if post.author else "[deleted]",
                        "score": post.score,
                        "num_comments": post.num_comments,
                        "created_utc": datetime.fromtimestamp(post.created_utc, tz=timezone.utc).isoformat(),
                        "matched_keywords": ", ".join(matched_keywords[:5]),
                        "companies_mentioned": ", ".join(companies),
                        "intent": intent,
                        "recommended_persona": persona,
                        "suggested_resource": resource,
                        "links_allowed": "Yes" if rules["links_allowed"] else "No",
                        "self_promo_allowed": "Yes" if rules["self_promo_allowed"] else "Caution",
                        "subreddit_rules": " | ".join(rules["rules_summary"][:3]),
                    })
                
                # DISABLED: Comment scanning removed - comments without post context are often irrelevant
                # Based on user feedback: comments matched keywords but parent post wasn't about interview prep
                # Only scan posts now for better relevance
        
        except Exception as e:
            print(f"Error scanning r/{subreddit_name}: {str(e)}")
        
        return results
    
    def scan_all_subreddits(self, limit_per_sub: int = None, initial_scan: bool = True) -> list:
        """Scan all configured subreddits."""
        all_results = []
        all_subreddits = dynamic_config.get_all_subreddits()
        
        for subreddit_name in all_subreddits:
            print(f"Scanning r/{subreddit_name}...")
            results = self.scan_subreddit(subreddit_name, limit=limit_per_sub)
            all_results.extend(results)
            print(f"  Found {len(results)} matches")
        
        # Sort by intent (HIGH first) then by score
        all_results.sort(key=lambda x: (x["intent"] != "HIGH", -x["score"]))
        
        # Update timestamp after successful scan (for incremental scans)
        if all_results:
            from datetime import datetime, timezone
            self.last_scan_timestamp = datetime.now(timezone.utc).timestamp()
        
        return all_results
    
    def get_comment_score(self, comment_url: str) -> int:
        """Get the current score of a comment by URL."""
        try:
            # Extract comment ID from URL
            # URL format: https://reddit.com/r/subreddit/comments/post_id/title/comment_id
            parts = comment_url.rstrip('/').split('/')
            comment_id = parts[-1] if parts else None
            
            if comment_id:
                comment = self.reddit.comment(id=comment_id)
                return comment.score
        except Exception as e:
            print(f"Error fetching comment score: {e}")
        
        return 0


if __name__ == "__main__":
    scanner = RedditScanner()
    results = scanner.scan_all_subreddits(limit_per_sub=10)
    print(f"\nTotal matches found: {len(results)}")
    for r in results[:5]:
        print(f"  [{r['intent']}] r/{r['subreddit']}: {r['title'][:50]}...")
