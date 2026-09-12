---
name: token-guardian
description: Use for Codex coding tasks in this repository when context or token efficiency matters. Minimize file reads, searches, edits, test scope, and response verbosity without sacrificing correctness.
---

# Token Guardian

Optimize for the smallest correct execution.

## Workflow
1. Read `PROJECT_STATE.md` only if project context is needed.
2. Identify the smallest task scope.
3. Search for exact symbols, filenames, imports, routes, or errors before opening broad files.
4. Read only the relevant sections/files.
5. Reuse already inspected context; do not reopen unchanged files unnecessarily.
6. Change only files required by the task.
7. Run the narrowest useful validation.
8. Stop when the requested task is complete.

## Avoid
- Repository-wide exploration unless necessary.
- Reading lockfiles, generated output, `node_modules`, `.next`, `dist`, `build`, coverage, logs, or binaries unless directly relevant.
- Unrelated refactors.
- Full test suites for isolated changes.
- Long explanations or reproducing full files in the final response.

## Escalation
Expand context only in this order:
exact target -> direct dependency -> related module -> shared architecture -> repository-wide search.

## Final response
Keep it short:
- Done
- Files changed
- Validation
- Important note, only if needed
