from flask import Blueprint, jsonify
from sqlalchemy import text
from app.extensions import db

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Verifica el estado del servicio y la conexión a la base de datos."""
    db_status = "ok"
    try:
        db.session.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)}"

    return jsonify({
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
        "message": "Backend Hares operando correctamente"
    }), 200 if db_status == "ok" else 500
