"""Daily two-asset portfolio accounting with close-date rebalancing."""

from datetime import date
from math import isclose, isfinite
from typing import Mapping

import pandas as pd

from asset_quant.backtest.costs import TransactionCostModel
from asset_quant.strategies.base import AllocationStrategy

ASSETS = ("480080", "480081")


def _validate_weights(weights: Mapping[str, float]) -> dict[str, float]:
    if set(weights) != set(ASSETS):
        raise ValueError(f"Strategy weights must contain exactly {', '.join(ASSETS)}")
    values = dict(weights)
    if any(
        not isinstance(weight, (int, float))
        or not isfinite(weight)
        or weight < 0
        or weight > 1
        for weight in values.values()
    ):
        raise ValueError("Strategy weights must be finite decimals between 0 and 1")
    if not isclose(sum(values.values()), 1.0, rel_tol=0, abs_tol=1e-12):
        raise ValueError("Strategy weights must sum to 1")
    return {asset: float(values[asset]) for asset in ASSETS}


def _validate_prices(prices: pd.DataFrame) -> list[date]:
    if not isinstance(prices, pd.DataFrame):
        raise TypeError("Prices must be a pandas DataFrame")
    if set(prices.columns) != set(ASSETS) or len(prices.columns) != 2:
        raise ValueError(f"Prices must have exactly the columns {', '.join(ASSETS)}")
    if len(prices) == 0:
        raise ValueError("Prices must contain at least one common trading date")
    if not prices.index.is_monotonic_increasing or prices.index.has_duplicates:
        raise ValueError("Price dates must be strictly increasing and unique")
    if prices.isna().any().any() or (prices <= 0).any().any():
        raise ValueError("Close prices must be finite and positive")
    if not all(isfinite(float(value)) for value in prices.to_numpy().flat):
        raise ValueError("Close prices must be finite and positive")
    dates = [pd.Timestamp(value).date() for value in prices.index]
    if len(set(dates)) != len(dates):
        raise ValueError("Price dates must be unique by calendar date")
    return dates


def run_backtest(
    prices: pd.DataFrame,
    strategy: AllocationStrategy,
    cost_model: TransactionCostModel,
    *,
    initial_capital: float = 1.0,
) -> pd.DataFrame:
    """Run a close-to-close backtest and return daily NAV, weights, and costs.

    Target weights selected at a close are used from the following trading
    date onward. The first row records initial purchase costs as a return from
    the supplied initial capital, before any market return is earned.
    """
    dates = _validate_prices(prices)
    if not isinstance(initial_capital, (int, float)) or not isfinite(initial_capital) or initial_capital <= 0:
        raise ValueError("Initial capital must be a finite positive number")
    target = _validate_weights(strategy.target_weights)
    scheduled_dates = list(strategy.rebalance_dates(dates))
    if any(day not in set(dates) for day in scheduled_dates):
        raise ValueError("Strategy returned a rebalance date outside the price history")
    if len(set(scheduled_dates)) != len(scheduled_dates):
        raise ValueError("Strategy returned duplicate rebalance dates")

    schedule = set(scheduled_dates)
    first_costs = cost_model.calculate(
        trade_date=dates[0],
        buy_notional=initial_capital * sum(target.values()),
        sell_notional=0,
    )
    nav = float(initial_capital) - first_costs.total
    if nav <= 0:
        raise ValueError("Initial transaction costs exhaust the initial capital")
    weights = target.copy()
    records = [
        {
            "portfolio_return": nav / float(initial_capital) - 1,
            "nav": nav,
            "weight_480080": weights["480080"],
            "weight_480081": weights["480081"],
            "buy_notional": initial_capital,
            "sell_notional": 0.0,
            "commission": first_costs.commission,
            "slippage": first_costs.slippage,
            "stamp_duty": first_costs.stamp_duty,
            "transaction_cost": first_costs.total,
        }
    ]

    for row_number in range(1, len(prices)):
        previous = prices.iloc[row_number - 1]
        current = prices.iloc[row_number]
        asset_returns = {
            asset: float(current[asset] / previous[asset] - 1)
            for asset in ASSETS
        }
        portfolio_growth = sum(
            weights[asset] * (1 + asset_returns[asset]) for asset in ASSETS
        )
        pretrade_nav = nav * portfolio_growth
        drifted_weights = {
            asset: weights[asset] * (1 + asset_returns[asset]) / portfolio_growth
            for asset in ASSETS
        }

        buy_notional = 0.0
        sell_notional = 0.0
        transaction_cost = 0.0
        commission = 0.0
        slippage = 0.0
        stamp_duty = 0.0
        if dates[row_number] in schedule:
            buy_notional = pretrade_nav * sum(
                max(target[asset] - drifted_weights[asset], 0.0)
                for asset in ASSETS
            )
            sell_notional = pretrade_nav * sum(
                max(drifted_weights[asset] - target[asset], 0.0)
                for asset in ASSETS
            )
            costs = cost_model.calculate(
                trade_date=dates[row_number],
                buy_notional=buy_notional,
                sell_notional=sell_notional,
            )
            transaction_cost = costs.total
            commission = costs.commission
            slippage = costs.slippage
            stamp_duty = costs.stamp_duty
            weights = target.copy()
        else:
            weights = drifted_weights

        nav = pretrade_nav - transaction_cost
        if nav <= 0:
            raise ValueError(f"Transaction costs exhaust portfolio NAV on {dates[row_number]}")
        records.append(
            {
                "portfolio_return": nav / records[-1]["nav"] - 1,
                "nav": nav,
                "weight_480080": weights["480080"],
                "weight_480081": weights["480081"],
                "buy_notional": buy_notional,
                "sell_notional": sell_notional,
                "commission": commission,
                "slippage": slippage,
                "stamp_duty": stamp_duty,
                "transaction_cost": transaction_cost,
            }
        )

    result = pd.DataFrame(records, index=prices.index.copy())
    result.index.name = prices.index.name or "date"
    return result
