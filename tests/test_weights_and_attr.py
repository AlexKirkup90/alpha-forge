import json
import os

from src.engine.weights_and_attr import run_factor_weighting_and_attr


def test_weights_and_attr_artifacts(tmp_path):
    ic = {
        "mom_12_1": {"D1": 0.1, "D2": 0.0, "D3": -0.2},
        "quality_q": {"D1": 0.05, "D2": 0.06, "D3": 0.07},
    }
    bench = {"D1": 0.01, "D2": -0.02, "D3": 0.0}
    out = run_factor_weighting_and_attr(
        ic,
        bench,
        ["mom_12_1", "quality_q"],
        runs_dir=str(tmp_path),
    )
    base = os.path.join(out, "factors", "weights")
    for f in ["ic_ema.json", "gates.json", "weights.json", "contrib.json", "summary.json"]:
        assert os.path.isfile(os.path.join(base, f))
    data = json.load(open(os.path.join(base, "weights.json"), "r"))
    d1_sum = sum(data["D1"].values())
    assert abs(d1_sum - 1.0) < 1e-6 or d1_sum == 0.0
