from pathlib import Path
from typing import Any, Dict, List
import shutil
import tempfile
import uuid

from .patch_engine import PatchEngine
from .validation_pipeline import ValidationPipeline


class TransactionManager:
    """Applies a complete change set atomically with rollback."""

    def __init__(self) -> None:
        self.patch_engine = PatchEngine()
        self.validation = ValidationPipeline()

    def _create_backup(self, file_path: Path, transaction_id: str) -> Dict[str, str]:
        backup_root = Path(".ai_app_builder_backups") / transaction_id
        backup_root.mkdir(parents=True, exist_ok=True)
        backup_file = backup_root / f"{uuid.uuid4().hex}.backup"
        shutil.copy2(file_path, backup_file)
        return {"source": str(file_path), "backup": str(backup_file), "action": "modify"}

    def _restore(self, backups: List[Dict[str, str]], created_files: List[Path]) -> None:
        for created in reversed(created_files):
            if created.exists():
                created.unlink()

        for item in reversed(backups):
            source = Path(item["source"])
            backup = Path(item["backup"])
            if backup.exists():
                source.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup, source)

    def _atomic_write(self, file_path: Path, content: str) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=file_path.parent, delete=False
        ) as temp:
            temp.write(content)
            temp.flush()
            temp_path = Path(temp.name)
        temp_path.replace(file_path)

    def apply(self, project_path: str, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not changes:
            return {"success": False, "message": "No changes supplied."}

        root = Path(project_path).resolve()
        if not root.exists() or not root.is_dir():
            return {"success": False, "message": "Invalid project path."}

        transaction_id = uuid.uuid4().hex
        backups: List[Dict[str, str]] = []
        created_files: List[Path] = []
        applied: List[str] = []

        try:
            validated_changes = []

            # Validate every change before writing anything.
            for change in changes:
                relative_file = change["file"]
                target = (root / relative_file).resolve()

                try:
                    target.relative_to(root)
                except ValueError as exc:
                    raise ValueError(f"Change escapes project root: {relative_file}") from exc

                action = change.get("action", "modify")
                old_content = change.get("old_content", "")
                new_content = change.get("new_content")

                if not isinstance(new_content, str):
                    raise ValueError(f"new_content must be a string: {relative_file}")

                validation = self.patch_engine.validate_patch(
                    str(target),
                    old_content,
                    new_content,
                    change.get("expected_hash"),
                    action=action,
                )

                validated_changes.append({
                    "target": target,
                    "action": action,
                    "old_content": old_content,
                    "new_content": new_content,
                    "validation": validation,
                })

            # Back up only files that already exist.
            for item in validated_changes:
                if item["action"] == "modify":
                    backups.append(self._create_backup(item["target"], transaction_id))

            # Apply atomically.
            for item in validated_changes:
                target = item["target"]
                if item["action"] == "create":
                    created_files.append(target)
                self._atomic_write(target, item["new_content"])
                applied.append(str(target))

            validation_result = self.validation.run(str(root))

            if not validation_result.get("valid"):
                self._restore(backups, created_files)
                return {
                    "success": False,
                    "rolled_back": True,
                    "transaction_id": transaction_id,
                    "applied_files": applied,
                    "validation": validation_result,
                    "message": "Validation failed. All changes were rolled back.",
                }

            return {
                "success": True,
                "rolled_back": False,
                "transaction_id": transaction_id,
                "applied_files": applied,
                "backups": backups,
                "created_files": [str(p) for p in created_files],
                "validation": validation_result,
                "message": "Changes applied and validation passed.",
            }

        except Exception as exc:
            self._restore(backups, created_files)
            return {
                "success": False,
                "rolled_back": True,
                "transaction_id": transaction_id,
                "applied_files": applied,
                "error": str(exc),
                "message": "Transaction failed. Changes were rolled back.",
            }
