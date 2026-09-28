import unittest
from datetime import date

from asset_quant.metrics import MetricRegistry, default_metrics
from asset_quant.metrics.standard import (
    AnnualizedReturn,
    AnnualizedVolatility,
    MaxDrawdown,
    MaxDrawdownRecoveryDays,
    MaxDrawdownRecovered,
    SharpeRatio,
)


class MetricTests(unittest.TestCase):
    def test_cagr_uses_initial_cost_and_elapsed_calendar_years(self):
        metric = AnnualizedReturn()
        # First NAV is 0.9 after a 10% initial fee; final NAV is 1.21 after
        # one calendar year, so CAGR is measured against original capital 1.
        value = metric.calculate(
            dates=[date(2023, 1, 1), date(2024, 1, 1)],
            returns=[-0.1, 1.21 / 0.9 - 1],
            nav=[0.9, 1.21],
        )
        self.assertAlmostEqual(value, 1.21 ** (365.2425 / 365) - 1)

    def test_volatility_and_sharpe_use_population_daily_returns(self):
        dates = [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)]
        returns = [-0.1, 0.1, -0.1]
        nav = [0.9, 0.99, 0.891]
        volatility = AnnualizedVolatility().calculate(dates=dates, returns=returns, nav=nav)
        sharpe = SharpeRatio(risk_free_rate_annual=0.252).calculate(
            dates=dates, returns=returns, nav=nav
        )
        self.assertAlmostEqual(volatility, 0.1 * (252**0.5))
        self.assertAlmostEqual(sharpe, (0.0 - 0.001) / 0.1 * (252**0.5))

    def test_max_drawdown_and_recovery_count_from_preceding_peak(self):
        dates = [date(2024, 1, day) for day in range(1, 6)]
        nav = [100, 120, 90, 100, 120]
        returns = [0, 0.2, -0.25, 100 / 90 - 1, 0.2]
        args = dict(dates=dates, returns=returns, nav=nav)
        self.assertAlmostEqual(MaxDrawdown().calculate(**args), -0.25)
        self.assertEqual(MaxDrawdownRecoveryDays().calculate(**args), 3)
        self.assertTrue(MaxDrawdownRecovered().calculate(**args))

    def test_unrecovered_drawdown_reports_elapsed_trading_days_and_status(self):
        dates = [date(2024, 1, day) for day in range(1, 5)]
        nav = [100, 120, 90, 100]
        returns = [0, 0.2, -0.25, 100 / 90 - 1]
        args = dict(dates=dates, returns=returns, nav=nav)
        self.assertEqual(MaxDrawdownRecoveryDays().calculate(**args), 2)
        self.assertFalse(MaxDrawdownRecovered().calculate(**args))

    def test_registry_allows_additional_metric_without_engine_changes(self):
        class TerminalNav:
            name = "terminal_nav"

            def calculate(self, *, dates, returns, nav):
                return nav[-1]

        registry = MetricRegistry()
        registry.register(TerminalNav())
        result = registry.calculate_all(
            dates=[date(2024, 1, 1)], returns=[0], nav=[1.5]
        )
        self.assertEqual(result, {"terminal_nav": 1.5})
        self.assertEqual(len(default_metrics()), 6)


if __name__ == "__main__":
    unittest.main()
