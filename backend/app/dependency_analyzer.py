from pathlib import Path
import ast
from typing import Any, Dict


class DependencyAnalyzer:
    """Extracts Python imports without crashing the workflow."""

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)

        if not path.exists() or not path.is_file():
            return {"file": str(path), "imports": [], "analyzed": False, "error": "File does not exist."}

        if path.suffix.lower() != ".py":
            return {
                "file": str(path),
                "imports": [],
                "analyzed": False,
                "skipped": True,
                "reason": "DependencyAnalyzer currently performs AST analysis for Python files only.",
            }

        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            return {"file": str(path), "imports": [], "analyzed": False, "error": str(exc)}

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)

        return {"file": str(path), "imports": sorted(set(imports)), "analyzed": True}
