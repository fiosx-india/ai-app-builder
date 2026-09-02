from typing import Any, Dict

from .error_intelligence import ErrorIntelligence
from .test_engine import TestEngine
from .validation_engine import ValidationEngine


class ValidationPipeline:
    """Runs validation and tests without modifying project files."""

    def __init__(self) -> None:
        self.validator = ValidationEngine()
        self.tester = TestEngine()
        self.error_intelligence = ErrorIntelligence()

    def run(self, project_path: str) -> Dict[str, Any]:
        validation = self.validator.validate(project_path)
        errors = list(validation.get("errors", []))

        if not validation.get("valid", False):
            return {
                "valid": False,
                "safe_to_apply": False,
                "safe_to_deploy": False,
                "stage": "syntax_validation",
                "validation": validation,
                "tests": None,
                "errors": errors,
                "message": "Validation failed. No changes should be applied or deployed.",
            }

        tests = self.tester.run_pytest(project_path)
        if not tests.get("passed", False):
            errors.append(
                self.error_intelligence.analyze(
                    tests.get("stderr") or tests.get("stdout") or "Pytest failed."
                )
            )

        passed = bool(validation.get("valid")) and bool(tests.get("passed"))
        return {
            "valid": passed,
            "safe_to_apply": passed,
            "safe_to_deploy": passed,
            "stage": "complete",
            "validation": validation,
            "tests": tests,
            "errors": errors,
            "message": (
                "All validation stages passed."
                if passed else
                "Validation failed. Fix reported errors and run validation again."
            ),
        }
