from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg import Connection
from psycopg.rows import dict_row

from editalwatch.exceptions import DatabaseConnectionError


@dataclass(frozen=True, slots=True)
class DatabaseInfo:
    """Contém informações da conexão atual."""

    database_name: str
    username: str
    postgres_version: str


class Database:
    """Gerencia a criação de conexões com o PostgreSQL."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url

    def connect(
        self,
    ) -> Connection[dict[str, Any]]:
        """Cria e retorna uma nova conexão."""
        try:
            return psycopg.connect(
                self._database_url,
                row_factory=dict_row,
            )

        except psycopg.Error as error:
            raise DatabaseConnectionError(
                "Não foi possível conectar ao PostgreSQL."
            ) from error

    def check_connection(self) -> DatabaseInfo:
        """Testa a conexão e retorna informações do servidor."""
        try:
            with self.connect() as connection:
                row = connection.execute(
                    """
                    SELECT
                        current_database() AS database_name,
                        current_user AS username,
                        version() AS postgres_version
                    """
                ).fetchone()

        except psycopg.Error as error:
            raise DatabaseConnectionError(
                "A conexão foi criada, mas o PostgreSQL "
                "não respondeu corretamente."
            ) from error

        if row is None:
            raise DatabaseConnectionError(
                "O PostgreSQL não retornou informações."
            )

        return DatabaseInfo(
            database_name=row["database_name"],
            username=row["username"],
            postgres_version=row["postgres_version"],
        )