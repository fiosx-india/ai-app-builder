import os
from typing import Any, Dict, Optional

from github import Github


class GitHubManager:
    """
    GitHub integration layer.

    Responsible for:
    - connection
    - repository information
    - branch creation
    - commit preparation
    - pull-request creation

    It never deploys code directly.
    """

    def __init__(self) -> None:
        self.token = os.getenv("GITHUB_TOKEN")
        self.repository_name = os.getenv(
            "GITHUB_REPOSITORY"
        )
        self.default_branch = os.getenv(
            "GITHUB_BRANCH",
            "main",
        )

        self.client: Optional[Github] = None

        if self.token:
            self.client = Github(self.token)

    def status(self) -> Dict[str, Any]:
        return {
            "connected": self.client is not None,
            "repository": self.repository_name,
            "branch": self.default_branch,
        }

    def _require_connection(self):
        if not self.client:
            raise RuntimeError(
                "GITHUB_TOKEN is not configured."
            )

        if not self.repository_name:
            raise RuntimeError(
                "GITHUB_REPOSITORY is not configured."
            )

    def get_repository(self):
        self._require_connection()

        return self.client.get_repo(
            self.repository_name
        )

    def create_branch(
        self,
        branch_name: str,
    ) -> Dict[str, Any]:

        repository = self.get_repository()

        base = repository.get_branch(
            self.default_branch
        )

        repository.create_git_ref(
            ref=f"refs/heads/{branch_name}",
            sha=base.commit.sha,
        )

        return {
            "created": True,
            "branch": branch_name,
            "base": self.default_branch,
            "sha": base.commit.sha,
        }

    def create_pull_request(
        self,
        branch_name: str,
        title: str,
        body: str,
    ) -> Dict[str, Any]:

        repository = self.get_repository()

        pull_request = (
            repository.create_pull(
                title=title,
                body=body,
                head=branch_name,
                base=self.default_branch,
            )
        )

        return {
            "created": True,
            "number": pull_request.number,
            "url": pull_request.html_url,
            "branch": branch_name,
            "base": self.default_branch,
        }
