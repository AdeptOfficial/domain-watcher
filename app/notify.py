"""Notifier registry — add channels here without touching schema or checker."""
from . import db
from .checker import send_discord


def send(channel: str, content: str) -> bool:
    if channel == "discord":
        webhook = db.get_setting("discord_webhook")
        return bool(webhook) and send_discord(webhook, content)
    return False  # 'none' and unknown channels drop silently


CHANNELS = ["discord", "none"]
