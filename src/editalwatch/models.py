from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


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