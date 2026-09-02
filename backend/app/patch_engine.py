from pathlib import Path
import difflib

class PatchEngine:
    MAX_CHANGE_RATIO = 0.40

    def validate_patch(self, file_path, old_content, new_content):
        path = Path(file_path)
        if not path.exists():
            raise ValueError(f"Target file does not exist: {file_path}")
        if old_content == new_content:
            raise ValueError("No change detected.")
        if not old_content:
            raise ValueError("Old content cannot be empty.")

        diff = list(difflib.unified_diff(
            old_content.splitlines(), new_content.splitlines(), lineterm=""
        ))
        baseline = max(len(old_content.splitlines()), 1)
        changed = sum(1 for line in diff if line.startswith("+") or line.startswith("-"))
        ratio = changed / baseline

        if ratio > self.MAX_CHANGE_RATIO:
            raise ValueError("Patch is too broad. Use a smaller localized change.")

        return {
            "approved_for_review": True,
            "file": str(path),
            "change_ratio": round(ratio, 4),
            "diff": diff,
        }
