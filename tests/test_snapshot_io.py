import os

from src.data.snapshot import load_snapshot, write_snapshot


def test_snapshot_write_and_load(tmp_path):
    prices = {"2024-01-07": {"AAA": 100.0}}
    eps = {"2024-01-07": {"AAA": 1.0}}
    funda = {"AAA": {"gpm": 0.6, "accruals": 0.1, "leverage": 0.2}}
    sector = {"AAA": "Tech"}
    out = write_snapshot(prices, eps, funda, sector, base_dir=str(tmp_path), snap_id="SNAP_TEST")
    assert os.path.isdir(out)
    pb, eb, fb, sm = load_snapshot(out)
    assert pb["2024-01-07"]["AAA"] == 100.0
    assert eb["2024-01-07"]["AAA"] == 1.0
    assert fb["AAA"]["gpm"] == 0.6
    assert sm["AAA"] == "Tech"
