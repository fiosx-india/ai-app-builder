class DeploymentManager:
    def deploy(self, project_path):
        return {
            "deployed": False,
            "status": "blocked",
            "reason": "Deployment adapter is not connected; validation must pass first.",
            "project_path": project_path,
        }
