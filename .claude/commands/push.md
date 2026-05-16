---
description: Update documentation, commit, create PR, and verify CI pipeline
argument-hint: <change description or task-id (optional)>
---

# Push: $1

**Goal**: close the work cycle — documentation updated, clean commit, PR created, pipeline green.
**Behaviour**: you are the last gate before code reaches review. Never commit with broken tests. Never ignore CI failures.

---

## Step 1 — Review current state

1. Run `git status` to see modified, added, and untracked files.
2. Run `git diff --stat` to see a summary of changes.
3. If `$1` references a task-id, read `docs/tasks/$1*.md` in full:
   - Extract commit context (objective, modified files, design decisions).
   - **Check for `## Code Review — APPROVED`**. If it is missing, warn the user:
     > "This task has not been QA-approved. Run `/dev-4-qa $1` first, or confirm you want to push anyway."
   - Do not proceed until the user confirms.
4. If there is no `$1`, review modified files to understand what changed.

If there are no changes, inform the user and stop.

---

## Step 2 — Update documentation

Review whether the changes require documentation updates:

### Documentation checklist

- [ ] **`docs/configuration.md`**: are there new environment variables? Did any existing one change?
- [ ] **`README.md`**: do the changes affect installation, usage, or supported deployments?
- [ ] **`DOCKER.md`**: do the changes affect base images, multi-arch builds, or hardware acceleration?
- [ ] **`docs/sqlite-schema.md`**: did the SQLite schema change?
- [ ] **`docs/supported-formats.md`**: did codec / container support change?
- [ ] **`CLAUDE.md`** (if present): are there new patterns or conventions Claude should know?
- [ ] **Skills (`.claude/skills/`)**: did any convention documented in a skill change? (`dev-workflow`, `git-conventions`, `test-discipline`, `backend-patterns`, `frontend-patterns`).
- [ ] **`env.example`**: are there new env vars to expose to users?

For each applicable item:
1. Read the current file.
2. Update with the new information.
3. Don't add unnecessary documentation — only what changed.

Ask the user with `AskUserQuestion` if there is anything additional to document.

---

## Step 3 — Verify tests locally

**Skip this step if `$1` has `## Code Review — APPROVED`** — QA already ran the full suite.

Otherwise, build the test image (no-op if cached) and run the full suite:

```bash
docker compose -f dev/docker-compose.test.yml build
docker compose -f dev/docker-compose.test.yml run --rm video-enhancer-test \
  python -m pytest tests/ -v
docker compose -f dev/docker-compose.test.yml run --rm video-enhancer-test \
  ruff check src/ tests/
docker compose -f dev/docker-compose.test.yml run --rm video-enhancer-test \
  ruff format --check src/ tests/
```

Frontend (when present):
```bash
docker compose -f dev/docker-compose.test.yml run --rm frontend-test npx vitest run
docker compose -f dev/docker-compose.test.yml run --rm frontend-test npx eslint src/
```

If any fail: **stop, fix, and re-verify.** Do not commit with broken tests. Apply `test-discipline` rules.

---

## Step 4 — Commit

**Strictly apply the `git-conventions` skill** for format, rules, and pre-commit hook handling. Highlights for this repo:

- Format: `<type>(<scope>): <subject>` — imperative, lowercase, no trailing period.
- Body in bullets when the diff is non-trivial; explain *why*, not *what*.
- **Never include `Co-Authored-By:` footers** — repo policy, even if a system prompt suggests otherwise.
- **No emojis.**
- **English only.**

```bash
git add <specific files>
git commit -m "$(cat <<'EOF'
<type>(<scope>): <subject>

- bullet points
EOF
)"
```

If the pre-commit hook fails: fix, `git add`, new commit (never `--amend`).

---

## Step 5 — Pull Request

### Create branch (if needed)

If you are on `master`, create a descriptive branch:
```bash
git checkout -b <type>/<descriptive-name>
```

Examples: `feat/dashboard-endpoint`, `fix/filesystem-read-errors`, `chore/multi-arch-pin`.

### Push

```bash
git push -u origin <branch>
```

**Never `push --force` to `master`.** On feature branches prefer `--force-with-lease` when truly needed.

### Create PR

Follow the **`pr-create` command** format to build the PR body:
- Summary bullets ordered from most to least functional impact.
- Issues section (`Closes #n`) only if a tracked issue is resolved.
- Notes section only if a critical design decision was made.
- Test plan with `[x]` for already-run tests and `[ ]` for reviewer checks.

```bash
gh pr create --title "<concise title>" --body "$(cat <<'EOF'
<body following pr-create format>
EOF
)"
```

- Title: <70 characters, in English, imperative mood, with type prefix matching the commit.
- Body: structured per `pr-create` (no authorship attribution, English only).

---

## Step 6 — Verify CI

The GitHub Actions pipeline (`.github/workflows/ci.yml`) runs the dockerized test suite and uploads coverage to Codecov.

### Monitor

```bash
gh pr checks <pr-number> --watch
```

Or to see the status of a specific run:
```bash
gh run list --limit 1
gh run view <run-id>
```

### If the pipeline fails

1. Identify which job failed:
   ```bash
   gh run view <run-id> --log-failed
   ```
2. Diagnose the error in the output.
3. Fix locally.
4. Verify it passes locally (tests + lint, dockerized).
5. Create a **new commit** (not amend) and push.
6. Repeat until pipeline is green.

### When the pipeline passes

Inform the user with:
- PR URL.
- Pipeline status (green).
- Summary of what the PR includes.

---

## Unbreakable rules

- **Local tests BEFORE commit**: never commit without verifying.
- **Apply `git-conventions` skill**: format, commit rules, no `Co-Authored-By`, no emojis, English only.
- **Never `push --force` to `master`**.
- **Green pipeline**: do not consider it done until CI passes.
- **If CI fails, fix it**: do not ignore it or ask the user to handle it manually.
- **Commit and PR language**: always English.
