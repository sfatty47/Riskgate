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
