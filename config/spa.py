"""Serves the built React app (Vite `dist/`) so API and frontend share one HTTPS domain."""
import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse
from django.views.decorators.cache import never_cache


def _dist() -> Path:
    if not settings.FRONTEND_DIST:
        raise Http404("FRONTEND_DIST is not configured")
    return Path(settings.FRONTEND_DIST).resolve()


@never_cache
def spa(request, path: str = ""):
    dist = _dist()
    candidate = (dist / path).resolve()
    # Real files (favicon, assets) are returned as-is; everything else gets index.html for client routing.
    if path and candidate.is_file() and dist in candidate.parents:
        content_type, _ = mimetypes.guess_type(candidate.name)
        return FileResponse(open(candidate, "rb"), content_type=content_type)
    index = dist / "index.html"
    if not index.is_file():
        return HttpResponse("Frontend build not found. Check FRONTEND_DIST.", status=503, content_type="text/plain")
    return HttpResponse(index.read_bytes(), content_type="text/html; charset=utf-8")
