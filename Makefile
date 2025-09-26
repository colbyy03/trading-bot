.PHONY: install test lint typecheck format run

install:
python -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -e .[dev]

lint:
ruff check trading_bot tests
ruff format --check trading_bot tests

format:
ruff format trading_bot tests

typecheck:
mypy trading_bot

test:
pytest

run:
python -m trading_bot.cli --help
