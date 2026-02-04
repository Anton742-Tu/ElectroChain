from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    """Модель продукта/товара"""

    name = models.CharField(max_length=255, verbose_name="Название продукта")
    model = models.CharField(max_length=255, verbose_name="Модель", blank=True)
    release_date = models.DateField(verbose_name="Дата выхода на рынок")

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.model})" if self.model else self.name


class NetworkNode(models.Model):
    """Модель звена сети (иерархическая структура)"""

    class NodeType(models.TextChoices):
        FACTORY = "factory", "Завод"
        RETAIL_NETWORK = "retail_network", "Розничная сеть"
        INDIVIDUAL_ENTREPRENEUR = "individual_entrepreneur", "Индивидуальный предприниматель"

    # Основная информация
    name = models.CharField(max_length=255, verbose_name="Название звена")
    node_type = models.CharField(max_length=30, choices=NodeType.choices, verbose_name="Тип звена")

    # Иерархические связи
    supplier = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Поставщик",
        help_text="Вышестоящее звено в цепочке поставок",
    )

    # Контактная информация
    email = models.EmailField(unique=True, verbose_name="Электронная почта")
    phone = models.CharField(max_length=20, verbose_name="Телефон", blank=True)

    # Адрес
    country = models.CharField(max_length=100, verbose_name="Страна")
    city = models.CharField(max_length=100, verbose_name="Город")
    street = models.CharField(max_length=100, verbose_name="Улица")
    house_number = models.CharField(max_length=20, verbose_name="Номер дома")
    postal_code = models.CharField(max_length=20, verbose_name="Почтовый индекс", blank=True)

    # Продукция
    products = models.ManyToManyField(Product, related_name="network_nodes", verbose_name="Продукты", blank=True)

    # Финансовые показатели
    debt = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name="Задолженность перед поставщиком",
        help_text="Задолженность в рублях",
    )

    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Время последнего обновления")

    class Meta:
        verbose_name = "Звено сети"
        verbose_name_plural = "Звенья сети"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["node_type"]),
            models.Index(fields=["city"]),
            models.Index(fields=["country"]),
        ]

    def __str__(self):
        supplier_info = f" ← {self.supplier.name}" if self.supplier else ""
        return f"{self.get_node_type_display()}: {self.name}{supplier_info}"

    @property
    def level(self):
        """
        Динамически вычисляет уровень иерархии.
        0 - Завод (у него нет поставщика)
        1 - Прямой поставщик от завода
        2 - Второй уровень и т.д.
        """
        if not hasattr(self, "_level_cache"):
            if self.supplier is None:
                self._level_cache = 0
            else:
                self._level_cache = self.supplier.level + 1
        return self._level_cache

    @property
    def full_address(self):
        """Полный адрес в формате строки"""
        address_parts = [f"{self.country}, {self.city}", f"ул. {self.street}, д. {self.house_number}"]
        if self.postal_code:
            address_parts.append(f"индекс: {self.postal_code}")
        # Фильтруем пустые строки (если postal_code пустой)
        non_empty_parts = [part for part in address_parts if part.strip()]
        return ", ".join(non_empty_parts)

    def save(self, *args, **kwargs):
        """Переопределяем save для валидации иерархии"""
        # Проверка циклических ссылок
        if self.pk:
            # Получаем всех поставщиков по цепочке
            suppliers = set()
            current = self.supplier
            while current:
                if current.pk == self.pk or current in suppliers:
                    raise ValueError("Обнаружена циклическая ссылка в цепочке поставщиков!")
                suppliers.add(current)
                current = current.supplier

        # Для завода не может быть поставщика
        if self.node_type == self.NodeType.FACTORY and self.supplier:
            raise ValueError("Завод не может иметь поставщика!")

        super().save(*args, **kwargs)
