from fastapi import FastAPI
from pydantic import BaseModel

from .ai_engine import AIEngine
from .approval_engine import ApprovalEngine
from .validation_engine import ValidationEngine


app = FastAPI(
    title="AI App Builder",
    version="0.1.0",
    description="AI-powered application development platform",
)

ai_engine = AIEngine()
approval_engine = ApprovalEngine()
validation_engine = ValidationEngine()


class CommandRequest(BaseModel):
    command: str
    project_path: str = "./projects/default"


@app.get("/")
def root():
    return {
        "name": "AI App Builder",
        "status": "online",
        "version": "0.1.0",
    }


@app.post("/api/command")
def execute_command(request: CommandRequest):

    plan = ai_engine.create_plan(
        request.command,
        request.project_path,
    )

    approval = approval_engine.create_request(plan)

    return {
        "status": "approval_required",
        "plan": plan,
        "approval_id": approval["id"],
    }


@app.post("/api/validate")
def validate_project(request: CommandRequest):

    result = validation_engine.validate(
        request.project_path
    )

    return result
