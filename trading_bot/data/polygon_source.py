"""Polygon.io data access helpers."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from typing import Any

import pandas as pd
import structlog
from polygon import RESTClient, WebSocketClient
from polygon.websocket.models import WebSocketMessage

from .cache import cache_key, load_cached_dataframe, save_dataframe_to_cache

log = structlog.get_logger(__name__)


class PolygonDataSource:
    """Convenience wrapper for Polygon REST and WebSocket APIs."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ.get("POLYGON_API_KEY")
        if not self.api_key:
            raise RuntimeError("POLYGON_API_KEY environment variable is required")
        self._rest_client = RESTClient(self.api_key)

    # region Historical data -----------------------------------------------------------------
    def fetch_aggregates(
        self,
        ticker: str,
        start: str,
        end: str,
        timespan: str = "minute",
        adjusted: bool = True,
        limit: int = 50000,
    ) -> pd.DataFrame:
        """Fetch aggregates with transparent pagination."""

        request_args = {
            "ticker": ticker,
            "multiplier": 1,
            "timespan": timespan,
            "from_": start,
            "to": end,
            "adjusted": adjusted,
            "limit": limit,
        }
        log.info("polygon.fetch_aggregates.start", **request_args)

        results: list[dict[str, Any]] = []
        try:
            aggs_iterator = self._rest_client.list_aggs(**request_args)
            for agg in aggs_iterator:
                results.append(
                    {
                        "timestamp": agg.timestamp,
                        "open": agg.open,
                        "high": agg.high,
                        "low": agg.low,
                        "close": agg.close,
                        "volume": agg.volume,
                        "vwap": getattr(agg, "vwap", None),
                        "trade_count": getattr(agg, "transactions", None),
                    }
                )
        except Exception:
            log.exception("polygon.fetch_aggregates.error", **request_args)
            raise

        if not results:
            log.warning(
                "polygon.fetch_aggregates.empty",
                ticker=ticker,
                start=start,
                end=end,
            )
            return pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])

        df = pd.DataFrame(results)
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).dt.tz_convert(
            "US/Eastern"
        )
        df.set_index("timestamp", inplace=True)
        df.sort_index(inplace=True)
        log.info("polygon.fetch_aggregates.completed", ticker=ticker, rows=len(df))
        return df

    def fetch_and_cache(
        self,
        ticker: str,
        start: str,
        end: str,
        bar_size: str,
        force: bool = False,
    ) -> pd.DataFrame:
        """Fetch aggregates and cache them as parquet."""

        key = cache_key(ticker, bar_size, start, end)
        if not force:
            cached = load_cached_dataframe(key)
            if cached is not None:
                log.info("cache.hit", ticker=ticker, bar_size=bar_size, start=start, end=end)
                return cached
        timespan = "second" if bar_size == "1sec" else "minute"
        df = self.fetch_aggregates(ticker, start, end, timespan=timespan)
        save_dataframe_to_cache(df, key)
        return df

    # endregion ------------------------------------------------------------------------------

    # region Reference data -------------------------------------------------------------------
    def get_splits(self, ticker: str) -> pd.DataFrame:
        """Fetch splits for the given ticker."""

        log.info("polygon.fetch_splits.start", ticker=ticker)
        splits = list(self._rest_client.list_splits(ticker=ticker, raw=False))
        df = pd.DataFrame(splits)
        if not df.empty:
            df["execution_date"] = pd.to_datetime(df["execution_date"])
        return df

    def get_dividends(self, ticker: str) -> pd.DataFrame:
        """Fetch dividends for the given ticker."""

        log.info("polygon.fetch_dividends.start", ticker=ticker)
        divs = list(self._rest_client.list_dividends(ticker=ticker, raw=False))
        df = pd.DataFrame(divs)
        if not df.empty:
            df["ex_dividend_date"] = pd.to_datetime(df["ex_dividend_date"])
        return df

    # endregion ------------------------------------------------------------------------------

    # region Streaming -----------------------------------------------------------------------
    async def stream_aggregates(
        self,
        ticker: str,
        timespan: str = "minute",
    ) -> AsyncIterator[pd.Series]:
        """Yield aggregate bars from the Polygon WebSocket."""

        loop = asyncio.get_event_loop()
        queue: asyncio.Queue[pd.Series] = asyncio.Queue()

        def handle_message(msg: WebSocketMessage) -> None:
            for event in msg.events:
                if event.event_type not in {"A", "AM"}:  # aggregate types
                    continue
                if event.ticker != ticker:
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
                loop.call_soon_threadsafe(queue.put_nowait, bar)

        client = WebSocketClient(
            subscriptions=[f"A.{ticker}"], api_key=self.api_key, feed="delayed"
        )
        client.on_message = handle_message

        log.info("polygon.stream.start", ticker=ticker, timespan=timespan)
        task = asyncio.create_task(client.connect_async())
        try:
            while True:
                bar = await queue.get()
                yield bar
        finally:
            client.close()
            await task
            log.info("polygon.stream.stop", ticker=ticker)

    # endregion -----------------------------------------------------------------------------


__all__ = ["PolygonDataSource"]
