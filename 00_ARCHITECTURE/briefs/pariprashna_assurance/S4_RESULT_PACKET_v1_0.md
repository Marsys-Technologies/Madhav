---
artifact: S4_RESULT_PACKET
version: "1.0"
status: CURRENT — stream S4 (Pipeline Correctness & Door Parity) result packet per
  templates/STREAM_RESULT_PACKET_TEMPLATE.md. NOT yet integrator-accepted at the
  tracker level — see §7 for the honest gap.
date: 2026-08-28
stream_id: S4
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/charters/STREAM_CHARTER_S4_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/S4_LATENCY_WATERFALL_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md (V3-E-012..055, V3-E-S4-PROC-001, V3-E-S4-PROC-002)
changelog:
  - "1.0 (2026-08-28): initial and final packet for this session's S4 run."
---

# S4 Result Packet — Pipeline Correctness & Door Parity

## 1 — Scenarios planned / executed

**54 / 54.** Frozen denominator (stated at `work_started`, tracker event `3f9e4774…`):
11 pipeline stages × 4 dimensions (correctness/optimality/failure-honesty/
demonstrated-can-fail) = 44, + 3 dual-door repeats (S1/S5/S8 MCP-twinned stages) = 3,
+ 6 §4.3 synergy tests = 6, + 1 J10 whole-receipt parity = 1. All 54 executed by 17
parallel investigation agents; each scenario's evidence is a `.s4_scratch/*.md` report,
filed to the tracker as 54 `scenario_executed` events (stream_seq 91→145).

Several scenarios reached **LIVE rung** against the real deployed pipeline (real
`prashna_ask`/`prashna_status` MCP-door turns, real DB via Cloud SQL proxy) — notably
the latency waterfall, progress-truthfulness (E-003 re-verification), and citation
density (E-005 re-verification) scenarios. Deployed Cloud Run images (`amjis-web`,
`amjis-mcp`) were confirmed stale behind baseline at session open — any claim that
needed the actual deployed revision (rather than local-dev-against-real-DB, which is
what "LIVE" above means throughout) records that gap honestly rather than fabricating
a pass; see the charter's own pin note and the session's SECOND ACTION re-check.

## 2 — Findings and root causes

**44 new EDIR_V3 entries filed (`V3-E-012` through `V3-E-055`)**, deduplicated from
~60+ raw findings across 17 agent reports — 12 are fresh 2026-08-28 reproductions of
already-numbered historical findings (E-003/004/005/006/039/048/050/104/105/112,
GAP-6, GAP-8/PPR-16), the rest are new. Severity triaged by a Native Surrogate agent
(Opus), never by the finder, per register law. Two PROCESS findings filed on campaign
infrastructure itself: `V3-E-S4-PROC-001` (a confirmed cross-stream register/tracker
`finding_id` numbering collision — worked around locally, needs Session C
reconciliation) and `V3-E-S4-PROC-002` (the tracker's all-or-nothing remediation gate
— see §7).

**Headline findings:**
- Only **1 of 10** inter-stage boundaries has a real runtime schema gate; the other 9
  either crash raw or silently corrupt on malformed input (`V3-E-040`).
- S6's tool dispatch has **no per-tool timeout anywhere** — a hung tool blocks the
  entire retrieve stage indefinitely with zero honest reporting, demonstrated live
  (`V3-E-031`).
- The MCP door has **no call path to receipt assembly at all** (18/18 receipt fields
  diverge from Portal) and **runs zero S9 grounding validation** — both root-caused to
  the already-tracked P2-B-004/E-119 persistence gap (`V3-E-048`, `V3-E-017`).
- Predictive-class turns show **0% tool-selection efficiency** — full 10-tool floor
  dispatched, zero citations produced, 14/14 real DB-traced turns (`V3-E-028`).
- E-004 (truncation-disclosure) confirmed **still broken** pre-fix, live-reproduced,
  and its own permanent test suite never actually checked the thing it claimed to
  guard (`V3-E-013`) — fixed this session.
- E-003 (progress-freeze) confirmed **still broken and worse than the original seed**
  (91% of a live turn frozen vs. the seed's 43%), live-reproduced twice independently
  (`V3-E-012`).
- The published **latency waterfall** (§6 below) shows 99.31% of wall-clock time is
  natively unattributed on this pipeline today.

Full findings table, code anchors, evidence, and severities: `EDIR_V3_REGISTER_v1_0.md`
§4b (`V3-E-012`–`V3-E-055`).

## 3 — Remediations verified / rejected

**6 verified and merged; 38 dispositioned (not attempted this session, by design).**

| Finding | Fix | PR | Independent verifier |
|---|---|---|---|
| V3-E-013 (E-004 truncation) | Deterministic post-hoc disclosure sentence | [#1620](https://github.com/Marsys-Technologies/Madhav/pull/1620) | ACCEPT |
| V3-E-024 (llm_extension_note discarded) | Threaded through all 3 real call sites (extended after first verifier found the initial PR only covered 1 of 3) | [#1621](https://github.com/Marsys-Technologies/Madhav/pull/1621) | REJECT → fixed → ACCEPT |
| V3-E-026 + V3-E-039 (silent signal drops) | Additive flag emission, zero serving-decision change (verified by reverting only the regenerated baseline and re-running) | [#1622](https://github.com/Marsys-Technologies/Madhav/pull/1622) | ACCEPT |
| V3-E-041 (misleading entitlement error copy) | Honest, non-retry messages for 4 error codes | [#1623](https://github.com/Marsys-Technologies/Madhav/pull/1623) | ACCEPT |
| V3-E-049 (safety_decision envelope gap) | decision_id/review_id/audit_written added; checked for IDOR (none — UUIDv4, only consumer is super-admin-gated) | [#1624](https://github.com/Marsys-Technologies/Madhav/pull/1624) | ACCEPT |

All 5 PRs: verifier-accepted (distinct actor from fixer) + own-territory + full CI
green + weakens no test/CI/auth/safety/guard + merged via the branch-protection merge
queue. One genuine merge conflict encountered and resolved by hand (PR #1621 vs. the
already-merged #1622, both adding independent code in the same function) — both
additive blocks kept, 162/165 tests re-verified post-resolution before re-push.

None of the 6 fixes touch `authorizeChartAccess.ts` or `safety_gate.ts` gating logic —
confirmed independently by every verifier via `git diff`.

**38 findings dispositioned, not remediated this session** (Native Surrogate triage,
`SURROGATE_TRIAGE_TABLE.md`): `DEFER_OPEN_S4` (in S4 territory, too large/risky for
this session — 30), `REFER_S1`/`REFER_S5`/`REFER_S6` (cross-territory — 6, referral
notes appended to each EDIR entry), `ALREADY_TRACKED` (additive to P2-B-004/E-119,
cited not duplicated — 1), `NO_ACTION_NEEDED` (informational baseline — 1).

## 4 — Regression evidence

Every landed fix ran its own targeted red→green demonstration plus a broader
regression sweep, independently re-run by a distinct verifier agent (not the fixer):
124–2184 tests green per PR depending on scope, `tsc --noEmit`/`eslint` clean on every
touched file, zero pre-existing test broken. Full detail in each PR's description and
its independent verifier's report (see `.s4_scratch/AGENT_COMPLETION_LOG.md` for the
consolidated trail).

## 5 — Independent verifier verdict

**5 of 5 fix PRs independently verified ACCEPT** (one — #1621 — after an initial
REJECT correctly caught a real scope gap, which was then fixed and re-verified).
Verifiers were distinct actors from the fixers throughout (harness §independence law).
The stream's own closure was independently recommended by the `verifier` tracker actor
(`stream_closure_recommended`, tracker event, stream_seq 158) citing 54/54 scenarios,
44/44 findings triaged, 6/44 remediated-and-verified, 38/44 honestly dispositioned.

## 6 — Latency waterfall (required S6 input)

Published as its own first-class artifact: `S4_LATENCY_WATERFALL_v1_0.md`. Headline:
of a real 102.4s LIVE turn, 0.69% (tool dispatch) is natively accounted for; 99.31% is
unattributed because no per-stage timer exists between S1 and S11 on either door. This
independently corroborates and sharpens EDIR E-006 on a second live turn.

## 7 — Open A3 decisions and residual risks

- **Tracker closure credit is BLOCKED, not obtained** — `result_packet_accepted`/CG-3
  could not be filed at the tracker level. Root cause: the tracker's `S4:remediation`
  work-item gate requires ALL 44 triaged findings to reach `VERIFIED`, not just the 6
  selected for same-session remediation, conflicting with the elevation's own
  explicitly-endorsed partial-scope model. Filed as `V3-E-S4-PROC-002` — a decision
  for the Programme Integrator/native, not resolvable by more stream-local tracker
  events (fabricating verification for the 38 un-remediated findings was explicitly
  refused as an unearned-green violation). Tracker state: `work_started` →
  `finding_discovered` ×44 → `finding_triaged` ×44 → `decision_recorded` →
  `remediation_approved` (44-entry plan) → `scenario_executed` ×54 →
  `remediation_implemented` ×6 → `verification_accepted` ×6 →
  `stream_closure_recommended` → 3 of 6 `work_item_accepted` stages (`charter`,
  `baseline`, `triage`) landed; `remediation`/`verification`/`regression`/`closure`
  stages blocked on the same gate. Final tracker stream_seq: 165.
- **Cross-stream EDIR numbering collision** (`V3-E-S4-PROC-001`) — S4's `V3-E-012..055`
  collide with sibling streams' (S1/S2/S3/S5) independently-numbered entries on their
  own branches/on main. Worked around locally (tracker `finding_id`s prefixed `S4-`);
  the register's own entry numbers are unchanged pending Session C reconciliation.
- **6 findings referred cross-territory** (V3-E-042→S1, V3-E-044/V3-E-054→S5,
  V3-E-015/V3-E-031/V3-E-053→S6) — referral notes appended to each register entry;
  not fixed by S4 per elevation §8.3.
- **30 findings deferred OPEN in S4's own territory** — real, evidenced, triaged, not
  attempted this session (too large/risky for a same-session additive fix per Native
  Surrogate judgment). Available for a future S4-territory session; `V3-E-034`,
  `V3-E-045`, `V3-E-055` are the Surrogate's own stated top picks for next time.
- **B-002-class caution honored**: nothing in this session's 6 landed fixes touches
  `authorizeChartAccess`/`safety_gate.ts` gating logic — every candidate that came
  close (`V3-E-044`, `V3-E-053`, `V3-E-054`) was referred to S5 instead of squeezed in,
  per the harness's absolute rail on auth-adjacent changes.

This packet is a link set to primary evidence (EDIR_V3_REGISTER §4b, 5 merged PRs,
`S4_LATENCY_WATERFALL_v1_0.md`, `.s4_scratch/*` investigation reports). It is not
tracker-level acceptance until the §7 gap is resolved by the Programme Integrator.

*End S4_RESULT_PACKET v1.0.*
