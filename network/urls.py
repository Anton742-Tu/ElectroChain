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
    # API маршруты
    path("api/", include(router.urls)),
    path("api/auth/login/", LoginView.as_view(), name="login"),
    path("api/auth/logout/", LogoutView.as_view(), name="logout"),
    path("api/auth/profile/", views.profile, name="profile"),
    path("api/auth/me/", CurrentEmployeeView.as_view(), name="current-employee"),
    path("api/auth/register/", RegisterEmployeeView.as_view(), name="register-employee"),
    path("api/api-auth/", include("rest_framework.urls")),
    # Веб-страницы
    path("", views.home, name="home"),
    path("network/", views.network_list, name="network_list"),
    path("products/", views.product_list, name="product_list"),
    path("about/", views.about, name="about"),
]

# Корневой API (если нужно) - можно добавить отдельно
# path("api-root/", include(router.urls)),  # или оставить только с префиксом
