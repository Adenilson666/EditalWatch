from typing import Any

import psycopg
from psycopg.errors import UniqueViolation

from editalwatch.database import Database
from editalwatch.exceptions import (
    DatabaseOperationError,
    SourceAlreadyExistsError,
    SourceNotFoundError,
)
from editalwatch.models import (
    Source,
    SourceInput,
    SourceType,
)


class SourceRepository:
    """Executa operações da tabela sources."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def create(self, data: SourceInput) -> Source:
        """Cadastra e retorna uma nova fonte."""
        try:
            with self._database.connect() as connection:
                row = connection.execute(
                    """
                    INSERT INTO sources (
                        name,
                        base_url,
                        source_type,
                        terms_url,
                        robots_url,
                        collection_allowed,
                        policy_checked_at,
                        is_active
                    )
                    VALUES (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    RETURNING
                        id,
                        name,
                        base_url,
                        source_type,
                        terms_url,
                        robots_url,
                        collection_allowed,
                        policy_checked_at,
                        is_active,
                        created_at
                    """,
                    (
                        data.name,
                        data.base_url,
                        data.source_type.value,
                        data.terms_url,
                        data.robots_url,
                        data.collection_allowed,
                        data.policy_checked_at,
                        data.is_active,
                    ),
                ).fetchone()

        except UniqueViolation as error:
            raise SourceAlreadyExistsError(
                f'A fonte "{data.name}" já está cadastrada.'
            ) from error

        except psycopg.Error as error:
            raise DatabaseOperationError(
                "Não foi possível cadastrar a fonte."
            ) from error

        if row is None:
            raise DatabaseOperationError(
                "O PostgreSQL não retornou a fonte cadastrada."
            )

        return self._from_row(row)

    def get_by_id(
        self,
        source_id: int,
    ) -> Source | None:
        """Consulta uma fonte pelo identificador."""
        try:
            with self._database.connect() as connection:
                row = connection.execute(
                    """
                    SELECT
                        id,
                        name,
                        base_url,
                        source_type,
                        terms_url,
                        robots_url,
                        collection_allowed,
                        policy_checked_at,
                        is_active,
                        created_at
                    FROM sources
                    WHERE id = %s
                    """,
                    (source_id,),
                ).fetchone()

        except psycopg.Error as error:
            raise DatabaseOperationError(
                "Não foi possível consultar a fonte."
            ) from error

        if row is None:
            return None

        return self._from_row(row)

    def list_all(self) -> list[Source]:
        """Lista todas as fontes cadastradas."""
        try:
            with self._database.connect() as connection:
                rows = connection.execute(
                    """
                    SELECT
                        id,
                        name,
                        base_url,
                        source_type,
                        terms_url,
                        robots_url,
                        collection_allowed,
                        policy_checked_at,
                        is_active,
                        created_at
                    FROM sources
                    ORDER BY name
                    """
                ).fetchall()

        except psycopg.Error as error:
            raise DatabaseOperationError(
                "Não foi possível listar as fontes."
            ) from error

        return [
            self._from_row(row)
            for row in rows
        ]

    def update(
        self,
        source_id: int,
        data: SourceInput,
    ) -> Source:
        """Atualiza e retorna uma fonte existente."""
        try:
            with self._database.connect() as connection:
                row = connection.execute(
                    """
                    UPDATE sources
                    SET
                        name = %s,
                        base_url = %s,
                        source_type = %s,
                        terms_url = %s,
                        robots_url = %s,
                        collection_allowed = %s,
                        policy_checked_at = %s,
                        is_active = %s
                    WHERE id = %s
                    RETURNING
                        id,
                        name,
                        base_url,
                        source_type,
                        terms_url,
                        robots_url,
                        collection_allowed,
                        policy_checked_at,
                        is_active,
                        created_at
                    """,
                    (
                        data.name,
                        data.base_url,
                        data.source_type.value,
                        data.terms_url,
                        data.robots_url,
                        data.collection_allowed,
                        data.policy_checked_at,
                        data.is_active,
                        source_id,
                    ),
                ).fetchone()

        except UniqueViolation as error:
            raise SourceAlreadyExistsError(
                f'Já existe uma fonte chamada "{data.name}".'
            ) from error

        except psycopg.Error as error:
            raise DatabaseOperationError(
                "Não foi possível atualizar a fonte."
            ) from error

        if row is None:
            raise SourceNotFoundError(
                f"Nenhuma fonte foi encontrada com o ID "
                f"{source_id}."
            )

        return self._from_row(row)

    def delete(self, source_id: int) -> None:
        """Remove uma fonte pelo identificador."""
        try:
            with self._database.connect() as connection:
                row = connection.execute(
                    """
                    DELETE FROM sources
                    WHERE id = %s
                    RETURNING id
                    """,
                    (source_id,),
                ).fetchone()

        except psycopg.Error as error:
            raise DatabaseOperationError(
                "Não foi possível remover a fonte."
            ) from error

        if row is None:
            raise SourceNotFoundError(
                f"Nenhuma fonte foi encontrada com o ID "
                f"{source_id}."
            )

    @staticmethod
    def _from_row(
        row: dict[str, Any],
    ) -> Source:
        """Converte uma linha do banco em Source."""
        return Source(
            id=row["id"],
            name=row["name"],
            base_url=row["base_url"],
            source_type=SourceType(row["source_type"]),
            terms_url=row["terms_url"],
            robots_url=row["robots_url"],
            collection_allowed=row["collection_allowed"],
            policy_checked_at=row["policy_checked_at"],
            is_active=row["is_active"],
            created_at=row["created_at"],
        )