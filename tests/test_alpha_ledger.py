import pandas as pd

from src.ledger.alpha_ledger import compute_feature_marginals


def test_compute_feature_marginals_basic():
    dates = pd.Index(["2023-01-01", "2023-01-08"])
    weights = {
        "value": pd.DataFrame(
            {
                "AAA": [0.1, 0.0],
                "BBB": [0.0, 0.2],
            },
            index=dates,
        ),
        "momentum": pd.DataFrame(
            {
                "AAA": [0.0, -0.1],
                "BBB": [0.05, 0.0],
            },
            index=dates,
        ),
    }
    next_returns = pd.DataFrame(
        {
            "AAA": [0.02, -0.01],
            "BBB": [0.01, 0.03],
        },
        index=dates,
    )

    ledger = compute_feature_marginals(weights, next_returns)
    assert len(ledger) == 4
    first_value = ledger[(ledger["date"] == "2023-01-01") & (ledger["feature"] == "value")].iloc[0]
    expected_pnl = 0.1 * 0.02
    assert abs(first_value["marginal_pnl"] - expected_pnl) < 1e-9
    total_pnl = ledger.groupby("date")["marginal_pnl"].sum()
    manual_total = (
        weights["value"] * next_returns + weights["momentum"] * next_returns
    ).sum(axis=1)
    pd.testing.assert_series_equal(total_pnl.sort_index(), manual_total.sort_index(), check_names=False)
