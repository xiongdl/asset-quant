"""Contracts shared by portfolio allocation strategies."""

from datetime import date
from typing import Mapping, Protocol, Sequence


class AllocationStrategy(Protocol):
    """A strategy that supplies target weights and dates for target updates."""

    @property
    def target_weights(self) -> Mapping[str, float]:
        """Target asset weights, expressed as decimals."""

    def rebalance_dates(self, dates: Sequence[date]) -> list[date]:
        """Return close dates on which target weights are reset."""
