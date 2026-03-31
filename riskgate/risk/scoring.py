from __future__ import annotations

from dataclasses import dataclass

from riskgate.types import RiskLevel

DEFAULT_WEIGHTS = {
    "blast_radius": 0.25,
    "churn_score": 0.20,
    "security_hits": 0.25,
    "infra_proximity": 0.15,
    "pr_size": 0.15,
}

DEFAULT_THRESHOLDS = {
    "critical": 80,
    "high": 55,
    "medium": 30,
}


@dataclass(slots=True)
class ScoringEngine:
    weights: dict[str, float]
    thresholds: dict[str, float]

    @classmethod
    def from_config(cls, config: dict) -> "ScoringEngine":
        scoring_cfg = config.get("scoring", {}) if config else {}
        weights = {**DEFAULT_WEIGHTS, **scoring_cfg.get("weights", {})}
        thresholds = {**DEFAULT_THRESHOLDS, **scoring_cfg.get("thresholds", {})}
        return cls(weights=weights, thresholds=thresholds)

    def composite_score(self, signals: dict[str, float]) -> float:
        score = 0.0
        for name, weight in self.weights.items():
            score += float(signals.get(name, 0.0)) * float(weight)
        return round(min(100.0, max(0.0, score)), 2)

    def level_for_score(self, score: float) -> RiskLevel:
        if score >= float(self.thresholds["critical"]):
            return RiskLevel.CRITICAL
        if score >= float(self.thresholds["high"]):
            return RiskLevel.HIGH
        if score >= float(self.thresholds["medium"]):
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def normalize_security_hits(self, weighted_hits: float) -> float:
        return min(100.0, weighted_hits * 20.0)

    def normalize_pr_size(self, lines_changed: int) -> float:
        return min(100.0, (lines_changed / 500.0) * 100.0)
