from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="ElectroChain API",
        default_version="v1",
        description="API для управления сетью продаж электроники",
        contact=openapi.Contact(email="support@electrochain.ru"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("network.urls")),  # Все API с префиксом /api/
    path("swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    # Веб-страницы будут обрабатываться в network/urls.py на корневом уровне
    path("", include("network.urls")),  # Создайте отдельный файл для веб-маршрутов
]
