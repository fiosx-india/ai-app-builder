import os

class GitHubManager:
    def status(self):
        return {
            "connected": bool(os.getenv("GITHUB_TOKEN")),
            "repository": os.getenv("GITHUB_REPOSITORY"),
            "branch": os.getenv("GITHUB_BRANCH", "main"),
        }
