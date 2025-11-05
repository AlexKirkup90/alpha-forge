from src.regime.filters import make_regime_gates


def test_gates_structure():
    bench = {"D1": 0.01, "D2": -0.02, "D3": 0.0}
    factors = ["mom_12_1", "quality_q", "low_vol_26w"]
    gates = make_regime_gates(bench, factors)
    assert set(gates.keys()) == {"D1", "D2", "D3"}
    for d in gates:
        assert set(gates[d].keys()) == set(factors)
