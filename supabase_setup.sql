-- Run this in Supabase SQL Editor (https://supabase.com/dashboard → SQL Editor → New Query)

-- Opportunities table
CREATE TABLE IF NOT EXISTS opportunities (
    id TEXT PRIMARY KEY,
    type TEXT,
    intent TEXT,
    subreddit TEXT,
    title TEXT,
    text_snippet TEXT,
    url TEXT UNIQUE,
    author TEXT,
    score INTEGER,
    num_comments INTEGER,
    created_utc TEXT,
    matched_keywords TEXT,
    companies_mentioned TEXT,
    recommended_persona TEXT,
    suggested_resource TEXT,
    links_allowed TEXT,
    self_promo_allowed TEXT,
    subreddit_rules TEXT,
    comment_suggestion TEXT,
    status TEXT DEFAULT 'pending',
    reply_url TEXT,
    reply_timestamp TEXT,
    feedback TEXT,
    scan_time TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Scan state table
CREATE TABLE IF NOT EXISTS scan_state (
    id INTEGER PRIMARY KEY DEFAULT 1,
    next_index INTEGER DEFAULT 0,
    last_scan TEXT,
    last_batch JSONB
);

-- Insert initial scan state
INSERT INTO scan_state (id, next_index) VALUES (1, 0) ON CONFLICT (id) DO NOTHING;

-- Enable Row Level Security (optional but recommended)
ALTER TABLE opportunities ENABLE ROW LEVEL SECURITY;
ALTER TABLE scan_state ENABLE ROW LEVEL SECURITY;

-- Allow public access (since we're using anon key)
CREATE POLICY "Allow all access to opportunities" ON opportunities FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all access to scan_state" ON scan_state FOR ALL USING (true) WITH CHECK (true);
