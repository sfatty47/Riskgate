from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from riskgate.types import OwnershipReport, PRRiskReport, ThresholdResult


@dataclass(slots=True)
class AuditWriter:
    output_dir: str = "./riskgate-audit"

    def write(
        self,
        pr_number: int,
        risk_report: PRRiskReport,
        ownership: OwnershipReport,
        threshold_result: ThresholdResult,
    ) -> str:
        target = Path(self.output_dir)
        target.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pr_number": pr_number,
            "risk_level": risk_report.risk_level.value,
            "score": risk_report.score,
            "per_file_breakdown": [asdict(f) for f in risk_report.files],
            "recommended_reviewers": {
                f.path: [r.username for r in f.reviewers] for f in ownership.by_file
            },
            "threshold_policy": {
                "required": threshold_result.required,
                "missing": threshold_result.missing_required,
            },
            "approval_status": {
                "current": threshold_result.current,
                "met": threshold_result.met,
            },
            "final_decision": "blocked" if threshold_result.should_block else "allowed",
        }
        out_file = target / f"{pr_number}.json"
        out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return str(out_file)
