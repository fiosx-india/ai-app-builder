import re
from typing import Any, Dict


class ErrorIntelligence:
    """
    Converts raw errors and tracebacks into
    structured diagnostics.
    """

    FILE_LINE_PATTERN = re.compile(
        r'File "([^"]+)", line (\d+)'
    )

    def analyze(
        self,
        error_text: str,
    ) -> Dict[str, Any]:

        text = error_text or ""

        matches = list(
            self.FILE_LINE_PATTERN.finditer(text)
        )

        file_path = None
        line = None

        if matches:

            match = matches[-1]

            file_path = match.group(1)
            line = int(match.group(2))

        error_type = self._detect_type(text)

        message = self._extract_message(
            text,
            error_type,
        )

        return {
            "type": error_type,
            "file": file_path,
            "line": line,
            "message": message,
            "cause": self._cause(
                error_type
            ),
            "impact": self._impact(
                error_type
            ),
            "suggested_action": (
                "Create a minimal localized fix, "
                "validate it, and run tests again."
            ),
            "raw_error": text,
        }

    def _detect_type(
        self,
        text: str,
    ) -> str:

        known = [
            "SyntaxError",
            "IndentationError",
            "NameError",
            "TypeError",
            "AttributeError",
            "ImportError",
            "ModuleNotFoundError",
            "KeyError",
            "ValueError",
        ]

        for error_type in known:

            if error_type in text:
                return error_type

        return "RuntimeError"

    def _extract_message(
        self,
        text: str,
        error_type: str,
    ) -> str:

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        for line in reversed(lines):

            if (
                error_type in line
                or line.startswith(error_type)
            ):
                return line

        return (
            lines[-1]
            if lines
            else "Unknown error."
        )

    def _cause(
        self,
        error_type: str,
    ) -> str:

        causes = {
            "SyntaxError":
                "Python source contains invalid syntax.",
            "IndentationError":
                "Python indentation is invalid.",
            "NameError":
                "Code references an undefined name.",
            "TypeError":
                "An operation received an incompatible type.",
            "AttributeError":
                "An object does not provide the requested attribute.",
            "ImportError":
                "A required import could not be resolved.",
            "ModuleNotFoundError":
                "A required module is unavailable.",
            "KeyError":
                "A requested dictionary key does not exist.",
            "ValueError":
                "A value is invalid for the requested operation.",
        }

        return causes.get(
            error_type,
            "The application produced an unexpected error.",
        )

    def _impact(
        self,
        error_type: str,
    ) -> str:

        if error_type in {
            "SyntaxError",
            "IndentationError",
        }:
            return (
                "The affected source cannot be executed "
                "until the syntax problem is fixed."
            )

        return (
            "The affected execution path may fail "
            "until the underlying problem is corrected."
        )
