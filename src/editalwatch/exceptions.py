class ConfigurationError(Exception):
    """Indica uma configuração ausente ou inválida."""

class DatabaseConnectionError(Exception):
    """Indica um erro ao tentar conectar-se ao banco de dados."""

class DatabaseOperationError(Exception):
    """Indica um erro ao tentar realizar uma operação no banco de dados."""

class SourceAlreadyExistsError(Exception):
    """Indica que a fonte de dados já existe."""

class SourceNotFoundError(Exception):
    """Indica que a fonte de dados não foi encontrada."""
    