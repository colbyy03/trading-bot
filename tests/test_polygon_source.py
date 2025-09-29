
from dataclasses import dataclass
import pandas as pd
import pytest

from trading_bot.data.polygon_source import PolygonDataSource
from trading_bot.data import cache


@pytest.fixture(autouse=True)
def polygon_env(monkeypatch):
    monkeypatch.setenv("POLYGON_API_KEY", "test")


@dataclass
class DummyAgg:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: float
    transactions: int


def test_fetch_aggregates_paginates(monkeypatch):
    payloads = (
        DummyAgg(
            timestamp=1_700_000_000_000,
            open=1,
            high=2,
            low=0.5,
            close=1.5,
            volume=100,
            vwap=1.2,
            transactions=10,
        ),
        DummyAgg(
            timestamp=1_700_000_060_000,
            open=1.6,
            high=2.1,
            low=1.4,
            close=1.8,
            volume=120,
            vwap=1.7,
            transactions=12,
        ),
    )

    class DummyRest:
        def list_aggs(self, *args, **kwargs):
            return iter(payloads)

    ds = PolygonDataSource(api_key="test")
    monkeypatch.setattr(ds, "_rest_client", DummyRest())
    df = ds.fetch_aggregates("SPY", "2023-01-01", "2023-01-02")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert df.iloc[0]["close"] == 1.5


def test_fetch_and_cache_uses_cache_without_api_key(monkeypatch, tmp_path):
    monkeypatch.delenv("POLYGON_API_KEY", raising=False)
    cache_dir = tmp_path / "cache"
    monkeypatch.setattr(cache, "CACHE_DIR", cache_dir, raising=False)
    df = pd.DataFrame(
        {
            "open": [1.0],
            "high": [1.1],
            "low": [0.9],
            "close": [1.05],
            "volume": [100],
        },
        index=pd.to_datetime(["2023-01-03"], utc=True),
    )
    key = cache.cache_key("SPY", "1min", "2023-01-01", "2023-01-02")
    cache.save_dataframe_to_cache(df, key)

    ds = PolygonDataSource()
    result = ds.fetch_and_cache("SPY", "2023-01-01", "2023-01-02", "1min")

    pd.testing.assert_frame_equal(result, df)
