import os

import pytest

from editalwatch.database import Database
from editalwatch.exceptions import (
    CollectionRunStateError,
)
from editalwatch.models import (
    CollectionRunMetrics,
    CollectionRunStatus,
    Source,
)
from editalwatch.repositories.collection_run_repository import (
    CollectionRunRepository,
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


def test_collection_run_success_lifecycle(
    database: Database,
    temporary_source: Source,
) -> None:
    repository = CollectionRunRepository(database)

    started_run = repository.start(
        temporary_source.id
    )

    assert started_run.source_id == temporary_source.id
    assert started_run.status == CollectionRunStatus.RUNNING
    assert started_run.finished_at is None
    assert started_run.is_finished is False

    metrics = CollectionRunMetrics(
        records_found=10,
        records_inserted=6,
        records_updated=2,
        records_rejected=1,
    )

    finished_run = repository.complete_success(
        started_run.id,
        metrics,
    )

    assert finished_run.status == CollectionRunStatus.SUCCESS
    assert finished_run.is_finished is True
    assert finished_run.finished_at is not None
    assert finished_run.records_found == 10
    assert finished_run.records_inserted == 6
    assert finished_run.records_updated == 2
    assert finished_run.records_rejected == 1
    assert finished_run.error_message is None
    assert finished_run.duration_seconds is not None
    assert finished_run.duration_seconds >= 0

    with pytest.raises(CollectionRunStateError):
        repository.complete_success(
            started_run.id,
            metrics,
        )


def test_collection_run_records_failure(
    database: Database,
    temporary_source: Source,
) -> None:
    repository = CollectionRunRepository(database)

    started_run = repository.start(
        temporary_source.id
    )

    failed_run = repository.fail(
        run_id=started_run.id,
        error_message=(
            "A fonte não respondeu dentro do tempo limite."
        ),
        metrics=CollectionRunMetrics(
            records_found=2,
            records_rejected=2,
        ),
    )

    assert failed_run.status == CollectionRunStatus.FAILED
    assert failed_run.finished_at is not None
    assert failed_run.error_message is not None
    assert "tempo limite" in failed_run.error_message
    assert failed_run.records_found == 2
    assert failed_run.records_rejected == 2


def test_list_collection_runs_by_source(
    database: Database,
    temporary_source: Source,
) -> None:
    repository = CollectionRunRepository(database)

    first_run = repository.start(
        temporary_source.id
    )

    repository.complete_success(
        first_run.id,
        CollectionRunMetrics(
            records_found=3,
            records_inserted=3,
        ),
    )

    second_run = repository.start(
        temporary_source.id
    )

    repository.complete_partial(
        run_id=second_run.id,
        metrics=CollectionRunMetrics(
            records_found=5,
            records_inserted=3,
            records_rejected=1,
        ),
        error_message=(
            "Um registro permaneceu sem classificação."
        ),
    )

    runs = repository.list_by_source(
        temporary_source.id
    )

    assert len(runs) == 2

    assert {
        run.status
        for run in runs
    } == {
        CollectionRunStatus.SUCCESS,
        CollectionRunStatus.PARTIAL,
    }