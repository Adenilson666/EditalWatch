import time
from collections.abc import Callable
from typing import Any

import httpx
from tenacity import (
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from editalwatch.exceptions import (
    DataExtractionError,
    InvalidAPIResponseError,
    RetryableAPIError,
)
from editalwatch.models import (
    ApiPage,
    ExtractionResult,
)


SleepFunction = Callable[[float], None]


class PaginatedAPIExtractor:
    """Extrai registros de uma API paginada."""

    def __init__(
        self,
        base_url: str,
        endpoint: str,
        timeout: float,
        max_retries: int,
        user_agent: str,
        page_size: int = 50,
        transport: httpx.BaseTransport | None = None,
        sleep_function: SleepFunction = time.sleep,
    ) -> None:
        if timeout <= 0:
            raise ValueError(
                "O timeout deve ser maior que zero."
            )

        if max_retries < 0:
            raise ValueError(
                "A quantidade de tentativas não pode "
                "ser negativa."
            )

        if page_size <= 0:
            raise ValueError(
                "O tamanho da página deve ser maior "
                "que zero."
            )

        self._base_url = base_url.rstrip("/")
        self._endpoint = f"/{endpoint.lstrip('/')}"
        self._timeout = timeout
        self._max_retries = max_retries
        self._user_agent = user_agent
        self._page_size = page_size
        self._transport = transport
        self._sleep_function = sleep_function

    def fetch_all(self) -> ExtractionResult:
        """Percorre todas as páginas e retorna os registros."""
        records: list[dict[str, Any]] = []

        current_page = 1
        expected_total_pages: int | None = None
        expected_total_items: int | None = None

        with httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout,
            headers={
                "User-Agent": self._user_agent,
                "Accept": "application/json",
            },
            transport=self._transport,
            follow_redirects=True,
        ) as client:
            while (
                expected_total_pages is None
                or current_page <= expected_total_pages
            ):
                payload = self._fetch_page(
                    client=client,
                    page=current_page,
                )

                api_page = self._parse_page(
                    payload=payload,
                    expected_page=current_page,
                )

                if expected_total_pages is None:
                    expected_total_pages = api_page.total_pages
                    expected_total_items = api_page.total_items

                elif (
                    api_page.total_pages
                    != expected_total_pages
                ):
                    raise InvalidAPIResponseError(
                        "O total de páginas mudou durante "
                        "a extração."
                    )

                elif (
                    api_page.total_items
                    != expected_total_items
                ):
                    raise InvalidAPIResponseError(
                        "O total de registros mudou durante "
                        "a extração."
                    )

                records.extend(api_page.items)
                current_page += 1

        total_items = (
            expected_total_items
            if expected_total_items is not None
            else 0
        )

        pages_fetched = (
            expected_total_pages
            if expected_total_pages is not None
            else 0
        )

        if len(records) != total_items:
            raise InvalidAPIResponseError(
                "A quantidade recebida não corresponde "
                "ao total informado pela API."
            )

        return ExtractionResult(
            records=tuple(records),
            pages_fetched=pages_fetched,
            total_items=total_items,
        )

    def _fetch_page(
        self,
        client: httpx.Client,
        page: int,
    ) -> dict[str, Any]:
        """Busca uma página aplicando a política de retry."""
        retrying = Retrying(
            stop=stop_after_attempt(
                self._max_retries + 1
            ),
            wait=wait_exponential(
                multiplier=0.5,
                min=0.5,
                max=4,
            ),
            retry=retry_if_exception_type(
                (
                    httpx.RequestError,
                    RetryableAPIError,
                )
            ),
            reraise=True,
            sleep=self._sleep_function,
        )

        try:
            for attempt in retrying:
                with attempt:
                    response = client.get(
                        self._endpoint,
                        params={
                            "page": page,
                            "page_size": self._page_size,
                        },
                    )

                    if (
                        response.status_code == 429
                        or response.status_code >= 500
                    ):
                        raise RetryableAPIError(
                            "A API apresentou uma falha "
                            f"temporária HTTP "
                            f"{response.status_code}."
                        )

                    try:
                        response.raise_for_status()

                    except httpx.HTTPStatusError as error:
                        raise DataExtractionError(
                            "A API rejeitou a requisição "
                            f"com HTTP "
                            f"{response.status_code}."
                        ) from error

                    try:
                        payload = response.json()

                    except ValueError as error:
                        raise InvalidAPIResponseError(
                            "A API não retornou um JSON válido."
                        ) from error

                    if not isinstance(payload, dict):
                        raise InvalidAPIResponseError(
                            "A raiz da resposta deve ser "
                            "um objeto JSON."
                        )

                    return payload

        except RetryableAPIError:
            raise

        except httpx.RequestError as error:
            raise DataExtractionError(
                "Não foi possível comunicar-se com a API."
            ) from error

        raise DataExtractionError(
            "A página não pôde ser obtida."
        )

    @staticmethod
    def _parse_page(
        payload: dict[str, Any],
        expected_page: int,
    ) -> ApiPage:
        """Valida a estrutura de uma página."""
        items = payload.get("items")
        pagination = payload.get("pagination")

        if not isinstance(items, list):
            raise InvalidAPIResponseError(
                "O campo 'items' deve ser uma lista."
            )

        if not isinstance(pagination, dict):
            raise InvalidAPIResponseError(
                "O campo 'pagination' deve ser um objeto."
            )

        page = PaginatedAPIExtractor._read_integer(
            pagination,
            "page",
        )

        page_size = PaginatedAPIExtractor._read_integer(
            pagination,
            "page_size",
        )

        total_pages = PaginatedAPIExtractor._read_integer(
            pagination,
            "total_pages",
        )

        total_items = PaginatedAPIExtractor._read_integer(
            pagination,
            "total_items",
        )

        if page != expected_page:
            raise InvalidAPIResponseError(
                f"A API retornou a página {page}, mas "
                f"a página {expected_page} foi solicitada."
            )

        if page_size <= 0:
            raise InvalidAPIResponseError(
                "O tamanho da página deve ser positivo."
            )

        if total_pages <= 0:
            raise InvalidAPIResponseError(
                "O total de páginas deve ser positivo."
            )

        if total_items < 0:
            raise InvalidAPIResponseError(
                "O total de itens não pode ser negativo."
            )

        if page > total_pages:
            raise InvalidAPIResponseError(
                "A página atual é maior que o total "
                "de páginas."
            )

        validated_items: list[dict[str, Any]] = []

        for item in items:
            if not isinstance(item, dict):
                raise InvalidAPIResponseError(
                    "Cada item da resposta deve ser "
                    "um objeto JSON."
                )

            validated_items.append(item)

        return ApiPage(
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            total_items=total_items,
            items=tuple(validated_items),
        )

    @staticmethod
    def _read_integer(
        data: dict[str, Any],
        field_name: str,
    ) -> int:
        """Lê um inteiro e rejeita booleanos."""
        value = data.get(field_name)

        if (
            not isinstance(value, int)
            or isinstance(value, bool)
        ):
            raise InvalidAPIResponseError(
                f"O campo '{field_name}' deve ser inteiro."
            )

        return value