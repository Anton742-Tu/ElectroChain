from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (CurrentEmployeeView, EmployeeViewSet, LoginView,
                    LogoutView, NetworkNodeViewSet, ProductViewSet,
                    RegisterEmployeeView)

router = DefaultRouter()
router.register(r"network-nodes", NetworkNodeViewSet, basename="networknode")
router.register(r"products", ProductViewSet, basename="product")
router.register(r"employees", EmployeeViewSet, basename="employee")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", CurrentEmployeeView.as_view(), name="current-employee"),
    path("auth/register/", RegisterEmployeeView.as_view(), name="register-employee"),
    path("api-auth/", include("rest_framework.urls")),  # Для browsable API
]
