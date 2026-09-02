from typing import Any, Dict

from .error_intelligence import ErrorIntelligence
from .test_engine import TestEngine
from .validation_engine import ValidationEngine


class ValidationPipeline:
    """
    Complete validation gate.

    Validation must pass before a change is considered
    safe to deploy.
    """

    def __init__(self) -> None:

        self.validator = ValidationEngine()
        self.tester = TestEngine()
        self.error_intelligence = (
            ErrorIntelligence()
        )

    def run(
        self,
        project_path: str,
    ) -> Dict[str, Any]:

        # -----------------------------
        # Stage 1: Static validation
        # -----------------------------

        validation = self.validator.validate(
            project_path
        )

        errors = list(
            validation.get(
                "errors",
                [],
            )
        )

        if not validation.get(
            "valid",
            False,
        ):

            return {
                "valid": False,
                "safe_to_apply": False,
                "safe_to_deploy": False,
                "stage": "syntax_validation",
                "validation": validation,
                "tests": None,
                "errors": errors,
                "message": (
                    "Validation failed. "
                    "Changes must not be deployed."
                ),
            }

        # -----------------------------
        # Stage 2: Tests
        # -----------------------------

        tests = self.tester.run_pytest(
            project_path
        )

        if not tests.get(
            "passed",
            False,
        ):

            raw_error = (
                tests.get("stderr")
                or tests.get("stdout")
                or "Pytest failed."
            )

            diagnostic = (
                self.error_intelligence.analyze(
                    raw_error
                )
            )

            errors.append(
                diagnostic
            )

        passed = (
            validation.get("valid", False)
            and tests.get("passed", False)
        )

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
                if passed
                else
                "Validation failed. "
                "Fix reported errors and "
                "run validation again."
            ),
        }
