import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from editalwatch.exceptions import ConfigurationError


@dataclass(frozen=True, slots=True)
class Settings:
    """Agrupa as configurações utilizadas pelo EditalWatch."""

    database_url: str
    http_timeout: float
    http_max_retries: int
    user_agent: str
    raw_data_dir: Path

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

        http_timeout = cls._load_positive_float(
            variable_name="EDITALWATCH_HTTP_TIMEOUT",
            default_value="15",
        )

        http_max_retries = cls._load_non_negative_int(
            variable_name="EDITALWATCH_HTTP_MAX_RETRIES",
            default_value="3",
        )

        if http_max_retries > 10:
            raise ConfigurationError(
                "EDITALWATCH_HTTP_MAX_RETRIES não pode "
                "ser maior que 10."
            )

        user_agent = os.getenv(
            "EDITALWATCH_USER_AGENT",
            "EditalWatch/0.1",
        ).strip()

        if not user_agent:
            raise ConfigurationError(
                "EDITALWATCH_USER_AGENT não pode ficar vazio."
            )

        raw_data_dir = Path(
            os.getenv(
                "EDITALWATCH_RAW_DATA_DIR",
                "data/raw",
            ).strip()
        )

        return cls(
            database_url=database_url,
            http_timeout=http_timeout,
            http_max_retries=http_max_retries,
            user_agent=user_agent,
            raw_data_dir=raw_data_dir,
        )

    @staticmethod
    def _load_positive_float(
        variable_name: str,
        default_value: str,
    ) -> float:
        """Carrega um número decimal positivo."""
        raw_value = os.getenv(
            variable_name,
            default_value,
        ).strip()

        try:
            value = float(raw_value)

        except ValueError as error:
            raise ConfigurationError(
                f"{variable_name} deve ser um número."
            ) from error

        if value <= 0:
            raise ConfigurationError(
                f"{variable_name} deve ser maior que zero."
            )

        return value

    @staticmethod
    def _load_non_negative_int(
        variable_name: str,
        default_value: str,
    ) -> int:
        """Carrega um número inteiro não negativo."""
        raw_value = os.getenv(
            variable_name,
            default_value,
        ).strip()

        try:
            value = int(raw_value)

        except ValueError as error:
            raise ConfigurationError(
                f"{variable_name} deve ser um número inteiro."
            ) from error

        if value < 0:
            raise ConfigurationError(
                f"{variable_name} não pode ser negativo."
            )

        return value