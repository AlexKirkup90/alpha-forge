def test_yfinance_provider_instantiates_without_key():
    from src.data.providers.yf_provider import YFinanceProvider

    p = YFinanceProvider()
    assert p is not None
