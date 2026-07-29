import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from editalwatch.exceptions import ConfigurationError


@dataclass(frozen=True, slots=True)
class Settings:
    """Agrupa as configurações utilizadas pelo EditalWatch."""

    database_url: str

    @classmethod
    def load(
        cls,
        env_file: str | Path | None = ".env",
    ) -> "Settings":
        """Carrega e valida as configurações do ambiente."""
        if env_file is not None:
            load_dotenv(
                dotenv_path=env_file,
                override=False,
            )

        database_url = os.getenv(
            "EDITALWATCH_DATABASE_URL",
            "",
        ).strip()

        if not database_url:
            raise ConfigurationError(
                "EDITALWATCH_DATABASE_URL não foi configurada."
            )

        if not database_url.startswith(
            ("postgresql://", "postgres://")
        ):
            raise ConfigurationError(
                "EDITALWATCH_DATABASE_URL deve ser uma URL "
                "válida do PostgreSQL."
            )

        return cls(
            database_url=database_url,
        )