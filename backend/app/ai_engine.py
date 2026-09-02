class AIEngine:

    def create_plan(self, command: str, project_path: str):

        return {
            "command": command,
            "project_path": project_path,
            "actions": [
                {
                    "type": "analyze",
                    "description": "Analyze the existing project",
                },
                {
                    "type": "plan",
                    "description": "Create a development plan",
                },
            ],
            "rule": (
                "Never rewrite the entire project. "
                "Only modify the minimum required files."
            ),
        }
