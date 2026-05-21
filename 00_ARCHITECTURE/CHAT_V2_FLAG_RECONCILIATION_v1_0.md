---
artifact: CHAT_V2_FLAG_RECONCILIATION_v1_0
canonical_id: CHAT_V2_FLAG_RECONCILIATION
version: 1.0
status: CURRENT
authored: 2026-05-16
author: Claude (chat-v2 α6 session)
---

# Chat V2 — Feature Flag Reconciliation (α6)

## Problem

Two flags had divergent defaults between `feature_flags.ts` (dev fallback) and
`deploy.yml` (production override):

| Flag | feature_flags.ts default | deploy.yml | Prod runtime |
|---|---|---|---|
| `ADAPTERS_ENABLED` | `false` | `true` | `true` |
| `CONSUME_UI_V2_ENABLED` | `false` | `true` | `true` |

Local dev without a `.env.local` ran with both flags `false`, masking behavior
present in production. This caused silent divergence between local and prod
behavior for the adapter layer and consume-UI v2 paths.

## Fix (α6)

1. **`feature_flags.ts`** defaults flipped to `true` for both flags, matching prod.
2. **`MARSYS_FLAG_CHAT_V2_ENABLED`** added as a new flag with default `false`
   across all three surfaces (feature_flags.ts, deploy.yml, .env.local.example).

## New flag: MARSYS_FLAG_CHAT_V2_ENABLED

- **Purpose**: Gates the assistant-ui Chat V2 shell vs. legacy ConsumeChat.
- **Default**: `false` (legacy path until phase α exit gate).
- **Flip condition**: After phase α exit gate criteria are met (α7 wires the switch;
  β+γ phases add features behind the flag; flip to `true` at pre-merge PM1).
- **Surfaces**: `feature_flags.ts` · `deploy.yml env_vars` · `.env.local.example`

## Rationale

Keeping the new flag `false` in production means the Chat V2 shell is dark-launched:
new route infrastructure (data parts, UIMessage end-to-end, retry policy) is wired
in but the UI switch is off. This allows β-phase integration without user impact.
