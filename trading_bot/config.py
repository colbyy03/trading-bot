"""Configuration loading and validation for the trading bot."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, ValidationError, field_validator

BarSize = Literal["1min", "1sec"]


class RiskConfig(BaseModel):
    """Risk management configuration."""

    position_sizing: Literal["fixed_fraction"] = "fixed_fraction"
    fraction: float = Field(0.1, ge=0, le=1)
    max_positions: int = Field(5, ge=1)
    stop_loss: float = Field(0.02, ge=0)
    take_profit: float = Field(0.04, ge=0)


class StrategyConfig(BaseModel):
    """Configuration for a strategy selection."""

    name: str
    params: dict[str, Any] = Field(default_factory=dict)


class Config(BaseModel):
    """Top-level configuration structure."""

    tickers: list[str] = Field(default_factory=lambda: ["SPY"])
    bar_size: BarSize = "1min"
    start: str | None = None
    end: str | None = None
    transaction_cost_bps: float = Field(0.0, ge=0)
    slippage_bps: float = Field(0.0, ge=0)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    strategy: StrategyConfig = Field(default_factory=lambda: StrategyConfig(name="sma_cross"))
    benchmark_ticker: str = "SPY"

    @field_validator("tickers", mode="before")
    @classmethod
    def _uppercase(cls, v):  # type: ignore[override]
        if isinstance(v, list):
            return [item.upper() for item in v]
        if isinstance(v, str):
            return v.upper()
        return v


DEFAULT_CONFIG_PATH = Path("config.yaml")


def load_config(path: str | Path | None = None) -> Config:
    """Load a :class:`Config` from a YAML or JSON file."""

    cfg_path = Path(path) if path else DEFAULT_CONFIG_PATH
    if not cfg_path.exists():
        raise FileNotFoundError(f"Config file not found: {cfg_path}")
    data = yaml.safe_load(cfg_path.read_text())
    try:
        return Config(**data)
    except ValidationError as exc:  # pragma: no cover - validation message
        raise ValueError(f"Invalid configuration: {exc}") from exc


__all__ = ["DEFAULT_CONFIG_PATH", "Config", "RiskConfig", "StrategyConfig", "load_config"]
