"""Command-line entry point for the portfolio backtest."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from asset_quant.backtest.costs import StampDutyRate, TransactionCostModel
from asset_quant.backtest.engine import run_backtest
from asset_quant.data.market_data import load_market_data
from asset_quant.metrics import default_metrics
from asset_quant.reporting import write_report
from asset_quant.strategies.periodic import (
    PeriodicRebalanceStrategy,
    RebalancePeriod,
    allocation_grid,
)


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


def _required_object(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Configuration field '{key}' must be an object")
    return value


def _build_cost_model(config: dict[str, Any]) -> TransactionCostModel:
    costs = _required_object(config, "costs")
    schedule = costs.get("stamp_duty_schedule")
    if not isinstance(schedule, list) or not schedule:
        raise ValueError("Configuration field 'costs.stamp_duty_schedule' must be a non-empty list")
    try:
        rates = [
            StampDutyRate(
                effective_from=date.fromisoformat(item["effective_from"]),
                rate=float(item["rate_on_sales"]),
            )
            for item in schedule
            if isinstance(item, dict)
        ]
        if len(rates) != len(schedule):
            raise ValueError("each stamp-duty entry must be an object")
        return TransactionCostModel(
            commission_rate=costs["commission_rate_per_side"],
            slippage_rate=costs["slippage_rate_per_side"],
            stamp_duty_schedule=rates,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid transaction-cost configuration: {exc}") from exc


def _risk_free_rate(config: dict[str, Any]) -> float:
    rate = config.get("risk_free_rate_annual", 0.0)
    if not isinstance(rate, (int, float)) or isinstance(rate, bool):
        raise ValueError("Configuration field 'risk_free_rate_annual' must be numeric")
    if not (-1 < rate < float("inf")):
        raise ValueError("Configuration field 'risk_free_rate_annual' must be finite and greater than -1")
    return float(rate)


def _serialize_stamp_duty_schedule(cost_model: TransactionCostModel) -> list[dict[str, Any]]:
    schedule = cost_model.stamp_duty_schedule
    return [
        {
            "effective_from": item.effective_from.isoformat(),
            "effective_through": (
                (schedule[index + 1].effective_from - timedelta(days=1)).isoformat()
                if index + 1 < len(schedule)
                else None
            ),
            "rate_on_sales": item.rate,
        }
        for index, item in enumerate(schedule)
    ]


def run_configured_backtest(
    config_path: str | Path,
    output_dir: str | Path | None = None,
) -> Path:
    """Execute the full allocation/calendar grid and write one run directory."""
    config_path = Path(config_path)
    config = load_config(config_path)
    data = _required_object(config, "data")
    sources = _required_object(data, "sources")
    if set(sources) != {"480080", "480081"}:
        raise ValueError("Configuration field 'data.sources' must contain exactly 480080 and 480081")
    if any(not isinstance(source, str) or not source.strip() for source in sources.values()):
        raise ValueError("Each data source path must be a non-empty string")
    risk_free_rate = _risk_free_rate(config)
    cost_model = _build_cost_model(config)
    prices = load_market_data(sources)
    dates = [timestamp.date() for timestamp in prices.index]

    results: list[dict[str, Any]] = []
    for period in RebalancePeriod:
        for weights in allocation_grid():
            strategy = PeriodicRebalanceStrategy(period=period, target_weights=weights)
            frame = run_backtest(prices, strategy, cost_model)
            metric_values = default_metrics(risk_free_rate_annual=risk_free_rate).calculate_all(
                dates=dates,
                returns=frame["portfolio_return"].tolist(),
                nav=frame["nav"].tolist(),
            )
            results.append(
                {
                    "rebalance_period": period.value,
                    "weight_480080_pct": weights["480080"] * 100,
                    "weight_480081_pct": weights["480081"] * 100,
                    "start_date": dates[0].isoformat(),
                    "end_date": dates[-1].isoformat(),
                    "source_480080": str(sources["480080"]),
                    "source_480081": str(sources["480081"]),
                    "initial_capital": 1.0,
                    "buy_notional": float(frame["buy_notional"].sum()),
                    "sell_notional": float(frame["sell_notional"].sum()),
                    "commission": float(frame["commission"].sum()),
                    "slippage": float(frame["slippage"].sum()),
                    "stamp_duty": float(frame["stamp_duty"].sum()),
                    "transaction_cost": float(frame["transaction_cost"].sum()),
                    "commission_rate_per_side": cost_model.commission_rate,
                    "slippage_rate_per_side": cost_model.slippage_rate,
                    "stamp_duty_schedule": json.dumps(
                        _serialize_stamp_duty_schedule(cost_model), separators=(",", ":")
                    ),
                    "risk_free_rate_annual": risk_free_rate,
                    **metric_values,
                }
            )

    configured_output = output_dir if output_dir is not None else config.get("output_dir", "outputs")
    if not isinstance(configured_output, (str, Path)) or not str(configured_output).strip():
        raise ValueError("Configuration field 'output_dir' must be a non-empty path")
    run_id = datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%S_%fZ")
    run_dir = Path(configured_output) / run_id
    assumptions = {
        "sources": sources,
        "commission_rate_per_side": cost_model.commission_rate,
        "slippage_rate_per_side": cost_model.slippage_rate,
        "stamp_duty_schedule": _serialize_stamp_duty_schedule(cost_model),
        "risk_free_rate_annual": risk_free_rate,
        "start_capital": 1.0,
    }
    write_report(
        results,
        run_dir,
        assumptions=assumptions,
        data_start=dates[0].isoformat(),
        data_end=dates[-1].isoformat(),
    )
    return run_dir


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
    """Run the configured backtest and print its artifact directory."""
    args = build_parser().parse_args(argv)
    try:
        run_dir = run_configured_backtest(args.config, args.output_dir)
    except (ValueError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    print(f"Backtest report: {run_dir / 'report.md'}")
    print(f"Metrics CSV: {run_dir / 'metrics.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
