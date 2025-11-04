from src.ledger.alpha_ledger import compute_feature_marginals


def test_compute_feature_marginals_basic():
    weights = {
        "value": {
            "2023-01-01": {"AAA": 0.1, "BBB": 0.0},
            "2023-01-08": {"AAA": 0.0, "BBB": 0.2},
        },
        "momentum": {
            "2023-01-01": {"AAA": 0.0, "BBB": 0.05},
            "2023-01-08": {"AAA": -0.1, "BBB": 0.0},
        },
    }
    next_returns = {
        "2023-01-01": {"AAA": 0.02, "BBB": 0.01},
        "2023-01-08": {"AAA": -0.01, "BBB": 0.03},
    }

    ledger = compute_feature_marginals(weights, next_returns)
    assert isinstance(ledger, list)
    assert len(ledger) == 4

    # Check a specific feature/date row
    first_value = next(
        row
        for row in ledger
        if row["date"] == "2023-01-01" and row["feature"] == "value"
    )
    expected_pnl = 0.1 * 0.02
    assert abs(first_value["marginal_pnl"] - expected_pnl) < 1e-9

    # Date-wise totals should match manual sum of feature contributions
    totals = {}
    for row in ledger:
        totals.setdefault(row["date"], 0.0)
        totals[row["date"]] += row["marginal_pnl"]

    manual_totals = {}
    for date in next_returns:
        pnl = 0.0
        for feature in weights.values():
            weights_for_date = feature.get(date, {})
            for ticker, ret in next_returns[date].items():
                pnl += float(weights_for_date.get(ticker, 0.0)) * float(ret)
        manual_totals[date] = pnl

    for date, pnl in totals.items():
        assert abs(pnl - manual_totals[date]) < 1e-9