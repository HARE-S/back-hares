"""Excepciones personalizadas de la aplicación."""


class AppError(Exception):
    """Excepción base de la aplicación."""
    pass


class ValidationError(AppError):
    """Error de validación."""
    pass


class NotFoundError(AppError):
    """Recurso no encontrado."""
    pass


class ConflictError(AppError):
    """Conflicto (ej: email duplicado)."""
    pass


class UnauthorizedError(AppError):
    """Error de autenticación."""
    pass


class ForbiddenError(AppError):
    """Error de autorización."""
    pass
