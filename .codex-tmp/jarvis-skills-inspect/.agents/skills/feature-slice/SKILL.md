---
name: feature-slice
description: Use when implementing a new Jarvis or Tamagotchi feature. Build the smallest vertical slice first, preserve existing architecture, and avoid speculative abstractions or unrelated refactors.
---

# Feature Slice

Implement one usable feature slice at a time.

## Steps
1. Identify the user-visible behavior and acceptance condition.
2. Locate the existing domain, service, UI, and test patterns that directly apply.
3. Reuse existing types, components, hooks, services, and utilities.
4. Implement the minimum complete slice.
5. Add or update only directly relevant tests.
6. Validate the affected package/app.
7. Update `PROJECT_STATE.md` only when the feature changes project capabilities, architecture, or an important decision.

## Rules
- Do not create abstractions for hypothetical future features.
- Do not install dependencies if the project already has a suitable solution.
- Do not redesign unrelated UI.
- Do not rename/move unrelated files.
- Keep domain logic out of presentation components when practical.
