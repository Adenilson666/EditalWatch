import json
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer,
)
from math import ceil
from urllib.parse import (
    parse_qs,
    urlparse,
)


NOTICES = [
    {
        "external_id": "LOCAL-001",
        "title": (
            "Concurso para Analista de "
            "Tecnologia da Informação"
        ),
        "organization": (
            "Instituição Local de Demonstração"
        ),
        "publication_date": "2026-07-20",
        "registration_deadline": "2026-08-15",
        "url": (
            "http://localhost:8000/"
            "documents/local-001"
        ),
        "status": "open",
    },
    {
        "external_id": "LOCAL-002",
        "title": (
            "Seleção para Desenvolvedor Python"
        ),
        "organization": (
            "Instituição Local de Demonstração"
        ),
        "publication_date": "2026-07-22",
        "registration_deadline": "2026-08-18",
        "url": (
            "http://localhost:8000/"
            "documents/local-002"
        ),
        "status": "open",
    },
    {
        "external_id": "LOCAL-003",
        "title": (
            "Processo Seletivo para Banco de Dados"
        ),
        "organization": (
            "Universidade Local de Demonstração"
        ),
        "publication_date": "2026-07-24",
        "registration_deadline": "2026-08-20",
        "url": (
            "http://localhost:8000/"
            "documents/local-003"
        ),
        "status": "open",
    },
    {
        "external_id": "LOCAL-004",
        "title": (
            "Seleção para Segurança da Informação"
        ),
        "organization": (
            "Universidade Local de Demonstração"
        ),
        "publication_date": "2026-07-25",
        "registration_deadline": "2026-08-22",
        "url": (
            "http://localhost:8000/"
            "documents/local-004"
        ),
        "status": "open",
    },
    {
        "external_id": "LOCAL-005",
        "title": (
            "Seleção Temporária para Infraestrutura"
        ),
        "organization": (
            "Instituição Local de Demonstração"
        ),
        "publication_date": "2026-07-10",
        "registration_deadline": "2026-07-25",
        "url": (
            "http://localhost:8000/"
            "documents/local-005"
        ),
        "status": "closed",
    },
]


class DemoAPIHandler(BaseHTTPRequestHandler):
    """Atende requisições da API local."""

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)

        if parsed_url.path != "/notices":
            self._send_json(
                status_code=404,
                payload={
                    "error": "Endpoint não encontrado."
                },
            )
            return

        parameters = parse_qs(
            parsed_url.query
        )

        try:
            page = int(
                parameters.get(
                    "page",
                    ["1"],
                )[0]
            )

            page_size = int(
                parameters.get(
                    "page_size",
                    ["2"],
                )[0]
            )

        except ValueError:
            self._send_json(
                status_code=400,
                payload={
                    "error": (
                        "page e page_size devem "
                        "ser inteiros."
                    )
                },
            )
            return

        if page <= 0 or page_size <= 0:
            self._send_json(
                status_code=400,
                payload={
                    "error": (
                        "page e page_size devem "
                        "ser positivos."
                    )
                },
            )
            return

        total_items = len(NOTICES)

        total_pages = max(
            1,
            ceil(total_items / page_size),
        )

        start_index = (
            page - 1
        ) * page_size

        end_index = (
            start_index + page_size
        )

        items = NOTICES[
            start_index:end_index
        ]

        self._send_json(
            status_code=200,
            payload={
                "items": items,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages,
                    "total_items": total_items,
                },
            },
        )

    def _send_json(
        self,
        status_code: int,
        payload: dict,
    ) -> None:
        content = json.dumps(
            payload,
            ensure_ascii=False,
        ).encode("utf-8")

        self.send_response(status_code)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
        )

        self.send_header(
            "Content-Length",
            str(len(content)),
        )

        self.end_headers()
        self.wfile.write(content)

    def log_message(
        self,
        format: str,
        *args: object,
    ) -> None:
        print(
            f"[API local] {format % args}"
        )


def main() -> None:
    """Inicia a API local na porta 8000."""
    server = ThreadingHTTPServer(
        ("127.0.0.1", 8000),
        DemoAPIHandler,
    )

    print(
        "API local disponível em "
        "http://127.0.0.1:8000"
    )

    print(
        "Endpoint: "
        "http://127.0.0.1:8000/notices"
    )

    print(
        "Pressione Ctrl+C para encerrar."
    )

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print("\nEncerrando API local...")

    finally:
        server.server_close()


if __name__ == "__main__":
    main()