from datetime import datetime, timezone

from editalwatch.config import Settings
from editalwatch.database import Database
from editalwatch.exceptions import (
    CollectionExecutionError,
)
from editalwatch.extractors.paginated_api import (
    PaginatedAPIExtractor,
)
from editalwatch.models import (
    Source,
    SourceInput,
    SourceType,
)
from editalwatch.repositories.collection_run_repository import (
    CollectionRunRepository,
)
from editalwatch.repositories.source_repository import (
    SourceRepository,
)
from editalwatch.services.api_collection_service import (
    ApiCollectionService,
)
from editalwatch.storage.raw_json_storage import (
    RawJsonStorage,
)


DEMO_SOURCE_NAME = "API local de demonstração"


def find_or_create_demo_source(
    repository: SourceRepository,
) -> Source:
    """Obtém ou cadastra a fonte local."""
    for source in repository.list_all():
        if source.name == DEMO_SOURCE_NAME:
            return source

    return repository.create(
        SourceInput(
            name=DEMO_SOURCE_NAME,
            base_url="http://127.0.0.1:8000",
            source_type=SourceType.API,
            collection_allowed=True,
            policy_checked_at=datetime.now(
                timezone.utc
            ),
        )
    )


def main() -> None:
    """Executa uma coleta na API local."""
    settings = Settings.load()

    database = Database(
        settings.database_url
    )

    source_repository = SourceRepository(
        database
    )

    run_repository = CollectionRunRepository(
        database
    )

    source = find_or_create_demo_source(
        source_repository
    )

    extractor = PaginatedAPIExtractor(
        base_url=source.base_url,
        endpoint="/notices",
        timeout=settings.http_timeout,
        max_retries=settings.http_max_retries,
        user_agent=settings.user_agent,
        page_size=2,
    )

    raw_storage = RawJsonStorage(
        settings.raw_data_dir
    )

    service = ApiCollectionService(
        run_repository=run_repository,
        extractor=extractor,
        raw_storage=raw_storage,
    )

    try:
        outcome = service.collect(
            source.id
        )

    except CollectionExecutionError as error:
        print(f"Falha na coleta: {error}")
        return

    print("Coleta concluída com sucesso.")
    print(f"Execução: {outcome.run.id}")
    print(
        f"Páginas: "
        f"{outcome.extraction.pages_fetched}"
    )
    print(
        f"Registros encontrados: "
        f"{outcome.extraction.total_items}"
    )
    print(
        f"Arquivo bruto: "
        f"{outcome.raw_file}"
    )


if __name__ == "__main__":
    main()