from typing import Any, Dict, Optional

from .ai_engine import AIEngine
from .approval_engine import ApprovalEngine
from .project_scanner import ProjectScanner
from .code_generation_engine import CodeGenerationEngine
from .validation_pipeline import ValidationPipeline
from .repair_engine import RepairEngine
from .transaction_manager import TransactionManager
from .change_analyzer import ChangeAnalyzer
from .dependency_analyzer import DependencyAnalyzer
from .dependency_impact_engine import DependencyImpactEngine
from .change_scope_guard import ChangeScopeGuard


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

    ApprovalEngine is injected so the API layer and workflow
    always use the same approval store.
    """

    MAX_REPAIR_ATTEMPTS = 3

    def __init__(
        self,
        approval_engine: Optional[ApprovalEngine] = None,
    ) -> None:

        self.ai_engine = AIEngine()
        self.scanner = ProjectScanner()
        self.code_generator = CodeGenerationEngine()
        self.validation = ValidationPipeline()
        self.repair_engine = RepairEngine()
        self.transaction = TransactionManager()
        self.change_analyzer = ChangeAnalyzer()
        self.dependency_analyzer = DependencyAnalyzer()
        self.dependency_impact_engine = DependencyImpactEngine()

        # IMPORTANT:
        # main.py and WorkflowEngine must share the same instance.
        self.approval_engine = (
            approval_engine
            if approval_engine is not None
            else ApprovalEngine()
        )

    # --------------------------------------------------
    # APPROVAL API
    # --------------------------------------------------

    def approve(
        self,
        approval_id: str,
    ) -> Dict[str, Any]:

        return self.approval_engine.approve(
            approval_id
        )

    def reject(
        self,
        approval_id: str,
    ) -> Dict[str, Any]:

        return self.approval_engine.reject(
            approval_id
        )

    def get_approval(
        self,
        approval_id: str,
    ) -> Dict[str, Any]:

        return self.approval_engine.get_request(
            approval_id
        )

    # --------------------------------------------------
    # STEP 1: CREATE SAFE PLAN
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

        affected_files = plan.get("affected_files", [])
        code_proposal = self.code_generator.propose(
            command,
            architecture,
            inventory,
            project_path=project_path,
            affected_files=affected_files,
        )

        plan["code_proposal"] = code_proposal

        plan["changes"] = code_proposal.get("changes", [])

        # Analysis is advisory before approval. It explains scope and
        # dependency impact without applying any change.
        change_reports = []
        dependency_reports = []
        for change in plan["changes"]:
            file_name = change.get("file")
            action = change.get("action", "modify")
            if not file_name:
                continue
            if action == "modify":
                change_reports.append(
                    self.change_analyzer.analyze(
                        file_name,
                        change.get("old_content", ""),
                        change.get("new_content", ""),
                    )
                )
                dependency_reports.append(
                    self.dependency_analyzer.analyze_file(
                        str(__import__("pathlib").Path(project_path) / file_name)
                    )
                )

        plan["analysis"] = {
            "changes": change_reports,
            "dependencies": dependency_reports,
        }

        plan["project_path"] = project_path

        plan["workflow"] = {
            "stage": "approval_required",
            "changes_applied": False,
            "validation_passed": False,
            "repair_attempts": 0,
            "deployment_allowed": False,
        }

        # Approval is created in the SAME ApprovalEngine
        # instance used by the API.
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
    # STEP 2: APPLY APPROVED CHANGE
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
                "approval_id": approval_id,
                "success": False,
                "stage": "patching",
                "message": (
                    "No executable changes "
                    "were generated."
                ),
            }

        # Enforce approved scope immediately before any write.
        approved_files = [change.get("file") for change in changes if change.get("file")]
        scope_guard = ChangeScopeGuard(project_path)
        scope_result = scope_guard.inspect_plan(changes, approved_files)

        if not scope_result.get("allowed"):
            return {
                "approval_id": approval_id,
                "plan": plan,
                "transaction": {
                    "success": False,
                    "rolled_back": False,
                    "stage": "scope_guard_failed",
                    "scope_guard": scope_result,
                },
            }

        # TransactionManager handles backup → patch → validation → rollback.
        result = self.transaction.apply(project_path, changes)
        result["scope_guard"] = scope_result

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

            plan["workflow"][
                "validation_passed"
            ] = False

        return {
            "approval_id": approval_id,
            "plan": plan,
            "transaction": result,
        }

    # --------------------------------------------------
    # STEP 3: REPAIR FAILED VALIDATION
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
    # STEP 4: RE-RUN VALIDATION
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
