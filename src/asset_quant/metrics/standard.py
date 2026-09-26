"""Built-in return, risk, and drawdown metrics."""

from dataclasses import dataclass
from datetime import date
from math import isfinite, sqrt
from statistics import pstdev
from typing import Sequence

from asset_quant.metrics.base import MetricValue, validate_series

TRADING_DAYS_PER_YEAR = 252
CALENDAR_DAYS_PER_YEAR = 365.2425


def _initial_capital(returns: Sequence[float], nav: Sequence[float]) -> float:
    """Reconstruct capital before the first row's initial buy costs."""
    first_return = returns[0]
    if first_return <= -1:
        raise ValueError("The first return must leave positive capital after initial costs")
    return float(nav[0]) / (1 + float(first_return))


def _validate(dates: Sequence[date], returns: Sequence[float], nav: Sequence[float]) -> None:
    validate_series(dates=dates, returns=returns, nav=nav)


@dataclass(frozen=True)
class AnnualizedReturn:
    """Geometric annualized return over elapsed calendar time."""

    name: str = "annualized_return"

    def calculate(self, *, dates, returns, nav) -> float | None:
        _validate(dates, returns, nav)
        elapsed_days = (dates[-1] - dates[0]).days
        if elapsed_days <= 0:
            return None
        years = elapsed_days / CALENDAR_DAYS_PER_YEAR
        return (float(nav[-1]) / _initial_capital(returns, nav)) ** (1 / years) - 1


@dataclass(frozen=True)
class AnnualizedVolatility:
    """Population standard deviation of daily returns, scaled by sqrt(252)."""

    name: str = "annualized_volatility"

    def calculate(self, *, dates, returns, nav) -> float | None:
        _validate(dates, returns, nav)
        # Row zero records initial buy costs, not a close-to-close daily return.
        daily_returns = [float(value) for value in returns[1:]]
        if not daily_returns:
            return None
        return pstdev(daily_returns) * sqrt(TRADING_DAYS_PER_YEAR)


@dataclass(frozen=True)
class MaxDrawdown:
    """Most negative decline from the initial capital or a subsequent NAV peak."""

    name: str = "maximum_drawdown"

    def calculate(self, *, dates, returns, nav) -> float:
        _validate(dates, returns, nav)
        peak = _initial_capital(returns, nav)
        worst = 0.0
        for value in nav:
            peak = max(peak, float(value))
            worst = min(worst, float(value) / peak - 1)
        return worst


def _maximum_drawdown_window(
    returns: Sequence[float], nav: Sequence[float]
) -> tuple[float, int, int, int | None]:
    """Return drawdown, peak index, trough index, and recovery index."""
    capital = _initial_capital(returns, nav)
    values = [capital, *(float(value) for value in nav)]
    peak_value = values[0]
    peak_index = 0
    worst = 0.0
    worst_peak = worst_trough = 0
    for index, value in enumerate(values[1:], start=1):
        if value > peak_value:
            peak_value, peak_index = value, index
        drawdown = value / peak_value - 1
        if drawdown < worst:
            worst = drawdown
            worst_peak, worst_trough = peak_index, index
    if worst == 0:
        return 0.0, 0, 0, 0
    peak_at_trough = values[worst_peak]
    recovered = next(
        (index for index in range(worst_trough + 1, len(values)) if values[index] >= peak_at_trough),
        None,
    )
    return worst, worst_peak, worst_trough, recovered


@dataclass(frozen=True)
class MaxDrawdownRecoveryDays:
    """Trading-day distance from the maximum drawdown's preceding peak."""

    name: str = "maximum_drawdown_recovery_days"

    def calculate(self, *, dates, returns, nav) -> int:
        _validate(dates, returns, nav)
        _, peak, trough, recovered = _maximum_drawdown_window(returns, nav)
        end_index = recovered if recovered is not None else len(nav)
        # Values include original capital at index zero and each NAV at index+1.
        # The elapsed number of trading observations between points is index delta.
        return end_index - peak


@dataclass(frozen=True)
class MaxDrawdownRecovered:
    """Whether NAV recovered the peak preceding its maximum drawdown."""

    name: str = "maximum_drawdown_recovered"

    def calculate(self, *, dates, returns, nav) -> bool:
        _validate(dates, returns, nav)
        return _maximum_drawdown_window(returns, nav)[3] is not None


@dataclass(frozen=True)
class SharpeRatio:
    """Annualized Sharpe using daily excess returns and a configurable annual rate."""

    risk_free_rate_annual: float = 0.0
    name: str = "sharpe_ratio"

    def __post_init__(self) -> None:
        if (
            not isinstance(self.risk_free_rate_annual, (int, float))
            or not isfinite(self.risk_free_rate_annual)
            or self.risk_free_rate_annual <= -1
        ):
            raise ValueError("Annual risk-free rate must be numeric and greater than -100%")

    def calculate(self, *, dates, returns, nav) -> float | None:
        _validate(dates, returns, nav)
        daily_returns = [float(value) for value in returns[1:]]
        if not daily_returns:
            return None
        risk_free_daily = float(self.risk_free_rate_annual) / TRADING_DAYS_PER_YEAR
        excess = [value - risk_free_daily for value in daily_returns]
        deviation = pstdev(daily_returns)
        if deviation == 0:
            return None
        return (sum(excess) / len(excess)) / deviation * sqrt(TRADING_DAYS_PER_YEAR)


def default_metrics(*, risk_free_rate_annual: float = 0.0):
    """Build the standard extensible registry with the configured risk-free rate."""
    from asset_quant.metrics.base import MetricRegistry

    registry = MetricRegistry()
    for metric in (
        AnnualizedReturn(),
        AnnualizedVolatility(),
        MaxDrawdown(),
        MaxDrawdownRecoveryDays(),
        MaxDrawdownRecovered(),
        SharpeRatio(risk_free_rate_annual=risk_free_rate_annual),
    ):
        registry.register(metric)
    return registry
