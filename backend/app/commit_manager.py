from typing import Any, Dict, List
from .github_manager import GitHubManager


class CommitManager:
    """
    Controls the final GitHub commit gate.

    A commit is allowed only after:
    - validation passed
    - tests passed
    - final approval was granted
    """

    def __init__(self) -> None:
        self.github = GitHubManager()

    def check_commit_gate(
        self,
        validation: Dict[str, Any],
        final_approval: bool,
    ) -> Dict[str, Any]:

        if not validation.get("valid"):
            return {
                "allowed": False,
                "reason": (
                    "Validation has not passed."
                ),
            }

        if not validation.get(
            "safe_to_deploy"
        ):
            return {
                "allowed": False,
                "reason": (
                    "Project is not marked safe."
                ),
            }

        if not final_approval:
            return {
                "allowed": False,
                "reason": (
                    "Final user approval is required."
                ),
            }

        return {
            "allowed": True,
            "reason": (
                "Validation and final approval passed."
            ),
        }

    def create_branch(
        self,
        branch_name: str,
    ) -> Dict[str, Any]:

        return self.github.create_branch(
            branch_name
        )

    def create_pull_request(
        self,
        branch_name: str,
        title: str,
        body: str,
    ) -> Dict[str, Any]:

        return self.github.create_pull_request(
            branch_name,
            title,
            body,
        )
