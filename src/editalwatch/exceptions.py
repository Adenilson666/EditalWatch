class ConfigurationError(Exception):
    """Indica uma configuração ausente ou inválida."""


class DatabaseConnectionError(Exception):
    """Indica uma falha ao conectar com o PostgreSQL."""


class DatabaseOperationError(Exception):
    """Indica uma falha durante uma operação no banco."""


class SourceAlreadyExistsError(Exception):
    """Indica que uma fonte já está cadastrada."""


class SourceNotFoundError(Exception):
    """Indica que uma fonte não foi encontrada."""


class CategoryAlreadyExistsError(Exception):
    """Indica que uma categoria já está cadastrada."""


class CategoryNotFoundError(Exception):
    """Indica que uma categoria não foi encontrada."""


class CollectionRunNotFoundError(Exception):
    """Indica que uma execução de coleta não foi encontrada."""


class CollectionRunStateError(Exception):
    """Indica uma transição inválida no estado de uma coleta."""

class DataExtractionError(Exception):
    """Indica uma falha durante a extração de dados."""


class RetryableAPIError(DataExtractionError):
    """Indica uma falha temporária que permite nova tentativa."""


class InvalidAPIResponseError(DataExtractionError):
    """Indica que a API retornou uma estrutura inválida."""


class RawDataStorageError(Exception):
    """Indica uma falha ao armazenar os dados brutos."""


class CollectionExecutionError(Exception):
    """Indica que uma execução de coleta não foi concluída."""