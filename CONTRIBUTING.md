# Contributing

Thanks for contributing to RiskGate.

## Development

- Python 3.11+
- Install dependencies: `pip install -r requirements.txt`
- Run tests: `python -m pytest`

## Coding Guidelines

- Use dataclasses for core models and reports.
- Keep GitHub API calls resilient to rate limits.
- Keep analyzers focused on changed files and efficient graph traversal.
- Add unit tests for new scoring, ownership, and threshold logic.

## Pull Requests

- Include clear rationale and test coverage.
- Update docs (`README.md`, `.riskgate.yml` reference) when behavior changes.
- Follow `CODE_OF_CONDUCT.md` in all project interactions.

## Releasing

RiskGate uses **SemVer** tags (`vMAJOR.MINOR.PATCH`). **Downstream repositories** should pin workflows to a tag, for example `uses: sfatty47/Riskgate@v0.1.0`, not `@main`.

This repository’s own `.github/workflows/riskgate.yml` may use `@main` to exercise the latest action code on each push; that does not change the recommendation for consumers.

### First release (`v0.1.0`) — maintainer steps

1. Ensure `main` is green (CI passes) and `CHANGELOG.md` has an entry for the version you are tagging.
2. Create an **annotated** tag on the commit you want to release:

   ```bash
   git checkout main
   git pull origin main
   git tag -a v0.1.0 -m "Release v0.1.0 — see CHANGELOG.md"
   ```

3. Push the tag:

   ```bash
   git push origin v0.1.0
   ```

4. On GitHub: **Releases → Create a new release**, choose tag `v0.1.0`, title `v0.1.0`, and paste the **0.1.0** section from `CHANGELOG.md` into the release notes.

### Subsequent releases

1. Add a dated section under `## [Unreleased]` in `CHANGELOG.md`, then move those bullets into `## [x.y.z] - YYYY-MM-DD` when you cut the release.
2. Repeat the tag/push/release steps with the new version (e.g. `v0.2.0`).
