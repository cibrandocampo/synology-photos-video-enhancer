---
name: test-discipline
description: Testing discipline for synology-photos-video-enhancer — write strict tests, fail hard when they reveal bugs, diagnose and fix the root cause (code, infra, or test), then re-run until green. Use whenever writing or running pytest tests, debugging a failing test, or tempted to reach for `pytest.skip` / weakened assertions / `mock.ANY` / "known pre-existing failure" labels.
---

# Test Discipline — synology-photos-video-enhancer

The test suite is dockerized (`dev/docker-compose.test.yml`), runs in CI on every push and PR, and gates merges. A test that is softened to pass while the code is broken is worse than no test at all — it actively lies. This skill captures the rules to keep the suite trustworthy.

## Core principles

1. **One test = one concept.** Multiple `assert` calls are fine if they validate the same concept ("saving a transcoding persists status AND error_message" — two facets of one save). If you need "and" to name the test, split it.
2. **Fail hard, never softly.** If a test reveals a bug in the app (not in the test), the test must fail until the bug is fixed. Do **not** comment the assertion, loosen it, skip the test, or label the failure "known / pre-existing" to move on.
3. **Diagnose before changing anything.** Reproduce the failure in isolation (`pytest tests/path/test_x.py::TestY::test_z`) before touching code. The smaller the reproducer, the cleaner the fix.
4. **Fix at the right layer.** A test failure can originate in:
   - **The test itself** — bad mock setup, stale fixture, wrong assumption about behaviour.
   - **The app code** — real regression or feature gap.
   - **The infrastructure** — Docker image stale, bind-mount permissions, env vars missing, base image change.
   Identify the layer first, then fix there. Do not paper over an app bug with a test tweak.
5. **Re-run until green.** One pass of the failing test alone is not enough — also run the full suite (`make test` or the docker compose command) to catch unintended regressions before declaring done.

## Required workflow when a test fails

1. **Read the failure.** Stack trace, captured stdout/stderr from `--tb=short`, and the assert diff. Don't guess from the test name.
2. **Reproduce in isolation.** `docker compose -f dev/docker-compose.test.yml run --rm video-enhancer-test python -m pytest tests/path/test_x.py::TestY::test_z -v`. If it passes alone but fails in the full run, suspect order dependency or shared state (DB, filesystem, monkeypatch leaking).
3. **Classify the layer.** Test drift / app bug / infra mismatch (see core principle 4).
4. **Apply the minimal fix.** Touch only what the diagnosis pointed to. Do not bundle unrelated cleanups in the same commit.
5. **Re-run the failing test isolated.** Expect green.
6. **Run the full suite.** No regression, no new warning the run wasn't producing before.

## Forbidden patterns

- `pytest.skip(...)` without an open issue / TODO referencing why.
- `assert result is not None` where `assert result == specific_value` would work — vague asserts hide regressions.
- `mock.ANY` for arguments you actually care about — only use it when the value is genuinely irrelevant to the behaviour under test.
- Increasing implicit timeouts (e.g., `time.sleep` in a test) to "make it pass" when a real race exists.
- Catching and ignoring exceptions inside a test to avoid the failure.
- Editing the assertion until it matches current (wrong) behaviour without understanding why current behaviour is wrong.
- Labelling a failure "pre-existing / not our code" to move on. There is no such thing — the suite is your responsibility end to end.
- Merging with any test skipped or failing. Zero exceptions.

## When the test reveals an infra issue

Common shapes in this repo:

- **Stale Docker image**: tests pass locally but you changed `requirements.txt` or `Dockerfile` and didn't rebuild. Solution: `docker compose -f dev/docker-compose.test.yml build` (or `make test` which does both).
- **Bind-mount permission mismatch**: tests that read `tests/media/` or `tests/data/` fail with `PermissionError` only inside Docker. Solution: check the mount in `dev/docker-compose.test.yml` — those should be `:ro`. If they're not, the test container may have polluted the host directory.
- **Missing env var**: the test container has minimal env vars set explicitly in `dev/docker-compose.test.yml`. If a new test needs a new env var, add it there explicitly — don't rely on the host having it.
- **Pytest collecting test files outside `tests/`**: `pytest.ini` pins `testpaths = tests`. If you add tests elsewhere, they won't run in CI.

If a failure is infra, fix it once at the source (compose file, Dockerfile, pytest.ini) — don't work around it inside the test.

## When the test reveals a real app bug

1. Stop the task — the test cannot pass.
2. Surface the bug to the user: short summary, blast radius, proposed fix.
3. Ask whether the fix belongs in this task or a separate one.
4. If approved here: apply the fix, keep the test that found it.
5. If separate: write up the bug, leave the failing test in place, do not comment it out.

## Anti-pattern checklist before declaring done

- [ ] Every test is atomic (one concept).
- [ ] Every failure I saw was diagnosed, not patched away.
- [ ] Assertions are specific — not `is not None` when an exact value is known.
- [ ] No `pytest.skip`, no commented assertions, no loosened sleeps.
- [ ] Full suite passes: `make test` (or equivalent docker command) shows zero failures, zero unexpected skips.
- [ ] Coverage didn't drop on lines I touched. `pytest.ini` produces an HTML report — check it if a regression in coverage is suspected.

## Why this matters here

The app runs unattended on a Synology NAS, transcoding user videos in place. A regression that produces malformed output or stalls the queue may not be noticed for days. The CI suite is the only line of defence between a refactor and corrupted user files. Strict discipline now is much cheaper than recovering from a silent failure later.
