import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from editalwatch.config import Settings
from editalwatch.database import Database
from editalwatch.models import SourceInput, SourceType
from editalwatch.repositories.source_repository import (
    SourceRepository,
)


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_INTEGRATION_TESTS") != "1",
    reason=(
        "Defina RUN_INTEGRATION_TESTS=1 para executar "
        "testes com PostgreSQL."
    ),
)


def test_source_repository_crud() -> None:
    settings = Settings.load()
    database = Database(settings.database_url)
    repository = SourceRepository(database)

    unique_name = f"Fonte de teste {uuid4()}"
    created_source_id: int | None = None

    try:
        created_source = repository.create(
            SourceInput(
                name=unique_name,
                base_url="https://example.com",
                source_type=SourceType.HTML,
                collection_allowed=True,
                policy_checked_at=datetime.now(
                    timezone.utc
                ),
            )
        )

        created_source_id = created_source.id

        found_source = repository.get_by_id(
            created_source.id
        )

        assert found_source == created_source

        updated_source = repository.update(
            created_source.id,
            SourceInput(
                name=f"{unique_name} atualizado",
                base_url="https://example.com",
                source_type=SourceType.HTML,
                collection_allowed=True,
                policy_checked_at=datetime.now(
                    timezone.utc
                ),
                is_active=False,
            ),
        )

        assert updated_source.is_active is False
        assert updated_source.name.endswith(
            "atualizado"
        )

        repository.delete(created_source.id)
        created_source_id = None

        assert (
            repository.get_by_id(created_source.id)
            is None
        )

    finally:
        if created_source_id is not None:
            repository.delete(created_source_id)