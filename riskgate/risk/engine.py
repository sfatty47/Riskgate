from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass

from riskgate.analyzer.churn import ChurnAnalyzer
from riskgate.analyzer.graph import DependencyGraphBuilder
from riskgate.risk.patterns import INFRA_PATTERNS, SECURITY_PATTERNS
from riskgate.risk.scoring import ScoringEngine
from riskgate.types import ChangedFile, FileRiskBreakdown, PRRiskReport


@dataclass(slots=True)
class RiskEngine:
    repo_path: str = "."

    def assess(self, changed_files: list[ChangedFile], config: dict) -> PRRiskReport:
        scorer = ScoringEngine.from_config(config)
        churn = ChurnAnalyzer(self.repo_path)
        graph_builder = DependencyGraphBuilder(self.repo_path)
        dep_graph = graph_builder.build()

        changed_paths = [f.path for f in changed_files]
        pr_blast = graph_builder.compute_blast_radius(changed_paths, dep_graph)

        file_reports: list[FileRiskBreakdown] = []
        for file in changed_files:
            security_hits, flags = self._security_signals(file.patch)
            infra = self._infra_proximity(file.path)
            size = scorer.normalize_pr_size(file.lines_added + file.lines_removed)
            churn_score = churn.get_churn_score(file.path)

            signals = {
                "blast_radius": float(pr_blast),
                "churn_score": float(churn_score),
                "security_hits": scorer.normalize_security_hits(security_hits),
                "infra_proximity": float(infra),
                "pr_size": float(size),
            }
            score = scorer.composite_score(signals)
            file_reports.append(
                FileRiskBreakdown(
                    path=file.path,
                    score=score,
                    risk_level=scorer.level_for_score(score),
                    blast_radius=float(pr_blast),
                    churn_score=float(churn_score),
                    security_hits=int(security_hits),
                    infra_proximity=float(infra),
                    pr_size=float(size),
                    security_flags=flags,
                )
            )

        pr_score = self._aggregate_pr_score(file_reports)
        pr_level = scorer.level_for_score(pr_score)
        return PRRiskReport(score=pr_score, risk_level=pr_level, files=file_reports)

    def _security_signals(self, patch: str) -> tuple[int, list[str]]:
        if not patch:
            return 0, []
        weighted_hits = 0.0
        flags: list[str] = []
        added_lines = "\n".join(line[1:] for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++"))
        for pattern in SECURITY_PATTERNS:
            if re.search(pattern["pattern"], added_lines, flags=re.IGNORECASE):
                weighted_hits += float(pattern["weight"])
                flags.append(str(pattern["name"]))
        return int(round(weighted_hits)), flags

    def _infra_proximity(self, path: str) -> int:
        for rule in INFRA_PATTERNS:
            if rule == "migrations/" and "migrations/" in path:
                return 100
            if rule == ".github/*.yml" and fnmatch.fnmatch(path, ".github/*.yml"):
                return 100
            if fnmatch.fnmatch(path, rule):
                return 100
        return 0

    def _aggregate_pr_score(self, file_reports: list[FileRiskBreakdown]) -> float:
        if not file_reports:
            return 0.0
        scores = sorted([f.score for f in file_reports], reverse=True)
        weighted_sum = 0.0
        denominator = 0.0
        for idx, score in enumerate(scores):
            weight = max(0.5, 1.0 - (idx * 0.1))
            weighted_sum += score * weight
            denominator += weight
        return round(weighted_sum / denominator, 2)
