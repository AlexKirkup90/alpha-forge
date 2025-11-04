from collections import OrderedDict

from src.portfolio.costs import CostRow, estimate_costs


def _make_inputs(multiplier: float = 1.0):
    trades = OrderedDict[
        str, dict[str, float]
    ](
        {
            "2023-01-01": {"AAA": 100.0 * multiplier, "BBB": 200.0 * multiplier, "CCC": 300.0 * multiplier},
            "2023-01-02": {"AAA": -50.0 * multiplier, "BBB": -100.0 * multiplier, "CCC": -150.0 * multiplier},
        }
    )
    adv = {"AAA": 1000.0, "BBB": 2000.0, "CCC": 1500.0}
    spreads = {"AAA": 5.0, "BBB": 10.0, "CCC": 8.0}
    sigma = {"AAA": 0.02, "BBB": 0.015, "CCC": 0.025}
    params = {"p_max": 0.2, "k": 0.7, "fee_bps": 1.0}
    return trades, adv, spreads, sigma, params


def test_costs_scale_with_trades():
    inputs = _make_inputs()
    costs, _ = estimate_costs(*inputs)
    larger_inputs = _make_inputs(multiplier=2.0)
    larger_costs, _ = estimate_costs(*larger_inputs)
    for base_row, larger_row in zip(costs, larger_costs):
        assert larger_row.C_total > base_row.C_total


def test_impact_sublinear_growth():
    inputs = _make_inputs()
    base_costs, _ = estimate_costs(*inputs)
    doubled_inputs = _make_inputs(multiplier=2.0)
    doubled_costs, _ = estimate_costs(*doubled_inputs)
    for base_row, doubled_row in zip(base_costs, doubled_costs):
        ratio = doubled_row.C_impact / base_row.C_impact if base_row.C_impact else 1.0
        assert ratio > 1.0
        assert ratio < 2.0


def test_participation_caps_flag_violations():
    trades, adv, spreads, sigma, params = _make_inputs(multiplier=20.0)
    params["p_max"] = 0.05
    costs, diagnostics = estimate_costs(trades, adv, spreads, sigma, params)
    assert costs  # ensure we computed rows
    violations = diagnostics["violations"]
    assert any(count > 0 for count in violations.values())
    participation = diagnostics["participation"]
    for per_date in participation.values():
        for value in per_date.values():
            assert value <= params["p_max"] + 1e-12
