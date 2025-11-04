from src.metrics.diagnostics import (
    breadth,
    cross_sectional_ic,
    hit_rate,
    hhi,
    quintile_spread,
)


def test_ic_and_quintile():
    factor = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}
    nxt = {"A": -0.02, "B": 0.0, "C": 0.01, "D": 0.02, "E": 0.03}
    ic = cross_sectional_ic(factor, nxt)
    spread = quintile_spread(factor, nxt, 5)
    assert ic > 0
    assert spread > 0


def test_hit_breadth_hhi():
    pred = {"A": 1, "B": -1, "C": 1}
    realized = {"A": 0.01, "B": -0.02, "C": 0.03}
    assert hit_rate(pred, realized) == 1.0
    weights = {"A": 0.5, "B": 0.3, "C": 0.2}
    assert breadth(weights) == 3
    hh = hhi(weights)
    assert 0 < hh <= 1
