from pathlib import Path

import yaml

from trading_bot.config import load_config


def test_load_config(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    data = {
        "tickers": ["spy"],
        "bar_size": "1min",
        "start": "2023-01-01",
        "end": "2023-01-31",
        "strategy": {"name": "sma_cross", "params": {"fast": 5, "slow": 20}},
    }
    config_path.write_text(yaml.safe_dump(data))
    cfg = load_config(config_path)
    assert cfg.tickers == ["SPY"]
    assert cfg.strategy.name == "sma_cross"
