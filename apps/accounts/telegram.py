"""Validation of Telegram Mini App `initData`.

https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""
import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl


class InitDataError(Exception):
    pass


@dataclass
class TelegramInitData:
    user: dict
    auth_date: int
    query_id: str | None
    start_param: str | None
    raw: dict


def validate_init_data(init_data: str, bot_token: str, max_age: int = 86400) -> TelegramInitData:
    if not init_data:
        raise InitDataError("initData is empty")
    if not bot_token:
        raise InitDataError("TELEGRAM_BOT_TOKEN is not configured")

    pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=False))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise InitDataError("hash is missing")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received_hash):
        raise InitDataError("invalid signature")

    try:
        auth_date = int(pairs.get("auth_date", "0"))
    except ValueError as exc:
        raise InitDataError("invalid auth_date") from exc
    if max_age and time.time() - auth_date > max_age:
        raise InitDataError("initData is expired")

    try:
        user = json.loads(pairs.get("user", "{}"))
    except json.JSONDecodeError as exc:
        raise InitDataError("invalid user payload") from exc
    if not user.get("id"):
        raise InitDataError("user is missing")

    return TelegramInitData(
        user=user,
        auth_date=auth_date,
        query_id=pairs.get("query_id"),
        start_param=pairs.get("start_param"),
        raw=pairs,
    )


def sign_init_data(fields: dict, bot_token: str) -> str:
    """Builds a signed initData string. Used in tests and local tooling."""
    from urllib.parse import urlencode

    data = {k: (json.dumps(v, separators=(",", ":")) if isinstance(v, dict) else str(v)) for k, v in fields.items()}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    data["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(data)
