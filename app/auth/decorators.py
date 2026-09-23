from functools import wraps
from flask import current_app, g, jsonify, request, session
import jwt


def get_current_user():
    """
    Obtiene el usuario autenticado actual del JWT en el header Authorization o de la sesión.
    Si no hay JWT/sesión y DEV_AUTH_BYPASS está activo, retorna usuario simulado.
    """
    if hasattr(g, "current_user") and g.current_user is not None:
        return g.current_user

    # Extraer JWT del header Authorization
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            payload = jwt.decode(
                token,
                current_app.config["SECRET_KEY"],
                algorithms=["HS256"],
            )
            user = {
                "id": payload.get("sub"),
                "email": payload.get("email"),
                "role": payload.get("role"),
                "area": payload.get("area"),
            }
            g.current_user = user
            return user
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

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

    # Modo bypass para desarrollo (BE-45)
    if current_app.config.get("DEV_AUTH_BYPASS"):
        dev_role = session.get("dev_role", "tutor")
        dev_email = session.get("user_email") or f"dev.{dev_role}@grupopenascal.com"
        dev_user = {
            "id": "dev-user-id",
            "email": dev_email,
            "role": dev_role,
            "area": session.get("dev_area", "Desarrollo"),
            "sections": session.get("dev_sections") or [],
            "is_dev": True,
        }
        g.current_user = dev_user
        return dev_user

    return None


def require_role(*allowed_roles):
    """Restricts access to endpoint based on user role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()

            if not user:
                return jsonify({"error": "UNAUTHORIZED"}), 401

            user_role = str(user.get("role", "")).strip().lower()
            if user_role == "superadmin":
                return f(*args, **kwargs)

            allowed_normalized = set()
            for r in allowed_roles:
                r_low = r.strip().lower()
                allowed_normalized.add(r_low)
                if r_low in ("coordinator", "coordinador"):
                    allowed_normalized.add("coordinator")
                    allowed_normalized.add("coordinador")
                if r_low == "admin":
                    allowed_normalized.add("superadmin")

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
