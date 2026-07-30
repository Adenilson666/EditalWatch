from typing import Any

import psycopg
from psycopg.errors import ForeignKeyViolation

from editalwatch.database import Database
from editalwatch.exceptions import (
    CollectionRunNotFoundError,
    CollectionRunStateError,
    DatabaseOperationError,
    SourceNotFoundError,
)
from editalwatch.models import (
    CollectionRun,
    CollectionRunMetrics,
    CollectionRunStatus,
)


class CollectionRunRepository:
    """Executa operações da tabela collection_runs."""

    def __init__(self, database: Database) -> None:
        self._database = database

    def start(
        self,
        source_id: int,
    ) -> CollectionRun:
        """Inicia uma nova execução de coleta."""
        try:
            with self._database.connect() as connection:
                row = connection.execute(
                    """
                    INSERT INTO collection_runs (
                        source_id
                    )
                    VALUES (
                        %s
                    )
                    RETURNING
                        id,
                        source_id,
                        started_at,
                        finished_at,
                        status,
                        records_found,
                        records_inserted,
                        records_updated,
                        records_rejected,
                        error_message
                    """,
                    (source_id,),
                ).fetchone()

        except ForeignKeyViolation as error:
            raise SourceNotFoundError(
                f"Nenhuma fonte foi encontrada "
                f"com o ID {source_id}."
            ) from error

        except psycopg.Error as error:
            raise DatabaseOperationError(
                "Não foi possível iniciar a coleta."
            ) from error

        if row is None:
            raise DatabaseOperationError(
                "O PostgreSQL não retornou a execução "
                "iniciada."
            )

        return self._from_row(row)

    def get_by_id(
        self,
        run_id: int,
    ) -> CollectionRun | None:
        """Consulta uma execução pelo identificador."""
        try:
            with self._database.connect() as connection:
                row = connection.execute(
                    """
                    SELECT
                        id,
                        source_id,
                        started_at,
                        finished_at,
                        status,
                        records_found,
                        records_inserted,
                        records_updated,
                        records_rejected,
                        error_message
                    FROM collection_runs
                    WHERE id = %s
                    """,
                    (run_id,),
                ).fetchone()

        except psycopg.Error as error:
            raise DatabaseOperationError(
                "Não foi possível consultar a execução."
            ) from error

        if row is None:
            return None

        return self._from_row(row)

    def list_by_source(
        self,
        source_id: int,
        limit: int = 50,
    ) -> list[CollectionRun]:
        """Lista as execuções mais recentes de uma fonte."""
        if limit <= 0:
            raise ValueError(
                "O limite deve ser maior que zero."
            )

        if limit > 500:
            raise ValueError(
                "O limite máximo permitido é 500."
            )

        try:
            with self._database.connect() as connection:
                rows = connection.execute(
                    """
                    SELECT
                        id,
                        source_id,
                        started_at,
                        finished_at,
                        status,
                        records_found,
                        records_inserted,
                        records_updated,
                        records_rejected,
                        error_message
                    FROM collection_runs
                    WHERE source_id = %s
                    ORDER BY started_at DESC
                    LIMIT %s
                    """,
                    (
                        source_id,
                        limit,
                    ),
                ).fetchall()

        except psycopg.Error as error:
            raise DatabaseOperationError(
                "Não foi possível listar as execuções."
            ) from error

        return [
            self._from_row(row)
            for row in rows
        ]

    def complete_success(
        self,
        run_id: int,
        metrics: CollectionRunMetrics,
    ) -> CollectionRun:
        """Finaliza uma execução bem-sucedida."""
        return self._finish(
            run_id=run_id,
            status=CollectionRunStatus.SUCCESS,
            metrics=metrics,
            error_message=None,
        )

    def complete_partial(
        self,
        run_id: int,
        metrics: CollectionRunMetrics,
        error_message: str,
    ) -> CollectionRun:
        """Finaliza uma execução parcialmente concluída."""
        normalized_message = error_message.strip()

        if not normalized_message:
            raise ValueError(
                "Uma execução parcial deve possuir "
                "uma mensagem explicativa."
            )

        return self._finish(
            run_id=run_id,
            status=CollectionRunStatus.PARTIAL,
            metrics=metrics,
            error_message=normalized_message,
        )

    def fail(
        self,
        run_id: int,
        error_message: str,
        metrics: CollectionRunMetrics | None = None,
    ) -> CollectionRun:
        """Registra a falha de uma execução."""
        normalized_message = error_message.strip()

        if not normalized_message:
            raise ValueError(
                "Uma execução com falha deve possuir "
                "uma mensagem de erro."
            )

        selected_metrics = (
            metrics
            if metrics is not None
            else CollectionRunMetrics()
        )

        return self._finish(
            run_id=run_id,
            status=CollectionRunStatus.FAILED,
            metrics=selected_metrics,
            error_message=normalized_message,
        )

    def _finish(
        self,
        run_id: int,
        status: CollectionRunStatus,
        metrics: CollectionRunMetrics,
        error_message: str | None,
    ) -> CollectionRun:
        """Finaliza uma execução que esteja em andamento."""
        try:
            with self._database.connect() as connection:
                row = connection.execute(
                    """
                    UPDATE collection_runs
                    SET
                        finished_at = CURRENT_TIMESTAMP,
                        status = %s,
                        records_found = %s,
                        records_inserted = %s,
                        records_updated = %s,
                        records_rejected = %s,
                        error_message = %s
                    WHERE id = %s
                      AND status = 'running'
                    RETURNING
                        id,
                        source_id,
                        started_at,
                        finished_at,
                        status,
                        records_found,
                        records_inserted,
                        records_updated,
                        records_rejected,
                        error_message
                    """,
                    (
                        status.value,
                        metrics.records_found,
                        metrics.records_inserted,
                        metrics.records_updated,
                        metrics.records_rejected,
                        error_message,
                        run_id,
                    ),
                ).fetchone()

        except psycopg.Error as error:
            raise DatabaseOperationError(
                "Não foi possível finalizar a execução."
            ) from error

        if row is not None:
            return self._from_row(row)

        existing_run = self.get_by_id(run_id)

        if existing_run is None:
            raise CollectionRunNotFoundError(
                f"Nenhuma execução foi encontrada "
                f"com o ID {run_id}."
            )

        raise CollectionRunStateError(
            f"A execução {run_id} já foi finalizada "
            f"com o status '{existing_run.status.value}'."
        )

    @staticmethod
    def _from_row(
        row: dict[str, Any],
    ) -> CollectionRun:
        """Converte uma linha do banco em CollectionRun."""
        return CollectionRun(
            id=row["id"],
            source_id=row["source_id"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            status=CollectionRunStatus(row["status"]),
            records_found=row["records_found"],
            records_inserted=row["records_inserted"],
            records_updated=row["records_updated"],
            records_rejected=row["records_rejected"],
            error_message=row["error_message"],
        )