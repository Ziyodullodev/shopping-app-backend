"""Order notifications through the Telegram Bot API. Failures are logged and never break checkout."""
import logging
from html import escape

import requests
from django.conf import settings

log = logging.getLogger(__name__)


def _send(chat_id, text: str) -> None:
    token = settings.TELEGRAM_BOT_TOKEN
    if not token or not chat_id:
        return
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=5,
        )
        if not resp.ok:
            log.warning("Telegram sendMessage failed (%s): %s", resp.status_code, resp.text[:200])
    except requests.RequestException as exc:
        log.warning("Telegram sendMessage error: %s", exc)


def _items_text(order) -> str:
    return "\n".join(
        f"• {escape(i.product_name)} (EU {i.size}) × {i.quantity} — ${i.line_total:.2f}" for i in order.items.all()
    )


def notify_order_created(order) -> None:
    items = _items_text(order)
    _send(
        order.user.telegram_id,
        f"✅ <b>Order #{order.pk} received</b>\n\n{items}\n\n"
        f"Total: <b>${order.total:.2f}</b>\nWe will contact you at {escape(order.phone)} to confirm delivery.",
    )
    _send(
        settings.TELEGRAM_ADMIN_CHAT_ID,
        f"🛒 <b>New order #{order.pk}</b>\n"
        f"Customer: {escape(order.full_name or order.user.display_name)}"
        f"{' (@' + escape(order.user.username) + ')' if order.user.telegram_id and order.user.username else ''}\n"
        f"Phone: {escape(order.phone)}\nAddress: {escape(order.address)}\n"
        f"Payment: {order.get_payment_method_display()}\n"
        f"{'Comment: ' + escape(order.comment) + chr(10) if order.comment else ''}\n{items}\n\n"
        f"Total: <b>${order.total:.2f}</b>",
    )


def notify_status_changed(order) -> None:
    _send(order.user.telegram_id, f"📦 Order #{order.pk} is now <b>{order.get_status_display()}</b>.")
