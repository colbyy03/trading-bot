"""MACD trend following strategy."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from trading_bot.indicators import ta

from .base import Signal, Strategy, StrategyState


class MacdTrendStrategy(Strategy):
    name = "macd_trend"

    @classmethod
    def default_params(cls) -> dict[str, Any]:
        return {"fast": 12, "slow": 26, "signal": 9}

    @classmethod
    def param_space(cls) -> Mapping[str, Any]:
        return {"fast": [8, 12], "slow": [17, 26], "signal": [9]}

    def prepare(self, data: pd.DataFrame) -> StrategyState:
        macd_df = ta.macd(
            data["close"],
            fast=int(self.params["fast"]),
            slow=int(self.params["slow"]),
            signal=int(self.params["signal"]),
        )
        return StrategyState(data=macd_df, metadata={})

    def on_bar(self, bar: pd.Series, state: StrategyState) -> tuple[Signal, float]:
        macd_value = state.data.loc[bar.name, "macd"]
        signal_value = state.data.loc[bar.name, "signal"]
        if pd.isna(macd_value) or pd.isna(signal_value):
            return Signal.HOLD, 0.0
        if macd_value > signal_value:
            return Signal.BUY, 0.6
        if macd_value < signal_value:
            return Signal.SELL, 0.6
        return Signal.HOLD, 0.0


def create(params: dict[str, Any] | None = None) -> MacdTrendStrategy:
    return MacdTrendStrategy(**(params or {}))


__all__ = ["MacdTrendStrategy", "create"]
