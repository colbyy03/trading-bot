# Trading Bot

Production-ready Polygon.io powered trading bot with backtesting, walk-forward optimization, and live Discord alerts.

## Features

- Polygon Stocks Starter compatible data pipeline with parquet caching.
- Vectorized technical indicators (SMA/EMA/RSI/MACD/Bollinger/VWAP).
- Strategy framework with SMA crossover, RSI reversion, MACD trend, and VWAP breakout samples.
- Backtesting engine with benchmark comparison, metrics, and Matplotlib reporting.
- Walk-forward grid search utilities and Typer-powered CLI (`tb`).
- Live alert runtime streaming delayed Polygon aggregates and posting to Discord.
- Notebook quickstart and comprehensive test suite.

## Getting Started

### Prerequisites

- Python 3.11+
- Polygon Stocks Starter API key (set via `POLYGON_API_KEY`).
- Discord webhook URL for alerts (set via `DISCORD_WEBHOOK_URL`).

### Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"

> **Note for Zsh users:** if you are using `zsh`, make sure to wrap `.[dev]` in quotes (as shown above) so the shell does not try to expand it as a glob pattern.
```

Copy `.env.example` to `.env` and populate the secrets or export them in your shell.

### CLI Usage

```bash
# Fetch historical aggregates (cached to .cache/)
tb fetch --ticker SPY --start 2023-01-01 --end 2023-03-31 --bar-size 1min

# Run a backtest using config.yaml and write reports/demo_sma
 tb backtest --config config.yaml --report-name demo_sma

# Walk-forward grid search
 tb optimize --strategy sma_cross --ticker SPY --bar-size 1min --grid '{"fast":[5,10,20],"slow":[30,50,100]}'

# Start live alert runtime (15-minute delayed data per plan)
 tb live --config config.yaml

# Rebuild plots for an existing report
 tb plot --report reports/demo_sma/summary.json
```

Reports are stored under `reports/<name>` and include CSV equity curves, trades, summary JSON, benchmark comparison, and PNG plots.

### Live Alerts

Live streaming uses the Polygon delayed aggregates feed and posts BUY/SELL embeds to Discord when the configured strategy changes state. Alerts include price, timestamp, strategy parameters, indicator snapshots, and a reminder of delayed data due to plan limitations.

### Tests & Quality

```bash
pytest
ruff check trading_bot tests
ruff format trading_bot tests
mypy trading_bot
```

### Adding a Custom Strategy

1. Create a new file under `trading_bot/strategies/` (e.g. `my_strategy.py`) implementing the `Strategy` interface from `base.py`.
2. Define `default_params`, `param_space`, `prepare`, and `on_bar` methods.
3. Register the strategy in `trading_bot/strategies/__init__.py` by adding it to the `REGISTRY` dictionary.
4. Update your configuration file to reference the new strategy name and parameters.

### Notebook Quickstart

Open `examples/quickstart.ipynb` for an end-to-end example fetching SPY data, running an SMA crossover backtest, and generating a report.

### Notes on Polygon Plan Limits

- Historical fetches are capped to the last five years; the CLI validates `start`/`end` inputs accordingly.
- Live aggregates are delayed by 15 minutes; the live runtime logs this constraint prominently.

## License

MIT License. See [LICENSE](LICENSE) for details.
