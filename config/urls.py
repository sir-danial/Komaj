from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from apps.catalog.sitemaps import SITEMAPS

urlpatterns = [
    path("admin/", admin.site.urls),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path("", include("apps.catalog.urls")),
    path("", include("apps.cart.urls")),
    path("", include("apps.orders.urls")),
    path("", include("apps.payments.urls")),
    path("", include("apps.coupons.urls")),
    path("", include("apps.accounts.urls")),
    path("", include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif not settings.USE_S3_STORAGE:
    # no S3 yet: gunicorn serves the handful of admin-uploaded product images
    # straight from the persistent volume (fine at this traffic level)
    from django.urls import re_path
    from django.views.static import serve

    def _serve_media(request, path):
        return serve(request, path, document_root=settings.MEDIA_ROOT)

    urlpatterns += [re_path(r"^media/(?P<path>.*)$", _serve_media)]
