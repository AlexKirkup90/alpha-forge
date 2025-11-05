import numpy as np
import pandas as pd

from src.metrics.ic import ic_series, ic_summary


def test_ic_series_positive_for_monotonic_relation():
    idx = pd.Index([f"D{i:02d}" for i in range(10)])
    cols = ["A", "B", "C", "D", "E"]
    base = np.tile(np.arange(len(cols)), (len(idx), 1))
    scores = pd.DataFrame(base, index=idx, columns=cols)
    next_ret = pd.DataFrame(base, index=idx, columns=cols)
    ics = ic_series(scores, next_ret)
    assert (ics.dropna() > 0.95).all()


def test_ic_summary_fields():
    s = pd.Series([0.1, 0.2, -0.1, 0.0, 0.05])
    summary = ic_summary(s)
    assert set(summary.keys()) == {"n", "ic_mean", "ic_std", "ir", "tstat"}
    assert summary["n"] == 5
