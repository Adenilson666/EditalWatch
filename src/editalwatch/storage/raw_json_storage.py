import json
from datetime import datetime, timezone
from pathlib import Path

from editalwatch.exceptions import RawDataStorageError
from editalwatch.models import ExtractionResult


class RawJsonStorage:
    """Armazena resultados brutos em arquivos JSON."""

    def __init__(
        self,
        root_directory: Path,
    ) -> None:
        self._root_directory = root_directory

    def save(
        self,
        source_id: int,
        run_id: int,
        result: ExtractionResult,
    ) -> Path:
        """Salva uma extração e retorna o caminho criado."""
        saved_at = datetime.now(timezone.utc)

        source_directory = (
            self._root_directory
            / f"source_{source_id}"
        )

        file_name = (
            f"run_{run_id}_"
            f"{saved_at.strftime('%Y%m%dT%H%M%SZ')}.json"
        )

        target_path = source_directory / file_name
        temporary_path = target_path.with_suffix(".tmp")

        payload = {
            "source_id": source_id,
            "collection_run_id": run_id,
            "saved_at": saved_at.isoformat(),
            "pages_fetched": result.pages_fetched,
            "record_count": len(result.records),
            "records": result.records,
        }

        try:
            source_directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            serialized_content = json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            )

            temporary_path.write_text(
                serialized_content,
                encoding="utf-8",
            )

            temporary_path.replace(target_path)

        except (OSError, TypeError, ValueError) as error:
            if temporary_path.exists():
                temporary_path.unlink(
                    missing_ok=True
                )

            raise RawDataStorageError(
                "Não foi possível salvar os dados brutos."
            ) from error

        return target_path