#!/usr/bin/env python3
"""
AI News Hub - Hybrid Agent (GitHub Actions Version)
Runs every 30 minutes via GitHub Actions.
Fetches RSS → Filters with Groq LLM → Appends to news.json + maintains memory.json
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
    # === INDIA NATIONAL (High Quality) ===
    {"url": "https://www.thehindu.com/feeder/default.rss", "category": "india_national", "name": "The Hindu"},
    {"url": "https://indianexpress.com/feed/", "category": "india_national", "name": "Indian Express"},
    {"url": "https://www.livemint.com/rss/news", "category": "india_business", "name": "Mint"},

    # === HYDERABAD / TELANGANA (Local Focus) ===
    {"url": "https://www.thehindu.com/news/cities/Hyderabad/feeder/default.rss", "category": "hyderabad", "name": "The Hindu Hyderabad"},
    {"url": "https://telanganatoday.com/feed", "category": "hyderabad", "name": "Telangana Today"},

    # === INDIA TECH & STARTUPS ===
    {"url": "https://yourstory.com/feed", "category": "india_tech", "name": "YourStory"},
    {"url": "https://inc42.com/feed/", "category": "india_tech", "name": "Inc42"},

    # === GLOBAL (Keep a few high-quality ones) ===
    {"url": "https://techcrunch.com/feed/", "category": "global_tech", "name": "TechCrunch"},
    {"url": "https://feeds.reuters.com/reuters/topNews", "category": "global_geopolitics", "name": "Reuters"},
]

MAX_ARTICLES = 50  # Keep up to 50 articles in feed
MEMORY_EXPIRY_HOURS = 24
ARTICLE_EXPIRY_HOURS = 24  # Remove articles older than 24 hours
MAX_REJECTED = 500   # Keep only the latest 500 rejected articles

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


def load_news() -> List[Dict]:
    """Load existing news from news.json"""
    if not os.path.exists("news.json"):
        return []
    try:
        with open("news.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ News load error: {e}")
        return []


def is_article_expired(article: Dict) -> bool:
    """Check if article is older than ARTICLE_EXPIRY_HOURS"""
    try:
        if "fetched_at" not in article:
            return False
        
        fetched_time = datetime.fromisoformat(article["fetched_at"].replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        age_hours = (now - fetched_time).total_seconds() / 3600
        return age_hours > ARTICLE_EXPIRY_HOURS
    except Exception as e:
        print(f"⚠️ Error checking article expiry: {e}")
        return False


def save_rejected(article: dict, reason: str = "Not relevant"):
    """Append rejected article to rejected.json (keeps last 500)"""
    try:
        if os.path.exists("rejected.json"):
            with open("rejected.json", "r", encoding="utf-8") as f:
                rejected = json.load(f)
        else:
            rejected = []

        rejected.append({
            "title": article.get("title"),
            "source": article.get("source"),
            "category": article.get("category"),
            "link": article.get("link"),
            "rejected_at": datetime.now(timezone.utc).isoformat(),
            "reason": reason
        })

        # Keep only the latest MAX_REJECTED entries
        rejected = rejected[-MAX_REJECTED:]

        with open("rejected.json", "w", encoding="utf-8") as f:
            json.dump(rejected, f, indent=2, ensure_ascii=False)

    except Exception as e:
        print(f"   ⚠️ Failed to save rejected article: {e}")


# ==================== GROQ LLM ANALYSIS ====================
def analyze_article(title: str, source: str, category: str, api_key: str) -> Dict[str, Any]:
    """Send article to Groq for relevance evaluation - BALANCED FILTERING"""
    prompt = f"""You are a News Curator at a quality news aggregator.
Your Job: Identify INTERESTING, NEWSWORTHY, or NOTABLE stories worth reading.

BALANCED FILTERING RULES (Accept ~50-60% of input):
1. REJECT ONLY these types (Return relevant: false):
   - Spam, pure clickbait ("Top 10 shocking...", "You won't believe...")
   - Unsubstantiated rumors with no credible source
   - Duplicate/repeat stories already covered
   - Entertainment fluff (celebrity gossip, movie reviews, quotes of the day)
   - Weather reports, mundane local incidents
   - Trivial stories with no real impact

2. ACCEPT these types (Return relevant: true):
   - Breaking news, official announcements
   - Business & market news (company updates, earnings, funding, M&A)
   - Technology developments & AI breakthroughs
   - Policy changes & government decisions
   - International relations & geopolitical news
   - Infrastructure & development projects
   - Crime/investigation with significance
   - Health & science research findings
   - Economic indicators & analysis
   - Any news from credible sources with actual substance

Input News:
Title: "{title}"
Source: "{source}"
Category: "{category}"

If RELEVANT, return JSON:
{{
  "relevant": true,
  "topic": "HEADLINE",
  "summary": ["Key point 1", "Key point 2"],
  "impact": "MEDIUM"
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
                    {"role": "system", "content": "You are a balanced news curator. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
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

    # Load existing news
    existing_news = load_news()
    print(f"   Existing news: {len(existing_news)} articles")

    # Remove expired articles (older than 24 hours)
    unexpired_news = [article for article in existing_news if not is_article_expired(article)]
    expired_count = len(existing_news) - len(unexpired_news)
    if expired_count > 0:
        print(f"   Removed {expired_count} expired articles (>24h old)")

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
        else:
            save_rejected(article)
            print(f"   ❌ REJECTED: {article['title'][:60]}...")

    # Append new articles to existing ones (prepend for freshness)
    all_news = accepted + unexpired_news
    
    # Keep only the most recent MAX_ARTICLES
    all_news = all_news[:MAX_ARTICLES]

    print(f"\n📊 Results: {len(accepted)} new stories found")
    print(f"   Total in feed: {len(all_news)} articles (max {MAX_ARTICLES})")

    # Save outputs
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(all_news, f, indent=2, ensure_ascii=False)

    save_memory(memory)

    print("✅ news.json and memory.json updated successfully")


if __name__ == "__main__":
    main()
