"""Polygon WebSocket streaming utilities."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator

import pandas as pd
import structlog
from polygon import WebSocketClient
from polygon.websocket.models import WebSocketMessage

log = structlog.get_logger(__name__)


class AggregateStreamer:
    """Wrapper around the Polygon WebSocket aggregate feed."""

    def __init__(self, ticker: str, api_key: str | None = None) -> None:
        self.ticker = ticker
        self.api_key = api_key or os.environ.get("POLYGON_API_KEY")
        if not self.api_key:
            raise RuntimeError("POLYGON_API_KEY environment variable is required")
        self._client = WebSocketClient(
            api_key=self.api_key, subscriptions=[f"A.{ticker}"], feed="delayed"
        )
        self._queue: asyncio.Queue[pd.Series] = asyncio.Queue()
        self._client.on_message = self._on_message

    def _on_message(self, message: WebSocketMessage) -> None:
        for event in message.events:
            if event.event_type not in {"A", "AM"}:
                continue
            timestamp = pd.Timestamp(event.start_timestamp, unit="ms", tz="UTC").tz_convert(
                "US/Eastern"
            )
            bar = pd.Series(
                {
                    "open": event.open,
                    "high": event.high,
                    "low": event.low,
                    "close": event.close,
                    "volume": event.volume,
                    "vwap": event.vwap,
                    "trade_count": event.transactions,
                },
                name=timestamp,
            )
            self._queue.put_nowait(bar)

    async def stream(self) -> AsyncIterator[pd.Series]:
        log.info("streamer.start", ticker=self.ticker)
        connect_task = asyncio.create_task(self._client.connect_async())
        try:
            while True:
                bar = await self._queue.get()
                yield bar
        finally:
            self._client.close()
            await connect_task
            log.info("streamer.stop", ticker=self.ticker)


__all__ = ["AggregateStreamer"]
