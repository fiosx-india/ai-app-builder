class SandboxRunner:
    def run(self, command, project_path):
        return {
            "executed": False,
            "safe": False,
            "message": "Sandbox adapter not connected yet.",
            "command": command,
            "project_path": project_path,
        }
