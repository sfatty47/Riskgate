from __future__ import annotations

from dataclasses import dataclass

from riskgate.ownership.github import GitHubClient


@dataclass(slots=True)
class GitHubStatusPublisher:
    github: GitHubClient

    def publish(self, sha: str, state: str, description: str) -> None:
        self.github.set_commit_status(
            sha=sha,
            state=state,
            description=description,
            context="riskgate/threshold",
        )
