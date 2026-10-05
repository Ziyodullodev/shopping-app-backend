# Shopping App — Backend

Django REST API for the Shoer.lk Telegram Mini App. Frontend: [shopping-app-frontend](https://github.com/Ziyodullodev/shopping-app-frontend).

- Sign-in with Telegram WebApp `initData` (HMAC check against the bot token), JWT for API calls.
- Catalogue with brands, sizes and stock, filtering, search and sorting.
- Server-side wishlist and cart per Telegram user.
- Checkout that reserves stock in a transaction, order history and cancel.
- Telegram bot messages to the customer and an admin chat on new orders and status changes.
- Django admin for products, stock and orders.
- Telegram bot over a webhook: `/start`, `/shop`, `/orders`, `/help` in Uzbek and English, with Mini App buttons.

## Run locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env            # then set DJANGO_SECRET_KEY and TELEGRAM_BOT_TOKEN
.venv/bin/python manage.py migrate
.venv/bin/python manage.py seed_catalog      # demo brands and products
.venv/bin/python manage.py createsuperuser   # for /admin
.venv/bin/python manage.py runserver 127.0.0.1:8010
```

Run the tests:

```bash
.venv/bin/python manage.py test apps
```

## Environment

See `.env.example`. The important ones:

| Variable | Purpose |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Token from @BotFather. Used to verify `initData` and send messages. |
| `TELEGRAM_ADMIN_CHAT_ID` | Chat or group that receives new order alerts. Optional. |
| `TELEGRAM_DEV_AUTH` | `true` lets the app run in a normal browser as a dev user. Only works with `DJANGO_DEBUG=true`. |
| `SHIPPING_FEE` | Flat delivery fee added to every order. |
| `POSTGRES_DB` … | Set to use PostgreSQL instead of SQLite (install `psycopg[binary]`). |

## API

All endpoints are under `/api/`. Send `Authorization: Bearer <access>` except where marked public.

| Method | Path | Description |
| --- | --- | --- |
| POST | `/auth/telegram/` | Public. `{init_data}` → `{access, refresh, user}` |
| POST | `/auth/refresh/` | `{refresh}` → new access token |
| GET, PATCH | `/auth/me/` | Current user, `phone` is editable |
| GET | `/brands/` | Public. Active brands |
| GET | `/products/` | Public. `?brand=nike&search=white&ordering=price\|-price\|-rating\|-sold_count&min_price=&max_price=&size=` |
| GET | `/products/{slug}/` | Public. Detail with sizes and stock |
| GET, POST | `/favorites/` | List wishlist, add `{product: slug}` |
| DELETE | `/favorites/{slug}/` | Remove from wishlist |
| GET, DELETE | `/cart/` | Cart with totals, or clear it |
| POST | `/cart/items/` | `{product, size?, quantity?}` add or increment |
| PUT | `/cart/items/` | `{product, size, quantity}` set exact quantity, `0` removes |
| PATCH, DELETE | `/cart/items/{id}/` | Edit or remove a line |
| GET, POST | `/orders/` | History, or checkout `{phone, address, full_name?, comment?, payment_method: cash\|card}` |
| GET | `/orders/{id}/` | Order detail |
| POST | `/orders/{id}/cancel/` | Cancel a `new` order and return stock |

Checkout answers `409` when a size ran out and `400` when the cart is empty.

## Telegram bot

The bot runs on a webhook at `/api/telegram/webhook/`, so no extra process is needed.
Telegram signs every call with `TELEGRAM_WEBHOOK_SECRET`; requests without it get `403`.

```bash
.venv/bin/python manage.py setup_bot
```

This registers the webhook, the command list (English and Uzbek) and the Mini App menu button.
Run it again after changing `WEBAPP_URL` or the bot token.

## Production notes

- Set `DJANGO_DEBUG=false`, a long `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` and `CORS_ALLOWED_ORIGINS` (your frontend origin).
- Keep `TELEGRAM_DEV_AUTH=false`.
- Run with a WSGI server, e.g. `gunicorn config.wsgi`, behind HTTPS, and run `collectstatic`.
- Serve `media/` (product photos) from the web server or object storage.
