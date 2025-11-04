from src.portfolio.constraints import cap_by_name, cap_by_sector


def test_cap_by_name_renormalizes():
    weights = {"A": 0.9, "B": 0.1}
    capped = cap_by_name(weights, cap=0.5)
    assert all(abs(v) <= 0.5 + 1e-12 for v in capped.values())
    assert abs(sum(abs(v) for v in capped.values()) - 1.0) < 1e-9


def test_cap_by_sector_limits_sector_exposure():
    weights = {"A": 0.6, "B": 0.4, "C": 0.0}
    sector = {"A": "S1", "B": "S1", "C": "S2"}
    capped = cap_by_sector(weights, sector, cap=0.7)
    s1 = abs(capped["A"]) + abs(capped["B"])
    assert s1 <= 0.7 + 1e-12
