from django.contrib import admin
from django.utils.html import format_html

from .models import NetworkNode, Product


class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "model", "release_date")
    list_filter = ("release_date",)
    search_fields = ("name", "model")
    ordering = ("name",)


class NetworkNodeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "node_type_display",
        "level_display",
        "supplier_link",
        "city",
        "debt_display",
        "created_at",
    )
    list_filter = ("node_type", "city", "country", "created_at")
    search_fields = ("name", "email", "country", "city")
    readonly_fields = ("level_display", "full_address_display", "created_at", "updated_at")
    fieldsets = (
        ("Основная информация", {"fields": ("name", "node_type", "supplier", "level_display")}),
        ("Контактная информация", {"fields": ("email", "phone", "full_address_display")}),
        ("Адрес", {"fields": ("country", "city", "street", "house_number", "postal_code")}),
        ("Продукция", {"fields": ("products",)}),
        ("Финансы", {"fields": ("debt",)}),
        ("Временные метки", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    filter_horizontal = ("products",)
    actions = ["clear_debt"]

    def node_type_display(self, obj):
        return obj.get_node_type_display()

    node_type_display.short_description = "Тип звена"
    node_type_display.admin_order_field = "node_type"

    def level_display(self, obj):
        return obj.level

    level_display.short_description = "Уровень"

    def supplier_link(self, obj):
        if obj.supplier:
            return format_html(
                '<a href="{}">{}</a>', f"/admin/network/networknode/{obj.supplier.id}/change/", obj.supplier.name
            )
        return "—"

    supplier_link.short_description = "Поставщик"
    supplier_link.admin_order_field = "supplier__name"

    def debt_display(self, obj):
        """Отображение задолженности с цветовой индикацией"""
        try:
            # Преобразуем в float, если это Decimal
            debt_value = float(obj.debt) if obj.debt else 0.0
        except (ValueError, TypeError):
            debt_value = 0.0

        if debt_value > 0:
            return format_html('<span style="color: red; font-weight: bold;">{} руб.</span>', f"{debt_value:.2f}")
        else:
            return format_html('<span style="color: green;">{} руб.</span>', f"{debt_value:.2f}")

    def full_address_display(self, obj):
        return format_html(
            "{}<br>{}<br>{}",
            f"{obj.country}, {obj.city}",
            f"ул. {obj.street}, д. {obj.house_number}",
            f"индекс: {obj.postal_code}" if obj.postal_code else "",
        )

    full_address_display.short_description = "Полный адрес"

    def clear_debt(self, request, queryset):
        """Действие для очистки задолженности"""
        updated = queryset.update(debt=0)
        self.message_user(request, f"Задолженность очищена для {updated} объектов.")

    clear_debt.short_description = "Очистить задолженность"

    def get_queryset(self, request):
        """Оптимизируем запрос, чтобы избежать N+1 проблемы"""
        queryset = super().get_queryset(request)
        # Используем select_related для supplier, чтобы избежать дополнительных запросов
        queryset = queryset.select_related("supplier")
        return queryset


admin.site.register(Product, ProductAdmin)
admin.site.register(NetworkNode, NetworkNodeAdmin)
