"""Strategy abstraction for the trading bot."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Any

import pandas as pd

from trading_bot.config import RiskConfig


class Signal(Enum):
    """Buy/Sell/Hold signals."""

    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class StrategyState:
    """Container returned by :meth:`Strategy.prepare`."""

    data: pd.DataFrame
    metadata: dict[str, Any]


class Strategy(ABC):
    """Base class for strategies."""

    name: str

    def __init__(self, **params: Any) -> None:
        self.params = {**self.default_params(), **params}

    @classmethod
    def default_params(cls) -> dict[str, Any]:
        return {}

    @classmethod
    def param_space(cls) -> Mapping[str, Any]:
        return {}

    @abstractmethod
    def prepare(self, data: pd.DataFrame) -> StrategyState:
        """Return indicator data needed for processing."""

    @abstractmethod
    def on_bar(self, bar: pd.Series, state: StrategyState) -> tuple[Signal, float]:
        """Return a signal and optional confidence."""

    def position_sizing(
        self,
        signal: Signal,
        equity: float,
        price: float,
        risk_cfg: RiskConfig,
    ) -> float:
        """Fixed-fraction position sizing."""

        if signal is Signal.HOLD:
            return 0.0
        fraction = risk_cfg.fraction
        qty = (equity * fraction) / price
        return max(qty, 0.0)


__all__ = ["Signal", "Strategy", "StrategyState"]
