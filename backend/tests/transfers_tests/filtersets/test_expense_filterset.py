import pytest
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from transfers.models.expense_model import Expense
from transfers.serializers.expense_serializer import ExpenseSerializer


def transfers_url(budget_id):
    """Create and return an Expense detail URL."""
    return reverse("budgets:expense-list", args=[budget_id])


def transfer_detail_url(budget_id, transfer_id):
    """Create and return an Expense detail URL."""
    return reverse("budgets:expense-detail", args=[budget_id, transfer_id])


@pytest.mark.django_db
class TestExpenseFilterSetOrdering:
    """Tests for ordering with ExpenseFilterSet."""

    @pytest.mark.parametrize(
        "sort_param",
        (
            "id",
            "name",
            "value",
            "date",
            "period__name",
            "entity__name",
            "deposit__name",
            "category__name",
            "category__priority",
            "-id",
            "-name",
            "-value",
            "-date",
            "-period__name",
            "-entity__name",
            "-deposit__name",
            "-category__name",
            "-category__priority",
        ),
    )
    def test_get_transfers_list_sorted_by_single_param(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
        sort_param: str,
    ):
        """
        GIVEN: Five Expense objects created in database.
        WHEN: The ExpenseViewSet list view is called with sorting by given param and without any filters.
        THEN: Response must contain all Expense existing in database sorted by given param.
        """
        budget = budget_factory(owner=base_user)
        for _ in range(5):
            expense_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(transfers_url(budget.id), data={"ordering": sort_param})

        assert response.status_code == status.HTTP_200_OK
        transfers = Expense.objects.all().order_by(sort_param)
        serializer = ExpenseSerializer(transfers, many=True)
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == len(transfers) == 5
        assert response.data["results"] == serializer.data


# @pytest.mark.django_db
# class TestExpenseFilterSetFiltering:
#     """Tests for filtering with ExpenseFilterSet."""
#
#     @pytest.mark.parametrize(
#         "filter_value",
#         (
#             "Some transfer",
#             "SOME CATEGORY",
#             "some transfer",
#             "SoMe CaTeGoRy",
#             "Some",
#             "some",
#             "SOME",
#             "Category",
#             "transfer",
#             "CATEGORY",
#         ),
#     )
#     def test_get_transfers_list_filtered_by_name(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_factory: FactoryMetaClass,
#         filter_value: str,
#     ):
#         """
#         GIVEN: Two Expense objects for single Budget.
#         WHEN: The ExpenseViewSet list view is called with "name" filter.
#         THEN: Response must contain all Expense existing in database assigned to Budget containing given
#         "name" value in name param.
#         """
#         budget = budget_factory(owner=base_user)
#         matching_transfer = expense_factory(budget=budget, name="Some transfer")
#         expense_factory(budget=budget, name="Other one")
#         api_client.force_authenticate(base_user)
#
#         response = api_client.get(transfers_url(budget.id), data={"name": filter_value})
#
#         assert response.status_code == status.HTTP_200_OK
#         assert Expense.objects.all().count() == 2
#         transfers = Expense.objects.filter(budget=budget, id=matching_transfer.id)
#         serializer = ExpenseSerializer(
#             transfers,
#             many=True,
#         )
#         assert response.data["results"] and serializer.data
#         assert len(response.data["results"]) == len(serializer.data) == transfers.count() == 1
#         assert response.data["results"] == serializer.data
#         assert response.data["results"][0]["id"] == matching_transfer.id
#
#     def test_get_transfers_list_filtered_by_common_only(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Two Expense objects for single Budget.
#         WHEN: The ExpenseViewSet list view is called with "common_only"=True filter.
#         THEN: Response must contain all Expense existing in database assigned to Budget without owner assigned.
#         """
#         budget = budget_factory(owner=base_user)
#         matching_transfer = expense_factory(budget=budget, name="Some transfer", owner=None)
#         expense_factory(budget=budget, name="Other one", owner=base_user)
#         api_client.force_authenticate(base_user)
#
#         response = api_client.get(transfers_url(budget.id), data={"common_only": True})
#
#         assert response.status_code == status.HTTP_200_OK
#         assert Expense.objects.all().count() == 2
#         transfers = Expense.objects.filter(budget=budget, id=matching_transfer.id)
#         serializer = ExpenseSerializer(
#             transfers,
#             many=True,
#         )
#         assert response.data["results"] and serializer.data
#         assert len(response.data["results"]) == len(serializer.data) == transfers.count() == 1
#         assert response.data["results"] == serializer.data
#         assert response.data["results"][0]["id"] == matching_transfer.id
#
#     def test_get_transfers_list_filtered_by_owner(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Two Expense objects for single Budget.
#         WHEN: The ExpenseViewSet list view is called with "owner" filter.
#         THEN: Response must contain all Expense existing in database assigned to Budget with
#         matching "owner" value.
#         """
#         budget = budget_factory(owner=base_user)
#         matching_transfer = expense_factory(budget=budget, name="Some transfer", owner=base_user)
#         expense_factory(budget=budget, name="Other one", owner=None)
#         api_client.force_authenticate(base_user)
#
#         response = api_client.get(transfers_url(budget.id), data={"owner": base_user.id})
#
#         assert response.status_code == status.HTTP_200_OK
#         assert Expense.objects.all().count() == 2
#         transfers = Expense.objects.filter(budget=budget, id=matching_transfer.id)
#         serializer = ExpenseSerializer(
#             transfers,
#             many=True,
#         )
#         assert response.data["results"] and serializer.data
#         assert len(response.data["results"]) == len(serializer.data) == transfers.count() == 1
#         assert response.data["results"] == serializer.data
#         assert response.data["results"][0]["id"] == matching_transfer.id
#
#     @pytest.mark.parametrize("filter_value", (True, False))
#     def test_get_transfers_list_filtered_by_is_active(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_factory: FactoryMetaClass,
#         filter_value: bool,
#     ):
#         """
#         GIVEN: Two Expense objects for single Budget.
#         WHEN: The ExpenseViewSet list view is called with "is_active" filter.
#         THEN: Response must contain all Expense existing in database assigned to Budget with
#         matching "is_active" value.
#         """
#         budget = budget_factory(owner=base_user)
#         matching_transfer = expense_factory(budget=budget, name="Some transfer", is_active=filter_value)
#         expense_factory(budget=budget, name="Other one", is_active=not filter_value)
#         api_client.force_authenticate(base_user)
#
#         response = api_client.get(transfers_url(budget.id), data={"is_active": filter_value})
#
#         assert response.status_code == status.HTTP_200_OK
#         assert Expense.objects.all().count() == 2
#         transfers = Expense.objects.filter(budget=budget, id=matching_transfer.id)
#         serializer = ExpenseSerializer(
#             transfers,
#             many=True,
#         )
#         assert response.data["results"] and serializer.data
#         assert len(response.data["results"]) == len(serializer.data) == transfers.count() == 1
#         assert response.data["results"] == serializer.data
#         assert response.data["results"][0]["id"] == matching_transfer.id
#
#     def test_get_transfers_list_filtered_by_priority(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Two Expense objects for single Budget.
#         WHEN: The ExpenseViewSet list view is called with "priority" filter.
#         THEN: Response must contain all Expense existing in database assigned to Budget with
#         matching "priority" value.
#         """
#         budget = budget_factory(owner=base_user)
#         matching_transfer = expense_factory(
#             budget=budget, name="Some transfer", priority=ExpensePriority.MOST_IMPORTANT
#         )
#         expense_factory(budget=budget, name="Other one", priority=ExpensePriority.DEBTS)
#         api_client.force_authenticate(base_user)
#
#         response = api_client.get(
#             transfers_url(budget.id), data={"priority": ExpensePriority.MOST_IMPORTANT.value}
#         )
#
#         assert response.status_code == status.HTTP_200_OK
#         assert Expense.objects.all().count() == 2
#         transfers = Expense.objects.filter(budget=budget, id=matching_transfer.id)
#         serializer = ExpenseSerializer(
#             transfers,
#             many=True,
#         )
#         assert response.data["results"] and serializer.data
#         assert len(response.data["results"]) == len(serializer.data) == transfers.count() == 1
#         assert response.data["results"] == serializer.data
#         assert response.data["results"][0]["id"] == matching_transfer.id
