"""Notifier registry — add channels here without touching schema or checker."""
import datetime as dt

from . import db
from .checker import send_discord


def send(channel: str, content: str) -> bool:
    if channel != "discord":
        return False  # 'none' and unknown channels drop silently
    webhook = db.get_setting("discord_webhook")
    ok = bool(webhook) and send_discord(webhook, content)
    if ok:
        db.set_setting("notify_failed", "")
        return True
    # A dropped alert must leave a trace: container log plus a UI warning
    # that stays until the next successful send.
    lines = content.count("\n") + 1
    why = "no webhook configured" if not webhook else "send failed"
    print(f"[domain-watcher] ALERT NOT DELIVERED ({why}): {lines} line(s)", flush=True)
    now = dt.datetime.now().isoformat(timespec="seconds")
    db.set_setting("notify_failed", f"{now} · {why} · {lines} alert line(s) lost")
    return False


CHANNELS = ["discord", "none"]
