"""Minimal command-line runner for the Streamlit stub."""
from __future__ import annotations

import argparse
import runpy
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="streamlit")
    subparsers = parser.add_subparsers(dest="command")
    run_parser = subparsers.add_parser("run", help="Run a Streamlit script")
    run_parser.add_argument("script", help="Path to the Python script")
    args = parser.parse_args(argv)

    if args.command != "run":
        parser.print_help()
        return 1

    script_path = Path(args.script)
    if not script_path.exists():
        print(f"streamlit stub: script not found: {script_path}")
        return 1

    runpy.run_path(str(script_path), run_name="__main__")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
