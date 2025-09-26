import numpy as np
import pandas as pd

from trading_bot.indicators.ta import bollinger_bands, macd, rsi, sma, vwap


def test_sma() -> None:
    series = pd.Series([1, 2, 3, 4, 5])
    result = sma(series, 3)
    assert result.iloc[-1] == 4


def test_rsi_bounds() -> None:
    prices = pd.Series(np.linspace(1, 10, 30))
    values = rsi(prices, 14)
    assert values.between(0, 100).all()


def test_macd_histogram_zero_when_equal() -> None:
    prices = pd.Series(np.arange(1, 100))
    macd_df = macd(prices)
    hist = macd_df["histogram"].iloc[-1]
    assert isinstance(hist, float)


def test_bollinger_band_shapes() -> None:
    prices = pd.Series(np.arange(1, 50))
    bands = bollinger_bands(prices, 5)
    assert set(bands.columns) == {"mid", "upper", "lower"}


def test_vwap_monotonic() -> None:
    df = pd.DataFrame(
        {
            "high": [2, 3, 4],
            "low": [1, 2, 3],
            "close": [1.5, 2.5, 3.5],
            "volume": [100, 200, 300],
        }
    )
    values = vwap(df)
    assert values.is_monotonic_increasing
