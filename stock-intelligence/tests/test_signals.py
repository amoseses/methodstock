from stock_intelligence.signals import decision_from_score, generate_signals

def test_thresholds():
    assert decision_from_score(70)=="STRONG_BUY"
    assert decision_from_score(30)=="BUY"
    assert decision_from_score(0)=="HOLD"
    assert decision_from_score(-30)=="SELL"
    assert decision_from_score(-70)=="STRONG_EXIT"

def test_negative_override():
    assert decision_from_score(90,True)=="STRONG_EXIT"

def test_combined_weight():
    x=generate_signals(100,0)
    assert x["combined"]["score"]==60
