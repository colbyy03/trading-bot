
from dataclasses import dataclass

import pandas as pd
import pytest

from trading_bot.data.polygon_source import PolygonDataSource


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
