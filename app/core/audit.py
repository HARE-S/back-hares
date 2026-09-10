import datetime
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("audit")

# Registro en memoria para trazabilidad, desarrollo y tests
_audit_records: List[Dict[str, Any]] = []


def log_audit(
    user: Optional[Dict[str, Any]],
    action: str,
    resource_type: str,
    resource_id: str,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Registra una entrada de auditoría (BE-18 Escenario 8 y BE-44).
    Guarda quién realizó la acción, cuándo y qué recurso fue afectado.
    """
    user_identifier = None
    if isinstance(user, dict):
        user_identifier = user.get("email") or user.get("id") or user.get("name")
    elif user is not None:
        user_identifier = str(user)
    else:
        user_identifier = "anonymous"

    now = datetime.datetime.now(datetime.timezone.utc)

    record = {
        "user": user_identifier,
        "action": action,
        "resource_type": resource_type,
        "resource_id": str(resource_id),
        "timestamp": now.isoformat(),
        "date": now.date().isoformat(),
        "details": details or {},
    }

    _audit_records.append(record)
    logger.info(
        "AUDIT: user=%s action=%s resource=%s/%s",
        user_identifier,
        action,
        resource_type,
        resource_id,
    )
    return record


def get_audit_logs(
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Devuelve las entradas de auditoría registradas, opcionalmente filtradas."""
    logs = list(_audit_records)
    if resource_type:
        logs = [entry for entry in logs if entry.get("resource_type") == resource_type]
    if resource_id:
        logs = [entry for entry in logs if entry.get("resource_id") == str(resource_id)]
    return logs


def clear_audit_logs() -> None:
    """Limpia los registros de auditoría en memoria (útil para tests)."""
    _audit_records.clear()
