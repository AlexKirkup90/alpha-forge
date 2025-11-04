from src.portfolio.governor import compute_drawdown, governor_signal


def test_compute_drawdown_monotonic():
    equity = [1.0, 1.1, 1.2, 1.1]
    dd = compute_drawdown(equity)
    assert dd[0] == 0.0
    assert dd[-1] > 0


def test_governor_reduces_exposure_in_dd():
    equity = [1, 1.05, 1.1, 1.0, 0.9, 0.85, 0.86, 0.9, 0.95, 1.0]
    vol = [0.15] * len(equity)
    signal = governor_signal(equity, vol, dd_soft=0.05, dd_hard=0.2)
    assert min(signal) < 1.0
    assert signal[-1] >= signal[-2]
