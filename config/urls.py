from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from .spa import spa

admin.site.site_header = "Shoer.lk admin"
admin.site.site_title = "Shoer.lk"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.catalog.urls")),
    path("api/", include("apps.shop.urls")),
    path("api/telegram/", include("apps.bot.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.FRONTEND_DIST:
    # Must stay last: catches every non-API route for the React router.
    urlpatterns += [re_path(r"^(?!api/|admin/|static/|media/)(?P<path>.*)$", spa, name="spa")]
