from riskgate.ownership.resolver import OwnershipResolver


class FakeGitHub:
    def get_review_history(self, file_paths):
        return {path: {"alice": 2} for path in file_paths}


def test_resolver_outputs_ranked_candidates() -> None:
    resolver = OwnershipResolver(github=FakeGitHub(), repo_path=".")
    report = resolver.resolve(["src/payments/charge.py"], config={"ownership": {"teams": {"payments": {"paths": ["src/payments/**"], "members": ["bob"]}}}})
    assert report.by_file
    assert report.by_file[0].reviewers
