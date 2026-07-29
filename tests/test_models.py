from datetime import datetime, timezone

import pytest

from editalwatch.models import (
    SourceInput,
    SourceType,
)


def test_source_input_normalizes_text() -> None:
    source = SourceInput(
        name="  Portal de Editais  ",
        base_url="  https://example.com  ",
        source_type=SourceType.HTML,
    )

    assert source.name == "Portal de Editais"
    assert source.base_url == "https://example.com"


def test_source_input_rejects_empty_name() -> None:
    with pytest.raises(
        ValueError,
        match="nome da fonte",
    ):
        SourceInput(
            name="   ",
            base_url="https://example.com",
            source_type=SourceType.HTML,
        )


def test_source_input_rejects_invalid_url() -> None:
    with pytest.raises(
        ValueError,
        match="http:// ou https://",
    ):
        SourceInput(
            name="Fonte inválida",
            base_url="example.com",
            source_type=SourceType.HTML,
        )


def test_allowed_source_requires_policy_date() -> None:
    with pytest.raises(
        ValueError,
        match="data de verificação",
    ):
        SourceInput(
            name="Fonte sem verificação",
            base_url="https://example.com",
            source_type=SourceType.API,
            collection_allowed=True,
        )


def test_allowed_source_accepts_policy_date() -> None:
    source = SourceInput(
        name="Fonte verificada",
        base_url="https://example.com",
        source_type=SourceType.API,
        collection_allowed=True,
        policy_checked_at=datetime.now(timezone.utc),
    )

    assert source.collection_allowed is True