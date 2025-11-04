import json
from pathlib import Path

from src.telemetry.hashing import code_sha, hash_config
from src.telemetry.run_registry import RunRecord, save_run


def test_hash_config_deterministic():
    cfg = {"b": 2, "a": 1}
    assert hash_config(cfg) == hash_config({"a": 1, "b": 2})


def test_code_sha_returns_string():
    sha = code_sha()
    assert isinstance(sha, str)
    assert sha


def test_save_run_writes_files(tmp_path: Path):
    record = RunRecord(
        run_id="test-run",
        code_sha="abc123",
        data_snapshot_id="snap-1",
        config_hash="cfg-xyz",
        started_at="2024-01-01T00:00:00Z",
        ended_at="2024-01-01T01:00:00Z",
        metrics={"Sharpe": 1.2},
        paths={"ledger": "ledger.parquet"},
    )
    run_dir = Path(save_run(record, base_dir=tmp_path))
    assert run_dir.exists()
    with (run_dir / "run.json").open() as f:
        payload = json.load(f)
    assert payload["run_id"] == "test-run"
    with (run_dir / "metrics.json").open() as f:
        metrics = json.load(f)
    assert metrics["Sharpe"] == 1.2
    with (run_dir / "hashes.json").open() as f:
        hashes = json.load(f)
    assert hashes["code_sha"] == "abc123"
