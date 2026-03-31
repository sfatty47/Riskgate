from __future__ import annotations

import json
import os
from dataclasses import dataclass

from riskgate.analyzer.diff import DiffAnalyzer
from riskgate.output.audit import AuditWriter
from riskgate.output.badge import BadgeInjector
from riskgate.output.comment import CommentPublisher
from riskgate.ownership.github import GitHubClient
from riskgate.ownership.resolver import OwnershipResolver
from riskgate.risk.engine import RiskEngine
from riskgate.threshold.engine import ThresholdEngine
from riskgate.threshold.github_status import GitHubStatusPublisher
from riskgate.types import ChangedFile

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


@dataclass(slots=True)
class AppConfig:
    github_token: str
    repository: str
    pr_number: int
    config_path: str


def load_config(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    if yaml is None:
        return json.loads(open(path, "r", encoding="utf-8").read())
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def parse_env() -> AppConfig:
    token = os.getenv("GITHUB_TOKEN") or os.getenv("INPUT_GITHUB-TOKEN") or ""
    repo = os.getenv("GITHUB_REPOSITORY", "")
    pr_number = int(
        os.getenv("PR_NUMBER")
        or os.getenv("GITHUB_EVENT_PULL_REQUEST_NUMBER")
        or os.getenv("INPUT_PR_NUMBER", "0")
    )
    config_path = os.getenv("INPUT_CONFIG", ".riskgate.yml")

    if not token or not repo or not pr_number:
        raise RuntimeError("Missing GITHUB_TOKEN, GITHUB_REPOSITORY, or PR_NUMBER")
    return AppConfig(github_token=token, repository=repo, pr_number=pr_number, config_path=config_path)


def to_changed_files(raw_files: list[dict]) -> list[ChangedFile]:
    files: list[ChangedFile] = []
    for f in raw_files:
        files.append(
            ChangedFile(
                path=f.get("filename", ""),
                lines_added=int(f.get("additions", 0)),
                lines_removed=int(f.get("deletions", 0)),
                is_new=f.get("status") == "added",
                is_deleted=f.get("status") == "removed",
                patch=f.get("patch", ""),
            )
        )
    return files


def run() -> int:
    env = parse_env()
    config = load_config(env.config_path)

    gh = GitHubClient(token=env.github_token, repository=env.repository)
    pull = gh.get_pull(env.pr_number)
    base_sha = pull["base"]["sha"]
    head_sha = pull["head"]["sha"]

    # Prefer GitHub file patches; fallback to local git diff.
    gh_files = to_changed_files(gh.get_pull_files(env.pr_number))
    if gh_files:
        changed_files = gh_files
    else:
        changed_files = DiffAnalyzer().get_changed_files(base_sha, head_sha)

    risk_report = RiskEngine().assess(changed_files=changed_files, config=config)

    resolver = OwnershipResolver(github=gh)
    ownership = resolver.resolve([f.path for f in changed_files], config)

    approvals = gh.get_current_approvals(env.pr_number)
    teams = {
        name: cfg.get("members", [])
        for name, cfg in config.get("ownership", {}).get("teams", {}).items()
    }
    threshold = ThresholdEngine(status_publisher=GitHubStatusPublisher(gh)).evaluate(
        risk_level=risk_report.risk_level,
        approvals=approvals,
        team_members=teams,
        config=config,
        sha=head_sha,
    )

    CommentPublisher(gh).publish(env.pr_number, risk_report, ownership, threshold)
    BadgeInjector(gh).inject(env.pr_number, risk_report.risk_level)
    audit_path = AuditWriter().write(env.pr_number, risk_report, ownership, threshold)

    reviewers = []
    for file in ownership.by_file:
        for r in file.reviewers:
            if r.username not in reviewers:
                reviewers.append(r.username)
    gh.assign_reviewers(env.pr_number, reviewers[:10])

    print(f"RiskGate completed. Audit: {audit_path}")
    return 1 if threshold.should_block else 0


if __name__ == "__main__":
    raise SystemExit(run())
