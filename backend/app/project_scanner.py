from pathlib import Path
from typing import Any, Dict, List


class ProjectScanner:
    """Safely scans a project and returns lightweight project intelligence."""

    IGNORED_DIRECTORIES = {
        ".git", ".venv", "venv", "__pycache__", "node_modules",
        ".next", "dist", "build",
    }

    LANGUAGE_BY_EXTENSION = {
        ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript",
        ".ts": "TypeScript", ".tsx": "TypeScript", ".java": "Java",
        ".kt": "Kotlin", ".dart": "Dart", ".php": "PHP",
        ".go": "Go", ".rs": "Rust", ".cs": "C#",
    }

    DEPENDENCY_FILES = {
        "requirements.txt": "python_requirements",
        "pyproject.toml": "python_pyproject",
        "poetry.lock": "python_poetry_lock",
        "package.json": "node_package",
        "pnpm-lock.yaml": "node_pnpm_lock",
        "yarn.lock": "node_yarn_lock",
        "pom.xml": "maven",
        "build.gradle": "gradle",
        "build.gradle.kts": "gradle_kotlin",
        "pubspec.yaml": "flutter",
    }

    ENTRYPOINT_CANDIDATES = (
        "main.py", "app.py", "manage.py", "server.py",
        "main.js", "server.js", "index.js", "main.ts", "index.ts",
        "main.dart",
    )

    def _detect_frameworks(self, paths: set[str]) -> List[str]:
        frameworks = []
        if "manage.py" in paths:
            frameworks.append("Django")
        if "main.py" in paths or "app.py" in paths:
            frameworks.append("Python application (candidate; verify dependencies)")
        if "package.json" in paths:
            frameworks.append("Node.js/JavaScript project")
        if "pubspec.yaml" in paths:
            frameworks.append("Flutter/Dart project")
        if "pom.xml" in paths:
            frameworks.append("Maven/Java project")
        if "build.gradle" in paths or "build.gradle.kts" in paths:
            frameworks.append("Gradle project")
        return frameworks

    def scan(self, project_path: str, max_files: int = 1000) -> Dict[str, Any]:
        root = Path(project_path).resolve()

        if not root.exists():
            raise ValueError(f"Project path does not exist: {project_path}")
        if not root.is_dir():
            raise ValueError(f"Project path is not a directory: {project_path}")

        files: List[Dict[str, Any]] = []
        languages = set()
        dependency_files = []
        relative_paths = set()

        for path in root.rglob("*"):
            if len(files) >= max_files:
                break
            if not path.is_file():
                continue
            relative_path = path.relative_to(root)
            if any(part in self.IGNORED_DIRECTORIES for part in relative_path.parts):
                continue

            relative = str(relative_path)
            suffix = path.suffix.lower()
            relative_paths.add(relative)

            if suffix in self.LANGUAGE_BY_EXTENSION:
                languages.add(self.LANGUAGE_BY_EXTENSION[suffix])
            if path.name in self.DEPENDENCY_FILES:
                dependency_files.append({
                    "path": relative,
                    "type": self.DEPENDENCY_FILES[path.name],
                })

            files.append({
                "path": relative,
                "extension": suffix,
                "size": path.stat().st_size,
            })

        entry_points = [
            p for p in relative_paths
            if Path(p).name in self.ENTRYPOINT_CANDIDATES
        ]

        return {
            "project_path": str(root),
            "file_count": len(files),
            "files": files,
            "intelligence": {
                "languages": sorted(languages),
                "frameworks": self._detect_frameworks(relative_paths),
                "dependency_files": dependency_files,
                "entry_points": sorted(entry_points),
            },
        }
