# Run Registry

Each backtest/run writes an artifact under /runs/YYYY-MM-DD/{run_id}/ containing:
- run.json (metadata)
- metrics.json (headline metrics)
- ledger.parquet (alpha ledger rows)
- config.json (exact parameters)
- hashes.json (code_sha, config_hash, data_snapshot_id)

**run.json fields**
- run_id (uuid)
- started_at, ended_at (ISO8601)
- code_sha (git HEAD or "dirty")
- data_snapshot_id (string you supply)
- config_hash (stable json hash)
- metrics: dict of key numbers (Sharpe, Sortino, MaxDD, Alpha_weekly, CAGR_gross, CAGR_net, Turnover, Costs_bps_week)
- paths: local file paths to artifacts
