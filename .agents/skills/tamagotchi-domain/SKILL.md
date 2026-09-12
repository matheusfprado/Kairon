---
name: tamagotchi-domain
description: Use for Tamagotchi companion state, needs, mood, XP, levels, reactions, decay, interactions, persistence, and domain rules. Keep game logic deterministic and independent from UI.
---

# Tamagotchi Domain

The Tamagotchi is the living visual companion for Jarvis.

## Core state
Prefer a typed domain model for:
- mood
- energy
- hunger
- affection
- xp
- level
- current reaction/state
- timestamps needed for decay or persistence

Use 0..100 for bounded needs unless an existing model says otherwise.

## Architecture
Keep domain rules separate from UI:

Input/Event
-> Tamagotchi domain/engine
-> New state
-> Character reaction
-> UI rendering

## Rules
- Domain functions should be deterministic when possible.
- Clamp bounded values.
- Centralize XP/level rules.
- Avoid timers directly inside pure domain logic.
- Treat persistence as an adapter, not part of the core rules.
- UI components display/dispatch; they should not own game formulas.
- Add focused tests for state transitions and edge cases.

## Examples of events
feed, play, talk, sleep, wake, commandCompleted, commandFailed, idleTick.

Do not implement unrelated Jarvis integrations when working only on companion behavior.
