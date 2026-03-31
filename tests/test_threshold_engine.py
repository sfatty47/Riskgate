from riskgate.threshold.engine import ThresholdEngine
from riskgate.types import RiskLevel


class FakePublisher:
    def __init__(self):
        self.calls = []

    def publish(self, sha: str, state: str, description: str) -> None:
        self.calls.append((sha, state, description))


def test_threshold_blocks_when_requirements_missing() -> None:
    pub = FakePublisher()
    engine = ThresholdEngine(status_publisher=pub)
    result = engine.evaluate(
        risk_level=RiskLevel.HIGH,
        approvals=["alice"],
        team_members={"security-team": ["dave"]},
        config={"thresholds": {"high": {"min_reviewers": 2, "must_include": ["security-team"], "block_merge": True}}},
        sha="abc123",
    )
    assert result.should_block is True
    assert pub.calls[0][1] == "failure"
