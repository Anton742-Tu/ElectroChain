from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIRequestFactory

from network.models import Employee
from network.permissions import DepartmentPermission, IsActiveEmployee
from network.views import NetworkNodeViewSet


class PermissionsTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = NetworkNodeViewSet()

        # Создаем разных пользователей
        self.superuser = User.objects.create_user(
            username="superuser", password="super123", is_superuser=True, is_staff=True
        )

        self.admin_user = User.objects.create_user(username="admin_user", password="admin123", is_staff=True)

        self.sales_user = User.objects.create_user(username="sales_user", password="sales123", is_staff=True)

        self.analyst_user = User.objects.create_user(username="analyst_user", password="analyst123", is_staff=True)

        self.inactive_user = User.objects.create_user(username="inactive_user", password="inactive123", is_staff=True)

        # Создаем профили сотрудников
        Employee.objects.create(
            user=self.admin_user, department="Администрация", position="Администратор", is_active=True
        )

        Employee.objects.create(user=self.sales_user, department="Продажи", position="Менеджер", is_active=True)

        Employee.objects.create(user=self.analyst_user, department="Аналитика", position="Аналитик", is_active=True)

        Employee.objects.create(
            user=self.inactive_user, department="Техподдержка", position="Специалист", is_active=False  # Неактивный!
        )

    def test_is_active_employee_permission(self):
        """Тест разрешения IsActiveEmployee"""
        permission = IsActiveEmployee()

        # Суперпользователь должен иметь доступ
        request = self.factory.get("/")
        request.user = self.superuser
        self.assertTrue(permission.has_permission(request, self.view))

        # Активный сотрудник должен иметь доступ
        request.user = self.admin_user
        self.assertTrue(permission.has_permission(request, self.view))

        # Неактивный сотрудник не должен иметь доступ
        request.user = self.inactive_user
        self.assertFalse(permission.has_permission(request, self.view))

        # Не-персонал не должен иметь доступ
        non_staff = User.objects.create_user(username="nonstaff", password="test")
        request.user = non_staff
        self.assertFalse(permission.has_permission(request, self.view))

        # Неаутентифицированный пользователь не должен иметь доступ
        request.user = None
        self.assertFalse(permission.has_permission(request, self.view))

    def test_department_permission_safe_methods(self):
        """Тест разрешений отделов для безопасных методов"""
        permission = DepartmentPermission()

        # GET запрос должен быть разрешен для всех активных сотрудников
        for user in [self.admin_user, self.sales_user, self.analyst_user]:
            request = self.factory.get("/")
            request.user = user
            self.assertTrue(permission.has_permission(request, self.view))

    def test_department_permission_admin_department(self):
        """Тест что администрация имеет полный доступ"""
        permission = DepartmentPermission()

        # Администрация должна иметь доступ к POST
        request = self.factory.post("/")
        request.user = self.admin_user
        self.assertTrue(permission.has_permission(request, self.view))

        # Администрация должна иметь доступ к DELETE
        request = self.factory.delete("/")
        request.user = self.admin_user
        self.assertTrue(permission.has_permission(request, self.view))

    def test_department_permission_sales_department(self):
        """Тест что отдел продаж имеет доступ кроме DELETE"""
        permission = DepartmentPermission()

        # Продажи должны иметь доступ к POST
        request = self.factory.post("/")
        request.user = self.sales_user
        self.assertTrue(permission.has_permission(request, self.view))

        # Продажи НЕ должны иметь доступ к DELETE
        request = self.factory.delete("/")
        request.user = self.sales_user
        self.assertFalse(permission.has_permission(request, self.view))

    def test_department_permission_analytics_department(self):
        """Тест что аналитика имеет только безопасные методы"""
        permission = DepartmentPermission()

        # Аналитика должна иметь доступ к GET
        request = self.factory.get("/")
        request.user = self.analyst_user
        self.assertTrue(permission.has_permission(request, self.view))

        # Аналитика НЕ должна иметь доступ к POST
        request = self.factory.post("/")
        request.user = self.analyst_user
        self.assertFalse(permission.has_permission(request, self.view))

        # Аналитика НЕ должна иметь доступ к DELETE
        request = self.factory.delete("/")
        request.user = self.analyst_user
        self.assertFalse(permission.has_permission(request, self.view))
