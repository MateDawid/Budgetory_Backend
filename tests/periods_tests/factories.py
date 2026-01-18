from datetime import date

import factory
from dateutil.relativedelta import relativedelta
from wallets_tests.factories import WalletFactory

from periods.models.choices.period_status import PeriodStatus


class PeriodFactory(factory.django.DjangoModelFactory):
    """Factory for Period model."""

    class Meta:
        model = "periods.Period"

    wallet = factory.SubFactory(WalletFactory)
    status = factory.Sequence(lambda _: PeriodStatus.DRAFT)

    @factory.lazy_attribute
    def date_start(self) -> date:
        """Generates date_start field."""
        last_date_start = self.wallet.periods.all().order_by("date_start").values_list("date_start", flat=True).last()
        if not last_date_start:
            return date(2023, 1, 1)
        return last_date_start + relativedelta(months=1)

    @factory.lazy_attribute
    def date_end(self) -> date:
        """Generates date_end field."""
        last_date_start = self.wallet.periods.all().order_by("date_start").values_list("date_start", flat=True).last()
        if not last_date_start:
            return date(2023, 1, 31)
        return last_date_start + relativedelta(months=2) - relativedelta(days=1)

    @factory.lazy_attribute
    def name(self) -> str:
        """Generates period name basing on provided date_range."""
        year_start, year_end = self.date_start.year, self.date_end.year
        month_start, month_end = self.date_start.month, self.date_end.month
        if year_start == year_end and month_start == month_end:
            return f"{year_start}_{month_start:02d}"  # noqa:E231
        else:
            return f"{year_start}_{month_start:02d} - {year_end}_{month_end:02d}"  # pragma: no cover  # noqa:E231
