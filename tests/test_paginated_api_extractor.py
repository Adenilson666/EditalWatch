from typing import Any

import httpx
import pytest

from editalwatch.exceptions import (
    InvalidAPIResponseError,
)
from editalwatch.extractors.paginated_api import (
    PaginatedAPIExtractor,
)


def build_page(
    page: int,
    items: list[dict[str, Any]],
    total_pages: int,
    total_items: int,
) -> dict[str, Any]:
    """Cria uma resposta paginada para os testes."""
    return {
        "items": items,
        "pagination": {
            "page": page,
            "page_size": 2,
            "total_pages": total_pages,
            "total_items": total_items,
        },
    }


def test_fetch_all_collects_every_page() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        page = int(
            request.url.params["page"]
        )

        responses = {
            1: build_page(
                page=1,
                items=[
                    {"id": 1},
                    {"id": 2},
                ],
                total_pages=2,
                total_items=3,
            ),
            2: build_page(
                page=2,
                items=[
                    {"id": 3},
                ],
                total_pages=2,
                total_items=3,
            ),
        }

        return httpx.Response(
            status_code=200,
            json=responses[page],
            request=request,
        )

    extractor = PaginatedAPIExtractor(
        base_url="https://testserver",
        endpoint="/notices",
        timeout=5,
        max_retries=0,
        user_agent="EditalWatch-Test/1.0",
        page_size=2,
        transport=httpx.MockTransport(
            handler
        ),
    )

    result = extractor.fetch_all()

    assert result.pages_fetched == 2
    assert result.total_items == 3

    assert result.records == (
        {"id": 1},
        {"id": 2},
        {"id": 3},
    )


def test_fetch_all_retries_temporary_error() -> None:
    request_count = 0

    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        nonlocal request_count

        request_count += 1

        if request_count == 1:
            return httpx.Response(
                status_code=503,
                request=request,
            )

        return httpx.Response(
            status_code=200,
            json=build_page(
                page=1,
                items=[
                    {"id": 1},
                ],
                total_pages=1,
                total_items=1,
            ),
            request=request,
        )

    extractor = PaginatedAPIExtractor(
        base_url="https://testserver",
        endpoint="/notices",
        timeout=5,
        max_retries=1,
        user_agent="EditalWatch-Test/1.0",
        transport=httpx.MockTransport(
            handler
        ),
        sleep_function=lambda _: None,
    )

    result = extractor.fetch_all()

    assert request_count == 2
    assert result.total_items == 1


def test_fetch_all_rejects_invalid_items() -> None:
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "items": "não é uma lista",
                "pagination": {
                    "page": 1,
                    "page_size": 2,
                    "total_pages": 1,
                    "total_items": 1,
                },
            },
            request=request,
        )

    extractor = PaginatedAPIExtractor(
        base_url="https://testserver",
        endpoint="/notices",
        timeout=5,
        max_retries=0,
        user_agent="EditalWatch-Test/1.0",
        transport=httpx.MockTransport(
            handler
        ),
    )

    with pytest.raises(
        InvalidAPIResponseError,
        match="items",
    ):
        extractor.fetch_all()