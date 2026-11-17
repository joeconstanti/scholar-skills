# CI validation

The `test` workflow runs the complete standard-library unittest suite, including skill lint, on Ubuntu with Python 3.10 and 3.12. No dependency install, credentials, paid services or live API access is required.

## Commands

From the repository root:

```sh
python3 -m unittest discover -s tests -v
```

For a collector-only change, use this focused local check, then require both full hosted matrix checks before merge:

```sh
python3 -m unittest discover -s tests -p 'test_collector*.py' -v
python3 -m unittest discover -s tests -p test_skills.py -v
```

Do not remove assertions, extend timeouts without a demonstrated cause, or rerun an unchanged failure. Inspect its exact head SHA and logs, fix the cause, and rerun the affected checks. On a heavily loaded shared host, follow the coordinator's validation slot schedule; focused checks and hosted full suites remain available. A hosted pass is not a claim that a final combined local suite ran.

## Triggers and cancellation

PR creation and updates run the matrix. Push runs are limited to `main`, so feature branch pushes do not duplicate PR runs. Keep the main push run: it validates the merged commit and can expose integration errors missed by a PR check.

A concurrency group includes workflow, event and PR number (falling back to commit SHA on main pushes). A newer PR revision cancels the superseded run for that PR. Different PRs and different main commits cannot cancel each other. A cancelled superseded run is not evidence of passing tests; the current head must pass both checks. See [GitHub's concurrency documentation](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/control-workflow-concurrency).

There are no path exclusions: changes to skills, reference instructions and reports can affect skill lint or CLI contracts. Neither checks nor failure notifications are disabled. The workflow token needs only `contents: read`.

## Evidence and limits

On 17 November 2026, the audit found all 26 recorded PR workflow runs successful, including campaign PRs #23–27. The first four campaign merge push runs also passed. No campaign failure needed a runtime or test repair. The concurrency change prevents obsolete work; it does not conceal an observed failure. Later run state is recorded in the owning campaign thread rather than frozen here.

Collector and link-probe tests use offline adapters and mocks. They check parsing, retry and error behavior; they do not prove public endpoint availability, source truth, installed-app behavior or a production deployment. Test temporary files are isolated with `TemporaryDirectory`; no known shared-file or live-network test failure was found in this audit. No deployment workflow exists in this repository.
