"""Periodic target-weight strategy and calendar schedule generation."""

from datetime import date
from enum import Enum
from math import isclose
from typing import Sequence

from asset_quant.strategies.base import AllocationStrategy


class RebalancePeriod(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    SEMIANNUAL = "semiannual"
    ANNUAL = "annual"


def _period_key(day: date, period: RebalancePeriod) -> tuple[int, ...]:
    if period is RebalancePeriod.WEEKLY:
        iso = day.isocalendar()
        return (iso.year, iso.week)
    if period is RebalancePeriod.MONTHLY:
        return (day.year, day.month)
    if period is RebalancePeriod.QUARTERLY:
        return (day.year, (day.month - 1) // 3 + 1)
    if period is RebalancePeriod.SEMIANNUAL:
        return (day.year, (day.month - 1) // 6 + 1)
    return (day.year,)


def generate_rebalance_dates(
    dates: Sequence[date], period: RebalancePeriod | str
) -> list[date]:
    """Select the last supplied trading date in each calendar period."""
    try:
        period = RebalancePeriod(period)
    except ValueError as exc:
        raise ValueError(f"Unsupported rebalance period: {period!r}") from exc
    if any(not isinstance(day, date) for day in dates):
        raise TypeError("Rebalance dates must contain date values")
    if any(later <= earlier for earlier, later in zip(dates, dates[1:])):
        raise ValueError("Trading dates must be strictly increasing and unique")

    last_by_period: dict[tuple[int, ...], date] = {}
    for day in dates:
        last_by_period[_period_key(day, period)] = day
    return list(last_by_period.values())


def allocation_grid() -> list[dict[str, float]]:
    """Return the 11 fully invested allocations in 10% increments."""
    return [
        {"480080": step / 10, "480081": 1 - step / 10}
        for step in range(11)
    ]


class PeriodicRebalanceStrategy(AllocationStrategy):
    """Reset to a fixed two-asset allocation on calendar period ends."""

    def __init__(
        self,
        *,
        period: RebalancePeriod | str,
        target_weights: dict[str, float],
    ) -> None:
        try:
            self.period = RebalancePeriod(period)
        except ValueError as exc:
            raise ValueError(f"Unsupported rebalance period: {period!r}") from exc
        if set(target_weights) != {"480080", "480081"}:
            raise ValueError("Target weights must contain 480080 and 480081")
        if any(not isinstance(weight, (int, float)) for weight in target_weights.values()):
            raise TypeError("Target weights must be numeric decimals")
        if any(weight < 0 or weight > 1 for weight in target_weights.values()):
            raise ValueError("Target weights must be between 0 and 1")
        if not isclose(sum(target_weights.values()), 1.0, rel_tol=0, abs_tol=1e-12):
            raise ValueError("Target weights must sum to 1")
        self._target_weights = dict(target_weights)

    @property
    def target_weights(self) -> dict[str, float]:
        return dict(self._target_weights)

    def rebalance_dates(self, dates: Sequence[date]) -> list[date]:
        return generate_rebalance_dates(dates, self.period)
