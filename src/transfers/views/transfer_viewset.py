from django.db import transaction
from django.db.models import QuerySet
from django_filters import rest_framework as filters
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from transfers.serializers.transfer_serializer import TransferSerializer


class TransferViewSet(ModelViewSet):
    """Base ViewSet for managing Transfers."""

    serializer_class = TransferSerializer
    permission_classes = (IsAuthenticated, UserBelongsToBudgetPermission)
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    ordering_fields = ("id", "name", "value", "date", "period", "entity", "category", "deposit")

    def get_queryset(self) -> QuerySet:
        """
        Retrieve Transfer for Budget passed in URL.

        Returns:
            QuerySet: Filtered TransferCategory QuerySet.
        """
        return (
            self.serializer_class.Meta.model.objects.prefetch_related("period", "category")
            .filter(period__budget__pk=self.kwargs.get("budget_pk"))
            .distinct()
        )

    @swagger_auto_schema(
        method="delete",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "objects_ids": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_INTEGER),
                    description="List of IDs to delete.",
                )
            },
            required=["objects_ids"],
        ),
    )
    @action(detail=False, methods=["delete"])
    def bulk_delete(self, request, budget_pk: str) -> Response:
        """
        Removes multiple Transfers with given IDs at once.

        Returns:
            Response: API response with status.
        """
        ids = request.data.get("objects_ids", None)
        if not isinstance(ids, list):
            return Response({"error": "objects_ids must be a list."}, status=status.HTTP_400_BAD_REQUEST)
        if not ids:
            return Response({"error": "objects_ids must not be an empty list."}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            self.serializer_class.Meta.model.objects.filter(period__budget__id=int(budget_pk), id__in=ids).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        method="post",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "objects_ids": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_INTEGER),
                    description="List of IDs to copy.",
                )
            },
            required=["objects_ids"],
        ),
    )
    @action(detail=False, methods=["post"])
    def copy(self, request, budget_pk: str) -> Response:
        """
        Copies multiple Transfers with given IDs.

        Returns:
            Response: API response with status.
        """
        ids = request.data.get("objects_ids", None)
        if not isinstance(ids, list):
            return Response({"error": "objects_ids must be a list."}, status=status.HTTP_400_BAD_REQUEST)
        if not ids:
            return Response({"error": "objects_ids must not be an empty list."}, status=status.HTTP_400_BAD_REQUEST)
        new_objects = [
            self.serializer_class.Meta.model(
                **{
                    field_name: getattr(copied_object, field_name)
                    for field_name in ("transfer_type", *self.serializer_class.Meta.fields)
                    if field_name not in ("id",)
                }
            )
            for copied_object in self.serializer_class.Meta.model.objects.filter(
                period__budget__id=int(budget_pk), id__in=ids
            )
        ]
        objs = self.serializer_class.Meta.model.objects.bulk_create(new_objects)
        return Response({"ids": [obj.id for obj in objs]} if objs else [], status=status.HTTP_201_CREATED)
