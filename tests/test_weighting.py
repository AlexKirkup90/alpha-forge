from src.signals.weighting import clamp_and_normalize_weights, compute_ic_ema_series


def test_clamp_and_normalize():
    w = clamp_and_normalize_weights({"a": -0.1, "b": 0.0, "c": 0.2})
    assert abs(sum(w.values()) - 1.0) < 1e-9
    assert w["a"] == 0.0 and w["b"] == 0.0 and w["c"] == 1.0


def test_ic_ema_progression():
    series = {"f": {"D1": 0.1, "D2": 0.3, "D3": -0.1}}
    ema = compute_ic_ema_series(series, alpha=0.5)["D2"]["f"]
    assert 0.19 < ema < 0.21
