from pathlib import Path
from typing import Any, Dict, Optional
import time

from .ai_engine import AIEngine
from .approval_engine import ApprovalEngine
from .project_scanner import ProjectScanner
from .code_generation_engine import CodeGenerationEngine
from .validation_pipeline import ValidationPipeline
from .repair_engine import RepairEngine
from .transaction_manager import TransactionManager
from .change_scope_guard import ChangeScopeGuard
from .dependency_impact_engine import DependencyImpactEngine
from .risk_gate import RiskGate
from .security_manager import SecurityManager


class WorkflowEngine:
    """
    Central orchestration engine for AI App Builder.

    All change decisions flow through this class:
    scan -> plan -> proposal -> analysis -> approval -> scope/security gate
    -> transaction -> validation/tests -> deployment risk decision.
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
        self.dependency_impact_engine = DependencyImpactEngine()
        self.risk_gate = RiskGate()
        self.security_manager = SecurityManager()

        self.approval_engine = (
            approval_engine
            if approval_engine is not None
            else ApprovalEngine()
        )

    def approve(self, approval_id: str) -> Dict[str, Any]:
        return self.approval_engine.approve(approval_id)

    def reject(self, approval_id: str) -> Dict[str, Any]:
        return self.approval_engine.reject(approval_id)

    def get_approval(self, approval_id: str) -> Dict[str, Any]:
        return self.approval_engine.get_request(approval_id)

    def create_plan(
            self,
            command: str,
            project_path: str,
        ) -> Dict[str, Any]:
            if not command.strip():
                raise ValueError("Command cannot be empty.")

            total_start = time.perf_counter()
            print("[TRACE] CREATE PLAN START")

            start = time.perf_counter()
            inventory = self.scanner.scan(project_path)
            print(
                f"[TRACE] SCANNER DONE: "
                f"{time.perf_counter() - start:.3f}s"
            )

            start = time.perf_counter()
            plan = self.ai_engine.create_plan(command, project_path)
            print(
                f"[TRACE] AI PLAN DONE: "
                f"{time.perf_counter() - start:.3f}s"
            )

            plan["inventory"] = inventory

            architecture = plan.get("architecture", {})
            affected_files = plan.get("affected_files", [])

            start = time.perf_counter()
            try:
                code_proposal = self.code_generator.propose(
                    command,
                    architecture,
                    inventory,
                    project_path=project_path,
                    affected_files=affected_files,
                )
            except TypeError:
                code_proposal = self.code_generator.propose(
                    command,
                    architecture,
                    inventory,
                )

            print(
                f"[TRACE] CODE PROPOSAL DONE: "
                f"{time.perf_counter() - start:.3f}s"
            )

            plan["code_proposal"] = code_proposal
            plan["changes"] = code_proposal.get("changes", [])
            plan["project_path"] = project_path

            start = time.perf_counter()
            security = self.security_manager.inspect_paths(
                change.get("file", "")
                for change in plan["changes"]
            )
            print(
                f"[TRACE] SECURITY DONE: "
                f"{time.perf_counter() - start:.3f}s"
            )

            dependency_impacts = []

            start = time.perf_counter()

            for change in plan["changes"]:
                file_name = change.get("file", "")
                action = change.get("action", "modify")

                if file_name and action == "modify":
                    dependency_impacts.append(
                        self.dependency_impact_engine.analyze(
                            project_path,
                            file_name,
                        )
                    )

            print(
                f"[TRACE] DEPENDENCY ANALYSIS DONE: "
                f"{time.perf_counter() - start:.3f}s"
            )

            plan["analysis"] = {
                "security": security,
                "dependency_impacts": dependency_impacts,
            }

            plan["workflow"] = {
                "stage": "approval_required",
                "changes_applied": False,
                "validation_passed": False,
                "repair_attempts": 0,
                "deployment_allowed": False,
            }

            start = time.perf_counter()

            approval = self.approval_engine.create_request(plan)

            approval_time = time.perf_counter() - start

            print(
                f"[TRACE] APPROVAL ID CREATED: "
                f"{approval['id']} "
                f"({approval_time:.3f}s)"
            )

            print(
                f"[TRACE] CREATE PLAN TOTAL: "
                f"{time.perf_counter() - total_start:.3f}s"
            )

            return {
                "status": "approval_required",
                "approval_id": approval["id"],
                "plan": plan,
            }

    def apply_approved_plan(self, approval_id: str) -> Dict[str, Any]:
        approval = self.approval_engine.get_request(approval_id)

        if approval["status"] != "approved":
            raise ValueError(
                "User approval is required before changes can be applied."
            )

        plan = approval["plan"]
        project_path = plan["project_path"]
        changes = plan.get("changes", [])

        if not changes:
            return {
                "approval_id": approval_id,
                "success": False,
                "stage": "patching",
                "message": "No executable changes were generated.",
            }

        # Re-check security immediately before write. Planning data is advisory
        # and must never be trusted as a permanent authorization.
        security = self.security_manager.inspect_paths(
            change.get("file", "")
            for change in changes
        )

        if not security["passed"]:
            plan["workflow"]["stage"] = "security_blocked"
            return {
                "approval_id": approval_id,
                "plan": plan,
                "transaction": {
                    "success": False,
                    "rolled_back": False,
                    "stage": "security_blocked",
                    "security": security,
                },
            }

        approved_files = [
            change.get("file")
            for change in changes
            if change.get("file")
        ]

        scope_guard = ChangeScopeGuard(project_path)
        scope_result = scope_guard.inspect_plan(
            changes,
            approved_files,
        )

        if not scope_result.get("allowed"):
            plan["workflow"]["stage"] = "scope_guard_failed"
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

        result = self.transaction.apply(project_path, changes)
        result["security"] = security
        result["scope_guard"] = scope_result

        validation_result = result.get("validation") or {}
        tests_result = validation_result.get("tests") or {}

        validation_passed = bool(validation_result.get("valid", False))
        tests_passed = bool(
            tests_result.get("passed", validation_passed)
        )

        risk_level = plan.get("code_proposal", {}).get("risk", "medium")

        risk_gate = self.risk_gate.can_deploy(
            risk=risk_level,
            validation_passed=validation_passed,
            tests_passed=tests_passed,
            security_passed=bool(security["passed"]),
            user_approved=True,
        )

        result["risk_gate"] = risk_gate

        success = bool(result.get("success")) and bool(risk_gate.get("allowed"))

        if success:
            plan["workflow"].update({
                "stage": "release_checks_passed",
                "changes_applied": True,
                "validation_passed": True,
                "deployment_allowed": True,
            })
        else:
            plan["workflow"].update({
                "stage": (
                    "risk_gate_blocked"
                    if result.get("success")
                    else "rolled_back"
                ),
                "changes_applied": bool(result.get("success")),
                "validation_passed": validation_passed,
                "deployment_allowed": False,
            })

        return {
            "approval_id": approval_id,
            "plan": plan,
            "transaction": result,
        }

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
                "reason": "Maximum repair attempts reached.",
            }

        proposal = self.repair_engine.propose_fix(
            error,
            context,
            attempt,
        )

        if not proposal.get("repair_allowed", True):
            return proposal

        file_path = proposal.get("file")
        old_content = proposal.get("old_content")
        new_content = proposal.get("new_content")

        if not file_path:
            return {
                "repair_allowed": False,
                "stage": "failed",
                "reason": "Repair proposal did not identify a file.",
            }

        if old_content is None:
            return {
                "repair_allowed": False,
                "stage": "failed",
                "reason": "Repair proposal did not provide exact old_content.",
            }

        if new_content is None:
            return {
                "repair_allowed": False,
                "stage": "failed",
                "reason": "Repair proposal did not provide new_content.",
            }

        return proposal
