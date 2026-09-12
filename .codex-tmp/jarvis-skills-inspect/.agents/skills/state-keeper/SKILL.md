---
name: state-keeper
description: Use after a meaningful completed feature or architecture decision to keep PROJECT_STATE.md useful for future low-context Codex sessions. Do not update it for trivial edits or debugging noise.
---

# State Keeper

Keep `PROJECT_STATE.md` short and continuation-focused.

Update only when one of these changes:
- current phase or next milestone
- implemented project capability
- architecture or important technical decision
- important dependency/integration choice
- known blocker that another session must know

## Do not record
- commit-by-commit history
- trivial styling changes
- temporary debugging attempts
- verbose implementation details
- information easily discovered from one obvious source file

## Size
Prefer under about 150 lines.

Replace stale information instead of endlessly appending.

The goal is to let a fresh Codex session understand the current project without scanning the repository.
