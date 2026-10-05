from html import escape

from django.utils import timezone

from apps.accounts.views import upsert_telegram_user
from apps.shop.models import Order

from .api import send_message, webapp_keyboard
from .texts import t


def handle_update(update: dict) -> None:
    message = update.get("message")
    if not message or message.get("chat", {}).get("type") != "private":
        return
    sender = message.get("from") or {}
    if not sender.get("id") or sender.get("is_bot"):
        return

    user = upsert_telegram_user(sender)
    lang = sender.get("language_code")
    tx = t(lang)
    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()
    command = text.split()[0].split("@")[0].lower() if text.startswith("/") else ""

    if command == "/start":
        name = escape(sender.get("first_name") or "do'st")
        send_message(chat_id, tx["start"].format(name=name), reply_markup=webapp_keyboard(tx["open"]))
    elif command == "/shop":
        send_message(chat_id, tx["shop"], reply_markup=webapp_keyboard(tx["open"], "home"))
    elif command == "/orders":
        orders = list(Order.objects.filter(user=user).order_by("-created_at")[:5])
        if not orders:
            send_message(chat_id, tx["orders_empty"], reply_markup=webapp_keyboard(tx["open"], "home"))
            return
        body = tx["orders_title"] + "".join(
            tx["orders_line"].format(
                id=o.id,
                date=timezone.localtime(o.created_at).strftime("%d.%m.%Y"),
                total=f"{o.total:.2f}",
                status=tx["status"].get(o.status, o.status),
            )
            for o in orders
        )
        send_message(chat_id, body, reply_markup=webapp_keyboard(tx["orders_open"], "orders"))
    elif command == "/help":
        send_message(chat_id, tx["help"])
    else:
        send_message(chat_id, tx["unknown"], reply_markup=webapp_keyboard(tx["open"]))
