"""Depósito compartido para ficheros subidos pendientes de confirmar (BE-09).

Guarda el contenido decodificado del CSV asociado a un token temporal.
Persiste tanto en memoria local como en disco (/tmp/hares_upload_store) para que
múltiples workers de gunicorn compartan el estado de las subidas sin perder tokens.
"""
import json
import os
from pathlib import Path
import secrets
import time
from typing import Any, Dict, List, Optional


_DEFAULT_TTL = 900       # 15 minutos
_DEFAULT_MAX = 200       # máximo de entradas simultáneas
_STORAGE_DIR = Path(os.environ.get("HARES_UPLOAD_DIR", "/tmp/hares_upload_store"))


class UploadStore:
    """Token-based CSV buffer shared across gunicorn workers."""

    def __init__(self, ttl: int = _DEFAULT_TTL, max_entries: int = _DEFAULT_MAX, storage_dir: Optional[Path] = None):
        self._ttl = ttl
        self._max = max_entries
        self._storage_dir = storage_dir or _STORAGE_DIR
        self._entries: Dict[str, Dict[str, Any]] = {}
        self._order: List[str] = []

    def _ensure_dir(self) -> None:
        try:
            self._storage_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass

    def _file_path(self, token: str) -> Path:
        return self._storage_dir / f"{token}.json"

    # ------------------------------------------------------------------
    def put(self, filename: str, content: str, extra: Optional[Dict[str, Any]] = None) -> str:
        """Stores content under a new random token and returns it.

        Prunes expired entries first and evicts the oldest if over capacity.
        """
        self._prune()
        if len(self._order) >= self._max:
            oldest = self._order.pop(0)
            self._entries.pop(oldest, None)

        token = secrets.token_urlsafe(16)
        entry = {
            "filename": filename,
            "content": content,
            "extra": extra or {},
            "uploaded_at": time.time(),
        }
        self._entries[token] = entry
        self._order.append(token)

        try:
            self._ensure_dir()
            tmp_path = self._storage_dir / f"{token}.tmp"
            tmp_path.write_text(json.dumps(entry, ensure_ascii=False), encoding="utf-8")
            tmp_path.replace(self._file_path(token))
        except Exception:
            pass

        return token

    def get(self, token: Optional[str]) -> Optional[Dict[str, Any]]:
        """Returns the entry for *token* if it exists and hasn't expired.

        Returns None for missing or expired tokens. The entry is NOT
        removed: the caller deletes it explicitly after a successful
        import so that a failed confirm allows retry.
        """
        if token is None:
            return None

        self._prune()

        file_path = self._file_path(token)
        # Si el fichero no existe en disco y ya intentamos persistirlo,
        # significa que otro worker lo consumió o fue borrado.
        if self._storage_dir.exists() and not file_path.exists():
            self._entries.pop(token, None)
            return None

        entry = self._entries.get(token)
        if entry is None:
            if file_path.exists():
                try:
                    entry = json.loads(file_path.read_text(encoding="utf-8"))
                    self._entries[token] = entry
                    if token not in self._order:
                        self._order.append(token)
                except Exception:
                    entry = None

        if entry is None:
            return None

        age = time.time() - entry.get("uploaded_at", 0)
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
        try:
            if self._storage_dir.exists():
                for f in self._storage_dir.glob("*.json"):
                    try:
                        f.unlink()
                    except Exception:
                        pass
                for f in self._storage_dir.glob("*.tmp"):
                    try:
                        f.unlink()
                    except Exception:
                        pass
        except Exception:
            pass

    # ------------------------------------------------------------------
    def _delete(self, token: Optional[str]) -> None:
        if token and token in self._entries:
            del self._entries[token]
            if token in self._order:
                self._order.remove(token)
        if token:
            try:
                f = self._file_path(token)
                if f.exists():
                    f.unlink()
            except Exception:
                pass

    def _prune(self) -> None:
        """Removes all entries whose TTL has elapsed."""
        now = time.time()
        expired = [
            t for t, e in list(self._entries.items())
            if (now - e.get("uploaded_at", 0)) > self._ttl
        ]
        for t in expired:
            self._delete(t)

        try:
            if self._storage_dir.exists():
                for f in self._storage_dir.glob("*.json"):
                    try:
                        if (now - f.stat().st_mtime) > self._ttl:
                            f.unlink()
                    except Exception:
                        pass
        except Exception:
            pass

    @property
    def size(self) -> int:
        """Current number of stored entries (useful in tests)."""
        if self._storage_dir.exists():
            return len(list(self._storage_dir.glob("*.json")))
        return len(self._entries)


# Singleton used by the import blueprint.
upload_store = UploadStore()
