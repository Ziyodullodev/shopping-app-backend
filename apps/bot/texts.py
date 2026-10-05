"""Bot copy in Uzbek and English. Uzbek is used for `uz` clients, English otherwise."""

TEXTS = {
    "uz": {
        "start": (
            "Assalomu alaykum, <b>{name}</b>! 👋\n\n"
            "<b>Shoer.lk</b> — sevimli brendlaringizdagi krossovkalar do'koni.\n"
            "Bata, Nike, Adidas, Wilson va boshqalar bitta joyda.\n\n"
            "Do'konni ochish uchun pastdagi tugmani bosing 👇"
        ),
        "open": "🛍 Do'konni ochish",
        "shop": "Katalog shu yerda 👇",
        "orders_empty": "Sizda hali buyurtmalar yo'q. Do'konni ochib, birinchi juftingizni tanlang 👇",
        "orders_title": "📦 <b>Oxirgi buyurtmalaringiz</b>\n\n",
        "orders_line": "#{id} · {date} · <b>${total}</b> · {status}\n",
        "orders_open": "📦 Buyurtmalarni ochish",
        "help": (
            "Buyruqlar:\n"
            "/start — do'konni ochish\n"
            "/shop — katalog\n"
            "/orders — buyurtmalarim\n"
            "/help — yordam\n\n"
            "Savollar bo'lsa, shu chatga yozing."
        ),
        "unknown": "Buyurtma berish uchun do'konni oching 👇 Buyruqlar ro'yxati: /help",
        "status": {"new": "🆕 Yangi", "confirmed": "✅ Tasdiqlangan", "shipped": "🚚 Yo'lda", "delivered": "🎉 Yetkazildi", "cancelled": "❌ Bekor qilingan"},
    },
    "en": {
        "start": (
            "Hi, <b>{name}</b>! 👋\n\n"
            "<b>Shoer.lk</b> is a sneaker shop for the brands you love.\n"
            "Bata, Nike, Adidas, Wilson and more in one place.\n\n"
            "Tap the button below to open the shop 👇"
        ),
        "open": "🛍 Open shop",
        "shop": "Here is the catalogue 👇",
        "orders_empty": "You have no orders yet. Open the shop and pick your first pair 👇",
        "orders_title": "📦 <b>Your recent orders</b>\n\n",
        "orders_line": "#{id} · {date} · <b>${total}</b> · {status}\n",
        "orders_open": "📦 Open my orders",
        "help": (
            "Commands:\n"
            "/start — open the shop\n"
            "/shop — catalogue\n"
            "/orders — my orders\n"
            "/help — help\n\n"
            "Questions? Just write to this chat."
        ),
        "unknown": "Open the shop to place an order 👇 Command list: /help",
        "status": {"new": "🆕 New", "confirmed": "✅ Confirmed", "shipped": "🚚 Shipped", "delivered": "🎉 Delivered", "cancelled": "❌ Cancelled"},
    },
}


def t(lang: str | None) -> dict:
    return TEXTS["uz"] if (lang or "").startswith("uz") else TEXTS["en"]
