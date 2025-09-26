"""Walk-forward and cross-validation utilities."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import ParameterGrid, TimeSeriesSplit

from trading_bot.config import Config

from .engine import BacktestEngine


@dataclass
class OptimizationResult:
    params: dict[str, float]
    sharpe: float
    trades: int


def grid_search(
    data: pd.DataFrame,
    config: Config,
    param_grid: dict[str, Iterable],
    splits: int = 3,
) -> OptimizationResult:
    """Perform a simple walk-forward grid search returning the best Sharpe."""

    tscv = TimeSeriesSplit(n_splits=splits)
    best_result = OptimizationResult(params={}, sharpe=float("-inf"), trades=0)
    engine = BacktestEngine()
    for params in ParameterGrid(param_grid):
        sharpes: list[float] = []
        trade_counts: list[int] = []
        for fold, (_, test_idx) in enumerate(tscv.split(data)):
            test = data.iloc[test_idx]
            test_config = config.model_copy(
                update={"strategy": {"name": config.strategy.name, "params": params}}
            )
            tmp_report = Path("reports/_opt") / f"fold_{fold}"
            engine_result = engine.run(test, test_config, report_path=tmp_report)
            sharpes.append(engine_result.summary.sharpe)
            trade_counts.append(engine_result.summary.trades)
        avg_sharpe = float(np.mean(sharpes)) if sharpes else float("-inf")
        min_trades = min(trade_counts) if trade_counts else 0
        if avg_sharpe > best_result.sharpe and min_trades >= 1:
            best_result = OptimizationResult(
                params=dict(params), sharpe=avg_sharpe, trades=min_trades
            )
    return best_result


__all__ = ["OptimizationResult", "grid_search"]
