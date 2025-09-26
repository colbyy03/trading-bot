
import pandas as pd
import pytest

from trading_bot.data.polygon_source import PolygonDataSource


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def polygon_env(monkeypatch):
    monkeypatch.setenv("POLYGON_API_KEY", "test")


def test_fetch_aggregates_paginates(monkeypatch):
    payloads = [
        {
            "status": "OK",
            "results": [
                {
                    "t": 1_700_000_000_000,
                    "o": 1,
                    "h": 2,
                    "l": 0.5,
                    "c": 1.5,
                    "v": 100,
                    "vw": 1.2,
                    "n": 10,
                }
            ],
            "next_url": "next",
            "request_id": "abc",
        },
        {
            "status": "OK",
            "results": [
                {
                    "t": 1_700_000_060_000,
                    "o": 1.6,
                    "h": 2.1,
                    "l": 1.4,
                    "c": 1.8,
                    "v": 120,
                    "vw": 1.7,
                    "n": 12,
                }
            ],
            "request_id": "abc",
        },
    ]
    calls = iter(payloads)

    class DummyRest:
        def list_aggs(self, *args, **kwargs):
            payload = next(calls)
            return DummyResponse(payload)

    ds = PolygonDataSource(api_key="test")
    monkeypatch.setattr(ds, "_rest_client", DummyRest())
    df = ds.fetch_aggregates("SPY", "2023-01-01", "2023-01-02")
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert df.iloc[0]["close"] == 1.5
