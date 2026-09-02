from pathlib import Path
import difflib
import hashlib
from typing import Dict, Any


class PatchEngine:
    """
    Safe localized patch validator.

    Rules:
    - Target file must exist.
    - Expected original content must match.
    - Empty/no-op changes are rejected.
    - Excessively broad changes are rejected.
    - This class does not write files.
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
    ) -> Dict[str, Any]:

        path = Path(file_path)

        if not path.exists():
            raise ValueError(
                f"Target file does not exist: {file_path}"
            )

        current_content = path.read_text(
            encoding="utf-8"
        )

        # Protect against another process/change modifying
        # the file after the plan was created.
        if current_content != old_content:
            raise ValueError(
                f"Target file changed since planning: {file_path}"
            )

        actual_hash = self.sha256(
            current_content
        )

        if expected_hash and actual_hash != expected_hash:
            raise ValueError(
                f"File integrity check failed: {file_path}"
            )

        if old_content == new_content:
            raise ValueError(
                "No change detected."
            )

        if not old_content:
            raise ValueError(
                "Old content cannot be empty."
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

        ratio = changed_lines / baseline

        if ratio > self.MAX_CHANGE_RATIO:
            raise ValueError(
                "Patch is too broad. "
                "Use a smaller localized change."
            )

        return {
            "approved_for_review": True,
            "file": str(path),
            "change_ratio": round(ratio, 4),
            "changed_lines": changed_lines,
            "old_hash": actual_hash,
            "new_hash": self.sha256(new_content),
            "diff": diff,
        }
