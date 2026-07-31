import hashlib
import json
import unicodedata
from collections.abc import Sequence
from datetime import date
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import pandas as pd

from editalwatch.exceptions import (
    DataTransformationError,
)
from editalwatch.models import (
    NoticeRecord,
    NoticeStatus,
    NoticeTransformationResult,
    TransformationIssue,
)


EXPECTED_COLUMNS = (
    "external_id",
    "title",
    "organization",
    "notice_number",
    "publication_date",
    "registration_deadline",
    "url",
    "status",
)


ALLOWED_STATUSES = {
    status.value
    for status in NoticeStatus
}


class NoticeTransformer:
    """Limpa e valida registros brutos de editais."""

    def transform(
        self,
        records: Sequence[dict[str, Any]],
    ) -> NoticeTransformationResult:
        """Transforma registros brutos em editais validados."""
        raw_records = list(records)

        if not raw_records:
            return NoticeTransformationResult(
                valid_records=(),
                rejected_records=(),
                input_count=0,
                duplicate_count=0,
            )

        if any(
            not isinstance(record, dict)
            for record in raw_records
        ):
            raise DataTransformationError(
                "Todos os registros devem ser objetos JSON."
            )

        frame = pd.json_normalize(
            raw_records,
            sep="_",
        )

        for column_name in EXPECTED_COLUMNS:
            if column_name not in frame.columns:
                frame[column_name] = pd.NA

        frame["_row_number"] = range(
            1,
            len(frame) + 1,
        )

        original_status = frame["status"].copy()
        original_publication_date = (
            frame["publication_date"].copy()
        )
        original_deadline = (
            frame["registration_deadline"].copy()
        )

        frame["external_id"] = frame[
            "external_id"
        ].map(
            lambda value: self._normalize_optional_text(
                value,
                allow_numeric=True,
            )
        )

        text_columns = (
            "title",
            "organization",
            "notice_number",
        )

        for column_name in text_columns:
            frame[column_name] = frame[
                column_name
            ].map(
                self._normalize_optional_text
            )

        normalized_status = original_status.map(
            self._normalize_status
        )

        status_was_provided = original_status.map(
            self._has_value
        )

        invalid_status = (
            status_was_provided
            & ~normalized_status.isin(
                ALLOWED_STATUSES
            )
        )

        frame["status"] = normalized_status.fillna(
            NoticeStatus.UNKNOWN.value
        )

        frame["url"] = frame["url"].map(
            self._canonicalize_url
        )

        publication_text = (
            original_publication_date.map(
                self._normalize_optional_text
            )
        )

        deadline_text = original_deadline.map(
            self._normalize_optional_text
        )

        publication_dates = pd.to_datetime(
            publication_text,
            format="%Y-%m-%d",
            errors="coerce",
        )

        registration_deadlines = pd.to_datetime(
            deadline_text,
            format="%Y-%m-%d",
            errors="coerce",
        )

        publication_was_provided = (
            original_publication_date.map(
                self._has_value
            )
        )

        deadline_was_provided = (
            original_deadline.map(
                self._has_value
            )
        )

        invalid_publication_date = (
            publication_was_provided
            & publication_dates.isna()
        )

        invalid_deadline = (
            deadline_was_provided
            & registration_deadlines.isna()
        )

        deadline_before_publication = (
            publication_dates.notna()
            & registration_deadlines.notna()
            & (
                registration_deadlines
                < publication_dates
            )
        )

        normalized_external_ids = frame[
            "external_id"
        ].map(
           self._normalize_casefold_text
        )

        duplicated_external_id = (
            normalized_external_ids.notna()
            & normalized_external_ids.duplicated(
                keep="first"
            )
        )

        duplicated_url = (
            frame["url"].notna()
            & frame["url"].duplicated(
                keep="first"
            )
        )

        duplicated_record = (
            duplicated_external_id
            | duplicated_url
        )

        reasons_by_index: dict[
            int,
            list[str],
        ] = {
            index: []
            for index in frame.index
        }

        self._add_reason(
            reasons_by_index,
            frame["title"].isna(),
            "Título ausente ou inválido.",
        )

        self._add_reason(
            reasons_by_index,
            frame["url"].isna(),
            "URL ausente ou inválida.",
        )

        self._add_reason(
            reasons_by_index,
            invalid_status,
            "Status inválido.",
        )

        self._add_reason(
            reasons_by_index,
            invalid_publication_date,
            "Data de publicação inválida.",
        )

        self._add_reason(
            reasons_by_index,
            invalid_deadline,
            "Prazo de inscrição inválido.",
        )

        self._add_reason(
            reasons_by_index,
            deadline_before_publication,
            (
                "O prazo de inscrição não pode ser "
                "anterior à data de publicação."
            ),
        )

        self._add_reason(
            reasons_by_index,
            duplicated_record,
            "Registro duplicado dentro do lote.",
        )

        valid_records: list[NoticeRecord] = []
        rejected_records: list[
            TransformationIssue
        ] = []

        for index, row in frame.iterrows():
            row_number = int(
                row["_row_number"]
            )

            raw_payload = dict(
                raw_records[
                    row_number - 1
                ]
            )

            reasons = reasons_by_index[
                index
            ]

            if reasons:
                rejected_records.append(
                    TransformationIssue(
                        row_number=row_number,
                        external_id=row[
                            "external_id"
                        ],
                        reasons=tuple(reasons),
                        raw_payload=raw_payload,
                    )
                )

                continue

            publication_date = (
                self._timestamp_to_date(
                    publication_dates.loc[
                        index
                    ]
                )
            )

            registration_deadline = (
                self._timestamp_to_date(
                    registration_deadlines.loc[
                        index
                    ]
                )
            )

            status = NoticeStatus(
                row["status"]
            )

            content_hash = (
                self._generate_content_hash(
                    external_id=row[
                        "external_id"
                    ],
                    title=row["title"],
                    organization=row[
                        "organization"
                    ],
                    notice_number=row[
                        "notice_number"
                    ],
                    publication_date=(
                        publication_date
                    ),
                    registration_deadline=(
                        registration_deadline
                    ),
                    url=row["url"],
                    status=status,
                )
            )

            valid_records.append(
                NoticeRecord(
                    external_id=row[
                        "external_id"
                    ],
                    title=row["title"],
                    organization=row[
                        "organization"
                    ],
                    notice_number=row[
                        "notice_number"
                    ],
                    publication_date=(
                        publication_date
                    ),
                    registration_deadline=(
                        registration_deadline
                    ),
                    url=row["url"],
                    status=status,
                    content_hash=content_hash,
                    raw_payload=raw_payload,
                )
            )

        return NoticeTransformationResult(
            valid_records=tuple(
                valid_records
            ),
            rejected_records=tuple(
                rejected_records
            ),
            input_count=len(raw_records),
            duplicate_count=int(
                duplicated_record.sum()
            ),
        )

    @staticmethod
    def _normalize_status(
        value: Any,
    ) -> str | None:
        """""Normaliza um status e preserva valores ausentes"""
        normalized_value = (
            NoticeTransformer
            ._normalize_optional_text(
                value
            )
        )

        if normalized_value is None:
            return None

        return normalized_value.casefold()

    @staticmethod
    def _normalize_casefold_text(
        value: Any,
    ) -> str | None:
        """Normaliza espaços e caracteres Unicode e aplica casefold."""
        normalized_value = (
            NoticeTransformer
            ._normalize_optional_text(
                value,
                allow_numeric=True,
            )
        )

        if normalized_value is None:
            return None

        return normalized_value.casefold()

    @staticmethod
    def _normalize_optional_text(
        value: Any,
        allow_numeric: bool = False,
    ) -> str | None:
        """Normaliza espaços e caracteres Unicode."""
        if not NoticeTransformer._has_value(
            value
        ):
            return None

        if not isinstance(value, str):
            if (
                allow_numeric
                and isinstance(
                    value,
                    (int, float),
                )
                and not isinstance(
                    value,
                    bool,
                )
            ):
                value = str(value)

            else:
                return None

        normalized_value = unicodedata.normalize(
            "NFKC",
            value,
        )

        normalized_value = " ".join(
            normalized_value.split()
        )

        if not normalized_value:
            return None

        return normalized_value

    @staticmethod
    def _has_value(
        value: Any,
    ) -> bool:
        """Verifica se o valor não representa ausência."""
        if value is None or value is pd.NA:
            return False

        try:
            missing_result = pd.isna(
                value
            )

            
            return not bool(missing_result)

        except (
            TypeError,
            ValueError,
        ):
            

            return True

    @staticmethod
    def _canonicalize_url(
        value: Any,
    ) -> str | None:
        """Valida e normaliza uma URL HTTP ou HTTPS."""
        normalized_value = (
            NoticeTransformer
            ._normalize_optional_text(
                value
            )
        )

        if normalized_value is None:
            return None

        try:
            parsed_url = urlsplit(
                normalized_value
            )

        except ValueError:
            return None

        if parsed_url.scheme.casefold() not in {
            "http",
            "https",
        }:
            return None

        if not parsed_url.netloc:
            return None

        if parsed_url.hostname is None:
            return None

        normalized_path = (
            parsed_url.path
            or "/"
        )

        if normalized_path != "/":
            normalized_path = (
                normalized_path.rstrip("/")
            )

        return urlunsplit(
            (
                parsed_url.scheme.casefold(),
                parsed_url.netloc.casefold(),
                normalized_path,
                parsed_url.query,
                "",
            )
        )

    @staticmethod
    def _timestamp_to_date(
        value: pd.Timestamp,
    ) -> date | None:
        """Converte um Timestamp do Pandas em date."""
        if pd.isna(value):
            return None

        return value.date()

    @staticmethod
    def _generate_content_hash(
        external_id: str | None,
        title: str,
        organization: str | None,
        notice_number: str | None,
        publication_date: date | None,
        registration_deadline: date | None,
        url: str,
        status: NoticeStatus,
    ) -> str:
        """Gera uma assinatura SHA-256 do edital."""
        hash_payload = {
            "external_id": (
                external_id
                or ""
            ),
            "title": title,
            "organization": (
                organization
                or ""
            ),
            "notice_number": (
                notice_number
                or ""
            ),
            "publication_date": (
                publication_date.isoformat()
                if publication_date
                else ""
            ),
            "registration_deadline": (
                registration_deadline.isoformat()
                if registration_deadline
                else ""
            ),
            "url": url,
            "status": status.value,
        }

        serialized_payload = json.dumps(
            hash_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            serialized_payload.encode(
                "utf-8"
            )
        ).hexdigest()

    @staticmethod
    def _add_reason(
        reasons_by_index: dict[
            int,
            list[str],
        ],
        mask: pd.Series,
        reason: str,
    ) -> None:
        """Adiciona uma justificativa às linhas indicadas."""
        for index in mask[
            mask
        ].index:
            reasons_by_index[
                index
            ].append(reason)