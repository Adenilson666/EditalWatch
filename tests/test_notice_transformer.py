from datetime import date

from editalwatch.models import (
    NoticeStatus,
)
from editalwatch.transformers.notice_transformer import (
    NoticeTransformer,
)


def test_transform_normalizes_valid_record() -> None:
    transformer = NoticeTransformer()

    result = transformer.transform(
        [
            {
                "external_id": "  LOCAL-001  ",
                "title": (
                    "  Concurso   para "
                    "Analista de TI  "
                ),
                "organization": (
                    " Instituição Federal "
                ),
                "notice_number": " 01/2026 ",
                "publication_date": "2026-07-20",
                "registration_deadline": "2026-08-15",
                "url": (
                    "https://EXAMPLE.COM/"
                    "notices/1/#documento"
                ),
                "status": " OPEN ",
            }
        ]
    )

    assert result.input_count == 1
    assert result.valid_count == 1
    assert result.rejected_count == 0

    notice = result.valid_records[0]

    assert notice.external_id == "LOCAL-001"

    assert notice.title == (
        "Concurso para Analista de TI"
    )

    assert notice.organization == (
        "Instituição Federal"
    )

    assert notice.notice_number == "01/2026"

    assert notice.publication_date == date(
        2026,
        7,
        20,
    )

    assert notice.registration_deadline == date(
        2026,
        8,
        15,
    )

    assert notice.url == (
        "https://example.com/notices/1"
    )

    assert notice.status == NoticeStatus.OPEN
    assert len(notice.content_hash) == 64


def test_transform_rejects_invalid_records() -> None:
    transformer = NoticeTransformer()

    result = transformer.transform(
        [
            {
                "external_id": "INVALID-001",
                "title": "   ",
                "url": "https://example.com/1",
            },
            {
                "external_id": "INVALID-002",
                "title": "Edital com URL inválida",
                "url": "example.com/2",
            },
            {
                "external_id": "INVALID-003",
                "title": "Edital com data inválida",
                "publication_date": "2026-02-31",
                "url": "https://example.com/3",
            },
            {
                "external_id": "INVALID-004",
                "title": "Edital com prazo inválido",
                "publication_date": "2026-07-20",
                "registration_deadline": "2026-07-10",
                "url": "https://example.com/4",
            },
            {
                "external_id": "INVALID-005",
                "title": "Edital com status inválido",
                "url": "https://example.com/5",
                "status": "pending",
            },
        ]
    )

    assert result.valid_count == 0
    assert result.rejected_count == 5

    all_reasons = {
        reason
        for issue in result.rejected_records
        for reason in issue.reasons
    }

    assert (
        "Título ausente ou inválido."
        in all_reasons
    )

    assert (
        "URL ausente ou inválida."
        in all_reasons
    )

    assert (
        "Data de publicação inválida."
        in all_reasons
    )

    assert (
        "O prazo de inscrição não pode ser "
        "anterior à data de publicação."
        in all_reasons
    )

    assert "Status inválido." in all_reasons


def test_transform_detects_duplicates() -> None:
    transformer = NoticeTransformer()

    result = transformer.transform(
        [
            {
                "external_id": "DUP-001",
                "title": "Primeiro edital",
                "url": "https://example.com/1",
            },
            {
                "external_id": "DUP-001",
                "title": "Mesmo ID externo",
                "url": "https://example.com/2",
            },
            {
                "external_id": "DUP-002",
                "title": "Mesma URL",
                "url": "https://example.com/1",
            },
        ]
    )

    assert result.valid_count == 1
    assert result.rejected_count == 2
    assert result.duplicate_count == 2

    assert all(
        (
            "Registro duplicado dentro do lote."
            in issue.reasons
        )
        for issue in result.rejected_records
    )


def test_content_hash_is_stable_after_normalization() -> None:
    transformer = NoticeTransformer()

    first_result = transformer.transform(
        [
            {
                "external_id": "HASH-001",
                "title": "Edital para Analista de TI",
                "organization": "Instituição Federal",
                "publication_date": "2026-07-20",
                "url": "https://example.com/notices/1",
                "status": "open",
            }
        ]
    )

    second_result = transformer.transform(
        [
            {
                "external_id": " HASH-001 ",
                "title": (
                    " Edital   para Analista de TI "
                ),
                "organization": (
                    " Instituição Federal "
                ),
                "publication_date": "2026-07-20",
                "url": (
                    "https://EXAMPLE.COM/"
                    "notices/1/#documento"
                ),
                "status": " OPEN ",
            }
        ]
    )

    first_hash = (
        first_result
        .valid_records[0]
        .content_hash
    )

    second_hash = (
        second_result
        .valid_records[0]
        .content_hash
    )

    assert first_hash == second_hash


def test_transform_accepts_empty_collection() -> None:
    transformer = NoticeTransformer()

    result = transformer.transform([])

    assert result.input_count == 0
    assert result.valid_count == 0
    assert result.rejected_count == 0
    assert result.duplicate_count == 0


def test_transform_users_uknown_for_missing_status() -> None:
    transformer = NoticeTransformer()

    result = transformer.transform(
        [
            {
                "external_id": "STATUS-001",
                "title": "Edital sem status",
                "url": "https://example.com/notices/1",
            }
        ]
    )

    assert result.valid_count == 1
    assert result.rejected_count == 0

    notice = result.valid_records[0]

    assert notice.status == NoticeStatus.UNKNOWN