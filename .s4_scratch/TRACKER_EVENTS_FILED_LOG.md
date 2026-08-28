# S4 Tracker Events — Filed Log

**Role:** Tracker Ops, S4 (Pipeline Correctness & Door Parity), resuming after
the halt caused by the confirmed global `finding_id` collision
(`V3-E-S4-PROC-001`). Workaround: all tracker `finding_id` values in this
stream's events use the collision-safe `S4-V3-E-0NN` prefix; the EDIR
register's own `V3-E-0NN` entry numbers are unchanged.

## Step 0 — Preflight confirmation

`GET /api/projection` + direct read of
`/Users/Dev/.pariprashna-assurance-control/control-plane.sqlite3`
`stream_sequences` table confirmed, before any write:

- S4 `current_seq` = **1** (only `work_started` had landed)
- S4 `findings` = **[]** (0 accepted writes from the prior halted attempt —
  only rejected `FINDING_ID_CONFLICT` probes on `V3-E-012..024,031`, visible
  in the projection's `rejected_events` trail)

Matched the expected precondition. Proceeded.

## Result summary

| Event type | Expected | Succeeded | Notes |
|---|---|---|---|
| `finding_discovered` | 44 | **44** | actor `lead-s4`; ids `S4-V3-E-012`..`S4-V3-E-055` |
| `finding_triaged` | 44 | **44** | actor `surrogate`; same 44 ids |
| `decision_recorded` (triage philosophy) | 1 | **1** | actor `surrogate` |
| `remediation_approved` | 1 | **1** | actor `surrogate` — see schema note below |

**Final `stream_seq` reached: 91** (1 preflight + 44 + 44 + 1 + 1 = 91).
Confirmed independently via `sqlite3 control-plane.sqlite3
"SELECT * FROM stream_sequences WHERE stream_id='S4'"` → `91`.

**Live projection cross-check** (`GET /api/projection`, post-run):
- `streams[S4].findings` length = 44
- `streams[S4].findings_by_severity` = `{"CRITICAL": 3, "HIGH": 24, "MEDIUM": 15, "LOW": 2}`
  — matches the 44-row severity column in `.s4_scratch/SURROGATE_TRIAGE_TABLE.md`
  exactly (3 CRITICAL: E-013/E-028/E-054; 24 HIGH; 15 MEDIUM; 2 LOW: E-015/E-050)
- `streams[S4].remediation_plan` length = 44
- `streams[S4].remediations` = `{"implemented": 0, "planned": 44, "verified": 0}`

All 88 `finding_discovered`/`finding_triaged` idempotency keys are unique
(44 + 44, no duplicates); all logged HTTP responses were 200/201 with
`accepted: true`.

## Deviation from the task template — `remediation_approved` schema

The task's illustrative `remediation_approved` payload listed only the 6
`FIX_THIS_SESSION` findings. The **first** attempt with exactly those 6
entries was rejected:

```
409 {"accepted": false, "code": "REMEDIATION_PLAN_SCHEMA",
     "error": "the frozen remediation plan must account for every triaged
     stream finding"}
```

Root cause, read directly from
`00_ARCHITECTURE/briefs/pariprashna_assurance/tracker/control.py:582-589`:
the validator computes `planned_findings` from the submitted plan and
requires `set(stream_findings) == planned_findings` — i.e. **every triaged
finding in the stream must have exactly one plan entry**, not just the ones
selected for an actual code fix this session. This is a hard, permanent
schema rule (the remediation plan freezes on submission — a second
`remediation_approved` for the same stream is rejected `REMEDIATION_PLAN_LOCKED`),
so it could not be worked around by filing a partial plan now and topping up
later.

**Resolution:** filed one `remediation_approved` event with all 44 entries —
`id: "S4-REM-0NN"`, `finding_id: "S4-V3-E-0NN"` for every finding. The 6
`FIX_THIS_SESSION` entries carry the exact descriptions given in the task
(S4-REM-013/024/026/039/041/049). The other 38 entries carry an honest
no-op description citing each finding's actual triage disposition from
`SURROGATE_TRIAGE_TABLE.md` (`DEFER_OPEN_S4`, `REFER_S1`/`REFER_S5`/`REFER_S6`,
`ALREADY_TRACKED (P2-B-004/E-119)`, or `NO_ACTION_NEEDED`) rather than
fabricating remediation work that was not planned. No finding was silently
dropped and no false "remediation planned" claim was made for the 38 that
stay OPEN on the register only.

## Severity → finding_id mapping used (tracker severity from the triage table)

| finding_id | severity | disposition |
|---|---|---|
| S4-V3-E-012 | HIGH | DEFER_OPEN_S4 |
| S4-V3-E-013 | CRITICAL | FIX_THIS_SESSION |
| S4-V3-E-014 | HIGH | DEFER_OPEN_S4 |
| S4-V3-E-015 | LOW | REFER_S6 |
| S4-V3-E-016 | MEDIUM | DEFER_OPEN_S4 |
| S4-V3-E-017 | HIGH | DEFER_OPEN_S4 |
| S4-V3-E-018 | MEDIUM | DEFER_OPEN_S4 |
| S4-V3-E-019 | MEDIUM | DEFER_OPEN_S4 |
| S4-V3-E-020 | HIGH | DEFER_OPEN_S4 |
| S4-V3-E-021 | HIGH | DEFER_OPEN_S4 |
| S4-V3-E-022 | MEDIUM | DEFER_OPEN_S4 |
| S4-V3-E-023 | MEDIUM | DEFER_OPEN_S4 |
| S4-V3-E-024 | HIGH | FIX_THIS_SESSION |
| S4-V3-E-025 | HIGH | DEFER_OPEN_S4 |
| S4-V3-E-026 | HIGH | FIX_THIS_SESSION |
| S4-V3-E-027 | HIGH | DEFER_OPEN_S4 |
| S4-V3-E-028 | CRITICAL | DEFER_OPEN_S4 |
| S4-V3-E-029 | MEDIUM | DEFER_OPEN_S4 |
| S4-V3-E-030 | HIGH | DEFER_OPEN_S4 |
| S4-V3-E-031 | HIGH | REFER_S6 |
| S4-V3-E-032 | MEDIUM | DEFER_OPEN_S4 |
| S4-V3-E-033 | HIGH | DEFER_OPEN_S4 |
| S4-V3-E-034 | MEDIUM | DEFER_OPEN_S4 |
| S4-V3-E-035 | HIGH | DEFER_OPEN_S4 |
| S4-V3-E-036 | MEDIUM | DEFER_OPEN_S4 |
| S4-V3-E-037 | MEDIUM | DEFER_OPEN_S4 |
| S4-V3-E-038 | HIGH | DEFER_OPEN_S4 |
| S4-V3-E-039 | HIGH | FIX_THIS_SESSION |
| S4-V3-E-040 | HIGH | DEFER_OPEN_S4 |
| S4-V3-E-041 | HIGH | FIX_THIS_SESSION |
| S4-V3-E-042 | HIGH | REFER_S1 |
| S4-V3-E-043 | HIGH | DEFER_OPEN_S4 |
| S4-V3-E-044 | HIGH | REFER_S5 |
| S4-V3-E-045 | MEDIUM | DEFER_OPEN_S4 |
| S4-V3-E-046 | MEDIUM | DEFER_OPEN_S4 |
| S4-V3-E-047 | MEDIUM | DEFER_OPEN_S4 |
| S4-V3-E-048 | HIGH | ALREADY_TRACKED (P2-B-004/E-119) |
| S4-V3-E-049 | HIGH | FIX_THIS_SESSION |
| S4-V3-E-050 | LOW | NO_ACTION_NEEDED |
| S4-V3-E-051 | HIGH | DEFER_OPEN_S4 |
| S4-V3-E-052 | MEDIUM | DEFER_OPEN_S4 |
| S4-V3-E-053 | MEDIUM | REFER_S6 |
| S4-V3-E-054 | CRITICAL | REFER_S5 |
| S4-V3-E-055 | HIGH | DEFER_OPEN_S4 |

## Errors encountered (all resolved, none unexplained)

1. `finding_discovered` for `S4-V3-E-012`, first probe: an ad-hoc manual test
   POST (outside the batch script) at `expected_stream_seq: 1` succeeded
   (201, `stream_seq: 2`). A subsequent batch-script run reused the same
   `idempotency_key` but a different `expected_stream_seq` (2), which the
   server correctly rejected as `409 IDEMPOTENCY_CONFLICT` ("idempotency key
   was already used for a different request") — the idempotency fingerprint
   covers the full request body including `expected_stream_seq`. Fixed by
   re-running the batch from `current_seq=1` so the first call's body
   byte-for-byte matched the earlier probe and replayed idempotently
   (`idempotent: true`, `stream_seq: 2` returned), then continuing normally.
2. `remediation_approved`, first submission (6-entry plan): `409
   REMEDIATION_PLAN_SCHEMA` — see the schema-deviation section above. Fixed
   by resubmitting with all 44 entries.

No `FINDING_ID_CONFLICT` occurred on any of the 44 `S4-V3-E-0NN` ids — the
collision-safe prefix worked as designed.

## Evidence

Every `finding_discovered` event cited `{kind: "code", uri: "repo://<code
anchor>"}` (the anchor from that entry's EDIR register body) plus `{kind:
"doc", uri: "repo://00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md#V3-E-0NN"}`.
Three entries had no code anchor in the register (BASELINE/measurement
findings) and used the nearest available source-report or component path in
its place: `S4-V3-E-015` (`.s4_scratch/S4_synergy_latency_waterfall_report.md`),
`S4-V3-E-043` (`platform/src/lib/trace/emitter.ts`), `S4-V3-E-050`
(`platform/src/components/pariprashna/working/WorkingBand.tsx`).

`decision_recorded` cited `.s4_scratch/SURROGATE_TRIAGE_TABLE.md` and the
register's own `V3-E-S4-PROC-001` process-finding entry. `remediation_approved`
cited `.s4_scratch/SURROGATE_TRIAGE_TABLE.md`.

## Status

**Complete.** All 44 findings filed and triaged, decision recorded,
remediation plan frozen (44/44 findings accounted for, 6 real fixes + 38
honest no-op dispositions). Final `stream_seq = 91`, verified against both
the live `/api/projection` endpoint and the control-plane sqlite ledger
directly.
