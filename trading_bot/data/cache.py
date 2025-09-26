"""Simple parquet caching utilities."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

CACHE_DIR = Path(".cache")


def ensure_cache_dir() -> Path:
    """Ensure that the cache directory exists."""

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR


def cache_key(ticker: str, bar_size: str, start: str | None, end: str | None) -> Path:
    """Return a deterministic cache path for the query."""

    ensure_cache_dir()
    safe_ticker = ticker.replace("/", "_")
    return CACHE_DIR / f"{safe_ticker}_{bar_size}_{start or 'start'}_{end or 'end'}.parquet"


def load_cached_dataframe(path: Path) -> pd.DataFrame | None:
    """Load a dataframe from cache if it exists."""

    if path.exists():
        return pd.read_parquet(path)
    return None


def save_dataframe_to_cache(df: pd.DataFrame, path: Path) -> None:
    """Persist dataframe to the cache."""

    ensure_cache_dir()
    df.to_parquet(path)


__all__ = [
    "CACHE_DIR",
    "cache_key",
    "ensure_cache_dir",
    "load_cached_dataframe",
    "save_dataframe_to_cache",
]
