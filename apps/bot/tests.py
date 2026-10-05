import json
from unittest import mock

from django.test import TestCase, override_settings

from apps.accounts.models import User
from apps.shop.models import Order

SECRET = "s3cret"
URL = "/api/telegram/webhook/"


def update(text, user_id=42, lang="uz", chat_type="private"):
    return {
        "update_id": 1,
        "message": {
            "message_id": 1,
            "from": {"id": user_id, "is_bot": False, "first_name": "Ali", "language_code": lang},
            "chat": {"id": user_id, "type": chat_type},
            "text": text,
        },
    }


@override_settings(TELEGRAM_BOT_TOKEN="1:T", TELEGRAM_WEBHOOK_SECRET=SECRET, WEBAPP_URL="https://shop.example")
@mock.patch("apps.bot.api.requests.post")
class WebhookTests(TestCase):
    def post(self, body, secret=SECRET):
        return self.client.post(URL, json.dumps(body), content_type="application/json",
                                HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN=secret)

    def sent(self, post):
        return post.call_args.kwargs["json"]

    def test_rejects_wrong_secret(self, post):
        self.assertEqual(self.post(update("/start"), secret="nope").status_code, 403)
        post.assert_not_called()

    def test_start_sends_webapp_button_and_creates_user(self, post):
        self.assertEqual(self.post(update("/start")).status_code, 200)
        msg = self.sent(post)
        self.assertIn("Assalomu alaykum", msg["text"])
        button = msg["reply_markup"]["inline_keyboard"][0][0]
        self.assertEqual(button["web_app"]["url"], "https://shop.example/")
        self.assertTrue(User.objects.filter(telegram_id=42).exists())

    def test_english_for_other_languages(self, post):
        self.post(update("/start", lang="ru"))
        self.assertIn("Hi,", self.sent(post)["text"])

    def test_start_with_bot_suffix_and_payload(self, post):
        self.post(update("/start@Shopping_app1_bot promo"))
        self.assertIn("Shoer.lk", self.sent(post)["text"])

    def test_orders_lists_recent(self, post):
        self.post(update("/start"))
        user = User.objects.get(telegram_id=42)
        Order.objects.create(user=user, phone="1234567", address="A", subtotal=10, shipping_fee=1, total=11)
        self.post(update("/orders"))
        msg = self.sent(post)
        self.assertIn("$11.00", msg["text"])
        self.assertTrue(msg["reply_markup"]["inline_keyboard"][0][0]["web_app"]["url"].endswith("/orders"))

    def test_orders_empty(self, post):
        self.post(update("/orders", lang="en"))
        self.assertIn("no orders", self.sent(post)["text"])

    def test_ignores_groups(self, post):
        self.post(update("/start", chat_type="group"))
        post.assert_not_called()

    def test_handler_error_still_returns_200(self, post):
        with mock.patch("apps.bot.views.handle_update", side_effect=RuntimeError):
            self.assertEqual(self.post(update("/start")).status_code, 200)

    def test_unknown_text(self, post):
        self.post(update("salom"))
        self.assertIn("/help", self.sent(post)["text"])




@override_settings(TELEGRAM_BOT_TOKEN="123:SECRET")
class ApiTests(TestCase):
    @mock.patch("apps.bot.api.time.sleep")
    @mock.patch("apps.bot.api.requests.post")
    def test_retries_and_never_logs_token(self, post, sleep):
        import requests

        from apps.bot.api import call

        post.side_effect = requests.ConnectionError("url: /bot123:SECRET/getMe proxy 503")
        with self.assertLogs("apps.bot.api", "WARNING") as logs:
            self.assertIsNone(call("getMe", retries=2))
        self.assertEqual(post.call_count, 3)
        self.assertNotIn("123:SECRET", "\n".join(logs.output))
        self.assertIn("<token>", logs.output[0])
