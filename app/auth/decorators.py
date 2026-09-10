from functools import wraps
from flask import current_app, g, jsonify, request, session


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
        sections = session.get("user_sections", [])
        if not sections:
            header_sec = request.headers.get("X-User-Sections")
            if header_sec:
                sections = [s.strip() for s in header_sec.split(",") if s.strip()]
        user = {
            "id": user_id,
            "email": session.get("user_email", "user@penascal.org"),
            "role": session.get("user_role", "tutor"),
            "name": session.get("user_name", "Usuario Autenticado"),
            "sections": sections,
        }
        g.current_user = user
        return user

    # Modo bypass para desarrollo (BE-45 / Contrato 2)
    if current_app.config.get("DEV_AUTH_BYPASS"):
        dev_role = session.get("dev_role", "tutor")
        sections = session.get("dev_sections", session.get("user_sections", []))
        if not sections:
            header_sec = request.headers.get("X-User-Sections")
            if header_sec:
                sections = [s.strip() for s in header_sec.split(",") if s.strip()]
        dev_email = session.get("user_email") or f"dev.{dev_role}@penascal.org"
        dev_user = {
            "id": 9999,
            "email": dev_email,
            "role": dev_role,
            "name": f"Usuario Dev ({dev_role})",
            "is_dev": True,
            "sections": sections,
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

            user_role = str(user.get("role", "")).strip().lower()
            allowed_normalized = set()
            for r in allowed_roles:
                r_low = r.strip().lower()
                allowed_normalized.add(r_low)
                if r_low in ("coordinator", "coordinador"):
                    allowed_normalized.add("coordinator")
                    allowed_normalized.add("coordinador")

            if allowed_roles and user_role not in allowed_normalized:
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

