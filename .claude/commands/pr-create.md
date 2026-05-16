---
description: Analyze branch changes and create a GitHub PR with a structured, relevance-ordered body
argument-hint: <base-branch (optional, default: master)>
---

# Create PR

**Goal**: understand what changed in this branch, then open a GitHub PR with a well-structured body.
**Base branch**: use `$1` if provided, otherwise `master`.

---

## Step 1 — Understand the branch

Run these commands to gather full context:

```bash
git branch --show-current
git log master..HEAD --oneline
git diff master...HEAD --stat
git diff master...HEAD
```

Read any task file referenced by the commits (`docs/tasks/*.md`) if it exists — it contains objective, design decisions, and test results from QA.

---

## Step 2 — Analyse the changes

From the diff and commit log, extract:

1. **What changed** — group by area (`domain` model, `application` use case, `infrastructure` adapter, `controllers` entrypoint, frontend, infra/Docker, CI, docs).
2. **Impact on the project** — rank each change by how much it affects live functionality:
   - High: changes to data models, transcoding pipeline, hardware-acceleration logic, FFmpeg argv, SQLite schema, public ports/interfaces.
   - Medium: new behaviour in adapters, new endpoints (when added), config or env changes that affect runtime, Docker base images / multi-arch.
   - Low: refactors with no behaviour change, test additions, style fixes, documentation.
3. **Resolved issues** — check commit messages and task files for "closes #N", "fixes #N", or any explicit issue references.
4. **Critical design decisions** — anything non-obvious that was deliberately chosen over an alternative (e.g. "chose V4L2M2M over QSV on arm64 because…", "stored error_message as TEXT instead of structured JSON because…").
5. **Test evidence** — what tests were actually run (from QA task or local verification), and what a reviewer should run to validate.

---

## Step 3 — Write the PR body

Use this exact structure. Omit sections that don't apply (Issues, Notes).

```
## Summary

- <change — most impactful first>
- <change>
- <change — least impactful last>

## Issues

Closes #<n>

## Notes

> **Note**: <critical design decision and brief rationale>

## Test plan

- [x] <test that was already executed>
- [ ] <test a reviewer must run to validate>
```

### Rules for each section

**Summary**
- Bullet points ordered from highest to lowest functional impact.
- Each bullet describes *what* changed and *why*, not just the file name.
- Be concrete: "Add `error_message` propagation in `LocalFilesystem.read_file` so callers get the real error instead of a silent `None`" — not "filesystem changes".
- Maximum ~6 bullets; group minor items if needed.

**Issues** _(omit if no issue was resolved)_
- One `Closes #n` line per resolved issue.
- Only include if the change directly resolves a tracked issue.

**Notes** _(omit if no critical design decision was made)_
- One blockquote per decision.
- Format: `> **Note**: <decision>. <rationale in one sentence>.`
- Only include genuinely non-obvious choices; skip self-evident ones.

**Test plan**
- `[x]` for tests already confirmed passing (local or CI).
- `[ ]` for tests a reviewer must run before merging.
- Be specific: name the test path, the curl call, the docker buildx command.
- Always include at minimum: backend tests (dockerized), lint, and one manual smoke-test step (e.g. `docker compose -f dev/docker-compose.dev.yml up` and observe a transcoding cycle).

---

## Step 4 — Create branch and PR

### Branch (if still on master)

Branch naming follows the `git-conventions` skill: `<type>/<kebab-slug>`.

```bash
git checkout -b <type>/<descriptive-slug>
git push -u origin <type>/<descriptive-slug>
```

Examples: `feat/dashboard-endpoint`, `fix/filesystem-read-errors`, `chore/multi-arch-pin`.

### PR title

- Under 70 characters.
- Imperative mood, lowercase type prefix matches commit type: `feat:`, `fix:`, `chore:`, `refactor:`, `perf:`, `docs:`, `test:`, `style:`. Scope is preferred when applicable: `feat(transcoder): ...`.
- English only.

### Create

```bash
gh pr create --title "<title>" --body "$(cat <<'EOF'
<body>
EOF
)"
```

**Never use `gh pr edit`** — it triggers a GraphQL deprecation warning. To amend the body after creation:
```bash
gh api repos/<owner>/<repo>/pulls/<n> --method PATCH --field body="<body>"
```

---

## Unbreakable rules

- **English only** — title, body, bullet points, notes, everything.
- **No authorship attribution** — do not mention any tool, assistant, or generator anywhere in the PR. The `git-conventions` skill in this repo also prohibits `Co-Authored-By` footers in commits; the same spirit applies to PR bodies.
- **Relevance order** — Summary bullets must go from most to least impactful; never alphabetical or file-order.
- **Evidence-based test plan** — only mark `[x]` if you have confirmed the test passed; never pre-check unrun tests.
- **Omit empty sections** — if there are no resolved issues, drop the Issues section entirely. Same for Notes.
