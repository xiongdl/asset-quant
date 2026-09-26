# Spec: Modular 480080/480081 Portfolio Backtest

## Objective

Create a reusable Python command-line backtest that compares 11 complementary allocations of 480080 and 480081 across five fixed rebalance calendars. A single run evaluates all 55 combinations and writes a human-readable report and detailed machine-readable results. The initial strategy is periodic target-weight rebalancing; the design must let later strategies plug into the same backtest engine and metric pipeline.

The source index factsheets identify 480080 as 成长100R and 480081 as 价值100R. These are index series, not directly tradable securities. Their historical returns are therefore a proxy for a hypothetical portfolio, and fee assumptions do not represent a real product's costs.

## Assumptions to make explicit in the implementation

1. The two existing performance workbooks are the initial data source. Read their `日期` and `收盘价` columns, discard non-date note rows, sort ascending, validate unique dates and positive numeric close values, and inner-join on common dates.
2. Use close-to-close total-return-index changes as daily returns. The current common history is 2012-12-31 through 2026-08-07. The start date establishes initial capital and target allocations; the first return is earned on the following common trading date.
3. Weights are fully invested and allow fractional holdings. The allocation grid is exactly 0%, 10%, ..., 100% for 480080, with 480081 set to 100% minus that weight.
4. Rebalance on the last available common trading date in each ISO week, calendar month, calendar quarter, half-year, and calendar year. A close-date rebalance takes effect for the next trading day's return; do not use future returns when selecting or executing a target.
5. Since there is no actual investment vehicle or broker schedule, commission and slippage are transparent, editable proportional assumptions applied per side to traded notional. Provide illustrative defaults of 0.03% commission and 0.05% slippage per side; label them as examples, not market quotes. Provide a configurable stamp-duty schedule that charges only sales: 0.10% through 2023-08-27 and 0.05% from 2023-08-28 onward. The initial allocation incurs buy-side commission and slippage, but no sell-side stamp duty.
6. Apply transaction costs to portfolio turnover at initial investment and each rebalance. The cost model must distinguish buy and sell notional so one-way taxes are not charged on purchases. Expose rates and effective dates in JSON configuration; do not hard-code them in the backtest engine.
7. Annualized return is geometric CAGR using elapsed calendar years (365.2425 days/year). Annualized volatility and Sharpe use daily portfolio returns and 252 trading days/year. The default annual risk-free rate is 0%, configurable in the run settings.
8. Maximum drawdown is the most negative decline from a previous NAV peak. Maximum drawdown recovery time is the trading-day count from the peak preceding the maximum drawdown until NAV first regains that peak; if it is not recovered by the end of the data, report the elapsed trading days and an unrecovered status.
9. A report compares all configurations and explains the input assumptions and formulas. It does not declare one portfolio universally “best,” because no single optimization objective was requested.

## Proposed project structure

```text
src/asset_quant/
  cli.py                  # command-line entry point and run orchestration
  data/market_data.py     # workbook loading, validation, date alignment
  backtest/engine.py      # daily portfolio accounting and strategy dispatch
  backtest/costs.py       # configurable turnover, commission, slippage, tax model
  strategies/base.py      # strategy protocol / target-allocation contract
  strategies/periodic.py  # periodic target-weight strategy
  metrics/base.py         # metric contract and registry
  metrics/standard.py     # CAGR, volatility, drawdown, recovery, Sharpe
  reporting/              # summary report and detailed CSV export
config/portfolio_backtest.json
outputs/                  # generated, untracked run output
tests/                    # focused checks for calculations and input handling
```

The engine should consume a strategy through a small interface that supplies target weights and rebalance decisions. Metrics should be registered independently of the engine so adding a metric does not require editing portfolio accounting. A future strategy should be addable as a strategy module plus configuration, without changing the periodic-strategy implementation.

## Technology

- Python 3.11 or newer.
- `pandas` and `openpyxl` for the existing OOXML workbooks (two files have `.xls` suffixes despite OOXML contents); do not use a legacy binary `.xls` parser for these files.
- Standard-library `argparse`, `dataclasses`/`Protocol`, `json`, `csv`, and `unittest` where useful. Avoid adding a dependency for metric formulas that are straightforward to calculate directly.

## Commands

```bash
# Create and activate an isolated environment, then install declared dependencies.
python3 -m venv .venvs/portfolio-backtest
. .venvs/portfolio-backtest/bin/activate
python -m pip install -r requirements.txt

# Run the configured 55-case backtest.
python -m asset_quant.cli --config config/portfolio_backtest.json

# Run focused automated checks during implementation.
python -m unittest discover -s tests -v
```

The CLI must allow an alternate config path and output directory. It should fail with a clear message for missing files, missing required columns, invalid rates/weights, duplicate dates, non-positive closes, or no overlapping dates.

## Outputs

- `report.md`: assumptions, data range, metric definitions, and a readable comparison of all 55 configurations.
- `metrics.csv`: exactly 55 rows with allocation, rebalance schedule, cost assumptions, and all built-in metric values.
- Keep generated files under `outputs/` in a run-specific directory; do not modify source workbooks.

## Code style

- Keep modules focused and interfaces typed.
- Name weights and rates explicitly as decimals internally; serialize percentages with clear column names and units.
- Keep business logic pure where practical: a metric receives dates and a return/NAV series and returns a named result; a cost model receives buy/sell turnover and date and returns cost components.
- Example extension point:

```python
class Metric(Protocol):
    name: str

    def calculate(self, *, dates: Sequence[date], returns: Sequence[float], nav: Sequence[float]) -> float | int | None: ...
```

## Verification strategy

- Validate both source files independently, then verify the aligned series has unique increasing dates from 2012-12-31 through 2026-08-07 for the current data.
- Verify one run emits exactly 55 metric rows, includes all 11 allocations and all five periods, and reports cost assumptions.
- Check the no-rebalance/zero-cost path against a direct weighted daily-return calculation; check a rebalance boundary with a small hand-calculated example to catch lookahead and turnover errors.
- Confirm commission/slippage apply to both buy and sell notional, stamp duty only to sell notional, and the stamp-duty rate changes on its configured effective date.
- Spot-check the five built-in metrics independently and verify unrecovered drawdown duration is labeled correctly.
- Do not use this hypothetical index-proxy backtest to claim realizable performance for a specific fund or account.

## Boundaries

- **Always:** preserve raw workbooks; show assumptions and units in every run; align both indices on common dates; make cost assumptions and risk-free rate configurable; keep strategy, engine, metrics, and reporting independently extendable.
- **Ask first:** adding live data dependencies, an actual fund/security proxy, account-specific fees, leverage/short selling, benchmark optimization, or trade execution.
- **Never:** silently represent the indices as investable funds; use future data in a rebalance; charge sell-only tax on purchases; silently omit invalid rows or cost assumptions; present hypothetical results as a return promise.

## Success criteria

1. The default CLI run reads the two repository source files and produces a report and a 55-row metrics file for the full common sample.
2. All requested metrics are present with documented formulas and units, and an additional metric can be added through the metric registry without modifying the engine.
3. A second strategy can use the engine through the strategy contract without changing the periodic strategy implementation.
4. Cost, risk-free-rate, source-path, and output-path assumptions can be changed through configuration.
5. Rebalance dates and costs are applied without lookahead; source files remain untouched.

## Sources

- Index identities and the 480080 code mapping: [CNI Growth 100 factsheet](https://www.cnindex.com.cn/html2pdf/preview/jj_980080.pdf) and [CNI index series](https://www.cnindex.com.cn/zh_indices/cni/style/index.html?act_menu=null&index_type=202).
- Stamp duty was single-sided at 1‰ from 2008-09-19: [Ministry of Finance, 2008 notice](https://www.mof.gov.cn/zhengwuxinxi/caizhengxinwen/200809/t20080919_76432.htm). Securities transaction stamp duty was halved from 2023-08-28: [Ministry of Finance and State Taxation Administration notice](https://www.mof.gov.cn/caizhengshipin/caizhengxinwen2/202308/t20230828_3904230.htm). The modeled schedule is explicitly a hypothetical constituent-level A-share assumption for these index proxies.

## Open questions

- None blocking specification. Commission and slippage defaults are illustrative and must be visible/editable; the user has not supplied a real vehicle or broker schedule.
