from pathlib import Path
from typing import Any, Dict, List
from .ai_provider import AIProvider


class CodeGenerationEngine:
    """Generates proposed localized changes. Never writes to the project."""

    MAX_CONTEXT_FILES = 8
    MAX_FILE_CHARS = 12000

    def __init__(self) -> None:
        self.ai = AIProvider()

    def build_source_context(
        self,
        project_path: str,
        affected_files: List[str],
    ) -> List[Dict[str, Any]]:
        root = Path(project_path).resolve()
        context = []

        for relative_file in affected_files[: self.MAX_CONTEXT_FILES]:
            target = (root / relative_file).resolve()
            try:
                target.relative_to(root)
            except ValueError:
                continue

            if target.exists() and target.is_file():
                try:
                    content = target.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                context.append({
                    "file": relative_file,
                    "exists": True,
                    "content": content[: self.MAX_FILE_CHARS],
                })
            else:
                context.append({"file": relative_file, "exists": False, "content": ""})

        return context

    def _validate_proposal(self, result: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(result, dict):
            raise ValueError("Code proposal must be a JSON object.")

        changes = result.get("changes", [])
        if not isinstance(changes, list):
            raise ValueError("Code proposal changes must be a list.")

        for change in changes:
            if not isinstance(change, dict):
                raise ValueError("Each change must be an object.")
            if change.get("action") not in {"modify", "create"}:
                raise ValueError("Each change must use action modify or create.")
            if not isinstance(change.get("file"), str) or not change["file"].strip():
                raise ValueError("Each change must contain a relative file path.")
            if not isinstance(change.get("new_content"), str):
                raise ValueError("Each change must contain new_content.")
            if change["action"] == "modify" and not isinstance(change.get("old_content"), str):
                raise ValueError("Modify changes must contain exact old_content.")
            if change["action"] == "create" and change.get("old_content", "") not in {"", None}:
                raise ValueError("Create changes must not contain old_content.")

        result.setdefault("summary", "")
        result.setdefault("risk", "medium")
        result.setdefault("validation_steps", [])
        return result

    def propose(
        self,
        command: str,
        architecture: Dict[str, Any],
        inventory: Dict[str, Any],
        project_path: str | None = None,
        affected_files: List[str] | None = None,
    ) -> Dict[str, Any]:

        source_context = []
        if project_path and affected_files:
            source_context = self.build_source_context(project_path, affected_files)

        result = self.ai.generate_json(
            """
You are the code-generation engine of a production-safe AI App Builder.
Return ONLY valid JSON.

For modifications, you may only use exact old_content that appears in source_context.
If required source is not supplied, return no change rather than inventing code.

Required JSON:
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
4. Never invent existing code.
5. Never delete files.
6. Do not claim changes were applied.
7. Flag high-risk changes.
""",
            {
                "command": command,
                "architecture": architecture,
                "inventory": inventory,
                "source_context": source_context,
            },
        )

        return self._validate_proposal(result)
