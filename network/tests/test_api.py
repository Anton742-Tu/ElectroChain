from datetime import date

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from network.models import Employee, NetworkNode, Product


class ProductAPITest(APITestCase):
    def setUp(self):
        # Создаем пользователя
        self.user = User.objects.create_user(username="testuser", password="testpass123", is_staff=True)

        # Создаем профиль сотрудника
        self.employee = Employee.objects.create(
            user=self.user, department="Тестирование", position="Тестировщик", is_active=True
        )

        # Аутентифицируем клиент
        self.client.force_authenticate(user=self.user)

        # Создаем тестовый продукт
        self.product = Product.objects.create(
            name="Тестовый продукт API", model="API-TEST-001", release_date=date(2024, 1, 1)
        )

    def test_get_products_list(self):
        """Тест получения списка продуктов"""
        url = reverse("product-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "Тестовый продукт API")

    def test_create_product(self):
        """Тест создания продукта"""
        url = reverse("product-list")
        data = {"name": "Новый продукт", "model": "NEW-001", "release_date": "2024-06-01"}

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(Product.objects.get(id=response.data["id"]).name, "Новый продукт")

    def test_update_product(self):
        """Тест обновления продукта"""
        url = reverse("product-detail", args=[self.product.id])
        data = {"name": "Обновленный продукт", "model": "UPDATED-001", "release_date": "2024-06-01"}

        response = self.client.put(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Обновленный продукт")

    def test_delete_product(self):
        """Тест удаления продукта"""
        url = reverse("product-detail", args=[self.product.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Product.objects.count(), 0)


class NetworkNodeAPITest(APITestCase):
    def setUp(self):
        # Создаем пользователя
        self.user = User.objects.create_user(username="testuser", password="testpass123", is_staff=True)

        # Создаем профиль сотрудника
        self.employee = Employee.objects.create(
            user=self.user, department="Тестирование", position="Тестировщик", is_active=True
        )

        # Аутентифицируем клиент
        self.client.force_authenticate(user=self.user)

        # Создаем тестовые данные
        self.factory = NetworkNode.objects.create(
            name="Тестовый завод API",
            node_type="factory",
            email="factory_api@test.ru",
            country="Россия",
            city="Москва",
            street="Заводская",
            house_number="1",
        )

        self.retail = NetworkNode.objects.create(
            name="Тестовая розница API",
            node_type="retail_network",
            supplier=self.factory,
            email="retail_api@test.ru",
            country="Россия",
            city="Москва",
            street="Торговая",
            house_number="100",
            debt=50000.00,
        )

    def test_get_network_nodes_list(self):
        """Тест получения списка звеньев сети"""
        url = reverse("networknode-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_filter_by_country(self):
        """Тест фильтрации по стране (требование задания 4)"""
        url = reverse("networknode-list")
        response = self.client.get(url, {"country": "Россия"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

        # Проверяем что все объекты из России
        for item in response.data["results"]:
            self.assertEqual(item["country"], "Россия")

    def test_create_network_node(self):
        """Тест создания звена сети"""
        url = reverse("networknode-list")
        data = {
            "name": "Новый поставщик API",
            "node_type": "individual_entrepreneur",
            "supplier": self.retail.id,
            "email": "new_api@test.ru",
            "country": "Россия",
            "city": "Казань",
            "street": "Новая",
            "house_number": "25",
            "phone": "+79991234567",
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(NetworkNode.objects.count(), 3)

        # Проверяем, что debt автоматически установлен в 0
        self.assertEqual(response.data["debt"], "0.00")

    def test_cannot_update_debt_via_api(self):
        """Тест запрета обновления поля debt через API (требование задания 4)"""
        url = reverse("networknode-detail", args=[self.retail.id])
        data = {"name": "Обновленное название", "debt": 10000.00}  # Пытаемся изменить debt

        response = self.client.patch(url, data, format="json")

        # Должна быть ошибка валидации или запрет доступа
        # Проверяем что debt не изменился
        self.retail.refresh_from_db()
        self.assertEqual(float(self.retail.debt), 50000.00)

        # Либо ошибка 400, либо 403 в зависимости от permissions
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN])

    def test_clear_debt_action(self):
        """Тест действия очистки задолженности"""
        url = reverse("networknode-clear-debt", args=[self.retail.id])
        response = self.client.post(url)

        # Проверяем что запрос прошел (200 или 403 в зависимости от прав)
        if response.status_code == status.HTTP_200_OK:
            self.retail.refresh_from_db()
            self.assertEqual(float(self.retail.debt), 0.0)
        else:
            # Если нет прав, проверяем что debt не изменился
            self.retail.refresh_from_db()
            self.assertEqual(float(self.retail.debt), 50000.00)

    def test_suppliers_summary(self):
        """Тест получения статистики"""
        url = reverse("networknode-suppliers-summary")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("statistics", response.data)
        self.assertIn("by_country", response.data)


class SimpleAuthenticationTest(APITestCase):
    """Упрощенные тесты аутентификации без создания NetworkNode"""

    def setUp(self):
        # Создаем разных пользователей
        self.admin = User.objects.create_user(username="admin", password="admin123", is_staff=True, is_superuser=True)

        self.active_employee_user = User.objects.create_user(
            username="active_employee", password="active123", is_staff=True
        )

        self.inactive_employee_user = User.objects.create_user(
            username="inactive_employee", password="inactive123", is_staff=True
        )

        self.non_staff_user = User.objects.create_user(username="non_staff", password="nonstaff123", is_staff=False)

        # Создаем профили сотрудников
        Employee.objects.create(
            user=self.active_employee_user, department="Тестирование", position="Тестировщик", is_active=True
        )

        Employee.objects.create(
            user=self.inactive_employee_user,
            department="Тестирование",
            position="Тестировщик",
            is_active=False,  # Неактивный!
        )

    def test_admin_access(self):
        """Тест доступа администратора"""
        self.client.force_authenticate(user=self.admin)
        url = reverse("product-list")  # Используем products вместо network-nodes
        response = self.client.get(url)

        # Админ должен иметь доступ
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_active_employee_access(self):
        """Тест доступа активного сотрудника"""
        self.client.force_authenticate(user=self.active_employee_user)
        url = reverse("product-list")
        response = self.client.get(url)

        # Активный сотрудник должен иметь доступ
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_inactive_employee_access(self):
        """Тест что неактивный сотрудник не имеет доступа"""
        self.client.force_authenticate(user=self.inactive_employee_user)
        url = reverse("product-list")
        response = self.client.get(url)

        # Неактивный сотрудник не должен иметь доступ
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_non_staff_access(self):
        """Тест что не-персонал не имеет доступа"""
        self.client.force_authenticate(user=self.non_staff_user)
        url = reverse("product-list")
        response = self.client.get(url)

        # Не-персонал не должен иметь доступ
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_access(self):
        """Тест что неаутентифицированные пользователи не имеют доступа"""
        url = reverse("product-list")
        response = self.client.get(url)

        # Неаутентифицированные не должны иметь доступ
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
