from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Sequence


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(slots=True)
class ChangedFile:
    path: str
    lines_added: int = 0
    lines_removed: int = 0
    is_new: bool = False
    is_deleted: bool = False
    patch: str = ""


@dataclass(slots=True)
class FileRiskBreakdown:
    path: str
    score: float
    risk_level: RiskLevel
    blast_radius: float
    churn_score: float
    security_hits: int
    infra_proximity: float
    pr_size: float
    security_flags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PRRiskReport:
    score: float
    risk_level: RiskLevel
    files: list[FileRiskBreakdown]


@dataclass(slots=True)
class ReviewerCandidate:
    username: str
    score: float
    reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class FileOwnership:
    path: str
    reviewers: list[ReviewerCandidate]


@dataclass(slots=True)
class OwnershipReport:
    by_file: list[FileOwnership]
    clusters: dict[tuple[str, ...], list[str]]


@dataclass(slots=True)
class ThresholdPolicy:
    min_reviewers: int = 1
    must_include: list[str] = field(default_factory=list)
    block_merge: bool = False
    notify: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ThresholdResult:
    met: bool
    required: int
    current: int
    missing_required: list[str]
    should_block: bool
    description: str


@dataclass(slots=True)
class RuntimeContext:
    owner: str
    repo: str
    pr_number: int
    base_sha: str
    head_sha: str
    author: str
    changed_files: Sequence[ChangedFile]
    config: Dict
