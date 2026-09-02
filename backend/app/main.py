from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .ai_engine import AIEngine
from .approval_engine import ApprovalEngine
from .project_manager import ProjectManager
from .validation_pipeline import ValidationPipeline
from .workflow_engine import WorkflowEngine
from .transaction_manager import TransactionManager


app = FastAPI(
    title="AI App Builder",
    version="0.3.0",
)


ai_engine = AIEngine()
approval_engine = ApprovalEngine()
project_manager = ProjectManager()
validation_pipeline = ValidationPipeline()
workflow_engine = WorkflowEngine()
transaction_manager = TransactionManager()


class CommandRequest(BaseModel):
    command: str
    project_path: str = "./projects/default"


class ApprovalRequest(BaseModel):
    approval_id: str


class ApplyRequest(BaseModel):
    approval_id: str


@app.get("/")
def root():
    return {
        "name": "AI App Builder",
        "status": "online",
        "version": "0.3.0",
    }


@app.post("/api/command")
def execute_command(
    request: CommandRequest,
):

    try:

        result = workflow_engine.create_plan(
            request.command,
            request.project_path,
        )

        return result

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@app.post("/api/approve")
def approve(
    request: ApprovalRequest,
):

    try:

        return approval_engine.approve(
            request.approval_id
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@app.post("/api/reject")
def reject(
    request: ApprovalRequest,
):

    try:

        return approval_engine.reject(
            request.approval_id
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@app.get(
    "/api/approval/{approval_id}"
)
def get_approval(
    approval_id: str,
):

    try:

        return approval_engine.get_request(
            approval_id
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@app.post("/api/validate")
def validate_project(
    request: CommandRequest,
):

    return validation_pipeline.run(
        request.project_path
    )


@app.post("/api/project")
def create_project(
    request: CommandRequest,
):

    return project_manager.create_project(
        request.project_path
    )


@app.post("/api/apply")
def apply_approved_changes(
    request: ApplyRequest,
):

    try:

        approval = (
            approval_engine.get_request(
                request.approval_id
            )
        )

        if approval["status"] != "approved":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Changes cannot be applied. "
                    "Approval is required."
                ),
            )

        plan = approval["plan"]

        changes = plan.get(
            "changes",
            [],
        )

        project_path = plan.get(
            "project_path"
        )

        if not changes:

            return {
                "success": False,
                "message": (
                    "No executable changes "
                    "are present in the approved plan."
                ),
            }

        result = transaction_manager.apply(
            project_path,
            changes,
        )

        return result

    except HTTPException:
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )
