from collections.abc import Iterator
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from editalwatch.config import Settings
from editalwatch.database import Database
from editalwatch.models import (
    Source,
    SourceInput,
    SourceType,
)
from editalwatch.repositories.source_repository import (
    SourceRepository,
)


@pytest.fixture
def database() -> Database:
    """Cria o objeto de acesso ao banco de testes."""
    settings = Settings.load()

    return Database(settings.database_url)


@pytest.fixture
def temporary_source(
    database: Database,
) -> Iterator[Source]:
    """Cria e remove uma fonte temporária."""
    repository = SourceRepository(database)

    unique_value = uuid4().hex

    source = repository.create(
        SourceInput(
            name=f"Fonte temporária {unique_value}",
            base_url=(
                f"https://example.com/"
                f"sources/{unique_value}"
            ),
            source_type=SourceType.API,
            collection_allowed=True,
            policy_checked_at=datetime.now(
                timezone.utc
            ),
        )
    )

    try:
        yield source

    finally:
        with database.connect() as connection:
            connection.execute(
                """
                DELETE FROM collection_runs
                WHERE source_id = %s
                """,
                (source.id,),
            )

        existing_source = repository.get_by_id(
            source.id
        )

        if existing_source is not None:
            repository.delete(source.id)