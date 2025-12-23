from django.db.models import DecimalField, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from categories.models.choices.category_type import CategoryType
from entities.models import Entity
from transfers.models import Transfer


def get_entity_period_transfers_sum(
    transfer_type: CategoryType, period_id: str, deposit_id: str | None = None
) -> Coalesce:
    """
    Calculates given Transfer type Transfers sum in Period for entity.

    Args:
        transfer_type (CategoryType): Type of Transfer.
        period_id (str): BudgetingPeriod ID.
        deposit_id (str | None): Optional Deposit ID.
    Returns:
        Coalesce: Django ORM Coalesce function with Transfer subquery.
    """
    queryset_kwargs = {"transfer_type": transfer_type, "period_id": period_id}
    if deposit_id:
        queryset_kwargs["deposit_id"] = deposit_id
    return Coalesce(
        Subquery(
            Transfer.objects.filter(Q(entity_id=OuterRef("id"), **queryset_kwargs))
            .values("entity")
            .annotate(total=Sum("value"))
            .values("total")[:1],
            output_field=DecimalField(decimal_places=2),
        ),
        Value(0),
        output_field=DecimalField(decimal_places=2),
    )


class TopEntitiesInPeriodChartAPIView(APIView):
    """
    API view for retrieving data about Entity Transfers in Periods for chart purposes.

    Returns:
        Response containing:
            - xAxis: List of Entity names for chart x-axis
            - series: List of accumulated Expenses from Entities in given period.
    """

    permission_classes = (
        IsAuthenticated,
        UserBelongsToBudgetPermission,
    )

    def get(self, request: Request, budget_pk: int) -> Response:
        """
        Handle GET requests for Period Transfers chart data.

        Args:
            request (Request): User Request.
            budget_pk (int): Budget PK.

        Returns:
            Response: JSON response containing chart data with xAxis (entity names) and
            series (accumulated Expenses from Entities in given Period)
        """
        # Query params
        period_id = request.query_params.get("period", None)
        transfer_type = request.query_params.get("transfer_type", None)
        deposit_id = request.query_params.get("deposit", None)
        if period_id is None or transfer_type is None:
            return Response({"xAxis": [], "series": []})
        try:
            entities_count = int(request.query_params.get("entities_count"))
        except TypeError:  # Handle None value of query_params.entities_count
            entities_count = 5
        # Database query
        entities = (
            Entity.objects.filter(budget_id=budget_pk)
            .annotate(
                result=get_entity_period_transfers_sum(
                    transfer_type=transfer_type, period_id=period_id, deposit_id=deposit_id
                )
            )
            .filter(result__gt=0)
            .order_by("-result")
            .values()[:entities_count]
        )
        # Response
        response = {"xAxis": [], "series": []}
        for entity in entities:
            response["xAxis"].insert(0, entity["name"])
            response["series"].insert(0, entity["result"])
        return Response(response)
