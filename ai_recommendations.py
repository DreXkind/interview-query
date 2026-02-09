"""
AI Recommendations Engine
Uses OpenAI to analyze skipped posts and generate configuration recommendations.
"""

import os
import json
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
import dynamic_config
import local_storage

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are an AI assistant helping to optimize a Reddit scanning system for Interview Query, a company that helps people prepare for data science, analytics, and tech interviews.

The system scans Reddit for posts where people are asking about interview preparation, and suggests helpful replies that can mention Interview Query's resources.

Your job is to analyze feedback from skipped posts (posts that were incorrectly flagged as relevant) and recommend configuration changes to improve the system's accuracy.

The system has these configurable elements:
1. **Keywords** - phrases that trigger a post to be considered (e.g., "interview prep", "coding interview")
2. **Relevant Signals** - phrases that indicate a post IS relevant to Interview Query (e.g., "preparing", "tips", "practice")
3. **Irrelevant Signals** - phrases that indicate a post is NOT relevant (e.g., "resume review", "salary negotiation")
4. **Subreddits** - which subreddits to scan, organized by persona

Interview Query's services focus on:
- Interview preparation for data science, analytics, ML, and tech roles
- Practice questions (SQL, Python, statistics, probability, machine learning)
- Mock interviews and interview guides
- Company-specific interview prep

Posts that are NOT relevant include:
- Job application frustrations (resume help, cover letters, ghosting)
- Salary negotiation or offer discussions
- General career advice not about interviews
- Technical help that's not interview-related
- Market research, focus groups, scams

When analyzing skipped posts, identify patterns and suggest specific changes."""


def get_skipped_opportunities() -> List[Dict[str, Any]]:
    """Get all opportunities that were skipped with feedback."""
    opportunities = local_storage.get_all_opportunities()
    return [opp for opp in opportunities if opp.get("status") == "skipped" and opp.get("feedback")]


def generate_recommendations(conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Generate AI recommendations based on skipped posts.
    Can continue a conversation if history is provided.
    """
    skipped = get_skipped_opportunities()
    config_summary = dynamic_config.get_config_summary()
    
    if not skipped:
        return {
            "success": True,
            "message": "No skipped posts with feedback to analyze yet.",
            "recommendations": [],
            "conversation_id": None
        }
    
    # Build context about skipped posts
    skipped_context = []
    for opp in skipped[:20]:  # Limit to 20 most recent
        skipped_context.append({
            "subreddit": opp.get("subreddit"),
            "title": opp.get("title"),
            "text_snippet": opp.get("text_snippet", "")[:200],
            "matched_keywords": opp.get("matched_keywords"),
            "feedback": opp.get("feedback")
        })
    
    # Build the user message
    user_message = f"""Please analyze these skipped posts and their feedback to recommend configuration changes.

## Current Configuration Summary
- Total keywords: {config_summary['total_keywords']}
- Total subreddits: {config_summary['total_subreddits']}
- Total relevant signals: {config_summary['total_relevant_signals']}
- Total irrelevant signals: {config_summary['total_irrelevant_signals']}

## Skipped Posts with Feedback
{json.dumps(skipped_context, indent=2)}

Based on this feedback, what specific changes would you recommend? Please provide:
1. Keywords to add or remove
2. Irrelevant signals to add
3. Subreddits to remove (if any consistently produce irrelevant results)
4. Any other pattern you notice

Format your recommendations as actionable items that can be approved and applied."""

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add conversation history if continuing
    if conversation_history:
        messages.extend(conversation_history)
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=2000
        )
        
        ai_response = response.choices[0].message.content
        
        return {
            "success": True,
            "recommendations": ai_response,
            "skipped_count": len(skipped),
            "analyzed_count": len(skipped_context)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "recommendations": None
        }


def chat_with_ai(user_message: str, conversation_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Continue a conversation with the AI about recommendations.
    """
    config_summary = dynamic_config.get_config_summary()
    current_config = dynamic_config.load_config()
    
    # Build context message
    context = f"""Current configuration:
- Keywords ({config_summary['total_keywords']}): {', '.join(current_config['keywords'][:10])}... 
- Subreddits ({config_summary['total_subreddits']}): {', '.join(dynamic_config.get_all_subreddits()[:10])}...
- Irrelevant signals: {', '.join(current_config['irrelevant_signals'][:10])}..."""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + f"\n\n{context}"}
    ]
    
    if conversation_history:
        messages.extend(conversation_history)
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=1500
        )
        
        ai_response = response.choices[0].message.content
        
        return {
            "success": True,
            "response": ai_response
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def parse_and_apply_changes(changes_text: str) -> Dict[str, Any]:
    """
    Parse AI-suggested changes and apply them to the configuration.
    Expected format from AI includes structured recommendations.
    """
    applied_changes = []
    
    # Use AI to parse the changes into structured format
    parse_prompt = f"""Parse the following recommendations into a JSON structure with these arrays:
- "add_keywords": list of keywords to add
- "remove_keywords": list of keywords to remove  
- "add_irrelevant_signals": list of irrelevant signals to add
- "remove_subreddits": list of subreddits to remove

Only include items that are explicitly recommended. Return valid JSON only, no explanation.

Recommendations:
{changes_text}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": parse_prompt}],
            temperature=0,
            max_tokens=1000
        )
        
        # Parse the JSON response
        json_str = response.choices[0].message.content
        # Clean up potential markdown formatting
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]
        
        changes = json.loads(json_str.strip())
        
        # Apply the changes
        for keyword in changes.get("add_keywords", []):
            if dynamic_config.add_keyword(keyword):
                applied_changes.append(f"Added keyword: {keyword}")
        
        for keyword in changes.get("remove_keywords", []):
            if dynamic_config.remove_keyword(keyword):
                applied_changes.append(f"Removed keyword: {keyword}")
        
        for signal in changes.get("add_irrelevant_signals", []):
            if dynamic_config.add_irrelevant_signal(signal):
                applied_changes.append(f"Added irrelevant signal: {signal}")
        
        for subreddit in changes.get("remove_subreddits", []):
            if dynamic_config.remove_subreddit(subreddit):
                applied_changes.append(f"Removed subreddit: {subreddit}")
        
        return {
            "success": True,
            "applied_changes": applied_changes,
            "parsed_changes": changes
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Failed to parse AI response as JSON: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
