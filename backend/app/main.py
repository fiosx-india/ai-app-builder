from fastapi import FastAPI
from pydantic import BaseModel
from .ai_engine import AIEngine
from .approval_engine import ApprovalEngine
from .validation_engine import ValidationEngine
from .project_manager import ProjectManager

app = FastAPI(title="AI App Builder", version="0.2.0")
ai_engine = AIEngine()
approval_engine = ApprovalEngine()
validation_engine = ValidationEngine()
project_manager = ProjectManager()

class CommandRequest(BaseModel):
    command: str
    project_path: str = "./projects/default"

class ApprovalRequest(BaseModel):
    approval_id: str

@app.get("/")
def root():
    return {"name": "AI App Builder", "status": "online", "version": "0.2.0"}

@app.post("/api/command")
def execute_command(request: CommandRequest):
    plan = ai_engine.create_plan(request.command, request.project_path)
    approval = approval_engine.create_request(plan)
    return {"status": "approval_required", "plan": plan, "approval_id": approval["id"]}

@app.post("/api/approve")
def approve(request: ApprovalRequest):
    return approval_engine.approve(request.approval_id)

@app.post("/api/reject")
def reject(request: ApprovalRequest):
    return approval_engine.reject(request.approval_id)

@app.get("/api/approval/{approval_id}")
def get_approval(approval_id: str):
    return approval_engine.get_request(approval_id)

@app.post("/api/validate")
def validate_project(request: CommandRequest):
    return validation_engine.validate(request.project_path)

@app.post("/api/project")
def create_project(request: CommandRequest):
    return project_manager.create_project(request.project_path)
