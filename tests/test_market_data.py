from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from asset_quant.data.market_data import clean_price_data, load_market_data


class CleanPriceDataTests(unittest.TestCase):
    def test_discards_note_rows_sorts_dates_and_renames_close_column(self) -> None:
        source = pd.DataFrame(
            {
                "日期": ["2024-01-03", "注：数据说明", "2024-01-02"],
                "收盘价": [12.0, None, 10.0],
            }
        )

        result = clean_price_data(source, "480080")

        self.assertEqual(list(result.index), list(pd.to_datetime(["2024-01-02", "2024-01-03"])))
        self.assertEqual(result.name, "480080")
        self.assertEqual(result.tolist(), [10.0, 12.0])

    def test_rejects_missing_required_columns(self) -> None:
        with self.assertRaisesRegex(ValueError, "日期.*收盘价"):
            clean_price_data(pd.DataFrame({"date": ["2024-01-02"], "close": [10]}), "480080")

    def test_rejects_duplicate_dates(self) -> None:
        source = pd.DataFrame({"日期": ["2024-01-02", "2024-01-02"], "收盘价": [10, 11]})
        with self.assertRaisesRegex(ValueError, "duplicate date.*2024-01-02"):
            clean_price_data(source, "480080")

    def test_rejects_invalid_price_on_a_valid_date(self) -> None:
        source = pd.DataFrame({"日期": ["2024-01-02"], "收盘价": ["not a price"]})
        with self.assertRaisesRegex(ValueError, "invalid close price"):
            clean_price_data(source, "480080")

    def test_rejects_non_positive_price(self) -> None:
        source = pd.DataFrame({"日期": ["2024-01-02"], "收盘价": [0]})
        with self.assertRaisesRegex(ValueError, "must be positive"):
            clean_price_data(source, "480080")

    def test_rejects_malformed_row_with_a_close_value(self) -> None:
        source = pd.DataFrame({"日期": ["not a date"], "收盘价": [10]})
        with self.assertRaisesRegex(ValueError, "malformed date"):
            clean_price_data(source, "480080")


class LoadMarketDataTests(unittest.TestCase):
    def test_loads_repository_workbooks_and_returns_common_dates(self) -> None:
        root = Path(__file__).resolve().parents[1]
        sources = {
            "480080": root / "data/raw/480080_perf_20121231_20260807.xls",
            "480081": root / "data/raw/480081_perf_20121231_20260807.xls",
        }

        result = load_market_data(sources)

        self.assertEqual(result.index.min(), pd.Timestamp("2012-12-31"))
        self.assertEqual(result.index.max(), pd.Timestamp("2026-08-07"))
        self.assertEqual(list(result.columns), ["480080", "480081"])
        self.assertTrue(result.index.is_monotonic_increasing)
        self.assertTrue(result.index.is_unique)
        self.assertFalse(result.isna().any().any())

    def test_missing_file_error_identifies_asset_and_path(self) -> None:
        with self.assertRaisesRegex(ValueError, "480080.*missing workbook"):
            load_market_data({"480080": "/missing/480080.xlsx", "480081": "/missing/480081.xlsx"})

    def test_no_common_dates_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.xlsx"
            second = Path(directory) / "second.xlsx"
            pd.DataFrame({"日期": ["2024-01-02"], "收盘价": [10]}).to_excel(first, index=False)
            pd.DataFrame({"日期": ["2024-01-03"], "收盘价": [11]}).to_excel(second, index=False)

            with self.assertRaisesRegex(ValueError, "(?i)no common trading dates"):
                load_market_data({"480080": first, "480081": second})


if __name__ == "__main__":
    unittest.main()
