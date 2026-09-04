from typing import Any, Dict

from .ai_provider import AIProvider


class AIEngine:
    """
    AI planning engine for AI App Builder.

    This layer is responsible for:
    - understanding the user's command
    - analyzing the project context
    - creating a safe development plan

    It does NOT modify files directly.
    """

    def __init__(self) -> None:
        self.provider = AIProvider()

    def create_plan(
        self,
        command: str,
        project_path: str,
    ) -> Dict[str, Any]:

        if not command.strip():
            raise ValueError(
                "Command cannot be empty."
            )

        if not project_path.strip():
            raise ValueError(
                "Project path cannot be empty."
            )

        system_prompt = """
You are the planning engine of a production-safe AI App Builder.

Return ONLY valid JSON.

Your job is to understand the user's request and create
a safe development plan.

The response must contain:

{
  "summary": "...",
  "architecture": {
    "goal": "...",
    "components": [],
    "dependencies": []
  },
  "plan": [
    {
      "step": 1,
      "description": "...",
      "files": [],
      "risk": "low|medium|high"
    }
  ],
  "affected_files": [],
  "risk": "low|medium|high",
  "validation_steps": []
}

Rules:

1. NEVER rewrite the entire project.
2. NEVER propose deleting the whole codebase.
3. Identify only the files and sections actually relevant
   to the user's request.
4. Preserve unrelated files and code.
5. Prefer the smallest safe change.
6. Do not invent files that are not justified by the request.
7. Do not directly apply or claim to have applied changes.
8. Destructive or high-risk operations must be clearly flagged.
9. The plan must be suitable for a later approval process.
10. Validation must be considered before any change is applied.
11. If the request is unclear, identify the ambiguity in the plan
    instead of making destructive assumptions.
"""

        payload = {
            "command": command,
            "project_path": project_path,
        }

        result = self.provider.generate_json(
            system_prompt,
            payload,
        )

        if not isinstance(result, dict):
            raise ValueError(
                "AI plan must be a JSON object."
            )

        result.setdefault(
            "summary",
            "",
        )

        result.setdefault(
            "architecture",
            {},
        )

        result.setdefault(
            "plan",
            [],
        )

        result.setdefault(
            "affected_files",
            [],
        )

        result.setdefault(
            "risk",
            "medium",
        )

        result.setdefault(
            "validation_steps",
            [],
        )

        return result
