from functools import wraps
from flask import current_app, g, jsonify, session, request
import jwt


def get_current_user():
    """
    Obtiene el usuario autenticado actual del JWT en el header Authorization.
    Si no hay JWT y DEV_AUTH_BYPASS está activo, retorna usuario simulado.
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

    # Modo bypass para desarrollo (BE-45)
    if current_app.config.get("DEV_AUTH_BYPASS"):
        dev_role = session.get("dev_role", "tutor")
        dev_user = {
            "id": "dev-user-id",
            "email": f"dev.{dev_role}@grupopenascal.com",
            "role": dev_role,
            "area": session.get("dev_area", "Desarrollo"),
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

            if allowed_roles and user.get("role") not in allowed_roles:
                return jsonify({"error": "FORBIDDEN"}), 403

            return f(*args, **kwargs)

        return decorated_function

    return decorator
