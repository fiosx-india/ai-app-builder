"""
MarketVerse Lab
change_scope_guard.py

Purpose:
Hard boundary for AI-generated changes.

This module decides whether a proposed change is
inside the explicitly approved scope.

It does NOT modify files.
It does NOT deploy anything.
It does NOT replace PatchEngine.

PatchEngine validates the actual patch.
ChangeScopeGuard validates the allowed scope.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


class ChangeScopeGuard:
    """
    Prevents AI from expanding a requested change
    beyond its approved scope.
    """

    ALLOWED_ACTIONS = {
        "modify",
        "create",
    }

    def __init__(self, project_path: str) -> None:
        self.project_root = Path(project_path).resolve()

    def _safe_path(self, file_path: str) -> Path:
        candidate = (self.project_root / file_path).resolve()

        try:
            candidate.relative_to(self.project_root)
        except ValueError as exc:
            raise ValueError(
                f"Change rejected: path escapes project root: {file_path}"
            ) from exc

        return candidate

    def inspect_change(
        self,
        change: Dict[str, Any],
        approved_files: List[str],
    ) -> Dict[str, Any]:

        file_path = change.get("file")
        action = change.get("action")

        if not file_path:
            return self._reject(
                "Change does not identify a target file."
            )

        if not action:
            return self._reject(
                f"Change action is missing for: {file_path}"
            )

        if action not in self.ALLOWED_ACTIONS:
            return self._reject(
                f"Action '{action}' is not allowed: {file_path}"
            )

        if file_path not in approved_files:
            return self._reject(
                f"Change is outside approved scope: {file_path}"
            )

        self._safe_path(file_path)

        if action == "create":
            return self._inspect_create(
                file_path,
                change,
            )

        return self._inspect_modify(
            file_path,
            change,
        )

    def _inspect_create(
        self,
        file_path: str,
        change: Dict[str, Any],
    ) -> Dict[str, Any]:

        path = self._safe_path(file_path)

        if path.exists():
            return self._reject(
                f"Create rejected because file already exists: {file_path}"
            )

        new_content = change.get("new_content")

        if not isinstance(new_content, str):
            return self._reject(
                f"New file must contain explicit new_content: {file_path}"
            )

        if not new_content.strip():
            return self._reject(
                f"New file cannot be empty: {file_path}"
            )

        return {
            "allowed": True,
            "action": "create",
            "file": file_path,
            "reason": (
                "New file is explicitly included in the approved scope."
            ),
        }

    def _inspect_modify(
        self,
        file_path: str,
        change: Dict[str, Any],
    ) -> Dict[str, Any]:

        path = self._safe_path(file_path)

        if not path.exists():
            return self._reject(
                f"Modify rejected because file does not exist: {file_path}"
            )

        old_content = change.get("old_content")
        new_content = change.get("new_content")

        if not isinstance(old_content, str):
            return self._reject(
                f"Modify requires exact old_content: {file_path}"
            )

        if not isinstance(new_content, str):
            return self._reject(
                f"Modify requires exact new_content: {file_path}"
            )

        if not old_content:
            return self._reject(
                f"Modify cannot use empty old_content: {file_path}"
            )

        if old_content == new_content:
            return self._reject(
                f"No actual change was proposed: {file_path}"
            )

        current_content = path.read_text(
            encoding="utf-8"
        )

        if old_content not in current_content:
            return self._reject(
                "Exact old_content was not found in the current file.",
                file=file_path,
            )

        return {
            "allowed": True,
            "action": "modify",
            "file": file_path,
            "reason": (
                "Target file is inside the approved scope and "
                "contains the exact requested source section."
            ),
        }

    def inspect_plan(
        self,
        changes: List[Dict[str, Any]],
        approved_files: List[str],
    ) -> Dict[str, Any]:

        if not changes:
            return self._reject(
                "No changes were proposed."
            )

        if not approved_files:
            return self._reject(
                "No files were approved for modification."
            )

        checked: List[Dict[str, Any]] = []

        for change in changes:
            result = self.inspect_change(
                change,
                approved_files,
            )

            checked.append(result)

            # ONE unsafe change rejects the ENTIRE plan.
            if not result.get("allowed"):
                return {
                    "allowed": False,
                    "stage": "scope_guard_failed",
                    "reason": result.get("reason"),
                    "failed_change": result,
                    "checked_changes": checked,
                }

        return {
            "allowed": True,
            "stage": "scope_guard_passed",
            "approved_files": approved_files,
            "checked_changes": checked,
            "change_count": len(changes),
        }

    @staticmethod
    def _reject(
        reason: str,
        **extra: Any,
    ) -> Dict[str, Any]:

        result = {
            "allowed": False,
            "stage": "scope_guard_failed",
            "reason": reason,
        }

        result.update(extra)

        return result
