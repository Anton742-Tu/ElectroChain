from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .filters import NetworkNodeFilter
from .models import NetworkNode, Product
from .serializers import (NetworkNodeCreateSerializer, NetworkNodeSerializer,
                          NetworkNodeUpdateSerializer, ProductSerializer)


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet для модели Product"""

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "model"]
    ordering_fields = ["name", "release_date"]


class NetworkNodeViewSet(viewsets.ModelViewSet):
    """
    ViewSet для модели NetworkNode (поставщиков).
    Реализует CRUD операции с запретом обновления поля 'debt'.
    """

    queryset = NetworkNode.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = NetworkNodeFilter
    search_fields = ["name", "email", "city", "country"]
    ordering_fields = ["name", "created_at", "debt", "level"]

    def get_serializer_class(self):
        """
        Выбираем сериализатор в зависимости от действия.
        """
        if self.action == "create":
            return NetworkNodeCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return NetworkNodeUpdateSerializer
        return NetworkNodeSerializer

    def perform_create(self, serializer):
        """Создание нового объекта с автоматическим заполнением debt=0"""
        serializer.save(debt=0)  # При создании всегда debt=0

    @action(detail=False, methods=["get"])
    def by_country(self, request):
        """Получить звенья по стране (альтернативный способ фильтрации)"""
        country = request.query_params.get("country", None)
        if country:
            queryset = self.get_queryset().filter(country__iexact=country)
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response({"error": "Параметр country обязателен"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def suppliers_summary(self, request):
        """Статистика по поставщикам"""
        from django.db.models import Avg, Count, Sum

        stats = NetworkNode.objects.aggregate(
            total=Count("id"),
            factories=Count("id", filter=models.Q(node_type="factory")),
            retail_networks=Count("id", filter=models.Q(node_type="retail_network")),
            entrepreneurs=Count("id", filter=models.Q(node_type="individual_entrepreneur")),
            total_debt=Sum("debt"),
            avg_debt=Avg("debt"),
            with_supplier=Count("id", filter=models.Q(supplier__isnull=False)),
            without_supplier=Count("id", filter=models.Q(supplier__isnull=True)),
        )

        # Статистика по странам
        countries = (
            NetworkNode.objects.values("country")
            .annotate(count=Count("id"), total_debt=Sum("debt"))
            .order_by("-count")
        )

        return Response(
            {
                "statistics": stats,
                "by_country": list(countries),
                "filters_available": {
                    "country": "Фильтр по стране: /api/network-nodes/?country=Россия",
                    "city": "Фильтр по городу: /api/network-nodes/?city=Москва",
                    "node_type": "Фильтр по типу: /api/network-nodes/?node_type=factory",
                    "debt": "Фильтр по задолженности: /api/network-nodes/?debt_gt=1000",
                    "has_supplier": "Фильтр по наличию поставщика: /api/network-nodes/?has_supplier=true",
                },
            }
        )

    @action(detail=True, methods=["post"])
    def clear_debt(self, request, pk=None):
        """Очистить задолженность для конкретного объекта"""
        node = self.get_object()
        old_debt = node.debt
        node.debt = 0
        node.save()

        return Response(
            {"message": "Задолженность очищена", "object": node.name, "old_debt": float(old_debt), "new_debt": 0}
        )

    @action(detail=False, methods=["post"])
    def bulk_clear_debt(self, request):
        """Массовая очистка задолженности"""
        ids = request.data.get("ids", [])
        if not ids:
            return Response({"error": "Необходимо указать ids объектов"}, status=status.HTTP_400_BAD_REQUEST)

        queryset = NetworkNode.objects.filter(id__in=ids)
        count = queryset.count()
        total_debt = queryset.aggregate(total=Sum("debt"))["total"] or 0

        queryset.update(debt=0)

        return Response(
            {"message": "Задолженность очищена", "cleared_count": count, "total_debt_cleared": float(total_debt)}
        )
