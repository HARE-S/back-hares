class DomainException(Exception):
    """Excepción base del dominio de la aplicación."""
    pass


class DuplicateCodeError(DomainException):
    """Se lanza cuando un código que debe ser único ya existe en el sistema."""
    pass


class ValidationError(DomainException):
    """Se lanza cuando los datos de entrada no cumplen las reglas de validación."""
    pass


class ForbiddenError(DomainException):
    """Se lanza cuando el usuario no tiene permisos suficientes para la acción."""
    pass


class ConflictError(DomainException):
    """Se lanza cuando una operación entra en conflicto con el estado actual del dominio."""
    pass


class SchemaValidationError(DomainException):
    """Se lanza cuando un esquema de actualización o entrada tiene formato o valores semánticamente no procesables (422)."""
    pass

