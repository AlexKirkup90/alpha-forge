import pandas as pd

from src.portfolio.costs import estimate_costs


def _make_inputs(multiplier: float = 1.0):
    dates = pd.date_range("2023-01-01", periods=2, freq="D")
    tickers = ["AAA", "BBB", "CCC"]
    trades = pd.DataFrame(
        {
            "AAA": [100.0, -50.0],
            "BBB": [200.0, -100.0],
            "CCC": [300.0, -150.0],
        },
        index=dates,
    ) * multiplier
    adv = pd.Series({"AAA": 1000.0, "BBB": 2000.0, "CCC": 1500.0})
    spreads = pd.Series({"AAA": 5.0, "BBB": 10.0, "CCC": 8.0})
    sigma = pd.Series({"AAA": 0.02, "BBB": 0.015, "CCC": 0.025})
    params = {"p_max": 0.2, "k": 0.7, "fee_bps": 1.0}
    return trades, adv, spreads, sigma, params


def test_costs_scale_with_trades():
    inputs = _make_inputs()
    costs = estimate_costs(*inputs)
    larger_inputs = _make_inputs(multiplier=2.0)
    larger_costs = estimate_costs(*larger_inputs)
    assert (larger_costs["C_total"] > costs["C_total"]).all()


def test_impact_sublinear_growth():
    inputs = _make_inputs()
    base = estimate_costs(*inputs)
    doubled_inputs = _make_inputs(multiplier=2.0)
    doubled = estimate_costs(*doubled_inputs)
    ratio = doubled["C_impact"] / base["C_impact"]
    assert (ratio > 1.0).all()
    assert (ratio < 2.0).all()


def test_participation_caps_flag_violations():
    trades, adv, spreads, sigma, params = _make_inputs(multiplier=20.0)
    params["p_max"] = 0.05
    costs = estimate_costs(trades, adv, spreads, sigma, params)
    violations = costs.attrs["violations"]
    assert (violations > 0).any()
    participation = costs.attrs["participation"]
    assert (participation <= params["p_max"] + 1e-12).all().all()
