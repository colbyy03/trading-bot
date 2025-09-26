"""Backtest performance metrics."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
import pandas as pd

TRADING_DAYS = 252


@dataclass
class PerformanceSummary:
    total_return: float
    cagr: float
    sharpe: float
    sortino: float
    volatility: float
    max_drawdown: float
    max_drawdown_duration: int
    win_rate: float
    avg_trade: float
    trades: int
    exposure: float
    turnover: float
    best_trade: float
    worst_trade: float

    def to_dict(self) -> dict[str, float]:
        return self.__dict__.copy()


def _annualize_return(series: pd.Series) -> float:
    total_return = series.iloc[-1] / series.iloc[0] - 1
    num_days = (series.index[-1] - series.index[0]).days or 1
    years = num_days / 365.25
    return (1 + total_return) ** (1 / years) - 1 if years > 0 else total_return


def _sharpe_ratio(returns: pd.Series, risk_free: float = 0.0) -> float:
    excess = returns - risk_free / TRADING_DAYS
    std = excess.std()
    if std == 0 or math.isnan(std):
        return 0.0
    return (excess.mean() / std) * math.sqrt(TRADING_DAYS)


def _sortino_ratio(returns: pd.Series, risk_free: float = 0.0) -> float:
    downside = returns[returns < 0]
    downside_std = downside.std()
    if downside_std == 0 or math.isnan(downside_std):
        return 0.0
    return ((returns.mean() - risk_free / TRADING_DAYS) / downside_std) * math.sqrt(TRADING_DAYS)


def max_drawdown(equity: pd.Series) -> tuple[float, int]:
    cummax = equity.cummax()
    drawdown = equity / cummax - 1
    max_dd = drawdown.min()
    durations = (drawdown == 0).astype(int)
    max_duration = (durations.groupby((durations != durations.shift()).cumsum()).cumsum().max())
    return float(max_dd), int(max_duration if not math.isnan(max_duration) else 0)


def summarize_backtest(
    equity: pd.Series, trades: Iterable[float], exposures: pd.Series
) -> PerformanceSummary:
    returns = equity.pct_change().dropna()
    total_return = equity.iloc[-1] / equity.iloc[0] - 1
    cagr = _annualize_return(equity)
    sharpe = _sharpe_ratio(returns)
    sortino = _sortino_ratio(returns)
    volatility = returns.std() * math.sqrt(TRADING_DAYS)
    max_dd, max_dd_duration = max_drawdown(equity)
    trades_list = list(trades)
    wins = [t for t in trades_list if t > 0]
    win_rate = len(wins) / len(trades_list) if trades_list else 0.0
    avg_trade = float(np.mean(trades_list)) if trades_list else 0.0
    exposure = exposures.mean() if not exposures.empty else 0.0
    turnover = exposures.diff().abs().sum() if not exposures.empty else 0.0
    best_trade = max(trades_list) if trades_list else 0.0
    worst_trade = min(trades_list) if trades_list else 0.0
    return PerformanceSummary(
        total_return=float(total_return),
        cagr=float(cagr),
        sharpe=float(sharpe),
        sortino=float(sortino),
        volatility=float(volatility),
        max_drawdown=float(max_dd),
        max_drawdown_duration=max_dd_duration,
        win_rate=float(win_rate),
        avg_trade=float(avg_trade),
        trades=len(trades_list),
        exposure=float(exposure),
        turnover=float(turnover),
        best_trade=float(best_trade),
        worst_trade=float(worst_trade),
    )


__all__ = ["PerformanceSummary", "max_drawdown", "summarize_backtest"]
