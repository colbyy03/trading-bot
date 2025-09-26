"""Plotting helpers for backtests."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

plt.switch_backend("Agg")


def _plot_equity(report_path: Path, equity: pd.Series, benchmark: pd.Series) -> None:
    fig, ax = plt.subplots(figsize=(10, 5))
    equity.plot(ax=ax, label="Strategy")
    benchmark.plot(ax=ax, label="Benchmark")
    ax.set_title("Equity Curve")
    ax.set_ylabel("Equity ($)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(report_path / "equity_curve.png")
    plt.close(fig)


def _plot_drawdown(report_path: Path, equity: pd.Series) -> None:
    cummax = equity.cummax()
    drawdown = equity / cummax - 1
    fig, ax = plt.subplots(figsize=(10, 3))
    drawdown.plot(ax=ax, color="red")
    ax.set_title("Drawdown")
    ax.set_ylabel("Drawdown")
    fig.tight_layout()
    fig.savefig(report_path / "drawdown.png")
    plt.close(fig)


def _plot_rolling_sharpe(report_path: Path, equity: pd.Series, window: int = 63) -> None:
    returns = equity.pct_change().dropna()
    sharpe = returns.rolling(window=window).mean() / returns.rolling(window=window).std()
    fig, ax = plt.subplots(figsize=(10, 3))
    sharpe.plot(ax=ax, color="purple")
    ax.set_title(f"Rolling Sharpe ({window} bars)")
    fig.tight_layout()
    fig.savefig(report_path / "rolling_sharpe.png")
    plt.close(fig)


def generate_plots(report_path: Path, equity: pd.Series, benchmark: pd.Series) -> None:
    _plot_equity(report_path, equity, benchmark)
    _plot_drawdown(report_path, equity)
    _plot_rolling_sharpe(report_path, equity)


__all__ = ["generate_plots"]
