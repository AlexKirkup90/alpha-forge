from src.engine.weekly import WeeklyParams, run_weekly
import os


def test_weekly_engine_creates_run(tmp_path):
    prices = {
        "AAA": [10, 11, 12, 13, 14, 15],
        "BBB": [10, 9, 9.5, 9.7, 9.9, 10.2],
        "CCC": [5, 5.1, 5.2, 5.3, 5.4, 5.5],
    }
    eps = {
        "AAA": [1, 1, 1, 1.1, 1.2, 1.25],
        "BBB": [1, 1, 0.98, 0.97, 0.96, 0.95],
        "CCC": [0.5, 0.5, 0.51, 0.52, 0.53, 0.54],
    }
    fundamentals = {
        "AAA": {"gpm": 0.6, "accruals": 0.1, "leverage": 0.2},
        "BBB": {"gpm": 0.3, "accruals": 0.2, "leverage": 0.4},
        "CCC": {"gpm": 0.55, "accruals": 0.12, "leverage": 0.25},
    }
    sector = {"AAA": "Tech", "BBB": "Finance", "CCC": "Tech"}
    next_ret = {"AAA": 0.02, "BBB": -0.01, "CCC": 0.015}
    bench = {"SPY": 0.008}

    out = run_weekly(
        prices,
        eps,
        fundamentals,
        sector,
        next_ret,
        bench,
        data_snapshot_id="SNAP",
        params=WeeklyParams(top_k=2),
        runs_dir=str(tmp_path),
    )
    assert os.path.isdir(out)
    assert os.path.isfile(os.path.join(out, "metrics.json"))
    assert os.path.isfile(os.path.join(out, "config.json"))
