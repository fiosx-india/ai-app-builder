"""
MarketVerse Lab
root_cause_engine.py

Purpose:
Identify the probable root cause of a project error.

This module does NOT modify files.
This module does NOT apply patches.
This module only analyzes errors and proposes a precise scope.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Optional


class RootCauseEngine:
    """
    Analyze an error and identify its probable root cause.

    Core safety rule:

        ERROR
          ↓
        LOCATE
          ↓
        IDENTIFY ROOT CAUSE
          ↓
        DEFINE MINIMAL SCOPE
          ↓
        REPAIR PROPOSAL

    The engine must never assume that the entire project is broken.
    """

    TRACEBACK_PATTERN = re.compile(
        r'File "([^"]+)", line (\d+)(?:, in ([^\n]+))?'
    )

    SYNTAX_PATTERN = re.compile(
        r"SyntaxError:\s*(.+)"
    )

    IMPORT_PATTERN = re.compile(
        r"(?:ModuleNotFoundError|ImportError):\s*(.+)"
    )

    NAME_PATTERN = re.compile(
        r"NameError:\s*(.+)"
    )

    TYPE_PATTERN = re.compile(
        r"TypeError:\s*(.+)"
    )

    def analyze(
        self,
        error: Dict[str, Any],
        project_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a structured error report.

        Returns:
        - error type
        - exact file
        - line
        - probable cause
        - impact
        - repair scope
        - suggested next action
        """

        if not isinstance(error, dict):
            raise ValueError("Error must be a dictionary.")

        message = str(
            error.get("message")
            or error.get("error")
            or error.get("detail")
            or ""
        ).strip()

        traceback = str(
            error.get("traceback")
            or error.get("output")
            or ""
        )

        error_type = str(
            error.get("type")
            or error.get("error_type")
            or ""
        ).strip()

        location = self._extract_location(
            error,
            traceback,
            project_path,
        )

        if not error_type:
            error_type = self._detect_error_type(
                message,
                traceback,
            )

        cause = self._determine_cause(
            error_type,
            message,
        )

        impact = self._determine_impact(
            error_type,
            location,
        )

        scope = self._determine_scope(
            error_type,
            location,
        )

        return {
            "root_cause_found": bool(location["file"] or message),
            "error_type": error_type or "UnknownError",
            "message": message,
            "location": location,
            "probable_cause": cause,
            "impact": impact,
            "repair_scope": scope,
            "whole_project_change_allowed": False,
            "suggested_action": self._suggest_action(
                error_type
            ),
        }

    def _extract_location(
        self,
        error: Dict[str, Any],
        traceback: str,
        project_path: Optional[str],
    ) -> Dict[str, Any]:

        file_path = error.get("file")
        line = error.get("line")
        column = error.get("column")
        function = error.get("function")

        match = self.TRACEBACK_PATTERN.search(traceback)

        if match:
            file_path = file_path or match.group(1)
            line = line or int(match.group(2))
            function = function or match.group(3)

        if file_path and project_path:
            try:
                path = Path(str(file_path))
                root = Path(project_path)

                if path.is_absolute():
                    file_path = str(path.relative_to(root))
            except (ValueError, OSError):
                pass

        return {
            "file": str(file_path) if file_path else None,
            "line": int(line) if line is not None else None,
            "column": int(column) if column is not None else None,
            "function": function,
        }

    def _detect_error_type(
        self,
        message: str,
        traceback: str,
    ) -> str:

        combined = f"{message}\n{traceback}"

        known_types = [
            "SyntaxError",
            "IndentationError",
            "ModuleNotFoundError",
            "ImportError",
            "NameError",
            "TypeError",
            "ValueError",
            "AttributeError",
            "KeyError",
            "IndexError",
            "FileNotFoundError",
            "PermissionError",
        ]

        for error_type in known_types:
            if error_type in combined:
                return error_type

        return "UnknownError"

    def _determine_cause(
        self,
        error_type: str,
        message: str,
    ) -> str:

        if error_type == "SyntaxError":
            return (
                "The affected source contains invalid Python syntax "
                "near the reported location."
            )

        if error_type == "IndentationError":
            return (
                "The affected Python block has inconsistent or "
                "invalid indentation."
            )

        if error_type == "ModuleNotFoundError":
            return (
                "A required module or dependency could not be "
                "resolved by the runtime."
            )

        if error_type == "ImportError":
            return (
                "A requested import could not be resolved or loaded."
            )

        if error_type == "NameError":
            return (
                "The code references a name that is not defined "
                "in the current scope."
            )

        if error_type == "TypeError":
            return (
                "An operation received an incompatible value or "
                "argument type."
            )

        if error_type == "AttributeError":
            return (
                "The code attempted to access an attribute that "
                "does not exist on the target object."
            )

        if error_type == "KeyError":
            return (
                "The code requested a dictionary key that is not "
                "present."
            )

        if error_type == "FileNotFoundError":
            return (
                "The application attempted to access a file or "
                "path that does not exist."
            )

        if error_type == "PermissionError":
            return (
                "The runtime lacks permission to perform the "
                "requested filesystem operation."
            )

        return (
            "The available error information is insufficient for "
            "a definitive root-cause determination."
        )

    def _determine_impact(
        self,
        error_type: str,
        location: Dict[str, Any],
    ) -> str:

        if location["file"] and location["line"]:
            location_text = (
                f"{location['file']} at line "
                f"{location['line']}"
            )
        elif location["file"]:
            location_text = location["file"]
        else:
            location_text = "the reported execution path"

        if error_type in {
            "SyntaxError",
            "IndentationError",
        }:
            return (
                f"Execution/validation is blocked at "
                f"{location_text}."
            )

        return (
            f"The reported failure affects "
            f"{location_text}; unrelated project files "
            f"should remain unchanged."
        )

    def _determine_scope(
        self,
        error_type: str,
        location: Dict[str, Any],
    ) -> Dict[str, Any]:

        file_path = location.get("file")

        return {
            "mode": "localized",
            "file": file_path,
            "line": location.get("line"),
            "function": location.get("function"),
            "whole_project": False,
            "reason": (
                "Repair must be limited to the smallest affected "
                "file/function/section supported by evidence."
            ),
        }

    def _suggest_action(
        self,
        error_type: str,
    ) -> str:

        if error_type in {
            "SyntaxError",
            "IndentationError",
        }:
            return "Inspect and minimally repair the reported source location."

        if error_type in {
            "ModuleNotFoundError",
            "ImportError",
        }:
            return "Inspect dependency/import configuration before modifying application logic."

        if error_type == "NameError":
            return "Inspect the definition and scope of the reported name."

        if error_type == "TypeError":
            return "Inspect the failing function arguments and expected types."

        if error_type == "AttributeError":
            return "Inspect the target object's interface and attribute access."

        return (
            "Collect additional validation/test evidence before "
            "proposing a code change."
      )
