---
canonical_id: R11A_A_S9
session_id: A-S9
title: Telemetry — log capability paths per request to Observatory
phase: R11.A — Foundation
depends_on: [A-S7]
flag: MARSYS_FLAG_R11V2_CAPABILITY_TELEMETRY
flag_default: true
client_side: "no — server-side telemetry pipeline"
authored: 2026-05-22
---

# A-S9 — Telemetry: Capability Paths

## Context

When the dispatcher routes a capability call, we want to log:
- Which stack id was active
- Which capability was invoked
- Whether the manifest declared support (and via which variant)
- Whether the call succeeded or threw `CapabilityUnsupportedOnStackError`

This telemetry feeds Observatory dashboards (Phase O infrastructure) and informs future Learning-Layer feedback (R11.H). Gated by `MARSYS_FLAG_R11V2_CAPABILITY_TELEMETRY` (default true).

A new SSE data part `data-capability-path` carries per-request capability invocation info to the client (Observatory pipeline downstream). Existing Observatory cost-events emit pattern is the template.

## Files in Scope

### Add

- `platform/src/lib/observatory/capability_telemetry.ts` — telemetry emitter:
  ```typescript
  export interface CapabilityPathRecord {
    stackId: StackId;
    capability: keyof CapabilityAdapter;
    manifestSupport: string | boolean | number | null;
    success: boolean;
    durationMs: number;
    errorClass?: string;
  }
  
  export function logCapabilityPath(record: CapabilityPathRecord): void {
    if (!FLAGS.MARSYS_FLAG_R11V2_CAPABILITY_TELEMETRY) return;
    // Emit to Observatory + audit log
  }
  ```
- `platform/tests/observatory/capability_telemetry.test.ts` — unit tests for emit + flag-guard behavior.

### Modify

- `platform/src/lib/providers/dispatcher.ts` — wrap `dispatch()` to record a `CapabilityPathRecord` on every call (success + failure). Use `logCapabilityPath()`.
- `platform/src/lib/streams/data_parts.ts` — declare `CapabilityPathPart` SSE data-part shape (mirrors `CapabilityPathRecord` shape minus internal fields).
- `platform/src/app/api/chat/consume/route.ts` — emit `data-capability-path` part for each dispatch call within a turn.

## Files MUST NOT Touch

- Observatory dashboard UI (separate workstream; only the pipeline is touched)
- Existing cost-events emit logic (A-S9 adds alongside)
- Other adapters

## Acceptance Criteria

1. `logCapabilityPath()` writes telemetry records via the Observatory pipeline.
2. `dispatch()` calls `logCapabilityPath()` on every invocation (success and failure paths).
3. `data-capability-path` SSE part is declared in `data_parts.ts` and emitted by route.ts.
4. Flag guard: when `MARSYS_FLAG_R11V2_CAPABILITY_TELEMETRY=false`, no records written + no SSE part emitted.
5. Server-side only — no NEXT_PUBLIC.
6. Tests verify: flag-on writes; flag-off skips; record shape matches schema; failure paths include `errorClass`.
7. No regression: existing cost-events still emit unchanged.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11A/platform
test -f src/lib/observatory/capability_telemetry.ts && echo "PASS"
grep -rn "NEXT_PUBLIC.*CAPABILITY_TELEMETRY" src --include="*.ts*" && echo "FAIL: should be server-side" || echo "PASS"
grep -n "data-capability-path\|CapabilityPathPart" src/lib/streams/data_parts.ts && echo "PASS: SSE part declared"
grep -n "logCapabilityPath" src/lib/providers/dispatcher.ts && echo "PASS: dispatcher emits"
npx jest --testPathPattern="capability_telemetry|A-S9" --passWithNoTests
```

## Commit Template

```
feat(observatory): capability-path telemetry per dispatch (A-S9)

logCapabilityPath() records every dispatch call: stack id, capability,
manifest support, success/failure, duration, error class on failure.
Pipeline emits data-capability-path SSE part to client for downstream
Observatory aggregation.

Gated by MARSYS_FLAG_R11V2_CAPABILITY_TELEMETRY=true (server-side; no
NEXT_PUBLIC). Pipeline integration preserves existing cost-events emit.

Foundation for Learning-Layer feedback (R11.H) and Observatory dashboards.
```

## Decision Log

*(Executor: paste sample telemetry record from a real dispatch; confirm Observatory ingestion is end-to-end.)*
