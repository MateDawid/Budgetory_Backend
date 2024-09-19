import logging

from django.db import DatabaseError, connections

logger = logging.getLogger("db_connection_logger")


class DatabaseConnectionService:
    """
    Service for checking state of database connection.

    Args:
        database_alias (str): Alias for database from DATABASES declared in settings.py, f.e. "default".
    """

    def __init__(self, database_alias: str):
        self.database_alias = database_alias

    def is_connection_alive(self):
        """
        Checks if database connection with given alias is alive.

        Returns:
            bool: True if database connection is fine. False in case of DatabaseError raised during ensuring connection.
        """
        try:
            db_connection = connections[self.database_alias]
            db_connection.ensure_connection()
        except DatabaseError as e:
            logger.error(f'Database error raised for alias "{self.database_alias}".')
            logger.error(str(e))
            return False
        return True
