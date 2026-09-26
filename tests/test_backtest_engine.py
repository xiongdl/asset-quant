import unittest
from datetime import date

import pandas as pd

from asset_quant.backtest.costs import StampDutyRate, TransactionCostModel
from asset_quant.backtest.engine import run_backtest


class FixedStrategy:
    def __init__(self, dates, weights):
        self._dates = dates
        self.target_weights = weights

    def rebalance_dates(self, dates):
        return self._dates


def no_costs():
    return TransactionCostModel(
        commission_rate=0,
        slippage_rate=0,
        stamp_duty_schedule=[StampDutyRate(date(1900, 1, 1), 0)],
    )


class BacktestEngineTests(unittest.TestCase):
    def test_no_rebalance_path_matches_fixed_share_valuation(self):
        dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
        prices = pd.DataFrame(
            {"480080": [100, 110, 121], "480081": [100, 100, 120]}, index=dates
        )
        result = run_backtest(
            prices,
            FixedStrategy([], {"480080": 0.6, "480081": 0.4}),
            no_costs(),
        )
        expected_nav = [1.0, 1.06, 1.206]
        for actual, expected in zip(result["nav"], expected_nav):
            self.assertAlmostEqual(actual, expected)
        self.assertAlmostEqual(result.iloc[2]["portfolio_return"], 1.206 / 1.06 - 1)

    def test_rebalance_at_close_changes_following_day_return_only(self):
        dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
        prices = pd.DataFrame(
            {"480080": [100, 200, 200], "480081": [100, 100, 200]}, index=dates
        )
        result = run_backtest(
            prices,
            FixedStrategy(
                [date(2024, 1, 2)], {"480080": 0.5, "480081": 0.5}
            ),
            no_costs(),
        )
        self.assertAlmostEqual(result.iloc[1]["nav"], 1.5)
        self.assertAlmostEqual(result.iloc[2]["nav"], 2.25)

    def test_initial_purchases_and_later_buy_sell_turnover_are_costed(self):
        dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"])
        prices = pd.DataFrame(
            {"480080": [100, 200, 200], "480081": [100, 50, 50]}, index=dates
        )
        costs = TransactionCostModel(
            commission_rate=0.01,
            slippage_rate=0.005,
            stamp_duty_schedule=[StampDutyRate(date(2000, 1, 1), 0.001)],
        )
        result = run_backtest(
            prices,
            FixedStrategy(
                [date(2024, 1, 2)], {"480080": 0.6, "480081": 0.4}
            ),
            costs,
            initial_capital=1000,
        )
        initial = result.iloc[0]
        self.assertAlmostEqual(initial["buy_notional"], 1000)
        self.assertEqual(initial["sell_notional"], 0)
        self.assertAlmostEqual(initial["commission"], 10)
        self.assertAlmostEqual(initial["slippage"], 5)
        self.assertEqual(initial["stamp_duty"], 0)
        self.assertAlmostEqual(initial["portfolio_return"], -0.015)
        rebalance = result.iloc[1]
        self.assertGreater(rebalance["buy_notional"], 0)
        self.assertGreater(rebalance["sell_notional"], 0)
        self.assertGreater(rebalance["stamp_duty"], 0)
        self.assertAlmostEqual(
            rebalance["transaction_cost"],
            rebalance["commission"]
            + rebalance["slippage"]
            + rebalance["stamp_duty"],
        )


if __name__ == "__main__":
    unittest.main()
