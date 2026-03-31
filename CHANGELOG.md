# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Fixed

### Removed

---

## [0.1.0] - 2026-03-31

First public release suitable for downstream workflows.

### Added

- GitHub Action (`action.yml`) for PR analysis: checkout with full history, install deps from action path, run `python -m riskgate.main`.
- **Analyzers:** diff (`git diff`), dependency graph (Python `ast` + JS/TS import regex), 90-day churn cache.
- **Risk engine:** weighted signals (blast radius, churn, security patterns on added lines, infra proximity, PR size), configurable `.riskgate.yml` scoring thresholds.
- **Ownership:** git author signals, GitHub review/search hints, CODEOWNERS + team path globs, ranked reviewer suggestions.
- **Thresholds:** per–risk-level policies, commit status `riskgate/threshold`, optional Slack webhook via `SLACK_WEBHOOK_URL`.
- **Output:** PR comment (upsert), PR description risk badge line, JSON audit artifact under `riskgate-audit/`.
- **Docs:** README quickstart, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `SUPPORT.md`, issue/PR templates.
- **CI:** workflow running `pytest` on push and pull requests.

[Unreleased]: https://github.com/sfatty47/Riskgate/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/sfatty47/Riskgate/releases/tag/v0.1.0
