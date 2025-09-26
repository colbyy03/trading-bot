"""VWAP breakout strategy."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pandas as pd

from trading_bot.indicators import ta

from .base import Signal, Strategy, StrategyState


class BreakoutVwapStrategy(Strategy):
    name = "breakout_vwap"

    @classmethod
    def default_params(cls) -> dict[str, Any]:
        return {"lookback": 20, "std_multiplier": 2.0}

    @classmethod
    def param_space(cls) -> Mapping[str, Any]:
        return {"lookback": [10, 20, 30], "std_multiplier": [1.5, 2.0]}

    def prepare(self, data: pd.DataFrame) -> StrategyState:
        df = data.copy()
        df["vwap"] = ta.vwap(df)
        bands = ta.bollinger_bands(
            df["close"],
            window=int(self.params["lookback"]),
            num_std=float(self.params["std_multiplier"]),
        )
        indicators = pd.concat([df[["close", "vwap"]], bands], axis=1)
        return StrategyState(data=indicators, metadata={})

    def on_bar(self, bar: pd.Series, state: StrategyState) -> tuple[Signal, float]:
        row = state.data.loc[bar.name]
        if row.isna().any():
            return Signal.HOLD, 0.0
        if row["close"] > row["upper"] and row["close"] > row["vwap"]:
            return Signal.BUY, 0.8
        if row["close"] < row["lower"] and row["close"] < row["vwap"]:
            return Signal.SELL, 0.8
        return Signal.HOLD, 0.2


def create(params: dict[str, Any] | None = None) -> BreakoutVwapStrategy:
    return BreakoutVwapStrategy(**(params or {}))


__all__ = ["BreakoutVwapStrategy", "create"]
