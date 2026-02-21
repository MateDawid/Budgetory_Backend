import re

from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions, routers

from app_infrastructure.views.healthcheck_view import HealthcheckView
from predictions.views.prediction_progress_status_view import PredictionProgressStatusView
from wallets.views.currency_viewset import CurrencyViewSet

schema_view = get_schema_view(
    openapi.Info(
        title="Budgetory API",
        default_version="v1",
        description="API for Budgetory application.",
        contact=openapi.Contact(email="mateusiakdawid@gmail.com"),
        # license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

router = routers.SimpleRouter()

urlpatterns = [
    path("api/swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path("api/swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("api/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("api/healthcheck", HealthcheckView.as_view(), name="healthcheck"),
    path("api/admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/users/", include("app_users.urls")),
    path("api/wallets/", include("wallets.urls")),
    path("api/wallets/<int:wallet_pk>/", include("predictions.urls")),
    path("api/categories/", include("categories.urls")),
    path("api/", include("charts.urls")),
    path(
        "api/predictions/progress_statuses/", PredictionProgressStatusView.as_view(), name="prediction-progress-status"
    ),
    path("api/currencies/", CurrencyViewSet.as_view({"get": "list"}), name="currency"),
    re_path(
        r"^%s(?P<path>.*)$" % re.escape(settings.STATIC_URL.lstrip("/")), serve, {"document_root": settings.STATIC_ROOT}
    ),
]

if settings.DEBUG_TOOLBAR_ENABLED:
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
