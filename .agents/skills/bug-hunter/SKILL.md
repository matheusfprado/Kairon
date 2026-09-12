---
name: bug-hunter
description: Use when fixing a bug, runtime error, failed test, type error, or regression in Jarvis. Diagnose from concrete evidence and make the smallest verified fix.
---

# Bug Hunter

## Debug loop
1. Start from the exact error, failing behavior, stack trace, or reproduction.
2. Locate the first relevant source location.
3. Inspect direct callers/dependencies only as needed.
4. Form one likely cause.
5. Make the smallest reasonable fix.
6. Re-run the narrowest reproduction/test.
7. Expand scope only if the evidence disproves the hypothesis.

## Do not
- Refactor while debugging unless required by the fix.
- Search the whole repository before checking the direct failure path.
- Change multiple unrelated hypotheses at once.
- Silence errors with unsafe casts, ignored promises, disabled lint rules, or removed tests.

## Finish
Report root cause in one sentence, changed files, and validation.
