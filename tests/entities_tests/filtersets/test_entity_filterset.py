import pytest
from django.contrib.auth.models import AbstractUser
from entities_tests.urls import entities_url
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from entities.models import Entity
from entities.serializers.entity_serializer import EntitySerializer


@pytest.mark.django_db
class TestEntityFilterSetOrdering:
    """Tests for ordering with EntityFilterSet."""

    @pytest.mark.parametrize(
        "sort_param",
        (
            "id",
            "-id",
            "name",
            "-name",
            "name,id",
        ),
    )
    def test_get_sorted_entities_list(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        sort_param: str,
    ):
        """
        GIVEN: Three Entity objects created in database.
        WHEN: The EntityViewSet list view is called with sorting by given param and without any filters.
        THEN: Response must contain all Entity existing in database sorted by given param.
        """
        owner = user_factory(email="bob@bob.com")
        wallet = wallet_factory(owner=owner)
        for _ in range(3):
            entity_factory(wallet=wallet)
        api_client.force_authenticate(owner)

        response = api_client.get(entities_url(wallet.id), data={"ordering": sort_param})

        assert response.status_code == status.HTTP_200_OK
        entities = Entity.objects.all().order_by(*sort_param.split(","))
        serializer = EntitySerializer(entities, many=True)
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == len(entities) == 3
        assert response.data == serializer.data


@pytest.mark.django_db
class TestEntityFilterSetFiltering:
    """Tests for filtering with EntityFilterSet."""

    @pytest.mark.parametrize(
        "filter_value",
        (
            "Some entity",
            "SOME ENTITY",
            "some entity",
            "SoMe EnTiTy",
            "Some",
            "some",
            "SOME",
            "Entity",
            "entity",
            "ENTITY",
        ),
    )
    @pytest.mark.parametrize(
        "param",
        ("name", "description"),
    )
    def test_get_entities_list_filtered_by_char_filter(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        param: str,
        filter_value: str,
    ):
        """
        GIVEN: Two Entity objects for single Wallet.
        WHEN: The EntityViewSet list view is called with CharFilter.
        THEN: Response must contain all Entity existing in database assigned to Wallet containing given
        "name" value in name param.
        """
        wallet = wallet_factory(owner=base_user)
        matching_entity = entity_factory(wallet=wallet, **{param: "Some entity"})
        entity_factory(wallet=wallet, **{param: "Other one"})
        api_client.force_authenticate(base_user)

        response = api_client.get(entities_url(wallet.id), data={param: filter_value})

        assert response.status_code == status.HTTP_200_OK
        assert Entity.objects.all().count() == 2
        entities = Entity.objects.filter(wallet=wallet, id=matching_entity.id)
        serializer = EntitySerializer(
            entities,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == entities.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == matching_entity.id

    @pytest.mark.parametrize("filter_value", (True, False))
    def test_get_entities_list_filtered_by_is_active(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        filter_value: bool,
    ):
        """
        GIVEN: Two Entity objects for single Wallet.
        WHEN: The EntityViewSet list view is called with "is_active" filter.
        THEN: Response must contain all Entity existing in database assigned to Wallet with
        matching "is_active" value.
        """
        wallet = wallet_factory(owner=base_user)
        matching_entity = entity_factory(wallet=wallet, name="Some entity", is_active=filter_value)
        entity_factory(wallet=wallet, name="Other one", is_active=not filter_value)
        api_client.force_authenticate(base_user)

        response = api_client.get(entities_url(wallet.id), data={"is_active": filter_value})

        assert response.status_code == status.HTTP_200_OK
        assert Entity.objects.all().count() == 2
        entities = Entity.objects.filter(wallet=wallet, id=matching_entity.id)
        serializer = EntitySerializer(
            entities,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == entities.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == matching_entity.id

    @pytest.mark.parametrize("filter_value", (True, False))
    def test_get_entities_list_filtered_by_is_deposit(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        filter_value: bool,
    ):
        """
        GIVEN: Two Entity objects for single Wallet.
        WHEN: The EntityViewSet list view is called with "is_deposit" filter.
        THEN: Response must contain all Entity existing in database assigned to Wallet with
        matching "is_deposit" value.
        """
        wallet = wallet_factory(owner=base_user)
        matching_entity = entity_factory(
            wallet=wallet,
            name="Some entity",
            is_deposit=filter_value,
        )
        entity_factory(
            wallet=wallet,
            name="Other one",
            is_deposit=not filter_value,
        )
        api_client.force_authenticate(base_user)

        response = api_client.get(entities_url(wallet.id), data={"is_deposit": filter_value})

        assert response.status_code == status.HTTP_200_OK
        assert Entity.objects.all().count() == 2
        entities = Entity.objects.filter(wallet=wallet, id=matching_entity.id)
        serializer = EntitySerializer(
            entities,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == entities.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == matching_entity.id
