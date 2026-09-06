from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any, Dict, Iterable, List


class SecurityManager:
    """
    Path-level safety guard for AI-generated changes.

    This component only decides whether a path is safe to write.
    It never reads secrets and never modifies files.
    """

    PROTECTED_FILENAMES = {
        ".env",
        ".env.local",
        ".env.production",
        ".env.development",
        "id_rsa",
        "id_ed25519",
        "credentials.json",
        "service-account.json",
    }

    PROTECTED_DIRECTORIES = {
        ".git",
        ".ssh",
    }

    PROTECTED_SUFFIXES = {
        ".pem",
        ".key",
        ".p12",
        ".pfx",
    }

    def inspect_path(self, path: str) -> Dict[str, Any]:
        normalized = str(path or "").replace("\\", "/").strip()

        if not normalized:
            return self._blocked(path, "Path cannot be empty.")

        pure = PurePosixPath(normalized)

        if pure.is_absolute():
            return self._blocked(path, "Absolute paths are not allowed.")

        if ".." in pure.parts:
            return self._blocked(path, "Path traversal is not allowed.")

        parts = set(pure.parts)
        filename = pure.name.lower()

        if parts & self.PROTECTED_DIRECTORIES:
            return self._blocked(path, "Path targets a protected directory.")

        if filename in self.PROTECTED_FILENAMES:
            return self._blocked(path, "Path targets a protected secret/config file.")

        if any(filename.endswith(suffix) for suffix in self.PROTECTED_SUFFIXES):
            return self._blocked(path, "Path has a protected credential extension.")

        return {
            "path": path,
            "protected": False,
            "safe_for_ai_write": True,
            "reason": "Path passed security policy.",
        }

    def inspect_paths(self, paths: Iterable[str]) -> Dict[str, Any]:
        reports: List[Dict[str, Any]] = [self.inspect_path(path) for path in paths]
        blocked = [report for report in reports if not report["safe_for_ai_write"]]

        return {
            "passed": not blocked,
            "reports": reports,
            "blocked_paths": [report["path"] for report in blocked],
        }

    @staticmethod
    def _blocked(path: str, reason: str) -> Dict[str, Any]:
        return {
            "path": path,
            "protected": True,
            "safe_for_ai_write": False,
            "reason": reason,
        }
