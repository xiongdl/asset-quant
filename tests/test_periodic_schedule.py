import unittest
from datetime import date

from asset_quant.strategies.periodic import (
    RebalancePeriod,
    PeriodicRebalanceStrategy,
    allocation_grid,
    generate_rebalance_dates,
)


class PeriodicScheduleTests(unittest.TestCase):
    def setUp(self):
        self.dates = [
            date(2024, 1, 1),
            date(2024, 1, 5),
            date(2024, 1, 8),
            date(2024, 2, 1),
            date(2024, 3, 28),
            date(2024, 3, 29),
            date(2024, 4, 1),
            date(2024, 6, 28),
            date(2024, 7, 1),
            date(2024, 12, 31),
        ]

    def test_weekly_uses_last_available_day_in_each_iso_week(self):
        self.assertEqual(
            generate_rebalance_dates(self.dates, RebalancePeriod.WEEKLY),
            [
                date(2024, 1, 5),
                date(2024, 1, 8),
                date(2024, 2, 1),
                date(2024, 3, 29),
                date(2024, 4, 1),
                date(2024, 6, 28),
                date(2024, 7, 1),
                date(2024, 12, 31),
            ],
        )

    def test_calendar_periods_use_last_available_common_trading_day(self):
        cases = {
            RebalancePeriod.MONTHLY: [date(2024, 1, 8), date(2024, 2, 1), date(2024, 3, 29), date(2024, 4, 1), date(2024, 6, 28), date(2024, 7, 1), date(2024, 12, 31)],
            RebalancePeriod.QUARTERLY: [date(2024, 3, 29), date(2024, 6, 28), date(2024, 7, 1), date(2024, 12, 31)],
            RebalancePeriod.SEMIANNUAL: [date(2024, 6, 28), date(2024, 12, 31)],
            RebalancePeriod.ANNUAL: [date(2024, 12, 31)],
        }
        for period, expected in cases.items():
            with self.subTest(period=period):
                self.assertEqual(generate_rebalance_dates(self.dates, period), expected)

    def test_grid_has_eleven_complementary_fully_invested_allocations(self):
        allocations = allocation_grid()
        self.assertEqual(len(allocations), 11)
        self.assertEqual([row["480080"] for row in allocations], [i / 10 for i in range(11)])
        self.assertTrue(all(row["480080"] + row["480081"] == 1 for row in allocations))

    def test_strategy_exposes_schedule_and_target_weights(self):
        strategy = PeriodicRebalanceStrategy(
            period=RebalancePeriod.QUARTERLY,
            target_weights={"480080": 0.4, "480081": 0.6},
        )
        self.assertEqual(strategy.rebalance_dates(self.dates), [date(2024, 3, 29), date(2024, 6, 28), date(2024, 7, 1), date(2024, 12, 31)])
        self.assertEqual(strategy.target_weights, {"480080": 0.4, "480081": 0.6})

    def test_schedule_rejects_unsorted_or_duplicate_dates(self):
        with self.assertRaises(ValueError):
            generate_rebalance_dates([date(2024, 1, 2), date(2024, 1, 1)], RebalancePeriod.MONTHLY)
        with self.assertRaises(ValueError):
            generate_rebalance_dates([date(2024, 1, 1), date(2024, 1, 1)], RebalancePeriod.MONTHLY)


if __name__ == "__main__":
    unittest.main()
