import pytest
from categories_tests.utils import annotate_transfer_category_queryset
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from categories.models.transfer_category_model import TransferCategory
from categories.serializers.transfer_category_serializer import TransferCategorySerializer


def categories_url(budget_id):
    """Create and return an TransferCategory detail URL."""
    return reverse("budgets:category-list", args=[budget_id])


def category_detail_url(budget_id, category_id):
    """Create and return an TransferCategory detail URL."""
    return reverse("budgets:category-detail", args=[budget_id, category_id])


@pytest.mark.django_db
class TestTransferCategoryFilterSetOrdering:
    """Tests for ordering with TransferCategoryFilterSet."""

    @pytest.mark.parametrize(
        "sort_param",
        (
            "id",
            "-id",
            "name",
            "-name",
            "category_type",
            "-category_type",
            "priority",
            "-priority",
            "owner",
            "-owner",
            "priority,name",
        ),
    )
    def test_get_sorted_categories_list(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        sort_param: str,
    ):
        """
        GIVEN: Three TransferCategory objects created in database.
        WHEN: The TransferCategoryViewSet list view is called with sorting by given param and without any filters.
        THEN: Response must contain all TransferCategory existing in database sorted by given param.
        """
        member_1 = user_factory(email="bob@bob.com")
        member_2 = user_factory(email="alice@alice.com")
        budget = budget_factory(members=[member_1, member_2])
        transfer_category_factory(budget=budget, name="Aaa", owner=member_2, priority=CategoryPriority.MOST_IMPORTANT)
        transfer_category_factory(budget=budget, name="Bbb", owner=member_1, priority=CategoryPriority.OTHERS)
        transfer_category_factory(budget=budget, name="Ccc", owner=None, priority=CategoryPriority.REGULAR)
        api_client.force_authenticate(member_1)

        response = api_client.get(categories_url(budget.id), data={"ordering": sort_param})

        assert response.status_code == status.HTTP_200_OK
        categories = annotate_transfer_category_queryset(TransferCategory.objects.all()).order_by(
            *sort_param.split(",")
        )
        serializer = TransferCategorySerializer(categories, many=True)
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == len(categories) == 3
        assert response.data == serializer.data


@pytest.mark.django_db
class TestTransferCategoryFilterSetFiltering:
    """Tests for filtering with TransferCategoryFilterSet."""

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
    @pytest.mark.parametrize(
        "param",
        ("name", "description"),
    )
    def test_get_categories_list_filtered_by_char_filter(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        param: str,
        filter_value: str,
    ):
        """
        GIVEN: Two TransferCategory objects for single Budget.
        WHEN: The TransferCategoryViewSet list view is called with "name" filter.
        THEN: Response must contain all TransferCategory existing in database assigned to Budget containing given
        "name" value in name param.
        """
        budget = budget_factory(members=[base_user])
        matching_category = transfer_category_factory(budget=budget, **{param: "Some category"})
        transfer_category_factory(budget=budget, **{param: "Other one"})
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_url(budget.id), data={param: filter_value})

        assert response.status_code == status.HTTP_200_OK
        assert TransferCategory.objects.all().count() == 2
        categories = annotate_transfer_category_queryset(
            TransferCategory.objects.filter(budget=budget, id=matching_category.id)
        )
        serializer = TransferCategorySerializer(
            categories,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == categories.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == matching_category.id

    def test_get_categories_list_filtered_by_owner(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two TransferCategory objects for single Budget - one with owner set, one without an owner.
        WHEN: The TransferCategoryViewSet list view is called with "owner" filter.
        THEN: Response must contain all TransferCategory existing in database assigned to Budget with
        matching "owner" value.
        """
        budget = budget_factory(members=[base_user])
        matching_category = transfer_category_factory(budget=budget, name="Some category", owner=base_user)
        transfer_category_factory(budget=budget, name="Other one", owner=None)
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_url(budget.id), data={"owner": base_user.id})

        assert response.status_code == status.HTTP_200_OK
        assert TransferCategory.objects.all().count() == 2
        categories = annotate_transfer_category_queryset(
            TransferCategory.objects.filter(budget=budget, id=matching_category.id)
        )
        serializer = TransferCategorySerializer(
            categories,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == categories.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == matching_category.id

    def test_get_categories_list_filtered_by_empty_owner(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two TransferCategory objects for single Budget - one with owner set, one without an owner.
        WHEN: The TransferCategoryViewSet list view is called with -1 value for "owner" filter.
        THEN: Response must contain all TransferCategory existing in database assigned to Budget with
        None value for "owner" field.
        """
        budget = budget_factory(members=[base_user])
        matching_category = transfer_category_factory(budget=budget, name="Some category", owner=None)
        transfer_category_factory(budget=budget, name="Other one", owner=base_user)
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_url(budget.id), data={"owner": -1})

        assert response.status_code == status.HTTP_200_OK
        assert TransferCategory.objects.all().count() == 2
        categories = annotate_transfer_category_queryset(
            TransferCategory.objects.filter(budget=budget, id=matching_category.id)
        )
        serializer = TransferCategorySerializer(
            categories,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == categories.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == matching_category.id

    @pytest.mark.parametrize("filter_value", (True, False))
    def test_get_categories_list_filtered_by_is_active(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        filter_value: bool,
    ):
        """
        GIVEN: Two TransferCategory objects for single Budget.
        WHEN: The TransferCategoryViewSet list view is called with "is_active" filter.
        THEN: Response must contain all TransferCategory existing in database assigned to Budget with
        matching "is_active" value.
        """
        budget = budget_factory(members=[base_user])
        matching_category = transfer_category_factory(budget=budget, name="Some category", is_active=filter_value)
        transfer_category_factory(budget=budget, name="Other one", is_active=not filter_value)
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_url(budget.id), data={"is_active": filter_value})

        assert response.status_code == status.HTTP_200_OK
        assert TransferCategory.objects.all().count() == 2
        categories = annotate_transfer_category_queryset(
            TransferCategory.objects.filter(budget=budget, id=matching_category.id)
        )
        serializer = TransferCategorySerializer(
            categories,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == categories.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == matching_category.id

    def test_get_categories_list_filtered_by_category_type(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two TransferCategory objects for single Budget.
        WHEN: The TransferCategoryViewSet list view is called with "category_type" filter.
        THEN: Response must contain all TransferCategory existing in database assigned to Budget with
        matching "category_type" value.
        """
        budget = budget_factory(members=[base_user])
        matching_category = transfer_category_factory(
            budget=budget, name="Some category", category_type=CategoryType.EXPENSE
        )
        transfer_category_factory(budget=budget, name="Other one", category_type=CategoryType.INCOME)
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_url(budget.id), data={"category_type": CategoryType.EXPENSE.value})

        assert response.status_code == status.HTTP_200_OK
        assert TransferCategory.objects.all().count() == 2
        categories = annotate_transfer_category_queryset(
            TransferCategory.objects.filter(budget=budget, id=matching_category.id)
        )
        serializer = TransferCategorySerializer(
            categories,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == categories.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == matching_category.id

    def test_get_categories_list_filtered_by_priority(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two TransferCategory objects for single Budget.
        WHEN: The TransferCategoryViewSet list view is called with "priority" filter.
        THEN: Response must contain all TransferCategory existing in database assigned to Budget with
        matching "priority" value.
        """
        budget = budget_factory(members=[base_user])
        matching_category = transfer_category_factory(
            budget=budget, name="Some category", priority=CategoryPriority.MOST_IMPORTANT
        )
        transfer_category_factory(budget=budget, name="Other one", priority=CategoryPriority.OTHERS)
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_url(budget.id), data={"priority": CategoryPriority.MOST_IMPORTANT.value})

        assert response.status_code == status.HTTP_200_OK
        assert TransferCategory.objects.all().count() == 2
        categories = annotate_transfer_category_queryset(
            TransferCategory.objects.filter(budget=budget, id=matching_category.id)
        )
        serializer = TransferCategorySerializer(
            categories,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == categories.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == matching_category.id
