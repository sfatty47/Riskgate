from __future__ import annotations

import fnmatch
import subprocess
from collections import defaultdict
from dataclasses import dataclass

from riskgate.ownership.github import GitHubClient
from riskgate.types import FileOwnership, OwnershipReport, ReviewerCandidate


@dataclass(slots=True)
class OwnershipResolver:
    github: GitHubClient
    repo_path: str = "."

    def resolve(self, file_paths: list[str], config: dict) -> OwnershipReport:
        history = self.github.get_review_history(file_paths)
        codeowners = self._parse_codeowners()
        teams = config.get("ownership", {}).get("teams", {}) if config else {}

        file_owners: list[FileOwnership] = []
        for path in file_paths:
            ranked = self._rank_for_file(path, history.get(path, {}), codeowners, teams)
            file_owners.append(FileOwnership(path=path, reviewers=ranked[:3]))

        clusters: dict[tuple[str, ...], list[str]] = defaultdict(list)
        for item in file_owners:
            key = tuple(sorted(r.username for r in item.reviewers))
            clusters[key].append(item.path)
        return OwnershipReport(by_file=file_owners, clusters=dict(clusters))

    def _rank_for_file(
        self,
        path: str,
        review_freq: dict[str, int],
        codeowners: list[tuple[str, list[str]]],
        teams: dict,
    ) -> list[ReviewerCandidate]:
        scores: dict[str, ReviewerCandidate] = {}

        for author, score in self._git_authors(path).items():
            scores[author] = ReviewerCandidate(username=author, score=score, reasons=["recent commits"])

        for reviewer, count in review_freq.items():
            if reviewer not in scores:
                scores[reviewer] = ReviewerCandidate(username=reviewer, score=0.0, reasons=[])
            scores[reviewer].score += count * 1.5
            scores[reviewer].reasons.append("prior reviews")

        for pattern, owners in codeowners:
            if fnmatch.fnmatch(path, pattern):
                for owner in owners:
                    u = owner.lstrip("@").split("/")[-1]
                    if u not in scores:
                        scores[u] = ReviewerCandidate(username=u, score=0.0, reasons=[])
                    scores[u].score += 1.0
                    scores[u].reasons.append("CODEOWNERS")

        for _, team in teams.items():
            team_paths = team.get("paths", [])
            if any(fnmatch.fnmatch(path, p) for p in team_paths):
                for member in team.get("members", []):
                    if member not in scores:
                        scores[member] = ReviewerCandidate(username=member, score=0.0, reasons=[])
                    scores[member].score += 2.0
                    scores[member].reasons.append("team config")

        ranked = sorted(scores.values(), key=lambda x: x.score, reverse=True)
        for r in ranked:
            r.reasons = sorted(set(r.reasons))
        return ranked

    def _git_authors(self, path: str) -> dict[str, float]:
        cmd = ["git", "log", "--follow", "--format=%ae|%ad", "--date=short", "--since=90.days.ago", "--", path]
        proc = subprocess.run(cmd, cwd=self.repo_path, text=True, capture_output=True, check=False)
        if proc.returncode != 0:
            return {}
        scores: dict[str, float] = defaultdict(float)
        for line in proc.stdout.splitlines():
            if not line.strip() or "|" not in line:
                continue
            email, date = line.split("|", 1)
            username = email.split("@")[0]
            month = int(date.split("-")[1]) if len(date.split("-")) >= 2 else 1
            recency_boost = 2.0 if month >= 10 else 1.0
            scores[username] += recency_boost
        return dict(scores)

    def _parse_codeowners(self) -> list[tuple[str, list[str]]]:
        possible = ["CODEOWNERS", ".github/CODEOWNERS", "docs/CODEOWNERS"]
        for p in possible:
            try:
                with open(f"{self.repo_path}/{p}", "r", encoding="utf-8") as f:
                    lines = f.readlines()
                out: list[tuple[str, list[str]]] = []
                for line in lines:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split()
                    out.append((parts[0], parts[1:]))
                return out
            except FileNotFoundError:
                continue
        return []
