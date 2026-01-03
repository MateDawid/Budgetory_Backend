from django_filters import rest_framework as filters


class WalletFilterSet(filters.FilterSet):
    """FilterSet for Wallet list endpoint."""

    name = filters.CharFilter(lookup_expr="icontains", field_name="name")
