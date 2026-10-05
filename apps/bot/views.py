import hmac
import json
import logging

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .handlers import handle_update

log = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def webhook(request):
    secret = settings.TELEGRAM_WEBHOOK_SECRET
    given = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not secret or not hmac.compare_digest(given, secret):
        return HttpResponseForbidden()
    try:
        update = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return HttpResponse(status=400)
    try:
        handle_update(update)
    except Exception:  # Always answer 200 so Telegram does not retry the same update forever.
        log.exception("Failed to handle update %s", update.get("update_id"))
    return HttpResponse("ok")
