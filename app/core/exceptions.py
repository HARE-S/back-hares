class DomainException(Exception):
    """Excepción base del dominio de la aplicación."""
    pass


class DuplicateCodeError(DomainException):
    """Se lanza cuando un código que debe ser único ya existe en el sistema."""
    pass


class ValidationError(DomainException):
    """Se lanza cuando los datos de entrada no cumplen las reglas de validación."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.message = message
        self.field = field


class ForbiddenError(DomainException):
    """Se lanza cuando el usuario no tiene permisos suficientes para la acción."""
    pass


class ConflictError(DomainException):
    """Se lanza cuando una operación entra en conflicto con el estado actual del dominio."""
    pass


class SchemaValidationError(DomainException):
    """Se lanza cuando un esquema de actualización o entrada tiene formato o valores semánticamente no procesables (422)."""
    pass


class NotFoundError(DomainException):
    """Se lanza cuando un recurso solicitado no existe en el sistema (404)."""
    pass


class BatchValidationError(DomainException):
    """Se lanza cuando un lote contiene filas inválidas o con errores específicos por fila (BE-22)."""

    def __init__(self, message: str, errors: list):
        super().__init__(message)
        self.message = message
        self.errors = errors



