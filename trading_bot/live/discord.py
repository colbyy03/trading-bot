"""Discord webhook utilities."""

from __future__ import annotations

import os
import time
from typing import Any

import requests
import structlog

log = structlog.get_logger(__name__)

DEFAULT_RETRIES = 3
DEFAULT_BACKOFF = 2.0


def build_embed(signal: str, ticker: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Construct a Discord embed payload."""

    color = 0x808080
    if signal.lower() == "buy":
        color = 0x00FF00
    elif signal.lower() == "sell":
        color = 0xFF0000
    return {
        "title": f"Signal: {signal.upper()} ({ticker})",
        "color": color,
        "fields": [
            {"name": key, "value": str(value), "inline": True} for key, value in payload.items()
        ],
    }


def send_alert(
    signal: str,
    ticker: str,
    payload: dict[str, Any],
    webhook_url: str | None = None,
    retries: int = DEFAULT_RETRIES,
) -> None:
    """Send an alert to Discord with retries."""

    url = webhook_url or os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        raise RuntimeError("DISCORD_WEBHOOK_URL is not configured")

    body = {"embeds": [build_embed(signal, ticker, payload)]}

    for attempt in range(1, retries + 1):
        response = requests.post(url, json=body, timeout=10)
        if response.status_code < 300:
            log.info("discord.alert_sent", signal=signal, ticker=ticker)
            return
        log.warning(
            "discord.alert_failed",
            status=response.status_code,
            body=response.text,
            attempt=attempt,
        )
        time.sleep(DEFAULT_BACKOFF ** attempt)
    response.raise_for_status()


__all__ = ["build_embed", "send_alert"]
