from src.features.momentum import price_momentum
from src.features.revisions import revision_velocity
from src.features.quality import quality_composite


def test_price_momentum_basic():
    prices = {"AAA": [10, 11, 12, 13, 14], "BBB": [10, 10, 10, 10, 10]}
    m = price_momentum(prices, [2, 4])
    assert m["AAA"][2] > 0 and m["AAA"][4] > 0
    assert m["BBB"][2] == 0 and m["BBB"][4] == 0


def test_revision_velocity_basic():
    eps = {"AAA": [1, 1, 1, 1.2, 1.3, 1.35, 1.4, 1.45, 1.5, 1.6, 1.7, 1.75, 1.8]}
    rv = revision_velocity(eps, short=4, long=8)
    assert rv["AAA"] != 0


def test_quality_composite_signs():
    q = quality_composite({"AAA": 0.6}, {"AAA": 0.1}, {"AAA": 0.2})
    q_high_gpm = quality_composite({"AAA": 0.8}, {"AAA": 0.1}, {"AAA": 0.2})["AAA"]
    assert q_high_gpm > q["AAA"]
    q_high_acc = quality_composite({"AAA": 0.6}, {"AAA": 0.3}, {"AAA": 0.2})["AAA"]
    assert q_high_acc < q["AAA"]
