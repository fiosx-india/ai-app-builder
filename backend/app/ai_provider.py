"""
AI Engine

Purpose:
High-level AI planning layer for the AI App Builder.

AIProvider handles OpenAI communication.
AIEngine handles project planning and converts
natural-language commands into structured plans.
"""

from typing import Any, Dict

from .ai_provider import AIProvider


class AIEngine:
    """
    High-level AI planning engine.

    This class does not modify project files.
    It only analyzes the user command and returns
    a structured development plan.
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

Your job is to analyze the user's natural-language command
and create a structured development plan.

Return ONLY valid JSON.

Required JSON structure:

{
  "summary": "short explanation of the requested change",
  "architecture": {
    "type": "web|api|fullstack|other",
    "components": [],
    "notes": []
  },
  "risk": "low|medium|high",
  "plan": [
    {
      "step": 1,
      "description": "specific development step"
    }
  ],
  "validation_steps": []
}

Safety rules:

1. Do not modify files.
2. Do not claim that anything has already been changed.
3. Do not invent files that are known to exist.
4. Prefer the smallest safe implementation.
5. Preserve existing project architecture.
6. Do not propose destructive actions unless explicitly requested.
7. Flag potentially destructive or high-risk operations as high risk.
8. The plan must be concrete enough for the code-generation engine
   to produce localized changes.
9. Never rewrite the entire project for a localized request.
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
            "risk",
            "medium",
        )

        result.setdefault(
            "plan",
            [],
        )

        result.setdefault(
            "validation_steps",
            [],
        )

        return result
