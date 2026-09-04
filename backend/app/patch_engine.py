from pathlib import Path
import difflib
import hashlib
from typing import Dict, Any


class PatchEngine:
    """
    Safe localized patch validator.

    Supports:
    - Existing-file modifications.
    - New-file creation.
    - Exact original-content matching.
    - Optional SHA-256 integrity checks.
    - Empty/no-op change rejection.
    - Broad-change protection.

    This class validates changes only.
    It never writes files.
    """

    MAX_CHANGE_RATIO = 0.40

    @staticmethod
    def sha256(content: str) -> str:
        return hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest()

    def validate_patch(
        self,
        file_path: str,
        old_content: str,
        new_content: str,
        expected_hash: str | None = None,
        action: str = "modify",
    ) -> Dict[str, Any]:

        path = Path(file_path)

        if action not in {
            "modify",
            "create",
        }:
            raise ValueError(
                f"Unsupported patch action: {action}"
            )

        # --------------------------------------------------
        # CREATE
        # --------------------------------------------------

        if action == "create":

            if path.exists():
                raise ValueError(
                    f"Target file already exists: {file_path}"
                )

            if not new_content:
                raise ValueError(
                    "New file content cannot be empty."
                )

            if old_content not in {
                "",
                None,
            }:
                raise ValueError(
                    "New-file creation must not contain "
                    "old_content."
                )

            new_hash = self.sha256(
                new_content
            )

            return {
                "approved_for_review": True,
                "action": "create",
                "file": str(path),
                "change_ratio": 1.0,
                "changed_lines": len(
                    new_content.splitlines()
                ),
                "old_hash": None,
                "new_hash": new_hash,
                "diff": list(
                    difflib.unified_diff(
                        [],
                        new_content.splitlines(),
                        fromfile="/dev/null",
                        tofile=file_path,
                        lineterm="",
                    )
                ),
            }

        # --------------------------------------------------
        # MODIFY
        # --------------------------------------------------

        if not path.exists():
            raise ValueError(
                f"Target file does not exist: {file_path}"
            )

        current_content = path.read_text(
            encoding="utf-8"
        )

        # Protect against another process/change
        # modifying the file after the plan was created.
        if current_content != old_content:
            raise ValueError(
                f"Target file changed since planning: "
                f"{file_path}"
            )

        actual_hash = self.sha256(
            current_content
        )

        if (
            expected_hash
            and actual_hash != expected_hash
        ):
            raise ValueError(
                f"File integrity check failed: "
                f"{file_path}"
            )

        if old_content == new_content:
            raise ValueError(
                "No change detected."
            )

        if not old_content:
            raise ValueError(
                "Old content cannot be empty "
                "for a modification."
            )

        diff = list(
            difflib.unified_diff(
                old_content.splitlines(),
                new_content.splitlines(),
                fromfile=file_path,
                tofile=file_path,
                lineterm="",
            )
        )

        changed_lines = sum(
            1
            for line in diff
            if (
                line.startswith("+")
                or line.startswith("-")
            )
            and not line.startswith("+++")
            and not line.startswith("---")
        )

        baseline = max(
            len(old_content.splitlines()),
            1,
        )

        ratio = (
            changed_lines / baseline
        )

        if ratio > self.MAX_CHANGE_RATIO:
            raise ValueError(
                "Patch is too broad. "
                "Use a smaller localized change."
            )

        return {
            "approved_for_review": True,
            "action": "modify",
            "file": str(path),
            "change_ratio": round(
                ratio,
                4,
            ),
            "changed_lines": changed_lines,
            "old_hash": actual_hash,
            "new_hash": self.sha256(
                new_content
            ),
            "diff": diff,
        }
