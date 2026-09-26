"""Command-line entry point for the portfolio backtest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a JSON run configuration and ensure its root is an object."""
    config_path = Path(path)
    try:
        with config_path.open(encoding="utf-8") as config_file:
            config = json.load(config_file)
    except FileNotFoundError as exc:
        raise ValueError(f"Configuration file not found: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in configuration {config_path}: {exc}") from exc

    if not isinstance(config, dict):
        raise ValueError(f"Configuration must contain a JSON object: {config_path}")
    return config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare 480080/480081 portfolio rebalancing strategies."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/portfolio_backtest.json"),
        help="Path to the JSON run configuration.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Override the output directory configured in the JSON file.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse command-line options; execution is wired in a later checkpoint."""
    build_parser().parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
