from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views
from .views import (CurrentEmployeeView, EmployeeViewSet, LoginView,
                    LogoutView, NetworkNodeViewSet, ProductViewSet,
                    RegisterEmployeeView)

router = DefaultRouter()
router.register(r"network-nodes", NetworkNodeViewSet, basename="networknode")
router.register(r"products", ProductViewSet, basename="product")
router.register(r"employees", EmployeeViewSet, basename="employee")

urlpatterns = [
    # API маршруты (с префиксом /api/ из корневого urls.py)
    path("", include(router.urls)),
    # Аутентификация
    path("auth/login/", LoginView.as_view(), name="login"),  # /api/auth/login/
    path("auth/logout/", LogoutView.as_view(), name="logout"),  # /api/auth/logout/
    path("auth/profile/", views.profile, name="profile"),  # /api/auth/profile/
    path("auth/me/", CurrentEmployeeView.as_view(), name="current-employee"),  # /api/auth/me/
    path("auth/register/", RegisterEmployeeView.as_view(), name="register-employee"),  # /api/auth/register/
    # DRF browsable API - добавляем уникальный namespace
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    # Веб-страницы
    path("", views.home, name="home"),
    path("network/", views.network_list, name="network_list"),
    path("products/", views.product_list, name="product_list"),
    path("about/", views.about, name="about"),
]
