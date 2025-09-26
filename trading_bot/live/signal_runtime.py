"""Live signal runtime for alerting."""

from __future__ import annotations

import asyncio
from collections import deque

import pandas as pd
import structlog

from trading_bot.config import Config
from trading_bot.strategies import Signal, create_strategy

from .discord import send_alert
from .streamer import AggregateStreamer

log = structlog.get_logger(__name__)


class LiveSignalRuntime:
    """Consumes live bars, evaluates a strategy, and pushes Discord alerts."""

    def __init__(
        self,
        config: Config,
        window: int = 1000,
    ) -> None:
        self.config = config
        self.window = window
        self.strategy = create_strategy(config.strategy.name, **config.strategy.params)
        self.streamer = AggregateStreamer(config.tickers[0])
        self.history: deque[pd.Series] = deque(maxlen=window)
        self.last_signal: Signal | None = None

    async def run(self) -> None:
        log.info(
            "live.runtime_start",
            ticker=self.config.tickers[0],
            note="Polygon data is 15 minutes delayed per plan",
        )
        async for bar in self.streamer.stream():
            self.history.append(bar)
            df = pd.DataFrame(list(self.history))
            df.index = [b.name for b in self.history]
            state = self.strategy.prepare(df)
            signal, confidence = self.strategy.on_bar(bar, state)
            if self.last_signal == signal:
                continue
            self.last_signal = signal
            if signal is Signal.HOLD:
                continue
            payload = {
                "Price": f"${bar['close']:.2f}",
                "Time": bar.name.isoformat(),
                "Strategy": self.strategy.name,
                "Params": self.strategy.params,
                "Confidence": f"{confidence:.2f}",
            }
            if "rsi" in state.data.columns:
                payload["RSI"] = round(state.data.iloc[-1]["rsi"], 2)
            if "macd" in state.data.columns:
                payload["MACD"] = round(state.data.iloc[-1]["macd"], 2)
            send_alert(signal.value, self.config.tickers[0], payload)
            await asyncio.sleep(0)


__all__ = ["LiveSignalRuntime"]
