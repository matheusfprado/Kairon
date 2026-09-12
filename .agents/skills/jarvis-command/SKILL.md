---
name: jarvis-command
description: Use when adding a Jarvis command, intent, desktop action, website/app opener, Spotify action, smart-device action, or external integration. Keep intent parsing, execution, adapters, permissions, and UI separated.
---

# Jarvis Command

Use this flow:

User input
-> intent/command
-> assistant core
-> command handler
-> integration adapter
-> result
-> optional Tamagotchi reaction

## Implementation
1. Define or reuse a command contract.
2. Keep parsing/routing separate from side effects.
3. Put external APIs and OS-specific behavior behind adapters.
4. Return typed success/error results.
5. Make permission-sensitive actions explicit.
6. Add a focused test for routing/handler behavior when practical.

## Safety
- Never execute arbitrary shell text derived directly from untrusted natural language.
- Do not expose secrets in logs or responses.
- Use environment variables for credentials.
- Prefer allowlisted actions for desktop automation.
- Require confirmation for destructive or high-impact actions unless the product already has an approved permission model.

Do not couple an integration directly to the Tamagotchi UI.
