from __future__ import annotations

import os
from dataclasses import dataclass

import requests

from riskgate.threshold.github_status import GitHubStatusPublisher
from riskgate.types import RiskLevel, ThresholdPolicy, ThresholdResult

DEFAULT_THRESHOLDS = {
    "critical": {"min_reviewers": 3, "must_include": ["security-team", "tech-lead"], "block_merge": True, "notify": []},
    "high": {"min_reviewers": 2, "must_include": ["domain-owner"], "block_merge": True, "notify": []},
    "medium": {"min_reviewers": 1, "must_include": [], "block_merge": False, "notify": []},
    "low": {"min_reviewers": 1, "must_include": [], "block_merge": False, "notify": []},
}


@dataclass(slots=True)
class ThresholdEngine:
    status_publisher: GitHubStatusPublisher

    def evaluate(
        self,
        risk_level: RiskLevel,
        approvals: list[str],
        team_members: dict[str, list[str]],
        config: dict,
        sha: str,
    ) -> ThresholdResult:
        policy = self._policy_for_level(risk_level, config)

        required_people = self._expand_required(policy.must_include, team_members)
        missing = [r for r in required_people if r not in approvals]

        met = len(approvals) >= policy.min_reviewers and not missing
        should_block = policy.block_merge and not met
        state = "failure" if should_block else "success"
        description = self._description(policy.min_reviewers, len(approvals), missing)

        self.status_publisher.publish(sha=sha, state=state, description=description)
        self._notify_if_needed(policy.notify, risk_level, description)
        return ThresholdResult(
            met=met,
            required=policy.min_reviewers,
            current=len(approvals),
            missing_required=missing,
            should_block=should_block,
            description=description,
        )

    def _policy_for_level(self, risk_level: RiskLevel, config: dict) -> ThresholdPolicy:
        merged = dict(DEFAULT_THRESHOLDS)
        merged.update(config.get("thresholds", {}) if config else {})
        cfg = merged[risk_level.value]
        return ThresholdPolicy(
            min_reviewers=int(cfg.get("min_reviewers", 1)),
            must_include=list(cfg.get("must_include", [])),
            block_merge=bool(cfg.get("block_merge", False)),
            notify=list(cfg.get("notify", [])),
        )

    def _expand_required(self, must_include: list[str], team_members: dict[str, list[str]]) -> list[str]:
        required: list[str] = []
        for token in must_include:
            if token in team_members:
                required.extend(team_members[token])
            else:
                required.append(token)
        seen = set()
        out = []
        for r in required:
            if r not in seen:
                out.append(r)
                seen.add(r)
        return out

    def _description(self, min_reviewers: int, current: int, missing: list[str]) -> str:
        base = f"{current}/{min_reviewers} required approvals"
        if missing:
            return f"{base} · @{missing[0]} review needed"
        return base

    def _notify_if_needed(self, channels: list[str], risk_level: RiskLevel, description: str) -> None:
        if not channels:
            return
        webhook = os.getenv("SLACK_WEBHOOK_URL", "")
        if not webhook:
            return
        text = f"RiskGate {risk_level.value.upper()}: {description}"
        for channel in channels:
            payload = {"text": text, "channel": channel.replace("slack:", "")}
            try:
                requests.post(webhook, json=payload, timeout=10)
            except Exception:
                continue
