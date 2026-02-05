from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from .filters import NetworkNodeFilter
from .models import NetworkNode, Product
from .serializers import (NetworkNodeCreateSerializer, NetworkNodeSerializer,
                          NetworkNodeUpdateSerializer, ProductSerializer)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class NetworkNodeViewSet(viewsets.ModelViewSet):
    queryset = NetworkNode.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = NetworkNodeFilter  # Используем кастомный фильтр
    search_fields = ["name", "email", "city"]
    ordering_fields = ["name", "created_at", "debt"]

    def get_serializer_class(self):
        if self.action == "create":
            return NetworkNodeCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return NetworkNodeUpdateSerializer
        return NetworkNodeSerializer
