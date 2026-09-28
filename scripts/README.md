# Asset Quant scripts and portfolio backtest

## 480080 / 480081 portfolio backtest

This command compares 11 target allocations (0% through 100% in 10% steps for
480080, with 480081 as the complement) under weekly, monthly, quarterly,
semiannual, and annual close-based rebalancing. One run therefore evaluates 55
configurations. Run commands from the repository root because the sample
configuration uses repository-relative paths.

### Prerequisites and installation

- Python 3.11 or newer.
- The two source workbooks checked into `data/raw/`:
  `480080_perf_20121231_20260807.xls` and
  `480081_perf_20121231_20260807.xls`. They contain OOXML workbooks despite the
  `.xls` filename suffix; the project reads them with `openpyxl`.
- A network connection for the initial dependency installation, unless the
  required packages are already available in the pip cache.

Create an isolated environment and install the package and its declared
dependencies:

```bash
python3.11 -m venv .venvs/portfolio-backtest
source .venvs/portfolio-backtest/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The `.venvs/` environment and generated `outputs/` directory are ignored by
Git. To check the command-line options after installation:

```bash
python -m asset_quant.cli --help
```

### Run

Run the complete backtest with the checked-in inputs and settings:

```bash
python -m asset_quant.cli --config config/portfolio_backtest.json
```

The command prints the paths of the generated `report.md` and `metrics.csv`.
Each run creates a unique UTC-timestamped directory under `outputs/`, for
example `outputs/run_YYYYMMDDTHHMMSS_microsecondsZ/`.

To use another JSON configuration or write the run elsewhere:

```bash
python -m asset_quant.cli --config path/to/backtest.json
python -m asset_quant.cli --config config/portfolio_backtest.json --output-dir /path/to/output
```

The CLI accepts `--config` and optional `--output-dir`. The second option
overrides `output_dir` in the JSON file. Relative paths are resolved from the
current working directory; the sample paths assume the repository root.

### Configuration

`config/portfolio_backtest.json` is the editable example. It contains:

| Field | Meaning |
| --- | --- |
| `data.sources.480080` | Path to the 480080 workbook. |
| `data.sources.480081` | Path to the 480081 workbook. |
| `costs.commission_rate_per_side` | Illustrative commission as a decimal per buy or sell notional (default `0.0003`, or 0.03%). |
| `costs.slippage_rate_per_side` | Illustrative slippage as a decimal per buy or sell notional (default `0.0005`, or 0.05%). |
| `costs.stamp_duty_schedule` | Ordered entries with `effective_from` (ISO date) and `rate_on_sales` (decimal). Stamp duty applies only to sell notional. Each rate remains active until the next entry's effective date; the final rate has no end date. |
| `risk_free_rate_annual` | Annual risk-free rate as a decimal, used for Sharpe (default `0.0`). |
| `output_dir` | Parent directory for timestamped run folders (default `outputs`). |

The example stamp-duty entries use 0.10% through 2023-08-27 and 0.05% from
2023-08-28. Commission and slippage are editable examples, not quotes or
estimates for a particular broker, fund, account, or investment vehicle. The
tax schedule is a hypothetical constituent-level A-share assumption for index
proxies. The inputs are index series, not directly investable securities, so
results are hypothetical and do not represent realizable returns for a
specific product.

### Inputs, assumptions, and metrics

The loader reads `日期` and `收盘价`, drops non-date note rows, validates and
sorts each series, then keeps only dates shared by both indices. With the
checked-in workbooks the common range is 2012-12-31 through 2026-08-07.
Close-to-close changes are used as daily returns. The first common date sets
initial capital and target allocation; the first return is earned on the next
common trading date. A rebalance at a period's last available close affects
the following trading day's return.

The report summarizes metric-leading configurations, shared start and end
dates, assumptions, and metric definitions. The CSV includes the full
480080/480081 weights and rebalance-period grid, dates, configured
commission/slippage/tax rates, buy and sell notional, summed cost components,
and the six built-in metrics:

- `annualized_return`: geometric CAGR over elapsed calendar years, using
  365.2425 days per year and including initial buy costs relative to initial
  capital.
- `annualized_volatility`: population standard deviation of daily
  close-to-close portfolio returns multiplied by √252.
- `maximum_drawdown`: the most negative decline from initial capital or a
  later NAV peak.
- `maximum_drawdown_recovery_days`: trading observations from the peak before
  the maximum drawdown until that peak is regained; for an unrecovered drawdown
  the elapsed observations through the last date are reported.
- `maximum_drawdown_recovered`: whether that peak was regained within the
  sample.
- `sharpe_ratio`: mean daily excess return divided by daily return standard
  deviation, multiplied by √252. The configured annual risk-free rate is
  divided by 252. Initial buy cost is excluded from volatility and Sharpe
  because it is not a close-to-close return.

### Outputs and side effects

Each invocation creates a new run directory and writes:

- `report.md`: a Chinese overview with concise metric leaders, assumptions,
  data range, and metric definitions. It embeds the two comparison charts.
- `metrics.csv`: exactly one row per allocation and rebalance-period pair,
  including all metric and cost fields.
- `performance_heatmaps.svg`: heatmaps for annualized return, Sharpe ratio, and
  maximum drawdown across the full 11-allocation × 5-period grid.
- `risk_return.svg`: an annualized-return versus maximum-drawdown scatter plot
  for all 55 configurations, with rebalance periods distinguished by color
  and the three metric leaders annotated.

The command reads the configured workbooks and JSON file and writes only the
new run artifacts under the selected output directory. It does not modify the
input workbooks or configuration. No single portfolio is declared universally
best; compare the metrics in light of the intended investment objective.

### Extension points

The code separates source loading (`asset_quant.data`), strategy contracts and
periodic schedules (`asset_quant.strategies`), portfolio accounting and costs
(`asset_quant.backtest`), metrics (`asset_quant.metrics`), and output writing
(`asset_quant.reporting`). A new metric can implement the `Metric` contract
and be registered in the metric registry without changing the backtest engine.
A future strategy can implement the strategy contract and be passed to the
engine independently of data loading and reporting. Keep each extension in
its corresponding module and preserve these boundaries as additional
strategies, metrics, and data sources are introduced.
