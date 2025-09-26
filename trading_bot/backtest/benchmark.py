"""Benchmark utilities."""

from __future__ import annotations

import pandas as pd


def buy_and_hold_benchmark(
    data: pd.DataFrame, ticker: str, starting_equity: float = 100_000.0
) -> pd.Series:
    """Compute a buy-and-hold equity curve for the provided price series."""

    if data.empty:
        raise ValueError("No data provided for benchmark")
    prices = data["close"]
    shares = starting_equity / prices.iloc[0]
    equity = prices * shares
    equity.name = f"benchmark_{ticker}"
    return equity


__all__ = ["buy_and_hold_benchmark"]
