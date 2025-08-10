import os
import re
import time
import requests
import pandas as pd
from typing import List, Dict, Any
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import snscrape.modules.twitter as sntwitter
from googleapiclient.discovery import build
from tqdm import tqdm
import json
from openai import OpenAI
from transformers import pipeline

# Load environment variables
load_dotenv()

# ---------- API KEYS ----------
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
YOUTUBE_KEY = os.getenv("YOUTUBE_API_KEY")

if not OPENAI_KEY:
    raise RuntimeError("Set OPENAI_API_KEY in your environment variables.")

# OpenAI client (new >=1.0 syntax)
client = OpenAI(api_key=OPENAI_KEY)

# YouTube client
if YOUTUBE_KEY:
    youtube = build("youtube", "v3", developerKey=YOUTUBE_KEY)
else:
    youtube = None

# ---------- CONFIG ----------
KEYWORD_LIST = ["smart fan"]
N_RESULTS = 25
COMPETITORS = ["Atomberg", "Crompton", "Havells", "Orient", "Usha", "Bajaj"]
WEIGHT_MENTION_FREQ = 0.6
WEIGHT_SENTIMENT = 0.4
OUTPUT_PREFIX = "sov_multi"
USER_AGENT = "Mozilla/5.0"

# ---------- UTILITIES ----------
def fetch_page_text(url: str) -> str:
    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"[fetch_page_text] failed for {url}: {e}")
        return ""
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return re.sub(r"\s+", " ", soup.get_text(separator=" ", strip=True))

def count_brand_mentions(text: str, brands: List[str]) -> Dict[str, int]:
    lower = text.lower()
    return {b: lower.count(b.lower()) for b in brands}

sentiment_model = pipeline("sentiment-analysis")

def call_openai_sentiment(snippet: str) -> Dict[str, Any]:
    try:
        res = sentiment_model(snippet[:512])[0]  # limit to 512 chars
        label = res["label"]  # "POSITIVE", "NEGATIVE", "NEUTRAL" (some models only pos/neg)
        score = float(res["score"])
        if "POS" in label.upper():
            return {"label": "Positive", "score": score}
        elif "NEG" in label.upper():
            return {"label": "Negative", "score": score}
        else:
            return {"label": "Neutral", "score": score}
    except Exception as e:
        print(f"[sentiment error] {e}")
        return {"label": "Neutral", "score": 0.5}
    
def compute_sov(brand: str, rows: List[Dict[str, Any]]) -> float:
    total_mentions = sum(sum(r["brand_counts"].values()) for r in rows)
    brand_mentions = sum(r["brand_counts"].get(brand, 0) for r in rows)
    freq = (brand_mentions / total_mentions) if total_mentions else 0.0
    sent_scores = []
    for r in rows:
        sb = r.get("sentiment_by_brand", {}).get(brand)
        if sb:
            lbl = sb["label"].lower()
            sc = sb["score"]
            val = 1.0*sc if lbl=="positive" else (0.5*sc if lbl=="neutral" else 0.0)
            sent_scores.append(val)
    avg_sent = sum(sent_scores)/len(sent_scores) if sent_scores else 0.5
    return WEIGHT_MENTION_FREQ*freq + WEIGHT_SENTIMENT*avg_sent

# ---------- GOOGLE COLLECTOR (SerpAPI + fallback) ----------
def collect_google(keyword: str, n: int) -> List[Dict[str, Any]]:
    rows = []

    def process_results(result_links):
        local_rows = []
        for url, title in result_links:
            text = fetch_page_text(url)
            full = f"{title} {text}"
            bc = count_brand_mentions(full, COMPETITORS)
            sb = {}
            for b, cnt in bc.items():
                if cnt > 0:
                    idx = full.lower().find(b.lower())
                    ctx = full[max(0, idx - 200):idx + 200]
                    sb[b] = call_openai_sentiment(ctx)
                    time.sleep(0.5)
            local_rows.append({
                "platform": "Google",
                "keyword": keyword,
                "title": title,
                "url": url,
                "brand_counts": bc,
                "sentiment_by_brand": sb
            })
        return local_rows

    try:
        if SERPAPI_KEY:
            from serpapi import GoogleSearch
            search = GoogleSearch({
                "engine": "google",
                "q": keyword,
                "num": n,
                "api_key": SERPAPI_KEY
            })
            resp = search.get_dict()
            result_links = [
                (r.get("link", ""), r.get("title", ""))
                for r in resp.get("organic_results", [])
                if r.get("link")
            ]
            print(f"[Google] Using SerpAPI, got {len(result_links)} results.")
            rows.extend(process_results(result_links))
        else:
            raise ImportError("SERPAPI not configured.")
    except Exception as e:
        print(f"[Google] SerpAPI failed ({e}). Falling back to scraping...")
        try:
            headers = {"User-Agent": USER_AGENT}
            r = requests.get(f"https://www.google.com/search?q={keyword}", headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            search_results = soup.select("div.tF2Cxc")
            result_links = []
            for result in search_results[:n]:
                link_tag = result.select_one("a")
                title_tag = result.select_one("h3")
                if link_tag and title_tag:
                    result_links.append((link_tag["href"], title_tag.text))
            print(f"[Google] Scraped {len(result_links)} results.")
            rows.extend(process_results(result_links))
        except Exception as scrape_err:
            print(f"[Google] Fallback scraping also failed: {scrape_err}")

    return rows

# ---------- YOUTUBE COLLECTOR ----------
def collect_youtube(keyword: str, n: int) -> List[Dict[str, Any]]:
    if not youtube:
        print("[YouTube] API key not set, skipping...")
        return []
    rows = []
    res = youtube.search().list(q=keyword, part="snippet", type="video", maxResults=n).execute()
    for item in res.get("items", []):
        vid = item["id"]["videoId"]
        stats = youtube.videos().list(part="statistics", id=vid).execute()["items"][0]["statistics"]
        title = item["snippet"]["title"]
        desc = item["snippet"]["description"]
        full = title + " " + desc
        bc = count_brand_mentions(full, COMPETITORS)
        sb = {}
        for b, cnt in bc.items():
            if cnt > 0:
                idx = full.lower().find(b.lower())
                ctx = full[max(0, idx - 200):idx + 200]
                sb[b] = call_openai_sentiment(ctx)
                time.sleep(0.5)
        rows.append({
            "platform": "YouTube",
            "keyword": keyword,
            "title": title,
            "url": f"https://youtu.be/{vid}",
            "brand_counts": bc,
            "sentiment_by_brand": sb,
            "engagement": stats
        })
    return rows

# ---------- TWITTER COLLECTOR ----------
def collect_twitter(keyword: str, n: int) -> List[Dict[str, Any]]:
    rows = []
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(keyword).get_items()):
        if i >= n:
            break
        content = tweet.content
        bc = count_brand_mentions(content, COMPETITORS)
        sb = {}
        for b, cnt in bc.items():
            if cnt > 0:
                idx = content.lower().find(b.lower())
                ctx = content[max(0, idx - 200):idx + 200]
                sb[b] = call_openai_sentiment(ctx)
                time.sleep(0.5)
        rows.append({
            "platform": "Twitter",
            "keyword": keyword,
            "title": None,
            "url": None,
            "brand_counts": bc,
            "sentiment_by_brand": sb,
            "engagement": {"likes": tweet.likeCount, "retweets": tweet.retweetCount}
        })
    return rows

# ---------- MAIN ----------
def run_agent():
    all_rows = []
    for kw in KEYWORD_LIST:
        all_rows += collect_google(kw, N_RESULTS)
        all_rows += collect_youtube(kw, N_RESULTS)
        # Skipping Twitter for now
        # all_rows += collect_twitter(kw, N_RESULTS)

    # Summary
        # Overall SoV
    summary = []
    for b in COMPETITORS:
        sov = compute_sov(b, all_rows)
        total = sum(r["brand_counts"].get(b, 0) for r in all_rows)
        summary.append({"brand": b, "total_mentions": total, "sov": sov})
    df_sum = pd.DataFrame(summary).sort_values("sov", ascending=False)
    print("\nOverall SoV across all platforms:\n", df_sum.to_string(index=False))

    # Per-platform SoV
    platform_summary = []
    platforms = set(r["platform"] for r in all_rows)
    for plat in platforms:
        plat_rows = [r for r in all_rows if r["platform"] == plat]
        for b in COMPETITORS:
            sov = compute_sov(b, plat_rows)
            total = sum(r["brand_counts"].get(b, 0) for r in plat_rows)
            platform_summary.append({
                "platform": plat,
                "brand": b,
                "total_mentions": total,
                "sov": sov
            })
    df_platform_sum = pd.DataFrame(platform_summary).sort_values(["platform", "sov"], ascending=[True, False])
    print("\nPer-platform SoV breakdown:\n", df_platform_sum.to_string(index=False))

    # Save outputs
    df_details = pd.DataFrame([{
        "platform": r["platform"],
        "keyword": r["keyword"],
        "brand_counts": str(r["brand_counts"]),
        "sentiment_by_brand": str(r["sentiment_by_brand"]),
        "engagement": str(r.get("engagement", {}))
    } for r in all_rows])
    df_details.to_csv(f"{OUTPUT_PREFIX}_details.csv", index=False)
    df_sum.to_csv(f"{OUTPUT_PREFIX}_summary.csv", index=False)
    df_platform_sum.to_csv(f"{OUTPUT_PREFIX}_platform_summary.csv", index=False)
    print(f"\nSaved: {OUTPUT_PREFIX}_details.csv, {OUTPUT_PREFIX}_summary.csv & {OUTPUT_PREFIX}_platform_summary.csv")

if __name__ == "__main__":
    run_agent()
