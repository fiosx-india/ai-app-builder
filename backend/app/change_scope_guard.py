"""
MarketVerse Lab
change_scope_guard.py

Purpose:
Hard safety boundary for AI-generated code changes.

This module ensures that:
1. Only explicitly affected files may be changed.
2. Only the requested change scope may be modified.
3. Unrelated code must remain unchanged.
4. Broad rewrites are rejected.
5. Deletions require explicit permission.
6. New files must be explicitly proposed.
7. Unexpected changes are rejected before application.
"""

from __future__ import annotations

import hashlib
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List


class ChangeScopeGuard:
    """
    Enforces the minimum-change principle.

    The guard does NOT decide what the AI should build.
    It decides whether the proposed change stays inside
    the approved scope.
    """

    MAX_CHANGE_RATIO = 0.40

    ALLOWED_ACTIONS = {
        "modify",
        "create",
    }

    def __init__(self, project_path: str) -> None:
        self.project_root = Path(project_path).resolve()

    def _safe_path(self, file_path: str) -> Path:
        """
        Prevent changes outside the project root.
        """
        candidate = (self.project_root / file_path).resolve()

        try:
            candidate.relative_to(self.project_root)
        except ValueError as exc:
            raise ValueError(
                f"Change rejected: path escapes project boundary: {file_path}"
            ) from exc

        return candidate

    @staticmethod
    def _hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def _change_ratio(old: str, new: str) -> float:
        if old == new:
            return 0.0

        if not old:
            return 1.0

        return 1.0 - SequenceMatcher(
            None,
            old,
            new,
        ).ratio()

    def inspect_change(
        self,
        change: Dict[str, Any],
        approved_files: List[str],
    ) -> Dict[str, Any]:
        """
        Inspect one proposed change.

        Returns a structured decision instead of modifying anything.
        """

        file_path = change.get("file")
        action = change.get("action")
        old_content = change.get("old_content")
        new_content = change.get("new_content")

        if not file_path:
            return self._reject(
                "Missing target file."
            )

        if not action:
            return self._reject(
                f"Missing action for {file_path}."
            )

        if action not in self.ALLOWED_ACTIONS:
            return self._reject(
                f"Action '{action}' is not allowed by the safety guard."
            )

        if file_path not in approved_files:
            return self._reject(
                f"File is outside the approved change scope: {file_path}"
            )

        path = self._safe_path(file_path)

        # ---------------------------------------------------------
        # CREATE
        # ---------------------------------------------------------

        if action == "create":
            if path.exists():
                return self._reject(
                    f"Create rejected: file already exists: {file_path}"
                )

            if not isinstance(new_content, str) or not new_content.strip():
                return self._reject(
                    f"Create rejected: new_content is empty: {file_path}"
                )

            return {
                "allowed": True,
                "action": "create",
                "file": file_path,
                "reason": "New file is explicitly inside the approved scope.",
                "change_ratio": 1.0,
            }

        # ---------------------------------------------------------
        # MODIFY
        # ---------------------------------------------------------

        if not path.exists():
            return self._reject(
                f"Modify rejected: target file does not exist: {file_path}"
            )

        if not isinstance(old_content, str):
            return self._reject(
                f"Modify rejected: exact old_content is required: {file_path}"
            )

        if not isinstance(new_content, str):
            return self._reject(
                f"Modify rejected: exact new_content is required: {file_path}"
            )

        try:
            current_content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            return self._reject(
                f"Modify rejected: target file is not UTF-8 text: {file_path}",
                error=str(exc),
            )

        # The AI must base its patch on the exact current content.
        if self._hash(current_content) != self._hash(current_content):
            return self._reject(
                f"Internal content verification failure: {file_path}"
            )

        # old_content must exist exactly.
        if old_content not in current_content:
            return self._reject(
                f"Modify rejected: exact old_content was not found: {file_path}"
            )

        # Replace ONLY the exact requested section.
        expected_content = current_content.replace(
            old_content,
            new_content,
            1,
        )

        # Safety check against accidental broad replacement.
        ratio = self._change_ratio(
            current_content,
            expected_content,
        )

        if ratio > self.MAX_CHANGE_RATIO:
            return self._reject(
                f"Modify rejected: proposed change is too broad "
                f"({ratio:.2%} of file content).",
                change_ratio=ratio,
            )

        return {
            "allowed": True,
            "action": "modify",
            "file": file_path,
            "reason": "Change is limited to the exact requested content.",
            "change_ratio": ratio,
            "current_hash": self._hash(current_content),
            "proposed_hash": self._hash(expected_content),
        }

    def inspect_plan(
        self,
        changes: List[Dict[str, Any]],
        approved_files: List[str],
    ) -> Dict[str, Any]:
        """
        Inspect the complete AI change plan.

        If ONE change violates the scope, the entire plan is rejected.
        Nothing is applied.
        """

        if not changes:
            return self._reject(
                "Change plan contains no changes."
            )

        results: List[Dict[str, Any]] = []

        for change in changes:
            result = self.inspect_change(
                change,
                approved_files,
            )

            results.append(result)

            if not result.get("allowed"):
                return {
                    "allowed": False,
                    "stage": "scope_guard",
                    "reason": result.get("reason"),
                    "failed_change": result,
                    "checked_changes": results,
                }

        return {
            "allowed": True,
            "stage": "scope_guard_passed",
            "checked_changes": results,
            "approved_files": approved_files,
            "change_count": len(changes),
        }

    @staticmethod
    def _reject(
        reason: str,
        **extra: Any,
    ) -> Dict[str, Any]:
        result = {
            "allowed": False,
            "stage": "scope_guard",
            "reason": reason,
        }

        result.update(extra)

        return result
