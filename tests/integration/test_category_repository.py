import os
from uuid import uuid4

import pytest

from editalwatch.database import Database
from editalwatch.models import CategoryInput
from editalwatch.repositories.category_repository import (
    CategoryRepository,
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


def test_category_repository_crud(
    database: Database,
) -> None:
    repository = CategoryRepository(database)

    unique_value = uuid4().hex
    category_id: int | None = None

    try:
        created_category = repository.create(
            CategoryInput(
                name=f"Categoria {unique_value}"
            )
        )

        category_id = created_category.id

        found_category = repository.get_by_id(
            created_category.id
        )

        assert found_category == created_category

        updated_category = repository.update(
            created_category.id,
            CategoryInput(
                name=(
                    f"Categoria atualizada "
                    f"{unique_value}"
                )
            ),
        )

        assert updated_category.id == created_category.id
        assert updated_category.name.startswith(
            "Categoria atualizada"
        )

        categories = repository.list_all()

        assert any(
            category.id == created_category.id
            for category in categories
        )

        repository.delete(created_category.id)
        category_id = None

        assert (
            repository.get_by_id(created_category.id)
            is None
        )

    finally:
        if category_id is not None:
            existing_category = repository.get_by_id(
                category_id
            )

            if existing_category is not None:
                repository.delete(category_id)


def test_category_get_or_create_avoids_duplicate(
    database: Database,
) -> None:
    repository = CategoryRepository(database)

    unique_name = f"Categoria única {uuid4().hex}"
    category_id: int | None = None

    try:
        first_result = repository.get_or_create(
            CategoryInput(name=unique_name)
        )

        category_id = first_result.id

        second_result = repository.get_or_create(
            CategoryInput(name=unique_name)
        )

        assert second_result.id == first_result.id
        assert second_result.name == first_result.name

    finally:
        if category_id is not None:
            existing_category = repository.get_by_id(
                category_id
            )

            if existing_category is not None:
                repository.delete(category_id)