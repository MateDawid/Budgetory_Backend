from decimal import Decimal

from django.db.models import Model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from entities.models import Deposit
from wallets.models.wallet_deposit_model import WalletDeposit


class WalletDepositSerializer(serializers.ModelSerializer):
    """Serializer for WalletDeposit model."""

    class Meta:
        model: Model = WalletDeposit
        fields = ("id", "deposit", "planned_weight")
        read_only_fields = ("id",)

    def validate_deposit(self, deposit: Deposit) -> Deposit:
        # if deposit.budget.pk != self.context["view"].kwargs["wallet_pk"]:
        #     raise ValidationError("Budget not the same for Wallet and Deposit.")
        if WalletDeposit.objects.filter(
            wallet__budget__pk=self.context["view"].kwargs["budget_pk"], deposit=deposit
        ).exists():
            raise ValidationError("Deposit already assigned to another Wallet.")
        return deposit

    def validate_planned_weight(self, planned_weight: Decimal) -> Decimal:
        if not (Decimal("0.00") < planned_weight < Decimal("100.00")):
            raise ValidationError()
        # wallet_values = Wallet.objects.get(
        # wallet__pk=self.context["view"].kwargs["wallet_pk"]
        # ).deposits.values_list("planned_weight", flat=True)
        # if sum([planned_weight, *wallet_values])> Decimal("100"):
        #     raise ValidationError("Sum of planned weights for single Wallet has to be lower than 100.")
