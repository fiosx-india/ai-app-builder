"""
MarketVerse Lab
regression_guard.py

Purpose:
Prevent a successful-looking repair from breaking existing
functionality.

This module does NOT modify files.
This module does NOT apply patches.
This module does NOT deploy applications.

It evaluates validation and regression-test results.
"""

from __future__ import annotations

from typing import Any, Dict, List


class RegressionGuard:
    """
    Safety gate for post-change regression verification.

    Core rule:

        REPAIR
          ↓
        VALIDATION
          ↓
        TESTS
          ↓
        REGRESSION CHECK
          ↓
        PASS / BLOCK

    A repair is not considered successful merely because the
    original error disappeared.
    """

    def evaluate(
        self,
        *,
        validation_passed: bool,
        tests_passed: bool,
        regression_passed: bool,
        original_error_resolved: bool,
        new_errors: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        """
        Evaluate whether a repaired change is safe to continue.

        Every mandatory condition must pass.
        """

        errors = new_errors or []

        checks = {
            "validation_passed": bool(validation_passed),
            "tests_passed": bool(tests_passed),
            "regression_passed": bool(regression_passed),
            "original_error_resolved": bool(
                original_error_resolved
            ),
            "no_new_errors": len(errors) == 0,
        }

        failed_checks = [
            name
            for name, passed in checks.items()
            if not passed
        ]

        if failed_checks:
            return {
                "allowed": False,
                "stage": "regression_blocked",
                "checks": checks,
                "failed_checks": failed_checks,
                "new_errors": errors,
                "repair_successful": False,
                "safe_to_continue": False,
                "rollback_recommended": True,
                "reason": (
                    "The repair did not pass all mandatory "
                    "regression checks."
                ),
            }

        return {
            "allowed": True,
            "stage": "regression_passed",
            "checks": checks,
            "failed_checks": [],
            "new_errors": [],
            "repair_successful": True,
            "safe_to_continue": True,
            "rollback_recommended": False,
            "reason": (
                "The original error is resolved and all "
                "regression checks passed."
            ),
        }

    def compare_test_results(
        self,
        before: Dict[str, Any],
        after: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compare test results before and after a change.

        This detects cases where the original tests pass but
        the overall test state became worse.
        """

        before_passed = int(
            before.get("passed", 0)
        )

        before_failed = int(
            before.get("failed", 0)
        )

        after_passed = int(
            after.get("passed", 0)
        )

        after_failed = int(
            after.get("failed", 0)
        )

        failures_increased = (
            after_failed > before_failed
        )

        passed_decreased = (
            after_passed < before_passed
        )

        regression_detected = (
            failures_increased
            or passed_decreased
        )

        return {
            "regression_detected": regression_detected,
            "before": {
                "passed": before_passed,
                "failed": before_failed,
            },
            "after": {
                "passed": after_passed,
                "failed": after_failed,
            },
            "failures_increased": failures_increased,
            "passed_tests_decreased": passed_decreased,
            "safe_to_continue": not regression_detected,
        }

    def block_on_new_errors(
        self,
        errors: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Hard-stop helper for newly introduced errors.
        """

        if errors:
            return {
                "allowed": False,
                "stage": "new_error_detected",
                "new_errors": errors,
                "safe_to_continue": False,
                "rollback_recommended": True,
                "reason": (
                    "New errors were detected after the change. "
                    "The change must not proceed."
                ),
            }

        return {
            "allowed": True,
            "stage": "new_error_check_passed",
            "new_errors": [],
            "safe_to_continue": True,
            "rollback_recommended": False,
            }
