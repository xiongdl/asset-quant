"""Load and align close-price series from the source OOXML workbooks."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pandas as pd


def clean_price_data(frame: pd.DataFrame, asset_name: str) -> pd.Series:
    """Validate one workbook's 日期/收盘价 columns and return sorted prices.

    Rows containing non-date notes are discarded when they have no close value.
    A non-date row with a close value is treated as malformed source data.
    """
    required_columns = {"日期", "收盘价"}
    missing = required_columns.difference(frame.columns)
    if missing:
        raise ValueError(
            f"{asset_name}: missing required workbook columns: "
            f"{', '.join(sorted(missing))}; expected 日期 and 收盘价"
        )

    rows: list[tuple[pd.Timestamp, float, int]] = []
    for row_number, (raw_date, raw_close) in enumerate(
        zip(frame["日期"], frame["收盘价"]), start=2
    ):
        try:
            parsed_date = pd.to_datetime(raw_date, errors="coerce")
        except (TypeError, ValueError, OverflowError):
            parsed_date = pd.NaT

        if pd.isna(parsed_date):
            if pd.isna(raw_close):
                continue
            raise ValueError(
                f"{asset_name}: malformed date in workbook row {row_number}: {raw_date!r}"
            )

        try:
            close = float(raw_close)
        except (TypeError, ValueError, OverflowError):
            raise ValueError(
                f"{asset_name}: invalid close price in workbook row {row_number} "
                f"for {pd.Timestamp(parsed_date).date()}: {raw_close!r}"
            ) from None

        if pd.isna(close) or close == float("inf") or close == float("-inf"):
            raise ValueError(
                f"{asset_name}: invalid close price in workbook row {row_number} "
                f"for {pd.Timestamp(parsed_date).date()}: {raw_close!r}"
            )
        if close <= 0:
            raise ValueError(
                f"{asset_name}: close price must be positive in workbook row "
                f"{row_number} for {pd.Timestamp(parsed_date).date()}, got {close}"
            )

        rows.append((pd.Timestamp(parsed_date).normalize(), close, row_number))

    if not rows:
        raise ValueError(f"{asset_name}: workbook contains no valid dated close prices")

    dates = pd.DatetimeIndex([date for date, _, _ in rows], name="date")
    duplicate_mask = dates.duplicated(keep=False)
    if duplicate_mask.any():
        duplicate_date = dates[duplicate_mask][0].date()
        raise ValueError(f"{asset_name}: duplicate date {duplicate_date} in workbook")

    prices = pd.Series(
        [close for _, close, _ in rows],
        index=dates,
        name=asset_name,
        dtype="float64",
    )
    return prices.sort_index()


def load_market_data(sources: Mapping[str, str | Path]) -> pd.DataFrame:
    """Read each source workbook and return close prices on common dates only.

    The index is the ascending common trading-date index. Each source key is
    retained as its output column name.
    """
    if len(sources) < 2:
        raise ValueError("At least two asset workbooks are required for alignment")

    price_series: list[pd.Series] = []
    for asset_name, source in sources.items():
        path = Path(source)
        if not path.is_file():
            raise ValueError(f"{asset_name}: missing workbook file: {path}")
        try:
            frame = pd.read_excel(path, engine="openpyxl")
        except Exception as exc:
            raise ValueError(f"{asset_name}: could not read workbook {path}: {exc}") from exc
        price_series.append(clean_price_data(frame, asset_name))

    aligned = pd.concat(price_series, axis=1, join="inner").sort_index()
    if aligned.empty:
        asset_names = ", ".join(sources)
        raise ValueError(f"No common trading dates across source workbooks: {asset_names}")
    aligned.index.name = "date"
    return aligned
