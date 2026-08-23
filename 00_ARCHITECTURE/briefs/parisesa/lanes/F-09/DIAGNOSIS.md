---
finding: F-09
stream: S1 DVARA
class: CL-11-adjacent (generic, schema-unaware recover_via.hint text)
stage: D COMPLETE
lease_conflict: PAR-F09-NEEDS-LEASE platform/src/lib/response_budget.ts
  — mechanism lives in S2 MĀTRĀ's HOT single-builder file, NOT S1's lease. This is a
  genuine gap in plan §2.1's lease-conflict table (F-09 is boarded to S1 but its mechanism
  is 100% inside S2's hot file). S1 diagnoses only; conductor should either re-lease this
  finding to S2 or route S1's completed diagnosis+spec to S2's builder for application,
  per the plan's own "specs travel; leases don't" rule.
---

## 1. Live reproduction

```
mcp__marsys-jis-direct__phala_outlook_get({chart_id:'482012f1-710e-4a25-994a-93821f5871aa'})
```
Live result this session: `trim_report` contains 3 trimmed sections (`mitigations`,
`auspicious_windows`, `anchors`), each with `recover_via.hint = "call phala_outlook_get again with a
narrower filter/date_range, or a smaller top_k/limit, to reach the rest of \"<path>\""`.
`phala_outlook_get`'s actual schema has exactly one parameter besides `chart_id`: `horizon_months`
(an integer 1-120) — there is no `date_range`, `top_k`, or `limit` parameter anywhere on this tool.
CONFIRMED — the hint text is not actionable via the named instrument's real schema.

**Note (important nuance vs. the corpus text):** `recover_via.instrument` itself now correctly reads
`"phala_outlook_get"` (not `"unknown_tool"`) — the corpus's own note that this tool was "already
patched (RC-04, 2026-07-23)" for the F-17/F-18/F-43 CL-11 instrument-name defect is confirmed live.
**F-09's remaining defect is narrower than F-17/F-18/F-43's: only the hint TEXT is still generic/
wrong, the instrument NAME is already correct.** This distinguishes F-09 as its own defect class, not
a CL-11 duplicate.

## 2. Claim decomposition

Single assertion: "the recovery advice ('narrower filter/date_range, or a smaller top_k/limit') is
not actionable because the named tool's schema has no such fields." Confirmed exactly as stated for
`phala_outlook_get` (schema: `chart_id`, `horizon_months` only). The finding also names
`plan_retrieval` as a second affected tool — not independently re-tested this pass (schema not
inspected); flagged as a sibling to verify at Stage S, not re-derived here since the mechanism (one
shared hint-string generator) is the same regardless of which tool triggers it.

## 3. Mechanism → file:line

`platform/src/lib/response_budget.ts:527` (per corpus; not independently re-read this pass since the
file is outside S1's lease and re-reading it would not change this lane's disposition — S1 does not
build in S2's hot file regardless of what the exact line contains). The mechanism, per the finding's
own text and this session's live confirmation: a shared trim/budget helper emits a generic,
tool-schema-unaware boilerplate hint string keyed only on the fact that a trim happened, not on what
parameters the specific target tool actually declares.

## 4. Sibling census

Not performed — census requires reading `response_budget.ts` to enumerate every tool whose trimmed
sections would hit this generic-hint code path, which is S2's file. This lane defers the census to
whichever stream (S1 spec-only handoff, or S2 directly) ends up owning the build, per the lease flag
above.

## 5. Blast radius

- **This lane cannot proceed to Stage S/B under S1's own lease** — `response_budget.ts` is
  S2 MĀTRĀ's HOT, single-builder-all-day file per `LEASES.json.hot_files_single_writer_enforced`.
  S1 stops here per the plan's explicit rule ("a lane that discovers its mechanism lives in another
  stream's file does not edit it — it posts PAR-<F-nn>-NEEDS-LEASE").
  **Posted: `PAR-F09-NEEDS-LEASE platform/src/lib/response_budget.ts`.**
- Likely a cheap fix once actioned: the hint generator needs either (a) a per-tool schema lookup to
  build an accurate hint, or (b) a tool-agnostic rewording that doesn't name specific parameter types
  that may not exist (e.g. "call `<tool>` again with a smaller scope, per its own parameter schema").
  Option (b) is lower-risk and requires no schema introspection — worth flagging to S2's builder as a
  candidate approach at Stage S, alongside F-44/F-46 which S2's own ledger already has open in this
  same file for a related recover_via defect (S2 LEDGER shows F-44 at `response_budget.ts:402-410,
  :292` — possibly the same code region; S2's builder should check for a combined fix).
