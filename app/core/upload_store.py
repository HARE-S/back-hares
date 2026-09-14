"""Depósito en memoria para ficheros subidos pendientes de confirmar (BE-09).

Guarda el contenido decodificado del CSV asociado a un token temporal, de
forma que el endpoint de previsualización y el de confirmación comparten
el fichero sin necesidad de tabla ni directorio temporal.

Limitaciones conocidas (aceptables en dev / un solo worker):
  - El estado no se comparte entre procesos gunicorn.
  - Los tokens caducan al reiniciar el contenedor.
"""
import secrets
import time
from typing import Any, Dict, List, Optional


_DEFAULT_TTL = 900       # 15 minutos
_DEFAULT_MAX = 200       # máximo de entradas simultáneas
_MAX_BYTES_HINT = 2 * 1024 * 1024  # solo para referencia; el límite real está en Config


class UploadStore:
    """Token-based in-memory CSV buffer."""

    def __init__(self, ttl: int = _DEFAULT_TTL, max_entries: int = _DEFAULT_MAX):
        self._ttl = ttl
        self._max = max_entries
        self._entries: Dict[str, Dict[str, Any]] = {}
        self._order: List[str] = []

    # ------------------------------------------------------------------
    def put(self, filename: str, content: str) -> str:
        """Stores content under a new random token and returns it.

        Prunes expired entries first and evicts the oldest if over capacity.
        """
        self._prune()
        if len(self._order) >= self._max:
            oldest = self._order.pop(0)
            self._entries.pop(oldest, None)

        token = secrets.token_urlsafe(16)
        self._entries[token] = {
            "filename": filename,
            "content": content,
            "uploaded_at": time.monotonic(),
        }
        self._order.append(token)
        return token

    def get(self, token: Optional[str]) -> Optional[Dict[str, Any]]:
        """Returns the entry for *token* if it exists and hasn't expired.

        Returns None for missing or expired tokens.  The entry is NOT
        removed: the caller deletes it explicitly after a successful
        import so that a failed confirm allows retry.
        """
        if token is None:
            return None

        self._prune()
        entry = self._entries.get(token)
        if entry is None:
            return None

        age = time.monotonic() - entry["uploaded_at"]
        if age > self._ttl:
            self._delete(token)
            return None

        return entry

    def delete(self, token: Optional[str]) -> None:
        """Explicitly removes an entry (e.g. after a successful confirm)."""
        self._delete(token)

    def clear(self) -> None:
        """Empties the store (used by tests)."""
        self._entries.clear()
        self._order.clear()

    # ------------------------------------------------------------------
    def _delete(self, token: Optional[str]) -> None:
        if token and token in self._entries:
            del self._entries[token]
            if token in self._order:
                self._order.remove(token)

    def _prune(self) -> None:
        """Removes all entries whose TTL has elapsed."""
        now = time.monotonic()
        expired = [
            t for t, e in self._entries.items()
            if (now - e["uploaded_at"]) > self._ttl
        ]
        for t in expired:
            self._delete(t)

    @property
    def size(self) -> int:
        """Current number of stored entries (useful in tests)."""
        return len(self._entries)


# Singleton used by the import blueprint.
upload_store = UploadStore()
