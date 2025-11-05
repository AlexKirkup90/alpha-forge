from src.data.adapter import pivot_prices_to_ticker_series


def test_pivot_prices_to_ticker_series():
    prices = {"2024-01-01": {"A": 10, "B": 20}, "2024-01-08": {"A": 11}}
    series = pivot_prices_to_ticker_series(prices)
    assert series["A"] == [10.0, 11.0]
    assert series["B"] == [20.0, 0.0]


def test_header_tolerance_and_bom(tmp_path):
    p = tmp_path / "eps.csv"
    content = "\ufeffdate,ticker,eps\n2024-01-07,AAA,1.0\n"
    p.write_text(content, encoding="utf-8")
    from src.data.adapter import load_eps_csv

    data = load_eps_csv(str(p))
    assert data["2024-01-07"]["AAA"] == 1.0
