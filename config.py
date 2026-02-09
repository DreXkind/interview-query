"""
Configuration for Reddit Automation - Interview Query
"""

# Keywords to search for in posts and comments
# FOCUS: Interview preparation, practice, what to expect - NOT job application frustration
# Based on user feedback: removed vague terms like "what to expect", "google interview" alone
KEYWORDS = [
    # Interview Discussion flair posts (cscareerquestions uses this)
    "interview discussion",
    
    # Interview prep phrases (high relevance)
    "interview prep",
    "interview preparation",
    "preparing for my interview",
    "how to prepare for interview",
    "tips for my interview",
    "interview tips",
    "mock interview",
    
    # Specific interview types - must include "interview" or "prep"
    "coding interview prep",
    "technical interview prep",
    "behavioral interview prep",
    "system design prep",
    "case study prep",
    "preparing for coding interview",
    "preparing for technical interview",
    
    # Interview rounds - specific phrases
    "have an interview coming up",
    "interview next week",
    "interview tomorrow",
    "upcoming interview",
    "final round tips",
    "onsite tips",
    
    # Practice and study for interviews
    "practice for interview",
    "study for interview",
    "interview questions",
    "sql interview",
    "python interview",
    "data science interview",
    "data analyst interview",
    "data engineer interview",
    "machine learning interview",
    "product sense",
    "statistics interview",
    "probability interview",
    
    # Company interview prep - must include "prep" or "tips" or "questions"
    "faang prep",
    "faang interview tips",
    "maang prep",
    "big tech interview",
    
    # Assessment prep
    "online assessment tips",
    "oa prep",
    "hackerrank prep",
    "codesignal prep",
    "leetcode prep",
    
    # Asking for help with prep
    "how do i prepare for interview",
    "best way to prepare for interview",
    "resources for interview prep",
    "how to study for interview",
    "what should i study for interview",
    
    # BROAD keyword - will be filtered by relevance check
    "interview",
]

# Relevance signals for Interview Query - post must contain at least one to be relevant
# Used when "interview" is matched broadly to filter out irrelevant posts
IQ_RELEVANT_SIGNALS = [
    # Interview preparation context
    "preparing", "prepare", "prep", "study", "practice", "tips", "advice",
    "how to", "how do i", "what should i", "any suggestions", "recommendations",
    
    # Asking about interview process
    "what to expect", "interview process", "interview experience", "anyone interviewed",
    "how is the interview", "interview loop", "interview stages",
    
    # Specific interview types
    "coding", "technical", "behavioral", "system design", "case study",
    "sql", "python", "data science", "data analyst", "machine learning",
    "phone screen", "onsite", "final round", "take home",
    
    # Struggling/need help signals
    "struggling", "failed", "bombed", "nervous", "anxious", "worried",
    "need help", "any tips", "advice for", "help me",
    
    # Upcoming interview signals
    "coming up", "next week", "tomorrow", "scheduled", "upcoming",
    "got an interview", "have an interview", "landed an interview",
    
    # Practice/resources
    "resources", "study material", "leetcode", "hackerrank", "mock",
]

# Signals that indicate post is NOT relevant to Interview Query
IQ_IRRELEVANT_SIGNALS = [
    # Job application (not interview prep)
    "resume review", "cover letter", "job application", "applying to",
    "no response", "ghosted", "rejected application",
    
    # Post-interview/offer stage
    "salary negotiation", "negotiate offer", "offer letter", "compensation package",
    "accepted offer", "declined offer", "counter offer", "signing bonus",
    
    # General career (not interview)
    "should i quit", "toxic workplace", "work life balance",
    "return to office", "layoff", "fired", "terminated",
    
    # Dev technical help (not interview prep)
    "bug fix", "code review", "pull request", "production issue",
    "deployment", "architecture decision", "refactor",
]

# Subreddits to monitor - focused on career/interview prep communities
# Expanded with regional job subreddits across North America
SUBREDDITS = {
    # Persona 1: warmeggnog (NYC metro) - focus on career subs + East Coast regional
    "warmeggnog": [
        "cscareerquestions",
        "analytics",
        "leetcode",
        "interviews",
        # Career advice subs
        "jobs",
        "resumes",
        "ITCareerQuestions",
        # NYC/East Coast regional
        "NYCjobs",
        "bostonjobs",
        "philadelphiajobs",
        "dcjobs",
        "AskNYC",
    ],
    # Persona 2: KitchenTaste7229 (Pacific Northwest) - senior/experienced + PNW regional
    "KitchenTaste7229": [
        "datascience",
        "machinelearning",
        "experienceddevs",
        "dataengineering",
        # Career advice subs
        "careeradvice",
        "FinancialCareers",
        "consulting",
        # Pacific Northwest regional
        "seattlejobs",
        "portlandjobs",
        "AskSeattle",
        # Canada
        "vancouverjobs",
        "torontojobs",
        "montrealjobs",
        "calgaryjobs",
        "ottawajobs",
    ],
    # Persona 3: Holiday_Lie_9435 (Austin/Chicago/Atlanta - Career Switcher) + Midwest/South regional
    "Holiday_Lie_9435": [
        "careerguidance",
        "learnprogramming",
        "careerchange",
        # Career advice subs
        "cscareerquestionsCAD",
        "ProductManagement",
        "BusinessAnalysis",
        # Midwest regional
        "chicagojobs",
        "minneapolisjobs",
        "detroitjobs",
        "columbusjobs",
        "AskChicago",
        # South regional
        "austinjobs",
        "DFWJobs",
        "houstonjobs",
        "atlantajobs",
        "nashvillejobs",
        "raboraleigh",
    ],
    # Persona 4: Cryoschema (California/International) + West Coast regional
    "Cryoschema": [
        "cscareerquestionsEU",
        "AskEngineers",
        "startups",
        # Career advice subs
        "dataanalysis",
        "SQL",
        "learnpython",
        # California regional
        "bayareajobs",
        "SFBayJobs",
        "losangelesjobs",
        "sandiegojobs",
        "AskSF",
        "AskLosAngeles",
        # Southwest regional
        "denverjobs",
        "phoenixjobs",
        "AskDenver",
        # Florida
        "miamijobs",
    ],
}

# All unique subreddits (flattened)
ALL_SUBREDDITS = list(set(
    sub for subs in SUBREDDITS.values() for sub in subs
))

# Interview Query resources to suggest based on topic
IQ_RESOURCES = {
    "sql": "https://www.interviewquery.com/p/sql-questions-data-analyst",
    "python": "https://www.interviewquery.com/p/python-interview-questions",
    "machine learning": "https://www.interviewquery.com/p/machine-learning-interview-questions",
    "probability": "https://www.interviewquery.com/p/probability-interview-questions",
    "statistics": "https://www.interviewquery.com/p/statistics-interview-questions",
    "data analyst": "https://www.interviewquery.com/p/data-analyst-interview-questions",
    "data scientist": "https://www.interviewquery.com/p/data-science-interview-questions",
    "data engineer": "https://www.interviewquery.com/p/data-engineer-interview-questions",
    "product analyst": "https://www.interviewquery.com/p/product-analyst-interview-questions",
    "case study": "https://www.interviewquery.com/p/case-study-interview-questions",
    "pandas": "https://www.interviewquery.com/p/pandas-interview-questions",
    "company guides": "https://www.interviewquery.com/companies",
    "project ideas": "https://www.interviewquery.com/p/data-analytics-project-ideas-and-datasets",
    "practice questions": "https://www.interviewquery.com/questions",
}

# Company names for matching
COMPANIES = [
    "meta", "facebook", "google", "amazon", "apple", "microsoft", "netflix",
    "bloomberg", "stripe", "airbnb", "uber", "lyft", "coinbase", "robinhood",
    "databricks", "snowflake", "spotify", "twitter", "x", "linkedin", "salesforce",
    "oracle", "ibm", "intel", "nvidia", "adobe", "paypal", "square", "block",
    "doordash", "instacart", "pinterest", "snap", "tiktok", "bytedance",
]
