# RiskGate

RiskGate is an open-source GitHub Action for PR risk assessment, ownership mapping, and merge-threshold enforcement.

## What It Does

- Scores PR risk using blast radius, churn, security flags, infra proximity, and PR size.
- Recommends reviewers dynamically based on git history, review history, CODEOWNERS, and team config.
- Enforces review policy by risk level and sets commit status to block/allow merge.
- Publishes a PR comment, risk badge, and JSON audit artifact.

## Quickstart (use in another repository)

1. In the **project you want to analyze**, add `.riskgate.yml` at the repo root (optional; sensible defaults work with no file).
2. Add `.github/workflows/riskgate.yml`:

```yaml
name: RiskGate PR Analysis
on:
  pull_request:
    types: [opened, synchronize, ready_for_review]
permissions:
  pull-requests: write
  statuses: write
  contents: read
jobs:
  riskgate:
    runs-on: ubuntu-latest
    steps:
      - name: Run RiskGate
        uses: sfatty47/Riskgate@main
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          config: .riskgate.yml
```

3. Open a pull request (or push new commits to one). RiskGate runs, posts a PR comment, sets commit status `riskgate/threshold`, and uploads an audit artifact.

**Note:** `GITHUB_TOKEN` must be allowed to comment on PRs and set statuses (permissions above). For a **private** consumer repo, the default token is fine for same-repo workflows.

## Local Debug Run

```bash
GITHUB_TOKEN=xxx PR_NUMBER=123 GITHUB_REPOSITORY=org/repo python -m riskgate.main
```

## Config Reference

RiskGate supports optional config in `.riskgate.yml`:

- `ownership.teams`: per-team path globs and members.
- `thresholds.<level>`: required reviewers, required people/teams, merge blocking, notifications.
- `scoring.weights`: signal weights for risk scoring.
- `scoring.thresholds`: score boundaries for `critical/high/medium`.

## How Scoring Works

Signals normalized to 0-100:

- `blast_radius` (dependency graph downstream impact)
- `churn_score` (git commit frequency in 90 days)
- `security_hits` (pattern matches in added diff lines)
- `infra_proximity` (file touches infra-sensitive areas)
- `pr_size` (total lines changed)

Composite score = weighted sum of signals.

Default levels:

- `critical >= 80`
- `high >= 55`
- `medium >= 30`
- `low < 30`

## Testing

```bash
pip install -r requirements.txt
python -m pytest
```

## License

MIT
