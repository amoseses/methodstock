from .config import settings

def decision_from_score(score, major_negative=False):
    if major_negative: return "STRONG_EXIT"
    if score >= 65: return "STRONG_BUY"
    if score >= 25: return "BUY"
    if score > -25: return "HOLD"
    if score > -65: return "SELL"
    return "STRONG_EXIT"

def generate_signals(technical_score, news_score, major_negative=False):
    weight = settings.combined_tech_weight
    if not 0 <= weight <= 1:
        raise ValueError("COMBINED_TECH_WEIGHT must be between 0 and 1")
    combined = weight * technical_score + (1-weight) * news_score
    return {
        "technical": {"score": technical_score, "decision": decision_from_score(technical_score)},
        "news": {"score": news_score, "decision": decision_from_score(news_score, major_negative)},
        "combined": {"score": combined, "decision": decision_from_score(combined, major_negative)}
    }
