---
canonical_id: R11C_C_S0
session_id: C-S0
title: Streaming capability check via adapter (R11.CDE entry-point)
phase: R11.C (within R11.CDE composite)
depends_on: []
flag: FLAGLESS
client_side: "no — verification + capability matrix read"
authored: 2026-05-22
---

# C-S0 — Streaming Capability Check

## Context

First session of stream-2 (R11.CDE). Verify R11.A foundation is healthy and the adapter manifests correctly report each provider's streaming capabilities (smoothStreaming: true, extendedThinking variants, etc.).

## Files in Scope

- `platform/tests/providers/streaming-capability-check.test.ts` (new) — reads each of the 5 manifests and asserts the streaming-relevant fields match CAPABILITY_MATRIX expectations.

## Files MUST NOT Touch

- Stream-1 (R11.B) UI files
- Phase 4C files

## Acceptance Criteria

1. All 5 manifests report streaming capabilities correctly.
2. Test passes against the post-R11.A merged state.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
npx jest --testPathPattern="streaming-capability-check|C-S0" --passWithNoTests
```

## Commit Template

```
test(chat-v2): R11.CDE streaming capability check (C-S0)
```

## Decision Log

*(Executor: paste 5-provider manifest streaming-field readout.)*
