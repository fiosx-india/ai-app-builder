from pathlib import Path
from typing import Any, Dict, List


class ProjectScanner:
    """
    Safely scans a project without modifying files.
    """

    IGNORED_DIRECTORIES = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "node_modules",
        ".next",
        "dist",
        "build",
    }

    def scan(
        self,
        project_path: str,
        max_files: int = 1000,
    ) -> Dict[str, Any]:

        root = Path(project_path)

        if not root.exists():
            raise ValueError(
                f"Project path does not exist: {project_path}"
            )

        if not root.is_dir():
            raise ValueError(
                f"Project path is not a directory: {project_path}"
            )

        files: List[Dict[str, Any]] = []

        for path in root.rglob("*"):

            if len(files) >= max_files:
                break

            if not path.is_file():
                continue

            if any(
                part in self.IGNORED_DIRECTORIES
                for part in path.parts
            ):
                continue

            relative_path = path.relative_to(root)

            files.append(
                {
                    "path": str(relative_path),
                    "extension": path.suffix.lower(),
                    "size": path.stat().st_size,
                }
            )

        return {
            "project_path": str(root),
            "file_count": len(files),
            "files": files,
        }
