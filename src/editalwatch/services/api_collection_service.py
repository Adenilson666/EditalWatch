from pathlib import Path
from typing import Protocol

from editalwatch.exceptions import (
    CollectionExecutionError,
)
from editalwatch.models import (
    CollectionOutcome,
    CollectionRunMetrics,
    ExtractionResult,
)
from editalwatch.repositories.collection_run_repository import (
    CollectionRunRepository,
)


class APIExtractor(Protocol):
    """Contrato de um extrator de API."""

    def fetch_all(self) -> ExtractionResult:
        """Extrai todos os registros disponíveis."""
        ...


class RawStorage(Protocol):
    """Contrato de armazenamento dos dados brutos."""

    def save(
        self,
        source_id: int,
        run_id: int,
        result: ExtractionResult,
    ) -> Path:
        """Salva o resultado bruto."""
        ...


class ApiCollectionService:
    """Coordena uma coleta completa por API."""

    def __init__(
        self,
        run_repository: CollectionRunRepository,
        extractor: APIExtractor,
        raw_storage: RawStorage,
    ) -> None:
        self._run_repository = run_repository
        self._extractor = extractor
        self._raw_storage = raw_storage

    def collect(
        self,
        source_id: int,
    ) -> CollectionOutcome:
        """Executa e registra uma coleta completa."""
        started_run = self._run_repository.start(
            source_id
        )

        try:
            extraction = self._extractor.fetch_all()

            raw_file = self._raw_storage.save(
                source_id=source_id,
                run_id=started_run.id,
                result=extraction,
            )

            metrics = CollectionRunMetrics(
                records_found=len(
                    extraction.records
                ),
            )

            completed_run = (
                self._run_repository.complete_success(
                    run_id=started_run.id,
                    metrics=metrics,
                )
            )

        except Exception as error:
            error_message = (
                f"{type(error).__name__}: {error}"
            )

            try:
                self._run_repository.fail(
                    run_id=started_run.id,
                    error_message=error_message,
                )

            except Exception as registration_error:
                raise CollectionExecutionError(
                    "A coleta falhou e também não foi "
                    "possível registrar a falha no banco."
                ) from registration_error

            raise CollectionExecutionError(
                f"A coleta {started_run.id} falhou: "
                f"{error}"
            ) from error

        return CollectionOutcome(
            run=completed_run,
            extraction=extraction,
            raw_file=raw_file,
        )