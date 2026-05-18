---
description: Plan a new feature — conceptual design, scope, and proposal
argument-hint: <brief description of the feature>
---

# Plan feature: $1

**Goal**: produce a design document approved by the user.
**Behaviour**: you only plan and ask questions. No code, no tasks, no files beyond the plan document itself.

---

## Phase 1 — Understand the goal

1. Read `CLAUDE.md` (if present) and `MEMORY.md` for project context.
2. Read `docs/` for existing documentation (`configuration.md`, `sqlite-schema.md`, `supported-formats.md`, `DOCKER.md`, etc.).
3. If previous plans exist in `docs/plans/`, read them to understand decisions already made.
4. Ask the user everything needed with `AskUserQuestion`:
   - What problem does this feature solve?
   - What layers does it affect? (`domain`, `application`, `infrastructure`, `controllers`, frontend, infra/Docker, tests)
   - Are there open design decisions?
   - Are there constraints or preferences? (e.g.: "no schema migration", "infrastructure only", "must run on arm64 Synology")

**Never assume. If anything is unclear, ask with `AskUserQuestion` before continuing. Five questions now beats a full rewrite later.**

**Do not advance to Phase 2 until you have clear answers.**

---

## Phase 2 — Explore the affected code

1. Use `Explore` agents to understand the current state of the code in affected areas.
2. Identify:
   - Files that will be modified or created.
   - Existing patterns that must be followed (consult `backend-patterns`, `frontend-patterns` skills when present; always honour the hexagonal split in `dev-workflow` skill: `domain` imports nothing, `application` imports only `domain`, `infrastructure` and `controllers` are the only places that touch third-party libraries).
   - Dependencies between components.
   - Known risks or pitfalls (consult `MEMORY.md`).
3. Present the user with a summary of findings and validate your understanding.

---

## Phase 3 — Write the proposal

Create the plan document at `docs/plans/<feature-name>.md` with this structure:

```markdown
# Feature name

## Context

What problem it solves. Why it is needed now.

## Decisions confirmed with user

| Topic | Decision |
|-------|----------|
| ... | ... |

## Design proposal

Conceptual design (not code). Components involved, data flow,
architecture decisions. Respect the hexagonal direction of imports.

## Scope

### What is included
- ...

### What is NOT included
- ...

## Affected layers

| Layer | Impact |
|-------|--------|
| Domain (`src/domain/`) | ... |
| Application (`src/application/`) | ... |
| Infrastructure (`src/infrastructure/`) | ... |
| Controllers (`src/controllers/`) | ... |
| Frontend | ... |
| Infrastructure (Docker / compose / CI) | ... |
| Database (SQLite schema) | ... |
| Tests (`tests/`) | ... |

## Implementation order

Numbered list of high-level steps. Domain → application → infrastructure → controllers → tests is the typical order for this project.

## Critical files

| File | Changes |
|------|---------|
| ... | ... |

## Risks and considerations

- Hardware-acceleration regressions on arm64 / amd64 (see `dev-workflow` matrix).
- Schema migration impact on existing SQLite databases.
- ...

## Open design decisions

(If there are decisions yet to be made, list them here. They must be closed before creating tasks.)
```

Present the document to the user and ask for feedback.

---

## Phase 4 — Iterate until approval

- If the user has feedback, adjust the document.
- If there are open decisions, close them with `AskUserQuestion`.
- Once approved, tell the user: **"Plan saved. Next step: `/dev-2-tasks docs/plans/<feature-name>.md`"**

---

## Unbreakable rules

- **Do not implement anything**: no code, no tasks, no files beyond the plan document.
- **Ask before assuming**: if in doubt, use `AskUserQuestion`. Always.
- **Read the actual code** before proposing changes to existing areas.
- **The document must be self-contained**: someone reading it without prior context must understand the proposal.
- **All exploration and verification commands via Docker** (`dev-workflow` skill).
- **Documentation language: English.**
