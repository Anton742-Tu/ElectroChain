from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from network.models import NetworkNode, Product


class ProductModelTest(TestCase):
    def setUp(self):
        # Создаем продукт с датой выпуска - 30 дней назад (новый продукт)
        self.product = Product.objects.create(
            name="Тестовый продукт", model="TEST-001", release_date=timezone.now().date() - timedelta(days=30)
        )

    def test_product_creation(self):
        """Тест создания продукта"""
        self.assertEqual(self.product.name, "Тестовый продукт")
        self.assertEqual(self.product.model, "TEST-001")
        self.assertIn(str(self.product.release_date.year), str(self.product))

    def test_is_new_property_true(self):
        """Тест свойства is_new для нового продукта"""
        # Создаем новый продукт (менее 6 месяцев)
        new_product = Product.objects.create(
            name="Новый продукт", model="NEW-001", release_date=timezone.now().date() - timedelta(days=30)
        )
        self.assertTrue(new_product.is_new)

    def test_is_new_property_false(self):
        """Тест свойства is_new для старого продукта"""
        # Создаем старый продукт (более 6 месяцев)
        old_product = Product.objects.create(
            name="Старый продукт", model="OLD-001", release_date=timezone.now().date() - timedelta(days=200)
        )
        self.assertFalse(old_product.is_new)


class NetworkNodeModelTest(TestCase):
    def setUp(self):
        # Создаем продукты с актуальными датами
        self.product1 = Product.objects.create(
            name="Продукт 1", model="P1", release_date=timezone.now().date() - timedelta(days=30)
        )

        self.product2 = Product.objects.create(
            name="Продукт 2", model="P2", release_date=timezone.now().date() - timedelta(days=45)
        )

        # Создаем завод с обязательными полями
        self.factory = NetworkNode.objects.create(
            name="Тестовый завод",
            node_type="factory",
            email="factory@test.ru",
            country="Россия",
            city="Москва",
            street="Заводская",
            house_number="1",
        )
        self.factory.products.set([self.product1, self.product2])

        # Создаем розничную сеть
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
        self.retail.products.set([self.product1])

    def test_network_node_creation(self):
        """Тест создания звена сети"""
        self.assertEqual(self.factory.name, "Тестовый завод")
        self.assertEqual(self.factory.node_type, "factory")
        self.assertEqual(self.factory.level, 0)
        self.assertEqual(self.retail.level, 1)

    def test_level_property(self):
        """Тест вычисления уровня иерархии"""
        # Создаем еще один уровень
        entrepreneur = NetworkNode.objects.create(
            name="ИП Тест",
            node_type="individual_entrepreneur",
            supplier=self.retail,
            email="ip@test.ru",
            country="Россия",
            city="Казань",
            street="Торговая",
            house_number="10",
        )

        self.assertEqual(self.factory.level, 0)  # Завод
        self.assertEqual(self.retail.level, 1)  # Розничная сеть
        self.assertEqual(entrepreneur.level, 2)  # ИП

    def test_factory_cannot_have_supplier(self):
        """Тест что завод не может иметь поставщика"""
        factory2 = NetworkNode(
            name="Завод 2",
            node_type="factory",
            supplier=self.factory,
            email="factory2@test.ru",
            country="Россия",
            city="Москва",
            street="Заводская",
            house_number="2",
        )

        with self.assertRaises(ValidationError):
            factory2.full_clean()  # Должна быть ошибка валидации

    def test_full_address_property(self):
        """Тест свойства полного адреса"""
        expected_address = "Россия, г. Москва, ул. Заводская, д. 1"
        self.assertEqual(self.factory.full_address, expected_address)

    def test_contact_info_property(self):
        """Тест свойства контактной информации"""
        self.factory.phone = "+79991234567"
        self.factory.save()

        contact_info = self.factory.contact_info
        self.assertIn("factory@test.ru", contact_info)
        self.assertIn("+79991234567", contact_info)
        self.assertIn(self.factory.full_address, contact_info)

    def test_negative_debt_validation(self):
        """Тест что задолженность не может быть отрицательной"""
        node = NetworkNode(
            name="Тест отрицательный долг",
            node_type="retail_network",
            email="test@test.ru",
            country="Россия",
            city="Москва",
            street="Тестовая",
            house_number="1",
            debt=-100.00,  # Отрицательный долг
        )

        with self.assertRaises(ValidationError):
            node.full_clean()
