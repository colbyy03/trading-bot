"""RSI mean reversion strategy."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from trading_bot.indicators import ta

from .base import Signal, Strategy, StrategyState


class RsiReversionStrategy(Strategy):
    name = "rsi_reversion"

    @classmethod
    def default_params(cls) -> dict[str, Any]:
        return {"lower": 30, "upper": 70, "window": 14}

    @classmethod
    def param_space(cls) -> Mapping[str, Any]:
        return {"lower": [25, 30], "upper": [70, 75], "window": [14]}

    def prepare(self, data: pd.DataFrame) -> StrategyState:
        rsi_values = ta.rsi(data["close"], int(self.params["window"]))
        return StrategyState(data=pd.DataFrame({"rsi": rsi_values}), metadata={})

    def on_bar(self, bar: pd.Series, state: StrategyState) -> tuple[Signal, float]:
        rsi_value = state.data.loc[bar.name, "rsi"]
        if pd.isna(rsi_value):
            return Signal.HOLD, 0.0
        lower = float(self.params["lower"])
        upper = float(self.params["upper"])
        if rsi_value < lower:
            return Signal.BUY, min(1.0, (lower - rsi_value) / lower)
        if rsi_value > upper:
            return Signal.SELL, min(1.0, (rsi_value - upper) / (100 - upper))
        return Signal.HOLD, 0.1


def create(params: dict[str, Any] | None = None) -> RsiReversionStrategy:
    return RsiReversionStrategy(**(params or {}))


__all__ = ["RsiReversionStrategy", "create"]
