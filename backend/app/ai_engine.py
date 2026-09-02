import json
import os
from pathlib import Path
from typing import Any, Dict

from openai import OpenAI


class AIEngine:
    """OpenAI-backed planner. It creates plans but never writes project files."""

    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured.")
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-5-mini")

    def create_plan(self, command: str, project_path: str) -> Dict[str, Any]:
        root = Path(project_path)
        project_files = []
        if root.exists():
            for path in root.rglob("*"):
                if path.is_file() and ".git" not in path.parts:
                    project_files.append(str(path.relative_to(root)))
                    if len(project_files) >= 300:
                        break

        context = {
            "command": command,
            "project_path": project_path,
            "files": project_files,
            "rules": [
                "Never rewrite the entire project.",
                "Modify only the minimum required files.",
                "Preserve unrelated code.",
                "Do not delete files unless explicitly requested.",
                "Require approval before applying changes.",
                "Return a plan only; do not claim code was changed.",
            ],
        }

        response = self.client.responses.create(
            model=self.model,
            input=(
                "You are the planning engine for a safe AI App Builder. "
                "Analyze the command and project file list. Return JSON with "
                "summary, risk, affected_files, changes, validation_steps. "
                "Only list files actually needed. Do not claim completed work.\n\n"
                + json.dumps(context, ensure_ascii=False)
            ),
        )

        text = response.output_text.strip()
        try:
            plan = json.loads(text)
        except json.JSONDecodeError:
            plan = {
                "summary": text,
                "risk": "review_required",
                "affected_files": [],
                "changes": [],
                "validation_steps": ["Run project validation and tests."],
            }

        plan.update({
            "command": command,
            "project_path": project_path,
            "approval_required": True,
            "openai_model": self.model,
        })
        return plan
