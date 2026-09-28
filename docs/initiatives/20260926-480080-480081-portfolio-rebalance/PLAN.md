# Implementation Plan: Modular 480080/480081 Portfolio Backtest

## Overview

Implement the approved CLI backtest and report-visualization update in nine task units grouped into five Default execution checkpoints. Checkpoints 1–4 are complete through commit `ab8385c`. Checkpoint 5 restructures the report around concise Chinese findings and dependency-free SVG charts. The raw source workbooks remain unchanged.

## Architecture decisions

- Use a `src/asset_quant` Python package. `requirements.txt` includes the editable project install so the approved install command makes `python -m asset_quant.cli` work from the repository root.
- Keep data reading and date alignment in `data/market_data.py`; open the existing OOXML workbooks with pandas/openpyxl despite their `.xls` suffixes.
- Model target-weight behavior through a strategy contract and keep calendar schedule generation in the periodic strategy module.
- Let the backtest engine own portfolio value, daily returns, drifted weights, and rebalance timing. Delegate all fee calculation to a cost model that takes buy/sell turnover and date.
- Apply close-date rebalances after that date's market return, with target weights active on the next common trading day. Charge initial buy-side costs and rebalance costs; apply stamp duty only to sales using the configured effective-date schedule.
- Compute metrics after costs through a registry, separate from the strategy and engine. This provides a clear extension point for new metrics and strategies.
- Generate a run-specific `report.md` and `metrics.csv` under `outputs/`; do not commit generated outputs or edit raw data.
- Generate two standalone SVGs from the metric grid: a three-panel heatmap for return/Sharpe/drawdown and a risk-return scatter for all cases. Embed both from the Chinese Markdown report.
- Keep chart generation in a small reporting module using the standard library; avoid a new chart dependency and keep all 55 detailed rows in CSV.

## Task sequence and checkpoints

### Checkpoint 1: Data foundation

- Task 1: Package skeleton, dependency declaration, and run configuration.
- Task 2: Validated source data ingestion and common-date alignment.

**Exit criteria:** The configured two-index dataset loads as a clean, chronological common-date series, and malformed/missing input is rejected with actionable errors.

### Checkpoint 2: Strategy and portfolio accounting

- Task 3: Strategy contract and periodic rebalance schedule generation.
- Task 4: Portfolio engine and configurable turnover cost model.

**Exit criteria:** Weekly through annual schedules are deterministic, 11 complementary allocations can be simulated without lookahead, and one-way tax/turnover costs are applied on the correct side and date.

### Checkpoint 3: Metrics and reporting

- Task 5: Metric interface/registry and five required metric implementations.
- Task 6: CLI orchestration and report/CSV generation for all 55 cases.

**Exit criteria:** A configured run emits all 55 result rows with metric definitions, data range, and fee assumptions in a readable report.

### Checkpoint 4: User-facing instructions and acceptance

- Task 7: Document setup/configuration/output behavior and run the approved end-to-end acceptance checks against repository data.

**Exit criteria:** A new user can create the environment, configure assumptions, run the CLI, understand the outputs, and see the verified 55-case result.

### Checkpoint 5: Readable report and charts

- Task 8: Build accessible SVG charts for metric heatmaps and risk-return comparisons.
- Task 9: Rework report composition into a Chinese overview with metric leaders and embedded charts, then regenerate and visually inspect the full-data report.

**Exit criteria:** The report opens with a concise summary, charts expose the full 11×5 comparison grid, full-detail results remain in CSV, and generated SVGs render without clipping or unreadable labels.

## Verification approach

- Each task runs its focused checks before its task-level commit.
- Checkpoint 1 verifies package/config setup plus loading, normalization, overlap, and validation failures.
- Checkpoint 2 checks calendar boundaries, known two-asset return paths, rebalance timing, initial turnover, side-specific fees, and the stamp-duty effective date.
- Checkpoint 3 checks metric calculations on small known series and the CLI output row count, allocation grid, period set, columns, and assumption labels.
- Checkpoint 4 runs the complete documented command on the repository files and checks the generated report and CSV. Generated outputs stay out of Git.
- Checkpoint 5 checks chart value mapping and SVG labels, regenerates the full-data outputs, and visually inspects both figures and the rendered Markdown report at normal size.

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| `.xls` suffix does not match the OOXML workbook contents | Source loading may fail with a legacy reader | Explicitly configure the openpyxl engine and document why. |
| Index series are not investable vehicles | Modeled costs may be mistaken for actual costs | Label results as hypothetical index-proxy results and make every fee configurable. |
| Calendar period boundary handling can shift the holding period | Rebalance returns may contain lookahead or off-by-one errors | Select the last common trading date for each period and apply its target from the next date; verify with hand-calculated examples. |
| Extensibility can become unnecessary framework overhead | Slower implementation and harder usage | Keep strategy and metric contracts small and implement only the periodic strategy and requested metrics. |
| Drawdown is not recovered by the sample end | A plain numeric recovery duration is misleading | Report elapsed trading days plus an explicit unrecovered status. |

## Open questions

- None blocking. The approved spec labels commission and slippage defaults as editable illustrative assumptions and models stamp duty from an explicit effective-date schedule.
