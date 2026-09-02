from typing import Any, Dict
from .ai_provider import AIProvider


class CodeGenerationEngine:
    """
    Generates proposed localized changes.

    IMPORTANT:
    This class never writes directly to the project.
    """

    def __init__(self) -> None:
        self.ai = AIProvider()

    def propose(
        self,
        command: str,
        architecture: Dict[str, Any],
        inventory: Dict[str, Any],
    ) -> Dict[str, Any]:

        return self.ai.generate_json(
            """
You are the code-generation engine of a production-safe AI App Builder.

Return ONLY valid JSON.

The response must contain:

{
  "summary": "...",
  "risk": "low|medium|high",
  "changes": [
    {
      "file": "relative/path",
      "action": "modify|create",
      "target": "exact function/class/section",
      "old_content": "exact existing content",
      "new_content": "replacement content",
      "description": "what changed"
    }
  ],
  "validation_steps": []
}

Rules:

1. Never rewrite the entire project.
2. Modify the smallest possible area.
3. Preserve unrelated code.
4. Do not invent existing code.
5. For modifications, old_content must exactly match the existing source.
6. Never delete a file unless explicitly requested.
7. Do not claim the changes have already been applied.
8. High-risk or destructive changes must be flagged.
9. Prefer modifying one exact function/section rather than an entire file.
""",
            {
                "command": command,
                "architecture": architecture,
                "inventory": inventory,
            },
        )
