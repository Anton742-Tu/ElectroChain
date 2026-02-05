from django_filters import rest_framework as filters

from .models import NetworkNode


class NetworkNodeFilter(filters.FilterSet):
    debt_gt = filters.NumberFilter(field_name="debt", lookup_expr="gt")
    debt_lt = filters.NumberFilter(field_name="debt", lookup_expr="lt")
    has_debt = filters.BooleanFilter(method="filter_has_debt")

    class Meta:
        model = NetworkNode
        fields = ["country", "city", "node_type"]

    def filter_has_debt(self, queryset, name, value):
        if value:
            return queryset.filter(debt__gt=0)
        return queryset.filter(debt=0)
