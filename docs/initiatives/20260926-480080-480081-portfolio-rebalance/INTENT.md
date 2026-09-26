# Intent: 480080/480081 Modular Portfolio Backtest

## Outcome

Add a reusable, modular backtest tool to compare portfolios made from indices 480080 and 480081, and produce a report that can be rerun as source data or assumptions change.

## User and purpose

The project owner wants to compare allocation weights and rebalance frequencies using the historical data already kept in this repository, with enough structure to add other quantitative strategies later.

## Confirmed behavior

- Generate 11 target allocations: 480080 ranges from 0% through 100% in 10% steps; 480081 receives the balance.
- Compare weekly, monthly, quarterly, semiannual, and annual rebalancing in one run (55 combinations).
- Report annualized return, annualized volatility, maximum drawdown, maximum drawdown recovery time, Sharpe ratio, and extensible additional metrics.
- Include configurable assumptions for commission, slippage, and sell-side stamp duty. No real investment vehicle or fee schedule is specified, so costs are scenario estimates.
- Use the common daily history in the existing 480080 and 480081 source files, currently 2012-12-31 through 2026-08-07.
- Keep strategy logic, backtest execution, metric calculation, transaction-cost modeling, data loading, and report generation modular so future strategies can reuse the engine and add metrics.

## Success

One command can load the supplied data, evaluate all 55 combinations, and generate a readable report plus machine-readable detailed results. The calculation assumptions and metric definitions are visible, and the extension points for another strategy and metric are documented.

## Constraints and exclusions

- Treat 480080 and 480081 as total-return index series and use their daily closing values.
- Costs are hypothetical assumptions applied to portfolio turnover, not actual fills for a specified fund or account.
- Do not select or recommend a specific investment vehicle or execute trades.
- Preserve the source files and keep generated backtest outputs separate from raw data.
