from __future__ import annotations

import ast
import re
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path

_SKIP_DIRS = {"node_modules", ".venv", "__pycache__", ".git"}


@dataclass(slots=True)
class DependencyGraphBuilder:
    repo_path: str = "."

    def build(self) -> dict[str, list[str]]:
        root = Path(self.repo_path)
        file_imports: dict[str, set[str]] = defaultdict(set)
        all_files: set[str] = set()

        for path in root.rglob("*"):
            if path.is_dir() and path.name in _SKIP_DIRS:
                continue
            if not path.is_file():
                continue
            rel = str(path.relative_to(root))
            all_files.add(rel)

            if path.suffix == ".py":
                imports = self._python_imports(path)
            elif path.suffix in {".js", ".jsx", ".ts", ".tsx"}:
                imports = self._js_imports(path)
            else:
                continue
            for imp in imports:
                file_imports[rel].add(imp)

        reverse_graph: dict[str, list[str]] = defaultdict(list)
        for src, imports in file_imports.items():
            for dep in imports:
                target = self._resolve_to_file(dep, all_files)
                if target:
                    reverse_graph[target].append(src)

        for k in reverse_graph:
            reverse_graph[k] = sorted(set(reverse_graph[k]))
        return dict(reverse_graph)

    def compute_blast_radius(self, changed_files: list[str], dep_graph: dict[str, list[str]]) -> int:
        if not dep_graph:
            return 0
        visited: set[str] = set()
        q: deque[str] = deque(changed_files)

        while q:
            cur = q.popleft()
            for downstream in dep_graph.get(cur, []):
                if downstream in visited:
                    continue
                visited.add(downstream)
                q.append(downstream)

        repo_node_count = max(1, len(dep_graph))
        return int(min(100, (len(visited) / repo_node_count) * 100))

    def _python_imports(self, path: Path) -> set[str]:
        results: set[str] = set()
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            return results
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    results.add(name.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                results.add(node.module)
        return results

    def _js_imports(self, path: Path) -> set[str]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        hits = set(re.findall(r"import\\s+.*?from\\s+['\"]([^'\"]+)['\"]", text))
        hits.update(re.findall(r"require\\(['\"]([^'\"]+)['\"]\\)", text))
        return hits

    def _resolve_to_file(self, imp: str, all_files: set[str]) -> str | None:
        candidates = [
            f"{imp}.py",
            f"{imp}.js",
            f"{imp}.ts",
            f"{imp}/__init__.py",
            imp,
        ]
        normalized = imp.replace(".", "/")
        candidates.extend([f"{normalized}.py", f"{normalized}/__init__.py"])
        for c in candidates:
            if c in all_files:
                return c
        return None
