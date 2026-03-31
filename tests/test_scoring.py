from riskgate.risk.scoring import ScoringEngine
from riskgate.types import RiskLevel


def test_composite_score_and_level() -> None:
    engine = ScoringEngine.from_config({})
    score = engine.composite_score(
        {
            "blast_radius": 80,
            "churn_score": 60,
            "security_hits": 40,
            "infra_proximity": 20,
            "pr_size": 10,
        }
    )
    assert score > 0
    assert engine.level_for_score(85) == RiskLevel.CRITICAL
    assert engine.level_for_score(60) == RiskLevel.HIGH
    assert engine.level_for_score(40) == RiskLevel.MEDIUM
    assert engine.level_for_score(10) == RiskLevel.LOW
