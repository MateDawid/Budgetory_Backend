import os
import signal

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.views import View

from app_infrastructure.services.database_connection_service import DatabaseConnectionService


class HealthcheckView(View):
    """
    View checking if database connection is alive.
    """

    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse | None:
        """
        View returning API healthcheck status depending on database connection status.

        Args:
            request (HttpRequest): HttpRequest instance.

        Returns:
            HttpResponse | None: HttpResponse instance or None.
        """
        service = DatabaseConnectionService(database_alias=settings.DATABASE_CONNECTION_ALIAS)
        if service.is_connection_alive():
            return HttpResponse()
        else:
            os.kill(os.getpid(), signal.SIGINT)
