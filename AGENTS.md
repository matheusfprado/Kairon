# JARVIS — CODING AGENT RULES

## Goal

Build a local personal assistant called Jarvis with a Tamagotchi-style
virtual companion.

Jarvis should eventually support:

- text interaction
- voice interaction
- Tamagotchi character/state
- desktop commands
- integrations
- local automations

Keep the architecture modular so features can be added gradually.

---

# TOKEN EFFICIENCY — HIGH PRIORITY

Minimize token and context usage.

## Before coding

1. Identify the smallest scope required for the task.
2. Inspect only files directly related to that scope.
3. Prefer targeted file searches over repository-wide exploration.
4. Do not read unrelated directories.
5. Do not repeatedly read files already inspected during the current task.

Do not scan the entire repository unless explicitly necessary.

---

# CONTEXT RULES

Always prefer:

small context
→ targeted inspection
→ small change
→ targeted validation

Avoid:

large context
→ repository-wide exploration
→ unnecessary refactors
→ long explanations

Read `PROJECT_STATE.md` first when project context is required.

Do NOT reconstruct project history by scanning the repository if
`PROJECT_STATE.md` already contains the information.

---

# FILE READING RULES

Ignore unless directly required:

- node_modules
- .next
- dist
- build
- coverage
- generated files
- lockfiles
- logs
- temporary files
- binary files

Do not open package-lock.json, pnpm-lock.yaml or yarn.lock unless dependency
resolution requires it.

Do not read large files completely when a targeted search is sufficient.

---

# CODING RULES

Change only files required for the current task.

Do not:

- perform unrelated refactors
- rename unrelated files
- reorganize the project without request
- install packages unnecessarily
- rewrite working components without reason
- create duplicate utilities
- create abstractions before they are needed

Prefer existing project patterns.

Reuse existing:

- components
- hooks
- services
- types
- helpers
- utilities

Keep implementations simple.

---

# TASK SCOPE

For each request internally determine:

TARGET:
What needs to change?

FILES:
Which files are probably involved?

VALIDATION:
What is the smallest validation required?

Then proceed.

Do not output this planning unless useful.

---

# TESTING

Use targeted validation.

For a component change:

- test the component or affected package

For a TypeScript change:

- run targeted type checking when possible

For a backend change:

- test the affected route/service

Do NOT run the entire test suite for every small modification.

Run full tests only when:

- requested
- changing shared infrastructure
- modifying critical architecture
- preparing a release
- targeted validation is insufficient

---

# OUTPUT

Keep responses concise.

After completing a task report only:

### Done

- what changed

### Files

- files changed

### Validation

- tests/checks executed

### Note

- only if something important remains

Do not explain basic programming concepts unless asked.

Do not reproduce entire files in chat unless requested.

---

# ERROR HANDLING

When an error occurs:

1. Inspect the exact error.
2. Locate the relevant code.
3. Make the smallest reasonable fix.
4. Validate again.

Do not start exploring unrelated parts of the repository.

Maximum debugging expansion:

Error
→ direct dependency
→ related module
→ broader architecture only if necessary

---

# DEPENDENCIES

Before installing a dependency:

1. Check if the project already has a solution.
2. Prefer platform/native APIs when appropriate.
3. Install only if it materially simplifies the implementation.

Never install a package only for a trivial helper.

---

# ARCHITECTURE

The project should remain modular.

Expected domains:

apps/
desktop/
api/

packages/
assistant/
tamagotchi/
voice/
integrations/
shared/

Responsibilities must remain separated.

---

# TAMAGOTCHI DOMAIN

The Tamagotchi system should eventually manage:

- mood
- energy
- hunger
- affection
- sleep
- experience
- level
- interactions
- animations
- personality state

Business logic should not depend directly on UI components.

Prefer a domain/state layer.

Example:

TamagotchiEngine
↓
TamagotchiState
↓
UI

---

# ASSISTANT DOMAIN

Jarvis should separate:

User Input
↓
Intent / Command
↓
Assistant Core
↓
Action / Integration
↓
Response

Do not tightly couple integrations with UI.

Examples of integrations may include:

- Spotify
- desktop actions
- smart devices
- APIs

Each integration should have its own adapter/service.

---

# SECURITY

Desktop/system actions must be explicit and controlled.

Avoid:

- arbitrary shell execution from untrusted input
- exposing secrets
- committing .env files
- logging tokens or credentials

Sensitive integrations must use environment variables.

---

# PROJECT STATE

After a meaningful feature, architecture change or important decision,
update `PROJECT_STATE.md`.

Keep PROJECT_STATE.md concise.

Do not turn it into a development diary.

Only store information another coding session needs to continue working.

Maximum recommended size:
approximately 150 lines.

---

# PRIMARY PRINCIPLE

Do the smallest amount of work and context exploration necessary
to correctly complete the requested task.
