from typing import Any, Dict

from .ai_provider import AIProvider


class AIEngine:
    """
    Central AI planning engine for AI App Builder.

    Responsibilities:
    - Understand the user's command.
    - Produce a structured development plan.
    - Identify architecture requirements.
    - Keep the planning stage separate from code application.
    """

    def __init__(self) -> None:
        self.ai = AIProvider()

    def create_plan(
        self,
        command: str,
        project_path: str,
    ) -> Dict[str, Any]:

        if not command.strip():
            raise ValueError(
                "Command cannot be empty."
            )

        return self.ai.generate_json(
            """
You are the planning engine of a
production-safe AI App Builder.

Return ONLY valid JSON.

Return exactly this structure:

{
  "summary": "short description of the requested change",
  "architecture": {
    "application_type": "web|api|mobile|other",
    "framework": "framework name or unknown",
    "language": "language name or unknown",
    "requirements": []
  },
  "actions": [
    {
      "type": "analyze|locate|plan|generate|validate|test",
      "description": "specific action"
    }
  ],
  "risk": "low|medium|high",
  "rules": [
    "Never rewrite the entire project.",
    "Modify only the minimum required files.",
    "Preserve unrelated code.",
    "Require approval before changes are applied.",
    "Never claim that changes have already been applied.",
    "Never claim validation passed unless validation actually passed."
  ]
}

Safety rules:

1. Never rewrite the entire project.
2. Never invent existing files or source code.
3. Prefer the smallest possible change.
4. Preserve unrelated code.
5. Do not delete files unless explicitly requested.
6. Do not apply changes.
7. Do not claim changes were applied.
8. Do not claim tests passed without actual test results.
9. High-risk or destructive operations must be identified.
10. The plan is advisory until user approval.
""",
            {
                "command": command,
                "project_path": project_path,
            },
        )
