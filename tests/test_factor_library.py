import numpy as np
import pandas as pd

from src.factors.library import (
    factor_low_vol_26w,
    factor_mom_12_1,
    factor_mom_velocity,
)


def _toy_prices() -> pd.DataFrame:
    idx = pd.Index([f"D{i:02d}" for i in range(60)])
    cols = ["A", "B", "C"]
    base = pd.DataFrame(
        {
            "A": 100 + np.arange(60),
            "B": 50 + 0.5 * np.arange(60),
            "C": 80 + np.sin(np.arange(60) / 4.0) * 2.0,
        },
        index=idx,
    )
    return base


def test_mom_12_1_shape_and_finiteness():
    px = _toy_prices()
    f = factor_mom_12_1(px)
    assert f.shape == px.shape
    assert np.isfinite(f.fillna(0.0).to_numpy()).all()


def test_mom_velocity_outputs():
    px = _toy_prices()
    f = factor_mom_velocity(px)
    assert f.shape == px.shape


def test_low_vol_standardization():
    px = _toy_prices()
    f = factor_low_vol_26w(px)
    means = f.mean(axis=1).fillna(0.0)
    assert (means.abs() < 1e-6).all()
