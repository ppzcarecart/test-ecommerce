from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from catalog.sitemaps import (
    CategorySitemap,
    ProductSitemap,
    StaticSitemap,
)
from core.views import robots_txt, service_worker

sitemaps = {
    "static": StaticSitemap,
    "categories": CategorySitemap,
    "products": ProductSitemap,
}


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("shop/", include("catalog.urls")),
    path("cart/", include("cart.urls")),
    path("checkout/", include("payments.urls")),
    path("account/", include("accounts.urls")),
    path("accounts/", include("allauth.urls")),
    # SEO — sitemap.xml + robots.txt
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", robots_txt, name="robots"),
    # PWA service worker must be served from origin root
    path("sw.js", service_worker, name="service-worker"),
    path(
        "manifest.webmanifest",
        TemplateView.as_view(
            template_name="pwa/manifest.webmanifest",
            content_type="application/manifest+json",
        ),
        name="web-manifest",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
