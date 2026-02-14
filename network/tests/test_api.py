from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from network.models import Employee, NetworkNode, Product


class ProductAPITest(APITestCase):
    """Тесты для Product API"""

    def setUp(self):
        # Создаем активного сотрудника с правильными permissions
        self.user = User.objects.create_user(username="testuser", password="testpass123", is_staff=True)
        self.employee = Employee.objects.create(
            user=self.user, department="Тестирование", position="Тестировщик", is_active=True
        )
        # Аутентифицируем клиент
        self.client.force_authenticate(user=self.user)

        # Создаем тестовый продукт
        self.product = Product.objects.create(name="Тестовый продукт", model="TEST-001", release_date="2024-01-01")

    def test_get_products(self):
        """Получение списка продуктов"""
        url = reverse("product-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_product(self):
        """Создание продукта"""
        url = reverse("product-list")
        data = {"name": "Новый продукт", "model": "NEW-001", "release_date": "2024-01-01"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_product(self):
        """Обновление продукта"""
        url = reverse("product-detail", args=[self.product.id])
        data = {"name": "Обновленный продукт", "model": "UPDATED-001", "release_date": "2024-01-01"}
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_product(self):
        """Удаление продукта"""
        url = reverse("product-detail", args=[self.product.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class NetworkNodeAPITest(APITestCase):
    """Тесты для NetworkNode API"""

    def setUp(self):
        # Создаем активного сотрудника
        self.user = User.objects.create_user(username="testuser", password="testpass123", is_staff=True)
        self.employee = Employee.objects.create(
            user=self.user, department="Тестирование", position="Тестировщик", is_active=True
        )
        self.client.force_authenticate(user=self.user)

        # Создаем тестовые данные
        self.factory = NetworkNode.objects.create(
            name="Тестовый завод",
            node_type="factory",
            email="factory@test.ru",
            country="Россия",
            city="Москва",
            street="Заводская",
            house_number="1",
        )

        self.retail = NetworkNode.objects.create(
            name="Тестовая розница",
            node_type="retail_network",
            supplier=self.factory,
            email="retail@test.ru",
            country="Россия",
            city="Москва",
            street="Торговая",
            house_number="100",
            debt=50000.00,
        )

    def test_get_nodes(self):
        """Получение списка звеньев"""
        url = reverse("networknode-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_filter_by_country(self):
        """Фильтрация по стране"""
        url = reverse("networknode-list")
        response = self.client.get(url, {"country": "Россия"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_node(self):
        """Создание звена"""
        url = reverse("networknode-list")
        data = {
            "name": "Новый поставщик",
            "node_type": "individual_entrepreneur",
            "supplier": self.retail.id,
            "email": "new@test.ru",
            "country": "Россия",
            "city": "Казань",
            "street": "Новая",
            "house_number": "25",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class AuthenticationTest(APITestCase):
    """Тесты аутентификации"""

    def setUp(self):
        # Создаем суперпользователя (у него всегда есть доступ)
        self.admin = User.objects.create_superuser(username="admin", password="admin123", email="admin@test.ru")

        # Создаем активного сотрудника
        self.active_user = User.objects.create_user(username="active", password="active123", is_staff=True)
        self.active_employee = Employee.objects.create(
            user=self.active_user, department="Тестирование", position="Тестировщик", is_active=True
        )

        # Создаем неактивного сотрудника
        self.inactive_user = User.objects.create_user(username="inactive", password="inactive123", is_staff=True)
        self.inactive_employee = Employee.objects.create(
            user=self.inactive_user, department="Тестирование", position="Тестировщик", is_active=False
        )

    def test_login_success_active_employee(self):
        """Успешный вход активного сотрудника"""
        url = reverse("login")
        data = {"username": "active", "password": "active123"}
        response = self.client.post(url, data, format="json")

        # Проверяем статус ответа
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Проверяем что получили данные пользователя
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["username"], "active")

    def test_login_success_admin(self):
        """Успешный вход администратора"""
        url = reverse("login")
        data = {"username": "admin", "password": "admin123"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["username"], "admin")

    def test_login_inactive_employee(self):
        """Вход неактивного сотрудника - должен быть запрещен"""
        url = reverse("login")
        data = {"username": "inactive", "password": "inactive123"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error", response.data)

    def test_login_wrong_password(self):
        """Неверный пароль"""
        url = reverse("login")
        data = {"username": "active", "password": "wrongpassword"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("error", response.data)

    def test_login_nonexistent_user(self):
        """Несуществующий пользователь"""
        url = reverse("login")
        data = {"username": "nonexistent", "password": "password123"}
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_credentials(self):
        """Отсутствуют учетные данные"""
        url = reverse("login")
        response = self.client.post(url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authenticated_user_can_access_api(self):
        """Аутентифицированный пользователь имеет доступ к API"""
        # Сначала логинимся
        login_url = reverse("login")
        login_data = {"username": "active", "password": "active123"}
        login_response = self.client.post(login_url, login_data, format="json")
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # Получаем сессию из cookies
        session_cookie = self.client.cookies.get("sessionid")
        self.assertIsNotNone(session_cookie)

        # Пробуем получить доступ к API
        api_url = reverse("product-list")
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_user_cannot_access_api(self):
        """Неаутентифицированный пользователь не имеет доступа к API"""
        # Очищаем аутентификацию
        self.client.logout()

        api_url = reverse("product-list")
        response = self.client.get(api_url)

        # Должен быть 401 Unauthorized или 403 Forbidden
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class EmployeeModelTest(TestCase):
    """Тесты модели Employee"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        self.employee = Employee.objects.create(user=self.user, department="IT", position="Developer", is_active=True)

    def test_employee_creation(self):
        """Создание сотрудника"""
        self.assertEqual(self.employee.user.username, "testuser")
        self.assertEqual(self.employee.department, "IT")
        self.assertEqual(self.employee.position, "Developer")
        self.assertTrue(self.employee.is_active)

    def test_employee_str_method(self):
        """Строковое представление сотрудника"""
        self.user.first_name = "Иван"
        self.user.last_name = "Петров"
        self.user.save()
        expected = f"Иван Петров ({self.employee.position})"
        self.assertEqual(str(self.employee), expected)

    def test_employee_full_name_property(self):
        """Свойство full_name"""
        self.user.first_name = "Иван"
        self.user.last_name = "Петров"
        self.user.save()
        self.assertEqual(self.employee.full_name, "Иван Петров")

    def test_employee_email_property(self):
        """Свойство email"""
        self.user.email = "test@example.com"
        self.user.save()
        self.assertEqual(self.employee.email, "test@example.com")

    def test_update_last_login(self):
        """Обновление даты последнего входа"""

        self.assertIsNone(self.employee.last_login_date)
        self.employee.update_last_login()
        self.assertIsNotNone(self.employee.last_login_date)
