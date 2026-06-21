#!/usr/bin/env python3
"""
AI News Hub - Hybrid Agent (GitHub Actions Version)
Runs every 2 hours via GitHub Actions.
Fetches RSS → Filters with Groq LLM → Saves to news.json + memory.json
"""

import os
import json
import time
import requests
import feedparser
from datetime import datetime, timezone
from typing import List, Dict, Any

# ==================== CONFIGURATION ====================
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

RSS_SOURCES = [
    {"url": "https://techcrunch.com/feed/", "category": "ai_agentic_tech", "name": "TechCrunch"},
    {"url": "https://www.theverge.com/rss/index.xml", "category": "ai_agentic_tech", "name": "The Verge"},
    {"url": "https://hnrss.org/frontpage", "category": "global_tech_breakthroughs", "name": "Hacker News"},
    {"url": "https://feeds.bloomberg.com/markets/news.rss", "category": "us_markets_economy", "name": "Bloomberg"},
    {"url": "https://www.cnbc.com/id/100003114/device/rss/rss.html", "category": "us_markets_economy", "name": "CNBC"},
    {"url": "https://feeds.reuters.com/reuters/topNews", "category": "global_geopolitics", "name": "Reuters"},
    {"url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "category": "global_geopolitics", "name": "NYT World"},
    {"url": "https://www.space.com/feeds/all", "category": "global_tech_breakthroughs", "name": "Space.com"},
    {"url": "https://www.sciencedaily.com/rss/all.xml", "category": "global_tech_breakthroughs", "name": "ScienceDaily"},
]

MAX_ARTICLES = 30
MEMORY_EXPIRY_HOURS = 24

# ==================== MEMORY MANAGEMENT ====================
def load_memory() -> set:
    """Load persistent memory from memory.json"""
    if not os.path.exists("memory.json"):
        return set()
    try:
        with open("memory.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            now = time.time()
            expiry = MEMORY_EXPIRY_HOURS * 3600
            valid = {item["title"] for item in data if (now - item.get("timestamp", 0)) < expiry}
            return valid
    except Exception as e:
        print(f"⚠️ Memory load error: {e}")
        return set()


def save_memory(titles: set):
    """Save memory back to memory.json"""
    data = [{"title": t, "timestamp": time.time()} for t in titles]
    with open("memory.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ==================== GROQ LLM ANALYSIS ====================
def analyze_article(title: str, source: str, category: str, api_key: str) -> Dict[str, Any]:
    """Send article to Groq with strict Chief Editor prompt"""
    prompt = f"""You are a Cynical Chief Editor at a top-tier global news agency.
Your Job: Filter for GROUNDBREAKING, WORLD-CHANGING, or HIGH-IMPACT news only.

STRICT FILTERING RULES (Reject 95% of input):
1. IMMEDIATE REJECT (Return relevant: false):
   - Rumors, Speculation, "Analysts predict", "Experts say"
   - Opinion pieces, Reviews, "How-to" guides, "Best of" lists
   - Minor updates (e.g. "Software v1.1", "Small price dip")
   - Clickbait (e.g. "You won't believe")
   - DUPLICATE STORIES that everyone already knows

2. ACCEPT ONLY (Return relevant: true):
   - OFFICIAL Major Releases (e.g. "GPT-5 Launched")
   - CRITICAL Market Events (Stock crash >5%)
   - GOVERNMENT / GEOPOLITICS (War, Treaties, Bills)
   - DISASTERS (Major earthquakes, Emergencies)

Input News:
Title: "{title}"
Source: "{source}"
Category: "{category}"

If RELEVANT, return JSON:
{{
  "relevant": true,
  "topic": "URGENT HEADLINE",
  "summary": ["Critical Fact 1", "Impact Fact 2"],
  "impact": "HIGH"
}}

If NOT RELEVANT, return: {{ "relevant": false }}"""

    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a strict news editor. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 400,
                "response_format": {"type": "json_object"}
            },
            timeout=30
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as e:
        print(f"   ❌ Groq error: {e}")
        return {"relevant": False}


# ==================== RSS FETCHING ====================
def fetch_rss(source: Dict) -> List[Dict]:
    """Fetch and parse RSS feed"""
    try:
        feed = feedparser.parse(source["url"])
        articles = []
        for entry in feed.entries[:8]:
            articles.append({
                "title": entry.get("title", "").strip(),
                "link": entry.get("link", "").strip(),
                "published": entry.get("published", ""),
                "source": source["name"],
                "category": source["category"]
            })
        return articles
    except Exception as e:
        print(f"   ⚠️ RSS failed for {source['name']}: {e}")
        return []


# ==================== MAIN AGENT ====================
def main():
    print("🚀 AI News Hub Agent Started")
    print(f"   Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ ERROR: GROQ_API_KEY not set in GitHub Secrets")
        return

    memory = load_memory()
    print(f"   Memory loaded: {len(memory)} titles")

    all_articles = []
    for source in RSS_SOURCES:
        print(f"🔎 Fetching: {source['name']}")
        articles = fetch_rss(source)
        all_articles.extend(articles)

    print(f"   Total articles fetched: {len(all_articles)}")

    accepted = []
    for article in all_articles:
        if article["title"] in memory:
            continue

        analysis = analyze_article(
            article["title"],
            article["source"],
            article["category"],
            api_key
        )

        if analysis.get("relevant") is True:
            processed = {
                "title": article["title"],
                "link": article["link"],
                "source": article["source"],
                "category": article["category"],
                "published": article["published"],
                "topic": analysis.get("topic", article["title"]),
                "summary": analysis.get("summary", []),
                "impact": analysis.get("impact", "MEDIUM"),
                "fetched_at": datetime.now(timezone.utc).isoformat()
            }
            accepted.append(processed)
            memory.add(article["title"])
            print(f"   ✅ ACCEPTED: {article['title'][:60]}...")

    print(f"\n📊 Results: {len(accepted)} groundbreaking stories found")

    # Save outputs
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(accepted, f, indent=2, ensure_ascii=False)

    save_memory(memory)

    print("✅ news.json and memory.json updated successfully")


if __name__ == "__main__":
    main()