import json

from editalwatch.models import (
    ExtractionResult,
)
from editalwatch.storage.raw_json_storage import (
    RawJsonStorage,
)


def test_raw_storage_creates_json_file(
    tmp_path,
) -> None:
    storage = RawJsonStorage(
        tmp_path
    )

    result = ExtractionResult(
        records=(
            {
                "id": 1,
                "title": "Edital de teste",
            },
        ),
        pages_fetched=1,
        total_items=1,
    )

    file_path = storage.save(
        source_id=10,
        run_id=20,
        result=result,
    )

    assert file_path.exists()

    payload = json.loads(
        file_path.read_text(
            encoding="utf-8"
        )
    )

    assert payload["source_id"] == 10
    assert payload["collection_run_id"] == 20
    assert payload["pages_fetched"] == 1
    assert payload["record_count"] == 1

    assert payload["records"][0]["title"] == (
        "Edital de teste"
    )