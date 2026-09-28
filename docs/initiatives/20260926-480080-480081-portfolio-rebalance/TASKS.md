# Tasks: Modular 480080/480081 Portfolio Backtest

Initiative: `20260926-480080-480081-portfolio-rebalance`
Branch: `codex/20260926-480080-480081-portfolio-rebalance`
Approved source: `SPEC.md` (including the approved report-visualization update)
Task list owner: this file

Tasks are executed in checkpoint order. Each task is a separate commit unit. Each checkpoint is delegated to a fresh Default and ends at a clean, committed repository state.

## Checkpoint 1: Data foundation — complete at `ab8385c`

### Task 1: Package skeleton and run configuration

**Description:** Establish an installable `src/asset_quant` package, declare Python dependencies, add the initial CLI module, and define the JSON configuration for source paths and editable assumptions.

**Acceptance criteria:**
- [x] The package can be installed with the commands in the approved spec, and `python -m asset_quant.cli --help` is available.
- [x] `requirements.txt` includes the editable local package install as well as the declared runtime dependencies.
- [x] The sample JSON config defines both source paths, illustrative commission/slippage, date-effective stamp duty, risk-free rate, and output location.
- [x] Defaults are read from config and are not embedded in strategy or engine modules.

**Verification:** Create the isolated environment, install declared dependencies/package, load and validate the example configuration, and check the CLI help output.

**Dependencies:** None.

**Files likely touched:**
- `pyproject.toml`
- `requirements.txt`
- `src/asset_quant/__init__.py`
- `src/asset_quant/cli.py`
- `config/portfolio_backtest.json`

**Estimated scope:** Medium.

### Task 2: Validated market-data ingestion

**Description:** Implement source workbook loading, cleanup, validation, and common-date alignment for the two input index series.

**Acceptance criteria:**
- [x] The loader reads `日期`/`收盘价` from both supplied OOXML workbooks, removes non-date note rows, sorts dates ascending, rejects invalid/duplicate dates and non-positive prices, and returns only common dates.
- [x] The sample data reports the common range 2012-12-31 through 2026-08-07.
- [x] Missing files/columns, malformed rows, or no overlap produce actionable errors.

**Verification:** Load the current workbook pair; verify range, order, uniqueness, and overlap. Exercise validation failures with small in-memory malformed inputs.

**Dependencies:** Task 1.

**Files likely touched:**
- `src/asset_quant/data/__init__.py`
- `src/asset_quant/data/market_data.py`
- `tests/test_market_data.py`

**Estimated scope:** Small.

### Checkpoint 1 exit criteria

- [x] Tasks 1 and 2 are separately committed.
- [x] Package/config checks and focused data-loading checks pass.
- [x] The repository source files remain unchanged.

## Checkpoint 2: Strategy and portfolio accounting — complete at `ab8385c`

### Task 3: Strategy contract and periodic schedule generation

**Description:** Define the small target-allocation strategy contract and implement weekly, monthly, quarterly, semiannual, and annual rebalance date generation over common trading dates.

**Acceptance criteria:**
- [x] Strategy code is separate from input reading and portfolio accounting.
- [x] The schedule selects the last available common trading day in each ISO week/calendar month/calendar quarter/half-year/calendar year, with no duplicate or out-of-range event dates.
- [x] The allocation generator emits exactly 11 480080 weights from 0% to 100% in 10% increments and sets the 480081 weight to the complement.

**Verification:** Check known period-boundary dates, including week/month/quarter/year and half-year boundaries, using a small hand-constructed calendar; verify all allocation sums equal 100%.

**Dependencies:** Task 2.

**Files likely touched:**
- `src/asset_quant/strategies/base.py`
- `src/asset_quant/strategies/periodic.py`
- `tests/test_periodic_schedule.py`

**Estimated scope:** Small.

### Task 4: Backtest engine and turnover-based costs

**Description:** Implement daily two-asset portfolio accounting and the date-aware transaction-cost model. The engine applies same-day close rebalances to the following day's returns and computes net portfolio returns.

**Acceptance criteria:**
- [x] Daily returns are based on aligned close-to-close index changes and portfolio weights drift naturally between target rebalances.
- [x] Rebalance targets apply only after the rebalance close; the engine does not use future data.
- [x] Initial buys and later buys/sells incur configured commission and slippage by side; stamp duty applies only to sell notional using the effective-date schedule; cost components are visible in results.

**Verification:** Compare a no-rebalance path against direct weighted daily returns; verify a rebalance boundary with a hand-calculated example; check buy/sell turnover, initial cost, one-way tax, and the 2023-08-28 rate change.

**Dependencies:** Task 3.

**Files likely touched:**
- `src/asset_quant/backtest/engine.py`
- `src/asset_quant/backtest/costs.py`
- `src/asset_quant/backtest/__init__.py`
- `tests/test_backtest_engine.py`
- `tests/test_transaction_costs.py`

**Estimated scope:** Medium.

### Checkpoint 2 exit criteria

- [x] Tasks 3 and 4 are separately committed.
- [x] Focused checks pass for every period schedule and the hand-calculated net-return/cost cases.
- [x] The engine accepts a strategy through its contract and the periodic strategy contains no accounting implementation.

## Checkpoint 3: Metrics and reporting — complete at `ab8385c`

### Task 5: Extensible metrics registry and required metrics

**Description:** Add an independent metric contract/registry and implement annualized return, annualized volatility, maximum drawdown, maximum drawdown recovery duration/status, and Sharpe ratio.

**Acceptance criteria:**
- [x] Metrics consume the relevant date/return/NAV series and do not own or change portfolio accounting.
- [x] Annualization, drawdown recovery, risk-free rate, and unrecovered-period semantics match the approved spec.
- [x] A new metric can be registered without editing the backtest engine.

**Verification:** Compare all five outputs to hand-calculated small return/NAV series, including a never-recovered peak and a nonzero risk-free rate.

**Dependencies:** Task 4.

**Files likely touched:**
- `src/asset_quant/metrics/base.py`
- `src/asset_quant/metrics/standard.py`
- `src/asset_quant/metrics/__init__.py`
- `tests/test_metrics.py`

**Estimated scope:** Medium.

### Task 6: CLI orchestration and 55-case outputs

**Description:** Connect config, data, strategy, engine, metric registry, and report writer. Generate a run-specific Markdown report and detailed CSV for the full 11-by-5 grid.

**Acceptance criteria:**
- [x] CLI accepts an alternate config path and output directory and reports actionable input errors.
- [x] One run generates exactly 55 result rows across all five periods and all 11 weights.
- [x] Report and CSV include assumptions, dates, weights, rebalance period, cost components, and all registered metric outputs without selecting a single universally optimal portfolio.

**Verification:** Run the CLI using a small fixture config and inspect row counts/columns/content for report and CSV; verify missing/invalid config errors.

**Dependencies:** Task 5.

**Files likely touched:**
- `src/asset_quant/cli.py`
- `src/asset_quant/reporting/report.py`
- `src/asset_quant/reporting/__init__.py`
- `tests/test_reporting.py`

**Estimated scope:** Medium.

### Checkpoint 3 exit criteria

- [x] Tasks 5 and 6 are separately committed.
- [x] Focused checks pass for metric semantics, run configuration, and all 55 reported cases.
- [x] Strategy, metrics, and reporting remain separate from the core portfolio-accounting module.

## Checkpoint 4: Documentation and acceptance — complete at `ab8385c`

### Task 7: Usage documentation and full-data acceptance run

**Description:** Document environment setup, configuration fields, metric definitions, hypothetical cost assumptions, output files, and extension points. Run the complete approved backtest on repository data and verify the resulting artifacts.

**Acceptance criteria:**
- [x] `scripts/README.md` documents prerequisites, install/run commands, config options, output paths, and side effects.
- [x] A fresh environment can run the documented command against the current two source files and produce `report.md` and `metrics.csv` for all 55 combinations.
- [x] The report labels index-proxy/cost assumptions and defines all required metrics; generated output remains untracked.

**Verification:** Execute the documented full-data command and inspect the report, CSV row count, five periods, 11 allocations, date range, metric columns, and generated-output Git state.

**Dependencies:** Task 6.

**Files likely touched:**
- `scripts/README.md`
- `.gitignore`

**Estimated scope:** Small.

### Checkpoint 4 exit criteria

- [x] Task 7 is committed.
- [x] Full-data output matches the approved requirements, and the repository is clean with no generated output staged or tracked.
- [x] The implementation is ready for independent review across the full initiative commit range.

## Checkpoint 5: Readable report and charts

### Task 8: SVG comparison charts

**Description:** Add dependency-free SVG chart builders for the complete performance grid and return/risk comparison.

**Acceptance criteria:**
- [ ] The heatmap SVG contains all 11 allocation rows × 5 rebalance periods for annualized return, Sharpe ratio, and maximum drawdown, with clear units and readable labels.
- [ ] The scatter SVG contains all 55 cases, distinguishes rebalance periods, and annotates the highest-CAGR, highest-Sharpe, and shallowest-drawdown scenarios.
- [ ] SVG output includes accessible titles/descriptions, valid XML escaping, and no external charting dependency.

**Verification:** Focused tests check complete value mapping, all 55 scatter points, leader annotations, valid XML, accessibility metadata, and escaping.

**Dependencies:** Task 7.

**Files likely touched:**
- `src/asset_quant/reporting/charts_svg.py`
- `tests/test_charts_svg.py`

**Estimated scope:** Small.

### Task 9: Chinese report composition and full-data visual acceptance

**Description:** Put concise Chinese findings and metric leaders first, embed both charts, and regenerate the report from the complete repository data.

**Acceptance criteria:**
- [ ] The report opens with concise conclusions and a compact table for highest CAGR, highest Sharpe, and shallowest maximum drawdown, clearly labeled as metric leaders rather than recommendations.
- [ ] The report embeds both SVG files and gives data range, index-proxy/cost caveats, and metric definitions without reproducing all 55 cases as a dense table.
- [ ] The regenerated CSV retains exactly 55 rows and all existing metric and cost fields; generated outputs remain ignored.

**Verification:** Run focused reporting tests and the documented full-data command; inspect the Markdown and both charts at normal size for legibility, completeness, and clipping.

**Dependencies:** Task 8.

**Files likely touched:**
- `src/asset_quant/reporting/report.py`
- `tests/test_reporting.py`
- `scripts/README.md`

**Estimated scope:** Small.

### Checkpoint 5 exit criteria

- [ ] Tasks 8 and 9 are separately committed.
- [ ] Focused chart/report checks and full-data acceptance pass.
- [ ] Both charts render legibly; the report presents concise Chinese findings and leaves detailed rows in CSV.
