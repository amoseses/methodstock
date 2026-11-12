from stock_intelligence.news import score_news

def test_negative_event():
    x=score_news([{"headline":"Company announces bankruptcy","published_at":"2026-11-12T10:00:00Z"}])
    assert x["news_score"]<0
    assert x["major_negative"]

def test_deduplication():
    x=score_news([{"headline":"Company beats estimates"},{"headline":"Company beats estimates"}])
    assert x["article_count"]==1

def test_future_news_excluded():
    x=score_news([{"headline":"Company beats estimates","published_at":"2099-01-01T00:00:00Z"}])
    assert x["article_count"]==0
