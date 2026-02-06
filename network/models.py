from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone


class Product(models.Model):
    """Модель продукта/товара с требованиями из ТЗ"""

    name = models.CharField(max_length=255, verbose_name="Название продукта", help_text="Полное название продукта")
    model = models.CharField(max_length=255, verbose_name="Модель", help_text="Модель или артикул продукта")
    release_date = models.DateField(
        verbose_name="Дата выхода на рынок", help_text="Дата, когда продукт стал доступен для покупки"
    )

    # Дополнительные поля для расширения функциональности
    description = models.TextField(verbose_name="Описание", blank=True, help_text="Подробное описание продукта")
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Рекомендованная цена",
        null=True,
        blank=True,
        help_text="Цена в рублях",
    )

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"
        ordering = ["name", "model"]
        constraints = [models.UniqueConstraint(fields=["name", "model"], name="unique_product_name_model")]

    def __str__(self):
        return f"{self.name} - {self.model} ({self.release_date.year})"

    @property
    def is_new(self):
        """Является ли продукт новым (вышел менее 6 месяцев назад)"""
        six_months_ago = timezone.now().date() - timezone.timedelta(days=180)
        return self.release_date > six_months_ago


class NetworkNode(models.Model):
    """Модель звена сети с полным соответствием требованиям ТЗ"""

    class NodeType(models.TextChoices):
        FACTORY = "factory", "Завод"
        RETAIL_NETWORK = "retail_network", "Розничная сеть"
        INDIVIDUAL_ENTREPRENEUR = "individual_entrepreneur", "Индивидуальный предприниматель"

    # === 1. НАЗВАНИЕ ===
    name = models.CharField(
        max_length=255, verbose_name="Название звена", help_text="Официальное название компании или ИП"
    )

    # === 2. ТИП ЗВЕНА ===
    node_type = models.CharField(max_length=30, choices=NodeType.choices, verbose_name="Тип звена")

    # === 3. ИЕРАРХИЧЕСКИЕ СВЯЗИ ===
    supplier = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
        verbose_name="Поставщик",
        help_text="Вышестоящее звено в цепочке поставок",
    )

    # === 4. КОНТАКТЫ ===
    email = models.EmailField(unique=True, verbose_name="Электронная почта", help_text="Контактный email для связи")

    # Валидатор для номера телефона (русский формат)
    phone_regex = RegexValidator(
        regex=r"^\+?1?\d{9,15}$", message="Номер телефона должен быть в формате: '+79991234567'. До 15 цифр."
    )
    phone = models.CharField(
        validators=[phone_regex], max_length=17, verbose_name="Телефон", blank=True, help_text="Контактный телефон"
    )

    # Адресные поля
    country = models.CharField(max_length=100, verbose_name="Страна", default="Россия")
    city = models.CharField(max_length=100, verbose_name="Город", help_text="Город, где находится звено сети")
    street = models.CharField(max_length=100, verbose_name="Улица", help_text="Название улицы")
    house_number = models.CharField(
        max_length=20, verbose_name="Номер дома", help_text="Номер дома, включая корпус/строение"
    )
    postal_code = models.CharField(max_length=20, verbose_name="Почтовый индекс", blank=True)

    # === 5. ПРОДУКТЫ ===
    products = models.ManyToManyField(
        Product,
        related_name="network_nodes",
        verbose_name="Продукты",
        blank=True,
        help_text="Продукты, которые доступны у данного звена",
    )

    # === 6. ЗАДОЛЖЕННОСТЬ ===
    debt = models.DecimalField(
        max_digits=15,  # Максимум 9999999999999.99
        decimal_places=2,  # Точность до копеек ✓
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name="Задолженность перед поставщиком",
        help_text="Задолженность в рублях с точностью до копеек",
    )

    # === 7. ВРЕМЕННЫЕ МЕТКИ (автоматические) ===
    created_at = models.DateTimeField(
        auto_now_add=True,  # Автоматически при создании ✓
        verbose_name="Время создания",
        help_text="Дата и время создания записи (заполняется автоматически)",
    )
    updated_at = models.DateTimeField(
        auto_now=True, verbose_name="Время последнего обновления"  # Автоматически при обновлении
    )

    class Meta:
        verbose_name = "Звено сети"
        verbose_name_plural = "Звенья сети"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["node_type"]),
            models.Index(fields=["city"]),
            models.Index(fields=["country"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["supplier"]),
        ]

    def __str__(self):
        return f"{self.get_node_type_display()}: {self.name}"

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
                # Используем рекурсию с кешированием через БД
                self._level_cache = self.supplier.level + 1
        return self._level_cache

    @property
    def full_address(self):
        """Полный адрес в формате строки"""
        address_parts = [f"{self.country}, г. {self.city}", f"ул. {self.street}, д. {self.house_number}"]
        if self.postal_code:
            address_parts.append(f"индекс: {self.postal_code}")
        return ", ".join([part for part in address_parts if part.strip()])

    @property
    def contact_info(self):
        """Полная контактная информация"""
        contacts = [f"Email: {self.email}"]
        if self.phone:
            contacts.append(f"Телефон: {self.phone}")
        contacts.append(f"Адрес: {self.full_address}")
        return "\n".join(contacts)

    def clean(self):
        """Валидация данных перед сохранением"""
        from django.core.exceptions import ValidationError

        # Завод не может иметь поставщика
        if self.node_type == self.NodeType.FACTORY and self.supplier:
            raise ValidationError({"supplier": "Завод не может иметь поставщика!"})

        # Проверка циклических ссылок
        if self.pk and self.supplier:
            visited = set()
            current = self.supplier

            while current:
                if current.pk == self.pk:
                    raise ValidationError({"supplier": "Обнаружена циклическая ссылка в цепочке поставщиков!"})
                if current in visited:
                    break
                visited.add(current)
                current = current.supplier

        super().clean()

    def save(self, *args, **kwargs):
        """Переопределяем save для дополнительной валидации"""
        self.full_clean()  # Вызываем clean метод
        super().save(*args, **kwargs)


class Employee(models.Model):
    """Модель сотрудника с привязкой к пользователю Django"""

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="employee_profile", verbose_name="Пользователь"
    )
    department = models.CharField(
        max_length=100, verbose_name="Отдел", blank=True, help_text="Отдел, в котором работает сотрудник"
    )
    position = models.CharField(max_length=100, verbose_name="Должность", blank=True, help_text="Должность сотрудника")
    phone = models.CharField(max_length=20, verbose_name="Рабочий телефон", blank=True)
    is_active = models.BooleanField(
        default=True, verbose_name="Активный сотрудник", help_text="Определяет, имеет ли сотрудник доступ к системе"
    )
    hire_date = models.DateField(verbose_name="Дата приема на работу", auto_now_add=True)
    last_login_date = models.DateTimeField(verbose_name="Дата последнего входа", null=True, blank=True)

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ["user__last_name", "user__first_name"]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.position})"

    @property
    def full_name(self):
        return self.user.get_full_name()

    @property
    def email(self):
        return self.user.email

    @property
    def is_staff_member(self):
        """Проверяет, является ли сотрудник членом персонала"""
        return self.user.is_staff

    def update_last_login(self):
        """Обновляет дату последнего входа"""
        self.last_login_date = timezone.now()
        self.save(update_fields=["last_login_date"])
