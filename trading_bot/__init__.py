"""Trading bot package exposing backtesting and live alerting utilities."""

from importlib.metadata import PackageNotFoundError, version

try:  # pragma: no cover - handled at runtime
    __version__ = version("trading-bot")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

__all__ = ["__version__"]
