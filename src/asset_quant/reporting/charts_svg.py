"""Dependency-free SVG charts for the complete portfolio comparison grid."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any, Mapping, Sequence


_PERIOD_ORDER = ("weekly", "monthly", "quarterly", "semiannual", "annual")
_PERIOD_LABELS = {
    "weekly": "周度",
    "monthly": "月度",
    "quarterly": "季度",
    "semiannual": "半年度",
    "annual": "年度",
}
_PERIOD_COLORS = {
    "weekly": "#2864dc",
    "monthly": "#e0791b",
    "quarterly": "#16866b",
    "semiannual": "#9b55aa",
    "annual": "#c13c4a",
}
_METRICS = (
    ("annualized_return", "年化收益率", "%"),
    ("sharpe_ratio", "夏普比率", ""),
    ("maximum_drawdown", "最大回撤", "%"),
)


def _escape(value: Any) -> str:
    return escape(str(value), quote=True)


def _rows_by_grid(results: Sequence[Mapping[str, Any]]) -> dict[tuple[float, str], Mapping[str, Any]]:
    return {
        (float(row["weight_480080_pct"]), str(row["rebalance_period"])): row
        for row in results
    }


def _interpolate_color(position: float, *, higher_is_better: bool = True) -> str:
    if not higher_is_better:
        position = 1.0 - position
    low, high = (197, 70, 70), (38, 142, 106)
    # Keep the middle of the scale light so cell labels remain easy to read.
    if position < 0.5:
        start, end, fraction = low, (244, 220, 154), position * 2
    else:
        start, end, fraction = (244, 220, 154), high, (position - 0.5) * 2
    channels = [round(a + (b - a) * fraction) for a, b in zip(start, end)]
    return "#" + "".join(f"{channel:02x}" for channel in channels)


def _heatmap_svg(results: Sequence[Mapping[str, Any]]) -> str:
    width, height = 1080, 880
    table_x, table_y = 250, 86
    cell_width, cell_height = 148, 23
    panel_height = 270
    pieces = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        "<title id=\"title\">480080 / 480081 策略指标热力图</title>",
        "<desc id=\"desc\">按 480080 配置比例和再平衡周期展示 55 种组合的年化收益率、夏普比率和最大回撤。颜色由红到绿代表数值由低到高。</desc>",
        "<style>text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#182230}.panel-title{font-size:21px;font-weight:700}.axis{font-size:14px}.cell-label{font-size:13px;font-weight:600}.grid{stroke:#fff;stroke-width:2}</style>",
    ]
    grid = _rows_by_grid(results)
    for metric_index, (metric, title, unit) in enumerate(_METRICS):
        panel_y = 12 + metric_index * panel_height
        values = [float(row[metric]) for row in results]
        minimum, maximum = min(values), max(values)
        span = maximum - minimum or 1.0
        pieces.append(f'<g class="heatmap-panel" data-metric="{_escape(metric)}">')
        pieces.append(f'<text class="panel-title" x="28" y="{panel_y + 28}">{_escape(title)}</text>')
        pieces.append(f'<text class="axis" x="28" y="{panel_y + 51}">480080 比例 ↓　周期 →</text>')
        for column, period in enumerate(_PERIOD_ORDER):
            x = table_x + column * cell_width + cell_width / 2
            label = _PERIOD_LABELS[period]
            pieces.append(f'<text class="axis" text-anchor="middle" x="{x}" y="{panel_y + 74}">{_escape(label)}</text>')
        for row_index, weight in enumerate(range(100, -1, -10)):
            y = panel_y + table_y + row_index * cell_height
            pieces.append(f'<text class="axis" text-anchor="end" x="{table_x - 12}" y="{y + 16}">{weight}%</text>')
            for column, period in enumerate(_PERIOD_ORDER):
                data = grid[(float(weight), period)]
                value = float(data[metric])
                position = (value - minimum) / span
                fill = _interpolate_color(position)
                x = table_x + column * cell_width
                display = f"{value * 100:.1f}%" if unit == "%" else f"{value:.2f}"
                pieces.append(
                    f'<g><rect class="heatmap-cell grid" x="{x}" y="{y}" width="{cell_width}" height="{cell_height}" fill="{fill}" data-weight="{weight}" data-period="{_escape(period)}" data-value="{value:.12g}" data-metric="{_escape(metric)}"/><text class="cell-label" text-anchor="middle" x="{x + cell_width / 2}" y="{y + 16}">{display}</text></g>'
                )
        pieces.append("</g>")
    pieces.append("</svg>")
    return "\n".join(pieces)


def _leader_key(row: Mapping[str, Any], metric: str) -> tuple[float, float, str]:
    return (
        float(row[metric]),
        -float(row["weight_480080_pct"]),
        str(row["rebalance_period"]),
    )


def _risk_return_svg(results: Sequence[Mapping[str, Any]]) -> str:
    width, height = 1160, 650
    left, top, plot_width, plot_height = 92, 78, 730, 420
    right, bottom = left + plot_width, top + plot_height
    returns = [float(row["annualized_return"]) for row in results]
    drawdowns = [float(row["maximum_drawdown"]) for row in results]
    min_return, max_return = min(returns), max(returns)
    return_span = max_return - min_return or 1.0
    min_drawdown, max_drawdown = min(drawdowns), max(drawdowns)
    drawdown_span = max_drawdown - min_drawdown or 1.0

    def point(row: Mapping[str, Any]) -> tuple[float, float]:
        x_value = float(row["annualized_return"])
        y_value = float(row["maximum_drawdown"])
        x = left + (x_value - min_return) / return_span * plot_width
        # Deep, negative drawdowns appear toward the bottom of the chart.
        y = top + (max_drawdown - y_value) / drawdown_span * plot_height
        return x, y

    pieces = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        "<title id=\"title\">年化收益与最大回撤对比</title>",
        "<desc id=\"desc\">55 种组合的年化收益率和最大回撤散点图，颜色区分再平衡周期，并标注三项指标领跑组合。</desc>",
        "<style>text{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#182230}.heading{font-size:21px;font-weight:700}.axis{font-size:14px}.legend{font-size:14px}.leader-label{font-size:14px;font-weight:600}.gridline{stroke:#e1e6ed;stroke-width:1}.case-point{stroke:#fff;stroke-width:1.5}</style>",
        '<text class="heading" x="28" y="35">收益与回撤：每个点代表一种配置 × 周期</text>',
    ]
    for index in range(5):
        x = left + plot_width * index / 4
        value = min_return + return_span * index / 4
        pieces.append(f'<line class="gridline" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{bottom}"/>')
        pieces.append(f'<text class="axis" text-anchor="middle" x="{x:.1f}" y="{bottom + 24}">{value * 100:.1f}%</text>')
        y = top + plot_height * index / 4
        drawdown = max_drawdown - drawdown_span * index / 4
        pieces.append(f'<line class="gridline" x1="{left}" y1="{y:.1f}" x2="{right}" y2="{y:.1f}"/>')
        pieces.append(f'<text class="axis" text-anchor="end" x="{left - 10}" y="{y + 5:.1f}">{drawdown * 100:.1f}%</text>')
    pieces.append(f'<text class="axis" text-anchor="middle" x="{left + plot_width / 2}" y="{bottom + 54}">年化收益率</text>')
    pieces.append(f'<text class="axis" text-anchor="middle" transform="translate(25 {top + plot_height / 2}) rotate(-90)">最大回撤（越深越靠下）</text>')
    for row in results:
        x, y = point(row)
        period = str(row["rebalance_period"])
        weight = float(row["weight_480080_pct"])
        color = _PERIOD_COLORS.get(period, "#667085")
        pieces.append(
            f'<circle class="case-point" cx="{x:.2f}" cy="{y:.2f}" r="5.5" fill="{color}" data-period="{_escape(period)}" data-weight="{weight:g}" data-return="{float(row["annualized_return"]):.12g}" data-drawdown="{float(row["maximum_drawdown"]):.12g}"/>'
        )
    leader_metrics = (
        ("annualized_return", "最高年化收益"),
        ("sharpe_ratio", "最高夏普"),
        ("maximum_drawdown", "最浅最大回撤"),
    )
    for index, (metric, label) in enumerate(leader_metrics):
        leader = max(results, key=lambda row: _leader_key(row, metric))
        x, y = point(leader)
        label_y = 148 + index * 96
        period = _PERIOD_LABELS.get(str(leader["rebalance_period"]), str(leader["rebalance_period"]))
        weight = float(leader["weight_480080_pct"])
        callout = f"{label}：{period}，480080 {weight:g}%"
        pieces.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="9" fill="none" stroke="#182230" stroke-width="2.5"/>')
        pieces.append(f'<path d="M {x:.2f} {y:.2f} L {right + 18} {label_y - 5} L 865 {label_y - 5}" fill="none" stroke="#667085" stroke-width="1.3"/>')
        pieces.append(f'<text class="leader-label" data-leader="{_escape(metric)}" x="875" y="{label_y}">{_escape(callout)}</text>')
    legend_x, legend_y = left, height - 34
    for index, period in enumerate(_PERIOD_ORDER):
        x = legend_x + index * 156
        pieces.append(f'<circle cx="{x}" cy="{legend_y - 5}" r="6" fill="{_PERIOD_COLORS[period]}"/>')
        pieces.append(f'<text class="legend" x="{x + 12}" y="{legend_y}">{_PERIOD_LABELS[period]}</text>')
    pieces.append("</svg>")
    return "\n".join(pieces)


def write_comparison_charts(
    results: Sequence[Mapping[str, Any]], output_dir: str | Path
) -> tuple[Path, Path]:
    """Write the heatmap and risk-return SVGs and return their paths."""
    if not results:
        raise ValueError("At least one result row is required to draw comparison charts")
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    heatmap_path = destination / "performance_heatmaps.svg"
    scatter_path = destination / "risk_return.svg"
    heatmap_path.write_text(_heatmap_svg(results), encoding="utf-8")
    scatter_path.write_text(_risk_return_svg(results), encoding="utf-8")
    return heatmap_path, scatter_path
