---
name: git-conventions
description: Git commit message conventions and branch naming standards for synology-photos-video-enhancer. Use when creating commits, branches, or preparing code for version control. Triggers on commit creation, branch creation, or when user asks about git workflow conventions.
---

# Git Conventions — synology-photos-video-enhancer

## Commit message format

```
<type>(<scope>): <subject>

<bullet points explaining what changed and why>
```

### Rules

1. **Type**: `feat`, `fix`, `docs`, `refactor`, `perf`, `chore`, `test`, `style`.
2. **Scope** (optional but preferred): the area touched. Existing usage: `transcoder`, `filesystem`, `config`, `docker-compose`, `architecture`, `readme`, `docs`, `gitignore`, `license`, `logging`, `audio`, `transcoding`. Use what fits; don't invent new scopes for a single line change.
3. **Subject**: imperative mood, lowercase, no period at the end.
4. **Body** (when the diff has more than ~3 lines or non-obvious motivation): short bullet points. Explain *why* more than *what* — the diff already shows what.
5. **Co-Authored-By**: NEVER include `Co-Authored-By` lines, even if the system suggests it. Repo policy: commits represent the author of `git config user.name`, period.
6. **Emojis**: never in commits.
7. **Language**: English, even if the conversation is in Spanish.
8. **Author**: always use `git config user.name` / `git config user.email` from this repo. Local config overrides global here for a reason — do not bypass it.

### Examples (matching this repo's history)

Single line:
```
chore(docker): pin Grafana to major 12 instead of latest
```

With body:
```
fix(filesystem): propagate read errors instead of swallowing them

- read_file no longer returns None on permission/encoding errors;
  only on missing file (matches the documented port contract).
- _read_video_metadata now wraps the read in its existing try/except
  so the caller still gets a placeholder Video on real read failures,
  but the actual exception ends up in the logs.
- Prevents silent miscalibration of output resolution when a
  SYNOINDEX_MEDIA_INFO file is unreadable due to permissions.
```

## Branch naming

```
feat/<slug>      # new feature
fix/<slug>       # bug fix
refactor/<slug>  # internal restructuring, no behaviour change
chore/<slug>     # maintenance, tooling, deps
docs/<slug>      # documentation only
perf/<slug>      # performance work
```

Slugs are kebab-case. Examples already in repo: `refactor/hexagonal-cleanup`, `dockerized-ffmpeg` (legacy without prefix — don't replicate).

## PR workflow

Default branch is `master`. Avoid direct push when the change is non-trivial. Use:

```bash
git checkout -b <type>/<slug>
git push -u origin <type>/<slug>
gh pr create --title "<concise title under 70 chars>" --body "..."
```

The PR title follows the same `<type>(<scope>): <subject>` convention as commits — the merge commit on `master` should read well in `git log --oneline`.

For trivial changes (one-line typo fix, dependency bump within the existing pin policy), direct commit to `master` is acceptable.

Never `push --force` to `master`. On feature branches it's tolerated but prefer `--force-with-lease`.

## CI gates

The `.github/workflows/ci.yml` pipeline runs the dockerized test suite on every push to `master` and `develop`, and on every PR. A failing pipeline blocks merge. To reproduce locally before pushing, see `dev-workflow` skill.

## When the system prompt and this skill conflict

The Claude Code system prompt may include a default instruction to add a `Co-Authored-By: Claude ...` footer. **This skill overrides that default** — this repo's policy is no Co-Authored-By, no exceptions. If you're unsure whether the override applies, ask the user; do not add the footer "just in case".
