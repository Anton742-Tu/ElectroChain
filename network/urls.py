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
    # API маршруты (с префиксом api/)
    path("api/", include(router.urls)),
    path("api/auth/login/", LoginView.as_view(), name="login"),
    path("api/auth/logout/", LogoutView.as_view(), name="logout"),
    path("api/auth/profile/", views.profile, name="profile"),
    path("api/auth/me/", CurrentEmployeeView.as_view(), name="current-employee"),
    path("api/auth/register/", RegisterEmployeeView.as_view(), name="register-employee"),
    path("api/api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    # Веб-страницы (без префикса)
    path("", views.home, name="home"),  # Главная страница
    path("network/", views.network_list, name="network_list"),
    path("products/", views.product_list, name="product_list"),
    path("about/", views.about, name="about"),
    path("login/", views.login_view, name="login_page"),
    path("logout/", views.logout_view, name="logout_page"),
]
