import time
from unittest import mock

from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.accounts.telegram import InitDataError, sign_init_data, validate_init_data
from apps.catalog.models import ProductSize

BOT_TOKEN = "123456:TEST-TOKEN"


def init_data(user_id=777, **extra):
    fields = {
        "query_id": "AAE",
        "user": {"id": user_id, "first_name": "Ali", "username": "ali_test", "language_code": "uz"},
        "auth_date": int(time.time()),
        **extra,
    }
    return sign_init_data(fields, BOT_TOKEN)


class InitDataTests(TestCase):
    def test_valid(self):
        data = validate_init_data(init_data(), BOT_TOKEN)
        self.assertEqual(data.user["id"], 777)

    def test_tampered(self):
        bad = init_data().replace("Ali", "Bob")
        with self.assertRaises(InitDataError):
            validate_init_data(bad, BOT_TOKEN)

    def test_wrong_token(self):
        with self.assertRaises(InitDataError):
            validate_init_data(init_data(), "999:OTHER")

    def test_expired(self):
        old = init_data(auth_date=int(time.time()) - 10_000)
        with self.assertRaises(InitDataError):
            validate_init_data(old, BOT_TOKEN, max_age=3600)


@override_settings(TELEGRAM_BOT_TOKEN=BOT_TOKEN, TELEGRAM_ADMIN_CHAT_ID="", TELEGRAM_DEV_AUTH=False, SHIPPING_FEE="4.99")
class ShopFlowTests(TestCase):
    def setUp(self):
        call_command("seed_catalog", stdout=open("/dev/null", "w"))
        self.client = APIClient()

    def login(self, user_id=777):
        res = self.client.post("/api/auth/telegram/", {"init_data": init_data(user_id)}, format="json")
        self.assertEqual(res.status_code, 200, res.content)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {res.data['access']}")
        return res.data

    def test_auth_rejects_bad_init_data(self):
        res = self.client.post("/api/auth/telegram/", {"init_data": "user=%7B%7D&hash=abc"}, format="json")
        self.assertEqual(res.status_code, 401)

    def test_auth_creates_user_once(self):
        first = self.login()
        second = self.login()
        self.assertEqual(first["user"]["id"], second["user"]["id"])
        self.assertEqual(first["user"]["username"], "ali_test")

    def test_catalog_is_public_and_filterable(self):
        res = self.client.get("/api/products/?brand=nike&ordering=price")
        self.assertEqual(res.status_code, 200)
        prices = [float(p["price"]) for p in res.data["results"]]
        self.assertEqual(len(prices), 2)
        self.assertEqual(prices, sorted(prices))
        detail = self.client.get("/api/products/casual-brown/")
        self.assertEqual(detail.data["sizes"][0]["size"], 39)

    def test_cart_requires_auth(self):
        self.assertEqual(self.client.get("/api/cart/").status_code, 401)

    def test_favorites(self):
        self.login()
        self.client.post("/api/favorites/", {"product": "casual-blue"}, format="json")
        self.assertEqual([p["slug"] for p in self.client.get("/api/favorites/").data], ["casual-blue"])
        product = self.client.get("/api/products/casual-blue/").data
        self.assertTrue(product["is_favorite"])
        self.client.delete("/api/favorites/casual-blue/")
        self.assertEqual(self.client.get("/api/favorites/").data, [])

    def test_cart_add_increment_update_remove(self):
        self.login()
        self.client.post("/api/cart/items/", {"product": "casual-brown", "size": 42}, format="json")
        res = self.client.post("/api/cart/items/", {"product": "casual-brown", "size": 42}, format="json")
        self.assertEqual(res.data["count"], 2)
        self.assertEqual(res.data["subtotal"], "46.18")
        self.assertEqual(res.data["total"], "51.17")
        item_id = res.data["items"][0]["id"]
        res = self.client.patch(f"/api/cart/items/{item_id}/", {"quantity": 5}, format="json")
        self.assertEqual(res.data["count"], 5)
        res = self.client.patch(f"/api/cart/items/{item_id}/", {"quantity": 0}, format="json")
        self.assertEqual(res.data["count"], 0)
        self.assertEqual(res.data["shipping_fee"], "0.00")

    def test_cart_set_quantity(self):
        self.login()
        res = self.client.put("/api/cart/items/", {"product": "casual-blue", "size": 41, "quantity": 4}, format="json")
        self.assertEqual(res.data["count"], 4)
        res = self.client.put("/api/cart/items/", {"product": "casual-blue", "size": 41, "quantity": 0}, format="json")
        self.assertEqual(res.data["count"], 0)

    def test_list_has_default_size(self):
        res = self.client.get("/api/products/casual-brown/")
        self.assertEqual(res.data["default_size"], 41)

    def test_cart_rejects_unknown_size(self):
        self.login()
        res = self.client.post("/api/cart/items/", {"product": "casual-brown", "size": 50}, format="json")
        self.assertEqual(res.status_code, 400)

    def test_cart_is_per_user(self):
        self.login(1)
        self.client.post("/api/cart/items/", {"product": "casual-brown"}, format="json")
        self.login(2)
        self.assertEqual(self.client.get("/api/cart/").data["count"], 0)

    @mock.patch("apps.bot.api.requests.post")
    def test_checkout_creates_order_and_reduces_stock(self, post):
        self.login()
        self.client.post("/api/cart/items/", {"product": "casual-brown", "size": 42, "quantity": 3}, format="json")
        with self.captureOnCommitCallbacks(execute=True):
            res = self.client.post(
                "/api/orders/", {"phone": "+998 90 123 45 67", "address": "Tashkent", "payment_method": "card"}, format="json"
            )
        self.assertEqual(res.status_code, 201, res.content)
        self.assertEqual(res.data["total"], "74.26")
        self.assertEqual(ProductSize.objects.get(product__slug="casual-brown", size=42).stock, 7)
        self.assertEqual(self.client.get("/api/cart/").data["count"], 0)
        self.assertEqual(len(self.client.get("/api/orders/").data["results"]), 1)
        post.assert_called_once()  # message to the customer; admin chat is not configured

        cancel = self.client.post(f"/api/orders/{res.data['id']}/cancel/")
        self.assertEqual(cancel.data["status"], "cancelled")
        self.assertEqual(ProductSize.objects.get(product__slug="casual-brown", size=42).stock, 10)

    def test_checkout_fails_when_out_of_stock(self):
        self.login()
        self.client.post("/api/cart/items/", {"product": "casual-brown", "size": 42, "quantity": 11}, format="json")
        res = self.client.post("/api/orders/", {"phone": "+998901234567", "address": "Tashkent"}, format="json")
        self.assertEqual(res.status_code, 409)
        self.assertEqual(ProductSize.objects.get(product__slug="casual-brown", size=42).stock, 10)
        self.assertEqual(self.client.get("/api/cart/").data["count"], 11)

    def test_checkout_empty_cart(self):
        self.login()
        res = self.client.post("/api/orders/", {"phone": "+998901234567", "address": "Tashkent"}, format="json")
        self.assertEqual(res.status_code, 400)

    def test_orders_are_private(self):
        self.login(1)
        self.client.post("/api/cart/items/", {"product": "casual-brown"}, format="json")
        order_id = self.client.post("/api/orders/", {"phone": "+998901234567", "address": "A"}, format="json").data["id"]
        self.login(2)
        self.assertEqual(self.client.get(f"/api/orders/{order_id}/").status_code, 404)
