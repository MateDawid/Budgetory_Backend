from django.urls import path

from entities.views.deposit_type_view import DepositTypeView

app_name = "entities"

urlpatterns = [
    path("", DepositTypeView.as_view(), name="deposit-types"),
]
