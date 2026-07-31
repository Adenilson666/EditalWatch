from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class SourceType(StrEnum):
    """Representa os tipos permitidos de fonte."""

    API = "api"
    HTML = "html"
    BROWSER = "browser"
    FILE = "file"


@dataclass(frozen=True, slots=True)
class SourceInput:
    """Representa os dados necessários para cadastrar uma fonte."""

    name: str
    base_url: str
    source_type: SourceType
    terms_url: str | None = None
    robots_url: str | None = None
    collection_allowed: bool = False
    policy_checked_at: datetime | None = None
    is_active: bool = True

    def __post_init__(self) -> None:
        """Normaliza e valida os dados recebidos."""
        normalized_name = self.name.strip()
        normalized_base_url = self.base_url.strip()

        object.__setattr__(
            self,
            "name",
            normalized_name,
        )

        object.__setattr__(
            self,
            "base_url",
            normalized_base_url,
        )

        if not normalized_name:
            raise ValueError(
                "O nome da fonte não pode ficar vazio."
            )

        if not normalized_base_url.startswith(
            ("http://", "https://")
        ):
            raise ValueError(
                "A URL da fonte deve começar com "
                "http:// ou https://."
            )

        if (
            self.collection_allowed
            and self.policy_checked_at is None
        ):
            raise ValueError(
                "Uma fonte autorizada deve possuir a data "
                "de verificação da política."
            )


@dataclass(frozen=True, slots=True)
class Source:
    """Representa uma fonte persistida no banco."""

    id: int
    name: str
    base_url: str
    source_type: SourceType
    terms_url: str | None
    robots_url: str | None
    collection_allowed: bool
    policy_checked_at: datetime | None
    is_active: bool
    created_at: datetime


@dataclass(frozen=True, slots=True)
class CategoryInput:
    """Representa os dados para cadastrar uma categoria."""

    name: str

    def __post_init__(self) -> None:
        """Normaliza e valida o nome da categoria."""
        normalized_name = self.name.strip()

        object.__setattr__(
            self,
            "name",
            normalized_name,
        )

        if not normalized_name:
            raise ValueError(
                "O nome da categoria não pode ficar vazio."
            )

        if len(normalized_name) > 100:
            raise ValueError(
                "O nome da categoria deve possuir "
                "no máximo 100 caracteres."
            )


@dataclass(frozen=True, slots=True)
class Category:
    """Representa uma categoria persistida no banco."""

    id: int
    name: str
    created_at: datetime


class CollectionRunStatus(StrEnum):
    """Representa os estados de uma execução de coleta."""

    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class CollectionRunMetrics:
    """Contém as quantidades produzidas por uma coleta."""

    records_found: int = 0
    records_inserted: int = 0
    records_updated: int = 0
    records_rejected: int = 0

    def __post_init__(self) -> None:
        """Impede métricas negativas."""
        values = {
            "records_found": self.records_found,
            "records_inserted": self.records_inserted,
            "records_updated": self.records_updated,
            "records_rejected": self.records_rejected,
        }

        for field_name, value in values.items():
            if value < 0:
                raise ValueError(
                    f"{field_name} não pode ser negativo."
                )


@dataclass(frozen=True, slots=True)
class CollectionRun:
    """Representa uma execução de coleta persistida."""

    id: int
    source_id: int
    started_at: datetime
    finished_at: datetime | None
    status: CollectionRunStatus
    records_found: int
    records_inserted: int
    records_updated: int
    records_rejected: int
    error_message: str | None

    @property
    def is_finished(self) -> bool:
        """Informa se a execução já foi finalizada."""
        return self.finished_at is not None

    @property
    def duration_seconds(self) -> float | None:
        """Calcula a duração total da execução."""
        if self.finished_at is None:
            return None

        duration = self.finished_at - self.started_at

        return duration.total_seconds()


@dataclass(frozen=True, slots=True)
class ApiPage():
    """"Representa uma página válida de uma API"""

    page: int
    page_size: int
    total_pages: int
    total_items: int
    items: tuple[dict[str, Any], ...]

@dataclass(frozen=True, slots=True)
class ExtractionResult():
    """""Representa o resultado completo de uma extração"""

    records: tuple[dict[str, Any], ...]
    pages_fetched: int
    total_items: int

@dataclass(frozen=True, slots=True)
class CollectionOutcome():
    """""Representa o resultado de uma coleta concluida"""

    run: CollectionRun
    extraction: ExtractionResult
    raw_file: Path

class NoticeStatus(StrEnum):
    """Representa os estados permitidos de um edital."""

    UNKNOWN = "unknown"
    OPEN = "open"
    CLOSED = "closed"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class NoticeRecord:
    """Representa um edital limpo e validado."""

    external_id: str | None
    title: str
    organization: str | None
    notice_number: str | None
    publication_date: date | None
    registration_deadline: date | None
    url: str
    status: NoticeStatus
    content_hash: str
    raw_payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class TransformationIssue:
    """Representa um registro rejeitado na transformação."""

    row_number: int
    external_id: str | None
    reasons: tuple[str, ...]
    raw_payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class NoticeTransformationResult:
    """Agrupa o resultado completo da transformação."""

    valid_records: tuple[NoticeRecord, ...]
    rejected_records: tuple[TransformationIssue, ...]
    input_count: int
    duplicate_count: int

    @property
    def valid_count(self) -> int:
        """Retorna a quantidade de registros válidos."""
        return len(self.valid_records)

    @property
    def rejected_count(self) -> int:
        """Retorna a quantidade de registros rejeitados."""
        return len(self.rejected_records)