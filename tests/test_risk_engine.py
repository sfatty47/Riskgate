from riskgate.risk.engine import RiskEngine
from riskgate.types import ChangedFile


def test_risk_engine_assess() -> None:
    engine = RiskEngine(repo_path=".")
    changed = [
        ChangedFile(
            path="src/auth/jwt.py",
            lines_added=40,
            lines_removed=5,
            patch="+token = os.environ.get('API_KEY')\n+encrypt(data)",
        )
    ]
    report = engine.assess(changed, config={})
    assert report.files
    assert report.score >= 0
