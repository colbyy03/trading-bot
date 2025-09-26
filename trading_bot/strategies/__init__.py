"""Strategy registry."""

from __future__ import annotations

from .base import Signal, Strategy, StrategyState
from .breakout_vwap import BreakoutVwapStrategy
from .macd_trend import MacdTrendStrategy
from .rsi_reversion import RsiReversionStrategy
from .sma_cross import SmaCrossStrategy

REGISTRY: dict[str, type[Strategy]] = {
    SmaCrossStrategy.name: SmaCrossStrategy,
    RsiReversionStrategy.name: RsiReversionStrategy,
    MacdTrendStrategy.name: MacdTrendStrategy,
    BreakoutVwapStrategy.name: BreakoutVwapStrategy,
}


def create_strategy(name: str, **params) -> Strategy:
    try:
        strategy_cls = REGISTRY[name]
    except KeyError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Unknown strategy: {name}") from exc
    return strategy_cls(**params)


__all__ = [
    "REGISTRY",
    "BreakoutVwapStrategy",
    "MacdTrendStrategy",
    "RsiReversionStrategy",
    "Signal",
    "SmaCrossStrategy",
    "Strategy",
    "StrategyState",
    "create_strategy",
]
