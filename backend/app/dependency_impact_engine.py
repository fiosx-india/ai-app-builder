"""
MarketVerse Lab
dependency_impact_engine.py

Purpose:
Analyze the dependency impact of a proposed change.

This module does NOT modify files.
This module does NOT apply patches.
This module does NOT deploy applications.

It identifies which project files/modules may be affected
by a localized change.
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List, Set


class DependencyImpactEngine:
    """
    Determine the likely dependency impact of a change.

    Core rule:

        LOCAL CHANGE
             ↓
        DEPENDENCY ANALYSIS
             ↓
        IMPACTED FILES
             ↓
        VALIDATION SCOPE

    The engine must not expand a change unnecessarily.
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

    def analyze(
        self,
        project_path: str,
        changed_file: str,
    ) -> Dict[str, Any]:
        """
        Analyze which Python files import or depend on the
        changed file.

        Returns a structured impact report.
        """

        root = Path(project_path)

        if not root.exists():
            raise ValueError(
                f"Project path does not exist: {project_path}"
            )

        if not root.is_dir():
            raise ValueError(
                f"Project path is not a directory: {project_path}"
            )

        if not changed_file.strip():
            raise ValueError(
                "Changed file cannot be empty."
            )

        normalized_changed = self._normalize_path(
            changed_file
        )

        python_files = self._collect_python_files(root)

        direct_dependents: Set[str] = set()
        direct_dependencies: Set[str] = set()

        for file_path in python_files:

            relative_path = self._relative_path(
                root,
                file_path,
            )

            if relative_path == normalized_changed:
                direct_dependencies.update(
                    self._extract_imports(
                        file_path
                    )
                )
                continue

            imports = self._extract_imports(
                file_path
            )

            if self._imports_changed_file(
                imports,
                normalized_changed,
            ):
                direct_dependents.add(
                    relative_path
                )

        impacted_files = sorted(
            set(direct_dependents)
            | {normalized_changed}
        )

        return {
            "changed_file": normalized_changed,
            "direct_dependencies": sorted(
                direct_dependencies
            ),
            "direct_dependents": sorted(
                direct_dependents
            ),
            "impacted_files": impacted_files,
            "impact_count": len(impacted_files),
            "whole_project_impact": False,
            "analysis_complete": True,
        }

    def _collect_python_files(
        self,
        root: Path,
    ) -> List[Path]:

        files: List[Path] = []

        for path in root.rglob("*.py"):

            if any(
                part in self.IGNORED_DIRECTORIES
                for part in path.parts
            ):
                continue

            if path.is_file():
                files.append(path)

        return files

    def _extract_imports(
        self,
        file_path: Path,
    ) -> Set[str]:

        imports: Set[str] = set()

        try:
            source = file_path.read_text(
                encoding="utf-8"
            )

            tree = ast.parse(source)

        except (
            SyntaxError,
            UnicodeDecodeError,
            OSError,
        ):
            return imports

        for node in ast.walk(tree):

            if isinstance(node, ast.Import):

                for alias in node.names:
                    imports.add(alias.name)

            elif isinstance(node, ast.ImportFrom):

                if node.module:
                    imports.add(node.module)

        return imports

    def _imports_changed_file(
        self,
        imports: Set[str],
        changed_file: str,
    ) -> bool:

        module_name = changed_file

        if module_name.endswith(".py"):
            module_name = module_name[:-3]

        module_name = module_name.replace(
            "/",
            ".",
        ).replace(
            "\\",
            ".",
        )

        for imported in imports:

            if imported == module_name:
                return True

            if imported.startswith(
                module_name + "."
            ):
                return True

            if module_name.startswith(
                imported + "."
            ):
                return True

        return False

    @staticmethod
    def _normalize_path(
        file_path: str,
    ) -> str:

        return (
            str(file_path)
            .replace("\\", "/")
            .lstrip("./")
        )

    @staticmethod
    def _relative_path(
        root: Path,
        file_path: Path,
    ) -> str:

        return str(
            file_path.relative_to(root)
        ).replace(
            "\\",
            "/",
        )

    def summarize(
        self,
        impact: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Produce a concise impact summary for the planner.
        """

        impacted = impact.get(
            "impacted_files",
            [],
        )

        return {
            "changed_file": impact.get(
                "changed_file"
            ),
            "impact_count": len(impacted),
            "impacted_files": impacted,
            "localized": len(impacted) <= 5,
            "requires_dependency_review": (
                len(impacted) > 1
            ),
            "whole_project_change_required": False,
              }
