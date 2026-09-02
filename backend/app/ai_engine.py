class AIEngine:
    def create_plan(self, command: str, project_path: str):
        return {
            "command": command,
            "project_path": project_path,
            "actions": [
                {"type": "analyze", "description": "Analyze existing project"},
                {"type": "locate", "description": "Locate smallest affected section"},
                {"type": "plan", "description": "Create minimal change plan"},
                {"type": "validate", "description": "Validate and test before deployment"},
            ],
            "rules": [
                "Never rewrite the entire project.",
                "Modify only the minimum required files.",
                "Preserve unrelated code.",
                "Require approval for destructive/high-impact changes.",
                "Never claim success without validation.",
            ],
        }
