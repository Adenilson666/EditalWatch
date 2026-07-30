from typing import Any

import psycopg
from psycopg.errors import UniqueViolation

from editalwatch.database import Database
from editalwatch.exceptions import (
    CategoryAlreadyExistsError,
    CategoryNotFoundError,
    DatabaseOperationError,
)
from editalwatch.models import (
    Category,
    CategoryInput,
)


class CategoryRepository:
    """Executa operações da tabela categories."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def create(
        self,
        data: CategoryInput,
    ) -> Category:
        """Cadastra e retorna uma categoria."""
        try:
            with self._database.connect() as connection:
                row = connection.execute(
                    """
                    INSERT INTO categories (
                        name
                    )
                    VALUES (
                        %s
                    )
                    RETURNING
                        id,
                        name,
                        created_at
                    """,
                    (data.name,),
                ).fetchone()

        except UniqueViolation as error:
            raise CategoryAlreadyExistsError(
                f'A categoria "{data.name}" já existe.'
            ) from error

        except psycopg.Error as error:
            raise DatabaseOperationError(
                "Não foi possível cadastrar a categoria."
            ) from error

        if row is None:
            raise DatabaseOperationError(
                "O PostgreSQL não retornou a categoria "
                "cadastrada."
            )

        return self._from_row(row)

    def get_or_create(
        self,
        data: CategoryInput,
    ) -> Category:
        """Retorna uma categoria existente ou cria uma nova."""
        try:
            with self._database.connect() as connection:
                row = connection.execute(
                    """
                    INSERT INTO categories (
                        name
                    )
                    VALUES (
                        %s
                    )
                    ON CONFLICT (name)
                    DO NOTHING
                    RETURNING
                        id,
                        name,
                        created_at
                    """,
                    (data.name,),
                ).fetchone()

                if row is None:
                    row = connection.execute(
                        """
                        SELECT
                            id,
                            name,
                            created_at
                        FROM categories
                        WHERE name = %s
                        """,
                        (data.name,),
                    ).fetchone()

        except psycopg.Error as error:
            raise DatabaseOperationError(
                "Não foi possível obter ou cadastrar "
                "a categoria."
            ) from error

        if row is None:
            raise DatabaseOperationError(
                "A categoria não foi criada nem encontrada."
            )

        return self._from_row(row)

    def get_by_id(
        self,
        category_id: int,
    ) -> Category | None:
        """Consulta uma categoria pelo identificador."""
        try:
            with self._database.connect() as connection:
                row = connection.execute(
                    """
                    SELECT
                        id,
                        name,
                        created_at
                    FROM categories
                    WHERE id = %s
                    """,
                    (category_id,),
                ).fetchone()

        except psycopg.Error as error:
            raise DatabaseOperationError(
                "Não foi possível consultar a categoria."
            ) from error

        if row is None:
            return None

        return self._from_row(row)

    def get_by_name(
        self,
        name: str,
    ) -> Category | None:
        """Consulta uma categoria pelo nome."""
        normalized_name = name.strip()

        try:
            with self._database.connect() as connection:
                row = connection.execute(
                    """
                    SELECT
                        id,
                        name,
                        created_at
                    FROM categories
                    WHERE name = %s
                    """,
                    (normalized_name,),
                ).fetchone()

        except psycopg.Error as error:
            raise DatabaseOperationError(
                "Não foi possível consultar a categoria."
            ) from error

        if row is None:
            return None

        return self._from_row(row)

    def list_all(self) -> list[Category]:
        """Lista todas as categorias por ordem alfabética."""
        try:
            with self._database.connect() as connection:
                rows = connection.execute(
                    """
                    SELECT
                        id,
                        name,
                        created_at
                    FROM categories
                    ORDER BY name
                    """
                ).fetchall()

        except psycopg.Error as error:
            raise DatabaseOperationError(
                "Não foi possível listar as categorias."
            ) from error

        return [
            self._from_row(row)
            for row in rows
        ]

    def update(
        self,
        category_id: int,
        data: CategoryInput,
    ) -> Category:
        """Atualiza o nome de uma categoria."""
        try:
            with self._database.connect() as connection:
                row = connection.execute(
                    """
                    UPDATE categories
                    SET name = %s
                    WHERE id = %s
                    RETURNING
                        id,
                        name,
                        created_at
                    """,
                    (
                        data.name,
                        category_id,
                    ),
                ).fetchone()

        except UniqueViolation as error:
            raise CategoryAlreadyExistsError(
                f'A categoria "{data.name}" já existe.'
            ) from error

        except psycopg.Error as error:
            raise DatabaseOperationError(
                "Não foi possível atualizar a categoria."
            ) from error

        if row is None:
            raise CategoryNotFoundError(
                f"Nenhuma categoria foi encontrada "
                f"com o ID {category_id}."
            )

        return self._from_row(row)

    def delete(
        self,
        category_id: int,
    ) -> None:
        """Remove uma categoria pelo identificador."""
        try:
            with self._database.connect() as connection:
                row = connection.execute(
                    """
                    DELETE FROM categories
                    WHERE id = %s
                    RETURNING id
                    """,
                    (category_id,),
                ).fetchone()

        except psycopg.Error as error:
            raise DatabaseOperationError(
                "Não foi possível remover a categoria."
            ) from error

        if row is None:
            raise CategoryNotFoundError(
                f"Nenhuma categoria foi encontrada "
                f"com o ID {category_id}."
            )

    @staticmethod
    def _from_row(
        row: dict[str, Any],
    ) -> Category:
        """Converte uma linha do banco em Category."""
        return Category(
            id=row["id"],
            name=row["name"],
            created_at=row["created_at"],
        )