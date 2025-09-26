"""Vectorized backtest engine with basic risk management."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import structlog

from trading_bot.config import Config
from trading_bot.strategies import Signal, create_strategy

from .benchmark import buy_and_hold_benchmark
from .metrics import PerformanceSummary, summarize_backtest
from .plotting import generate_plots

log = structlog.get_logger(__name__)


@dataclass
class Trade:
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    qty: float
    entry_price: float
    exit_price: float
    pnl: float

    def to_dict(self) -> dict[str, float]:
        return {
            "entry_time": self.entry_time.isoformat(),
            "exit_time": self.exit_time.isoformat(),
            "qty": self.qty,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "pnl": self.pnl,
        }


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    positions: pd.Series
    exposures: pd.Series
    trades: list[Trade]
    summary: PerformanceSummary
    benchmark: PerformanceSummary
    signals: pd.Series


class BacktestEngine:
    """Event-driven long-only backtest engine."""

    def __init__(self, starting_equity: float = 100_000.0) -> None:
        self.starting_equity = starting_equity

    def run(self, data: pd.DataFrame, config: Config, report_path: Path) -> BacktestResult:
        if data.empty:
            raise ValueError("No data provided for backtest")
        strategy = create_strategy(config.strategy.name, **config.strategy.params)
        state = strategy.prepare(data)

        transaction_cost = config.transaction_cost_bps / 10_000
        slippage = config.slippage_bps / 10_000

        cash = self.starting_equity
        position = 0.0
        entry_price = 0.0
        entry_time: pd.Timestamp | None = None
        trades: list[Trade] = []

        equity_curve: list[float] = []
        positions: list[float] = []
        exposures: list[float] = []
        signals: list[str] = []
        index: list[pd.Timestamp] = []

        def close_position(timestamp: pd.Timestamp, price: float, reason: str) -> None:
            nonlocal cash, position, entry_price, entry_time
            if position == 0 or entry_time is None:
                return
            trade_price = price * (1 - slippage)
            proceeds = position * trade_price
            cost = proceeds * transaction_cost
            cash += proceeds - cost
            pnl = (trade_price - entry_price) * position - cost
            trades.append(
                Trade(
                    entry_time=entry_time,
                    exit_time=timestamp,
                    qty=position,
                    entry_price=entry_price,
                    exit_price=trade_price,
                    pnl=pnl,
                )
            )
            log.info("backtest.close", time=timestamp.isoformat(), reason=reason, pnl=pnl)
            position = 0.0
            entry_price = 0.0
            entry_time = None

        for timestamp, bar in data.iterrows():
            price = float(bar["close"])
            signal, confidence = strategy.on_bar(bar, state)
            equity = cash + position * price
            target_qty = position
            if signal is Signal.BUY:
                target_qty = strategy.position_sizing(signal, equity, price, config.risk)
            elif signal is Signal.SELL:
                target_qty = 0.0
            qty_change = target_qty - position
            if qty_change > 0:  # open/scale long
                trade_price = price * (1 + slippage)
                cost = qty_change * trade_price * transaction_cost
                cash -= qty_change * trade_price + cost
                position += qty_change
                entry_price = trade_price if entry_price == 0 else (entry_price + trade_price) / 2
                entry_time = timestamp if entry_time is None else entry_time
                log.info(
                    "backtest.buy",
                    time=timestamp.isoformat(),
                    qty=qty_change,
                    price=trade_price,
                )
            elif qty_change < 0:
                trade_price = price * (1 - slippage)
                qty_to_close = min(position, -qty_change)
                proceeds = qty_to_close * trade_price
                cost = proceeds * transaction_cost
                cash += proceeds - cost
                pnl = (trade_price - entry_price) * qty_to_close - cost
                trades.append(
                    Trade(
                        entry_time=entry_time or timestamp,
                        exit_time=timestamp,
                        qty=qty_to_close,
                        entry_price=entry_price,
                        exit_price=trade_price,
                        pnl=pnl,
                    )
                )
                position -= qty_to_close
                if position == 0:
                    entry_price = 0.0
                    entry_time = None
                log.info(
                    "backtest.sell",
                    time=timestamp.isoformat(),
                    qty=qty_to_close,
                    price=trade_price,
                )

            equity = cash + position * price
            if position > 0 and entry_price > 0:
                change = (price - entry_price) / entry_price
                if config.risk.stop_loss and change <= -config.risk.stop_loss:
                    close_position(timestamp, price, "stop_loss")
                    equity = cash
                elif config.risk.take_profit and change >= config.risk.take_profit:
                    close_position(timestamp, price, "take_profit")
                    equity = cash

            equity_curve.append(equity)
            positions.append(position)
            exposures.append(abs(position * price) / equity if equity else 0.0)
            signals.append(signal.value)
            index.append(timestamp)

        if position > 0 and entry_time is not None:
            close_position(index[-1], float(data.iloc[-1]["close"]), "final")

        equity_series = pd.Series(equity_curve, index=index, name="equity")
        position_series = pd.Series(positions, index=index, name="position")
        exposure_series = pd.Series(exposures, index=index, name="exposure")
        signal_series = pd.Series(signals, index=index, name="signal")

        trade_returns = [trade.pnl / self.starting_equity for trade in trades]
        summary = summarize_backtest(equity_series, trade_returns, exposure_series)

        benchmark_series = buy_and_hold_benchmark(data, config.benchmark_ticker)
        benchmark_summary = summarize_backtest(
            benchmark_series,
            [],
            pd.Series(index=benchmark_series.index, data=0.0),
        )

        self._export(
            report_path,
            equity_series,
            position_series,
            trades,
            summary,
            benchmark_summary,
            benchmark_series,
            signal_series,
        )

        return BacktestResult(
            equity_curve=equity_series,
            positions=position_series,
            exposures=exposure_series,
            trades=trades,
            summary=summary,
            benchmark=benchmark_summary,
            signals=signal_series,
        )

    def _export(
        self,
        report_path: Path,
        equity: pd.Series,
        positions: pd.Series,
        trades: list[Trade],
        summary: PerformanceSummary,
        benchmark: PerformanceSummary,
        benchmark_curve: pd.Series,
        signals: pd.Series,
    ) -> None:
        report_path.mkdir(parents=True, exist_ok=True)
        equity.to_csv(report_path / "equity_curve.csv")
        positions.to_csv(report_path / "positions.csv")
        signals.to_csv(report_path / "signals.csv")
        trades_df = pd.DataFrame([t.to_dict() for t in trades])
        trades_df.to_csv(report_path / "trades.csv", index=False)
        summary_payload = pd.Series(summary.to_dict()).to_json(indent=2)
        benchmark_payload = pd.Series(benchmark.to_dict()).to_json(indent=2)
        (report_path / "summary.json").write_text(summary_payload)
        (report_path / "benchmark.json").write_text(benchmark_payload)
        benchmark_curve.to_csv(report_path / "benchmark_curve.csv")
        generate_plots(report_path, equity, benchmark_curve)


__all__ = ["BacktestEngine", "BacktestResult", "Trade"]
