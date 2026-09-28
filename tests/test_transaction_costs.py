import unittest
from datetime import date

from asset_quant.backtest.costs import StampDutyRate, TransactionCostModel


class TransactionCostTests(unittest.TestCase):
    def setUp(self):
        self.costs = TransactionCostModel(
            commission_rate=0.001,
            slippage_rate=0.002,
            stamp_duty_schedule=[
                StampDutyRate(date(2000, 1, 1), 0.01),
                StampDutyRate(date(2023, 8, 28), 0.005),
            ],
        )

    def test_commission_and_slippage_apply_to_both_sides_and_tax_only_sales(self):
        result = self.costs.calculate(
            trade_date=date(2023, 8, 27), buy_notional=1000, sell_notional=500
        )
        self.assertEqual(result.buy_commission, 1)
        self.assertEqual(result.sell_commission, 0.5)
        self.assertEqual(result.buy_slippage, 2)
        self.assertEqual(result.sell_slippage, 1)
        self.assertEqual(result.stamp_duty, 5)
        self.assertEqual(result.total, 9.5)

    def test_stamp_duty_uses_rate_effective_on_trade_date(self):
        before = self.costs.calculate(
            trade_date=date(2023, 8, 27), buy_notional=0, sell_notional=1000
        )
        after = self.costs.calculate(
            trade_date=date(2023, 8, 28), buy_notional=0, sell_notional=1000
        )
        self.assertEqual(before.stamp_duty, 10)
        self.assertEqual(after.stamp_duty, 5)

    def test_purchase_does_not_pay_stamp_duty(self):
        result = self.costs.calculate(
            trade_date=date(2024, 1, 1), buy_notional=1000, sell_notional=0
        )
        self.assertEqual(result.stamp_duty, 0)

    def test_boolean_cost_rates_are_rejected(self):
        for commission, slippage, duty, label in (
            (True, 0, 0, "commission"),
            (0, True, 0, "slippage"),
            (0, 0, True, "stamp duty"),
        ):
            with self.subTest(rate=label):
                with self.assertRaisesRegex(ValueError, "(?i)" + label.replace(" ", "[- ]")):
                    TransactionCostModel(
                        commission_rate=commission,
                        slippage_rate=slippage,
                        stamp_duty_schedule=[StampDutyRate(date(2000, 1, 1), duty)],
                    )

    def test_invalid_turnover_and_rates_are_rejected(self):
        with self.assertRaises(ValueError):
            self.costs.calculate(
                trade_date=date(2024, 1, 1), buy_notional=-1, sell_notional=0
            )
        with self.assertRaises(ValueError):
            TransactionCostModel(
                commission_rate=-0.1,
                slippage_rate=0,
                stamp_duty_schedule=[StampDutyRate(date(2000, 1, 1), 0)],
            )


if __name__ == "__main__":
    unittest.main()
