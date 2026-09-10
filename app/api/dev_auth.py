from flask import Blueprint, g, jsonify, request, session
from app.auth.decorators import get_current_user

dev_auth_bp = Blueprint("dev_auth", __name__)


@dev_auth_bp.route("/session", methods=["POST"])
def set_dev_session():
    """
    Endpoint de desarrollo para cambiar el rol y datos del usuario simulado (BE-45).
    Solo se registra si DEV_AUTH_BYPASS=true y APP_ENV != production.
    """
    data = request.get_json() or {}
    role = data.get("role", "tutor")
    email = data.get("email", f"dev.{role}@penascal.org")

    session["dev_role"] = role
    session["user_email"] = email
    if hasattr(g, "current_user"):
        delattr(g, "current_user")

    user = get_current_user()
    return jsonify(
        {
            "message": "Sesión de desarrollo actualizada con éxito.",
            "user": user,
        }
    ), 200
