"""
MarketVerse Lab
change_manifest.py

Purpose:
Define a strict, auditable manifest for every proposed
application change.

This module does NOT modify files.
This module does NOT apply patches.
This module does NOT deploy applications.

It describes exactly what the AI intends to change.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ChangeItem:
    """
    Represents one localized file change.
    """

    file: str
    action: str
    target: str
    description: str

    old_content: Optional[str] = None
    new_content: Optional[str] = None

    expected_hash: Optional[str] = None

    risk: str = "medium"

    validation_steps: List[str] = field(default_factory=list)

    destructive: bool = False
    requires_approval: bool = True

    metadata: Dict[str, Any] = field(default_factory=dict)


class ChangeManifest:
    """
    Strict container for proposed application changes.

    Core rule:

        AI may propose changes,
        but this manifest does not apply them.

    Every change must identify the exact target and intended action.
    """

    VALID_ACTIONS = {
        "modify",
        "create",
        "delete",
    }

    VALID_RISK_LEVELS = {
        "low",
        "medium",
        "high",
        "critical",
    }

    def __init__(
        self,
        *,
        project_path: str,
        command: str,
    ) -> None:

        if not project_path.strip():
            raise ValueError("Project path cannot be empty.")

        if not command.strip():
            raise ValueError("Command cannot be empty.")

        self.project_path = project_path
        self.command = command

        self.changes: List[ChangeItem] = []

        self.metadata: Dict[str, Any] = {
            "change_count": 0,
            "destructive_changes": 0,
            "approval_required": True,
        }

    def add_change(self, change: ChangeItem) -> Dict[str, Any]:
        """
        Add one proposed change after validating its scope.
        """

        self._validate_change(change)

        self.changes.append(change)

        self._refresh_metadata()

        return self.serialize()

    def add_from_dict(
        self,
        change: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Add a change received from an AI-generated JSON proposal.
        """

        if not isinstance(change, dict):
            raise ValueError("Change must be a dictionary.")

        item = ChangeItem(
            file=str(change.get("file", "")).strip(),
            action=str(change.get("action", "")).strip().lower(),
            target=str(change.get("target", "")).strip(),
            description=str(
                change.get("description", "")
            ).strip(),

            old_content=change.get("old_content"),
            new_content=change.get("new_content"),

            expected_hash=change.get("expected_hash"),

            risk=str(
                change.get("risk", "medium")
            ).strip().lower(),

            validation_steps=list(
                change.get("validation_steps", [])
            ),

            destructive=bool(
                change.get("destructive", False)
            ),

            requires_approval=bool(
                change.get("requires_approval", True)
            ),

            metadata=dict(
                change.get("metadata", {})
            ),
        )

        return self.add_change(item)

    def _validate_change(
        self,
        change: ChangeItem,
    ) -> None:

        if not change.file.strip():
            raise ValueError(
                "Every change must identify an exact file."
            )

        if not change.target.strip():
            raise ValueError(
                f"Change target is missing for file: {change.file}"
            )

        if not change.description.strip():
            raise ValueError(
                f"Change description is missing for file: {change.file}"
            )

        if change.action not in self.VALID_ACTIONS:
            raise ValueError(
                f"Unsupported change action: {change.action}"
            )

        if change.risk not in self.VALID_RISK_LEVELS:
            raise ValueError(
                f"Unsupported risk level: {change.risk}"
            )

        if change.action == "modify":
            if change.old_content is None:
                raise ValueError(
                    f"Modify operation requires old_content: "
                    f"{change.file}"
                )

            if change.new_content is None:
                raise ValueError(
                    f"Modify operation requires new_content: "
                    f"{change.file}"
                )

        if change.action == "create":
            if change.new_content is None:
                raise ValueError(
                    f"Create operation requires new_content: "
                    f"{change.file}"
                )

        if change.action == "delete":
            change.destructive = True

        if change.destructive:
            change.requires_approval = True

    def _refresh_metadata(self) -> None:

        self.metadata["change_count"] = len(self.changes)

        self.metadata["destructive_changes"] = sum(
            1
            for change in self.changes
            if change.destructive
        )

        self.metadata["approval_required"] = any(
            change.requires_approval
            for change in self.changes
        )

    def validate(self) -> Dict[str, Any]:
        """
        Validate the complete manifest.

        No files are modified.
        """

        errors: List[str] = []

        for index, change in enumerate(self.changes):
            try:
                self._validate_change(change)
            except ValueError as exc:
                errors.append(
                    f"change[{index}]: {exc}"
                )

        return {
            "valid": not errors,
            "project_path": self.project_path,
            "change_count": len(self.changes),
            "errors": errors,
        }

    def serialize(self) -> Dict[str, Any]:
        """
        Return a JSON-compatible representation.
        """

        self._refresh_metadata()

        return {
            "project_path": self.project_path,
            "command": self.command,
            "changes": [
                asdict(change)
                for change in self.changes
            ],
            "metadata": dict(self.metadata),
        }

    def is_destructive(self) -> bool:
        return any(
            change.destructive
            for change in self.changes
        )

    def requires_approval(self) -> bool:
        return any(
            change.requires_approval
            for change in self.changes
        )
