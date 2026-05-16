---
description: Structured audit of a code area — find inconsistencies, propose fixes, apply with approval
argument-hint: <area to audit, e.g.: "FFmpeg argv building", "SQL repository", "video metadata parser">
---

# Audit: $1

**Goal**: systematically review a code area, surface inconsistencies against project conventions, and apply approved fixes in a single clean pass.
**Behaviour**: you explore and propose before touching anything. No changes until the user approves the full list.

---

## Step 1 — Load context

1. Read `CLAUDE.md` (if present) and `MEMORY.md`.
2. Read the relevant skills for the area being audited:
   - Hexagonal split, Docker workflow, hardware matrix → `dev-workflow`
   - Domain / application / infrastructure / controllers patterns → `backend-patterns` (when present)
   - UI / frontend → `frontend-patterns` (when present)
   - Tests → `test-discipline`
   - Commits / branches → `git-conventions`
3. Identify the canonical conventions that apply to `$1`.

---

## Step 2 — Explore the area

Use `Explore` agents to read all files in the target area.
Do not read the entire codebase — scope to what `$1` describes.

---

## Step 3 — Build the findings list

Compare what you found against the conventions from Step 1.
Produce a numbered findings table:

| # | File | Issue | Convention violated | Proposed fix |
|---|------|-------|--------------------|-----------|
| 1 | `src/infrastructure/transcoder/ffmpeg_args.py` | Calls third-party lib from domain | Hexagonal: domain imports nothing | Move helper to infrastructure layer |
| 2 | ... | ... | ... | ... |

Group findings by severity:
- **Must fix**: contradicts an explicit convention (hexagonal direction, `git-conventions`, `test-discipline`).
- **Should fix**: inconsistent with the rest of the codebase.
- **Minor**: style preference, low impact.

Present the table to the user and ask:
- Is anything missing from the list?
- Is anything out of scope?
- Are there findings you want to skip?

**Do not apply any changes until the user approves.**

---

## Step 4 — Apply approved fixes

Once the user approves (all or a subset):

1. Apply each fix in order.
2. For each fix: read the file, apply the change, re-read to confirm correctness.
3. Do not introduce changes beyond the approved list.

---

## Step 5 — Verify

Run the relevant test suite for the area touched. Backend is the default for this repo:

```bash
docker compose -f dev/docker-compose.test.yml run --rm video-enhancer-test \
  python -m pytest tests/ -v
docker compose -f dev/docker-compose.test.yml run --rm video-enhancer-test \
  ruff check src/ tests/
```

Frontend (when present):
```bash
docker compose -f dev/docker-compose.test.yml run --rm frontend-test npx vitest run
docker compose -f dev/docker-compose.test.yml run --rm frontend-test npm run build
```

If tests fail: diagnose and fix before handing off (apply `test-discipline`).

---

## Step 6 — Hand off

Tell the user: **"Audit complete — N fixes applied. Ready for `/push`."**
If any approved skill or convention changed during the audit, flag it: "Consider updating the `<skill>` skill to reflect finding #N."

---

## Unbreakable rules

- **Propose before applying**: no changes without user approval of the findings list.
- **Scope discipline**: only touch what `$1` describes. If you find issues outside scope, note them but do not fix them.
- **Read before writing**: never modify a file you haven't read in this session.
- **Do NOT commit**: that is `/push`'s responsibility.
- **Documentation language: English.**
