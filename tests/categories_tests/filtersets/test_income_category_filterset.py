import pytest
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from categories.models.income_category_model import IncomeCategory
from categories.models.transfer_category_choices import IncomeCategoryPriority
from categories.serializers.income_category_serializer import IncomeCategorySerializer


def categories_url(budget_id):
    """Create and return an IncomeCategory detail URL."""
    return reverse("budgets:income_category-list", args=[budget_id])


def category_detail_url(budget_id, category_id):
    """Create and return an IncomeCategory detail URL."""
    return reverse("budgets:income_category-detail", args=[budget_id, category_id])


@pytest.mark.django_db
class TestIncomeCategoryFilterSetOrdering:
    """Tests for ordering with IncomeCategoryFilterSet."""

    @pytest.mark.parametrize(
        "sort_param",
        ("id", "-id", "name", "-name", "priority", "-priority"),
    )
    def test_get_categories_list_sorted_by_single_param(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
        sort_param: str,
    ):
        """
        GIVEN: Five IncomeCategory objects created in database.
        WHEN: The IncomeCategoryViewSet list view is called with sorting by given param and without any filters.
        THEN: Response must contain all IncomeCategory existing in database sorted by given param.
        """
        member_1 = user_factory(email="bob@bob.com")
        member_2 = user_factory(email="alice@alice.com")
        member_3 = user_factory(email="george@george.com")
        budget = budget_factory(members=[member_1, member_2, member_3])
        income_category_factory(budget=budget, name="Eee", owner=member_1, priority=IncomeCategoryPriority.REGULAR)
        income_category_factory(budget=budget, name="Ddd", owner=None, priority=IncomeCategoryPriority.REGULAR)
        income_category_factory(budget=budget, name="Ccc", owner=member_2, priority=IncomeCategoryPriority.IRREGULAR)
        income_category_factory(budget=budget, name="Bbb", owner=member_3, priority=IncomeCategoryPriority.REGULAR)
        income_category_factory(budget=budget, name="Aaa", owner=None, priority=IncomeCategoryPriority.IRREGULAR)
        api_client.force_authenticate(member_1)

        response = api_client.get(categories_url(budget.id), data={"ordering": sort_param})

        assert response.status_code == status.HTTP_200_OK
        categories = IncomeCategory.objects.all().order_by(sort_param)
        serializer = IncomeCategorySerializer(categories, many=True)
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == len(categories) == 5
        assert response.data["results"] == serializer.data

    def test_get_categories_list_sorted_by_two_params(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Five IncomeCategory objects created in database.
        WHEN: The IncomeCategoryViewSet list view is called with two sorting params by given params.
        THEN: Response must contain all IncomeCategory existing in database sorted by given params.
        """
        member_1 = user_factory(email="bob@bob.com")
        member_2 = user_factory(email="alice@alice.com")
        member_3 = user_factory(email="george@george.com")
        budget = budget_factory(members=[member_1, member_2, member_3])
        income_category_factory(budget=budget, name="Ddd", owner=None, priority=IncomeCategoryPriority.REGULAR)
        income_category_factory(budget=budget, name="Eee", owner=member_1, priority=IncomeCategoryPriority.REGULAR)
        income_category_factory(budget=budget, name="Ccc", owner=member_2, priority=IncomeCategoryPriority.IRREGULAR)
        income_category_factory(budget=budget, name="Bbb", owner=member_3, priority=IncomeCategoryPriority.REGULAR)
        income_category_factory(budget=budget, name="Aaa", owner=None, priority=IncomeCategoryPriority.IRREGULAR)
        api_client.force_authenticate(member_1)

        response = api_client.get(categories_url(budget.id), data={"ordering": "priority,name"})

        assert response.status_code == status.HTTP_200_OK
        categories = IncomeCategory.objects.all().order_by("priority", "name")
        serializer = IncomeCategorySerializer(categories, many=True)
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == len(categories) == 5
        assert response.data["results"] == serializer.data


@pytest.mark.django_db
class TestIncomeCategoryFilterSetFiltering:
    """Tests for filtering with IncomeCategoryFilterSet."""

    @pytest.mark.parametrize(
        "filter_value",
        (
            "Some category",
            "SOME CATEGORY",
            "some category",
            "SoMe CaTeGoRy",
            "Some",
            "some",
            "SOME",
            "Category",
            "category",
            "CATEGORY",
        ),
    )
    def test_get_categories_list_filtered_by_name(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
        filter_value: str,
    ):
        """
        GIVEN: Two IncomeCategory objects for single Budget.
        WHEN: The IncomeCategoryViewSet list view is called with "name" filter.
        THEN: Response must contain all IncomeCategory existing in database assigned to Budget containing given
        "name" value in name param.
        """
        budget = budget_factory(members=[base_user])
        matching_category = income_category_factory(budget=budget, name="Some category")
        income_category_factory(budget=budget, name="Other one")
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_url(budget.id), data={"name": filter_value})

        assert response.status_code == status.HTTP_200_OK
        assert IncomeCategory.objects.all().count() == 2
        categories = IncomeCategory.objects.filter(budget=budget, id=matching_category.id)
        serializer = IncomeCategorySerializer(
            categories,
            many=True,
        )
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == categories.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == matching_category.id

    def test_get_categories_list_filtered_by_common_only(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two IncomeCategory objects for single Budget.
        WHEN: The IncomeCategoryViewSet list view is called with "common_only"=True filter.
        THEN: Response must contain all IncomeCategory existing in database assigned to Budget without owner assigned.
        """
        budget = budget_factory(members=[base_user])
        matching_category = income_category_factory(budget=budget, name="Some category", owner=None)
        income_category_factory(budget=budget, name="Other one", owner=base_user)
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_url(budget.id), data={"common_only": True})

        assert response.status_code == status.HTTP_200_OK
        assert IncomeCategory.objects.all().count() == 2
        categories = IncomeCategory.objects.filter(budget=budget, id=matching_category.id)
        serializer = IncomeCategorySerializer(
            categories,
            many=True,
        )
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == categories.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == matching_category.id

    def test_get_categories_list_filtered_by_owner(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two IncomeCategory objects for single Budget.
        WHEN: The IncomeCategoryViewSet list view is called with "owner" filter.
        THEN: Response must contain all IncomeCategory existing in database assigned to Budget with
        matching "owner" value.
        """
        budget = budget_factory(members=[base_user])
        matching_category = income_category_factory(budget=budget, name="Some category", owner=base_user)
        income_category_factory(budget=budget, name="Other one", owner=None)
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_url(budget.id), data={"owner": base_user.id})

        assert response.status_code == status.HTTP_200_OK
        assert IncomeCategory.objects.all().count() == 2
        categories = IncomeCategory.objects.filter(budget=budget, id=matching_category.id)
        serializer = IncomeCategorySerializer(
            categories,
            many=True,
        )
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == categories.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == matching_category.id

    @pytest.mark.parametrize("filter_value", (True, False))
    def test_get_categories_list_filtered_by_is_active(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
        filter_value: bool,
    ):
        """
        GIVEN: Two IncomeCategory objects for single Budget.
        WHEN: The IncomeCategoryViewSet list view is called with "is_active" filter.
        THEN: Response must contain all IncomeCategory existing in database assigned to Budget with
        matching "is_active" value.
        """
        budget = budget_factory(members=[base_user])
        matching_category = income_category_factory(budget=budget, name="Some category", is_active=filter_value)
        income_category_factory(budget=budget, name="Other one", is_active=not filter_value)
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_url(budget.id), data={"is_active": filter_value})

        assert response.status_code == status.HTTP_200_OK
        assert IncomeCategory.objects.all().count() == 2
        categories = IncomeCategory.objects.filter(budget=budget, id=matching_category.id)
        serializer = IncomeCategorySerializer(
            categories,
            many=True,
        )
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == categories.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == matching_category.id

    def test_get_categories_list_filtered_by_priority(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two IncomeCategory objects for single Budget.
        WHEN: The IncomeCategoryViewSet list view is called with "priority" filter.
        THEN: Response must contain all IncomeCategory existing in database assigned to Budget with
        matching "priority" value.
        """
        budget = budget_factory(members=[base_user])
        matching_category = income_category_factory(
            budget=budget, name="Some category", priority=IncomeCategoryPriority.REGULAR
        )
        income_category_factory(budget=budget, name="Other one", priority=IncomeCategoryPriority.IRREGULAR)
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_url(budget.id), data={"priority": IncomeCategoryPriority.REGULAR.value})

        assert response.status_code == status.HTTP_200_OK
        assert IncomeCategory.objects.all().count() == 2
        categories = IncomeCategory.objects.filter(budget=budget, id=matching_category.id)
        serializer = IncomeCategorySerializer(
            categories,
            many=True,
        )
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == categories.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == matching_category.id
