from functools import wraps
from flask import jsonify, request


def require_role(*allowed_roles):
    """
    Decorador de autorización basado en roles (Contrato 2 de REPARTO.md).
    Implementación desacoplada / provisional para desarrollo y pruebas:
    - Evalúa el rol enviado en la cabecera 'X-User-Role' (ej: 'coordinator', 'admin', 'tutor').
    - Si no se especifica cabecera, por defecto asume 'coordinator' en desarrollo para no bloquear peticiones manuales.
    - Si el rol no pertenece a allowed_roles, deniega con 403 Forbidden.
    - Cuando Santiago implemente la sesión con Google Auth (BE-38 a BE-42), se integrará la sesión real sin modificar los endpoints.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Obtener rol de la cabecera (o por defecto coordinator)
            role = request.headers.get("X-User-Role", "coordinator").strip().lower()

            allowed_lower = [r.lower() for r in allowed_roles]
            if role not in allowed_lower:
                return (
                    jsonify({
                        "error": (
                            f"Permiso denegado. Se requiere uno de los siguientes roles: "
                            f"{', '.join(allowed_roles)}"
                        )
                    }),
                    403,
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator
