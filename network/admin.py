from django.contrib import admin
from django.utils.html import format_html

from .models import NetworkNode, Product


class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "model", "release_date", "price_display", "is_new_display")
    list_filter = ("release_date",)
    search_fields = ("name", "model", "description")
    readonly_fields = ("is_new_display",)
    fieldsets = (
        ("Основная информация", {"fields": ("name", "model", "release_date", "is_new_display")}),
        ("Дополнительная информация", {"fields": ("description", "price")}),
    )

    def price_display(self, obj):
        return f"{obj.price} руб." if obj.price else "—"

    price_display.short_description = "Цена"

    def is_new_display(self, obj):
        if obj.is_new:
            return format_html('<span style="color: green;">✓ Новый</span>')
        return "—"

    is_new_display.short_description = "Новый продукт"


class NetworkNodeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "node_type_display",
        "level_display",
        "supplier_link",
        "city",
        "products_count",
        "debt_display",
        "created_at_display",
    )
    list_filter = ("node_type", "city", "country", "created_at")
    search_fields = ("name", "email", "phone", "country", "city", "street")
    readonly_fields = (
        "level_display",
        "full_address_display",
        "contact_info_display",
        "created_at",
        "updated_at",
        "products_list_display",
    )
    fieldsets = (
        ("Основная информация", {"fields": ("name", "node_type", "supplier", "level_display")}),
        ("Контактная информация", {"fields": ("email", "phone", "contact_info_display")}),
        ("Адрес", {"fields": ("country", "city", "street", "house_number", "postal_code", "full_address_display")}),
        ("Продукция", {"fields": ("products", "products_list_display"), "classes": ("wide",)}),
        ("Финансы", {"fields": ("debt",), "classes": ("collapse",)}),
        ("Временные метки", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )
    filter_horizontal = ("products",)
    actions = ["clear_debt"]

    def node_type_display(self, obj):
        type_colors = {"factory": "blue", "retail_network": "purple", "individual_entrepreneur": "green"}
        color = type_colors.get(obj.node_type, "black")
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_node_type_display())

    node_type_display.short_description = "Тип звена"
    node_type_display.admin_order_field = "node_type"

    def level_display(self, obj):
        colors = ["#4CAF50", "#2196F3", "#FF9800"]  # зеленый, синий, оранжевый
        color = colors[obj.level % len(colors)] if obj.level < len(colors) else "#9C27B0"
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px;/n'
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.level,
        )

    level_display.short_description = "Уровень"

    def supplier_link(self, obj):
        if obj.supplier:
            return format_html(
                '<a href="{}" style="color: #1976D2;">{}</a>',
                f"/admin/network/networknode/{obj.supplier.id}/change/",
                f"{obj.supplier.get_node_type_display()}: {obj.supplier.name}",
            )
        return format_html('<span style="color: #666;">— Нет поставщика —</span>')

    supplier_link.short_description = "Поставщик"
    supplier_link.admin_order_field = "supplier__name"

    def debt_display(self, obj):
        if obj.debt > 0:
            return format_html('<span style="color: #D32F2F; font-weight: bold;">{:.2f} ₽</span>', float(obj.debt))
        return format_html('<span style="color: #388E3C;">{:.2f} ₽</span>', float(obj.debt))

    debt_display.short_description = "Задолженность"
    debt_display.admin_order_field = "debt"

    def products_count(self, obj):
        count = obj.products.count()
        return format_html(
            '<span style="background: #E3F2FD; padding: 2px 8px; border-radius: 10px;">{}</span>', count
        )

    products_count.short_description = "Продуктов"
    products_count.admin_order_field = "products__count"

    def created_at_display(self, obj):
        return obj.created_at.strftime("%d.%m.%Y %H:%M")

    created_at_display.short_description = "Создан"
    created_at_display.admin_order_field = "created_at"

    def full_address_display(self, obj):
        return format_html('<pre style="margin: 0;">{}</pre>', obj.full_address)

    full_address_display.short_description = "Полный адрес"

    def contact_info_display(self, obj):
        return format_html(
            '<pre style="background: #f5f5f5; padding: 10px; border-radius: 5px;">{}</pre>', obj.contact_info
        )

    contact_info_display.short_description = "Контактная информация"

    def products_list_display(self, obj):
        products = obj.products.all()
        if not products:
            return "Нет продуктов"

        items = []
        for product in products:
            items.append(f"• {product.name} ({product.model}) - {product.release_date.year}")

        return format_html("<br>".join(items))

    products_list_display.short_description = "Список продуктов"

    def clear_debt(self, request, queryset):
        """Действие для очистки задолженности"""
        updated = queryset.update(debt=0)
        self.message_user(request, f"✅ Задолженность очищена для {updated} объектов.")

    clear_debt.short_description = "🔄 Очистить задолженность"

    def get_queryset(self, request):
        """Оптимизируем запросы"""
        queryset = super().get_queryset(request)
        return queryset.select_related("supplier").prefetch_related("products")


admin.site.register(Product, ProductAdmin)
admin.site.register(NetworkNode, NetworkNodeAdmin)
