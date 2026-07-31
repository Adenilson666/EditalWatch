import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from editalwatch.config import Settings
from editalwatch.exceptions import (
    DataTransformationError,
)
from editalwatch.models import (
    NoticeRecord,
    TransformationIssue,
)
from editalwatch.transformers.notice_transformer import (
    NoticeTransformer,
)


def find_latest_raw_file(
    raw_data_dir: Path,
) -> Path:
    """Localiza o arquivo bruto mais recente."""
    files = list(
        raw_data_dir.rglob(
            "run_*.json"
        )
    )

    if not files:
        raise FileNotFoundError(
            "Nenhum arquivo bruto foi encontrado. "
            "Execute primeiro editalwatch-api-demo."
        )

    return max(
        files,
        key=lambda file_path: (
            file_path.stat().st_mtime
        ),
    )


def load_raw_records(
    file_path: Path,
) -> list[dict[str, Any]]:
    """Carrega os registros de um arquivo bruto."""
    payload = json.loads(
        file_path.read_text(
            encoding="utf-8"
        )
    )

    records = payload.get(
        "records"
    )

    if not isinstance(records, list):
        raise DataTransformationError(
            "O arquivo bruto não possui uma "
            "lista válida em 'records'."
        )

    if any(
        not isinstance(record, dict)
        for record in records
    ):
        raise DataTransformationError(
            "O arquivo bruto possui registros inválidos."
        )

    return records


def valid_record_to_dict(
    record: NoticeRecord,
) -> dict[str, Any]:
    """Converte um edital válido em linha de relatório."""
    return {
        "external_id": record.external_id,
        "title": record.title,
        "organization": record.organization,
        "notice_number": record.notice_number,
        "publication_date": (
            record.publication_date.isoformat()
            if record.publication_date
            else None
        ),
        "registration_deadline": (
            record.registration_deadline.isoformat()
            if record.registration_deadline
            else None
        ),
        "url": record.url,
        "status": record.status.value,
        "content_hash": record.content_hash,
        "raw_payload": json.dumps(
            record.raw_payload,
            ensure_ascii=False,
            sort_keys=True,
        ),
    }


def issue_to_dict(
    issue: TransformationIssue,
) -> dict[str, Any]:
    """Converte uma rejeição em linha de relatório."""
    return {
        "row_number": issue.row_number,
        "external_id": issue.external_id,
        "reasons": " | ".join(
            issue.reasons
        ),
        "raw_payload": json.dumps(
            issue.raw_payload,
            ensure_ascii=False,
            sort_keys=True,
        ),
    }


def main() -> None:
    """Transforma o arquivo bruto mais recente."""
    settings = Settings.load()

    try:
        raw_file = find_latest_raw_file(
            settings.raw_data_dir
        )

        records = load_raw_records(
            raw_file
        )

        transformer = NoticeTransformer()

        result = transformer.transform(
            records
        )

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        DataTransformationError,
        OSError,
    ) as error:
        print(
            f"Falha na transformação: {error}"
        )
        return

    settings.export_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    generated_at = datetime.now(
        timezone.utc
    ).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    valid_file = (
        settings.export_dir
        / (
            "transformed_notices_"
            f"{generated_at}.csv"
        )
    )

    rejected_file = (
        settings.export_dir
        / (
            "rejected_notices_"
            f"{generated_at}.csv"
        )
    )

    valid_rows = [
        valid_record_to_dict(record)
        for record in result.valid_records
    ]

    rejected_rows = [
        issue_to_dict(issue)
        for issue in result.rejected_records
    ]

    valid_columns = [
        "external_id",
        "title",
        "organization",
        "notice_number",
        "publication_date",
        "registration_deadline",
        "url",
        "status",
        "content_hash",
        "raw_payload",
    ]

    rejected_columns = [
        "row_number",
        "external_id",
        "reasons",
        "raw_payload",
    ]

    valid_frame = pd.DataFrame(
        valid_rows,
        columns=valid_columns,
    )

    rejected_frame = pd.DataFrame(
        rejected_rows,
        columns=rejected_columns,
    )

    valid_frame.to_csv(
        valid_file,
        index=False,
        encoding="utf-8-sig",
    )

    rejected_frame.to_csv(
        rejected_file,
        index=False,
        encoding="utf-8-sig",
    )

    print("Transformação concluída.")
    print(f"Arquivo bruto: {raw_file}")
    print(
        f"Registros recebidos: "
        f"{result.input_count}"
    )
    print(
        f"Registros válidos: "
        f"{result.valid_count}"
    )
    print(
        f"Registros rejeitados: "
        f"{result.rejected_count}"
    )
    print(
        f"Duplicados detectados: "
        f"{result.duplicate_count}"
    )
    print(
        f"Arquivo de válidos: "
        f"{valid_file}"
    )
    print(
        f"Arquivo de rejeitados: "
        f"{rejected_file}"
    )

    if not valid_frame.empty:
        print("\nPrévia dos registros válidos:")

        print(
            valid_frame[
                [
                    "external_id",
                    "title",
                    "publication_date",
                    "status",
                ]
            ].to_string(
                index=False
            )
        )


if __name__ == "__main__":
    main()