from rest_framework import serializers

from .models import NetworkNode, Product


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = "__all__"


class NetworkNodeSerializer(serializers.ModelSerializer):
    level = serializers.IntegerField(read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    products_info = ProductSerializer(source="products", many=True, read_only=True)

    class Meta:
        model = NetworkNode
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")

    def validate(self, data):
        # Дополнительная валидация
        if "debt" in data and data["debt"] < 0:
            raise serializers.ValidationError({"debt": "Задолженность не может быть отрицательной"})
        return data


class NetworkNodeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkNode
        fields = "__all__"
        read_only_fields = ("created_at", "updated_at")

    def validate_debt(self, value):
        # Запрещаем установку долга при создании
        if value > 0:
            raise serializers.ValidationError("Нельзя установить задолженность при создании объекта")
        return value


class NetworkNodeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkNode
        exclude = ("debt",)  # Исключаем поле debt из обновления
        read_only_fields = ("created_at", "updated_at")
