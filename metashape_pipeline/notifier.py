"""Optional notifications; failures never fail processing."""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Protocol


class Notifier(Protocol):
    def send(self, message: str) -> None: ...


class NoOpNotifier:
    def send(self, message: str) -> None:
        return None


class TelegramNotifier:
    def __init__(self, token: str | None = None, chat_id: str | None = None):
        self.token = token or os.environ.get("DRONE_METASHAPE_TELEGRAM_TOKEN")
        self.chat_id = chat_id or os.environ.get("DRONE_METASHAPE_TELEGRAM_CHAT_ID")
        if not self.token or not self.chat_id:
            raise ValueError("Telegram runtime environment is incomplete")

    def send(self, message: str) -> None:
        body = json.dumps({"chat_id": self.chat_id, "text": message}).encode("utf-8")
        request = urllib.request.Request(
            f"https://api.telegram.org/bot{self.token}/sendMessage",
            data=body, headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(request, timeout=10):
            pass


def notify_safely(notifier: Notifier, message: str, log) -> None:
    try:
        notifier.send(message)
    except Exception as exc:
        log(f"Notifier warning: {type(exc).__name__}: {exc}")
