import json
import os

from src.engine.factor_telemetry import run_factor_ic_telemetry


def test_factor_telemetry_artifacts(tmp_path):
    dates = [f"2024-01-{7 + i * 7:02d}" for i in range(20)]
    prices = {d: {"A": 100 + i, "B": 50 + 0.5 * i, "C": 80 + 0.1 * i} for i, d in enumerate(dates)}
    eps = {d: {"A": 1.0 + 0.01 * i, "B": 0.8 - 0.002 * i, "C": 0.6 + 0.001 * i} for i, d in enumerate(dates)}
    funda = {
        "A": {"gpm": 0.6, "accruals": 0.1, "leverage": 0.2},
        "B": {"gpm": 0.4, "accruals": 0.2, "leverage": 0.35},
        "C": {"gpm": 0.55, "accruals": 0.12, "leverage": 0.25},
    }
    outdir = run_factor_ic_telemetry(
        prices,
        eps,
        funda,
        ["mom_12_1", "eps_rev_4_12"],
        runs_dir=str(tmp_path),
    )
    assert os.path.isdir(outdir)
    factors_dir = os.path.join(outdir, "factors")
    assert os.path.isdir(factors_dir)
    for f in ["mom_12_1", "eps_rev_4_12"]:
        fdir = os.path.join(factors_dir, f)
        assert os.path.isfile(os.path.join(fdir, "ic_series.json"))
        assert os.path.isfile(os.path.join(fdir, "ic_summary.json"))
        with open(os.path.join(fdir, "ic_summary.json"), encoding="utf-8") as fh:
            summary = json.load(fh)
        assert "n" in summary and "ic_mean" in summary
