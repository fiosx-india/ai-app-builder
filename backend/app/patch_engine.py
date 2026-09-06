from pathlib import Path
import difflib
import hashlib
from typing import Dict, Any


class PatchEngine:
    """Safe localized patch validator. Validation only; never writes files."""

    MAX_CHANGE_RATIO = 0.40
    SMALL_FILE_LINE_THRESHOLD = 10
    SMALL_FILE_MAX_CHANGED_OPERATIONS = 2
    MAX_CHANGED_OPERATIONS = 3

    @staticmethod
    def sha256(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    @staticmethod
    def _logical_change_metrics(old_content: str, new_content: str) -> Dict[str, Any]:
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)

        operations = []
        changed_old_lines = 0
        changed_new_lines = 0

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                continue
            operations.append({
                "operation": tag,
                "old_start": i1 + 1,
                "old_end": i2,
                "new_start": j1 + 1,
                "new_end": j2,
            })
            changed_old_lines += i2 - i1
            changed_new_lines += j2 - j1

        # A replacement should count as one logical changed area, not
        # two changes merely because diff has one '-' and one '+' line.
        changed_lines = max(changed_old_lines, changed_new_lines)
        baseline = max(len(old_lines), len(new_lines), 1)

        return {
            "changed_lines": changed_lines,
            "changed_operations": len(operations),
            "changed_ranges": operations,
            "change_ratio": changed_lines / baseline,
        }

    def validate_patch(
        self,
        file_path: str,
        old_content: str,
        new_content: str,
        expected_hash: str | None = None,
        action: str = "modify",
    ) -> Dict[str, Any]:

        path = Path(file_path)

        if action not in {"modify", "create"}:
            raise ValueError(f"Unsupported patch action: {action}")

        if action == "create":
            if path.exists():
                raise ValueError(f"Target file already exists: {file_path}")
            if not isinstance(new_content, str) or not new_content.strip():
                raise ValueError("New file content cannot be empty.")
            if old_content not in {"", None}:
                raise ValueError("New-file creation must not contain old_content.")

            return {
                "approved_for_review": True,
                "action": "create",
                "file": str(path),
                "change_ratio": 1.0,
                "changed_lines": len(new_content.splitlines()),
                "changed_operations": 1,
                "changed_ranges": [],
                "old_hash": None,
                "new_hash": self.sha256(new_content),
                "diff": list(difflib.unified_diff(
                    [], new_content.splitlines(),
                    fromfile="/dev/null", tofile=file_path, lineterm=""
                )),
            }

        if not path.exists():
            raise ValueError(f"Target file does not exist: {file_path}")

        current_content = path.read_text(encoding="utf-8")

        if current_content != old_content:
            raise ValueError(f"Target file changed since planning: {file_path}")

        actual_hash = self.sha256(current_content)

        if expected_hash and actual_hash != expected_hash:
            raise ValueError(f"File integrity check failed: {file_path}")

        if old_content == new_content:
            raise ValueError("No change detected.")

        if not old_content:
            raise ValueError("Old content cannot be empty for a modification.")

        metrics = self._logical_change_metrics(old_content, new_content)
        total_lines = max(len(old_content.splitlines()), 1)

        if total_lines <= self.SMALL_FILE_LINE_THRESHOLD:
            if metrics["changed_operations"] > self.SMALL_FILE_MAX_CHANGED_OPERATIONS:
                raise ValueError("Patch is too broad. Use a smaller localized change.")
        else:
            if metrics["changed_operations"] > self.MAX_CHANGED_OPERATIONS:
                raise ValueError("Patch changes too many separate sections.")
            if metrics["change_ratio"] > self.MAX_CHANGE_RATIO:
                raise ValueError("Patch is too broad. Use a smaller localized change.")

        diff = list(difflib.unified_diff(
            old_content.splitlines(), new_content.splitlines(),
            fromfile=file_path, tofile=file_path, lineterm=""
        ))

        return {
            "approved_for_review": True,
            "action": "modify",
            "file": str(path),
            "change_ratio": round(metrics["change_ratio"], 4),
            "changed_lines": metrics["changed_lines"],
            "changed_operations": metrics["changed_operations"],
            "changed_ranges": metrics["changed_ranges"],
            "old_hash": actual_hash,
            "new_hash": self.sha256(new_content),
            "diff": diff,
        }
