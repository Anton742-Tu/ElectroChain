from django.contrib.auth import authenticate, login, logout
from django.db.models import Avg, Count, Q, Sum
from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import ActiveEmployeeAuthentication
from .filters import NetworkNodeFilter
from .models import Employee, NetworkNode, Product, models
from .permissions import (DepartmentPermission, IsActiveEmployee,
                          IsAdminOrReadOnlyForEmployees)
from .serializers import (EmployeeSerializer, NetworkNodeCreateSerializer,
                          NetworkNodeSerializer, NetworkNodeUpdateSerializer,
                          ProductSerializer, UserRegistrationSerializer)


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet для модели Product с проверкой прав доступа"""

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    authentication_classes = [ActiveEmployeeAuthentication]
    permission_classes = [IsActiveEmployee, IsAdminOrReadOnlyForEmployees]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "model"]
    ordering_fields = ["name", "release_date"]


class NetworkNodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для модели NetworkNode с проверкой прав доступа.
    """

    queryset = NetworkNode.objects.all()
    authentication_classes = [ActiveEmployeeAuthentication]
    permission_classes = [IsActiveEmployee, DepartmentPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = NetworkNodeFilter
    search_fields = ["name", "email", "city", "country"]
    ordering_fields = ["name", "created_at", "debt", "level"]

    def get_serializer_class(self):
        if self.action == "create":
            return NetworkNodeCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return NetworkNodeUpdateSerializer
        return NetworkNodeSerializer

    def perform_create(self, serializer):
        serializer.save(debt=0)

    @action(detail=False, methods=["get"])
    def by_country(self, request):
        country = request.query_params.get("country", None)
        if country:
            queryset = self.get_queryset().filter(country__iexact=country)
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response({"error": "Параметр country обязателен"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def suppliers_summary(self, request):
        stats = NetworkNode.objects.aggregate(
            total=Count("id"),
            factories=Count("id", filter=Q(node_type="factory")),
            retail_networks=Count("id", filter=Q(node_type="retail_network")),
            entrepreneurs=Count("id", filter=Q(node_type="individual_entrepreneur")),
            total_debt=Sum("debt"),
            avg_debt=Avg("debt"),
            with_supplier=Count("id", filter=Q(supplier__isnull=False)),
            without_supplier=Count("id", filter=Q(supplier__isnull=True)),
        )

        countries = (
            NetworkNode.objects.values("country")
            .annotate(count=Count("id"), total_debt=Sum("debt"))
            .order_by("-count")
        )

        return Response(
            {
                "statistics": stats,
                "by_country": list(countries),
                "filters_available": {
                    "country": "Фильтр по стране: /api/network-nodes/?country=Россия",
                    "city": "Фильтр по городу: /api/network-nodes/?city=Москва",
                    "node_type": "Фильтр по типу: /api/network-nodes/?node_type=factory",
                    "debt": "Фильтр по задолженности: /api/network-nodes/?debt_gt=1000",
                    "has_supplier": "Фильтр по наличию поставщика: /api/network-nodes/?has_supplier=true",
                },
            }
        )

    @action(detail=True, methods=["post"])
    def clear_debt(self, request, pk=None):
        """Только активные сотрудники могут очищать задолженность"""
        # Проверяем права доступа вручную
        if not request.user or not request.user.is_authenticated:
            return Response({"error": "Требуется аутентификация"}, status=status.HTTP_401_UNAUTHORIZED)

        # Проверяем, является ли пользователь активным сотрудником
        permission = IsActiveEmployee()
        if not permission.has_permission(request, self):
            return Response({"error": permission.message}, status=status.HTTP_403_FORBIDDEN)

        node = self.get_object()
        old_debt = node.debt
        node.debt = 0
        node.save()

        return Response(
            {"message": "Задолженность очищена", "object": node.name, "old_debt": float(old_debt), "new_debt": 0}
        )

    @action(detail=False, methods=["post"])
    def bulk_clear_debt(self, request):
        """Массовая очистка задолженности только для активных сотрудников"""
        # Проверяем права доступа вручную
        if not request.user or not request.user.is_authenticated:
            return Response({"error": "Требуется аутентификация"}, status=status.HTTP_401_UNAUTHORIZED)

        # Проверяем, является ли пользователь активным сотрудником
        permission = IsActiveEmployee()
        if not permission.has_permission(request, self):
            return Response({"error": permission.message}, status=status.HTTP_403_FORBIDDEN)

        ids = request.data.get("ids", [])
        if not ids:
            return Response({"error": "Необходимо указать ids объектов"}, status=status.HTTP_400_BAD_REQUEST)

        queryset = NetworkNode.objects.filter(id__in=ids)
        count = queryset.count()
        total_debt = queryset.aggregate(total=Sum("debt"))["total"] or 0

        queryset.update(debt=0)

        return Response(
            {"message": "Задолженность очищена", "cleared_count": count, "total_debt_cleared": float(total_debt)}
        )


class EmployeeViewSet(viewsets.ModelViewSet):
    """ViewSet для управления сотрудниками (только для администраторов)"""

    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    authentication_classes = [ActiveEmployeeAuthentication]
    permission_classes = [permissions.IsAdminUser]  # Только администраторы
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["user__username", "user__email", "user__first_name", "user__last_name", "department", "position"]
    ordering_fields = ["user__last_name", "hire_date", "department"]

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """Активировать сотрудника"""
        # Проверяем, является ли пользователь администратором
        if not request.user.is_superuser:
            return Response({"error": "Требуются права администратора"}, status=status.HTTP_403_FORBIDDEN)

        employee = self.get_object()
        employee.is_active = True
        employee.save()
        return Response({"status": "Сотрудник активирован"})

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """Деактивировать сотрудника"""
        # Проверяем, является ли пользователь администратором
        if not request.user.is_superuser:
            return Response({"error": "Требуются права администратора"}, status=status.HTTP_403_FORBIDDEN)

        employee = self.get_object()
        employee.is_active = False
        employee.save()
        return Response({"status": "Сотрудник деактивирован"})


class CurrentEmployeeView(APIView):
    """Получение информации о текущем сотруднике"""

    authentication_classes = [ActiveEmployeeAuthentication]

    def get(self, request):
        # Проверяем права доступа
        permission = IsActiveEmployee()
        if not permission.has_permission(request, self):
            return Response({"error": permission.message}, status=status.HTTP_403_FORBIDDEN)

        try:
            employee = request.user.employee_profile
            serializer = EmployeeSerializer(employee)
            return Response(serializer.data)
        except Employee.DoesNotExist:
            return Response({"error": "Профиль сотрудника не найден"}, status=status.HTTP_404_NOT_FOUND)


class RegisterEmployeeView(generics.CreateAPIView):
    """Регистрация нового сотрудника (только для администраторов)"""

    serializer_class = UserRegistrationSerializer
    authentication_classes = [ActiveEmployeeAuthentication]

    def check_permissions(self, request):
        # Проверяем, является ли пользователь администратором
        if not request.user.is_superuser:
            self.permission_denied(request, message="Требуются права администратора")
        return super().check_permissions(request)


class LoginView(APIView):
    """Вход в систему для сотрудников"""

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Проверяем, есть ли у пользователя профиль сотрудника
            try:
                employee = user.employee_profile
                if not employee.is_active:
                    return Response(
                        {"error": "Ваш аккаунт сотрудника деактивирован"}, status=status.HTTP_403_FORBIDDEN
                    )

                # Выполняем вход
                login(request, user)

                # Обновляем дату последнего входа
                employee.update_last_login()

                return Response(
                    {
                        "message": "Вход выполнен успешно",
                        "user": {
                            "id": user.id,
                            "username": user.username,
                            "email": user.email,
                            "full_name": user.get_full_name(),
                            "department": employee.department,
                            "position": employee.position,
                        },
                    }
                )

            except Employee.DoesNotExist:
                # Проверяем, является ли пользователь суперпользователем
                if user.is_superuser:
                    login(request, user)
                    return Response(
                        {
                            "message": "Вход выполнен как суперпользователь",
                            "user": {
                                "id": user.id,
                                "username": user.username,
                                "email": user.email,
                                "full_name": user.get_full_name(),
                            },
                        }
                    )

                return Response({"error": "Профиль сотрудника не найден"}, status=status.HTTP_403_FORBIDDEN)

        return Response({"error": "Неверные учетные данные"}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    """Выход из системы"""

    authentication_classes = [ActiveEmployeeAuthentication]

    def post(self, request):
        # Проверяем права доступа
        permission = IsActiveEmployee()
        if not permission.has_permission(request, self):
            return Response({"error": permission.message}, status=status.HTTP_403_FORBIDDEN)

        logout(request)
        return Response({"message": "Выход выполнен успешно"})


def home(request):
    """Главная страница"""
    stats = {
        "factories": NetworkNode.objects.filter(node_type="factory").count(),
        "retail": NetworkNode.objects.filter(node_type="retail_network").count(),
        "entrepreneurs": NetworkNode.objects.filter(node_type="individual_entrepreneur").count(),
        "products": Product.objects.count(),
        "total_debt": NetworkNode.objects.aggregate(total=models.Sum("debt"))["total"] or 0,
    }

    return render(request, "network/home.html", {"stats": stats})


def network_list(request):
    """Список звеньев сети"""
    nodes = NetworkNode.objects.select_related("supplier").prefetch_related("products").all()

    # Фильтрация по стране
    country = request.GET.get("country")
    if country:
        nodes = nodes.filter(country__icontains=country)

    return render(request, "network/network_list.html", {"nodes": nodes, "current_country": country})


def product_list(request):
    """Список продуктов"""
    products = Product.objects.all()
    return render(request, "network/product_list.html", {"products": products})


def about(request):
    """О проекте"""
    return render(request, "network/about.html")
