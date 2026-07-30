import os

import pytest

from editalwatch.database import Database
from editalwatch.exceptions import (
    CollectionExecutionError,
    DataExtractionError,
)
from editalwatch.models import (
    CollectionRunStatus,
    ExtractionResult,
    Source,
)
from editalwatch.repositories.collection_run_repository import (
    CollectionRunRepository,
)
from editalwatch.services.api_collection_service import (
    ApiCollectionService,
)
from editalwatch.storage.raw_json_storage import (
    RawJsonStorage,
)


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION_TESTS") != "1",
        reason=(
            "Defina RUN_INTEGRATION_TESTS=1 para "
            "executar testes com PostgreSQL."
        ),
    ),
]


class SuccessfulExtractor:
    """Simula uma extração bem-sucedida."""

    def fetch_all(self) -> ExtractionResult:
        return ExtractionResult(
            records=(
                {
                    "external_id": "TEST-001",
                    "title": "Edital de teste",
                },
                {
                    "external_id": "TEST-002",
                    "title": "Outro edital",
                },
            ),
            pages_fetched=1,
            total_items=2,
        )


class FailingExtractor:
    """Simula uma falha de rede."""

    def fetch_all(self) -> ExtractionResult:
        raise DataExtractionError(
            "A API de teste está indisponível."
        )


def test_api_collection_records_success(
    database: Database,
    temporary_source: Source,
    tmp_path,
) -> None:
    run_repository = CollectionRunRepository(
        database
    )

    service = ApiCollectionService(
        run_repository=run_repository,
        extractor=SuccessfulExtractor(),
        raw_storage=RawJsonStorage(
            tmp_path
        ),
    )

    outcome = service.collect(
        temporary_source.id
    )

    assert (
        outcome.run.status
        == CollectionRunStatus.SUCCESS
    )

    assert outcome.run.records_found == 2
    assert outcome.run.records_inserted == 0
    assert outcome.raw_file.exists()


def test_api_collection_records_failure(
    database: Database,
    temporary_source: Source,
    tmp_path,
) -> None:
    run_repository = CollectionRunRepository(
        database
    )

    service = ApiCollectionService(
        run_repository=run_repository,
        extractor=FailingExtractor(),
        raw_storage=RawJsonStorage(
            tmp_path
        ),
    )

    with pytest.raises(
        CollectionExecutionError,
    ):
        service.collect(
            temporary_source.id
        )

    runs = run_repository.list_by_source(
        temporary_source.id
    )

    assert len(runs) == 1

    assert (
        runs[0].status
        == CollectionRunStatus.FAILED
    )

    assert runs[0].error_message is not None
    assert "indisponível" in runs[0].error_message