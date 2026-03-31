from __future__ import annotations

import subprocess
from dataclasses import dataclass

from riskgate.types import ChangedFile


@dataclass(slots=True)
class DiffAnalyzer:
    repo_path: str = "."

    def get_changed_files(self, base_sha: str, head_sha: str) -> list[ChangedFile]:
        names = self._run(["git", "diff", "--name-status", base_sha, head_sha])
        stats = self._run(["git", "diff", "--numstat", base_sha, head_sha])
        patches = self._run(["git", "diff", base_sha, head_sha])

        metadata: dict[str, ChangedFile] = {}
        for line in names.splitlines():
            if not line.strip():
                continue
            status, path = line.split("\t", 1)
            metadata[path] = ChangedFile(
                path=path,
                is_new=status.startswith("A"),
                is_deleted=status.startswith("D"),
            )

        for line in stats.splitlines():
            if not line.strip():
                continue
            added, removed, path = line.split("\t", 2)
            if path not in metadata:
                metadata[path] = ChangedFile(path=path)
            file = metadata[path]
            file.lines_added = int(added) if added.isdigit() else 0
            file.lines_removed = int(removed) if removed.isdigit() else 0

        current_file: str | None = None
        current_patch: list[str] = []
        for line in patches.splitlines():
            if line.startswith("diff --git "):
                if current_file and current_file in metadata:
                    metadata[current_file].patch = "\n".join(current_patch)
                parts = line.split(" b/", 1)
                current_file = parts[1] if len(parts) == 2 else None
                current_patch = [line]
            elif current_file:
                current_patch.append(line)
        if current_file and current_file in metadata:
            metadata[current_file].patch = "\n".join(current_patch)

        return sorted(metadata.values(), key=lambda f: f.path)

    def _run(self, cmd: list[str]) -> str:
        proc = subprocess.run(
            cmd,
            cwd=self.repo_path,
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            return ""
        return proc.stdout
