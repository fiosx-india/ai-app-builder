from pathlib import Path
from typing import Any, Dict, List
import shutil


class RollbackManager:
    """
    Explicit rollback service.
    """

    def rollback(
        self,
        backups: List[Dict[str, str]],
    ) -> Dict[str, Any]:

        restored = []
        errors = []

        for item in backups:

            source = Path(
                item["source"]
            )

            backup = Path(
                item["backup"]
            )

            try:

                if not backup.exists():
                    errors.append(
                        f"Backup missing: {backup}"
                    )
                    continue

                shutil.copy2(
                    backup,
                    source,
                )

                restored.append(
                    str(source)
                )

            except Exception as exc:

                errors.append(
                    f"{source}: {exc}"
                )

        return {
            "rolled_back": (
                len(errors) == 0
            ),
            "restored_files": restored,
            "errors": errors,
        }
