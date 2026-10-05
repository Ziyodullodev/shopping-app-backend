"""Minimal Telegram Bot API client. Errors are logged, never raised, so bot hiccups don't break requests."""
import logging

import requests
from django.conf import settings

log = logging.getLogger(__name__)


def call(method: str, **payload) -> dict | None:
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return None
    try:
        resp = requests.post(f"https://api.telegram.org/bot{token}/{method}", json=payload, timeout=10)
        data = resp.json()
        if not data.get("ok"):
            log.warning("Telegram %s failed: %s", method, data.get("description"))
        return data
    except (requests.RequestException, ValueError) as exc:
        log.warning("Telegram %s error: %s", method, exc)
        return None


def send_message(chat_id, text: str, **extra) -> dict | None:
    if not chat_id:
        return None
    return call("sendMessage", chat_id=chat_id, text=text, parse_mode="HTML", disable_web_page_preview=True, **extra)


def webapp_url(path: str = "") -> str:
    return settings.WEBAPP_URL.rstrip("/") + "/" + path.lstrip("/")


def webapp_keyboard(text: str, path: str = "") -> dict:
    return {"inline_keyboard": [[{"text": text, "web_app": {"url": webapp_url(path)}}]]}
