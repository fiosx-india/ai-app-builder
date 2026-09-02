from pathlib import Path


class PatchEngine:

    PROTECTED_RULES = {
        "full_file_rewrite": False,
        "delete_project": False,
        "delete_unrelated_files": False,
    }

    def validate_patch(
        self,
        file_path: str,
        old_content: str,
        new_content: str,
    ):

        path = Path(file_path)

        if not path.exists():
            raise ValueError(
                f"Target file does not exist: {file_path}"
            )

        if not old_content.strip():
            raise ValueError(
                "Old content cannot be empty."
            )

        if old_content not in new_content:
            raise ValueError(
                "Patch validation failed. "
                "The original code was not preserved."
            )

        return {
            "approved_for_review": True,
            "file": str(path),
            "message": (
                "Patch is limited to the specified file. "
                "Full project rewrite is prohibited."
            ),
        }
