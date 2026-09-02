from pathlib import Path
from typing import Any, Dict, List
import shutil
import tempfile
import uuid

from .patch_engine import PatchEngine
from .validation_pipeline import ValidationPipeline


class TransactionManager:
    """
    Applies a complete change set as a transaction.

    Flow:

    backup
      ↓
    validate patch
      ↓
    write change
      ↓
    validate project
      ↓
    tests
      ↓
    success OR rollback
    """

    def __init__(self) -> None:
        self.patch_engine = PatchEngine()
        self.validation = ValidationPipeline()

    def _create_backup(
        self,
        file_path: Path,
        transaction_id: str,
    ) -> Dict[str, str]:

        backup_root = Path(".ai_app_builder_backups") / transaction_id
        backup_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        backup_file = (
            backup_root
            / f"{uuid.uuid4().hex}.backup"
        )

        shutil.copy2(
            file_path,
            backup_file,
        )

        return {
            "source": str(file_path),
            "backup": str(backup_file),
        }

    def _restore(
        self,
        backups: List[Dict[str, str]],
    ) -> None:

        for item in backups:
            source = Path(item["source"])
            backup = Path(item["backup"])

            if backup.exists():
                shutil.copy2(
                    backup,
                    source,
                )

    def _atomic_write(
        self,
        file_path: Path,
        content: str,
    ) -> None:

        parent = file_path.parent

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=parent,
            delete=False,
        ) as temp:

            temp.write(content)
            temp.flush()

            temp_path = Path(
                temp.name
            )

        temp_path.replace(
            file_path
        )

    def apply(
        self,
        project_path: str,
        changes: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        if not changes:
            return {
                "success": False,
                "message": "No changes supplied.",
            }

        transaction_id = uuid.uuid4().hex

        backups: List[
            Dict[str, str]
        ] = []

        applied: List[str] = []

        try:

            # ---------------------------------
            # 1. Validate every change first.
            # ---------------------------------

            validated_changes = []

            for change in changes:

                relative_file = change["file"]

                target = (
                    Path(project_path)
                    / relative_file
                )

                old_content = change[
                    "old_content"
                ]

                new_content = change[
                    "new_content"
                ]

                validation = (
                    self.patch_engine.validate_patch(
                        str(target),
                        old_content,
                        new_content,
                        change.get("expected_hash"),
                    )
                )

                validated_changes.append(
                    {
                        "target": target,
                        "old_content": old_content,
                        "new_content": new_content,
                        "validation": validation,
                    }
                )

            # ---------------------------------
            # 2. Backup.
            # ---------------------------------

            for item in validated_changes:

                backup = self._create_backup(
                    item["target"],
                    transaction_id,
                )

                backups.append(backup)

            # ---------------------------------
            # 3. Apply atomically.
            # ---------------------------------

            for item in validated_changes:

                self._atomic_write(
                    item["target"],
                    item["new_content"],
                )

                applied.append(
                    str(item["target"])
                )

            # ---------------------------------
            # 4. Validate after modification.
            # ---------------------------------

            validation_result = (
                self.validation.run(
                    project_path
                )
            )

            if not validation_result[
                "valid"
            ]:

                self._restore(
                    backups
                )

                return {
                    "success": False,
                    "rolled_back": True,
                    "transaction_id": transaction_id,
                    "applied_files": applied,
                    "validation": validation_result,
                    "message": (
                        "Validation failed. "
                        "All changes were rolled back."
                    ),
                }

            # ---------------------------------
            # 5. Everything passed.
            # ---------------------------------

            return {
                "success": True,
                "rolled_back": False,
                "transaction_id": transaction_id,
                "applied_files": applied,
                "backups": backups,
                "validation": validation_result,
                "message": (
                    "Changes applied and "
                    "validation passed."
                ),
            }

        except Exception as exc:

            self._restore(
                backups
            )

            return {
                "success": False,
                "rolled_back": True,
                "transaction_id": transaction_id,
                "applied_files": applied,
                "error": str(exc),
                "message": (
                    "Transaction failed. "
                    "Changes were rolled back."
                ),
          }
