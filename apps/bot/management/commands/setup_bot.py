from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.bot.api import call, webapp_url

COMMANDS = {
    "uz": [("start", "Do'konni ochish"), ("shop", "Katalog"), ("orders", "Buyurtmalarim"), ("help", "Yordam")],
    "en": [("start", "Open the shop"), ("shop", "Catalogue"), ("orders", "My orders"), ("help", "Help")],
}


class Command(BaseCommand):
    help = "Register the webhook, command list and Mini App menu button with Telegram."

    def handle(self, *args, **options):
        if not settings.TELEGRAM_BOT_TOKEN:
            raise CommandError("TELEGRAM_BOT_TOKEN is empty")
        if not settings.TELEGRAM_WEBHOOK_SECRET:
            raise CommandError("TELEGRAM_WEBHOOK_SECRET is empty")

        hook = webapp_url("api/telegram/webhook/")
        steps = [
            ("setWebhook", dict(url=hook, secret_token=settings.TELEGRAM_WEBHOOK_SECRET,
                                allowed_updates=["message"], drop_pending_updates=True)),
            ("setMyCommands", dict(commands=[{"command": c, "description": d} for c, d in COMMANDS["en"]])),
            ("setMyCommands", dict(commands=[{"command": c, "description": d} for c, d in COMMANDS["uz"]], language_code="uz")),
            ("setChatMenuButton", dict(menu_button={"type": "web_app", "text": "Shop", "web_app": {"url": webapp_url()}})),
        ]
        failed = False
        for method, payload in steps:
            res = call(method, **payload) or {}
            ok = res.get("ok")
            failed |= not ok
            self.stdout.write(f"{method}: {'ok' if ok else res.get('description', 'no response')}")

        info = (call("getWebhookInfo") or {}).get("result", {})
        self.stdout.write(f"webhook: {info.get('url')} pending={info.get('pending_update_count')} last_error={info.get('last_error_message')}")
        if failed:
            raise CommandError("Some steps failed, see above.")
        self.stdout.write(self.style.SUCCESS("Bot is ready."))
