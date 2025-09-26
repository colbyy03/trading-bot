import pandas as pd

from trading_bot.strategies.sma_cross import SmaCrossStrategy


def test_sma_cross_signals() -> None:
    prices = pd.Series(
        [1, 2, 3, 2, 1, 2, 3], index=pd.date_range("2023-01-01", periods=7, freq="D")
    )
    data = pd.DataFrame({"close": prices})
    strategy = SmaCrossStrategy(fast=2, slow=3)
    state = strategy.prepare(data)
    last_bar = data.iloc[-1]
    last_bar.name = data.index[-1]
    signal, confidence = strategy.on_bar(last_bar, state)
    assert signal.value in {"buy", "sell", "hold"}
    assert 0.0 <= confidence <= 1.0
