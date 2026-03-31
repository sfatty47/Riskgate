from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import requests


@dataclass(slots=True)
class GitHubClient:
    token: str
    repository: str
    api_url: str = "https://api.github.com"

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        url = f"{self.api_url}{path}"
        headers = kwargs.pop("headers", {})
        headers.update(
            {
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self.token}",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )
        delay = 1.0
        for _ in range(5):
            resp = requests.request(method, url, headers=headers, timeout=30, **kwargs)
            if resp.status_code not in (403, 429):
                return resp
            retry_after = resp.headers.get("Retry-After")
            time.sleep(float(retry_after) if retry_after else delay)
            delay *= 2
        return resp

    def get_pull(self, pr_number: int) -> dict:
        owner, repo = self.repository.split("/", 1)
        resp = self._request("GET", f"/repos/{owner}/{repo}/pulls/{pr_number}")
        resp.raise_for_status()
        return resp.json()

    def get_pull_files(self, pr_number: int) -> list[dict]:
        owner, repo = self.repository.split("/", 1)
        resp = self._request("GET", f"/repos/{owner}/{repo}/pulls/{pr_number}/files")
        resp.raise_for_status()
        return resp.json()

    def get_current_approvals(self, pr_number: int) -> list[str]:
        owner, repo = self.repository.split("/", 1)
        resp = self._request("GET", f"/repos/{owner}/{repo}/pulls/{pr_number}/reviews")
        resp.raise_for_status()
        approvals = set()
        for review in resp.json():
            if review.get("state") == "APPROVED":
                user = review.get("user", {})
                if user.get("login"):
                    approvals.add(user["login"])
        return sorted(approvals)

    def get_review_history(self, file_paths: list[str]) -> dict[str, dict[str, int]]:
        owner, repo = self.repository.split("/", 1)
        out: dict[str, dict[str, int]] = {p: {} for p in file_paths}
        for path in file_paths:
            query = f"repo:{owner}/{repo} is:pr is:closed {path}"
            resp = self._request("GET", "/search/issues", params={"q": query, "per_page": 10})
            if resp.status_code >= 400:
                continue
            issues = resp.json().get("items", [])
            for issue in issues:
                login = issue.get("user", {}).get("login")
                if not login:
                    continue
                out[path][login] = out[path].get(login, 0) + 1
        return out

    def assign_reviewers(self, pr_number: int, reviewers: list[str]) -> None:
        if not reviewers:
            return
        owner, repo = self.repository.split("/", 1)
        resp = self._request(
            "POST",
            f"/repos/{owner}/{repo}/pulls/{pr_number}/requested_reviewers",
            json={"reviewers": reviewers[:10]},
        )
        if resp.status_code >= 400:
            return

    def set_commit_status(self, sha: str, state: str, description: str, context: str) -> None:
        owner, repo = self.repository.split("/", 1)
        self._request(
            "POST",
            f"/repos/{owner}/{repo}/statuses/{sha}",
            json={"state": state, "description": description[:140], "context": context},
        )
