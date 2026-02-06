from rest_framework import serializers

from .models import NetworkNode, Product


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
