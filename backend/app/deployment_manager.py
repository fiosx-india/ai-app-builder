from typing import Any, Dict


class DeploymentManager:
    """
    Deployment safety gate.

    Actual hosting-provider deployment is intentionally
    not implemented here until a provider is configured.
    """

    def check_gate(
        self,
        validation: Dict[str, Any],
        final_approval: bool,
        github_result: Dict[str, Any],
    ) -> Dict[str, Any]:

        if not validation.get(
            "valid"
        ):
            return {
                "allowed": False,
                "status": "blocked",
                "reason": (
                    "Validation failed."
                ),
            }

        if not final_approval:
            return {
                "allowed": False,
                "status": "blocked",
                "reason": (
                    "Final approval is required."
                ),
            }

        if not github_result.get(
            "created"
        ):
            return {
                "allowed": False,
                "status": "blocked",
                "reason": (
                    "GitHub publication has not "
                    "completed."
                ),
            }

        return {
            "allowed": True,
            "status": "ready",
            "reason": (
                "Deployment gate passed. "
                "A hosting provider adapter is still required."
            ),
        }

    def deploy(
        self,
        project_path: str,
        validation: Dict[str, Any],
        final_approval: bool,
        github_result: Dict[str, Any],
    ) -> Dict[str, Any]:

        gate = self.check_gate(
            validation,
            final_approval,
            github_result,
        )

        if not gate["allowed"]:
            return {
                "deployed": False,
                **gate,
                "project_path": project_path,
            }

        return {
            "deployed": False,
            "status": "ready_for_provider",
            "project_path": project_path,
            "reason": (
                "Safety gates passed, but no hosting "
                "provider adapter is configured."
            ),
        }
