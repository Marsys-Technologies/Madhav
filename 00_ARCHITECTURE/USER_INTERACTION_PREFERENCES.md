---
artifact: USER_INTERACTION_PREFERENCES.md
status: LIVING
authored_on: 2026-05-22
authoring_session: Cowork (R11 launch)
purpose: >
  Persistent record of native preferences for how Cowork sessions should
  communicate with the native during execution. Every Cowork session reads
  this file once at session-open in addition to CLAUDE.md.
version: "1.0"
---

# Native Interaction Preferences

## §1 — Command delivery format

**Preferred (default):** Cowork delivers actions as **Claude Code prompts**
that the native pastes into Claude Code running inside Google Antigravity IDE.
The session in Antigravity executes the prompt and reports back.

**Last resort only:** raw terminal commands for the native to run in their own
shell. Use this format only when:
- The action cannot be done from a Claude Code session (e.g., the action
  requires Antigravity itself to be restarted, or it's a one-shot decision the
  native makes manually).
- The native explicitly asks for shell commands.

When in doubt, wrap the work in a Claude Code paste-prompt. Antigravity is
the native's primary execution surface.

### Format conventions for Claude Code prompts

Each paste-prompt should:
- Open with one-sentence context ("You are continuing the R11 setup; the build
  failed at Step 11 due to missing .env files…").
- State which directory the Antigravity chat should be pointed at.
- List explicit halt-on-failure semantics ("STOP if any step fails; tell me
  what happened").
- Be self-contained (no implicit dependencies on conversation history the
  Claude Code session won't have).
- Be wrapped in a fenced code block for easy copy.

## §2 — Logging

This file is appended to when the native states a new preference or modifies
an existing one. Each new section gets a §N header and the date.

---

*End of USER_INTERACTION_PREFERENCES.md.*
*Native preference established 2026-05-22 during R11 launch.*
