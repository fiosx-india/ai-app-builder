from pathlib import Path
import ast
from typing import Any, Dict


class ValidationEngine:
    """
    Performs non-destructive source validation.

    Current implementation provides Python syntax validation.
    """

    def validate(
        self,
        project_path: str,
    ) -> Dict[str, Any]:

        root = Path(project_path)

        if not root.exists():
            return {
                "valid": False,
                "error_count": 1,
                "errors": [
                    {
                        "type": "project",
                        "file": str(root),
                        "line": None,
                        "column": None,
                        "message": (
                            "Project path does not exist."
                        ),
                        "cause": (
                            "The supplied project directory "
                            "could not be found."
                        ),
                        "impact": (
                            "The project cannot be validated."
                        ),
                    }
                ],
            }

        errors = []

        for file in root.rglob("*.py"):

            if any(
                part in {
                    ".git",
                    ".venv",
                    "venv",
                    "__pycache__",
                }
                for part in file.parts
            ):
                continue

            try:

                source = file.read_text(
                    encoding="utf-8"
                )

                ast.parse(source)

            except SyntaxError as error:

                errors.append(
                    {
                        "type": "syntax_error",
                        "file": str(file),
                        "line": error.lineno,
                        "column": error.offset,
                        "message": error.msg,
                        "cause": (
                            "Python source could not "
                            "be parsed."
                        ),
                        "impact": (
                            "The affected file cannot "
                            "be safely executed."
                        ),
                    }
                )

            except UnicodeDecodeError as error:

                errors.append(
                    {
                        "type": "encoding_error",
                        "file": str(file),
                        "line": None,
                        "column": None,
                        "message": str(error),
                        "cause": (
                            "The file is not valid UTF-8."
                        ),
                        "impact": (
                            "The source cannot be "
                            "reliably analyzed."
                        ),
                    }
                )

        return {
            "valid": len(errors) == 0,
            "error_count": len(errors),
            "errors": errors,
        }
