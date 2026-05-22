---
canonical_id: R11C_C_S2
session_id: C-S2
title: Smooth-stream rate-target ~30-50 cps on top of Y-S3 word-aware flush
phase: R11.C
depends_on: [C-S1]
flag: MARSYS_FLAG_R11C_SMOOTH_STREAM_V3 (server-side, default true)
client_side: "no — server-side stream adapter"
authored: 2026-05-22
---

# C-S2 — Smooth-Stream Rate-Target

## Context

Add char-per-sec rate-targeting on top of Y-S3's word-aware flush in `smooth_stream.ts`. TARGET_CPS=40 default. Server-side flag; rollback path is flag off.

## Files in Scope

- `platform/src/lib/streaming/smooth_stream.ts` — add rate-target loop preserving Y-S3 word-boundary + MAX_BUFFER_MS=80.
- `platform/scripts/measure_smooth_stream.ts` — extend benchmarking.
- `platform/src/lib/config/feature_flags.ts` — register flag.

## Files MUST NOT Touch

- SSE event shape
- Stream-1 UI files
- Y-S3 word-boundary detection (preserve, extend)

## Acceptance Criteria

1. TARGET_CPS=40 constant in smooth_stream.ts.
2. With flag=true, observed mean cps over 5s window within ±15% of TARGET_CPS on bursty input.
3. Y-S3 word boundary + 80ms MAX preserved.
4. Flag=false retains Y-S3 behavior exactly.
5. Server-side only — no NEXT_PUBLIC.
6. Unit test + baseline measurement.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
grep -rn "NEXT_PUBLIC.*SMOOTH_STREAM_V3" src --include="*.ts*" && echo "FAIL" || echo "PASS"
grep -n "TARGET_CPS" src/lib/streaming/smooth_stream.ts && echo "PASS"
npx jest --testPathPattern="smooth.?stream|C-S2" --passWithNoTests
```

## Commit Template

```
feat(streaming): rate-target buffer ~40 cps on Y-S3 word-aware (C-S2)
```

## Decision Log

*(Executor: paste pre/post measure_smooth_stream metrics.)*
