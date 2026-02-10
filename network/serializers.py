from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Employee, NetworkNode, Product


class ProductSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Product"""

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ("id",)


class NetworkNodeSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения данных NetworkNode"""

    level = serializers.IntegerField(read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    supplier_type = serializers.CharField(source="supplier.get_node_type_display", read_only=True)
    products_info = ProductSerializer(source="products", many=True, read_only=True)
    full_address = serializers.CharField(read_only=True)

    class Meta:
        model = NetworkNode
        fields = "__all__"
        read_only_fields = ("id", "created_at", "updated_at", "level")


class NetworkNodeCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания NetworkNode"""

    class Meta:
        model = NetworkNode
        exclude = ("debt",)  # Исключаем debt при создании
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, data):
        """Дополнительная валидация"""
        # Завод не может иметь поставщика
        if data.get("node_type") == NetworkNode.NodeType.FACTORY and data.get("supplier"):
            raise serializers.ValidationError({"supplier": "Завод не может иметь поставщика!"})

        # Проверка циклических ссылок (упрощенная)
        supplier = data.get("supplier")
        if supplier and supplier.supplier and supplier.supplier == data.get("self"):
            raise serializers.ValidationError({"supplier": "Обнаружена циклическая ссылка в цепочке поставщиков!"})

        return data


class NetworkNodeUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления NetworkNode (без поля debt)"""

    class Meta:
        model = NetworkNode
        exclude = ("debt",)  # Запрещаем обновление debt через API
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, data):
        """Дополнительная валидация при обновлении"""
        # Проверяем, что debt не пытаются обновить
        if "debt" in self.initial_data:
            raise serializers.ValidationError({"debt": 'Обновление поля "Задолженность" через API запрещено!'})

        # Завод не может иметь поставщика
        if self.instance and self.instance.node_type == NetworkNode.NodeType.FACTORY and data.get("supplier"):
            raise serializers.ValidationError({"supplier": "Завод не может иметь поставщика!"})

        return data


class EmployeeSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Employee"""

    full_name = serializers.CharField(source="user.get_full_name", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id",
            "user",
            "full_name",
            "email",
            "username",
            "department",
            "position",
            "phone",
            "is_active",
            "hire_date",
            "last_login_date",
            "is_staff_member",
        ]
        read_only_fields = ["id", "user", "hire_date", "last_login_date"]


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации новых пользователей-сотрудников"""

    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    password_confirm = serializers.CharField(write_only=True, style={"input_type": "password"})
    department = serializers.CharField(write_only=True)
    position = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "password",
            "password_confirm",
            "department",
            "position",
        ]

    def validate(self, data):
        # Проверяем совпадение паролей
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Пароли не совпадают."})

        # Проверяем уникальность email
        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError({"email": "Пользователь с таким email уже существует."})

        return data

    def create(self, validated_data):
        # Создаем пользователя
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            is_staff=True,  # Все зарегистрированные сотрудники - персонал
        )

        # Создаем профиль сотрудника
        Employee.objects.create(
            user=user, department=validated_data["department"], position=validated_data["position"], is_active=True
        )

        return user
