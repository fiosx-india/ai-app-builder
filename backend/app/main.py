from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .approval_engine import ApprovalEngine
from .project_manager import ProjectManager
from .validation_pipeline import ValidationPipeline
from .workflow_engine import WorkflowEngine


app = FastAPI(
    title="AI App Builder",
    version="0.4.0",
)


# --------------------------------------------------
# SHARED APPLICATION SERVICES
# --------------------------------------------------

# IMPORTANT:
# There must be ONE ApprovalEngine instance.
#
# /api/command creates the approval through WorkflowEngine.
# /api/approve, /api/reject, /api/approval and /api/apply
# must therefore use that exact same instance.

approval_engine = ApprovalEngine()

project_manager = ProjectManager()

validation_pipeline = ValidationPipeline()

workflow_engine = WorkflowEngine(
    approval_engine=approval_engine,
)


# --------------------------------------------------
# REQUEST MODELS
# --------------------------------------------------

class CommandRequest(BaseModel):

    command: str

    project_path: str = (
        "./projects/default"
    )


class ApprovalRequest(BaseModel):

    approval_id: str


class ApplyRequest(BaseModel):

    approval_id: str


# --------------------------------------------------
# ROOT
# --------------------------------------------------

@app.get("/")
def root():

    return {
        "name": "AI App Builder",
        "status": "online",
        "version": "0.4.0",
    }


# --------------------------------------------------
# COMMAND → PLAN → APPROVAL
# --------------------------------------------------

@app.post("/api/command")
def execute_command(
    request: CommandRequest,
):

    try:

        return workflow_engine.create_plan(
            request.command,
            request.project_path,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# --------------------------------------------------
# APPROVE
# --------------------------------------------------

@app.post("/api/approve")
def approve(
    request: ApprovalRequest,
):

    try:

        return workflow_engine.approve(
            request.approval_id
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


# --------------------------------------------------
# REJECT
# --------------------------------------------------

@app.post("/api/reject")
def reject(
    request: ApprovalRequest,
):

    try:

        return workflow_engine.reject(
            request.approval_id
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


# --------------------------------------------------
# GET APPROVAL
# --------------------------------------------------

@app.get(
    "/api/approval/{approval_id}"
)
def get_approval(
    approval_id: str,
):

    try:

        return workflow_engine.get_approval(
            approval_id
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


# --------------------------------------------------
# APPLY APPROVED CHANGES
# --------------------------------------------------

@app.post("/api/apply")
def apply_approved_changes(
    request: ApplyRequest,
):

    try:

        # IMPORTANT:
        # Do NOT call TransactionManager directly here.
        #
        # Everything must pass through WorkflowEngine
        # so the approval/workflow state remains consistent.

        return workflow_engine.apply_approved_plan(
            request.approval_id
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


# --------------------------------------------------
# VALIDATION
# --------------------------------------------------

@app.post("/api/validate")
def validate_project(
    request: CommandRequest,
):

    try:

        return workflow_engine.validate_after_change(
            request.project_path
        )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# --------------------------------------------------
# PROJECT
# --------------------------------------------------

@app.post("/api/project")
def create_project(
    request: CommandRequest,
):

    try:

        return project_manager.create_project(
            request.project_path
        )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
