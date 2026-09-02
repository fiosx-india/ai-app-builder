from typing import Any, Dict

from .ai_engine import AIEngine
from .approval_engine import ApprovalEngine
from .project_scanner import ProjectScanner
from .code_generation_engine import CodeGenerationEngine
from .validation_pipeline import ValidationPipeline
from .repair_engine import RepairEngine
from .transaction_manager import TransactionManager


class WorkflowEngine:
    """
    Central orchestration engine for AI App Builder.

    Safety flow:

    COMMAND
        ↓
    SCAN
        ↓
    PLAN
        ↓
    CODE PROPOSAL
        ↓
    USER APPROVAL
        ↓
    APPLY
        ↓
    VALIDATE
        ↓
    TEST
        ↓
    ERROR
        ↓
    REPAIR PROPOSAL
    """

    MAX_REPAIR_ATTEMPTS = 3

    def __init__(self) -> None:

        self.ai_engine = AIEngine()
        self.scanner = ProjectScanner()
        self.code_generator = CodeGenerationEngine()
        self.validation = ValidationPipeline()
        self.repair_engine = RepairEngine()
        self.transaction = TransactionManager()
        self.approval_engine = ApprovalEngine()

    # --------------------------------------------------
    # STEP 1: Create safe plan
    # --------------------------------------------------

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

        # ----------------------------------------------
        # Generate executable code proposal
        # ----------------------------------------------

        architecture = plan.get(
            "architecture",
            {},
        )

        code_proposal = (
            self.code_generator.propose(
                command,
                architecture,
                inventory,
            )
        )

        plan["code_proposal"] = code_proposal

        # Keep changes available to the apply stage.
        plan["changes"] = code_proposal.get(
            "changes",
            [],
        )

        plan["project_path"] = project_path

        plan["workflow"] = {
            "stage": "approval_required",
            "changes_applied": False,
            "validation_passed": False,
            "repair_attempts": 0,
            "deployment_allowed": False,
        }

        approval = (
            self.approval_engine.create_request(
                plan
            )
        )

        return {
            "status": "approval_required",
            "approval_id": approval["id"],
            "plan": plan,
        }

    # --------------------------------------------------
    # STEP 2: Apply approved change
    # --------------------------------------------------

    def apply_approved_plan(
        self,
        approval_id: str,
    ) -> Dict[str, Any]:

        approval = (
            self.approval_engine.get_request(
                approval_id
            )
        )

        if approval["status"] != "approved":
            raise ValueError(
                "User approval is required before "
                "changes can be applied."
            )

        plan = approval["plan"]

        project_path = plan[
            "project_path"
        ]

        changes = plan.get(
            "changes",
            [],
        )

        if not changes:
            return {
                "success": False,
                "stage": "patching",
                "message": (
                    "No executable changes "
                    "were generated."
                ),
            }

        # ----------------------------------------------
        # Transaction manager performs:
        # backup → patch → validation → rollback
        # ----------------------------------------------

        result = self.transaction.apply(
            project_path,
            changes,
        )

        if result.get("success"):

            plan["workflow"][
                "stage"
            ] = "validation_passed"

            plan["workflow"][
                "changes_applied"
            ] = True

            plan["workflow"][
                "validation_passed"
            ] = True

        else:

            plan["workflow"][
                "stage"
            ] = "rolled_back"

            plan["workflow"][
                "changes_applied"
            ] = False

        return {
            "approval_id": approval_id,
            "plan": plan,
            "transaction": result,
        }

    # --------------------------------------------------
    # STEP 3: Repair failed validation
    # --------------------------------------------------

    def repair(
        self,
        project_path: str,
        error: Dict[str, Any],
        context: Dict[str, Any],
        attempt: int = 0,
    ) -> Dict[str, Any]:

        if attempt >= self.MAX_REPAIR_ATTEMPTS:
            return {
                "repair_allowed": False,
                "stage": "failed",
                "reason": (
                    "Maximum repair attempts reached."
                ),
            }

        proposal = (
            self.repair_engine.propose_fix(
                error,
                context,
                attempt,
            )
        )

        if not proposal.get(
            "repair_allowed",
            True,
        ):
            return proposal

        file_path = proposal.get(
            "file"
        )

        old_content = proposal.get(
            "old_content"
        )

        new_content = proposal.get(
            "new_content"
        )

        if not file_path:
            return {
                "repair_allowed": False,
                "stage": "failed",
                "reason": (
                    "Repair proposal did not "
                    "identify a file."
                ),
            }

        if old_content is None:
            return {
                "repair_allowed": False,
                "stage": "failed",
                "reason": (
                    "Repair proposal did not "
                    "provide exact old_content."
                ),
            }

        if new_content is None:
            return {
                "repair_allowed": False,
                "stage": "failed",
                "reason": (
                    "Repair proposal did not "
                    "provide new_content."
                ),
            }

        return {
            "repair_allowed": True,
            "stage": "repair_proposed",
            "attempt": attempt + 1,
            "file": file_path,
            "target": proposal.get(
                "target"
            ),
            "old_content": old_content,
            "new_content": new_content,
            "explanation": proposal.get(
                "explanation"
            ),
            "validation_steps": proposal.get(
                "validation_steps",
                [],
            ),
        }

    # --------------------------------------------------
    # STEP 4: Re-run validation
    # --------------------------------------------------

    def validate_after_change(
        self,
        project_path: str,
    ) -> Dict[str, Any]:

        result = self.validation.run(
            project_path
        )

        return {
            "stage": (
                "validation_passed"
                if result.get("valid")
                else "validation_failed"
            ),
            **result,
            }
