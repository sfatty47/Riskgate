"""End-to-end smoke test: mock GitHub API, run riskgate.main.run() without network."""

from __future__ import annotations

import json
import pathlib
from urllib.parse import urlparse

import pytest
import requests

from riskgate.main import run


class _FakeResponse:
    def __init__(self, status_code: int = 200, payload: dict | list | None = None) -> None:
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.headers: dict[str, str] = {}

    def json(self) -> dict | list:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def _fake_pull_payload() -> dict:
    return {
        "base": {"sha": "base123"},
        "head": {"sha": "head123"},
        "body": "Existing PR description",
        "user": {"login": "contrib"},
    }


def _fake_files_payload() -> list[dict]:
    return [
        {
            "filename": "src/auth/jwt.py",
            "additions": 42,
            "deletions": 4,
            "status": "modified",
            "patch": "+token = os.environ.get('API_KEY')\n+encrypt(data)",
        },
        {
            "filename": ".github/workflows/ci.yml",
            "additions": 8,
            "deletions": 1,
            "status": "modified",
            "patch": "+name: CI",
        },
    ]


def test_main_run_smoke_mocked_github(monkeypatch: pytest.MonkeyPatch, tmp_path: pathlib.Path) -> None:
    """Full pipeline: env + cwd isolated; no real HTTP."""
    work = tmp_path
    monkeypatch.chdir(work)
    (work / ".riskgate.yml").write_text(
        "ownership:\n  teams: {}\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "org/repo")
    monkeypatch.setenv("PR_NUMBER", "123")
    monkeypatch.setenv("INPUT_CONFIG", str(work / ".riskgate.yml"))

    calls: list[tuple[str, str]] = []

    def fake_request(
        method: str,
        url: str,
        headers: dict | None = None,
        timeout: int = 30,
        **kwargs: object,
    ) -> _FakeResponse:
        calls.append((method, url))
        path = urlparse(url).path

        if method == "GET" and path == "/repos/org/repo/pulls/123":
            return _FakeResponse(payload=_fake_pull_payload())
        if method == "GET" and path == "/repos/org/repo/pulls/123/files":
            return _FakeResponse(payload=_fake_files_payload())
        if method == "GET" and path == "/repos/org/repo/pulls/123/reviews":
            return _FakeResponse(
                payload=[
                    {"state": "APPROVED", "user": {"login": "alice"}},
                    {"state": "COMMENTED", "user": {"login": "bob"}},
                ]
            )
        if method == "GET" and path == "/search/issues":
            return _FakeResponse(
                payload={"items": [{"user": {"login": "alice"}}, {"user": {"login": "carol"}}]}
            )
        if method == "GET" and path == "/repos/org/repo/issues/123/comments":
            return _FakeResponse(payload=[])
        if method == "POST" and path == "/repos/org/repo/issues/123/comments":
            return _FakeResponse(payload={})
        if method == "PATCH" and path == "/repos/org/repo/pulls/123":
            return _FakeResponse(payload={})
        if method == "POST" and path == "/repos/org/repo/statuses/head123":
            return _FakeResponse(payload={})
        if method == "POST" and path == "/repos/org/repo/pulls/123/requested_reviewers":
            return _FakeResponse(payload={})

        pytest.fail(f"Unexpected request: {method} {path}")

    monkeypatch.setattr(requests, "request", fake_request)

    code = run()

    assert code == 0
    audit_file = work / "riskgate-audit" / "123.json"
    assert audit_file.is_file()
    audit = json.loads(audit_file.read_text(encoding="utf-8"))
    assert "risk_level" in audit
    assert "final_decision" in audit
    assert audit["final_decision"] in ("allowed", "blocked")

    paths = [urlparse(u).path for _, u in calls]
    assert "/repos/org/repo/statuses/head123" in paths
    assert "/repos/org/repo/issues/123/comments" in paths
    assert ("GET", "/repos/org/repo/pulls/123") in [(m, urlparse(u).path) for m, u in calls]
