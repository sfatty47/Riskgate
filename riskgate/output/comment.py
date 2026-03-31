from __future__ import annotations

from dataclasses import dataclass

from riskgate.ownership.github import GitHubClient
from riskgate.types import OwnershipReport, PRRiskReport, ThresholdResult

SIGNATURE = "<sub>RiskGate · [view config](.riskgate.yml) · [docs](https://github.com/your-org/riskgate)</sub>"


@dataclass(slots=True)
class CommentPublisher:
    github: GitHubClient

    def publish(
        self,
        pr_number: int,
        risk_report: PRRiskReport,
        ownership: OwnershipReport,
        threshold: ThresholdResult,
    ) -> None:
        body = self._render(risk_report, ownership, threshold)
        owner, repo = self.github.repository.split("/", 1)
        comments = self.github._request("GET", f"/repos/{owner}/{repo}/issues/{pr_number}/comments")
        if comments.status_code >= 400:
            return
        existing = None
        for c in comments.json():
            if SIGNATURE in c.get("body", ""):
                existing = c
                break

        if existing:
            self.github._request("PATCH", f"/repos/{owner}/{repo}/issues/comments/{existing['id']}", json={"body": body})
        else:
            self.github._request("POST", f"/repos/{owner}/{repo}/issues/{pr_number}/comments", json={"body": body})

    def _render(self, risk: PRRiskReport, ownership: OwnershipReport, threshold: ThresholdResult) -> str:
        lines = [
            f"## RiskGate Analysis - {risk.risk_level.value.upper()} RISK (score: {int(risk.score)})",
            "",
            "| File | Risk | Blast Radius | Churn | Security Flags |",
            "|------|------|-------------|-------|----------------|",
        ]
        for file in risk.files:
            flags = ", ".join(file.security_flags) if file.security_flags else "-"
            lines.append(
                f"| {file.path} | {file.risk_level.value.upper()} | {int(file.blast_radius)} modules | {int(file.churn_score)} commits | {flags} |"
            )

        lines.append("\n**Recommended Reviewers:**")
        seen = set()
        for entry in ownership.by_file:
            for r in entry.reviewers:
                if r.username in seen:
                    continue
                seen.add(r.username)
                reason = ", ".join(r.reasons[:2]) if r.reasons else "ownership signal"
                lines.append(f"- @{r.username} - {reason}")

        status = "blocked" if threshold.should_block else "ready"
        missing = f" · @{threshold.missing_required[0]} approval required" if threshold.missing_required else ""
        lines.append(f"\n**Threshold Status:** {'❌' if threshold.should_block else '✅'} {threshold.current}/{threshold.required} approvals{missing}")
        lines.append(f"**Merge:** {'Blocked until threshold met' if threshold.should_block else 'Allowed'}")
        lines.append("\n---")
        lines.append(SIGNATURE)
        return "\n".join(lines)
