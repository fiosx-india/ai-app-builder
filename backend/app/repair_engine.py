from typing import Any, Dict

from .ai_provider import AIProvider


class RepairEngine:
    """
    Generates a proposed repair from a structured error.

    It never modifies project files directly.
    """

    MAX_ATTEMPTS = 3

    def __init__(self) -> None:
        self.ai = AIProvider()

    def propose_fix(
        self,
        error: Dict[str, Any],
        context: Dict[str, Any],
        attempt: int,
    ) -> Dict[str, Any]:

        if attempt >= self.MAX_ATTEMPTS:

            return {
                "repair_allowed": False,
                "reason": (
                    "Maximum repair attempts reached."
                ),
            }

        return self.ai.generate_json(
            """
You are the repair engine of a production-safe
AI App Builder.

Return ONLY valid JSON.

Return:

{
  "repair_allowed": true,
  "file": "relative/path",
  "target": "exact function/class/section",
  "old_content": "exact existing content",
  "new_content": "minimal corrected content",
  "explanation": "why this fixes the error",
  "validation_steps": []
}

Rules:

1. Fix only the reported problem.
2. Never rewrite the entire file.
3. Preserve unrelated code.
4. Never delete unrelated code.
5. old_content must be exact.
6. The proposed repair must remain localized.
7. Do not claim that the repair has been applied.
8. If the error cannot be safely fixed, return
   repair_allowed=false.
""",
            {
                "error": error,
                "context": context,
                "attempt": attempt + 1,
            },
        )
