from datetime import date

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from ..models import NetworkNode, Product


class NetworkNodeAPITestCase(APITestCase):
    def setUp(self):
        # Создаем пользователя для аутентификации
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.force_authenticate(user=self.user)

        # Создаем тестовые данные
        self.factory = NetworkNode.objects.create(
            name="Тестовый завод",
            node_type="factory",
            email="factory@test.ru",
            country="Россия",
            city="Москва",
            street="Тестовая",
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

        self.product = Product.objects.create(name="Тестовый продукт", model="TEST-001", release_date=date(2024, 1, 1))

    def test_list_network_nodes(self):
        """Тест получения списка звеньев сети"""
        response = self.client.get("/api/network-nodes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_filter_by_country(self):
        """Тест фильтрации по стране (требование задания)"""
        response = self.client.get("/api/network-nodes/?country=Россия")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

        # Проверяем что все объекты из России
        for item in response.data["results"]:
            self.assertEqual(item["country"], "Россия")

    def test_create_network_node(self):
        """Тест создания нового звена сети"""
        data = {
            "name": "Новый поставщик",
            "node_type": "individual_entrepreneur",
            "supplier": self.retail.id,
            "email": "new@test.ru",
            "country": "Россия",
            "city": "Казань",
            "street": "Новая",
            "house_number": "25",
            "phone": "+79991234567",
        }
        response = self.client.post("/api/network-nodes/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Проверяем, что debt автоматически установлен в 0
        self.assertEqual(response.data["debt"], "0.00")

    def test_cannot_update_debt_via_api(self):
        """Тест запрета обновления поля debt через API"""
        data = {"name": "Обновленное название", "debt": 10000.00}  # Пытаемся изменить debt
        response = self.client.patch(f"/api/network-nodes/{self.retail.id}/", data, format="json")

        # Должна быть ошибка валидации
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("debt", response.data)
        self.assertIn("запрещено", response.data["debt"][0])

    def test_factory_cannot_have_supplier(self):
        """Тест что завод не может иметь поставщика"""
        data = {
            "name": "Новый завод",
            "node_type": "factory",
            "supplier": self.retail.id,  # Не должно быть разрешено
            "email": "factory2@test.ru",
            "country": "Россия",
            "city": "Москва",
        }
        response = self.client.post("/api/network-nodes/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("supplier", response.data)
