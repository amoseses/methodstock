import re
from datetime import datetime, timezone

POSITIVE = {
    "earnings beat": 25, "beats estimates": 25, "raises guidance": 25,
    "guidance raised": 25, "record revenue": 18, "contract win": 18,
    "wins contract": 18, "analyst upgrade": 12, "price target raised": 12,
    "fda approval": 25, "share buyback": 10, "acquisition": 8
}
NEGATIVE = {
    "earnings miss": -30, "misses estimates": -25, "cuts guidance": -25,
    "guidance lowered": -25, "revenue decline": -18, "fraud": -40,
    "investigation": -20, "sec probe": -30, "bankruptcy": -50,
    "going concern": -50, "analyst downgrade": -12, "price target cut": -10,
    "fda rejection": -30, "recall": -18, "data breach": -20
}
CRITICAL_TERMS = ("bankruptcy", "going concern", "fraud", "sec probe", "accounting scandal")

def _parse_time(value):
    if not value: return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None

def score_news(articles, as_of=None):
    as_of = as_of or datetime.now(timezone.utc)
    seen, accepted = set(), []
    total = 0.0
    critical = False
    for a in articles:
        headline = (a.get("headline") or "").strip()
        summary = (a.get("summary") or "").strip()
        if not headline: continue
        key = re.sub(r"\W+", "", headline.lower())
        if key in seen: continue
        seen.add(key)
        published = _parse_time(a.get("published_at"))
        if published and published > as_of:
            continue
        text = (headline + " " + summary).lower()
        score = sum(v for phrase, v in POSITIVE.items() if phrase in text)
        score += sum(v for phrase, v in NEGATIVE.items() if phrase in text)
        # Small lexicon fallback; deliberately low weight and transparent.
        positive_words = ("growth", "surge", "strong demand", "partnership", "expansion")
        negative_words = ("weak demand", "decline", "lawsuit", "loss", "layoffs")
        score += 3 * sum(text.count(w) for w in positive_words)
        score -= 3 * sum(text.count(w) for w in negative_words)
        score = max(-50, min(50, score))
        critical = critical or (score < 0 and any(t in text for t in CRITICAL_TERMS))
        accepted.append({**a, "article_score": score})
        total += score
    # Aggregate by average to reduce bias from high article volume.
    avg = total / len(accepted) if accepted else 0.0
    normalized = max(-100.0, min(100.0, avg * 2))
    return {"news_score": normalized, "major_negative": critical,
            "article_count": len(accepted), "articles": accepted,
            "news_status": "ok" if accepted else "no_recent_articles"}
