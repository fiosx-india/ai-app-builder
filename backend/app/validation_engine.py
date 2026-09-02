from pathlib import Path
import ast


class ValidationEngine:

    def validate(self, project_path: str):

        root = Path(project_path)

        if not root.exists():
            return {
                "valid": False,
                "errors": [
                    {
                        "type": "project",
                        "message": "Project path does not exist.",
                    }
                ],
            }

        errors = []

        for file in root.rglob("*.py"):

            try:
                source = file.read_text(
                    encoding="utf-8"
                )

                ast.parse(source)

            except SyntaxError as error:

                errors.append(
                    {
                        "file": str(file),
                        "line": error.lineno,
                        "column": error.offset,
                        "message": error.msg,
                        "type": "syntax_error",
                    }
                )

        return {
            "valid": len(errors) == 0,
            "error_count": len(errors),
            "errors": errors,
        }
