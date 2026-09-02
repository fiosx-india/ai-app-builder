from typing import Any, Dict

from .ai_engine import AIEngine
from .approval_engine import ApprovalEngine
from .project_scanner import ProjectScanner


class WorkflowEngine:
    """
    Coordinates the safe planning stage.

    This engine does NOT directly modify project files.
    """

    def __init__(self) -> None:
        self.ai_engine = AIEngine()
        self.scanner = ProjectScanner()
        self.approval_engine = ApprovalEngine()

    def create_plan(
        self,
        command: str,
        project_path: str,
    ) -> Dict[str, Any]:

        if not command.strip():
            raise ValueError(
                "Command cannot be empty."
            )

        inventory = self.scanner.scan(
            project_path
        )

        plan = self.ai_engine.create_plan(
            command,
            project_path,
        )

        plan["inventory"] = inventory

        plan["workflow"] = {
            "stage": "approval_required",
            "changes_applied": False,
            "deployment_allowed": False,
        }

        approval = self.approval_engine.create_request(
            plan
        )

        return {
            "status": "approval_required",
            "approval_id": approval["id"],
            "plan": plan,
        }
