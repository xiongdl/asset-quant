import csv
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from asset_quant.cli import run_configured_backtest
from asset_quant.reporting import write_report


class ReportingTests(unittest.TestCase):
    def _fixture_config(self, root: Path) -> Path:
        dates = pd.to_datetime(["2024-01-02", "2024-01-05", "2024-01-31", "2024-02-29"])
        first = pd.DataFrame({"日期": dates, "收盘价": [100, 102, 103, 104]})
        second = pd.DataFrame({"日期": dates, "收盘价": [100, 99, 101, 100]})
        first_path, second_path = root / "first.xlsx", root / "second.xlsx"
        first.to_excel(first_path, index=False)
        second.to_excel(second_path, index=False)
        config_path = root / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "data": {"sources": {"480080": str(first_path), "480081": str(second_path)}},
                    "costs": {
                        "commission_rate_per_side": 0.0003,
                        "slippage_rate_per_side": 0.0005,
                        "stamp_duty_schedule": [
                            {"effective_from": "1900-01-01", "effective_through": None, "rate_on_sales": 0.001}
                        ],
                    },
                    "risk_free_rate_annual": 0.02,
                    "output_dir": str(root / "outputs"),
                }
            ),
            encoding="utf-8",
        )
        return config_path

    def test_one_run_writes_all_55_cases_and_cost_assumptions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = self._fixture_config(root)
            override_dir = root / "override-output"
            run_dir = run_configured_backtest(config_path, override_dir)
            self.assertEqual(run_dir.parent, override_dir)
            with (run_dir / "metrics.csv").open(encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 55)
            self.assertEqual({row["rebalance_period"] for row in rows}, {
                "weekly", "monthly", "quarterly", "semiannual", "annual"
            })
            self.assertEqual({float(row["weight_480080_pct"]) for row in rows}, set(range(0, 101, 10)))
            self.assertIn("annualized_return", rows[0])
            self.assertIn("source_480080", rows[0])
            self.assertIn("source_480081", rows[0])
            self.assertIn("annualized_volatility", rows[0])
            self.assertIn("maximum_drawdown", rows[0])
            self.assertIn("maximum_drawdown_recovery_days", rows[0])
            self.assertIn("maximum_drawdown_recovered", rows[0])
            self.assertIn("sharpe_ratio", rows[0])
            self.assertIn("commission", rows[0])
            self.assertIn("buy_notional", rows[0])
            self.assertIn("sell_notional", rows[0])
            self.assertIn("transaction_cost", rows[0])
            self.assertIn("slippage", rows[0])
            self.assertIn("stamp_duty", rows[0])
            self.assertIn("0.0003", rows[0]["commission_rate_per_side"])
            self.assertIn("effective_through", rows[0]["stamp_duty_schedule"])
            report = (run_dir / "report.md").read_text(encoding="utf-8")
            self.assertIn("55", report)
            self.assertTrue(report.startswith("# 480080 / 480081 组合回测概览"))
            self.assertIn("最高年化收益", report)
            self.assertIn("最高夏普", report)
            self.assertIn("最浅最大回撤", report)
            self.assertIn("不构成投资建议", report)
            self.assertIn("![配置与周期指标热力图](performance_heatmaps.svg)", report)
            self.assertIn("![收益与回撤散点图](risk_return.svg)", report)
            self.assertIn("报告中不逐行展开", report)
            self.assertTrue((run_dir / "performance_heatmaps.svg").is_file())
            self.assertTrue((run_dir / "risk_return.svg").is_file())
            self.assertIn("历史代理数据", report)
            self.assertIn("假设", report)
            self.assertIn("总体标准差", report)
            self.assertNotIn("| rebalance_period |", report)

    def test_missing_source_and_invalid_rate_have_actionable_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = self._fixture_config(root)
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["data"]["sources"]["480080"] = str(root / "missing.xlsx")
            config_path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing workbook"):
                run_configured_backtest(config_path)

            config["data"]["sources"]["480080"] = str(root / "first.xlsx")
            config["costs"]["commission_rate_per_side"] = -0.1
            config_path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "(?i)commission"):
                run_configured_backtest(config_path)

    def test_boolean_cost_rates_from_json_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_path = self._fixture_config(root)
            original = json.loads(config_path.read_text(encoding="utf-8"))
            rate_paths = (
                ("commission_rate_per_side", None, "commission"),
                ("slippage_rate_per_side", None, "slippage"),
                (None, "rate_on_sales", "stamp duty"),
            )
            for cost_key, schedule_key, label in rate_paths:
                with self.subTest(rate=label):
                    config = json.loads(json.dumps(original))
                    if schedule_key is None:
                        config["costs"][cost_key] = True
                    else:
                        config["costs"]["stamp_duty_schedule"][0][schedule_key] = True
                    config_path.write_text(json.dumps(config), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "(?i)" + label.replace(" ", "[- ]")):
                        run_configured_backtest(config_path)

    def test_report_writer_accepts_empty_results_and_writes_header(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            write_report(
                [], output, assumptions={"commission_rate_per_side": 0.0003},
                data_start="2024-01-01", data_end="2024-01-01"
            )
            self.assertTrue((output / "report.md").is_file())
            self.assertEqual((output / "metrics.csv").read_text(encoding="utf-8").strip(), "")
            report = (output / "report.md").read_text(encoding="utf-8")
            self.assertNotIn("performance_heatmaps.svg", report)
            self.assertNotIn("risk_return.svg", report)


if __name__ == "__main__":
    unittest.main()
