import django_filters

from .models import NetworkNode


class NetworkNodeFilter(django_filters.FilterSet):
    """Фильтр для NetworkNode с возможностью фильтрации по стране"""

    # Фильтр по стране (требование задания)
    country = django_filters.CharFilter(
        field_name="country", lookup_expr="iexact", label="Страна"  # Без учета регистра
    )

    # Фильтр по городу
    city = django_filters.CharFilter(field_name="city", lookup_expr="icontains", label="Город")

    # Фильтр по типу узла
    node_type = django_filters.ChoiceFilter(choices=NetworkNode.NodeType.choices, label="Тип звена")

    # Фильтр по наличию поставщика
    has_supplier = django_filters.BooleanFilter(method="filter_has_supplier", label="Есть поставщик")

    # Фильтр по задолженности
    debt_gt = django_filters.NumberFilter(field_name="debt", lookup_expr="gt", label="Задолженность больше чем")

    debt_lt = django_filters.NumberFilter(field_name="debt", lookup_expr="lt", label="Задолженность меньше чем")

    # Фильтр по уровню иерархии
    level = django_filters.NumberFilter(method="filter_by_level", label="Уровень иерархии")

    class Meta:
        model = NetworkNode
        fields = ["country", "city", "node_type"]

    def filter_has_supplier(self, queryset, name, value):
        """Фильтр по наличию поставщика"""
        if value:
            return queryset.filter(supplier__isnull=False)
        return queryset.filter(supplier__isnull=True)

    def filter_by_level(self, queryset, name, value):
        """Фильтр по уровню иерархии"""
        try:
            level = int(value)
            # Фильтруем через Python, так как level - свойство
            return [obj for obj in queryset if obj.level == level]
        except ValueError:
            return queryset
