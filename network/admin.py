from django.contrib import admin
from django.db import models
from django.shortcuts import render
from django.urls import reverse
from django.utils.html import format_html

from .models import NetworkNode, Product


class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "model", "release_date", "price_display")
    list_filter = ("release_date",)
    search_fields = ("name", "model", "description")

    def price_display(self, obj):
        if obj.price:
            return f"{obj.price} руб."
        return "—"

    price_display.short_description = "Цена"


class SupplierCityFilter(admin.SimpleListFilter):
    """Кастомный фильтр по городу поставщика"""

    title = "Город поставщика"
    parameter_name = "supplier_city"

    def lookups(self, request, model_admin):
        # Получаем уникальные города поставщиков
        cities = (
            NetworkNode.objects.exclude(supplier__isnull=True)
            .values_list("supplier__city", flat=True)
            .distinct()
            .order_by("supplier__city")
        )
        return [(city, city) for city in cities if city]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(supplier__city=self.value())
        return queryset


class NetworkNodeAdmin(admin.ModelAdmin):
    # === 1. ОТОБРАЖЕНИЕ В СПИСКЕ ===
    list_display = (
        "name",
        "node_type_display",
        "level_display",
        "supplier_link",
        "city",
        "debt_display",
        "created_at_display",
        "action_buttons",
    )

    # === 2. ФИЛЬТРЫ ===
    list_filter = (
        "node_type",
        "city",  # Фильтр по городу самого объекта
        SupplierCityFilter,  # Фильтр по городу поставщика
        "country",
        "created_at",
    )

    # === 3. ПОИСК ===
    search_fields = ("name", "email", "phone", "country", "city", "street")

    # === 4. ПОЛЯ ТОЛЬКО ДЛЯ ЧТЕНИЯ ===
    readonly_fields = (
        "level_display",
        "supplier_link_field",
        "created_at",
        "updated_at",
        "full_address_display",
        "contact_info_display",
        "products_list_display",
    )

    # === 5. ГРУППИРОВКА ПОЛЕЙ НА СТРАНИЦЕ ИЗМЕНЕНИЯ ===
    fieldsets = (
        ("Основная информация", {"fields": ("name", "node_type", "level_display", "supplier_link_field")}),
        ("Контактная информация", {"fields": ("email", "phone", "contact_info_display")}),
        ("Адрес", {"fields": ("country", "city", "street", "house_number", "postal_code", "full_address_display")}),
        ("Продукция", {"fields": ("products", "products_list_display"), "classes": ("wide", "collapse")}),
        ("Финансы", {"fields": ("debt",), "classes": ("collapse",)}),
        ("Временные метки", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )

    # === 6. ГОРИЗОНТАЛЬНЫЙ ФИЛЬТР ДЛЯ МНОГОКОЕ-МНОГОМ ===
    filter_horizontal = ("products",)

    # === 7. ADMIN ACTIONS ===
    actions = ["clear_debt_action", "mark_as_factory", "copy_object"]

    # === 8. ОПТИМИЗАЦИЯ ЗАПРОСОВ ===
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related("supplier").prefetch_related("products")

    # === 9. МЕТОДЫ ДЛЯ ОТОБРАЖЕНИЯ В СПИСКЕ ===

    def node_type_display(self, obj):
        """Отображение типа звена с цветовой кодировкой"""
        colors = {
            "factory": "#2196F3",  # синий
            "retail_network": "#9C27B0",  # фиолетовый
            "individual_entrepreneur": "#4CAF50",  # зеленый
        }
        color = colors.get(obj.node_type, "#757575")
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, obj.get_node_type_display())

    node_type_display.short_description = "Тип"
    node_type_display.admin_order_field = "node_type"

    def level_display(self, obj):
        """Отображение уровня иерархии с цветовым индикатором"""
        colors = ["#4CAF50", "#2196F3", "#FF9800", "#F44336"]  # зеленый, синий, оранжевый, красный
        color = colors[min(obj.level, len(colors) - 1)]
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 12px; font-weight: bold; font-size: 11px;">Уровень {}</span>',
            color,
            obj.level,
        )

    level_display.short_description = "Уровень"

    def supplier_link(self, obj):
        """Ссылка на поставщика в списке объектов"""
        if obj.supplier:
            url = reverse("admin:network_networknode_change", args=[obj.supplier.id])
            supplier_type = obj.supplier.get_node_type_display()
            city = obj.supplier.city
            return format_html(
                '<a href="{}" style="color: #1976D2; text-decoration: none;">'
                '<span style="font-weight: 500;">{}:</span><br>'
                '<span style="color: #666; font-size: 12px;">{} (г. {})</span>'
                "</a>",
                url,
                supplier_type,
                obj.supplier.name,
                city,
            )
        return format_html('<span style="color: #999; font-style: italic;">— Нет поставщика —</span>')

    supplier_link.short_description = "Поставщик"
    supplier_link.admin_order_field = "supplier__name"

    def supplier_link_field(self, obj):
        """Ссылка на поставщика на странице изменения объекта"""
        if obj.supplier:
            url = reverse("admin:network_networknode_change", args=[obj.supplier.id])
            return format_html(
                '<div style="padding: 10px; background: #f5f5f5; border-radius: 5px; margin: 5px 0;">'
                "<strong>Поставщик:</strong><br>"
                '<a href="{}" style="color: #1976D2; font-size: 14px;">'
                "{} → {}</a><br>"
                '<span style="color: #666; font-size: 12px;">г. {}, тел: {}</span>'
                "</div>",
                url,
                obj.supplier.get_node_type_display(),
                obj.supplier.name,
                obj.supplier.city,
                obj.supplier.phone or "не указан",
            )
        return format_html(
            '<div style="padding: 10px; background: #f5f5f5; border-radius: 5px; margin: 5px 0;">'
            "<strong>Поставщик:</strong><br>"
            '<span style="color: #999; font-style: italic;">Нет поставщика (завод)</span>'
            "</div>"
        )

    supplier_link_field.short_description = "Информация о поставщике"

    def debt_display(self, obj):
        """Отображение задолженности с цветовой индикацией"""
        debt_value = float(obj.debt)
        formatted_debt = f"{debt_value:,.2f}".replace(",", " ") + " ₽"

        if debt_value > 0:
            return format_html(
                '<div style="display: flex; align-items: center;">'
                '<span style="color: #D32F2F; font-weight: bold; font-size: 14px;">{}</span>'
                '<span style="margin-left: 5px; background: #FFCDD2; color: #C62828; '
                'padding: 2px 6px; border-radius: 3px; font-size: 11px;">ДОЛГ</span>'
                "</div>",
                formatted_debt,
            )
        else:
            return format_html('<span style="color: #388E3C; font-weight: 500;">{}</span>', formatted_debt)

    debt_display.short_description = "Задолженность"
    debt_display.admin_order_field = "debt"

    def created_at_display(self, obj):
        """Форматированное отображение даты создания"""
        return obj.created_at.strftime("%d.%m.%Y в %H:%M")

    created_at_display.short_description = "Создан"
    created_at_display.admin_order_field = "created_at"

    def action_buttons(self, obj):
        """Кнопки действий в списке"""
        change_url = reverse("admin:network_networknode_change", args=[obj.id])
        clear_debt_url = reverse("admin:network_networknode_clear_debt", args=[obj.id])

        return format_html(
            '<div style="display: flex; gap: 5px;">'
            '<a href="{}" class="button" style="padding: 5px 10px; background: #417690; '
            'color: white; text-decoration: none; border-radius: 3px; font-size: 12px;">Изменить</a>'
            "{}"
            "</div>",
            change_url,
            (
                format_html(
                    '<a href="{}" class="button" style="padding: 5px 10px; background: #4CAF50; '
                    'color: white; text-decoration: none; border-radius: 3px; font-size: 12px;" '
                    "onclick=\"return confirm('Очистить задолженность?')\">Очистить долг</a>",
                    clear_debt_url,
                )
                if obj.debt > 0
                else ""
            ),
        )

    action_buttons.short_description = "Действия"
    action_buttons.allow_tags = True

    # === 10. МЕТОДЫ ДЛЯ СТРАНИЦЫ ИЗМЕНЕНИЯ ОБЪЕКТА ===

    def full_address_display(self, obj):
        """Отображение полного адреса"""
        return format_html(
            '<div style="padding: 10px; background: #E3F2FD; border-radius: 5px; margin: 5px 0;">'
            "<strong>Полный адрес:</strong><br>"
            "{}<br>"
            '<span style="font-size: 12px; color: #666;">ID: {}</span>'
            "</div>",
            obj.full_address,
            obj.id,
        )

    full_address_display.short_description = "Адрес"

    def contact_info_display(self, obj):
        """Отображение контактной информации"""
        return format_html(
            '<div style="padding: 10px; background: #E8F5E8; border-radius: 5px; margin: 5px 0;">'
            "<strong>Контакты:</strong><br>"
            "📧 {}<br>"
            "📞 {}<br>"
            "</div>",
            obj.email,
            obj.phone or "не указан",
        )

    contact_info_display.short_description = "Контактная информация"

    def products_list_display(self, obj):
        """Отображение списка продуктов"""
        products = obj.products.all()
        if not products:
            return format_html(
                '<div style="padding: 10px; background: #FFF3E0; border-radius: 5px; '
                'color: #E65100; font-style: italic;">'
                "Нет привязанных продуктов"
                "</div>"
            )

        items = []
        for i, product in enumerate(products, 1):
            items.append(f"{i}. {product.name} ({product.model}) - {product.release_date.year} г.")

        return format_html(
            '<div style="padding: 10px; background: #F3E5F5; border-radius: 5px; margin: 5px 0;">'
            "<strong>Продукты ({}):</strong><br>{}"
            "</div>",
            len(products),
            "<br>".join(items),
        )

    products_list_display.short_description = "Список продуктов"

    # === 11. ADMIN ACTIONS ===

    def clear_debt_action(self, request, queryset):
        """Admin action: очистка задолженности"""
        count = queryset.count()
        total_debt = queryset.aggregate(total=models.Sum("debt"))["total"] or 0

        if count == 0:
            self.message_user(request, "Не выбрано ни одного объекта.", level="warning")
            return

        confirmation = request.POST.get("confirmation")
        if not confirmation and request.method == "POST":
            # Показываем подтверждение
            selected = queryset.values_list("id", "name", "debt")
            context = {
                "title": "Подтверждение очистки задолженности",
                "queryset": queryset,
                "selected": selected,
                "count": count,
                "total_debt": total_debt,
                "action_checkbox_name": admin.helpers.ACTION_CHECKBOX_NAME,
            }
            return render(request, "admin/clear_debt_confirmation.html", context)

        updated = queryset.update(debt=0)
        self.message_user(
            request,
            f"✅ Задолженность очищена для {updated} объектов. " f"Списано {total_debt:,.2f} ₽.",
            level="success",
        )

    clear_debt_action.short_description = "🔄 Очистить задолженность"
    clear_debt_action.icon = "icon-trash"

    def mark_as_factory(self, request, queryset):
        """Admin action: пометить как завод"""
        updated = queryset.update(node_type="factory", supplier=None)
        self.message_user(request, f"✅ {updated} объектов помечены как заводы. Поставщики сброшены.")

    mark_as_factory.short_description = "🏭 Пометить как завод"

    def copy_object(self, request, queryset):
        """Admin action: копировать объекты"""
        from django.db import transaction

        with transaction.atomic():
            copied_count = 0
            for obj in queryset:
                # Создаем копию объекта
                obj.pk = None
                obj.name = f"{obj.name} (копия)"
                obj.email = f"copy_{obj.email}"
                obj.debt = 0  # Сбрасываем долг при копировании
                obj.save()
                # Копируем связи ManyToMany
                obj.products.set(obj.products.all())
                copied_count += 1

        self.message_user(request, f"✅ Создано {copied_count} копий объектов.")

    copy_object.short_description = "📋 Создать копию"

    # === 12. КАСТОМНЫЕ URLS ДЛЯ ОДИНОЧНЫХ ДЕЙСТВИЙ ===

    def get_urls(self):
        """Добавляем кастомные URLs для действий с одним объектом"""
        from django.urls import path

        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/clear-debt/",
                self.admin_site.admin_view(self.clear_debt_single),
                name="network_networknode_clear_debt",
            ),
        ]
        return custom_urls + urls

    def clear_debt_single(self, request, object_id):
        """Очистка задолженности для одного объекта"""
        from django.shortcuts import redirect

        obj = self.get_object(request, object_id)
        if obj:
            old_debt = obj.debt
            obj.debt = 0
            obj.save()
            self.message_user(
                request, f"✅ Задолженность для '{obj.name}' очищена. " f"Списано {old_debt:,.2f} ₽.", level="success"
            )

        # Возвращаемся обратно
        referer = request.META.get("HTTP_REFERER")
        if referer:
            return redirect(referer)
        return redirect("admin:network_networknode_changelist")


admin.site.register(Product, ProductAdmin)
admin.site.register(NetworkNode, NetworkNodeAdmin)
