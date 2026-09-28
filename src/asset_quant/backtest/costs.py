"""Turnover-based proportional transaction costs."""

from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import Sequence


@dataclass(frozen=True)
class StampDutyRate:
    effective_from: date
    rate: float


@dataclass(frozen=True)
class TransactionCosts:
    buy_commission: float
    sell_commission: float
    buy_slippage: float
    sell_slippage: float
    stamp_duty: float

    @property
    def commission(self) -> float:
        return self.buy_commission + self.sell_commission

    @property
    def slippage(self) -> float:
        return self.buy_slippage + self.sell_slippage

    @property
    def total(self) -> float:
        return self.commission + self.slippage + self.stamp_duty


class TransactionCostModel:
    """Calculate side-specific fees and date-effective sell-only stamp duty."""

    def __init__(
        self,
        *,
        commission_rate: float,
        slippage_rate: float,
        stamp_duty_schedule: Sequence[StampDutyRate],
    ) -> None:
        self.commission_rate = self._validate_rate("commission", commission_rate)
        self.slippage_rate = self._validate_rate("slippage", slippage_rate)
        if not stamp_duty_schedule:
            raise ValueError("Stamp-duty schedule must contain at least one rate")
        schedule = list(stamp_duty_schedule)
        for item in schedule:
            if not isinstance(item.effective_from, date):
                raise TypeError("Stamp-duty effective dates must be date values")
            self._validate_rate("stamp duty", item.rate)
        if any(
            current.effective_from <= previous.effective_from
            for previous, current in zip(schedule, schedule[1:])
        ):
            raise ValueError("Stamp-duty effective dates must be strictly increasing")
        self.stamp_duty_schedule = tuple(schedule)

    @staticmethod
    def _validate_rate(name: str, rate: float) -> float:
        if (
            isinstance(rate, bool)
            or not isinstance(rate, (int, float))
            or not isfinite(rate)
            or rate < 0
        ):
            raise ValueError(f"{name.capitalize()} rate must be a finite non-negative decimal")
        return float(rate)

    def _stamp_duty_rate(self, trade_date: date) -> float:
        effective_rates = [
            item.rate
            for item in self.stamp_duty_schedule
            if item.effective_from <= trade_date
        ]
        if not effective_rates:
            raise ValueError(
                f"No stamp-duty rate is configured for trade date {trade_date}"
            )
        return effective_rates[-1]

    def calculate(
        self, *, trade_date: date, buy_notional: float, sell_notional: float
    ) -> TransactionCosts:
        if not isinstance(trade_date, date):
            raise TypeError("Trade date must be a date value")
        notionals = (buy_notional, sell_notional)
        if any(
            not isinstance(value, (int, float))
            or not isfinite(value)
            or value < 0
            for value in notionals
        ):
            raise ValueError("Buy and sell notionals must be finite and non-negative")

        duty_rate = self._stamp_duty_rate(trade_date)
        return TransactionCosts(
            buy_commission=buy_notional * self.commission_rate,
            sell_commission=sell_notional * self.commission_rate,
            buy_slippage=buy_notional * self.slippage_rate,
            sell_slippage=sell_notional * self.slippage_rate,
            stamp_duty=sell_notional * duty_rate,
        )
