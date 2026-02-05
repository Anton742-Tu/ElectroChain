from django.contrib import admin
from django.utils.html import format_html

from .models import NetworkNode, Product


class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "model", "release_date")
    list_filter = ("release_date",)
    search_fields = ("name", "model", "description")

    def price_display(self, obj):
        if obj.price:
            return f"{obj.price} руб."
        return "—"

    price_display.short_description = "Цена"

    def is_new_display(self, obj):
        if obj.is_new:
            return "✓ Новый"
        return "—"

    is_new_display.short_description = "Новый продукт"


class NetworkNodeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "get_node_type_display",
        "level_display",
        "supplier_info",
        "city",
        "debt_display",
        "created_at_display",
    )
    list_filter = ("node_type", "city", "country", "created_at")
    search_fields = ("name", "email", "phone", "country", "city", "street")
    readonly_fields = ("level_display", "created_at", "updated_at", "full_address_display")
    fieldsets = (
        ("Основная информация", {"fields": ("name", "node_type", "supplier", "level_display")}),
        (
            "Контактная информация",
            {"fields": ("email", "phone", "country", "city", "street", "house_number", "postal_code")},
        ),
        ("Продукция", {"fields": ("products",)}),
        ("Финансы", {"fields": ("debt",)}),
        ("Временные метки", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    filter_horizontal = ("products",)
    actions = ["clear_debt"]

    def level_display(self, obj):
        return obj.level

    level_display.short_description = "Уровень"

    def supplier_info(self, obj):
        if obj.supplier:
            # Простой текст вместо ссылки для начала
            return f"{obj.supplier.get_node_type_display()}: {obj.supplier.name}"
        return "—"

    supplier_info.short_description = "Поставщик"
    supplier_info.admin_order_field = "supplier__name"

    def debt_display(self, obj):
        """Отображение задолженности с цветовой индикацией"""
        debt_value = float(obj.debt)
        formatted_debt = f"{debt_value:.2f} руб."

        if debt_value > 0:
            return format_html('<span style="color: #D32F2F; font-weight: bold;">{}</span>', formatted_debt)
        else:
            return format_html('<span style="color: #388E3C;">{}</span>', formatted_debt)

    def created_at_display(self, obj):
        return obj.created_at.strftime("%d.%m.%Y %H:%M")

    created_at_display.short_description = "Создан"
    created_at_display.admin_order_field = "created_at"

    def full_address_display(self, obj):
        return obj.full_address

    full_address_display.short_description = "Полный адрес"

    def clear_debt(self, request, queryset):
        """Действие для очистки задолженности"""
        updated = queryset.update(debt=0)
        self.message_user(request, f"Задолженность очищена для {updated} объектов.")

    clear_debt.short_description = "Очистить задолженность"

    def get_queryset(self, request):
        """Оптимизируем запросы"""
        queryset = super().get_queryset(request)
        return queryset.select_related("supplier")


admin.site.register(Product, ProductAdmin)
admin.site.register(NetworkNode, NetworkNodeAdmin)
