"""Write the Chinese overview, comparison charts, and detailed CSV output."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from asset_quant.reporting.charts_svg import write_comparison_charts


_PERIOD_LABELS = {
    "weekly": "周度",
    "monthly": "月度",
    "quarterly": "季度",
    "semiannual": "半年度",
    "annual": "年度",
}
_LEADERS = (
    ("annualized_return", "最高年化收益"),
    ("sharpe_ratio", "最高夏普"),
    ("maximum_drawdown", "最浅最大回撤"),
)


def _format_metric(name: str, value: Any) -> str:
    number = float(value)
    if name in {"annualized_return", "maximum_drawdown"}:
        return f"{number:.2%}"
    return f"{number:.3f}"


def _leader_table(results: Sequence[Mapping[str, Any]]) -> list[str]:
    lines = [
        "| 指标 | 再平衡周期 | 480080 | 480081 | 指标值 |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for metric, label in _LEADERS:
        leader = max(results, key=lambda row: float(row[metric]))
        period = _PERIOD_LABELS.get(
            str(leader["rebalance_period"]), str(leader["rebalance_period"])
        )
        lines.append(
            f"| {label} | {period} | {float(leader['weight_480080_pct']):g}% "
            f"| {float(leader['weight_480081_pct']):g}% "
            f"| {_format_metric(metric, leader[metric])} |"
        )
    return lines


def write_report(
    results: Sequence[Mapping[str, Any]],
    output_dir: str | Path,
    *,
    assumptions: Mapping[str, Any],
    data_start: str,
    data_end: str,
) -> tuple[Path, Path]:
    """Write a concise Chinese Markdown report and the complete metrics CSV."""
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
        "# 480080 / 480081 组合回测概览",
        "",
        f"样本区间：**{data_start} 至 {data_end}**。本次对 11 档配置比例与 5 种再平衡周期进行组合比较，共 **{len(results)} 种配置**。",
        "",
        "## 核心发现",
        "",
        "下表列出三个单项指标的领先组合，供快速比较。它们分别代表单一指标的结果，不构成投资建议，也不表示某个组合在所有目标下都最优。",
        "",
    ]
    if results:
        lines.extend(_leader_table(results))
    else:
        lines.append("没有可展示的结果行。")
    lines.extend(
        [
            "",
            "## 全部配置对比",
            "",
            "热力图覆盖 11 档 480080 比例 × 5 种周期；颜色从红到绿表示该项指标从低到高。散点图中的颜色代表再平衡周期，每个点代表一种配置。",
            "",
        ]
    )
    if results:
        lines.extend(
            [
                "### 配置比例与周期指标",
                "",
                "![配置与周期指标热力图](performance_heatmaps.svg)",
                "",
                "### 收益与回撤",
                "",
                "横轴为年化收益率，纵轴为最大回撤；回撤越深，点越靠下。图中标注年化收益率、夏普比率和最大回撤的各自领先组合。",
                "",
                "![收益与回撤散点图](risk_return.svg)",
                "",
            ]
        )
    lines.extend(
        [
            "## 回测设置",
            "",
            f"- 数据区间：{data_start} 至 {data_end}；两个指数只使用日期交集。",
            f"- 比较范围：{len(results)} 种配置；报告中不逐行展开，完整结果保存在 CSV。",
            "- 480080 与 480081 是指数序列，仅作为历史代理数据，并非可直接买卖的产品。",
            "- 佣金、滑点和印花税是可编辑的假设值，不是特定基金、券商、账户或实际交易的报价。指数回测结果为假设性结果。",
            "",
            "### 本次假设",
            "",
            "```json",
            json.dumps(dict(assumptions), ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## 指标定义",
            "",
            "- 年化收益率：按经过的日历年数计算几何年化收益（每年 365.2425 天），并将初始买入成本计入相对初始资金的回报。",
            "- 年化波动率：日收盘到收盘收益率的总体标准差 × √252。",
            "- 最大回撤：相对初始资金或后续净值峰值的最大跌幅。",
            "- 最大回撤修复时间：从最大回撤前的峰值到净值重新达到该峰值所经过的交易观测数；样本结束仍未修复时，计至样本最后日期，并可在 CSV 中查看修复状态。",
            "- 夏普比率：日超额收益均值 ÷ 日收益标准差 × √252；年化无风险利率按 252 个交易日折算。初始买入成本不是日收盘到收盘收益，因此不计入波动率和夏普计算。",
            "",
            "## 输出文件",
            "",
            f"- `metrics.csv`：每种配置一行，共 {len(results)} 行；包含全部已注册指标、配置比例、日期、买入/卖出金额、佣金、滑点、印花税及成本假设字段。",
        ]
    )
    if results:
        lines.extend(
            [
                "- `performance_heatmaps.svg`：年化收益率、夏普比率和最大回撤热力图。",
                "- `risk_return.svg`：55 种组合的年化收益率与最大回撤散点图。",
            ]
        )
    lines.extend(["- `report.md`：本概览及回测假设说明。", ""])
    report_path.write_text("\n".join(lines), encoding="utf-8")
    if results:
        write_comparison_charts(results, destination)
    return report_path, csv_path
