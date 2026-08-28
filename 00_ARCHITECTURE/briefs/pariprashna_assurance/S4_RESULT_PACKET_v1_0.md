---
artifact: S4_RESULT_PACKET
version: "1.1"
status: CURRENT — stream S4 (Pipeline Correctness & Door Parity) result packet per
  templates/STREAM_RESULT_PACKET_TEMPLATE.md. CONVERGENCE-READY, NOT closed — a
  resume session (2026-08-29) drove additional remediation but the tracker-level
  result_packet_accepted/CG-3 event remains BLOCKED — see §7.
date: 2026-08-29
stream_id: S4
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/charters/STREAM_CHARTER_S4_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/S4_LATENCY_WATERFALL_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/EDIR_V3_REGISTER_v1_0.md (V3-E-012..056, V3-E-S4-PROC-001, V3-E-S4-PROC-002)
changelog:
  - "1.1 (2026-08-29, resume session): 4 additional findings driven to MERGED +
    independently-verified (V3-E-034, V3-E-045, V3-E-055, and newly-absorbed
    V3-E-056 — S3's citation_resolver.ts CRITICAL). 10/44 findings now have a
    landed fix (was 6/44). Confirmed a second facet of the tracker gate
    (FINDING_FREEZE blocks new findings post-plan-freeze, live-tested). 34
    findings remain OPEN, re-confirmed still valid (checked S1/S5/S6 branches
    for overlapping fixes — none found)."
  - "1.0 (2026-08-28): initial packet for the first S4 session."
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

**10 verified and merged (6 original session + 4 resume session); 34 dispositioned (not attempted, by design).**

| Finding | Fix | PR | Independent verifier |
|---|---|---|---|
| V3-E-013 (E-004 truncation) | Deterministic post-hoc disclosure sentence | [#1620](https://github.com/Marsys-Technologies/Madhav/pull/1620) | ACCEPT |
| V3-E-024 (llm_extension_note discarded) | Threaded through all 3 real call sites (extended after first verifier found the initial PR only covered 1 of 3) | [#1621](https://github.com/Marsys-Technologies/Madhav/pull/1621) | REJECT → fixed → ACCEPT |
| V3-E-026 + V3-E-039 (silent signal drops) | Additive flag emission, zero serving-decision change (verified by reverting only the regenerated baseline and re-running) | [#1622](https://github.com/Marsys-Technologies/Madhav/pull/1622) | ACCEPT |
| V3-E-041 (misleading entitlement error copy) | Honest, non-retry messages for 4 error codes | [#1623](https://github.com/Marsys-Technologies/Madhav/pull/1623) | ACCEPT |
| V3-E-049 (safety_decision envelope gap) | decision_id/review_id/audit_written added; checked for IDOR (none — UUIDv4, only consumer is super-admin-gated) | [#1624](https://github.com/Marsys-Technologies/Madhav/pull/1624) | ACCEPT |
| V3-E-034 (registry-lookup miss escapes toolEventLog) *(resume)* | Distinct `error_kind`, distinct `empty_reason` | [#1643](https://github.com/Marsys-Technologies/Madhav/pull/1643) | ACCEPT |
| V3-E-045 (turn_id ≠ persisted queryId) *(resume)* | Unified id (31 baseline fixtures regenerated, byte-identical after UUID normalization) | [#1644](https://github.com/Marsys-Technologies/Madhav/pull/1644) | ACCEPT |
| V3-E-055 (WEB door zero safety test coverage) *(resume)* | 5 new route-level tests, mutation-tested | [#1645](https://github.com/Marsys-Technologies/Madhav/pull/1645) | ACCEPT |
| **V3-E-056** (citation_resolver.ts CRITICAL, absorbed from S3's `V3-E-032`) *(resume)* | Widened id-recognition to 4 chart-scoped tables; root cause live-verified (SIG.MSR.NNN never occurs in production, `signal_id` is a UUID) | [#1646](https://github.com/Marsys-Technologies/Madhav/pull/1646) | **REJECT** (reader-visible leak found) → fixed → **ACCEPT** |

All 9 PRs: verifier-accepted (distinct actor from fixer) + own-territory + full CI
green + weakens no test/CI/auth/safety/guard + merged via the branch-protection merge
queue. Two genuine merge conflicts encountered and resolved by hand: PR #1621 vs. the
already-merged #1622 (both adding independent code in the same function, both blocks
kept); and the resume-session branches needed re-rebasing onto main twice as sibling
streams (S1/S3/S5) continued merging concurrently.

**The citation fix (V3-E-056) is the one genuine adversarial catch in this stream**:
round-1 review found the widened citation resolution surfaced raw internal DB strings
(`chart_facts.citation_human`, e.g. `"upagraha_position.DHUMA.sign_lord = Moon
(true_chitra)."`) as the reader-visible citation label, unlinted, on 14,945 live
production rows — and the fix's own test asserted the leak as expected output. The
follow-up removed `citation_human` from the SELECT entirely for the two affected
sources (structurally impossible to leak, not merely unused), preserving the
grounding-correctness fix (the actual point of the defect) via a safe placeholder
label. Round-2 review used mutation testing (reintroduced the exact original leak,
confirmed the new tests catch it) before accepting.

None of the 10 fixes touch `authorizeChartAccess.ts` or `safety_gate.ts` gating logic
— confirmed independently by every verifier via `git diff`.

**34 findings dispositioned, not remediated** (Native Surrogate triage,
`SURROGATE_TRIAGE_TABLE.md`, re-confirmed still valid this resume session — checked
S1/S5/S6 branches for any overlapping fix landing on the 6 cross-referred findings;
none found as of this session): `DEFER_OPEN_S4` (in S4 territory, too large/risky for
a same-session additive fix — 27, down from 30 as V3-E-034/045/055 moved to fixed),
`REFER_S1`/`REFER_S5`/`REFER_S6` (cross-territory — 6, referral notes appended to each
EDIR entry, still open on target streams), `ALREADY_TRACKED` (additive to
P2-B-004/E-119, cited not duplicated — 1), `NO_ACTION_NEEDED` (informational baseline
— 1).

## 4 — Regression evidence

Every landed fix ran its own targeted red→green demonstration plus a broader
regression sweep, independently re-run by a distinct verifier agent (not the fixer):
124–2184 tests green per PR depending on scope, `tsc --noEmit`/`eslint` clean on every
touched file, zero pre-existing test broken. Full detail in each PR's description and
its independent verifier's report (see `.s4_scratch/AGENT_COMPLETION_LOG.md` for the
consolidated trail).

## 5 — Independent verifier verdict

**9 of 9 fix PRs independently verified ACCEPT** (two — #1621 and #1646 — after an
initial REJECT correctly caught a real gap, fixed, and re-verified: #1621's scope was
incomplete, #1646's carried a real reader-visible data leak). Verifiers were distinct
actors from the fixers throughout (harness §independence law); the CRITICAL fix (#1646)
was reviewed twice by an Opus-tier verifier given its severity. The stream's own
closure was independently recommended by the `verifier` tracker actor
(`stream_closure_recommended`, tracker event, stream_seq 158, from the FIRST session)
citing 54/54 scenarios, 44/44 findings triaged; that recommendation predates the resume
session's additional 4 remediations and remains valid (nothing it cited changed, more
was only added on top).

## 6 — Latency waterfall (required S6 input)

Published as its own first-class artifact: `S4_LATENCY_WATERFALL_v1_0.md`. Headline:
of a real 102.4s LIVE turn, 0.69% (tool dispatch) is natively accounted for; 99.31% is
unattributed because no per-stage timer exists between S1 and S11 on either door. This
independently corroborates and sharpens EDIR E-006 on a second live turn.

## 7 — Open A3 decisions and residual risks

- **Tracker closure credit is BLOCKED, not obtained — confirmed in TWO distinct forms
  this resume session.** (a) The original gate: `S4:remediation` work-item acceptance
  requires ALL 44 triaged findings to reach `VERIFIED`, not just the ones with a real
  same-session fix — `V3-E-S4-PROC-002`. (b) NEW this session, live-tested: once
  `remediation_approved` freezes a stream's plan, the tracker ALSO refuses any new
  `finding_discovered` event (`409 FINDING_FREEZE`) — confirmed by a real API call,
  which is why `V3-E-056` (the absorbed citation CRITICAL) could not be filed as a
  tracker event despite being real, triaged, fixed, and independently verified. Both
  are the same underlying problem (the tracker has no path for a stream to resume with
  new in-scope work after its own plan freeze) and both need a Programme
  Integrator/native decision, not a stream-local workaround — fabricating either a
  verification or a finding-discovery event was explicitly refused both times.
  Tracker state as of this addendum: `work_started` → `finding_discovered` ×44 →
  `finding_triaged` ×44 → `decision_recorded` → `remediation_approved` (44-entry plan)
  → `scenario_executed` ×54 → `remediation_implemented` ×9 (6 original + 3 resume;
  `V3-E-056` excluded, see above) → `verification_accepted` ×6 (original session only
  — the resume session's 4 new fixes have real independent-verifier ACCEPT reports
  staged as evidence in this packet and the register, but their tracker-level
  `verification_accepted` event is convergence's to run, same as the original 6's
  formal-acceptance chain) → `stream_closure_recommended` → 3 of 6 `work_item_accepted`
  stages landed (`charter`, `baseline`, `triage`); `remediation`/`verification`/
  `regression`/`closure` stages remain blocked on gate (a). Final tracker stream_seq:
  **168**.
- **Cross-stream EDIR numbering collision** (`V3-E-S4-PROC-001`) — S4's `V3-E-012..056`
  collide with sibling streams' (S1/S2/S3/S5) independently-numbered entries on their
  own branches/on main. Worked around locally (tracker `finding_id`s prefixed `S4-`);
  the register's own entry numbers are unchanged pending Session C reconciliation.
- **6 findings referred cross-territory** (V3-E-042→S1, V3-E-044/V3-E-054→S5,
  V3-E-015/V3-E-031/V3-E-053→S6) — referral notes appended to each register entry;
  re-checked this resume session against S1/S5/S6's current branches, none yet
  addressed by their target streams (S5 independently hit the SAME `V3-E-S4-PROC-002`
  tracker gate at their own closure attempt — corroborating evidence the gate is a
  campaign-wide problem, not S4-specific).
- **27 findings deferred OPEN in S4's own territory** — real, evidenced, triaged, not
  attempted (too large/risky for a same-session additive fix per Native Surrogate
  judgment), down from 30 as `V3-E-034`/`V3-E-045`/`V3-E-055` — the Surrogate's own
  named top picks — moved to fixed this resume session. Available for a future
  S4-territory session.
- **B-002-class caution honored across both sessions**: nothing in the 10 landed fixes
  touches `authorizeChartAccess`/`safety_gate.ts` gating logic — every candidate that
  came close (`V3-E-044`, `V3-E-053`, `V3-E-054`) was referred to S5 instead of
  squeezed in, per the harness's absolute rail on auth-adjacent changes.
- **The citation CRITICAL (V3-E-056) is the one item genuinely absent from the
  original 44-finding denominator** — it was absorbed from a cross-stream referral
  discovered AFTER the original session's `work_started`/triage/plan-freeze sequence.
  It is real, fixed, merged, and independently verified (twice), but sits outside the
  tracker's own scenario/finding accounting for this stream by construction (see the
  FINDING_FREEZE point above) — convergence should treat it as in-scope, evidenced
  work product regardless of its absence from the tracker's own denominator.

This packet is a link set to primary evidence (EDIR_V3_REGISTER §4b, 9 merged PRs,
`S4_LATENCY_WATERFALL_v1_0.md`, `.s4_scratch/*` investigation reports). It is not
tracker-level acceptance until the §7 gaps are resolved by the Programme Integrator.
CONVERGENCE-READY per the resume task's own framing: every remediation this stream
could honestly drive to a real, independently-verified, merged fix has been; every
remaining gap is either a genuine cross-territory referral, a deliberately-deferred
larger fix, or a tracker-mechanics limitation outside this stream's authority to
resolve — staged for convergence, not closed by S4 itself.

*End S4_RESULT_PACKET v1.1.*
