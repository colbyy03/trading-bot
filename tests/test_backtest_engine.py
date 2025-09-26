from pathlib import Path

import pandas as pd

from trading_bot.backtest.engine import BacktestEngine
from trading_bot.config import Config, RiskConfig, StrategyConfig


def test_backtest_engine_generates_summary(tmp_path: Path) -> None:
    index = pd.date_range("2023-01-01", periods=50, freq="D")
    prices = pd.Series(range(1, 51), index=index)
    data = pd.DataFrame({
        "open": prices,
        "high": prices + 1,
        "low": prices - 1,
        "close": prices,
        "volume": 1_000,
    })
    config = Config(
        tickers=["SPY"],
        bar_size="1min",
        start="2023-01-01",
        end="2023-02-20",
        strategy=StrategyConfig(name="sma_cross", params={"fast": 2, "slow": 5}),
        risk=RiskConfig(fraction=0.1, stop_loss=0.0, take_profit=0.0),
    )
    engine = BacktestEngine(starting_equity=1000)
    result = engine.run(data, config, tmp_path)
    assert result.summary.total_return >= 0
    assert (tmp_path / "summary.json").exists()
