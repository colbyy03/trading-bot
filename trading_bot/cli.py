"""Command line interface for the trading bot."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pandas as pd
import typer

from trading_bot.backtest import BacktestEngine, grid_search
from trading_bot.config import Config, StrategyConfig, load_config
from trading_bot.data import PolygonDataSource, cache_key
from trading_bot.live.signal_runtime import LiveSignalRuntime

DEFAULT_CONFIG_PATH = Path("config.yaml")
DEFAULT_REPORT_NAME = "run"

app = typer.Typer(help="Trading bot CLI")


@app.command()
def fetch(
    ticker: str = typer.Option(..., help="Ticker symbol"),
    start: str = typer.Option(..., help="Start date (YYYY-MM-DD)"),
    end: str = typer.Option(..., help="End date (YYYY-MM-DD)"),
    bar_size: str = typer.Option("1min", help="Bar size (1min or 1sec)"),
    force: bool = typer.Option(False, help="Force re-download"),
) -> None:
    """Fetch and cache historical data."""

    ds = PolygonDataSource()
    df = ds.fetch_and_cache(ticker, start, end, bar_size, force=force)
    path = cache_key(ticker, bar_size, start, end)
    typer.echo(f"Fetched {len(df)} rows. Saved to {path}")


@app.command()
def backtest(
    config: Path = typer.Option(DEFAULT_CONFIG_PATH, help="Path to config"),  # noqa: B008
    report_name: str = typer.Option(DEFAULT_REPORT_NAME, help="Report folder name"),
) -> None:
    """Run a backtest and write a report."""

    cfg = load_config(config)
    ticker = cfg.tickers[0]
    ds = PolygonDataSource()
    df = ds.fetch_and_cache(
        ticker,
        cfg.start or "2018-01-01",
        cfg.end or "2024-01-01",
        cfg.bar_size,
    )
    engine = BacktestEngine()
    report_path = Path("reports") / report_name
    engine.run(df, cfg, report_path)
    typer.echo(f"Backtest complete. Summary saved to {report_path / 'summary.json'}")


@app.command()
def optimize(
    strategy: str = typer.Option(..., help="Strategy name"),
    ticker: str = typer.Option(...),
    bar_size: str = typer.Option("1min"),
    grid: str = typer.Option(..., help="JSON parameter grid"),
    start: str = typer.Option("2020-01-01"),
    end: str = typer.Option("2023-12-31"),
) -> None:
    """Grid search optimization for a strategy."""

    param_grid = json.loads(grid)
    ds = PolygonDataSource()
    data = ds.fetch_and_cache(ticker, start, end, bar_size)
    cfg = Config(
        tickers=[ticker],
        bar_size=bar_size,
        start=start,
        end=end,
        strategy=StrategyConfig(name=strategy, params={}),
    )
    result = grid_search(data, cfg, param_grid)
    typer.echo(f"Best Sharpe: {result.sharpe:.2f} params={result.params} trades={result.trades}")


@app.command()
def live(
    config: Path = typer.Option(DEFAULT_CONFIG_PATH, help="Config file"),  # noqa: B008
) -> None:
    """Run the live alert runtime."""

    cfg = load_config(config)
    runtime = LiveSignalRuntime(cfg)
    asyncio.run(runtime.run())


@app.command()
def plot(report: Path = typer.Option(..., help="Path to summary.json")) -> None:  # noqa: B008
    """Re-render plots for an existing report."""

    report_dir = report.parent
    equity = pd.read_csv(report_dir / "equity_curve.csv", index_col=0, parse_dates=True).squeeze()
    benchmark = pd.read_csv(
        report_dir / "benchmark_curve.csv", index_col=0, parse_dates=True
    ).squeeze()
    from trading_bot.backtest.plotting import generate_plots

    generate_plots(report_dir, equity, benchmark)
    typer.echo(f"Plots re-generated in {report_dir}")


if __name__ == "__main__":  # pragma: no cover
    app()
