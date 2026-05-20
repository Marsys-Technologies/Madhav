---
canonical_id: R10_Y_S3
version: 1.0
status: CURRENT
session_id: Y-S3
title: Smooth-stream tuning — word-aware chunking
depends_on: [Y-S2]
blocked_on: []
flag: MARSYS_FLAG_R10_SMOOTH_STREAM_V2
flag_default: true
client_side: "no — server-side streaming adapter only"
authored: 2026-05-20
---

# Y-S3 — Smooth-Stream Tuning

## Context

The current `smooth_stream.ts` adapter buffers and flushes streaming tokens. The existing behavior may flush mid-word (splitting "Vimshottari" as "Vimshot" + "tari" in consecutive flushes), causing visible flicker in the rendered text as the word builds character by character. Word-aware chunking — buffering until a word boundary (space, punctuation) is reached before flushing — eliminates this flicker.

This session: (1) adds a `measure_smooth_stream.ts` benchmarking script to capture baseline flush cadence, (2) documents the baseline, (3) tunes `smooth_stream.ts` to flush at word boundaries.

**Amendment 1:** Server-side flag only. `MARSYS_FLAG_R10_SMOOTH_STREAM_V2` is read in server-side streaming adapter code. No `NEXT_PUBLIC_` prefix. No deploy.yml build-arg required.

**Amendment 3:** FLAGGED — changes streaming cadence; fast rollback desired.

## Files in Scope

- `platform/src/lib/streaming/smooth_stream.ts` — tune flush logic to word-aware boundaries
- `platform/scripts/measure_smooth_stream.ts` (new) — benchmarking/measurement script; records average flush size, flush frequency, word-split rate to stdout; does NOT modify production code
- `platform/src/lib/feature_flags.ts` — add `MARSYS_FLAG_R10_SMOOTH_STREAM_V2` flag (default `true`)
- `platform/tests/` — unit test for word-boundary flush behavior

## Files Must NOT Touch

- Any `'use client'` components
- Phase 4C files
- `.github/workflows/deploy.yml` (server-side flag, no build-arg needed)
- `platform/src/lib/streaming/stream_adapter.ts` (if separate from smooth_stream — executor confirms)

## Acceptance Criteria

1. **Flag is server-side (Amendment 1 confirmation):** `MARSYS_FLAG_R10_SMOOTH_STREAM_V2` appears only in server-side files (route handlers, lib/streaming). Executor confirms: `grep -rn "MARSYS_FLAG_R10_SMOOTH_STREAM_V2" platform/src --include="*.ts*"` — zero results in `'use client'` files.
2. **Baseline documented:** `measure_smooth_stream.ts` script exists and produces readable output. Before shipping, executor runs the script against a sample stream and pastes the baseline metrics in the Decision Log of this brief (or a companion `SMOOTH_STREAM_BASELINE.md`).
3. **Word-aware flush:** With flag=true, `smooth_stream.ts` buffers incoming characters until a word boundary (space, punctuation, newline, end-of-stream) before flushing. Words are NEVER split across flushes.
4. **Max buffer guard:** A maximum buffer size (`MAX_WORD_BUFFER_MS = 80` ms or `MAX_WORD_BUFFER_CHARS = 200` chars) prevents the buffer from holding indefinitely on run-on text. When the buffer limit is hit, flush immediately regardless of word boundary.
5. **Flag guard:** When flag=false, the original flush behavior is preserved exactly (no regression).
6. **Unit test:** Test provides character-by-character input to `smooth_stream.ts` (flag=true) and asserts all emitted chunks end on a word boundary (last character is space/punctuation/newline or it is the final chunk).
7. **No latency regression:** Flush latency with flag=true must not exceed flag=false latency by more than 80ms (the `MAX_WORD_BUFFER_MS` guard ensures this). Document in Decision Log.

## Pre-commit Gates

```bash
# Verify flag is server-side only
grep -rn "MARSYS_FLAG_R10_SMOOTH_STREAM_V2" platform/src --include="*.ts*" | grep "'use client'" && echo "FAIL: client-side usage found" || echo "PASS: server-side only"

# Verify measure script exists
test -f platform/scripts/measure_smooth_stream.ts && echo "PASS: measure script" || echo "FAIL"

# Run tests
npx jest --testPathPattern="smooth.?stream|SmoothStream" --passWithNoTests
```

## Commit Template

```
feat(streaming): word-aware chunk flushing in smooth_stream.ts

Buffers to word boundary before flush; max buffer 80ms/200 chars.
Eliminates mid-word flicker during streaming. Baseline measured via
measure_smooth_stream.ts. Guarded by MARSYS_FLAG_R10_SMOOTH_STREAM_V2=true
(server-side; no NEXT_PUBLIC, no deploy.yml build-arg).
```

## Decision Log

*(Executor: paste baseline flush metrics here before merging, and latency delta vs flag=false.)*
