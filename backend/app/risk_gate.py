"""
MarketVerse Lab
risk_gate.py

Purpose:
Production safety gate for AI-generated application changes.

This module prevents risky changes from being applied or deployed
without the required validation, testing, security checks and
explicit approval.

This module does NOT modify files.
This module does NOT deploy applications.
It only decides whether the next stage is allowed.
"""

from __future__ import annotations

from typing import Any, Dict


class RiskGate:
    """
    Hard safety gate for application changes.

    A change must satisfy every required condition before it can
    move toward deployment.

    Important:
    - Risk level alone never grants permission.
    - Failed validation blocks deployment.
    - Failed tests block deployment.
    - Failed security checks block deployment.
    - Missing explicit approval blocks deployment.
    """

    VALID_RISK_LEVELS = {
        "low",
        "medium",
        "high",
        "critical",
    }

    def evaluate(
        self,
        *,
        risk: str,
        validation_passed: bool,
        tests_passed: bool,
        security_passed: bool,
        user_approved: bool,
    ) -> Dict[str, Any]:
        """
        Evaluate whether a change may proceed.

        Returns a structured decision.
        No deployment or file modification happens here.
        """

        normalized_risk = str(risk).strip().lower()

        if normalized_risk not in self.VALID_RISK_LEVELS:
            return self._blocked(
                reason=(
                    f"Unknown risk level: {risk}. "
                    "A valid risk level is required."
                )
            )

        checks = {
            "risk_level_valid": True,
            "validation_passed": bool(validation_passed),
            "tests_passed": bool(tests_passed),
            "security_passed": bool(security_passed),
            "user_approved": bool(user_approved),
        }

        failed_checks = [
            name
            for name, passed in checks.items()
            if not passed
        ]

        if failed_checks:
            return {
                "allowed": False,
                "stage": "risk_gate_blocked",
                "risk": normalized_risk,
                "checks": checks,
                "failed_checks": failed_checks,
                "deployment_allowed": False,
                "reason": (
                    "Change cannot proceed because one or more "
                    "mandatory safety checks failed."
                ),
            }

        return {
            "allowed": True,
            "stage": "risk_gate_passed",
            "risk": normalized_risk,
            "checks": checks,
            "failed_checks": [],
            "deployment_allowed": True,
            "reason": (
                "All mandatory safety checks passed and "
                "explicit approval was provided."
            ),
        }

    def can_apply(
        self,
        *,
        validation_passed: bool,
        tests_passed: bool,
        user_approved: bool,
    ) -> Dict[str, Any]:
        """
        Separate gate for applying changes.

        Security/deployment checks are intentionally not treated
        as a substitute for the apply-stage validation.
        """

        if not validation_passed:
            return self._blocked(
                reason="Changes cannot be applied: validation failed."
            )

        if not tests_passed:
            return self._blocked(
                reason="Changes cannot be applied: tests failed."
            )

        if not user_approved:
            return self._blocked(
                reason="Changes cannot be applied: user approval is required."
            )

        return {
            "allowed": True,
            "stage": "apply_gate_passed",
            "apply_allowed": True,
            "deployment_allowed": False,
        }

    def can_deploy(
        self,
        *,
        validation_passed: bool,
        tests_passed: bool,
        security_passed: bool,
        user_approved: bool,
        risk: str,
    ) -> Dict[str, Any]:
        """
        Final deployment gate.

        Deployment is allowed only when every mandatory condition
        passes.
        """

        return self.evaluate(
            risk=risk,
            validation_passed=validation_passed,
            tests_passed=tests_passed,
            security_passed=security_passed,
            user_approved=user_approved,
        )

    @staticmethod
    def _blocked(reason: str) -> Dict[str, Any]:
        return {
            "allowed": False,
            "stage": "risk_gate_blocked",
            "checks": {},
            "failed_checks": [],
            "apply_allowed": False,
            "deployment_allowed": False,
            "reason": reason,
        }
