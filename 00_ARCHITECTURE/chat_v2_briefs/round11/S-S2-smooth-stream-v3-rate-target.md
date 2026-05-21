---
canonical_id: R11_S_S2
version: 1.0
status: CURRENT
session_id: S-S2
title: Smooth-stream v3 — char-per-sec rate-targeting on top of Y-S3 word-aware flush
depends_on: ["S-S1"]
blocked_on: []
flag: MARSYS_FLAG_R11_SMOOTH_STREAM_V3
flag_default: true
client_side: "no — server-side adapter"
authored: 2026-05-21
---

# S-S2 — Smooth-Stream v3 (Rate-Target)

## Context

Y-S3 added word-aware flushing to `smooth_stream.ts` (no mid-word splits). Claude.ai goes one further: its perceived cadence is a near-uniform character-per-second rate (~30-50 cps) regardless of how lumpy the upstream token batches arrive. This session adds rate-target buffering on top of Y-S3's word-aware foundation.

Per Y-S3's MEASURE_SMOOTH_STREAM script, the executor first benchmarks current cadence, then implements a target cps that brings observed flush rate within ±15% of the target over a 5-second window.

## Files in Scope

- `platform/src/lib/streaming/smooth_stream.ts` — add a rate-target loop: if the buffer has content AND elapsed since last flush > `1000/TARGET_CPS * <chars in buffer>`, flush; preserve Y-S3's word-aware flushing as a tiebreaker.
- `platform/scripts/measure_smooth_stream.ts` — extend to record observed cps over a 5s window with new gate behavior.
- `platform/src/lib/feature_flags.ts` — register `MARSYS_FLAG_R11_SMOOTH_STREAM_V3` (default true; server-side, no NEXT_PUBLIC).
- `platform/tests/` — unit test for rate-target.

## Files Must NOT Touch

- The SSE event shape
- Client-side rendering (no `'use client'` files)
- `.github/workflows/deploy.yml` (server-side flag)
- Y-S3's word-aware boundary detection logic (preserve, extend)
- Phase 4C files

## Acceptance Criteria

1. **Flag is server-side (Amendment 1):** `MARSYS_FLAG_R11_SMOOTH_STREAM_V3` does NOT appear with NEXT_PUBLIC.
2. **TARGET_CPS constant:** declared at the top of `smooth_stream.ts`, default 40 (cps). Tunable via the same flag's value if needed (optional refinement).
3. **Rate-target loop:** with flag=true, observed mean cps over a 5s window on a stream with bursty input falls within ±15% of TARGET_CPS.
4. **Word boundary preserved:** Y-S3's word-boundary flush still holds — no mid-word splits.
5. **MAX_BUFFER_MS guard preserved:** Y-S3's 80ms max-hold preserved.
6. **Flag guard:** with flag=false, behavior is exactly Y-S3 (no rate-target).
7. **Unit test:** simulate a bursty input (one delta per char vs one delta per word), assert mean output cps within target band.
8. **Baseline + post measurement:** executor runs `measure_smooth_stream.ts` before and after, pastes both in Decision Log.

## Pre-commit Gates

```bash
grep -rn "NEXT_PUBLIC.*SMOOTH_STREAM_V3" platform/src --include="*.ts*" && echo "FAIL: NEXT_PUBLIC found" || echo "PASS: server-side only"
grep -n "TARGET_CPS\|targetCps" platform/src/lib/streaming/smooth_stream.ts && echo "PASS: constant defined"
npx jest --testPathPattern="smooth.?stream|S-S2" --passWithNoTests
```

## Commit Template

```
feat(streaming): smooth-stream v3 — char-per-sec rate-targeting

Adds TARGET_CPS=40 rate-target loop to smooth_stream.ts on top of Y-S3 word-aware
flush. Mean observed cps within ±15% of target on bursty input. Y-S3 word-boundary
+ 80ms max-hold preserved. Guarded by MARSYS_FLAG_R11_SMOOTH_STREAM_V3=true
(server-side; no NEXT_PUBLIC).
```

## Decision Log

*(Executor: paste pre/post measure_smooth_stream metrics, observed mean cps, and the chosen TARGET_CPS value.)*
