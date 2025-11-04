from src.signals.orthogonalize import sector_zscore


def test_sector_zscore_centers_sectors():
    scores = {"A": 1, "B": 2, "C": 3, "D": 10}
    sector = {"A": "S1", "B": "S1", "C": "S1", "D": "S2"}
    z = sector_zscore(scores, sector)
    assert z["D"] == 0.0
    mean_s1 = sum(z[k] for k in ("A", "B", "C")) / 3.0
    assert abs(mean_s1) < 1e-9
