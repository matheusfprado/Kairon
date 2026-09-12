---
name: targeted-tests
description: Use after code changes to choose the smallest meaningful validation for the affected Jarvis area. Prefer targeted typecheck, unit, integration, lint, or package tests over the entire repository suite.
---

# Targeted Tests

Choose validation based on the change.

## Selection
- Pure domain logic -> affected unit test(s).
- Component -> component test plus targeted typecheck/lint if available.
- API route/service -> affected service/route tests.
- Integration adapter -> adapter tests/mocks and relevant typecheck.
- Shared package contract -> package tests plus direct dependents if needed.
- Build/config/shared infrastructure -> broader validation may be justified.

## Rules
- Inspect package scripts only when needed to discover the correct command.
- Do not run every test by default.
- Do not repeatedly run unchanged validations.
- If no targeted test exists, run the narrowest typecheck/build that provides confidence.

Report the exact checks run and whether they passed.
