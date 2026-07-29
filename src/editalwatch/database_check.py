from editalwatch.config import Settings
from editalwatch.database import Database
from editalwatch.exceptions import (
    ConfigurationError,
    DatabaseConnectionError,
)

def main() -> None:
    """Verifica se o PostgreSQL está disponivel."""

    try:
        settings = Settings.load()
        database = Database(settings.database_url)
        information = database.check_connection()

    except ConfigurationError as error:
        print(f"Erro de configuração: {error}")
        return

    except DatabaseConnectionError as error:
        print(f"Erro de conexão com o banco de dados: {error}")
        return

    print("Conexão com o banco de dados estabelecida com sucesso!")
    print(f"Banco: {information.database_name}")
    print(f"Usuário: {information.username}")
    print(f"Versão: {information.postgres_version}")

if __name__ == "__main__":
    main()