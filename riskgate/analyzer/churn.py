from __future__ import annotations

import subprocess
from dataclasses import dataclass, field


@dataclass(slots=True)
class ChurnAnalyzer:
    repo_path: str = "."
    cache: dict[str, int] = field(default_factory=dict)

    def get_churn_score(self, filepath: str) -> int:
        commits = self.get_commit_count(filepath)
        return min(100, int((commits / 20) * 100))

    def get_commit_count(self, filepath: str) -> int:
        if filepath in self.cache:
            return self.cache[filepath]
        cmd = [
            "git",
            "log",
            "--follow",
            "--oneline",
            "--since=90.days.ago",
            "--",
            filepath,
        ]
        proc = subprocess.run(
            cmd,
            cwd=self.repo_path,
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            self.cache[filepath] = 0
            return 0
        count = len([line for line in proc.stdout.splitlines() if line.strip()])
        self.cache[filepath] = count
        return count
