from __future__ import annotations

from dataclasses import dataclass

from riskgate.ownership.github import GitHubClient
from riskgate.types import RiskLevel


@dataclass(slots=True)
class BadgeInjector:
    github: GitHubClient

    def inject(self, pr_number: int, risk_level: RiskLevel) -> None:
        badge = self._badge_line(risk_level)
        pull = self.github.get_pull(pr_number)
        body = pull.get("body") or ""
        lines = body.splitlines()
        if lines and lines[0].startswith("RiskGate:"):
            lines[0] = badge
        else:
            lines = [badge, "", *lines]

        owner, repo = self.github.repository.split("/", 1)
        self.github._request("PATCH", f"/repos/{owner}/{repo}/pulls/{pr_number}", json={"body": "\n".join(lines)})

    def _badge_line(self, risk_level: RiskLevel) -> str:
        mapping = {
            RiskLevel.LOW: "RiskGate: 🟢 LOW",
            RiskLevel.MEDIUM: "RiskGate: 🟡 MEDIUM",
            RiskLevel.HIGH: "RiskGate: 🔴 HIGH",
            RiskLevel.CRITICAL: "RiskGate: 🚨 CRITICAL",
        }
        return mapping[risk_level]
