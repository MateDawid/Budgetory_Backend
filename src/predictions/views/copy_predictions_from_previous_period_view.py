import logging

from django.db import transaction
from django.db.models import Subquery
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from periods.models import BudgetingPeriod
from predictions.models import ExpensePrediction

logger = logging.getLogger("default")


class CopyPredictionsFromPreviousPeriodAPIView(APIView):
    """
    View for copying predictions from previous period.
    """

    permission_classes = (
        IsAuthenticated,
        UserBelongsToBudgetPermission,
    )

    def post(self, request: Request, budget_pk: int, period_pk: int) -> Response:
        """
        Handles copying ExpensePrediction from previous BudgetingPeriod of one with given period_pk.

        Args:
            request [Request]: User request.
            budget_pk [int]: Budget PK.
            period_pk [int]: Budgeting Period PK into which predictions will be copied.

        Returns:
            Response: HTTP response.
        """

        if ExpensePrediction.objects.filter(period_id=period_pk, category__isnull=False).exists():
            logger.warning(
                f"Copying Predictions from previous Period not started - "
                f"some Predictions already exist in current Period | Period ID: {period_pk}"
            )
            return Response(
                "Can not copy Predictions from previous Period if any Prediction for current Period exists.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        previous_period_predictions = ExpensePrediction.objects.filter(
            period__budget__pk=budget_pk,
            period__pk=Subquery(BudgetingPeriod.objects.filter(pk=period_pk).values("previous_period__pk")[:1]),
            category__isnull=False,
        ).values("category", "deposit", "current_plan", "description")
        if not previous_period_predictions:
            logger.warning(
                f"Copying Predictions from previous Period not started - "
                f"no Predictions to copy. | Period ID: {period_pk}"
            )
            return Response("No predictions to copy from previous Period.")
        with transaction.atomic():
            try:
                logger.info(f"Copying Predictions from previous Period started. | Period ID: {period_pk}")
                ExpensePrediction.objects.bulk_create(
                    [
                        ExpensePrediction(
                            period_id=period_pk,
                            deposit_id=previous_prediction["deposit"],
                            category_id=previous_prediction["category"],
                            current_plan=previous_prediction["current_plan"],
                            description=previous_prediction["description"],
                        )
                        for previous_prediction in previous_period_predictions
                    ]
                )
                return Response("Predictions copied successfully from previous Period.")
            except Exception as e:
                logger.error(
                    f"Copying Predictions from previous Period failed. | Period ID: {period_pk} | Reason: {str(e)}"
                )
                return Response(
                    "Unexpected error raised on copying Predictions from previous Period.",
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
