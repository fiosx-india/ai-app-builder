from pathlib import Path
import ast

class ValidationEngine:
    def validate(self, project_path: str):
        root = Path(project_path)
        if not root.exists():
            return {"valid": False, "error_count": 1, "errors": [{
                "type": "project", "file": str(root), "line": None,
                "message": "Project path does not exist."
            }]}

        errors = []
        for file in root.rglob("*.py"):
            try:
                ast.parse(file.read_text(encoding="utf-8"))
            except SyntaxError as error:
                errors.append({
                    "file": str(file), "line": error.lineno,
                    "column": error.offset, "message": error.msg,
                    "type": "syntax_error",
                    "cause": "Python source could not be parsed.",
                    "impact": "Affected file cannot be safely executed."
                })
        return {"valid": len(errors) == 0, "error_count": len(errors), "errors": errors}
