"""Metric contracts and an engine-independent calculation registry."""

from datetime import date
from math import isfinite
from typing import Protocol, Sequence, TypeAlias

MetricValue: TypeAlias = float | int | bool | str | None


class Metric(Protocol):
    """A named calculation over one backtest's dates, returns, and NAV."""

    name: str

    def calculate(
        self,
        *,
        dates: Sequence[date],
        returns: Sequence[float],
        nav: Sequence[float],
    ) -> MetricValue:
        """Return one serializable value for the supplied backtest series."""


def validate_series(
    *, dates: Sequence[date], returns: Sequence[float], nav: Sequence[float]
) -> None:
    """Validate shared time-series assumptions before calculating a metric."""
    if not dates or len(dates) != len(returns) or len(dates) != len(nav):
        raise ValueError("Metric dates, returns, and NAV must have equal non-zero lengths")
    if any(not isinstance(day, date) for day in dates):
        raise TypeError("Metric dates must contain date values")
    if any(later <= earlier for earlier, later in zip(dates, dates[1:])):
        raise ValueError("Metric dates must be strictly increasing and unique")
    if any(not isinstance(value, (int, float)) or not isfinite(value) for value in returns):
        raise ValueError("Metric returns must be finite numbers")
    if any(
        not isinstance(value, (int, float)) or not isfinite(value) or value <= 0
        for value in nav
    ):
        raise ValueError("Metric NAV values must be finite positive numbers")
    if any(value <= -1 for value in returns):
        raise ValueError("Metric returns must be greater than -100%")


class MetricRegistry:
    """Run registered metrics without coupling them to portfolio accounting."""

    def __init__(self) -> None:
        self._metrics: list[Metric] = []

    @property
    def metrics(self) -> tuple[Metric, ...]:
        return tuple(self._metrics)

    def __len__(self) -> int:
        return len(self._metrics)

    def register(self, metric: Metric) -> None:
        if not isinstance(getattr(metric, "name", None), str) or not metric.name:
            raise ValueError("A metric must have a non-empty name")
        if not callable(getattr(metric, "calculate", None)):
            raise TypeError("A metric must provide a calculate method")
        if any(existing.name == metric.name for existing in self._metrics):
            raise ValueError(f"Metric name is already registered: {metric.name}")
        self._metrics.append(metric)

    def calculate_all(
        self,
        *,
        dates: Sequence[date],
        returns: Sequence[float],
        nav: Sequence[float],
    ) -> dict[str, MetricValue]:
        validate_series(dates=dates, returns=returns, nav=nav)
        return {
            metric.name: metric.calculate(dates=dates, returns=returns, nav=nav)
            for metric in self._metrics
        }
