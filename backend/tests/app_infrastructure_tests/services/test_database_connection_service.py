from unittest.mock import MagicMock, patch

from django.db.utils import DatabaseError

from app_infrastructure.services.database_connection_service import DatabaseConnectionService


class TestDatabaseConnectionService:
    """Tests for DatabaseConnectionService."""

    @patch("app_infrastructure.services.database_connection_service.DatabaseConnectionService.check_connection")
    def test_check_connection_successful(
        self,
        patched_check_connection: MagicMock,
    ):
        """
        GIVEN: Database account with password created.
        WHEN: Calling  DbConnector.check_connection() when connection is healthy.
        THEN: Method returns True.
        """
        patched_check_connection.side_effect = [None]
        connection = DatabaseConnectionService(database_alias="default")
        result = connection.is_connection_alive()

        assert result is True

    @patch("app_infrastructure.services.database_connection_service.DatabaseConnectionService.check_connection")
    def test_error_on_check_connection_successful(
        self,
        patched_check_connection: MagicMock,
    ):
        """
        GIVEN: Database account with password created.
        WHEN: Calling  DbConnector.check_connection() with not healthy connection and error not
        handled by .handle_db_error() method.
        THEN: Method returns False.
        """
        patched_check_connection.side_effect = [DatabaseError]

        connection = DatabaseConnectionService(database_alias="default")
        result = connection.is_connection_alive()

        assert result is False
