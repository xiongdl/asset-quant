"""Write human-readable and machine-readable backtest comparisons."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Mapping, Sequence


def write_report(
    results: Sequence[Mapping[str, Any]],
    output_dir: str | Path,
    *,
    assumptions: Mapping[str, Any],
    data_start: str,
    data_end: str,
) -> tuple[Path, Path]:
    """Write the complete result grid to `report.md` and `metrics.csv`."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    report_path = destination / "report.md"
    csv_path = destination / "metrics.csv"
    fields = list(results[0].keys()) if results else []

    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        if fields:
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="raise")
            writer.writeheader()
            writer.writerows(results)

    lines = [
        "# 480080 / 480081 Portfolio Backtest",
        "",
        f"- Data range: {data_start} to {data_end}",
        f"- Configurations evaluated: {len(results)}",
        "- Inputs are index series used as historical proxies; they are not directly investable funds.",
        "- Costs are editable hypothetical assumptions, not quotes for a specific product or account.",
        "- This comparison does not select a universally best portfolio; suitability depends on the investor's objective.",
        "",
        "## Assumptions",
        "",
        "```json",
        json.dumps(dict(assumptions), ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Metric definitions",
        "",
        "- Annualized return: geometric CAGR over elapsed calendar years (365.2425 days per year), including initial buy costs relative to starting capital.",
        "- Annualized volatility: sample standard deviation of close-to-close daily returns, multiplied by √252.",
        "- Maximum drawdown: deepest decline from starting capital or a subsequent NAV peak.",
        "- Maximum drawdown recovery days: trading observations from the preceding peak until recovery; if unrecovered, elapsed observations through the final date.",
        "- Maximum drawdown recovered: whether NAV regained that peak within the sample.",
        "- Sharpe ratio: mean daily excess return divided by daily return standard deviation, multiplied by √252; annual risk-free rate is divided by 252.",
        "- The initial buy-cost entry is excluded from daily volatility and Sharpe calculations because it is not a close-to-close return.",
        "",
        "## Comparison",
        "",
    ]
    if not results:
        lines.extend(["No result rows were supplied.", ""])
    else:
        table_fields = fields
        lines.append("| " + " | ".join(table_fields) + " |")
        lines.append("| " + " | ".join("---" for _ in table_fields) + " |")
        for row in results:
            lines.append("| " + " | ".join(str(row[field]) for field in table_fields) + " |")
        lines.append("")
    lines.extend(
        [
            "## Costs and output files",
            "",
            "The CSV includes per-case total buy/sell notional and summed commission, slippage, stamp duty, and transaction costs, together with configured cost rates and the effective-date tax schedule.",
            "",
            "- `metrics.csv`: one row per allocation and rebalance period.",
            "- `report.md`: assumptions, definitions, and all result rows.",
            "",
        ]
    )
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path, csv_path
