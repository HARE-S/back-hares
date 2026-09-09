from functools import wraps
from flask import current_app, g, jsonify, session


def get_current_user():
    """
    Obtiene el usuario autenticado actual.
    Si DEV_AUTH_BYPASS está activo y no hay sesión real, devuelve un usuario simulado.
    """
    if hasattr(g, "current_user") and g.current_user is not None:
        return g.current_user

    # Comprobación de sesión estándar
    user_id = session.get("user_id")
    if user_id is not None:
        user = {
            "id": user_id,
            "email": session.get("user_email", "user@penascal.org"),
            "role": session.get("user_role", "tutor"),
            "name": session.get("user_name", "Usuario Autenticado"),
        }
        g.current_user = user
        return user

    # Modo bypass para desarrollo (BE-45 / Contrato 2)
    if current_app.config.get("DEV_AUTH_BYPASS"):
        dev_role = session.get("dev_role", "tutor")
        dev_user = {
            "id": 9999,
            "email": f"dev.{dev_role}@penascal.org",
            "role": dev_role,
            "name": f"Usuario Dev ({dev_role})",
            "is_dev": True,
        }
        g.current_user = dev_user
        return dev_user

    return None


def require_role(*allowed_roles):
    """
    Decorador que restringe el acceso al endpoint según los roles especificados.

    Devuelve:
    - 401 UNAUTHORIZED si el usuario no ha iniciado sesión.
    - 403 FORBIDDEN si el rol del usuario no está en allowed_roles.
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()

            if not user:
                return (
                    jsonify(
                        {
                            "code": 401,
                            "error": "UNAUTHORIZED",
                            "message": "Se requiere autenticación para acceder a este recurso.",
                        }
                    ),
                    401,
                )

            user_role = user.get("role", "")
            if allowed_roles and user_role not in allowed_roles:
                return (
                    jsonify(
                        {
                            "code": 403,
                            "error": "FORBIDDEN",
                            "message": f"Acceso denegado. Se requiere uno de los siguientes roles: {list(allowed_roles)}.",
                        }
                    ),
                    403,
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator
