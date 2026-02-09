"""
Comment Suggestion Generator for Interview Query
Generates comment suggestions based on the warmeggnog persona style.
"""

import re
from config import IQ_RESOURCES, COMPANIES


class CommentGenerator:
    """Generate comment suggestions in the warmeggnog persona style."""
    
    def __init__(self):
        self.persona_style = {
            "tone": "warm, helpful, peer-like",
            "case": "lowercase casual",
            "phrases": [
                "what helped me was",
                "in my experience",
                "when i was prepping",
                "i found it super helpful to",
                "imo",
                "ngl",
                "good luck!",
            ]
        }
    
    def generate_suggestion(self, post_data: dict) -> str:
        """Generate a comment suggestion based on post data."""
        intent = post_data.get("intent", "LOW")
        text_snippet = post_data.get("text_snippet", "")
        title = post_data.get("title", "")
        companies = post_data.get("companies_mentioned", "")
        keywords = post_data.get("matched_keywords", "")
        suggested_resource = post_data.get("suggested_resource", "")
        links_allowed = post_data.get("links_allowed", "Yes") == "Yes"
        post_type = post_data.get("type", "post")
        
        combined_text = f"{title} {text_snippet}".lower()
        
        # Determine the topic focus
        topic = self._detect_topic(combined_text, keywords)
        
        # Build the comment suggestion
        if intent == "HIGH":
            suggestion = self._generate_high_intent_comment(
                topic, companies, suggested_resource, links_allowed, combined_text
            )
        else:
            suggestion = self._generate_low_intent_comment(
                topic, combined_text
            )
        
        return suggestion
    
    def _detect_topic(self, text: str, keywords: str) -> str:
        """Detect the main topic from text and keywords."""
        combined = f"{text} {keywords}".lower()
        
        if "sql" in combined:
            return "sql"
        elif "python" in combined:
            return "python"
        elif "machine learning" in combined or "ml " in combined:
            return "machine learning"
        elif "data scientist" in combined or "data science" in combined:
            return "data science"
        elif "data analyst" in combined or "data analysis" in combined:
            return "data analyst"
        elif "data engineer" in combined:
            return "data engineer"
        elif "probability" in combined or "statistics" in combined:
            return "probability"
        elif "leetcode" in combined or "coding" in combined:
            return "coding"
        elif "behavioral" in combined:
            return "behavioral"
        elif "resume" in combined or "job search" in combined:
            return "job search"
        elif any(company in combined for company in COMPANIES):
            return "company interview"
        else:
            return "general interview"
    
    def _generate_high_intent_comment(
        self, topic: str, companies: str, resource: str, links_allowed: bool, text: str
    ) -> str:
        """Generate comment for high-intent posts (interview prep, questions, etc.)."""
        
        # Opening - acknowledge their situation
        openings = {
            "sql": "sql interviews can definitely be tricky, especially when they throw real-world scenarios at you.",
            "python": "python interviews often go beyond just syntax - they want to see how you think through problems.",
            "machine learning": "ml interviews can be intense since they often mix theory with practical implementation.",
            "data science": "data science interviews usually cover a lot of ground - stats, coding, and business sense.",
            "data analyst": "data analyst interviews tend to focus heavily on sql and how you communicate insights.",
            "data engineer": "data engineering interviews often dive deep into system design and data pipelines.",
            "probability": "probability questions can be tough since they require you to think on your feet.",
            "coding": "getting back into coding prep can feel overwhelming at first, but it comes back quickly.",
            "behavioral": "behavioral rounds are often underestimated but they can make or break an offer.",
            "company interview": "company-specific prep is super important since each has their own style.",
            "job search": "the job search grind is real, but small optimizations can make a big difference.",
            "general interview": "interview prep can feel overwhelming, but breaking it down helps a lot.",
        }
        
        opening = openings.get(topic, openings["general interview"])
        
        # Middle - share personal experience/advice
        middles = {
            "sql": "when i was prepping for data analyst roles, i focused on practicing questions that mimicked real business scenarios rather than just syntax drills. things like window functions, ctes, and joins with edge cases came up a lot.",
            "python": "what helped me was practicing problems that required me to explain my thought process out loud, not just get the right answer. interviewers care about how you approach problems.",
            "machine learning": "in my experience, they care less about memorizing algorithms and more about understanding trade-offs and when to use what. being able to explain model choices simply was key.",
            "data science": "i found it super helpful to practice explaining technical concepts in simple terms - that's often what separates candidates in the final rounds.",
            "data analyst": "what worked for me was practicing sql with actual datasets and framing my answers around business impact, not just technical correctness.",
            "data engineer": "when i interviewed for similar roles, system design and understanding data flow end-to-end was heavily tested. knowing your tools deeply helps.",
            "probability": "imo the best way to prep for probability questions is to practice thinking through them step by step rather than memorizing formulas.",
            "coding": "when i got back into leetcode after a break, i found it helpful to focus on patterns (sliding window, two pointers, etc.) rather than grinding random problems.",
            "behavioral": "what helped me was preparing specific stories using the star method and practicing them until they felt natural, not rehearsed.",
            "company interview": "i made sure to read through interview experiences and company-specific guides before my interviews - knowing what to expect made a huge difference.",
            "job search": "tailoring my resume for each role and quantifying my impact (percentages, timelines) helped me get past the initial filters.",
            "general interview": "breaking down prep into categories (technical, behavioral, company research) and tackling them one at a time made it way more manageable.",
        }
        
        middle = middles.get(topic, middles["general interview"])
        
        # Closing - optional resource mention
        if links_allowed and resource:
            closing = f"you might also find it helpful to check out some structured practice resources - sites like interview query have [curated questions]({resource}) that are pretty close to what you'd see in real interviews. good luck with your prep!"
        elif links_allowed:
            closing = "interview query also has some solid company-specific guides and practice questions if you want more structured prep. good luck!"
        else:
            closing = "good luck with your prep! feel free to ask if you have more specific questions."
        
        return f"{opening} {middle} {closing}"
    
    def _generate_low_intent_comment(self, topic: str, text: str) -> str:
        """Generate comment for low-intent posts (general career advice, etc.)."""
        
        comments = {
            "sql": "sql is definitely a foundational skill that opens a lot of doors. practicing with real datasets and focusing on business-oriented questions helps a lot more than just syntax drills imo.",
            "python": "python's versatility is what makes it so valuable - whether you're doing data analysis, automation, or ml. focusing on practical projects tends to stick better than just tutorials.",
            "machine learning": "ml is a broad field - i'd recommend picking a specific area (nlp, computer vision, etc.) and going deep rather than trying to learn everything at once.",
            "data science": "the data science field is definitely evolving. staying current with industry trends while building strong fundamentals in stats and coding is key.",
            "data analyst": "data analysis is a great entry point into tech. building a portfolio with real projects that show business impact tends to stand out more than certifications.",
            "data engineer": "data engineering is in high demand right now. getting hands-on with tools like spark, airflow, and cloud platforms is super valuable.",
            "coding": "consistency beats intensity when it comes to coding practice. even 30 mins a day adds up over time.",
            "job search": "the job market can be tough but persistence pays off. networking and tailoring applications tends to work better than mass applying.",
            "general interview": "breaking things down into smaller goals and tracking progress helps keep momentum going. you've got this!",
        }
        
        return comments.get(topic, comments["general interview"])


if __name__ == "__main__":
    generator = CommentGenerator()
    
    # Test with sample data
    test_post = {
        "type": "post",
        "title": "How do I prepare for SQL interviews at tech companies?",
        "text_snippet": "I have an interview coming up and I'm nervous about the SQL portion.",
        "intent": "HIGH",
        "matched_keywords": "sql interview questions",
        "companies_mentioned": "",
        "suggested_resource": "https://www.interviewquery.com/p/sql-questions-data-analyst",
        "links_allowed": "Yes",
    }
    
    suggestion = generator.generate_suggestion(test_post)
    print("Generated comment suggestion:")
    print(suggestion)
