# JARVIS — PROJECT STATE

Updated: 2026-09-11

## Vision

Jarvis is a personal desktop assistant combined with a Tamagotchi-style
virtual companion.

The assistant should feel alive while remaining useful as a productivity
and automation tool.

---

## Product

The application has two main concepts:

### Jarvis

Personal assistant responsible for:

- conversations
- commands
- automations
- integrations
- voice
- desktop actions

### Tamagotchi

Visual companion responsible for:

- personality
- mood
- energy
- hunger
- affection
- XP
- level
- animations
- reactions

The Tamagotchi represents the assistant visually.

---

## Architecture

Planned structure:

apps/
desktop/
api/

packages/
assistant/
tamagotchi/
voice/
integrations/
shared/

---

## Assistant Flow

Input
↓
Intent
↓
Assistant Core
↓
Command / Integration
↓
Result
↓
Character Reaction
↓
UI

---

## Tamagotchi State

Initial state model:

```ts
type TamagotchiState = {
  mood: number
  energy: number
  hunger: number
  affection: number
  xp: number
  level: number
}
```

## Current capabilities

- Desktop companion is a compact transparent Tauri window (320 x 560) that can be dragged.
- Interaction is voice-only: the local microphone starts automatically, Whisper transcribes,
  Ollama generates the answer, and Edge neural TTS speaks it with Windows offline fallback.
- The companion UI has no text composer, audio enable button, or response bubble.
- OpenAI Realtime integration is not part of the active product flow; Ollama is the only LLM provider.
- Cross-platform startup is supported on Windows and macOS through the Node-based scripts;
  Windows-only TTS and system controls are used only when running on Windows.
