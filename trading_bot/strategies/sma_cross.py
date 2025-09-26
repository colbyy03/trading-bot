"""Simple moving average crossover strategy."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from trading_bot.indicators import ta

from .base import Signal, Strategy, StrategyState


class SmaCrossStrategy(Strategy):
    name = "sma_cross"

    @classmethod
    def default_params(cls) -> dict[str, Any]:
        return {"fast": 10, "slow": 20}

    @classmethod
    def param_space(cls) -> Mapping[str, Any]:
        return {"fast": [5, 10, 20], "slow": [30, 50, 100]}

    def prepare(self, data: pd.DataFrame) -> StrategyState:
        fast = ta.sma(data["close"], int(self.params["fast"]))
        slow = ta.sma(data["close"], int(self.params["slow"]))
        indicators = pd.DataFrame({"fast": fast, "slow": slow})
        return StrategyState(data=indicators, metadata={})

    def on_bar(self, bar: pd.Series, state: StrategyState) -> tuple[Signal, float]:
        fast = state.data.loc[bar.name, "fast"]
        slow = state.data.loc[bar.name, "slow"]
        if pd.isna(fast) or pd.isna(slow):
            return Signal.HOLD, 0.0
        if fast > slow:
            return Signal.BUY, 0.7
        if fast < slow:
            return Signal.SELL, 0.7
        return Signal.HOLD, 0.0


def create(params: dict[str, Any] | None = None) -> SmaCrossStrategy:
    return SmaCrossStrategy(**(params or {}))


__all__ = ["SmaCrossStrategy", "create"]
