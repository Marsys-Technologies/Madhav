---
artifact: PARIPRASHNA_EDIR_V3_REGISTER
version: 1.1
status: LIVING — opened by Session A phase A3-ABSORB. Append-only; an entry
  closes only at its named verification rung with dated evidence; a RETRACTED
  entry keeps its full history; severity is assigned at triage by the Native
  Surrogate, not by the finder. This register never self-certifies a gate.
date: 2026-08-28
authoritative_side: claude
role: >
  The v3 campaign's single accumulation point for divergences, and the carrier
  of the §6 prior-work absorption census. §0 imports the historical EDIR BY
  REFERENCE ONLY (ids, titles, classes, proposed severities, status at
  self-pause) — the full bodies stay on the quarantined swarm branch and are
  never restated here as if proven on current main. §3 is the branch census:
  every unmerged pariprashna branch, exactly one disposition each, with the
  evidence that disposition rests on. §4 holds this register's own V3 entries.
governs:
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/AUTONOMOUS_EXECUTION_ELEVATION_v1_0.md §6
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_1.md §6.2, §6.3
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/P2_BLOCKER_INTAKE_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/P1_CONTRADICTION_AND_NONRELIANCE_REGISTER_v1_0.md
baseline:
  origin_main_sha: cc6b1a55e85b21c4a3865b335061d5d9dc510474
  census_taken: 2026-08-28
  branches_censused: 81
changelog:
  - "1.0 (2026-08-28): opened by Session A phase A3-ABSORB. §0 reference-import
    of 115 historical EDIR entries; §3 census of all 81 unmerged
    origin/pariprashna/* and origin/codex/pariprashna-* branches with one
    disposition each; §4 seeded with five V3 entries surfaced by the census
    itself."
  - "1.1 (2026-08-28, S4 stream): appended 44 V3-E-nnn entries (V3-E-012..
    V3-E-055) from the S4 Pipeline Correctness & Door Parity stream's full
    11-stage + 6-synergy-test + J10 investigation (17 parallel agents, several
    reaching LIVE rung against the synthetic chart). New §4b section; §4's
    original five A3-census entries plus A4's six B-001/B-007/B-008-chain
    entries (V3-E-001..V3-E-011) are unchanged. Dedup discipline applied per
    the elevation's register law: 12 historical findings (E-003, E-004, E-005,
    E-006, E-039, E-048, E-050, E-104, E-105, E-112, GAP-6, GAP-8/PPR-16) each
    got exactly one fresh V3 entry citing all reproducing sources, not one
    entry per agent; the 18-diverging-receipt-fields cross-door finding was
    filed as 2 entries (systemic root cause + the one specific worst
    sub-finding) rather than 18. Footer entry count updated 11→55."
---

# Paripraśna EDIR V3 — Experience Defect & Improvement Register (v3 campaign)

## Register law (test plan v2.1 §6.3, verbatim in force)

An entry closes **only** when its fix is DEMONSTRATED at the entry's named
verification rung (§N.8 — merged is not fixed). No entry may be edited to
soften its observed text; corrections append. A RETRACTED entry keeps its full
history. Severity is assigned **at triage** by the Native Surrogate, not by the
finder — finder-proposed severities are marked `(proposed)`. **The register
never self-certifies a gate.**

## Entry schema (test plan v2.1 §6.3)

`V3-E-nnn · title · class (DEFECT / IMPROVEMENT / BASELINE / DOC / PROCESS) ·
severity (S1 blocking / S2 major / S3 minor / S4 polish) · lens(es) · pipeline
stage (S1–S11 or SURFACE/CROSS) · journey · expected (with the requirement or
doctrine it traces to) · observed (dated, evidenced) · code anchor (file:line) ·
PPR / gap-register cross-reference · proposed fix class · status (OPEN →
TRIAGED → FIX-PLANNED → FIXED → VERIFIED@rung → CLOSED, or PARKED / RETRACTED) ·
verification rung required to close`

A historical finding **reproduced on the current artifact** gets a fresh V3
entry carrying `provenance: E-nnn`. A historical entry is never promoted into
this register by import alone — §0 is a pointer table, not a claim.

---

## §0 — Historical EDIR: reference import (115 entries, BY REFERENCE ONLY)

**Source (quarantined, not on `origin/main`):**
`00_ARCHITECTURE/briefs/pariprashna_swarm/PARIPRASHNA_EXPERIENCE_DEFECT_AND_IMPROVEMENT_REGISTER_v1_0.md`
on the local-only branch `campaign/pariprashna-assurance-autonomous`
(worktree `/Users/Dev/Vibe-Coding/Apps/Madhav/.clone/worktrees/pariprashna-assurance`).
The path does not exist on `origin/main`; neither does the swarm harness
`00_ARCHITECTURE/autonomy_pariprashna/` that produced it (0 files on main).

**What this table is and is not.** It is the id/title/class/proposed-severity/
status-at-self-pause index, one line per entry, so a v3 worker can find an
entry without loading the historical register. It is **not** evidence that any
listed condition still holds on current main. Every status below is the status
*as recorded at the historical campaign's self-pause*, and per the elevation's
own rule historical material is a **lead, never a source**: reproduction on the
current artifact is required before any of these is acted on or cited as fact.
Bodies stay on the historical branch.

**Id-space honesty note (measured 2026-08-28):** the register carries 115
`## E-nnn` headings, all ids unique, spanning E-001..E-122 with gaps at
E-014, E-055..E-059 and E-121 — the residue of the documented concurrent-id
race (E-017/E-022) and its renumberings. The separate allocator ledger
`autonomy_pariprashna/state/EDIR_ID_CLAIMS.jsonl` holds 85 rows, fewer than the
115 headed entries; `P1_CONTRADICTION_AND_NONRELIANCE_REGISTER_v1_0.md`
P1-U-002 already records this tension and rules the claims ledger
allocation/audit-only. Nothing here resolves it.

| Historical id | Title | Class | Severity (proposed, historical) | Status at self-pause |
| --- | --- | --- | --- | --- |
| E-001 | Audit log mutable by the serving credential | DEFECT | S1 (proposed) — blocking for G1 | OPEN · close rung: LIVE (psql denial proof on production) |
| E-002 | C1 sacred-personal tables have no RLS policy objects at all | DEFECT | S1 (proposed) — blocking for G1 | OPEN · close rung: LIVE (cross-context SELECT denial on |
| E-003 | MCP-door progress goes stale for the majority of a turn | DEFECT | S2 (proposed) | OPEN · close rung: LIVE (poll-series transcript on deployed |
| E-004 | Evidence truncation flagged in the envelope, undisclosed in prose | DEFECT | S2 (proposed) | OPEN · close rung: INTEGRATION (seeded truncation fixture) + |
| E-005 | Citation density: many load-bearing claims, two citations | IMPROVEMENT | S3 (proposed) — pending adjudication | OPEN (needs adjudication) · close rung: INTEGRATION (density |
| E-006 | Turn latency waterfall: >95% of wall time outside tool dispatch | BASELINE (with an IMPROVEMENT flag) | S3 (proposed) | OPEN as baseline · close: absorbed into the G5 SLO baseline |
| E-007 | Verification Matrix PPR-19 evidence cell is stale | DOC | S3 (proposed) | OPEN · close rung: STATIC (doc edit through governed session) |
| E-008 | PPR-03 and PPR-05 suites pass but are unrecorded | DOC | S4 (proposed) | OPEN · close rung: STATIC |
| E-009 | PPR-17 evidence cell mislabels its own rung | DOC | S4 (proposed) | OPEN · close rung: STATIC |
| E-010 | Live probe used the native's real chart without specific need | PROCESS | S3 (proposed) | CLOSED-AS-CODIFIED (2026-08-24, plan v2.0 test-data law) — |
| E-011 | MCP-door TTFT is unmeasurable by a consumer; no streaming signal | IMPROVEMENT | S4 (proposed) — candidate for merge | OPEN (needs native ruling: intended asymmetry or gap) |
| E-012 | GET /api/charts/[id] had no per-chart authorization (any authenticated user could read any chart's PII) | DEFECT | S1 (native-triaged: PARKED, not declined-as-invalid) | PARKED (native disposition, 2026-08-24) — fix exists and is verified; |
| E-015 | RLS is structurally inert for the serving credential: it owns every table and FORCE is set nowhere | DEFECT | S1 (proposed) — blocking for G1; supersedes | OPEN — **FINDING CONFIRMED** (ADHIKĀRIN-PP D-PP-034, |
| E-016 | `chart_divisionals` RLS was enabled by a migration whose policy silently never applied | DEFECT | S2 (proposed) | OPEN — **SPLIT, countersigned (ADHIKĀRIN-PP D-PP-034: "must |
| E-017 | EDIR entry-id allocation has no reservation mechanism; two agents minted E-013 concurrently | PROCESS | S3 (proposed) | OPEN · close rung: STATIC (reservation mechanism + its |
| E-013 | Campaign branch is 27 commits behind the deployed artifact (L-CODE lens would read the wrong code) | PROCESS | S2 (proposed) — blocking for the L-CODE lens | OPEN · close rung: STATIC (branch/commit equality proof, or a |
| E-018 | All three DOC-class evidence-cell entries (E-007/E-008/E-009) carry evidence errors of their own | DOC | S3 (proposed) — raises the severity of the | OPEN · close rung: STATIC (all three corrections landed and |
| E-033 | The `mcp__postgres__query` door silently returns naive timestamps 5h30m early | PROCESS | S3 (proposed) — a **test-instrument** defect, | OPEN · close rung: STATIC (side-by-side query returns equal |
| E-019 | `amjis_app` OWNS the audit tables and inherits `cloudsqlsuperuser`: E-001's proposed REVOKE fix is self-reversible by the credential it is meant to constrain | DEFECT | S1 (proposed) — blocking for G1; re-scopes | OPEN · close rung: LIVE (denial proof from the serving identity) |
| E-020 | `charts.chart_service_policy` is fail-open on an unset GUC, and the GUC is set by nothing: confirmed in production | DEFECT | S2 (proposed) — escalates to S1 the moment the | OPEN · close rung: LIVE (zero-row cross-context SELECT on |
| E-021 | `pariprashna_persistence_outbox`'s policy set does not match the `pariprashna_ledger_outbox` precedent its own migration and module claim it matches "exactly" | DEFECT | S3 (proposed) — latent; sits behind the E-015 | OPEN · close rung: STATIC (source/DB policy-shape equality, or a |
| E-022 | Two different entries in this register are both numbered E-013 | PROCESS | S3 (proposed) — non-blocking for testing, | OPEN · close rung: STATIC (unique-id proof + a linter that fails |
| E-026 | A fired hard stop produces NO AcharyaReadingReceipt at all; PPR-12's "record its decision on the receipt" holds only for turns that produce a reading | DEFECT | S2 (proposed) — severity is triage's, not the | OPEN · close rung: INTEGRATION (a withheld turn on either door |
| E-034 | The `reframe` action, and both reader-facing HS-1/HS-4 notices, are unreachable in the running system | DEFECT | S2 (proposed) — §N.8: a declared control with no | OPEN · close rung: STATIC + REPLAY (a demonstrated reachable |
| E-035 | The Portal door's `runSafetyPolicyGate` has zero test coverage; the other two doors each have a behavioural before-the-planner test | DEFECT | S3 (proposed) — demonstrated-can-fail asymmetry | OPEN · close rung: INTEGRATION (the new test exists and is shown to |
| E-036 | HS-5 (retraction) has no production caller anywhere: it is a library, not a reachable governance act | DEFECT | S3 (proposed) | OPEN · close rung: INTEGRATION (a retraction initiated through a |
| E-023 | HS-6's predictive sampling is wired on one door only, and its sample rows are not receipt-linked | DEFECT | S3 (proposed) | OPEN · close rung: INTEGRATION (a sampled row on each door, joined |
| E-024 | Deployed revision arms the safety gate but not subject consent: the exact "flip the pair together" state the code warns against | IMPROVEMENT | S3 (proposed) — fails CLOSED, not open | OPEN · close rung: LIVE (a real HS-3 turn on the native's own chart |
| E-025 | HS-1/HS-4 detector misses three plain-English lifespan asks in a 9-phrasing probe | DEFECT | S3 (proposed) — a probe, explicitly NOT a corpus | OPEN · close rung: REPLAY (the corpus carries these cases and the |
| E-027 | S2 entitlement has no argument-level detector: a mutation that authorizes an attacker uid, at super_admin, against a different chart passes 2,099 tests | DEFECT | S2 (proposed) — test-coverage gap, not a live | OPEN · close rung: INTEGRATION (the recorded M2 mutation re-run and |
| E-028 | The plan's own S2 anchor `CHART_REQUIRED` (invoke_tool.ts:80) is on a chokepoint with zero production callers and a test suite excluded from the test run | DEFECT | S3 (proposed) — no runtime exposure (the code | OPEN · close rung: STATIC (a caller-count proof plus a running |
| E-029 | Portal door reveals whether a chart exists BEFORE authorizing, contradicting `authorizeChartAccess`'s own rule 4 and diverging from the MCP door | DEFECT | S3 (proposed) — information disclosure over | OPEN · close rung: REPLAY (regenerated baselines showing one |
| E-030 | No pipeline stage boundary is schema-validated at runtime; "a malformed object never crosses" rests entirely on TypeScript | DEFECT | S3 (proposed) — architecture claim without a | OPEN · close rung: INTEGRATION (malformed-object injection at each |
| E-031 | The mechanism that stops question text from naming another chart is flag-gated OFF by code default | DEFECT | S2 (proposed) — with an explicit unresolved | OPEN · close rung: LIVE (deployed flag values read, then the |
| E-032 | Two different resolvers answer "does this tool need chart authorization?" and "does this tool exist"; nothing detects them diverging | IMPROVEMENT | S3 (proposed) — latent, not live: measured | OPEN · close rung: STATIC (shared-resolver proof + a |
| E-048 | The MCP door (`prashna_ask`) runs NO stage-S9 grounding validation at all: neither the citation gate nor the register-leak lint touches its reading | DEFECT | S2 (proposed) | OPEN · close rung: LIVE (a deployed-route probe showing either the |
| E-049 | The Portal citation gate reads POST-scrub prose, so its citation count is structurally always 0 and its PASS is unearned | DEFECT | S2 (proposed) | OPEN · close rung: INTEGRATION (real validator on the real route, |
| E-050 | Citation DENSITY is measured nowhere: the per-class threshold table has zero production callers, and the live gate only asks "is there at least one?" | DEFECT | S3 (proposed) — filed as the first adjudication | OPEN · close rung: INTEGRATION |
| E-037 | `citation_gate` grade and its warn/error flags are emitted to the wire and then discarded by the live client: no reader-visible, and no state-visible, effect | DEFECT | S3 (proposed) | OPEN · close rung: INTEGRATION (adapter/reducer test proving the |
| E-038 | S8→S9 and S9→S11 cross no runtime schema validation, and the plan's S9→S10 edge does not exist in the code (S10 runs INSIDE S8, before S9) | DEFECT (boundary) + DOC (stage map) | S3 (proposed) | OPEN · close rung: INTEGRATION (malformed injection refused at the |
| E-039 | Register-leak lint: measured coverage boundary (four evasion classes pass clean) and one reader-visible mangling of a near-variant id | IMPROVEMENT | S3 (proposed) | OPEN · close rung: LIVE (deployed-route seeded-leak proof) for the |
| E-051 | PROCESS: the conductor destroyed four inbox messages, one unread, by exercising a destructive command as a "smoke test" | PROCESS | S2 (proposed) — no production system affected; | OPEN · close rung: STATIC (a detector that makes an unread |
| E-040 | `provenance.ranking_config.mode` is an unconditional string literal: the receipt can never report which ranking path actually ran | DEFECT | S3 (proposed) — severity is triage's, not the | OPEN · close rung: STATIC (a demonstrated-can-fail test showing the |
| E-041 | The throwing receipt validator `assertValidAcharyaReadingReceipt` has zero production callers, and `validate.ts`'s own docblock says the persistence call site uses it | DEFECT | S3 (proposed) — severity is triage's, not the | OPEN · close rung: STATIC (docblock↔code agreement) + INTEGRATION |
| E-042 | The receipt's §N.8 validator has no coherence check over four of its fields: forged `prose_binding`, forged `provenance`, and an unresolvable `derivation_chains` ref all validate clean | DEFECT | S3 (proposed) — severity is triage's, not the | OPEN · close rung: STATIC (a demonstrated-can-fail test in which |
| E-043 | The only receipt↔prose agreement code in the tree (`pariprashna/corpus`) has no production or CI caller: agreement is asserted by construction, never checked on a real turn | DEFECT | S2 (proposed) — severity is triage's, not the | OPEN · close rung: INTEGRATION (a CI run in which a deliberately |
| E-044 | `confidence_typing.precision_flags[].overstated` can never read false, and the receipt drops the placeholder disclosure its sibling activation gate carries | IMPROVEMENT | S4 (proposed) — severity is triage's, not | OPEN · close rung: STATIC (schema parity + a test asserting a |
| E-045 | `confidence_typing.entries[].confidence_type` is a per-claim assertion computed from a turn-scoped detector: one classical-text call types every non-L1 citation `classical_prior` | IMPROVEMENT | S3 (proposed) — severity is triage's, not | OPEN · close rung: STATIC (per-claim attribution proven by a test |
| E-046 | The MCP door emits no `AcharyaReadingReceipt` on any turn, and the receipt schema cannot express a non-web channel | DEFECT | S3 (proposed) — severity is triage's, not the | OPEN · close rung: STATIC (a receipt object obtainable from both |
| E-047 | A concurrent campaign agent's broad `git add` swept another worker's temporary scratch file into the campaign branch | PROCESS | S3 (proposed) — severity is triage's, not the | OPEN · close rung: PROCESS (the rule recorded in `_common.md` and |
| E-053 | The migration-content-integrity guard has no verifiable baseline for 17 of 451 applied migrations, and its disclosure asserts a cause its own detector cannot distinguish | DEFECT | S3 (proposed) — governance/build substrate, not | OPEN · close rung: STATIC (code + allowlist change) + LIVE (tracker |
| E-052 | The plan's own S2 anchor map cites dead code | DOC | S3 (proposed) — a defect in `PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_0.md` | OPEN · close rung: STATIC (plan §4.1 corrected, or the anchor re-pointed) |
| E-054 | The plan's own S2 anchor map cites dead code with an excluded test | DOC | S3 (proposed) — a defect in | OPEN · close rung: STATIC (plan §4.1 corrected, or the anchor |
| E-065 | The `citation_gate` outcome reaches NO durable store on any door: its one intended DB writer is a documented no-op and its table was dropped, so no persisted turn can be asked what the gate said | DEFECT | S3 (proposed) — extends E-037 (client-side | OPEN · close rung: INTEGRATION (a test proving the gate outcome |
| E-060 | HS-1/HS-4 widened mortality sweep: 22 of 56 mortality-shaped phrasings reach the planner, E-025's three reproduce, and the harness is now committed | DEFECT | S3 (proposed) — a 62-phrasing hand-written | OPEN · close rung: REPLAY (the corpus carries the cases, the |
| E-061 | The classifier's own normalizer deletes digits before any pattern runs, so a numeral-bounded lifespan ask is structurally unmatchable — and E-025's proposed fix class cannot work as written | DEFECT | S3 (proposed) — root cause for one whole | OPEN · close rung: REPLAY (a numeral-bounded lifespan ask |
| E-062 | Independent reproduction of E-018: every count re-measured by real runs; two of three sub-claims survive, one is split | DOC | S3 (proposed) — this entry is the reproduction | OPEN · close rung: STATIC (Matrix cells corrected with these |
| E-063 | E-018's V-6 asserts a PPR-05 test file does not exist; it exists at the pinned commit and passes 9/9 | DOC | S3 (proposed) — a fourth-order evidence defect: an | OPEN · close rung: STATIC (E-018 corrected and PPR-05's cell |
| E-064 | The plan names its own bottom proof rung two different things (frontmatter STATIC vs §2 Unit), and §12 hardcodes the wrong PPR-17 correction | DOC | S3 (proposed) — a governing-artifact defect; it is | OPEN · close rung: STATIC (plan amended to one vocabulary, §12 |
| E-066 | CHARTER §2 P5/P9 forbid, as unenumerated, the read-only GCP call the plan's own §11.1 preflight requires | DOC (governance instrument) | S2 (proposed, advisory per CHARTER §1 G7) | OPEN · close rung: STATIC (a charter amendment landing, which requires the native) |
| E-073 | 41.3% of the registered Vidhi floor is unexecutable on the web path, and the adapter computes that fact then throws it away: `unmappedPrimitives` and `compileFailed` have ZERO production readers | DEFECT | S2 (proposed) | OPEN · close rung: INTEGRATION (a fixture asserting the count reaches the envelope) |
| E-074 | NO-LEAKAGE runs AFTER the floors and nothing re-checks the floor: one machine-band floor item is stripped on every deepdive turn, in 11 of the 14 registered intent floors | DEFECT | S2 (proposed) | OPEN · close rung: INTEGRATION (a deepdive fixture asserting floor↔post-strip |
| E-075 | Portal door: the NO-LEAKAGE strip is a count-only wire flag that never reaches the reader's prose — E-004's defect class, three stages upstream | DEFECT | S2 (proposed) | OPEN · close rung: INTEGRATION (seeded-strip fixture) + a P-PORTAL LIVE spot-check |
| E-076 | The B.11 invariant is enforced by a hand-maintained 10-entry literal, 3 of whose entries resolve to no registered capability — PPR-15's "convention, not compilation" in its literal form | DEFECT | S3 (proposed) | OPEN · close rung: STATIC (a resolvability test over `L2_5_TOOLS`) — the mirror test |
| E-077 | The two doors implement OPPOSITE policies on whether stripped capability names may cross the wire; both cite the same doctrine | DEFECT | S3 (proposed) — a PPR-30 cross-door parity divergence, filed | OPEN · close rung: STATIC (doctrine located + both doors agreeing) |
| E-078 | Budget arbitration runs BEFORE floor composition and never re-runs, so the arbiter's one asserted invariant is false of the plan S5 actually emits (measured overshoot 4100 vs 2400) | DEFECT | S3 (proposed) | OPEN · close rung: INTEGRATION (post-floor cap fixture + a floor-tool-nonzero |
| E-079 | S5's output boundary is unenforced: zero zod parses in `plan_stage.ts`, and the plan's own `ToolCallItemSchema` is never re-applied after the stage mutates it | DEFECT | S3 (proposed) | OPEN · close rung: INTEGRATION (a boundary-parse fixture that demonstrably fails on |
| E-080 | `plan_stage.ts` has no test file, and the one test claiming "end-to-end floor adoption parity (route sequence)" omits both steps that can remove a floor tool | DEFECT | S3 (proposed) — the demonstrated-can-fail gap behind E-073, | OPEN · close rung: INTEGRATION (the extended parity harness landing with fixtures |
| E-067 | S6 dispatch is parallel on the Portal door and strictly serial on the MCP door; measured parallelism efficiency 0.101 vs 1.000, and no test anywhere asserts overlap | IMPROVEMENT | S3 (proposed) — cross-door optimality | OPEN · close rung: REPLAY for the detector (an overlap assertion |
| E-068 | A tool that THREW is reported inside a `completeness.status: "complete"` envelope: the MCP door's partial-ness predicate has no detector for dispatch errors | DEFECT | S2 (proposed) — a status signal asserting more | OPEN · close rung: REPLAY (a seeded throwing-tool fixture |
| E-069 | Portal-door S6 has no unserved/unresolved list at all: an unresolved tool leaves no row in the only per-tool log, and an aborted turn drops every tool with zero events | DEFECT | S3 (proposed) | OPEN · close rung: REPLAY (a fixture proving each of the three |
| E-070 | The two doors' S6 protections are exact complements: the MCP door has cost caps but no queue, the Portal door has the queue but no cost cap of any kind | IMPROVEMENT | S3 (proposed) — cross-door parity gap with | OPEN · close rung: INTEGRATION (both doors exercised under the |
| E-071 | Two S6 protections that cannot fire: the shipped queue's `QueueSaturatedError` is unreachable, and no per-tool latency budget or timeout exists on either door | DEFECT | S3 (proposed) — a refuse path and a stated | OPEN · close rung: INTEGRATION (a saturating concurrent-load run |
| E-072 | The advertised `cap_ceiling.maxCalls` overstates the servable tool count by exactly one, and the cap that starves the reading leaves `unserved_tools` empty | DEFECT | S4 (proposed) — a reported number that is not | OPEN · close rung: REPLAY (the boundary fixture above, asserting |
| E-081 | A verifier's numeric challenge was routed to the wrong KĀRAKA-PP; two concurrent workers share one role name, and the near-miss was a fabricated SQL predicate | PROCESS | S2 (proposed) — raised above the sibling | OPEN · close rung: PROCESS (discriminator stamped at dispatch and |
| E-082 | `parts_json` and `message_parts` disagree about whether the same turns contain citation markers | DEFECT | S3 (proposed) | OPEN · close rung: LIVE (both stores agree on a marker census, or |
| E-083 | Alternatives and falsifiers (PPR-02) are generated from the reading's own sentences with ZERO evidence in the prompt, and the schema has no field that could anchor them to a fact | DEFECT | S2 (proposed) — severity is triage's, not the | OPEN · close rung: INTEGRATION (a seeded judgment whose falsifier |
| E-084 | `runSynthesisStage` — S8's entire streaming half, and the single longest function on the Portal serving path — has no test file; the one suite touching `synthesis_stage.ts` covers only its prompt-assembly half | DEFECT (coverage) | S3 (proposed) — severity is | OPEN · close rung: INTEGRATION (the suite exists and each |
| E-085 | BASELINE: S8's model-call inventory, per door — and a conditional, blocking, entirely undisclosed LLM summarization call inside the Portal door's prompt assembly | BASELINE (with a DEFECT flag for item 3) | S3 | OPEN as baseline · close: absorbed into the G5 SLO baseline |
| E-086 | A demand-driven role has no self-invocation; an inbound message is its only wake signal (and my own first diagnosis of this was wrong) | PROCESS | S3 (proposed) | OPEN · close rung: STATIC (a stated wake mechanism with a demonstrated- |
| E-087 | PROCESS: `fleet_timer.sh` emitted a delivery success signal with no delivery detector; every poke stranded in a compose box | PROCESS | S2 (proposed) — campaign operating substrate, | OPEN · close rung: LIVE (one full tick cycle logging |
| E-088 | Decomposing the pin detector silently loosened the rule that consumed its PASS, permitting a campaign-authored file to be cited as deployed code | PROCESS (campaign tooling) | S3 (proposed, advisory per CHARTER §1 G7) | OPEN · close rung: STATIC (the detector extension landing and red-proven) |
| E-089 | Conditional authorizations carried untracked obligations: no mechanism could surface an undischarged condition | PROCESS (campaign governance) | severity **not self-proposed** — see below | OPEN · close rung: STATIC (the teeth clause exercised at a real gate advance) |
| E-090 | `fleet_timer.sh` never schedules LEKHAKA-PP, and cannot report that it doesn't | DEFECT | S2 (proposed) — in the campaign's own operating | OPEN · close rung: STATIC (dry-run names an unresolvable window) + LIVE |
| E-091 | `bundle_hydrator` drops a planner-selected asset it cannot load and the returned bundle carries no field that says so: the loss reaches the model as silence, and the bundle_hash makes it invisible | DEFECT | S3 (proposed) — severity is triage's, not the | OPEN · close rung: REPLAY (a fixture proving each of the three skip |
| E-092 | S7's stated contract cannot be checked on the Portal door because the "EvidenceBundle" and the dispatch results are disjoint objects: retrieval pass 1's results never enter the synthesis prompt at all | DEFECT | S2 (proposed) — severity is triage's, not the | OPEN · close rung: INTEGRATION (a live turn whose prompt capture |
| E-093 | `gap_ribbon` is a bare substring match over a whole block: one honest-gap sentence promotes an entire substantive reading paragraph into an "The chart is silent here" ribbon | DEFECT | S2 (proposed) — severity is triage's, not the | OPEN · close rung: REPLAY (a fixture in which a mixed block keeps |
| E-094 | `verse` and `heading` can only be recognised when they are the WHOLE block, and a block is only cut at a prose/thinking switch: a verse or heading inside a reading downgrades to a bare `paragraph` carrying no marker of the downgrade | DEFECT | S2 (proposed) — severity is triage's, not the | OPEN · close rung: REPLAY (a fixture in which a verse embedded in |
| E-095 | Three block/role surfaces in the Paripraśna renderer have no producer anywhere: `prediction_card` and `list` block kinds, and the `verse` reading role | DEFECT | S4 (proposed) — severity is triage's, not the | OPEN · close rung: STATIC (a lint or type-level check that the |
| E-099 | The one real schema boundary on the S10 path fails SILENTLY: a `block.commit` frame rejected by zod is dropped with no counter, no log and no flag, and the reader loses a settled block with no indication | DEFECT | S2 (proposed) — severity is triage's, not the | OPEN · close rung: REPLAY (a fixture in which a rejected frame |
| E-096 | E-017's stated reason for which duplicate id moved is refuted by the ledgers: both `E-013`s were cited, and the one that moved was cited first | DOC | S3 (proposed) — the finding E-017 records is real | OPEN · close rung: STATIC (the correction bullet exists on E-017, |
| E-097 | The only detector standing over the EDIR id space is provably blind to a duplicate id; E-022's close rung is unbuilt | DEFECT | S3 (proposed) — the control that ended the | OPEN · close rung: STATIC (a duplicate-id linter that turns red |
| E-098 | The register footer's own id-collision tally does not reconcile with itself or with git | DOC | S4 (proposed) — non-blocking; a counted claim in | OPEN · close rung: STATIC (footer tally re-derived by script, or |
| E-100 | `fleet_timer.sh`'s reachability detector is nested inside the STALENESS guard: the live loop prints `tick — all reactive roles fresh` for a role whose window does not resolve, and the rung declared binding for E-090 cannot see it | DEFECT | S2 (proposed) — campaign operating substrate, no | OPEN · close rung: LIVE — the `while true` loop (not `--dry-run`) emits a |
| E-101 | A `fleet_timer.sh` proof run cannot be isolated by the knobs the script documents: `heartbeat.sh` honours an ambient `PARIPRASHNA_REPO`, so my red-proof wrote `ROLE UNREACHABLE` into the LIVE record | DEFECT | S3 (proposed) — campaign operating substrate | OPEN · close rung: STATIC + LIVE (a scratch instance provably writes nowhere |
| E-102 | Three residual detector defects in `fleet_timer.sh`, found while certifying E-090: an "idle" guard that detects no idleness and skips silently, a dead dry-run branch left in the file, and an `elif` that discards the `NO-EFFECT` report | DEFECT | S3 (proposed) — campaign operating substrate | OPEN · close rung: STATIC for (b) and (c); (a)'s comment/behaviour mismatch is |
| E-103 | S1's intent/scope classifier reads the LITERAL query surface, so E-061's digit-destroying fold does NOT reach it — and the injection wrapper it is actually handed in production changes nothing either | DOC | S4 (proposed) — a NEGATIVE result, filed because it | OPEN · close rung: this entry has nothing to fix; it closes when a |
| E-104 | `fallback_recommended`'s second disjunct (`confidence < 0.5`) is structurally unreachable: the classifier's only ambiguity signal is a one-bit test wearing a two-term guard's clothes | DEFECT | S3 (proposed) — §N.8 earned-signal class. No | OPEN · close rung: STATIC (the guard either becomes reachable or is |
| E-105 | Clarification FALSE POSITIVES: "Will I get married?", "Where is my Moon?" and "Am I going to be rich?" are each sent back as a clarification instead of answered — the rule tables miss the ordinary wording of three of the commonest asks | DEFECT | S2 (proposed) — reader-visible. The turn ends with | OPEN · close rung: REPLAY (a versioned corpus exists, both directions |
| E-106 | Clarification FALSE NEGATIVES: an out-of-domain or adversarial question containing one incidental keyword produces a 0.8-confidence tuple and a full planned chart reading — S1 has no "not an astrological question" output at all | DEFECT | S2 (proposed) — the "mis-classify safely" | OPEN · close rung: REPLAY (an adversarial corpus exists and the named |
| E-107 | The web scope classifier's header declares itself a faithful port of the MCP source "do not diverge"; it has diverged on width, depth, entitlement and prompt-disclosure, and the two doors now disagree on the tuple for essentially every question | DEFECT | S2 (proposed) — PPR-30 cross-door parity class. | OPEN · close rung: REPLAY (a parity fixture runs both implementations |
| E-108 | The plan's S4 stage boundary does not exist as an object on the Portal door either: the ScopeTuple is built inside S5 and reaches the floor compiler without ever crossing a validated seam. The one real zod parse on this stage lives only on the MCP HTTP door | DOC | S3 (proposed) — a stage-graph correction plus a | OPEN · close rung: STATIC for the graph correction; the plan's §4.1 |
| E-109 | The ScopeTuple's depth and width DO change downstream behaviour, measured — but two of the three effective dimensions behave counter-intuitively: `intervention` is completely inert at the Portal's default depth, and asking for MORE width compiles a SMALLER floor | DEFECT | S3 (proposed) — the headline half is a NEGATIVE | OPEN · close rung: for (a) and (b), STATIC; the dispatched-tool delta |
| E-110 | GAP-8's mechanism, established: the composer's depth picker and the depth the reader is TOLD they received are computed from different inputs and cannot agree. "Deep dive" can never make `scope_tuple.depth` deep, because the Portal request has no field for it | DEFECT | S2 (proposed) — reader-visible. The disclosure | OPEN · close rung: LIVE (one Portal turn on `Deep dive` shows the chip |
| E-111 | The composer's depth picker has three options and two values: "Quick" and "Auto" are the same byte on the wire, so one third of the control is genuinely cosmetic | DEFECT | S3 (proposed) — reader-visible, small, and exactly | OPEN · close rung: STATIC (either a third protocol value exists and |
| E-112 | The Portal door still runs the keyword depth gate that a binding native ruling RETIRED: `scope_resolver.ts` calls deepdive-by-default "LAW", and the web classifier the Portal actually uses defaults to `standard` — costing the entire 15-item machine band on an ordinary question | DEFECT | S2 (proposed) — a live doctrine violation on the | OPEN · close rung: REPLAY (both doors resolve the same depth for the |
| E-113 | `cr_status.ts` is a FOURTH hand-synced copy of the vidhi registry across the process boundary, is the only one that has actually drifted, and is on `buildVidhiPlan`'s runtime path: mutating it changed nothing across 199 test files / 2210 tests | DEFECT | S3 (proposed) | OPEN · close rung: STATIC (a parity assertion over the three CR arrays that |
| E-114 | A THIRD planner door exists (`plan_retrieval` / `vidhi_plan`) with no NO-LEAKAGE machinery anywhere in its deployable, and it hands the caller `mechanism_retrodiction_get` as a non-skippable floor item in 11 of 14 intent floors — the same capability the other two doors strip | DEFECT | S2 (proposed) — a PPR-30 cross-door parity divergence, | OPEN · close rung: STATIC (doctrine located + a three-door agreement fixture) |
| E-115 | The B.11 whole-chart-read guard does not exist on the `plan_retrieval` door at all; 2 of 14 compiled floors already carry zero L2.5 capability, and nothing detects it | DEFECT | S3 (proposed) | OPEN · close rung: STATIC (a per-floor L2.5-intersection test with named exemptions) |
| E-116 | `buildVidhiPlan`'s output boundary is unenforced: zero zod parses across all 11 production modules in its chain, while its INPUT is fully zod-validated — the §4.3.1 finding reproduces on the third door, with the asymmetry inverted from `plan_stage.ts` | DEFECT | S3 (proposed) | OPEN · close rung: INTEGRATION (a boundary-parse fixture that demonstrably fails on |
| E-117 | The MCP door's synthesis LLM call writes no row to the cost ledger the daily spend ceiling reads: `channel='mcp'` has ZERO rows in `llm_usage_events`, all-time | DEFECT | S2 (proposed) | OPEN · close rung: LIVE (a deployed MCP turn producing a `channel='mcp'` synthesize row, verified by query) |
| E-118 | An MCP turn has three identities and no join key: the only id the caller ever sees exists in memory alone, and neither persisted id is reachable from it | DEFECT | S2 (proposed) | OPEN · close rung: LIVE (a `job_id` → DB row lookup succeeding on a deployed turn) |
| E-119 | No MCP turn leaves any durable record of what it said: no envelope, no reading, no judgment flags, no receipt — and the one replay substrate that exists holds 0 rows all-time | DEFECT | S2 (proposed) | OPEN · close rung: LIVE (a deployed MCP turn either producing the record or carrying the honest-absence disclosure) |
| E-120 | `JobRegistry.get()`'s docblock says its callers MUST check `chartId`; its only production caller cannot, and argues instead of resolving | DEFECT | S3 (proposed) | OPEN · close rung: STATIC for the docblock/decision alignment; INTEGRATION if the entitlement comparison is implemented |
| E-122 | `verify_heartbeat_provenance.sh` reports 13 genuine live-timer rows as harness contamination | DEFECT | S3 (proposed) — a **false-RED** in a control, i.e. the | OPEN · close rung: STATIC (detector reclassifies the 13 while still flagging |

---

## §1 — Branch census: method and honesty statement

**Baseline.** `origin/main` @ `cc6b1a55e85b21c4a3865b335061d5d9dc510474`
(PR #1595), fetched and measured 2026-08-28. 81 unmerged branches matched
`origin/pariprashna/*` or `origin/codex/pariprashna-*`. **Every one of the 81
carries exactly one disposition below — none is silently ignored.**

**Method, stated so it can be falsified.** For each branch:

1. `git diff --name-only origin/main...origin/<b>` — the set of files the
   branch actually changed relative to its merge base (its *own* work).
2. `git diff --numstat origin/main..origin/<b> -- <that set>` — how those same
   files differ from **current** main. Files absent from this second result are
   **byte-identical to main**: the branch's work on them has landed.
3. Insertion/deletion polarity on (2) is the discriminator. Read
   `origin/main → branch`: **deletions** are lines main has that the branch
   lacks (main is ahead); **insertions** are lines the branch has that main
   lacks (genuine unmerged content). A branch whose residue is
   overwhelmingly deletions is *behind* main, not ahead of it — its intent is
   satisfied and then some.
4. For DEEP-depth branches, the commit messages and the specific superseding
   artifact on main were read as well.

**Depth grades, stated honestly.** `DEEP` = mechanical evidence *plus* commit
bodies and/or the specific superseding file on main verified by hand (36
branches). `MECH` = the mechanical evidence in (1)–(3) plus the head commit
subject (44 branches) — objective and reproducible, but the commit bodies were
not read. `PRELIM` = disposition is a best judgment that a named question was
**not** settled in this pass (1 branch: `codex/pariprashna-shadow-deploy`; see
V3-E-004). No branch was dispositioned without running (1)–(3) against it.

**What this census does NOT claim.** It does not claim any branch's tests pass
on current main; it does not certify any gate; and a SUPERSEDED grade means
*the branch's content is present on main or main is strictly ahead on the files
it touched* — not that the underlying defect the branch addressed is proven
fixed in production. That proof is A4/stream work, at the rung the item names.

**Disposition tally (81 branches):** SUPERSEDED 70 · ARCHIVE 7 ·
EVIDENCE-ONLY 2 · SALVAGE 2.

**PRs opened by this lane: none.** Neither SALVAGE branch bears on
P2-B-001..B-006 (see V3-E-001), and the elevation's PR obligation in §6.3 is
scoped to P2-relevant SALVAGE. `pariprashna/p4-g` and
`codex/pariprashna-shadow-deploy` are recorded with their commits and deferred
for review — explicitly **done: disposition + evidence; deferred: PR**.

---

## §2 — Disposition classes (elevation §6.2)

| Class | Meaning | Action taken here |
| --- | --- | --- |
| SALVAGE | Contains a fix/test/doc worth landing on current main | Recorded with commits + what is salvageable. PR deferred (non-P2). Still requires reproduction/justification against current main before it lands — existing before is not evidence. |
| SUPERSEDED | Intent already satisfied on main or by a newer branch | Superseding evidence recorded; no code action. |
| EVIDENCE-ONLY | Valuable as diagnosis/precedent | Cited from the relevant work item; no merge. |
| ARCHIVE | Closed-history or abandoned | Reason recorded. **Branch NOT deleted** — deletion is Session C's act, and only after these dispositions are accepted. |

---

## §3 — The census


### A · P2-family (priority 1 — elevation §6.3)

| Branch | Disposition | Depth | Commits ahead | Residue vs main | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `pariprashna/citation-leak-fix` | **SUPERSEDED** | DEEP | 1 | +1/-36 in 2/4 files | register_leak_lint list-collapse fix + its 17 tests byte-identical to main | main additionally carries the PARIPRASHNA_CITATION_APPENDIX splice in synthesis_stage.ts that this branch predates |
| `pariprashna/hs4-fix` | **SUPERSEDED** | DEEP | 1 | +8/-22 in 1/3 files | HS-4 anniversary carve-out landed: phrasing_scan.ts + classifier.ts byte-identical to main | only earned_signal_allowlist.json differs, and main's copy is the newer one (max_occurrences 5->6 from citation-leak-fix + a nirmana entry the branch predates) |
| `pariprashna/p2` | **SUPERSEDED** | DEEP | 29 | +42/-1062 in 17/112 files | 29 commits; all 8 P2 lanes present on main in later form | main strictly ahead on all 17 still-differing files |
| `pariprashna/p2-close-fixes` | **SUPERSEDED** | DEEP | 1 | +34/-120 in 2/3 files | DD-20 schema validation in interpretation/worker.ts present on main in a later form | main +120 lines over branch in worker.ts |
| `pariprashna/p2-close-item5-dock-collapse` | **SUPERSEDED** | DEEP | 2 | +0/-14 in 1/5 files | RightDock mobile-hide + vitest e2e exclusion on main | branch adds nothing main lacks (+0/-14) |
| `pariprashna/p2-close-item6-observability` | **SUPERSEDED** | DEEP | 1 | 0 (all 1 files byte-identical) | observability identity wiring in route.ts on main | every touched file byte-identical to main |
| `pariprashna/p2-close-item7-voice-anchor` | **SUPERSEDED** | DEEP | 1 | 0 (all 2 files byte-identical) | voice_lint bare-imperative anchor fix on main | every touched file byte-identical to main |
| `pariprashna/p2-close-lane-k-typed-confidence` | **SUPERSEDED** | DEEP | 1 | +1/-11 in 1/3 files | GroundingCard typed confidence on main | branch adds 1 line main lacks; main +11 |
| `pariprashna/p2-epistemic` | **SUPERSEDED** | DEEP | 18 | +55/-712 in 10/74 files | G3-A..G3-F (receipt, interpretation_sets, typed confidence, voice, corpus) all on main | 64 of 74 touched files byte-identical to main |
| `pariprashna/p2-final` | **SUPERSEDED** | DEEP | 4 | +14/-80 in 3/15 files | G3-E/G3-G reader affordances + model qualification present on main | corpus/qualification/* byte-identical to main; only 3 UI files lag |

### A · g1-* (priority 1)

| Branch | Disposition | Depth | Commits ahead | Residue vs main | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `pariprashna/g1-a-hardened` | **SUPERSEDED** | DEEP | 10 | +564/-2593 in 18/91 files | migration renumbered 576->577 on main; contents byte-identical but for the header number (4-line diff) | safety classifier/phrasing_scan on main are later revisions |
| `pariprashna/g1-a-safety-gate` | **SUPERSEDED** | DEEP | 5 | +575/-4064 in 20/79 files | same 576->577 migration; superseded by g1-a-hardened then by main | main +4064 lines over branch across the safety surface |
| `pariprashna/g1-g-injection-containment` | **SUPERSEDED** | DEEP | 26 | +126/-1926 in 16/128 files | injection containment + g1c RLS arm/disarm scripts + arm3 roles_rls test all present on main | 112 of 128 touched files byte-identical to main |

### A · named EVIDENCE-ONLY (priority 1)

| Branch | Disposition | Depth | Commits ahead | Residue vs main | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `pariprashna/dd-credential-misdiagnosis` | **EVIDENCE-ONLY** | DEEP | 1 | +6/-36 in 2/2 files | DD-46 (a credential-repair diagnosis that named the wrong system twice) — elevation §6.2 names this branch EVIDENCE-ONLY for P2-B-004/B-005 | its DD-46 text is already merged on main, so there is nothing to merge; its value is the diagnosis-discipline rule it establishes |

### B · tracker-v2* (priority 2)

| Branch | Disposition | Depth | Commits ahead | Residue vs main | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `pariprashna/tracker-p2-p3-preflight-sync` | **SUPERSEDED** | MECH | 1 | 0 (all 1 files byte-identical) | every touched file byte-identical to main | fully landed |
| `pariprashna/tracker-v2` | **SUPERSEDED** | DEEP | 2 | +238/-4090 in 16/18 files | targets briefs/pariprashna_swarm/tracker/* — main carries a strictly later revision of every touched file | +238/-4090 vs main; the v3 campaign's live tracker is the separate event-sourced control plane |
| `pariprashna/tracker-v2-derive-reality` | **SUPERSEDED** | MECH | 1 | +13/-399 in 5/6 files | same swarm-tracker surface; main ahead | +13/-399 |
| `pariprashna/tracker-v2-durable-evidence` | **SUPERSEDED** | MECH | 1 | 0 (all 7 files byte-identical) | every touched file byte-identical to main | fully landed |
| `pariprashna/tracker-v2-harden-install` | **SUPERSEDED** | MECH | 1 | +107/-1527 in 8/8 files | same swarm-tracker surface; main ahead | +107/-1527 |
| `pariprashna/tracker-v2-launchd-path-fix` | **SUPERSEDED** | MECH | 1 | +8/-199 in 3/3 files | same swarm-tracker surface; main ahead | +8/-199 |
| `pariprashna/tracker-v2-mirror-refs` | **SUPERSEDED** | MECH | 1 | +69/-2086 in 7/7 files | same swarm-tracker surface; main ahead | +69/-2086 |
| `pariprashna/tracker-v2-pidfile-race` | **SUPERSEDED** | MECH | 1 | +3/-324 in 3/3 files | same swarm-tracker surface; main ahead | +3/-324 |
| `pariprashna/tracker-v2-rate-bucket-ref-proof` | **SUPERSEDED** | MECH | 7 | +75/-1312 in 10/21 files | same swarm-tracker surface; main ahead | +75/-1312 |
| `pariprashna/tracker-v2-url-and-supervision` | **SUPERSEDED** | MECH | 1 | +10/-186 in 4/6 files | same swarm-tracker surface; main ahead | +10/-186 |

### C · p3-preflight-* / p3-* (priority 3)

| Branch | Disposition | Depth | Commits ahead | Residue vs main | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `pariprashna/p3-a` | **SUPERSEDED** | MECH | 3 | 0 (all 3 files byte-identical) | every touched file byte-identical to main | fully landed |
| `pariprashna/p3-c` | **SUPERSEDED** | MECH | 3 | 0 (all 29 files byte-identical) | all 29 touched files byte-identical to main | fully landed |
| `pariprashna/p3-d-prep` | **SUPERSEDED** | MECH | 4 | 0 (all 2 files byte-identical) | every touched file byte-identical to main | fully landed |
| `pariprashna/p3-e` | **SUPERSEDED** | MECH | 7 | +0/-50 in 1/3 files | post-deploy smoke workflow on main is 50 lines longer than the branch's | +0/-50 |
| `pariprashna/p3-preflight-part-a` | **SUPERSEDED** | MECH | 1 | +7/-15 in 2/2 files | adapter_gemini responseFormat/thinking_level fix on main | +7/-15 |
| `pariprashna/p3-preflight-part-c` | **SUPERSEDED** | MECH | 1 | +7/-143 in 1/9 files | DD-22 table-in-prose promotion on main | +7/-143 |
| `pariprashna/p3-preflight-part-d` | **SUPERSEDED** | MECH | 2 | +13/-138 in 2/3 files | migration renumber 575->583 landed; platform/migrations/583_llm_pricing_versions_seed.sql present on main | +13/-138 |
| `pariprashna/p3-preflight-part-e` | **SUPERSEDED** | MECH | 2 | 0 (all 4 files byte-identical) | platform/migrations/587_llm_usage_events_interpretation_sets_stage.sql present on main; all 4 touched files byte-identical | fully landed |
| `pariprashna/p3-preflight-part-f` | **SUPERSEDED** | MECH | 1 | 0 (all 2 files byte-identical) | every touched file byte-identical to main | fully landed |
| `pariprashna/p3-preflight-part-f-residual-b` | **SUPERSEDED** | MECH | 1 | +13/-138 in 2/2 files | DD-13 residual record on main | +13/-138 |
| `pariprashna/p3-preflight-part-g` | **SUPERSEDED** | MECH | 1 | +12/-136 in 2/3 files | DD-13 close / DD-27 file on main | +12/-136 |
| `pariprashna/p3-preflight-part-h` | **SUPERSEDED** | MECH | 1 | +6/-130 in 2/3 files | DD register accuracy pass on main | +6/-130 |
| `pariprashna/p3-preflight-part-h-close` | **SUPERSEDED** | MECH | 1 | +1/-238 in 2/2 files | Part H governance-registry write on main | +1/-238 |
| `pariprashna/p3f-rollback-pin` | **SUPERSEDED** | MECH | 2 | +3/-17 in 1/1 files | P3F_FLIP_ROLLBACK_PIN doc on main is later | +3/-17 |
| `pariprashna/p3p4-charter` | **SUPERSEDED** | MECH | 1 | +2/-1886 in 2/8 files | overnight charter/ledger/report on main are later revisions | +2/-1886 |

### C · p4-* (priority 3)

| Branch | Disposition | Depth | Commits ahead | Residue vs main | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `pariprashna/p4-census` | **SUPERSEDED** | MECH | 2 | 0 (all 3 files byte-identical) | all 3 touched files byte-identical to main | fully landed |
| `pariprashna/p4-g` | **SALVAGE** | DEEP | 3 | +2384/-5 in 18/18 files | platform/src/lib/pariprashna/samiksha/window_ask/ does not exist on main (25 files under samiksha/, none of them window_ask) | +2384/-5 vs main: 12 new modules + 5 test files (199+ unit tests, 1 DB-integration). Flag-gated (window_ask/flag.ts). PR NOT opened by this lane — non-P2 per elevation §6.3; commits 7b63249bb, c8d31c9ba, 0bf74e448 |
| `pariprashna/p4-h` | **EVIDENCE-ONLY** | DEEP | 2 | +631/-105 in 4/4 files | PR #1496 REFUTED and PARKED by native-surrogate ruling: the restored dispute endpoint writes conversation_messages.metadata_json but the next ordinary turn erases it (DD-28); DD-28/29/30 already landed on main via pariprashna/dd28-30-split | its it.skip'd red detector (feedback_dispute_survives_turn.db.test.ts) becomes SALVAGE-eligible once the DD-28 writer fix lands; see V3-E-003 for the still-live main-side defect it evidences |
| `pariprashna/p4-i` | **SUPERSEDED** | MECH | 4 | 0 (all 8 files byte-identical) | migration 588_samiksha_digest_journal.sql present on main; all 8 files byte-identical | fully landed |
| `pariprashna/p4-j` | **SUPERSEDED** | MECH | 6 | 0 (all 16 files byte-identical) | all 16 touched files byte-identical to main | fully landed |
| `pariprashna/p4-k` | **SUPERSEDED** | MECH | 5 | 0 (all 20 files byte-identical) | all 20 touched files byte-identical to main | fully landed |

### D · closeout / governance / audit / dd / p0 / p1 (priority 4)

| Branch | Disposition | Depth | Commits ahead | Residue vs main | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `pariprashna/audit-fixes` | **SUPERSEDED** | DEEP | 3 | +1/-385 in 2/3 files | CI wiring of the P3-C DB persistence detector present on main | +1/-336 in ci.yml |
| `pariprashna/audit-ledger` | **SUPERSEDED** | DEEP | 1 | +2/-8 in 1/1 files | P3_P4_COMPLETENESS_AUDIT on main is later | +2/-8 |
| `pariprashna/closeout-dd11-amend` | **SUPERSEDED** | DEEP | 1 | +15/-311 in 3/3 files | DD-11 amendment present on main | +15/-311 |
| `pariprashna/closeout-final-2026-08-20` | **SUPERSEDED** | DEEP | 1 | +16/-196 in 2/3 files | DD-12 + close-out record present on main | +16/-196 |
| `pariprashna/closeout-record` | **SUPERSEDED** | DEEP | 1 | +6/-249 in 1/1 files | CLOSEOUT_TRACKER_AND_COLLISION on main is 249 lines longer | +6/-249 |
| `pariprashna/dd1-battery` | **SUPERSEDED** | DEEP | 6 | 0 (all 11 files byte-identical) | all 11 files byte-identical to main (platform/scripts/pariprashna/dd1_battery/*) | fully landed |
| `pariprashna/dd16-dd17-closeout` | **SUPERSEDED** | DEEP | 1 | +62/-459 in 4/6 files | migration 578_pariprashna_persistence_outbox.sql present on main; DD-16/17/19 text on main | +62/-459 |
| `pariprashna/dd17-supersede-diagnostic` | **SUPERSEDED** | DEEP | 1 | +19/-173 in 2/2 files | DD-17 supersession + DD-20 filing present on main | +19/-173 |
| `pariprashna/dd28-30-split` | **SUPERSEDED** | DEEP | 1 | +4/-36 in 2/2 files | DD-28/29/30 text present on main | +4/-32 |
| `pariprashna/governance-close` | **SUPERSEDED** | DEEP | 3 | +4/-39 in 2/2 files | DD-31..DD-44 + DD-45 text present on main | +4/-32, manifest-fingerprint bookkeeping only |
| `pariprashna/ledger-fold` | **SUPERSEDED** | DEEP | 1 | 0 (all 1 files byte-identical) | its single file is byte-identical to main | fully landed |
| `pariprashna/overnight-close` | **SUPERSEDED** | DEEP | 10 | +0/-71 in 1/4 files | OVERNIGHT_DECISION_LEDGER on main carries F-N17b/F-N18 and more | +0/-71 |
| `pariprashna/p0` | **SUPERSEDED** | DEEP | 36 | +597/-3730 in 31/65 files | every code file main-ahead; the only branch-side additions are stale SWARM_TRACKER.json / tracker_data.js state snapshots | +597/-3730; no code residue |
| `pariprashna/p0-c-ports-refactor` | **SUPERSEDED** | MECH | 4 | +124/-3927 in 31/58 files | folded into pariprashna/p0 then into main | +124/-3927 |
| `pariprashna/p1` | **SUPERSEDED** | MECH | 27 | +140/-1959 in 17/129 files | G1-A/G1-C/G1-G work present on main; 112 of 129 touched files byte-identical | +140/-1959 |
| `pariprashna/probe-harness` | **SUPERSEDED** | DEEP | 1 | +9/-35 in 2/4 files | platform/scripts/probe/ask.ts on main is a later revision (+9/-35) | the harness itself is the instrument P2-B-004 reproduction should use; it is on main, not owed |
| `pariprashna/register-closeout` | **SUPERSEDED** | DEEP | 2 | +19/-175 in 2/3 files | DD-14..DD-18 text present on main | +14/-45, manifest bookkeeping only |

### E · codex/pariprashna-* (priority 4)

| Branch | Disposition | Depth | Commits ahead | Residue vs main | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `codex/pariprashna-assurance-p0-tracker` | **ARCHIVE** | MECH | 21 | +46/-1650 in 8/21 files | P0 closed history (P0_CLOSURE_PACKET_v1_0.md); +46/-1650 vs main | do not delete before Session C |
| `codex/pariprashna-assurance-p1` | **ARCHIVE** | MECH | 7 | +40/-803 in 11/12 files | p1 family = closed history per elevation §6.1; P1_CLOSURE_PACKET_v1_0.md on main; +40/-803 | do not delete before Session C |
| `codex/pariprashna-assurance-p1-closure` | **ARCHIVE** | MECH | 2 | +4/-360 in 2/9 files | P1 closure recorded; +4/-360 | do not delete before Session C |
| `codex/pariprashna-assurance-p1-closure-docs` | **ARCHIVE** | MECH | 1 | 0 (all 7 files byte-identical) | every touched file byte-identical to main | closed history AND fully landed |
| `codex/pariprashna-assurance-p1-upgrade` | **ARCHIVE** | MECH | 4 | +10/-660 in 3/3 files | p1 family closed history; +10/-660 | do not delete before Session C |
| `codex/pariprashna-assurance-p2-enablement` | **SUPERSEDED** | DEEP | 1 | +3/-173 in 2/7 files | landed on main as PR #1593 / 8bdcb5d0c 'feat(pariprashna): enable phase-scoped P2/general-mode identities' | +3/-173 residue is bookkeeping |
| `codex/pariprashna-assurance-p2-release-upgrade` | **SUPERSEDED** | DEEP | 1 | 0 (all 2 files byte-identical) | landed on main as PR #1595 / cc6b1a55e (current origin/main HEAD); both files byte-identical | fully landed |
| `codex/pariprashna-autonomous-elevation` | **SUPERSEDED** | DEEP | 1 | +29/-79 in 1/1 files | an earlier draft of AUTONOMOUS_EXECUTION_ELEVATION_v1_0.md; main carries v1.1 (+79 lines over the branch) | +29/-79 |
| `codex/pariprashna-observed-at-idempotent-fix` | **SUPERSEDED** | MECH | 2 | +3/-115 in 2/3 files | elevation_worker.py on main is later | +3/-115 |
| `codex/pariprashna-p0b-option-b` | **ARCHIVE** | MECH | 3 | +22/-914 in 2/3 files | P0B closed (A3_OPTION_B_AUTHORIZATION_RECORD_v1_0.md, P0_CLOSURE_PACKET_v1_0.md); +22/-914 | do not delete before Session C |
| `codex/pariprashna-p1-proof-fix` | **ARCHIVE** | MECH | 2 | +6/-604 in 2/2 files | p1 family closed history; +6/-604 | do not delete before Session C |
| `codex/pariprashna-promote-test-plan-v2` | **SUPERSEDED** | DEEP | 1 | 0 (all 2 files byte-identical) | test plan v2.1 promoted and on main; both files byte-identical | fully landed |
| `codex/pariprashna-shadow-dashboard-and-payload-trim` | **SUPERSEDED** | MECH | 1 | +2/-62 in 2/5 files | elevation_worker.py on main is later | +2/-62 |
| `codex/pariprashna-shadow-deploy` | **SALVAGE** | PRELIM | 1 | +111/-239 in 2/2 files | adds tracker/elevation_service.py (83 lines, shadow-dashboard launchd spec, port 8788) which has NO counterpart file on main | PRELIMINARY — the only codex-family file with no main counterpart. Main carries elevation_operations.py + elevation_server.py which may already satisfy its intent; that equivalence was NOT established in this pass. No PR opened. See V3-E-004 |
| `codex/pariprashna-shadow-sync` | **SUPERSEDED** | MECH | 1 | +21/-293 in 2/2 files | shadow sync worker landed; elevation_worker.py on main is later | +21/-293 |
| `codex/pariprashna-tracker-closeout-gap1` | **SUPERSEDED** | MECH | 1 | 0 (all 2 files byte-identical) | both files byte-identical to main | fully landed |
| `codex/pariprashna-tracker-elevation` | **SUPERSEDED** | MECH | 1 | +27/-408 in 3/7 files | elevation.py / elevation_dashboard.html on main are later | +27/-408 |
| `codex/pariprashna-tracker-precondition` | **SUPERSEDED** | MECH | 4 | +25/-528 in 7/7 files | tracker-elevation precondition build landed (control.py/elevation*.py on main are later) | +25/-528 |
| `codex/pariprashna-tracker-precondition-path-fix` | **SUPERSEDED** | MECH | 1 | +3/-131 in 2/2 files | launchd PATH fix landed; elevation_worker.py on main is later | +3/-131 |

---

## §4 — V3 entries opened by A3-ABSORB

Five entries. Each is a finding of the census itself, evidenced against
`origin/main@cc6b1a55e` on 2026-08-28. Severities are finder-proposed and
await Native Surrogate triage.

### V3-E-001 — No unmerged branch contains any change to the P2-B-001 authorization surface

- **Class / severity:** PROCESS · S2 (proposed)
- **Lens / stage:** L-CODE · CROSS
- **Expected:** elevation §6.3 states the `p2`-family, `g1-*`, `hs4-fix` and
  `citation-leak-fix` branches "bear directly on P2 blockers", which would make
  A3 a source of candidate fixes for A4.
- **Observed (2026-08-28, exhaustive scan of all 81 branches' changed-file
  sets):** **not one** of the 81 branches touches
  `platform/src/app/api/charts/[id]/route.ts` — the exact surface P2-B-001 names
  (historical `GET /api/charts/[id]` lacked per-chart authorization, EDIR E-012,
  native-disposed PARKED). There is therefore **no historical fix to salvage for
  B-001**; A4 must originate it. The same scan finds no branch adding
  `verify_heartbeat_provenance.sh` (P2-B-005's named detector, EDIR E-122) —
  that script exists only in the quarantined swarm harness
  `00_ARCHITECTURE/autonomy_pariprashna/bin/`, which has **0 files on
  `origin/main`**. B-002's arming scripts (`platform/scripts/pariprashna/
  g1c_arm_rls.sql`) and B-004's reproduction instrument
  (`platform/scripts/probe/ask.ts`) *are* on main, but both are instruments, not
  fixes.
- **Code anchor:** `platform/src/app/api/charts/[id]/route.ts` (main, unchanged
  by any branch); `00_ARCHITECTURE/autonomy_pariprashna/` (absent from main).
- **Cross-refs:** P2-B-001 (E-012), P2-B-004 (E-119), P2-B-005 (E-122);
  elevation §6.3.
- **Proposed fix class:** none — this is a denominator correction for A4. A4's
  blocker denominator must not assume an absorbed fix exists for B-001 or a
  present detector for B-005.
- **Status:** OPEN · close rung: A4 records the correction in its frozen
  blocker denominator.

### V3-E-002 — `pariprashna/p4-g` holds 2,384 lines of unmerged, test-covered feature work absent from main

- **Class / severity:** PROCESS · S3 (proposed)
- **Lens / stage:** L-CODE · SURFACE/CROSS
- **Expected:** absorption leaves nothing of value stranded on an unmerged branch.
- **Observed (2026-08-28):** `platform/src/lib/pariprashna/samiksha/window_ask/`
  — 12 modules (`classify`, `compose`, `select`, `capture`, `turn_hook`, `flag`,
  …) plus 5 test files (199+ unit tests, one DB-integration) — **does not exist
  on main**: `git ls-tree origin/main platform/src/lib/pariprashna/samiksha/`
  returns 25 files, none under `window_ask/`. Residue vs main is +2384/-5, the
  only branch in the census whose insertions dominate. Flag-gated
  (`window_ask/flag.ts`).
- **Code anchor:** `origin/pariprashna/p4-g` commits `7b63249bb`, `c8d31c9ba`,
  `0bf74e448`.
- **Proposed fix class:** replay onto a fresh lane branch off current main, with
  its own failing-test justification, if a current work item wants the feature.
  **Not a P2 blocker**; no PR opened by this lane.
- **Status:** OPEN · close rung: a Session C integration decision (land, or
  record a deliberate drop).

### V3-E-003 — `/api/conversations/[id]/feedback` POST is still an unconditional stub on current main: a reader's dispute is silently discarded

- **Class / severity:** DEFECT · S2 (proposed)
- **Lens / stage:** L-CODE + L-WIRE · SURFACE (S11 persistence)
- **Expected:** a reader disputing a claim the instrument made must leave a
  durable record; test plan §9 / J8 (feedback & dispute) and the campaign's own
  G8 feedback/dispute obligation.
- **Observed (2026-08-28, read directly from `origin/main@cc6b1a55e`):**
  `platform/src/app/api/conversations/[id]/feedback/route.ts` is still the WS-0
  stub — `POST` parses the body, returns `{ ok: true, rating }`, and touches no
  database; `GET` always returns `{ feedback: [] }`. Its own header comment says
  so ("`message_feedback` table dropped in WS-0. Endpoint returns empty/ok
  stubs."). It is also the only `[id]/*` sibling that does not run
  `getConversation`'s ownership check — with no data read or written today that
  is not itself a leak, but it is a live divergence from sibling-route
  discipline. `pariprashna/p4-h` restored this path and was **REFUTED and
  PARKED** by native-surrogate ruling because the restored write to
  `conversation_messages.metadata_json` is erased wholesale by the next ordinary
  turn (DD-28, already on main); so the honest current state is that neither the
  stub nor the attempted restore delivers a durable dispute.
- **Code anchor:** `platform/src/app/api/conversations/[id]/feedback/route.ts:1-3`
  (the header comment that states the stub), `:7-11` (GET returns a constant
  empty array), `:13-22` (POST; `:18` is the unconditional
  `Response.json({ ok: true, rating })` that touches no database).
- **Cross-refs:** DD-28 / DD-29 / DD-30 (on main via
  `pariprashna/dd28-30-split`); `pariprashna/p4-h`'s `it.skip`-quarantined red
  detector `feedback_dispute_survives_turn.db.test.ts`.
- **Proposed fix class:** owning-stream decision (S5 data integrity or S2
  conversation experience) — the DD-30 recommendation of a dedicated
  `conversation_disputes` table is explicitly a native decision, not assumed here.
- **Status:** OPEN · close rung: INTEGRATION (the parked red detector un-skipped
  and green against a real Postgres) then LIVE.

### V3-E-004 — One census disposition is preliminary: `codex/pariprashna-shadow-deploy`'s `elevation_service.py` has no counterpart on main

- **Class / severity:** PROCESS · S4 (proposed)
- **Lens / stage:** L-CODE · CROSS (campaign infrastructure)
- **Expected:** every branch disposition rests on evidence, and a disposition
  that does not is labelled as such rather than rounded to a confident class.
- **Observed (2026-08-28):**
  `00_ARCHITECTURE/briefs/pariprashna_assurance/tracker/elevation_service.py`
  (83 lines; a loopback-only launchd spec for an isolated shadow dashboard on
  port 8788, runtime `/Users/Dev/.pariprashna-assurance-elevation-shadow`) is the
  only file in the entire codex family with no same-named counterpart on main.
  Main carries `elevation_operations.py` (whose `ShadowOperations` emits
  `com.marsys.pariprashna-assurance.shadow` launchd job specs) and
  `elevation_server.py`, which **may** already satisfy its intent — that
  equivalence was **not** established in this pass, so the branch is graded
  SALVAGE/PRELIM rather than SUPERSEDED on an assumption.
- **Code anchor:** `origin/codex/pariprashna-shadow-deploy` @ `ea081d3b3`.
- **Proposed fix class:** a 15-minute targeted comparison in A4 or Session C;
  then either SUPERSEDED with cited evidence, or a replay lane.
- **Status:** OPEN · close rung: STATIC (the comparison performed and recorded).

### V3-E-005 — The v3 campaign's own governing register (this one) is the first artifact of the programme that exists on neither main nor a pushed branch

- **Class / severity:** DOC · S4 (proposed)
- **Lens / stage:** L-CODE · CROSS (governance)
- **Expected:** §N.8 / the register law — a governance surface a downstream
  session is told to rely on must be reachable from where that session starts.
- **Observed (2026-08-28):** the historical EDIR, the swarm harness
  (`00_ARCHITECTURE/autonomy_pariprashna/`, 0 files on main) and the swarm
  tracker's live state all exist only in local worktrees on local-only branches.
  The census could read them only because those worktrees happen to still be
  checked out on this machine. This register's §0 is a pointer *into that same
  quarantine*; if the worktree is removed before Session C's cleanup step, §0's
  references become unresolvable and 115 findings lose their bodies.
- **Proposed fix class:** Session C's cleanup (elevation §9 C4) must not remove
  the `pariprashna-assurance` worktree until the historical EDIR bodies are
  either landed, archived, or explicitly ruled not-needed — a named precondition,
  not an assumption.
- **Status:** OPEN · close rung: Session C records the precondition in its
  cleanup checklist.

### V3-E-006 — `cockpit/clear`/`clear/execute` have no chart ownership check at all (P2-B-007)

- **Class / severity:** DEFECT · S1 (CRITICAL — surrogate-assigned; added to the
  P2 blocker denominator as **B-007**, tracker decision `465a692c-f1f6-459a-
  8974-292015ba6436`)
- **Lens / stage:** L-CODE · A4 (P2 blocker clearance)
- **Provenance:** surfaced as a collateral finding during the B-001/E-012
  independent verifier's adversarial sibling-bypass search on PR #1597 — not
  originally in the P2 intake.
- **Expected:** a destructive, chart-scoped operation requires the caller to
  own (or hold a grant on) the target chart before either previewing or
  executing it.
- **Observed (2026-08-27):** `platform/src/app/api/cockpit/clear/route.ts` and
  `clear/execute/route.ts` gate only on `requireUser()` — no `owner_id`/grant
  check on `chart_id` anywhere. For the `per_chart` scope tier (almost all
  chart-scoped assets) and non-`global`/non-brahmagyan `asset`/`layer`
  requests, any authenticated user (default `guest` role included) can preview
  and then **execute an irreversible DELETE** of another user's — or the
  native's real chart `482012f1`'s — build-derived data. Separately, the
  `scope: 'global'` preview branch returns the target chart's real
  `subject_name` to any authenticated caller regardless of ownership, and that
  value is exactly what `typed_confirmation` needs to satisfy the one
  confirmation gate `execute` has.
- **Code anchor:** `clear/route.ts` (preview `requires_typed_confirmation`
  branch), `clear/execute/route.ts:157-165,180-225` (the per-asset `DELETE`
  transaction), `clearScopeFilter.ts` (`filterScopeAssets` narrowing a
  non-admin's `global` request instead of rejecting it).
- **Proposed fix class:** reuse `authorizeChartAccess` (the same helper B-001
  uses) on `chart_id` before both routes proceed, for all non-`super_admin`
  callers; reject non-admin `scope: 'global'` outright rather than silently
  narrowing it.
- **Status:** IN REMEDIATION — fix dispatched same session; independent
  verification and PR/CI/merge pending. Close rung: LIVE deployed re-proof
  (cross-user denial) after merge, per the same rigor as B-001/B-002.

### V3-E-007 — `clients/[id]/nirmana/page.tsx`'s `generateMetadata` leaks `subject_name` with no auth guard

- **Class / severity:** DEFECT · S2 (MEDIUM-HIGH, proposed)
- **Lens / stage:** L-CODE · CROSS (no app-level `middleware.ts` exists)
- **Observed (2026-08-27):** `generateMetadata` runs a raw
  `SELECT subject_name FROM charts WHERE id=$1` outside the page body's
  `resolveChartPageAccess`/`canBuild` guard. Any unauthenticated request for a
  known `chart_id` (curl, a link-preview crawler) returns the real subject
  name in the rendered `<title>` tag. Blast radius bounded by needing the
  chart's UUID (not enumerable), but directly exploitable for any id an
  attacker already holds.
- **Proposed fix class:** move the guard check ahead of the metadata query, or
  have `generateMetadata` return a generic title when the caller cannot be
  authorized (metadata generation has no request-scoped session by default in
  Next.js — needs the same session-resolution path the page body uses).
- **Status:** OPEN, filed to stream **S5** (Security, Privacy & Data
  Integrity) territory — not fixed in Session A. Close rung: LIVE
  unauthenticated-denial proof.

### V3-E-008 — `share/[slug]/page.tsx`: by-design unguessable-token sharing, one minor follow-up

- **Class / severity:** IMPROVEMENT · S4 (proposed, informational)
- **Observed (2026-08-27):** the share page requires a 58-bit random `slug`
  (`crypto.getRandomValues`) and correctly checks `revoked_at`/`expires_at` —
  the standard capability-link pattern, not a defect. Minor: no rate-limiting
  on slug lookups was found; impractical to brute-force at 58 bits, so this is
  a non-blocking follow-up, not a finding requiring a fix.
- **Status:** OPEN, filed to stream **S5** as a low-priority improvement lead
  only. No close rung required to unblock anything.

### V3-E-009 — `charts/[id]/route.ts` DELETE's `client_id` check is legacy, not an escalation path

- **Class / severity:** DOC · S4 (proposed, informational)
- **Observed (2026-08-27):** DELETE checks `owner_id === uid || client_id ===
  uid`; `client_id` is a legacy pre-081 column confirmed (via
  `clients/create/route.ts` and migration history) to always equal `owner_id`
  for this app's actual data model — not a third-party designation, so not an
  exploitable privilege-escalation path. Documented for completeness given it
  surfaced during the B-001/DELETE-vs-GET asymmetry check.
- **Status:** CLOSED-AS-BENIGN at STATIC rung (code-read proof above) — no
  further action; filed for the record only.

---

*End EDIR_V3_REGISTER v1.0 — 115 historical entries imported by reference;
### V3-E-010 — Two more confirmed `chart_id`-ownership gaps outside the B-007/B-008 fix scope

- **Class / severity:** DEFECT · S2 (MEDIUM, proposed — auth-gated but not
  ownership-gated; narrower than B-007/B-008's zero-auth cases)
- **Lens / stage:** L-CODE · CROSS
- **Provenance:** surfaced by the B-008 fixer while sweeping `cockpit/*` for
  the same root cause (no per-route `chart_id` ownership check) already
  confirmed three times (B-001, B-007, B-008).
- **Observed (2026-08-27):**
  - `POST /api/build/rebuild-all` and `POST /api/build/rebuild` require login
    (`requireUser`) but insert `build_events` rows for any caller-supplied
    `chart_id` — a cross-tenant write, not read/delete.
  - `GET /api/assets/[chart_id]/[asset_key]` requires login but returns
    per-chart asset data for any `chart_id` in the path — a cross-tenant read.
- **Proposed fix class:** same pattern as B-007/B-008 — gate with
  `requireChartPermission`/`authorizeChartAccess` (the shared helper B-008
  introduced), `'all'` for the write path, `'read'` for the asset read.
- **Status:** OPEN, filed to stream **S5** — not fixed in Session A.

### V3-E-011 — Systemic: ~30 further routes take a `chart_id` with no verified ownership check

- **Class / severity:** PROCESS · S2 (MEDIUM, proposed — this is a coverage
  gap, not itself a proven exploit; severity of any individual route within it
  is unknown until triaged)
- **Lens / stage:** L-CODE · CROSS
- **Expected:** given the SAME root cause has now been independently confirmed
  four times in one session (`charts/[id]` GET → B-001; `cockpit/clear`+
  `execute` → B-007; `cockpit/runs`+`atlas/sample` → B-008; `build/rebuild*`+
  `assets/[chart_id]/[asset_key]` → V3-E-010 above), a bounded per-instance
  response is no longer proportionate — a systematic audit is needed.
- **Observed (2026-08-27):** the B-008 fixer's broader scan (not a full triage)
  flagged roughly 30 additional routes accepting a `chart_id` parameter with
  no independently-confirmed ownership check. The fixer explicitly declined to
  triage these individually within B-008's scope — "many are probably fine
  (owner-scoped SQL, admin-gated) but I did not triage them." One claimed
  instance (the `watchdog` route) was investigated and DISPROVEN as a gap — it
  is correctly gated by an `x-watchdog-auth` shared secret for Cloud
  Scheduler — demonstrating the list needs real per-route verification, not a
  grep-count treated as a defect count.
- **Why this is NOT fixed in Session A:** A4's mandate is the P2 blocker
  denominator (B-001..B-006) plus severity-driven additions where a live,
  CONFIRMED critical surfaces collaterally (B-007, B-008 both met that bar via
  independent reproduction of a real unauthorized DELETE). An unconfirmed list
  of ~30 candidates is exactly the open-ended "keep chasing every new lead"
  pattern the elevation's bounded-scope discipline (§5.3: scope changes are
  authorized and registered, not chased indefinitely) warns against — chasing
  it further here would prevent A4 from ever closing CG-2 and starting the
  campaign's actual six streams, which is Session A's real purpose.
- **Proposed fix class:** a dedicated, systematic authorization audit —
  per-route: (1) does it accept a `chart_id`; (2) is there a verified
  ownership/grant/role check before any sensitive read or any write; (3) fix
  or confirm-safe, one at a time, with the same TDD discipline B-001/B-007/
  B-008 used. This is squarely stream **S5**'s mandate (§9 security/privacy/
  data-integrity battery) — filed there as a named, evidenced work item, not
  silently dropped.
- **Status:** OPEN, filed to stream **S5** as its highest-priority lead. Close
  rung: every candidate route individually triaged with a cited verdict
  (fixed / confirmed-safe-with-reason), not a re-statement of this count.
- **Addendum (2026-08-27, B-008 independent verifier):** three more confirmed
  members of the same family: `cockpit/runs/active`, `cockpit/sse`, and
  `cockpit/runs/[id]/assets` — auth-only, no ownership check, disclosing the
  same build-state the now-fixed `GET /api/cockpit/runs` protects. Added to
  this list rather than fixed in Session A, for the same bounded-scope reason.

---

## §4b — V3 entries from the S4 Pipeline Correctness & Door Parity stream

44 entries (V3-E-012..V3-E-055), appended 2026-08-28 by the Tracker/Register
Ops role consolidating 17 parallel agent reports (11 pipeline-stage lanes S1,
S2, S3, ScopeTuple/S4, S5, S6, S7, S8, S9, S10, S11 + 6 synergy tests:
boundary-contract enforcement, degradation-propagation honesty, trace
coherence, latency-waterfall accounting, progress truthfulness, and
cross-door whole-receipt parity including journey J10). Source reports:
`.s4_scratch/S4_stage_{S1,S2,S3,ScopeTuple,S5,S6,S7,S8,S9,S10,S11}_report.md`
and `.s4_scratch/S4_synergy_{boundary_contracts,degradation_honesty,
trace_coherence,latency_waterfall,progress_truthfulness,crossdoor_j10}_report.md`.
Test subject throughout: synthetic chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a`
("Abhinandan Mohanty") — the native's real chart `482012f1-…` was never
queried by any of the 17 lanes. Several lanes reached genuine **LIVE** rung
(real deployed-shaped turns against the synthetic chart, real DB reads via
the read-only Cloud SQL proxy) — cited explicitly per entry below, not
undersold. Dedup discipline: a historical finding independently reproduced
by more than one lane is filed as ONE fresh entry with `Provenance:` citing
the historical id and all reproducing sources; a systemic root cause with one
sharply distinct, independently-actionable sub-finding is filed as two
entries (root cause + worst sub-finding), not one-per-symptom. Severities
below are finder-proposed and await Native Surrogate triage, per register law.

### V3-E-012 — MCP door progress reporting freezes for the entire synthesis phase (E-003 reproduction, worse than seed)

- **Class / severity:** DEFECT · S2 (proposed)
- **Lens(es) / pipeline stage:** Failure-honesty, synergy/progress-truthfulness · CROSS (S8-adjacent, job-status serving layer)
- **Provenance:** E-003
- **Expected:** `prashna_status`'s `progress.message`/`progress.pct` visibly change during a long synthesis phase, surfacing the `last_tool:'synthesis'` phase-transition signal the platform route already emits.
- **Observed (2026-08-28):** Two independent LIVE reproductions. (1) A dedicated in-process probe against the real route handler and real synthesis LLM call: `progress.message`/`pct` froze at `"8/~25 tool calls made, 2.5s elapsed"`/`pct:32` for 69.7s of a 77.1s turn — 91% of wall-clock, worse than the seed's originally-logged 43%. (2) An independently-run latency-waterfall probe against a second, separate live turn corroborated the identical mechanism: message `"11/~25 tool calls made, 0.7s elapsed"` held byte-identical from `elapsed_ms=8,726` to `elapsed_ms=51,613` before completing at 102,402ms. Root cause: `register_prashna_ask.ts`'s message-building `onProgress` callback discards the `last_tool` field entirely; `synthesizeReading()` is one `await`ed call with no intermediate progress emission; `JobRegistry.updateProgress()` simply holds the last snapshot verbatim. The outer top-level `elapsed_ms` JSON field is honestly live-computed throughout — only the embedded `progress.message`/`pct` are frozen.
- **Code anchor:** `platform-mcp/src/tools/register_prashna_ask.ts:198-206` (message-building callback, discards `last_tool`); `platform/src/app/api/mcp/prashna_ask/route.ts` (no heartbeat during the `await synthesizeReading(...)` call, ~line 743); `platform-mcp/src/lib/job_registry.ts` (`updateProgress`/`get`, no independent live refresh).
- **PPR/gap cross-reference:** door-parity note — the Portal door's `working/` region does NOT reproduce this defect (see V3-E-050); this is MCP-door-scoped.
- **Proposed fix class:** surface `last_tool` in the rendered message ("Synthesizing the reading… (Ns elapsed)"); emit periodic heartbeat progress events during the synthesis await; have `register_prashna_status.ts` recompute a live pct/message-elapsed from `job.createdAt` the same way it already does for the outer `elapsed_ms`.
- **Status:** OPEN · verification rung required to close: LIVE (already achieved this session — real DB, real synthesis call, real synthetic chart, reproduced independently twice).

### V3-E-013 — Evidence-truncation disclosed only in `judgment_flags`, never enforced/verified in reader-visible prose (E-004 reproduction, MCP door)

- **Class / severity:** DEFECT · S1 (proposed)
- **Lens(es) / pipeline stage:** Correctness, Failure-honesty (B.10) · S8
- **Provenance:** E-004
- **Expected:** reader-visible prose discloses truncation whenever `judgment_flags` contains `synthesis_evidence_truncated`.
- **Observed (2026-08-28, worktree HEAD `f62aeadb0`):** `formatEvidenceBlock()` pushes an inline prompt *instruction* asking the model to disclose truncation; `synthesizeReading()` sets the flag; the model's raw response is returned verbatim with no lint/repair/rejection pass. A real INTEGRATION-rung demonstrated-can-fail test forced truncation (400,000-char oversized row past the 320,000-char budget), mocked a plausible fluent reading containing zero truncation language, and confirmed the codebase permits exactly this: `judgment_flags` carries the flag, `reading` text matches none of `/truncat/i|partial|incomplete|exhaustive|only (a portion|some) of/`. The permanent test suite (`prashna_ask_synthesis.test.ts`) has asserted green on this exact gap for over a month across three "disclose truncation" commits, none of which ever asserted on `result.reading` content. A degradation-honesty pass independently corroborates the systemic pattern: `grade`/`flag` wire events are dropped by the client adapter before reaching the reducer for other stages too (see V3-E-042), suggesting E-004 is one instance of a repo-wide envelope-vs-prose decoupling.
- **Code anchor:** `platform/src/lib/pipeline/prashna_ask_synthesis.ts:285-294` (unverified prompt instruction), `:378-381` (flag set, no verification), `:439-444` (reading returned verbatim); `platform/src/app/api/mcp/prashna_ask/route.ts:775,787` (independent fields, never spliced).
- **PPR/gap cross-reference:** B.10 (no fabricated completeness); see V3-E-035 for the distinct, worse Portal-door gap (no truncation handling at all).
- **Proposed fix class:** post-hoc verification/repair pass on `reading` when the flag is set (lint that fails closed and appends a disclosure sentence, or a lightweight second check), or deterministically append a disclosure sentence rather than relying on model self-report.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session — real vitest run, real code paths, mocked adapter only).

### V3-E-014 — Citation density thin and updated; production's own citation counter is blind to this door's real footnote format (E-005 reproduction/update)

- **Class / severity:** DEFECT · S2 (proposed) — upgraded from E-005's original IMPROVEMENT/BASELINE framing
- **Lens(es) / pipeline stage:** Correctness, Failure-honesty · S9
- **Provenance:** E-005
- **Expected:** citation density is measured, not assumed, and the counter measuring it can see the citations the model actually produces.
- **Observed (2026-08-28, LIVE):** a real `prashna_ask` MCP call against the synthetic chart (job `e6870d9f-…`, trace `498e3184-…`) produced a reading with 7 well-formed GFM footnotes (up from the E-005 seed's 2 — the absolute count varies by reading, updating rather than refuting the pattern) but only 50% claim-density by hand count (7 of 14 distinct factual/computed claims carried a footnote). Separately and more severely: the footnote *definitions* in this real reading are raw evidence-row UUIDs, not the `SIG.MSR.NNN` format the shared synthesis prompt mandates — `countSignalCitations()`/`totalSignalCitations()` both return 0 on this reading, and `validateCitations()` returns a silent `gate_result:'PASS'` for the non-prescriptive `holistic` class. A many-claim reading with real, honestly-numbered footnotes and a measured 50% citation rate is therefore indistinguishable, to the one gate that exists, from a reading with zero grounding attempted.
- **Code anchor:** `platform/src/lib/synthesis/citation_check.ts:14` (pattern); `platform/src/lib/pipeline/prashna_ask_synthesis.ts` (evidence source, no citation-format enforcement); `synthesis_prompt_v2.ts:36-46` (the citation-format contract the model doesn't honor on this door).
- **PPR/gap cross-reference:** PPR-04.
- **Proposed fix class:** either `citation_check.ts`'s pattern accepts a UUID-shaped footnote definition when it resolves against a known evidence row id, or the MCP door's evidence floor is made to surface real `SIG.MSR.NNN` ids.
- **Status:** OPEN · verification rung required to close: INTEGRATION + LIVE (already achieved this session — one real data point plus a real vitest measurement script).

### V3-E-015 — Turn latency waterfall: >99% of wall-clock time remains unattributed outside tool dispatch (E-006 reproduction, sharpened)

- **Class / severity:** BASELINE (with an IMPROVEMENT flag) · S3 (proposed)
- **Lens(es) / pipeline stage:** Optimality, synergy/latency-waterfall · CROSS
- **Provenance:** E-006
- **Expected:** a latency baseline that can be re-derived and tracked over time as the pipeline's own SLO reference.
- **Observed (2026-08-28, LIVE, real end-to-end `prashna_ask`/`prashna_status` turn):** native telemetry (the job's own `completeness.tools_dispatched[].latency_ms`) shows S6 dispatch = 705ms of a 102,402ms total turn = 0.69%; UNATTRIBUTED = 99.31%. This corroborates and sharpens the E-006 seed (81.3s turn, tool dispatch ≈4.0s ≈4.9%, >95% unattributed) on a second, independent live turn — same shape, worse ratio. A best-effort 11-stage decomposition (mixing MEASURED-DIRECT, STATIC-PROVEN-negligible, and bounded-inference evidence classes, each labeled honestly) attributes the dominant remainder (~91.4% of wall-clock) to S8 synthesis, corroborated independently by S5's own DB-backed measurement of planner latency (3,925ms avg over 14 real turns, ≈4.8% of the E-006 reference turn) and by the fact that no direct S8 timer exists on either door (see V3-E-030 for that root cause).
- **Code anchor:** none — this is a measurement/baseline finding, not a code defect per se.
- **PPR/gap cross-reference:** feeds the S6 (Performance/Resilience) SLO baseline per MACRO_PLAN §9.
- **Proposed fix class:** none required to close this baseline itself; see V3-E-030 for the instrumentation fix that would let this baseline be re-derived with stage-level precision going forward.
- **Status:** OPEN as baseline · verification rung required to close: absorbed into the G5/S6 SLO baseline (LIVE rung already achieved this session, twice independently).
- **Cross-stream referral (2026-08-28):** this baseline IS S6's (Performance, Resilience & Observability) own NFR input, per the S4 charter — see `S4_LATENCY_WATERFALL_v1_0.md` for the full formal handoff artifact. Referred to **S6** as the baseline owner; S4 does not own SLO-target-setting.

### V3-E-016 — Register-leak lint: 4 confirmed evasion classes pass clean (E-039 reproduction)

- **Class / severity:** IMPROVEMENT · S3 (proposed)
- **Lens(es) / pipeline stage:** Optimality (false-negative rate), Failure-honesty · S9
- **Provenance:** E-039
- **Expected:** the PPR-04 "100% seeded-id catch" claim holds against a reasonable adversarial variant sweep, or is scoped honestly to what it actually covers.
- **Observed (2026-08-28, INTEGRATION, real vitest run against `lintReaderProse`):** 4 of 5 adversarial variants evade the lint with `leakCount:0`, text unchanged: lowercase register acronym ("msr"), mixed-case ("Msr"), uppercase asset-id prefix ("BO_laksana"), and a spaced-out acronym ("M S R"). The control ("MSR") is correctly caught. No comprehensive seeded false-negative-rate corpus exists to give this a formal percentage — the honest finding is "at least 4 known evasion classes pass clean, 0 known adversarial corpus measures the rest."
- **Code anchor:** `platform/src/lib/pariprashna/citations/register_leak_lint.ts:80` (asset-id pattern, lowercase-only), `:99` (register-acronym pattern, uppercase-only), `:157` (near-miss lowercase set, telemetry-only, never redacts).
- **PPR/gap cross-reference:** PPR-04.
- **Proposed fix class:** case-insensitive matching (with care for common-English-word collisions) and/or a real seeded evasion corpus wired into a CI false-negative-rate check.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session — real vitest, 4/5 real reds, 1 control green).

### V3-E-017 — MCP door (`prashna_ask`) runs zero stage-S9 grounding validation (E-048 reproduction)

- **Class / severity:** DEFECT · S2 (proposed)
- **Lens(es) / pipeline stage:** Correctness, Door parity (PPR-30) · S9
- **Provenance:** E-048
- **Expected:** every door that returns synthesized prose runs the same grounding/safety validation gate (or an equivalent), so a leak/uncited-claim defense that exists on one door exists on both.
- **Observed (2026-08-28, INTEGRATION + LIVE):** grep-confirmed zero matches for `lintReaderProse|validateCitations|register_leak|citation_gate|runValidationStage` in `platform/src/app/api/mcp/prashna_ask/route.ts` or `platform/src/lib/pipeline/prashna_ask_synthesis.ts`. The V3-E-014 reading — containing raw evidence-row UUIDs in visible prose — passed through completely unlinted, live. Of the 5 call points named in the test plan's S9 anchor, 4 fire live on the Portal door and 1 (`reader_text/review.ts:40`) is offline/build-time-only (reachable only from a manually-run curation script, never a live turn on either door) — the test plan's S9 anchor documentation should be corrected to distinguish "4 live per-turn call points + 1 offline curation-time gate."
- **Code anchor:** `platform/src/app/api/mcp/prashna_ask/route.ts:743-759` (the `synthesizeReading` call, no lint/gate wrapper); `platform/src/lib/pariprashna/reader_text/review.ts:40` (the offline-only call point, doc-scope correction).
- **PPR/gap cross-reference:** PPR-30, PPR-04.
- **Proposed fix class:** wire `lintReaderProse` over `synthesis.reading` before it enters `readingEnvelope`, and run `validateCitations`/an equivalent gate, surfacing the result in `judgment_flags` the same way the web door does; separately, correct the test plan's S9 call-point count.
- **Status:** OPEN · verification rung required to close: INTEGRATION (static grep) + LIVE (already achieved this session — the captured unlinted reading itself is the positive proof).

### V3-E-018 — Per-query-class citation density threshold table is dead code (E-050 reproduction)

- **Class / severity:** DEFECT · S3 (proposed)
- **Lens(es) / pipeline stage:** Correctness · S9
- **Provenance:** E-050
- **Expected:** a declared per-class minimum-citation table is actually consulted by the gate it exists next to.
- **Observed (2026-08-28, STATIC):** `MIN_CITATIONS_BY_CLASS`, `hasMinimumCitations`, `citationThresholdForClass` have zero callers anywhere in `src` outside their own defining file and its unit test. `validateCitations()`'s real gate logic only checks "≥1 verified citation ⇒ PASS", never the per-class floor.
- **Code anchor:** `platform/src/lib/synthesis/citation_check.ts:17-29,53-64`.
- **PPR/gap cross-reference:** PPR-04.
- **Proposed fix class:** call `hasMinimumCitations`/`citationThresholdForClass` from `validateCitations()`, or delete the table and its exports if superseded.
- **Status:** OPEN · verification rung required to close: STATIC (already achieved this session — caller-count grep).

### V3-E-019 — `fallback_recommended`'s `confidence < 0.5` disjunct is structurally unreachable dead code (E-104 reproduction)

- **Class / severity:** DEFECT · S3 (proposed)
- **Lens(es) / pipeline stage:** Failure-honesty, §N.8 Earned-Signal · S4
- **Provenance:** E-104
- **Expected:** a two-term ambiguity guard's second disjunct is reachable and meaningful.
- **Observed (2026-08-28, INTEGRATION):** `fallback_recommended = !intentMatched || confidence < 0.5` (`scope_classifier.ts:299`); since `intentMatched` alone contributes +0.6 to confidence and nothing pushes confidence below that floor while `intentMatched` is true, the second disjunct can never fire while the first is false. Confirmed by direct arithmetic and by every intent-matched query in the existing test suite clearing 0.6 the same way.
- **Code anchor:** `platform/src/lib/vidhi/scope_classifier.ts:289-299`.
- **PPR/gap cross-reference:** none specific — a classifier-internals defect.
- **Proposed fix class:** the guard either becomes reachable (recompute confidence from more than a binary intent-match signal) or is removed/documented as dead.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session — fresh reproduction, `failure_honesty_check.test.ts`).

### V3-E-020 — Clarification false positives: three ordinary questions bounced to clarification instead of answered (E-105 reproduction)

- **Class / severity:** DEFECT · S2 (proposed)
- **Lens(es) / pipeline stage:** Failure-honesty · S1/S4
- **Provenance:** E-105
- **Expected:** an ordinary, answerable astrological question is answered, not bounced back for clarification.
- **Observed (2026-08-28, INTEGRATION, fresh reproduction, same three queries as the historical seed):** `'Will I get married?'`, `'Where is my Moon?'`, and `'Am I going to be rich?'` each classify to `intent:'unknown', confidence:0, fallback_recommended:true` on the Portal classifier — every one of these is an ordinary, answerable question that would be bounced to a `ClarificationRequest` instead of answered.
- **Code anchor:** `platform/src/lib/vidhi/scope_classifier.ts:289-299` (same code region as V3-E-019 — both defects share a root cause in the classifier's confidence formula).
- **PPR/gap cross-reference:** none specific.
- **Proposed fix class:** broaden `INTENT_RULES` for these common phrasings, or adjust the confidence formula so a domain-matched-but-not-intent-matched query doesn't collapse to `unknown`.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session — fresh reproduction, `failure_honesty_check.test.ts`).

### V3-E-021 — Web door's classifier defaults `depth:'standard'`, violating the binding deepdive-default doctrine and excluding an entire machine-band tier (E-112 reproduction)

- **Class / severity:** DEFECT · S2 (proposed, per E-112's existing proposal)
- **Lens(es) / pipeline stage:** Correctness, Demonstrated-can-fail, Door parity (PPR-30/PPR-16) · S4
- **Provenance:** E-112
- **Expected:** per `compiler.ts`'s own BINDING doctrine comment ("Deepdive is the default state of the instrument… an unclassifiable question resolves to general_synthesis at deepdive, never trimmed"), depth should default to deep, not standard.
- **Observed (2026-08-28, INTEGRATION, fresh independent reproduction with exact tool-name-level detail):** `scope_classifier.ts:263` defaults `depth:'standard'`; the MCP-side module implementing the deepdive-default LAW (`scope_resolver.ts`) is never imported by the web door. For an identical tuple, `standard` compiles 6 retrieval tool_calls / 14 total floor items (0 machine_band); `deep` compiles 13 tool_calls / 28 floor items (14 machine_band). The reader-visible completeness denominator changes from N/14 to N/28 depending purely on this default.
- **Code anchor:** `platform/src/lib/vidhi/scope_classifier.ts:262-265`; `platform/src/lib/vidhi/compiler.ts:93-117`.
- **PPR/gap cross-reference:** PPR-16, PPR-30.
- **Proposed fix class:** per E-112's own proposed close rung — REPLAY, both doors resolve the same depth for the same class of question.
- **Status:** OPEN · verification rung required to close: REPLAY (INTEGRATION already achieved this session with exact tool-call counts — `depth_effect.test.ts`).

### V3-E-022 — SemanticReadingParts classification is dark by default with a silent, unmarked fallback to plain paragraph (GAP-6 reproduction)

- **Class / severity:** DEFECT · S2 (proposed)
- **Lens(es) / pipeline stage:** Failure-honesty, §N.7/§N.8 silent-downgrade class · S10
- **Provenance:** GAP-6
- **Expected:** either the classifier runs and the reader sees real verse/gap-ribbon/heading/table/role structure, or — if deliberately off — a marker records that classification was skipped.
- **Observed (2026-08-28, INTEGRATION, real server assembler + real client adapter + real reducer chained end-to-end):** `PARIPRASHNA_SEMANTIC_BLOCKS_ENABLED` defaults `false`. All 5 block-kind detectors (`table`/`verse`/`gap_ribbon`/`heading`/`paragraph`+role) are genuinely implemented, not stubs, and are proven correctly wired when the flag is on (40/40 pre-existing tests pass). With the flag off, `commitBlock()` emits `{block_id, text}` only — no `kind` — and `s1LiveAdapter.ts`'s `ev.kind ?? 'paragraph'` plus the reducer's pass-through mean a classical verse citation (`>` blockquote markers intact) or an honest-gap sentence ("the chart is silent…") renders identically to ordinary prose, with zero field anywhere (wire event, reducer `CommittedBlock`, or DOM) indicating classification was skipped. This is structural-fidelity loss with an accompanying honesty gap, not data loss — raw text is preserved.
- **Code anchor:** `platform/src/lib/pariprashna/pipeline/reading_parts.ts:353-355`; `platform/src/components/pariprashna/state/s1LiveAdapter.ts:211`; `platform/src/components/pariprashna/state/reducer.ts:259`; flag default `platform/src/lib/config/feature_flags.ts:558`.
- **PPR/gap cross-reference:** GAP-6.
- **Proposed fix class:** additive/observability — add a per-turn `em.flag({code:'semantic_classification_skipped', ...})`, or flip the flag now that client renderers are tested and exist; a native/EDIR-owner disposition question, not a code change made this session.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session — real assembler + real client adapter + real reducer, chained, no mocks of code under test).

### V3-E-023 — `scope_tuple`/depth never reaches the LLM planner's own prompt; the honest depth-disclosure grade ships dark by default (GAP-8/PPR-16 reproduction)

- **Class / severity:** DEFECT · S3 (proposed)
- **Lens(es) / pipeline stage:** Correctness, Failure-honesty · S4/S5
- **Provenance:** GAP-8, PPR-16
- **Expected:** it should be clear (by doctrine or disclosure) whether the planner LLM sees the depth signal directly, and the reader-facing honest disclosure of the depth actually received should be live.
- **Observed (2026-08-28, STATIC + INTEGRATION):** `pipeline_planner.ts`'s LLM `userPayload` is built from `native_id`, `manifest`, `history`, `query` only — `scope_tuple`/`classification` is computed but never included in what the planner reads; depth's only effect on the executed tool set is a POST-hoc, conditional floor merge (`plan_stage.ts:279`, no-op for any tool the planner already independently requested). Separately, the reader-facing `reading_depth_received` disclosure grade (`plan_stage.ts:253-260`, built to close this exact PPR-09/16 gap) is gated behind `isHonestControlsEnabled()`, which defaults OFF (`honest_controls/flag.ts:22-23`, `feature_flags.ts:312`: "Default false: ships dark") — in default configuration, the disclosure this mechanism exists to emit is never sent.
- **Code anchor:** `platform/src/lib/pipeline/pipeline_planner.ts:416-424`; `platform/src/lib/pariprashna/pipeline/plan_stage.ts:244-260,276-284`; `platform/src/lib/pariprashna/honest_controls/flag.ts:22-27`.
- **PPR/gap cross-reference:** GAP-8, PPR-16, PPR-09.
- **Proposed fix class:** either confirm the depth-blind-planner design is intentional (floor = deterministic safety net, planner = independent judgment) and document it, or surface `scope_tuple` in the planner's own prompt; separately, confirm production flag state for the disclosure grade and whether a flip is scheduled.
- **Status:** OPEN · verification rung required to close: STATIC/INTEGRATION (already achieved this session).

### V3-E-024 — `compileFloorForPlan` discards `llm_extension_note`; the E-7 INSIGHT MANDATE never reaches the web/Paripraśna synthesis prompt at any depth

- **Class / severity:** DEFECT · S2 (proposed)
- **Lens(es) / pipeline stage:** Correctness, Demonstrated-can-fail · S4
- **Expected:** per `compiler.ts`'s own docstring, a `deepdive`-depth contract's `llm_extension_note` should reach the synthesis system prompt, directing the answerer "past fact-gathering to the non-obvious" — the qualitative payoff of asking for more depth.
- **Observed (2026-08-28, INTEGRATION):** `compileContract(...).llm_extension_note` correctly differs between `standard` and `deep` (confirmed: `deep` contains "INSIGHT MANDATE"), but `compileFloorForPlan`'s return shape (`CompiledFloorResult`) has no field for it — both `llm_extension_note` and `adaptive_expansions` are computed and thrown away. The only consumer anywhere in `src/` (`floor_cache.ts`) itself has zero production importers. This is the concrete mechanism-level explanation for why "deep dive" so often reads to a native as no different from "standard" even on turns where the floor genuinely differs.
- **Code anchor:** `platform/src/lib/pipeline/compiled_floor_adapter.ts:241-309` (return shape + function body); `platform/src/lib/vidhi/compiler.ts:300-314,375-384`.
- **PPR/gap cross-reference:** GAP-8, PPR-16 (mechanism behind the symptom family E-109/E-110/E-112 describe).
- **Proposed fix class:** plumb `contract.llm_extension_note` (and optionally `adaptive_expansions`) through `CompiledFloorResult` into `plan.synthesis_guidance`.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session — real function, real inputs, `depth_effect.test.ts`).

### V3-E-025 — Web door compiles only 1 of N domain floors (single-intent precedence) vs MCP door's full union for multi-domain queries

- **Class / severity:** DEFECT · S2 (proposed)
- **Lens(es) / pipeline stage:** Door parity (PPR-30) · S5
- **Expected:** for a multi-domain question, both doors should compile the same floor-mandated evidence set.
- **Observed (2026-08-28, INTEGRATION, both compiler entry points called live against the real registry):** the web door's `classifierIntentToCompilerIntent` picks exactly ONE `IntentClass` via fixed precedence — the first domain in `tuple.domains[]` with a registered deepdive floor wins, every other domain's floor is never compiled (confirmed: `domains:['career','wealth']` compiles ONLY `career_deepdive`, 23 mapped + 15 unmapped primitives, wealth-deepdive entirely absent). The MCP door's `buildVidhiPlan` → `compileMultiDomainContract` UNIONS both domains' deepdive floors for the identical input. The same reader, asking the same multi-domain question through the two doors, receives a different floor-mandated evidence set, with the web door's plan a strict subset of the MCP door's, undisclosed on the wire. A secondary parity gap, same root cause pair: the MCP door's `adaptive_expansions` (E-3 Anusaraṇa) field is never surfaced or consumed by `plan_stage.ts`/`PipelinePlan` at all.
- **Code anchor:** `platform/src/lib/pipeline/compiled_floor_adapter.ts:86-95,262-309` vs `platform-mcp/src/resources/vidhi/plan_builder.ts:60-67`; `platform/src/lib/vidhi/compiler.ts:26-30` (union semantics doc comment).
- **PPR/gap cross-reference:** PPR-30.
- **Proposed fix class:** repoint `compileFloorForPlan` to call `compileMultiDomainContract` with the classifier tuple's full `domains[]` array, mirroring the MCP door.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session — both compiler entry points called live with an identical two-domain tuple).

### V3-E-026 — Compiled-floor failure signal (`compileFailed`/`unmappedPrimitives`/`mappedPrimitives`) is computed but never consumed by `plan_stage.ts`

- **Class / severity:** DEFECT · S2 (proposed) — §N.8 Earned-Signal class
- **Lens(es) / pipeline stage:** Correctness, §N.8 · S5
- **Expected:** when `compileFloorForPlan` computes `compileFailed:true` (the compiler's own documented "registry-completeness bug… must fail loudly" case), the caller surfaces it.
- **Observed (2026-08-28, INTEGRATION, real registry-throw mock + grep-verified caller):** `plan_stage.ts:276-284` only consumes `compiledFloor.toolCalls`; grep-confirmed the file contains no reference to `compiledFloor.compileFailed`, `.unmappedPrimitives`, or `.mappedPrimitives` anywhere. If `compileContract` ever throws in production, the turn silently falls through to the generic B.11 fallback with no `em.flag()`, no `judgment_flags` entry, no server log line marking that the intent-specific compiled floor failed to compile — indistinguishable from a healthy turn on every surface a reader/operator can see. Two real tests confirm the split: the low-level mechanism DOES fail loudly (real thrown Error, correctly caught, `compileFailed` correctly set); the caller silently drops the signal one call frame up.
- **Code anchor:** `platform/src/lib/pariprashna/pipeline/plan_stage.ts:276-284`; `platform/src/lib/pipeline/compiled_floor_adapter.ts:241-252`.
- **PPR/gap cross-reference:** none specific.
- **Proposed fix class:** when `compiledFloor.compileFailed` or `unmappedPrimitives.length > 0`, push a `judgment_flags` entry and `em.flag()`, mirroring the pattern this same file already applies to NO-LEAKAGE strips and safety exclusions.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session).

### V3-E-027 — `buildWebCompletenessReceipt` under-counts actual floor coverage for ~25% of the registry's `live_tool` surface

- **Class / severity:** DEFECT · S2 (proposed)
- **Lens(es) / pipeline stage:** Optimality, Correctness · S5
- **Expected:** the completeness receipt's served/empty/dark accounting should use the same tool-resolution path that actually decides dispatch.
- **Observed (2026-08-28, INTEGRATION, real registry data, both import paths exercised):** `buildWebCompletenessReceipt` resolves `live_tool → retrieval tool` using only the hand-curated `LIVE_TOOL_TO_RETRIEVAL` map, while the code path that actually decides dispatch (`compileFloorForPlan → resolveLiveTool`) additionally falls back to the generated projection bridge. Of 40 distinct `live_tool` names in the registry, 10 resolve to a real web-executable tool via the generated bridge but are invisible to the hand map — including major primitives (`ganita_chart_facts_get`, `ganita_positions_get`, `ganita_dasha_periods_get`, `mechanism_retrodiction_get`, and 6 others). For any floor primitive keyed to one of these, dispatch happens and gets results, but the receipt reports it as `web_namespace_gap` (empty/dark) regardless — the "honest" receipt is systematically too pessimistic for ~25% of the registry surface.
- **Code anchor:** `platform/src/lib/pipeline/completeness_wiring.ts:106` vs `platform/src/lib/pipeline/compiled_floor_adapter.ts:224-226`.
- **PPR/gap cross-reference:** §N.7 item 3 "reference, not a copy" class.
- **Proposed fix class:** `completeness_wiring.ts` should call `resolveLiveTool` (exported from `compiled_floor_adapter.ts`) instead of indexing `LIVE_TOOL_TO_RETRIEVAL` directly.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session).

### V3-E-028 — Predictive-class turns show 0% tool-selection efficiency: full floor dispatched, zero citations produced, 14/14 real turns

- **Class / severity:** DEFECT · S1 (proposed) — 100%-reproducible, DB-confirmed over-dispatch on a prescriptive query class where B.10 grounding matters most
- **Lens(es) / pipeline stage:** Optimality · S5/S8
- **Expected:** dispatched evidence should translate into cited, grounded output at some measurable non-zero rate.
- **Observed (2026-08-28, DB-backed/LIVE-adjacent, 14 real turns via `query_trace_steps`, `predictive` query class):** every one of 14 measured turns dispatched a full 10-tool floor and cited zero of it (`citation_error`/`citation_warn` rows, message: "prescriptive query (predictive) produced 0 citations — guidance must be grounded", on all 14). Root cause: `evidence_stage.ts`'s pass-1 dispatch fetches every authorized tool purely to build the completeness receipt and extract candidate signal-ids, but pass-1 content is never injected into the synthesis prompt; the synthesis model runs its own separate agentic loop, free to call or not call any subset of tools, and for predictive-class turns in this sample it chose to ground nothing.
- **Code anchor:** `platform/src/lib/pariprashna/pipeline/evidence_stage.ts:75-103`; `platform/src/lib/pariprashna/pipeline/citation_resolver.ts:44-54`; `platform/src/lib/pipelines/shared/run_adapter_dispatch.ts:441-489`.
- **PPR/gap cross-reference:** B.10, §N.6.
- **Proposed fix class:** either skip pass-1 dispatch for tools the agentic loop will redundantly re-call, or feed pass-1 results directly into the agentic loop's tool-result cache so an already-fetched tool is served from pass 1.
- **Status:** OPEN · verification rung required to close: DB-backed/LIVE-adjacent (already achieved this session — 14 independent real turns, 100% reproduction rate).

### V3-E-029 — `budget_arbiter` can zero a floor tool's `token_budget` while the presence-only floor check reports the floor satisfied (dormant)

- **Class / severity:** DEFECT · S3 (proposed) — currently latent, not actively starving evidence
- **Lens(es) / pipeline stage:** Failure-honesty · S5
- **Expected:** a B.11 floor guarantee should verify the floor tool is genuinely usable, not merely present by name.
- **Observed (2026-08-28, INTEGRATION, real `arbitrateBudgets` + real `ensureB11WholeChartReadFloor` called together, no mocking):** `arbitrateBudgets` can reduce a priority-3 tool's `token_budget` to 0; `ensureB11WholeChartReadFloor` checks only tool-name presence, not whether `token_budget > 0`, so the floor guarantee reports itself satisfied for a tool whose own budget field claims 0 tokens. Confirmed live: a real `msr_sql` p3 tool's budget zeroed 2000→0, floor check still returns `injected:false` (believes the floor is met). Currently dormant because `token_budget` is not actually consumed anywhere on the pass-1 dispatch path — but this means the arbiter's own stated job (hard cap on `planned_total`) is not currently enforced by anything downstream, and this exact interaction becomes a live evidence-starvation bug the moment someone wires `token_budget` into real content truncation.
- **Code anchor:** `platform/src/lib/pipeline/budget_arbiter.ts:54-66`; `platform/src/lib/pipeline/compiled_floor_adapter.ts:329-330`; `platform/src/lib/pariprashna/pipeline/evidence_stage.ts:75-103`; `platform/src/lib/cache/with_cache.ts:60-107`.
- **PPR/gap cross-reference:** §N.8 (looks-fine-because-nothing-reads-it trap).
- **Proposed fix class:** `ensureB11WholeChartReadFloor`/`ensureDashaContextFloor` should check `token_budget > 0`, not name presence alone; separately confirm whether `token_budget`'s non-use on the dispatch path is intentional or a stale wiring gap.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session — real functions, no mocking).

### V3-E-030 — No native per-stage latency telemetry exists between S1 and S11; the S8 synthesis trace-completion row is permanently stuck at `status:'running'`

- **Class / severity:** DEFECT · S2 (proposed)
- **Lens(es) / pipeline stage:** Optimality, synergy/latency-waterfall, synergy/trace-coherence · CROSS
- **Expected:** the sum of 11 stage durations should be reconstructable from telemetry so regressions are locatable to a specific stage, and E-006-style latency baselines should be re-derivable over time.
- **Observed (2026-08-28, LIVE + INTEGRATION, independently corroborated by four separate lanes this session):** (1) The Portal door's `em.phase()` instrumentation emits only 4 coarse buckets (plan/retrieve/synthesize/finalize), not exposed via the MCP door at all. (2) `query_trace_steps` rows for `step_name='synthesis'` (the WEB `consult` route) get a real `started_at` but `completed_at`/`latency_ms` are NEVER populated — confirmed live: 16/16 historical rows stuck `status='running'`, 0/0 ever reach `status='done'`; the scaffolding for an S8 timer exists and is silently abandoned mid-build. (3) The MCP door writes ZERO rows to `query_trace_steps` at all, ever — consistent with its `persistence: {status:'none'}` field (P2-B-004/E-119). (4) S5's own attempt to compute "plan latency share of turn" from this table was overstated by ~10x (46% vs the true ~4.8%) precisely because the synthesis step's missing `latency_ms` silently skews the step-sum denominator — a concrete demonstration that this instrumentation gap corrupts derived metrics, not just leaves a blank field. This means E-006's own latency-share figures cannot currently be re-derived from `query_trace_steps`.
- **Code anchor:** `platform/src/lib/synthesis/single_model_strategy.ts` (zero `traceEmitter` calls for synthesis completion); `platform/src/lib/trace/types.ts:315` (stale doc claim, "context_assembly… still emitted in prod" — false); `platform/src/app/api/pariprashna/route.ts:138,322`; `platform/src/lib/pariprashna/pipeline/{plan_stage.ts,evidence_stage.ts,synthesis_stage.ts,persistence_stage.ts,safety_gate.ts}` (4-bucket phase instrumentation only).
- **PPR/gap cross-reference:** feeds E-006 re-derivation; §N.8.
- **Proposed fix class:** add `em.phase()` (or equivalent trace-span) boundaries at each of the 11 architectural stage seams; complete the already-half-built `query_trace_steps` synthesis row (write `completed_at`/`latency_ms` when synthesis actually finishes); surface the same span data through the MCP door's job-result envelope.
- **Status:** OPEN · verification rung required to close: LIVE (already achieved this session — real completed job responses inspected field-by-field, plus live `query_trace_steps` DB reads, corroborated independently by 4 separate lanes).

### V3-E-031 — S6 ToolBroker dispatch has no protective bounds: no per-tool timeout, no queue backpressure refusal, no per-tool latency budget

- **Class / severity:** DEFECT · S1 (proposed) — a hung tool call blocks the entire retrieve stage indefinitely and is never reported
- **Lens(es) / pipeline stage:** Correctness, Failure-honesty, Optimality · S6
- **Expected:** per the dispatch queue's own honest-degradation doc-comment ("queue/refuse, never thin quality"), a hung call should be bounded and reported as unresolved/timed-out; sustained overload should eventually refuse rather than queue unbounded; a per-tool budget should exist to measure optimality against.
- **Observed (2026-08-28, INTEGRATION, real production code):** (1) A never-resolving `submit()` task does not settle within a 1500ms observation window; no `AbortController`/`setTimeout`/`Promise.race` exists anywhere in `dispatch_queue.ts` or `with_cache.ts`. Because `evidence_stage.ts` (and the MCP door's serial loop) `await` the full batch before emitting anything, one hung tool blocks the entire retrieve stage — no `unresolved`/`error`/`timeout` entry is ever produced; the request runs until an outer infrastructure timeout kills the whole thing, losing even the tools that *did* succeed. (2) `getSharedQosDispatchQueue()` constructs the singleton with no options — `maxQueueDepth` defaults `undefined` (unbounded); `QueueSaturatedError`/the refuse mechanism works correctly under test but is unreachable in production (grep-confirmed zero non-test call sites configure it). (3) `cap_tripped` (the one real, earned cost-cap signal) is only checked BETWEEN calls, so a hang leaves no "next iteration" for it to trip on — the cap's own job (bounding wall-clock exposure) is not actually enforced for a hang. (4) No `latency_budget`/`timeout_ms`/`sla` field exists anywhere on `CapabilityDescriptor` or the S6 surface, so per-tool optimality-vs-budget is structurally unmeasurable (only an aggregate whole-job wall-clock cap exists). Explicit tool rejections (throws), by contrast, ARE honestly surfaced end-to-end — this gap is specific to hangs, not failures generally.
- **Code anchor:** `platform/src/lib/retrieval/qos/dispatch_queue.ts:185-204` (`pump()`, unwrapped `next.run()`), `:271-274` (unconfigured singleton); `platform/src/lib/cache/with_cache.ts:60-107` (unbounded `await`); `platform/src/lib/pariprashna/pipeline/evidence_stage.ts:87-91`; `platform/src/app/api/mcp/prashna_ask/route.ts:655-671`; `platform/src/lib/pipeline/cost_caps.ts:67-89`; `platform/src/lib/retrieval/registry/types.ts` (`CapabilityDescriptor`, no latency field).
- **PPR/gap cross-reference:** none specific.
- **Proposed fix class:** wrap the `run()` closure (or `next.run()` in `pump()`) in `Promise.race` against a per-tool timeout that rejects, flowing through the existing honest-error path; set an explicit `maxQueueDepth` on the shared singleton; add an optional `expected_latency_ms_p95` field to `CapabilityDescriptor`.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session — real `QosDispatchQueue`, real hang test, real queue-depth grep).
- **Cross-stream referral (2026-08-28):** timeout/backpressure/latency-budget mechanisms are production resilience posture, not a drive-by pipeline fix — referred to **S6** (Performance, Resilience & Observability) per its charter ownership of timeouts/reconnect/resilience; S1-severity, high priority.

### V3-E-032 — Duplicated dispatch-loop implementation across two entry points is a door-parity/maintainability risk

- **Class / severity:** IMPROVEMENT · S3 (proposed)
- **Lens(es) / pipeline stage:** Door parity, Correctness · S6
- **Expected:** one dispatch implementation backs every door, so a fix (e.g. V3-E-031's timeout fix) lands everywhere at once.
- **Observed (2026-08-28, INTEGRATION, both call sites confirmed):** `consult/route.ts` (~L900-970) inlines a near-duplicate of `evidence_stage.ts`'s (L75-105) submit/executeWithCache/toolEventLog loop; both share the `getSharedQosDispatchQueue()` singleton but are separately written and maintained.
- **Code anchor:** `platform/src/app/api/chat/consult/route.ts:900-970`; `platform/src/lib/pariprashna/pipeline/evidence_stage.ts:75-105`.
- **PPR/gap cross-reference:** none specific.
- **Proposed fix class:** extract the shared dispatch-loop body into one function both routes call.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session — code read, both call sites confirmed).

### V3-E-033 — `hydrateBundle` silently drops failed non-floor assets with no bundle-level disclosure and no wire event at all

- **Class / severity:** DEFECT · S2 (proposed)
- **Lens(es) / pipeline stage:** Correctness, Failure-honesty (§N.6/§N.7 item 6) · S7
- **Expected:** when N assets are requested and M<N actually load, the returned bundle (or the wire) should be able to answer "which assets were dropped and why."
- **Observed (2026-08-28, INTEGRATION, two independent confirmations):** (1) A dedicated S7 investigation demonstrated live via real `hydrateBundle` calls that unknown `asset_id`s, manifest entries with no `path`, and `storage.readFile` throws each do `console.warn(...); continue` with no corresponding field on `HydratedBundle` — a caller reading the returned object cannot distinguish "got exactly what was asked" from "some of it silently vanished." (2) A separate degradation-honesty investigation independently confirmed the same code paths never reach the SSE wire in any form: `hydrateBundle(plan, manifest)` doesn't even accept an `em`/emitter parameter, so the failure structurally cannot become a flag, grade, or error event — it never reaches the client, machine-readable or otherwise (only the ONE floor asset, e.g. `CGM`, is fatal and becomes a real `em.error()`).
- **Code anchor:** `platform/src/lib/bundle/bundle_hydrator.ts:104-131` (three non-floor failure branches), `:107,114,127-130`; `platform/src/lib/pariprashna/pipeline/evidence_stage.ts:66` (no emitter passed in).
- **PPR/gap cross-reference:** §N.6, §N.7 item 6.
- **Proposed fix class:** add a `skipped: {asset_id, reason}[]` field to `HydratedBundle`, populated at each non-floor `continue` site; thread `em`/a warnings collector through `hydrateBundle` and emit `em.flag({code:'asset_hydration_failed', ...})` per skipped asset, feeding the skip list into the completeness receipt/synthesis prompt.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session — real filesystem I/O errors, real manifest shapes, two independent reproductions).

### V3-E-034 — Registry-lookup-miss silently escapes `toolEventLog`, unlike a dispatch throw

- **Class / severity:** DEFECT · S3 (proposed)
- **Lens(es) / pipeline stage:** Correctness, Failure-honesty · S7
- **Expected:** "tool not found in the registry bridge" and "tool found but dispatch threw" — two failures of the same class — should be recorded identically in `toolEventLog`.
- **Observed (2026-08-28, INTEGRATION, real `runEvidenceStage`, mocked only at the I/O seams):** a registry-lookup miss produces zero `toolEventLog` entries (`out.toolEventLog` empty), while the equivalent dispatch-throw case produces exactly one `status:'error'` row. Downstream, `completeness_wiring.ts`'s `if (!outcome)` branch treats the resulting gap as `empty_reason:'route_not_invoked'` — the SAME label used for "this tool was correctly never authorized" — rather than a distinct reason. The live `activity.upsert` SSE event does say `status:'error'` (streaming client sees it), but the server-side completeness receipt cannot see it — an inconsistency between what streams and what's recorded for the turn's own honesty accounting.
- **Code anchor:** `platform/src/lib/pariprashna/pipeline/evidence_stage.ts:80-84` (no `toolEventLog.push`) vs `:96-101` (catch branch does push); `platform/src/lib/pipeline/completeness_wiring.ts:98,120-129`.
- **PPR/gap cross-reference:** none specific.
- **Proposed fix class:** push a `toolEventLog` entry in the `if (!t)` branch too, matching the catch branch's shape; give `completeness_wiring.ts` a distinct `empty_reason` for "authorized but registry-unresolvable" vs. genuine non-authorization.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session — real `runEvidenceStage`).
- **Resolved (2026-08-29, resume session):** MERGED — PR [#1643](https://github.com/Marsys-Technologies/Madhav/pull/1643), independently verified ACCEPT (verifier traced `registry_unresolvable` to `receipt/assemble.ts`'s `buildHonestGaps()` and the live data-completeness SSE event — genuinely consumed, not a dead value; RED→GREEN independently reproduced; full repo suite 10480/10488, 8 pre-existing unrelated failures confirmed).

### V3-E-035 — Portal-door agentic-loop tool results have no size cap/truncation handling at all, unlike the MCP door's budgeted approach

- **Class / severity:** DEFECT · S2 (proposed)
- **Lens(es) / pipeline stage:** Correctness, Optimality, Door parity (PPR-30) · S8
- **Expected:** if one door budgets/truncates oversized evidence, the sibling door should have an equivalent mechanism, or the asymmetry should be a named, deliberate decision.
- **Observed (2026-08-28, INTEGRATION-adjacent static trace + grep):** `executeMCPTool` (`mcp_tool_executor.ts:66-71`) returns `JSON.stringify({tool, results, result_count})` to the model with zero size cap, zero row selection, zero truncation logic. Exhaustive grep for "truncat" across `synthesis_stage.ts` and `pariprashna/` returns only an unrelated prompt instruction and a different, later-stage concept (`interpretation_sets.truncated_count`, a cap on interpretation-set count, not raw evidence size). No `judgment_flags` vocabulary exists in the Portal pipeline at all. A wide `deep_dive` (up to 16 agentic-loop re-entries) accumulating many large tool results could grow the message history unboundedly, with no application-level truncation, no flag, and therefore no disclosure surface to even build prose-enforcement onto — a distinct, likely-worse failure mode than the MCP door's V3-E-013 (a silent provider-level context truncation/error with zero telemetry, vs. an honest-but-unverified partial fix).
- **Code anchor:** `platform/src/lib/synthesis/mcp_tool_executor.ts:66-71`; `platform/src/lib/synthesis/agentic_loop.ts` (no truncation logic found).
- **PPR/gap cross-reference:** PPR-30; sibling of V3-E-013.
- **Proposed fix class:** add a size cap / bearing-aware row selection to `executeMCPTool`'s results, mirroring the MCP door's `selectRowsWithinBudget` approach, plus a disclosure signal.
- **Status:** OPEN · verification rung required to close: LIVE (a repro test running an oversized tool result through the real agentic loop; INTEGRATION-adjacent static trace already achieved this session).

### V3-E-036 — Citation-gate PASS is not distinguishable from "0 citations, format-mismatch suspected" for non-prescriptive query classes

- **Class / severity:** DEFECT · S3 (proposed)
- **Lens(es) / pipeline stage:** Failure-honesty · S9
- **Expected:** per §N.6/§N.7, a reading with zero machine-verifiable citations should be visibly flagged even when the query class doesn't hard-require them.
- **Observed (2026-08-28, INTEGRATION):** `validateCitations()` returns `{gate_result:'PASS', gate_reason:"informational query (…); citations not required"}` for `layer1_count:0` on any non-prescriptive-class query, with no flag distinguishing "genuinely no claims to cite" from "7 real citations existed but none matched the expected pattern" (the exact V3-E-014 case).
- **Code anchor:** `platform/src/lib/synthesis/citation_check.ts:139-145`.
- **PPR/gap cross-reference:** §N.6, §N.7; sibling of V3-E-014/V3-E-018.
- **Proposed fix class:** emit a distinct, low-severity flag when `layer1_count===0` AND the raw text contains GFM footnote markers that didn't resolve to the expected pattern — a "format-mismatch suspected" signal instead of a bare PASS.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session).

### V3-E-037 — `interpretation_sets[].status:'generated'` claims genuine 3-way candidate distinctness on a lexical-overlap proxy that does not detect synonym-paraphrased near-duplicates

- **Class / severity:** DEFECT · S2 (proposed) — §N.8 Earned-Signal Principle
- **Lens(es) / pipeline stage:** Correctness, Demonstrated-can-fail · S11
- **Expected:** `status:'generated'` implies the system verified ≥3 genuinely distinct interpretive conclusions, per the worker's own system prompt.
- **Observed (2026-08-28, INTEGRATION, real `generateInterpretationSets`, only the LLM network seam mocked):** three synonym-paraphrased restatements of ONE identical claim ("career growth → leadership position → via hard work," reworded three ways with near-fully disjoint vocabulary) pass through the real, unmocked pipeline as `status:'generated'`, `candidates.length:3` — with no flag or degraded confidence. The only structural guard, `hasNearDuplicateCandidates` (lexical token-overlap), is self-disclosed in its own doc comment as "a floor-raise… not a semantic guarantee" that "cannot guarantee every near-duplicate candidate set is caught" — the code's own comments already disclose the limitation, but the receipt field consuming it does not.
- **Code anchor:** `platform/src/lib/pariprashna/interpretation/worker.ts:279-299` (`hasNearDuplicateCandidates`/`overlapRatio`), `:322-356` (`coerceEntry`).
- **PPR/gap cross-reference:** §N.8.
- **Proposed fix class:** strengthen the distinctness check with an embedding-similarity comparison (the codebase already has embedding infrastructure in L5), or surface the proxy's own disclosed limitation as a receipt field (e.g. `distinctness_check:'lexical_only'`).
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session — real pipeline, only the network seam mocked).

### V3-E-038 — `AcharyaReadingReceipt` has no mechanism to flag a substantive, uncited, time-indexed predictive claim in rendered prose

- **Class / severity:** DEFECT · S2 (proposed, escalating to S1 if this pattern occurs in production predictive-timing claims — career/health/marriage timing assertions are exactly the safety/calibration-adjacent class the Ethical Framework cares about)
- **Lens(es) / pipeline stage:** Failure-honesty, Correctness · S11
- **Expected:** an acharya-grade audit receipt should let an auditor distinguish "every substantive claim in this prose has grounding" from "this prose asserts things the receipt is silent about."
- **Observed (2026-08-28, INTEGRATION, real `assembleAcharyaReadingReceipt` + `validateAcharyaReadingReceipt`):** constructed a turn with an uncited, specific, falsifiable claim ("Saturn's Mahadasha begins in early 2027 and will bring five years of career stability and a confirmed promotion by 2029") alongside one cited claim. The receipt correctly recorded only the cited claim (`facts_consumed`=1 entry, `derivation_chains` for the uncited block has `fact_refs:[]`) — honest about what it captured — but `honest_gaps` is sourced entirely from the floor-item completeness model, which has zero visibility into prose content, so no entry exists for the uncited claim. `validateAcharyaReadingReceipt` reports the receipt fully coherent (0 violations). An auditor inspecting only the receipt has no way to know the prose asserted a specific 2027-2029 timing prediction.
- **Code anchor:** `platform/src/lib/pariprashna/receipt/assemble.ts:510-536` (`factRefsForBlock`/`buildFactsConsumed`), `:217-234` (`buildHonestGaps`).
- **PPR/gap cross-reference:** §N.7/§N.8 ("an honest null beats an invented judgment… but a genuine gap still needs a flag").
- **Proposed fix class:** add an uncited-substantive-claim detector (even coarse — a committed prose block with empty `fact_refs` matching a numeric/date/predictive-language heuristic), surfaced as a new honest field (e.g. `uncited_claim_blocks: string[]`).
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session — real receipt assembly + validation).

### V3-E-039 — Citation/grounding gate (`runValidationStage`) silently swallows internal errors on malformed synthesis input and defaults to PASS with ZERO wire event

- **Class / severity:** DEFECT · S2 (proposed) — worst of the 10 boundary-contract findings: no signal at all, not even a wrong grade
- **Lens(es) / pipeline stage:** synergy/boundary-contract · CROSS (S8→S9)
- **Expected:** the B.11 grounding-validation enforcement point should refuse loudly (or at minimum emit an explicit degraded-grade signal) when its input is malformed enough that validation could not run.
- **Observed (2026-08-28, INTEGRATION, real vitest harness, malformed-input probe):** `runValidationStage` wraps the entire citation-gate call in a try/catch that logs to the server console only and returns the PASS-default `citationGateResult` initialized before the try block; because the throw happens inside `validateCitationsForStream` BEFORE `em.grade({subject:'citation_gate', ...})` is reached, the `grade` wire event for this turn never fires — not PASS, not WARN, not ERROR. A deliberate, documented design choice ("the gate NEVER fails the turn"), but its consequence (total absence of the grounding signal on a malformed-input turn) is undisclosed to the wire protocol.
- **Code anchor:** `platform/src/lib/pariprashna/pipeline/validation_stage.ts:30-73`.
- **PPR/gap cross-reference:** B.11.
- **Proposed fix class:** emit a `flag`/judgment-flag entry ("citation_gate_errored") from inside the catch block so the wire always carries a signal, even when the PASS default is intentionally preserved as the serving decision.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session — real vitest harness, `.s4_scratch/boundary_contracts.test.ts`).

### V3-E-040 — Beyond the one S3→S4 Zod gate, no pipeline stage boundary re-validates its input at runtime: malformed objects crash with raw TypeErrors or silently corrupt/pass through

- **Class / severity:** DEFECT · S2 (proposed) — architecture-level: "a malformed object never crosses a boundary" holds for exactly 1 of 10 boundaries
- **Lens(es) / pipeline stage:** synergy/boundary-contract · CROSS (S4→S5, S5→S6, S6→S7, S7→S8, S9→S10)
- **Expected:** every stage boundary should validate its input against its own contract (or fail with a designed, named error), matching the one boundary (B3, S3→S4) that already does this correctly via `PipelinePlanSchema.safeParse`.
- **Observed (2026-08-28, INTEGRATION, real vitest harness against all 10 boundaries, 22 assertions):** `compiled_floor_adapter.ts` (S4→S5) reads `tuple.domains/width/depth/intent` with zero `ScopeTupleSchema.safeParse` calls — a missing `domains` throws a raw `TypeError`, an invalid `depth` enum silently becomes `depth:undefined` with no error. Three independent unguarded `.map()` calls crash with bare `TypeError`s on wrong-typed array fields at S5→S6 (`plan.tool_calls`), S6→S7 (`plan.asset_bundle`), and S7→S8 (`bundle.assets`). At S9→S10, `buildCanonicalParts`'s `for (const b of input.committedBlocks)` has no `Array.isArray` guard — a string input iterates per-character (JS's iterable protocol), producing a plausible-looking, silently empty result rather than an error. Score across all 10 boundaries: 1/10 has a real, actively-enforced runtime schema gate; 0/10 refuse a malformed object at their own entry point with a purpose-built check (two graceful cases at S5→S6/S6→S7 are incidental byproducts of unrelated registry/floor-asset presence logic, not boundary validation). Boundary 1 (S1→S2, `authorizeTurn`) could not be fully exercised in this sandbox (no DB route) and is flagged NOT FULLY TESTED rather than assumed safe.
- **Code anchor:** `platform/src/lib/pipeline/compiled_floor_adapter.ts:86-121`; `platform/src/lib/pariprashna/pipeline/evidence_stage.ts:68-70`; `platform/src/lib/bundle/bundle_hydrator.ts:66-67`; `platform/src/lib/pariprashna/pipeline/synthesis_stage.ts:241-244`; `platform/src/lib/pariprashna/pipeline/reading_parts.ts:565-591`; `platform/src/lib/pariprashna/pipeline/safety_gate.ts:237` (B1, tentative).
- **PPR/gap cross-reference:** PROJECT_ARCHITECTURE §3 ("a malformed object never crosses" boundary claim).
- **Proposed fix class:** call `ScopeTupleSchema.safeParse` (or equivalent) at the top of `compileFloorForPlan`; add a shared lightweight `PipelineBoundaryError`-style array/shape guard at each S5-S8 entry point; add an explicit `Array.isArray` guard to `buildCanonicalParts`; re-run Boundary 1 from an environment with real DB access.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session for 9/10 boundaries; Boundary 1 needs a DB-reachable environment).

### V3-E-041 — S2 entitlement-denial and consent-refusal codes are misclassified client-side as a generic transient "something failed on our side" error

- **Class / severity:** DEFECT · S1 (proposed) — safety/consent-adjacent: `SUBJECT_CONSENT_REQUIRED` is a PPR-14 consent refusal routed through the same misclassification
- **Lens(es) / pipeline stage:** synergy/degradation-honesty · S2
- **Expected:** an entitlement/consent refusal should be disclosed as what it is, with an action set that does not suggest retrying will help.
- **Observed (2026-08-28, INTEGRATION, real `classifyPariprashnaError`, 4/4 proven):** `safety_gate.ts`'s `authorizeTurn` emits `em.error({code:'FORBIDDEN'|'CHART_NOT_FOUND'|'SUBJECT_CONSENT_REQUIRED:<reason>'|'CONVERSATION_NOT_FOUND', message, ...})`. The client's `s1LiveAdapter.ts:335-341` routes every `error` event through `classifyPariprashnaError(ev.code)`, discarding `ev.message` (server/log-side only). `classify.ts`'s `classifyKind()` has no case for any of these four codes — all fall to `'unknown'` → "Something failed on our side… the plumbing. It is logged." with `actions:['retry']`. Proven by 4/4 real tests: each code asserts `kind:'unknown'` + the generic copy.
- **Code anchor:** `platform/src/components/pariprashna/state/s1LiveAdapter.ts:335-341`; `platform/src/lib/pariprashna/errors/classify.ts:112-124` (`classifyKind()`).
- **PPR/gap cross-reference:** PPR-11, PPR-14; sibling of V3-E-013's flag/disclosure-decoupling class.
- **Proposed fix class:** add explicit `kind`s (e.g. `'not_authorized'`, `'not_found'`, `'consent_required'`) to `classifyKind`/`copyFor` with non-retry actions, or forward a safe subset of `ev.message` for these business-logic codes.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session — 4/4 passing vitest run against real `classifyPariprashnaError`).

### V3-E-042 — `grade`/`flag` wire events for completeness and citation-gate signals are dropped or reducer-inert; the tool-activity UI has no rendering state for an errored tool either

- **Class / severity:** DEFECT · S2 (proposed)
- **Lens(es) / pipeline stage:** synergy/degradation-honesty · S6/S9
- **Expected:** a `grade` event carrying a real degradation signal, or a `flag` event marking a B.11 grounding-validation failure, should reach visible or at least reducer-tracked client state; a failed/timed-out tool should render distinguishably from a running one.
- **Observed (2026-08-28, INTEGRATION, direct code read confirmed for all three claims):** `s1LiveAdapter.ts:273-282`'s `case 'grade': if (ev.subject !== 'reading_depth_received') return []` discards every OTHER grade subject before the reducer ever sees it — including `completeness` (S6) and `citation_gate` (S9). `reducer.ts:290-292`'s `case 'flag'` only updates `lastEventId`/`seenEventIds` for a `citation_gate_warn`/`citation_gate_error` flag — no visible UI state results. Separately, `ActivityRow.tsx:13-17` renders the glyph/color purely from `row.status==='done'`, with NO branch for `status:'error'` — an errored or timed-out tool (see V3-E-031) renders pixel-identical to one still running or not yet started. Together: a real B.11 grounding-validation failure or a real tool-dispatch gap can be correctly detected and emitted server-side and still never become visible to the reader.
- **Code anchor:** `platform/src/components/pariprashna/state/s1LiveAdapter.ts:273-282`; `platform/src/components/pariprashna/state/reducer.ts:290-292`; `platform/src/components/pariprashna/activity/ActivityRow.tsx:13-17`.
- **PPR/gap cross-reference:** B.11; sibling of V3-E-013/V3-E-039.
- **Proposed fix class:** route non-`reading_depth_received` grade subjects into reducer-tracked (even aggregated) state; route citation-gate flags into `judgmentFlags`/an existing visible grounding-quality indicator (`GroundingCard`); add an explicit error-state render branch to `ActivityRow.tsx`.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session — direct code read of all three code paths).
- **Cross-stream referral (2026-08-28):** the client-side rendering fix (`s1LiveAdapter.ts`, `reducer.ts`, `ActivityRow.tsx`) is UI/surface territory, not S4's pipeline territory — referred to **S1** (Navigation, Shell & History) per elevation §8.3; S4 does not fix cross-territory.

### V3-E-043 — Three independent, mutually-disjoint telemetry/persistence systems back "the" 11-stage pipeline depending on which of three live routes serves the turn; no single trace_id joins stages across doors

- **Class / severity:** DEFECT · S2 (proposed) — the crux of the "one trace_id joins all 11 stages plus both doors' persistence" requirement is false as built
- **Lens(es) / pipeline stage:** synergy/trace-coherence, Door parity · CROSS
- **Expected:** one trace_id joins Portal + MCP persistence for the same logical turn.
- **Observed (2026-08-28, INTEGRATION local-dev + STATIC, 3 real turns driven through a real Firebase-authenticated local server + real DB):** `POST /api/chat/consult` (the live-default Consume chat UI) writes to `query_trace_steps`. `POST /api/pariprashna` (a separate, `PARIPRASHNA_ENABLED`-gated route implementing the exact stage-named files the charter's S1-S11 anchor table cites) writes to a completely disjoint typed-SSE/Redis-ring-buffer/optional-DB-capture system. The MCP door (`prashna_ask`) is a third, independent case: its `trace_id` is a bare `crypto.randomUUID()` used only for a few writer calls, never touching `query_trace_steps` (grep-confirmed zero references). No shared table or key links any two of the three doors' records for the same logical question.
- **Code anchor:** `platform/src/lib/trace/{emitter,writer}.ts` (consult); `platform/src/lib/pariprashna/protocol/{emitter,ring_buffer,stream_capture}.ts` (pariprashna); `platform/src/app/api/mcp/prashna_ask/route.ts:251` (MCP).
- **PPR/gap cross-reference:** door-parity, trace-coherence.
- **Proposed fix class:** either converge on one persistence surface, or add an explicit cross-reference column/table joining `query_trace_steps.query_id` ↔ `pariprashna_stream_capture.turn_id` ↔ MCP `trace_id`.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session — 2 routes tested live, 3rd confirmed via exhaustive static grep).

### V3-E-044 — S2/S3 entitlement and safety decisions run before the consult route's trace_id exists; a refused turn has zero forensic trail

- **Class / severity:** DEFECT · S2 (proposed) — the security-relevant refusal path is the one case with literally no trace record
- **Lens(es) / pipeline stage:** synergy/trace-coherence, safety-observability · S2/S3
- **Expected:** every admitted-or-refused turn correlates to a stable id from the moment entitlement/safety checks run.
- **Observed (2026-08-28, INTEGRATION + STATIC, structural code-order fact confirmed on the real route):** `authorizeChartAccess()` (`consult/route.ts:362`) and `classifyTurnSafety()` (`:476`) both run BEFORE `preAllocatedQueryId` is minted (`:531`); a refusal returns before that line is ever reached (`:512-516`). An admitted turn leaves no positive telemetry record of the decision having run either — no row in any query_id-keyed table for either decision.
- **Code anchor:** `platform/src/app/api/chat/consult/route.ts:362,476,512-516,531`.
- **PPR/gap cross-reference:** trace-coherence, PPR-11/PPR-12.
- **Proposed fix class:** mint the trace_id at request entry, before authz/safety, and emit `step_start`/`step_done` rows for both decisions using it — including on the refusal path.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session, 1 real live turn) + STATIC (structural fact, not turn-dependent).
- **Cross-stream referral (2026-08-28):** the fix reorders code around `authorizeChartAccess()`/`classifyTurnSafety()` — S4 does not touch auth/safety-gating logic per its scope boundary — referred to **S5** (Security, Privacy & Data Integrity).

### V3-E-045 — On `/api/pariprashna`, the wire-visible `turn_id` and the durably-persisted `conversation_messages.metadata_json.custom.queryId` for the same turn are two different, independently-generated UUIDs

- **Class / severity:** DEFECT · S3 (proposed)
- **Lens(es) / pipeline stage:** synergy/trace-coherence · S11
- **Expected:** the id a caller receives on the wire should be the id that resolves the persisted record.
- **Observed (2026-08-28, INTEGRATION, live, reproduced in 2/2 test turns):** the SSE wire identifies the turn by `turn_id` (`turn.open`/`turn.commit`/`turn.close`/`receipt.define` all key off it), but `conversation_messages.metadata_json.custom.queryId` for that same turn's message is a different, independently-generated UUID (`route.ts:104-105`, two separate `crypto.randomUUID()` calls). A caller holding only the wire `turn_id` cannot look up the persisted message by that id directly.
- **Code anchor:** `platform/src/app/api/pariprashna/route.ts:104-105`.
- **PPR/gap cross-reference:** trace-coherence.
- **Proposed fix class:** derive `queryId` from `turnId` (or persist `turnId` alongside it) so a caller can join wire events to the persisted row with one id.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session — live, reproduced twice).
- **Resolved (2026-08-29, resume session):** MERGED — PR [#1644](https://github.com/Marsys-Technologies/Madhav/pull/1644), independently verified ACCEPT (verifier normalized UUIDs across all 31 regenerated baseline fixtures — byte-identical, zero non-UUID structural change; reverted only the baselines with the code fix kept, confirmed 31/31 failures land exclusively on id fields; collision risk re-verified via `pending_streams` `ON CONFLICT` semantics — none introduced; 568/568 broader regression).

### V3-E-046 — Pre-synthesis bundle-level validation on the consult route has zero telemetry regardless of outcome

- **Class / severity:** DEFECT · S3 (proposed)
- **Lens(es) / pipeline stage:** synergy/trace-coherence · S9
- **Expected:** a trace-queryable record of the bundle-validation pass/fail decision.
- **Observed (2026-08-28, INTEGRATION, live turn):** `bundleSummary` (`runAll(bundle,'bundle',…)`) is computed and used only to gate an inline 422 response on `consult/route.ts`; it is never persisted, pass or fail.
- **Code anchor:** `platform/src/app/api/chat/consult/route.ts:1015-1022`.
- **PPR/gap cross-reference:** trace-coherence.
- **Proposed fix class:** emit a trace step (or audit_log row) for this validation regardless of pass/fail.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session).

### V3-E-047 — S10 (SemanticReadingParts) and S11 (AcharyaReadingReceipt) do not exist on the live-default `/api/chat/consult` path; both are gated behind flags that default off

- **Class / severity:** PROCESS · S4 (proposed, informational/scope-config) — may be working-as-designed (rollback gate) rather than a defect; flagged for owner triage
- **Lens(es) / pipeline stage:** synergy/trace-coherence, pipeline-stage-coverage · S10/S11
- **Expected/observed (2026-08-28, INTEGRATION, flags forced on locally):** `reading_parts.ts`/`block_classifier.ts` are imported only by `/api/pariprashna` and sibling `pariprashna/pipeline/*` files, never by `/api/chat/consult` — on the live default path these stages, as named, do not run at all (the consult route consumes plain AI-SDK text parts instead). `/api/pariprashna` itself is gated `PARIPRASHNA_ENABLED` (default `false`); its receipt sub-feature needs a second, also-default-off flag `PARIPRASHNA_RECEIPT_EMISSION_ENABLED`. Both confirmed live once forced on locally; never confirmed against the actual deployed environment's flag state (out of scope this session).
- **Code anchor:** `platform/src/lib/config/feature_flags.ts:170,356,523,572`.
- **PPR/gap cross-reference:** cross-reference V3-E-048/V3-E-049 (the same flag governs whether MCP-vs-Portal receipt comparison is even meaningful).
- **Proposed fix class:** none required — recommend the owning verifier confirm production flag state and grade whether this is a deliberate rollout gate.
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session, local flags forced on) → LIVE (confirm actual deployed flag state, not done this session).

### V3-E-048 — MCP `prashna_ask` has no call path to receipt assembly at all: no in-memory `AcharyaReadingReceipt` object is ever constructed for this door, even transiently

- **Class / severity:** DEFECT · S2 (proposed) — additive to the already-tracked P2-B-004/E-119 persistence gap, not a restatement of it
- **Lens(es) / pipeline stage:** synergy/cross-door-parity (PPR-30) · S11 · **Journey:** J10
- **Provenance:** additive to P2-B-004 / E-119 (`MCP_TURN_PERSISTENCE_NONE`) — cite that item as shared root cause, do not treat this as an independent new root cause.
- **Expected:** a whole-receipt parity check (PPR-30) should compare two doors that both *can* emit the same structured object.
- **Observed (2026-08-28, code-level comparison — deployed images confirmed stale, so LIVE dual-door was not attempted; the divergence is architectural, not data-dependent):** `grep -rn "assembleAcharyaReadingReceipt|runPersistenceStage"` across `platform-mcp/src` and the MCP route returns zero matches. Traced counterfactually with `PARIPRASHNA_RECEIPT_EMISSION_ENABLED=true` (the only state under which "whole-receipt parity" means anything, since Portal itself ships this flag dark-by-default too — see V3-E-047): under that condition Portal assembles a full receipt; MCP still assembles none — the flag is never referenced on the MCP door at all, so flipping it does nothing there. All 18 top-level receipt fields diverge (`receipt_schema_version`, `turn_id`, `conversation_id`, `chart_id`, `generated_at`, `coverage`, `facts_consumed`, `derivation_chains`, `cross_domain`, `evidence_grades`, `honest_gaps`, `calibration_disclosure`, `prose_binding`, `provenance`, `interpretation_sets`, `confidence_typing`, `receipt_hash`, and `safety_decision` — the last one filed separately as V3-E-049) — trivially absent rather than differently-valued. The single cheapest available fix identified: `cross_domain`/`plan.domains` is already computed in MCP request scope (used internally for `ensureB11WholeChartReadFloor`) but never written to the response envelope — pure wiring gap, no new computation needed. `coverage`'s Portal-side schema also hardcodes `channel: z.literal('web')`, which would need to become a non-literal enum before MCP could ever populate it honestly, independent of the call-path gap.
- **Code anchor:** `platform/src/app/api/mcp/prashna_ask/route.ts` (no import of `receipt/assemble.ts` or `pipeline/persistence_stage.ts`, confirmed by grep); `platform/src/lib/config/feature_flags.ts:344-356,572`; `platform/src/lib/pariprashna/pipeline/persistence_stage.ts:504-505`; `platform/src/lib/pariprashna/receipt/schema.ts:44-54` (`channel` literal).
- **PPR/gap cross-reference:** PPR-30; provenance P2-B-004/E-119.
- **Proposed fix class:** either (a) MCP door onboards a receipt-assembly call site gated by the same flag (with the individual cheap wins — `cross_domain`, `safety_decision` per V3-E-049 — landing first, independent of the full assembler), or (b) explicitly re-scope PPR-30's receipt-parity doctrine as "Portal-only, not a cross-door contract" until (a) lands.
- **Status:** OPEN · verification rung required to close: code-level comparison (fallback rung achieved this session — architectural absence, confirmed by exhaustive grep, not data-dependent so a live dual-door run would not change the finding).

### V3-E-049 — The full structured `SafetyDecision` object is computed on the MCP door but discarded; only lossy string flags reach the wire, dropping the exact FK fields (`decision_id`/`review_id`/`audit_written`) an auditor needs

- **Class / severity:** DEFECT · S1 (proposed) — safety-relevant audit field, flagged highest of the 18 receipt-field findings: the underlying object genuinely exists in MCP's own request scope, and the gap specifically drops the audit trail's join keys
- **Lens(es) / pipeline stage:** synergy/cross-door-parity (PPR-30), Correctness · S11 (also S-safety) · **Journey:** J10
- **Provenance:** additive to P2-B-004 / E-119; sibling of V3-E-048.
- **Expected:** `safety_decision.{status, decision_id, enforced, severity, action, classes_detected, review_id, audit_written}` on both doors — the MCP door's own route comment states this gate is deliberately mirrored from the web door.
- **Observed (2026-08-28, code-level comparison):** `classifyTurnSafety`/`reclassifyAfterPlan` genuinely run on the MCP door (`route.ts:356-361,483-491`) and gate dispatch/strip capabilities, but the final envelope only ever emits derived, lossy string flags (`safety_decision:<action>`, `safety_mortality_capabilities_excluded`, `safety_classes_detected:<n>`). The structured object itself — including `decision_id` and `review_id`, the FK fields an auditor would follow to `pariprashna_safety_decisions` — is discarded, not attached to the response.
- **Code anchor — Portal:** `platform/src/lib/pariprashna/receipt/assemble.ts:236-261` (`buildSafetyDecision`), `receipt/schema.ts:153-164`. **— MCP:** `platform/src/app/api/mcp/prashna_ask/route.ts:356-361,483-530` (`postPlanSafety`/`reclassifyAfterPlan`/`applyCapabilityExclusion`), `:511-516,769-788` (only string flags reach the wire).
- **PPR/gap cross-reference:** PPR-30; PPR-12.
- **Proposed fix class:** near-zero-cost — `postPlanSafety` already exists in scope at the point `readingEnvelope` is constructed; add a `safety_decision: buildSafetyDecision(postPlanSafety)`-equivalent key to the MCP envelope, reusing Portal's own builder shape. This does not require V3-E-048's full receipt-assembly wiring to land first.
- **Status:** OPEN · verification rung required to close: code-level comparison (fallback rung achieved this session) → INTEGRATION (a live MCP turn with the fix applied, showing the structured object on the wire).

### V3-E-050 — Portal door's progress-reporting architecture does NOT reproduce E-003; scope E-003 to the MCP door only

- **Class / severity:** IMPROVEMENT / DOC · S4 (proposed, informational/parity-closure)
- **Lens(es) / pipeline stage:** synergy/progress-truthfulness, Door parity (PPR-30) · CROSS
- **Expected:** per the PPR-30 doctrine, the register should explicitly record when two doors do NOT share a defect, so a single-door finding isn't mistakenly read as whole-product.
- **Observed (2026-08-28, STATIC — code trace only; no live browser turn run this session, `getServerUser()`'s real Firebase-session cost was judged out of budget):** Portal's `working/WorkingBand.tsx` elapsed counter is a pure client `setInterval` wall-clock tick, independent of server event cadence — it cannot freeze mid-turn the way the MCP door's cached `JobProgress` object can, by construction. Synthesis genuinely streams continuously (`text_delta`→`block.delta` events for the whole duration), the opposite shape of the MCP door's single unmonitored `await`. `currentLiveLabel()` picks up the `phase{synthesize,start}` event immediately, giving a fresh label before the freeze window that afflicts MCP would even begin. One number remains unmeasured: the exact TTFT-vs-band-label-update gap (architecturally bounded by ordinary LLM time-to-first-token, not measured live this session).
- **Code anchor:** `platform/src/components/pariprashna/working/WorkingBand.tsx` (`useElapsedSeconds`, `currentLiveLabel`); `platform/src/lib/pariprashna/pipeline/synthesis_stage.ts` (continuous `text_delta`→`block.delta` emission).
- **PPR/gap cross-reference:** PPR-30; parity counterpart to V3-E-012 (E-003).
- **Proposed fix class:** none required functionally; annotate E-003/V3-E-012 as MCP-door-scoped; confirm the unmeasured TTFT gap with live Portal browser access in a future pass.
- **Status:** OPEN · verification rung required to close: STATIC (already achieved this session) → LIVE (a real browser/Firebase-session turn, not attempted this session — deliberately, per the honesty caveat above).

### V3-E-051 — Scope-classifier "faithful port, do not diverge" contract has silently broken: three independent fix waves each landed on only one door

- **Class / severity:** DEFECT · S2 (proposed) — structural, affects every query through the standalone MCP classifier tools and any caller threading a pre-classified tuple back into `prashna_ask`
- **Lens(es) / pipeline stage:** Correctness, Door parity (PPR-30) · S1
- **Expected:** `intent_scope_classifier.ts` (MCP) and `scope_classifier.ts` (Portal) compute identical `scope_tuple` fields for identical input, per the Portal file's own docstring ("faithful port… do not diverge").
- **Observed (2026-08-28, REPLAY/INTEGRATION, 19-query representative set through both classifiers directly):** 19/19 queries diverged on at least one `scope_tuple` field. Three independent fix waves each landed on only one side: (1) MCP implements the Ω4 "earned-narrow, default-deep" width/depth doctrine (`route`, `narrow_confidence`, `depth_available` fields); Portal still implements the pre-Ω4 keyword-only model, default `standard`/`standard` — universal across all 19 queries. (2) Portal's W6.1 domain-inferred-intent fallback was never ported to MCP: `"What is my career direction and its timing over the next few years?"` resolves `intent:domain_assessment` on Portal but `intent:unknown, fallback_recommended:true` on MCP — a real clarification-outcome flip, demonstrated with a real RED vitest run against MCP's classifier (the exact defect class Portal's own W6.1 fix was built to close, referencing a real prior live E2E incident, trace `6d1eb827-…`). (3) MCP's F-24 plural-safety `DOMAIN_RULES` fix was never ported to Portal: `"What is my finances outlook?"` resolves `domains:['wealth']` on MCP but `domains:['general']` on Portal (same for "relationships" → `marriage`/`general`).
- **Code anchor:** `platform-mcp/src/tools/intent_scope_classifier.ts:212-350` (Ω4 apparatus, no Portal counterpart), `:182-193` (F-24 plural-safe `DOMAIN_RULES`); `platform/src/lib/vidhi/scope_classifier.ts:1-27` (the "do not diverge" docstring), `:241-254` (W6.1 fix, no MCP counterpart), `:164-175` (unfixed singular-only `DOMAIN_RULES`), `:256-265` (width/depth logic).
- **PPR/gap cross-reference:** PPR-30.
- **Proposed fix class:** port the Ω4 doctrine and the W6.1 domain-inferred-intent fallback to MCP's classifier verbatim; port the F-24 plural-safe `DOMAIN_RULES` to Portal verbatim; add a cross-door parity test so future drift is CI-caught (nothing today asserts cross-door equality — both `.test.ts` suites pass in isolation).
- **Status:** OPEN · verification rung required to close: REPLAY/INTEGRATION (already achieved this session — real vitest run against real source for the RED demonstration; direct unit-level function calls, real regex tables, for the 19-query parity sweep).

### V3-E-052 — No independent classification-accuracy corpus exists for the scope classifier on either door

- **Class / severity:** BASELINE / IMPROVEMENT · S3 (proposed)
- **Lens(es) / pipeline stage:** Optimality · S1
- **Expected:** a classifier this central to routing would ideally be measured against an independently-labeled corpus with a tracked accuracy number over time.
- **Observed (2026-08-28, REPLAY, test-suite inspection):** the only "accuracy" evidence is 37 (MCP) / 10 (Portal) hand-written unit-test cases, each asserting the classifier's output against its OWN regex tables — no independent ground truth. Both classifiers are effectively free latency-wise (sub-hundredth-of-a-millisecond, p95 ≤0.0082ms MCP / ≤0.0054ms Portal) — latency is not the concern; measured accuracy is the gap.
- **Code anchor:** `platform-mcp/src/tools/intent_scope_classifier.test.ts`; `platform/src/__tests__/lib/vidhi/scope_classifier.test.ts`.
- **PPR/gap cross-reference:** none specific.
- **Proposed fix class:** author a small independently-labeled fixture corpus (50-100 queries spanning all 11 intents × ambiguous/adversarial cases), checked in and run in CI as a standing accuracy gate, separate from the regex-table unit tests.
- **Status:** OPEN · verification rung required to close: REPLAY (already achieved this session — test-suite inspection + latency bench).

### V3-E-053 — Redundant `charts` table round-trip inflates every S2 entitlement decision by roughly 2x

- **Class / severity:** IMPROVEMENT (performance) · S3 (proposed, Low-Medium)
- **Lens(es) / pipeline stage:** Optimality · S2
- **Expected:** one round-trip to `charts` per turn to resolve both existence and ownership.
- **Observed (2026-08-28, INTEGRATION, real `authorizeChartAccess` calls over the live Cloud SQL Auth Proxy tunnel, real synthetic-chart rows):** `authorizeTurn` runs `SELECT id, name, client_id FROM charts WHERE id=$1` for the `CHART_NOT_FOUND` check, then calls `authorizeChartAccess`, which independently runs its own `SELECT owner_id FROM charts WHERE id=$1` against the same table/row — two sequential round trips to `charts` for the same `chart_id` on every turn, plus a `profiles` lookup in between (3 sequential DB round trips before `authorizeChartAccess` even reaches its own branch). Measured: full `authorizeTurn`-shaped sequence p50=326.3ms (deny) vs `authorizeChartAccess` alone p50=154.9ms — roughly 2x inflation of the fail-closed hot path.
- **Code anchor:** `platform/src/lib/pariprashna/pipeline/safety_gate.ts:237-245`; `platform/src/lib/auth/authorizeChartAccess.ts:56-67`.
- **PPR/gap cross-reference:** none specific.
- **Proposed fix class:** have `authorizeTurn` pass its already-fetched chart row (or just `owner_id`) into `authorizeChartAccess` so it never re-queries `charts`, or combine the existence + ownership check into one query. Local to this one caller — not a change to `authorizeChartAccess`'s public contract used identically elsewhere (`invoke_tool.ts`).
- **Status:** OPEN · verification rung required to close: INTEGRATION (already achieved this session — measured against real DB via real proxy).
- **Cross-stream referral (2026-08-28):** the fix touches `authorizeTurn`'s entitlement hot path (auth-adjacent); S4 does not modify auth-path code per its scope boundary — referred to **S6** (Performance, Resilience & Observability) for perf ownership, coordinating with S5 if the auth-path change itself needs security sign-off.

### V3-E-054 — SafetyPolicyDecision gate (HS-1..HS-4) ships flag-OFF by default; zero live enforcement until an operator flips the feature flag

- **Class / severity:** DEFECT (configuration-risk, not a code defect) · S2 (proposed)
- **Lens(es) / pipeline stage:** Correctness, Failure-honesty · S3
- **Expected:** per PPR-12/MP §3.5.C and the module's own doc comments, HS-1..HS-4 should be an active, live-enforced safety-critical hard-stop mechanism.
- **Observed (2026-08-28, static code read + config read):** `feature_flags.ts:546`: `PARIPRASHNA_SAFETY_GATE_ENABLED: false`; no override found in `platform/.env.local`. With the flag off, `classifyTurnSafety` returns `enforced:false, action:'proceed'` before running a single pattern and before touching the database (confirmed by the flag-OFF benchmark: 0 DB calls, sub-microsecond). This is documented as a deliberate ship-dark decision ("the flip is a deliberate act at P1 close"), but as shipped by default, none of HS-1..HS-4 are enforced in production — no question is classified, no hard-stop fires, no capability is excluded, no review is opened, unless `MARSYS_FLAG_PARIPRASHNA_SAFETY_GATE_ENABLED=true` is set. The mechanism itself is correct and well-tested (680 passing unit tests across 6 HS classes including HS-5/HS-6) — this is a deployed-state finding, not a code-correctness one.
- **Code anchor:** `platform/src/lib/config/feature_flags.ts:546`; `platform/src/lib/pariprashna/safety/flag.ts:23-27`.
- **PPR/gap cross-reference:** PPR-12.
- **Proposed fix class:** not a code fix — confirm with the native whether P1 close (the flip point named in the flag's own doc comment) has occurred, and if not, track it explicitly as an open operational item.
- **Status:** OPEN · verification rung required to close: static code read + config read (already achieved this session) → LIVE (confirm actual deployed flag value, out of this lane's authorized scope this session).
- **Cross-stream referral (2026-08-28):** an unverified-off safety hard-stop mechanism is a certification-blocking security/safety posture question, not a pipeline-correctness fix — referred to **S5** (Security, Privacy & Data Integrity) to confirm deployed flag state and escalate to the native if still off.

### V3-E-055 — WEB door (`/api/pariprashna`) has zero route-level test coverage for the S3 safety short-circuit

- **Class / severity:** DEFECT (test-coverage gap) · S2 (proposed)
- **Lens(es) / pipeline stage:** Correctness, Demonstrated-can-fail · S3
- **Expected:** a route carrying a safety-critical short-circuit should have at least one route-level test proving the short-circuit renders on ITS wire format, parallel to what the MCP door's `prashna_ask` route test already does (HS-2 hard-stop, seal path, plan-time escalation, floor test).
- **Observed (2026-08-28, exhaustive grep + static read):** `src/app/api/pariprashna/` has no `__tests__` directory at all; the golden-stream baseline corpus (30 scenario JSONs) contains none matching `safety|hard_stop|hs1|hs2|hs3|hs4|seal_pending`. The safety module's own unit tests (680 tests) and a consult-door test (7 tests) are thorough and green, but nothing proves `runSafetyPolicyGate`'s `speak()` calls actually reach the SSE wire for THIS route, and the post-plan escalation branch (`route.ts:186-199`) is unique to this route and untested anywhere — not exercised by the safety module's own unit tests, which stop at `reclassifyAfterPlan`'s return value.
- **Code anchor:** `platform/src/app/api/pariprashna/route.ts:153-199`; missing counterpart of `platform/src/app/api/mcp/prashna_ask/__tests__/route.test.ts:739-838`.
- **PPR/gap cross-reference:** PPR-12; door parity.
- **Proposed fix class:** add 1-2 golden-stream baseline scenarios (or a small dedicated route test) flipping `PARIPRASHNA_SAFETY_GATE_ENABLED` on and asserting the HS-2 fixed text + a `safety_decision:*` judgment flag appear verbatim in the SSE stream, plus one scenario exercising the post-plan escalation branch specifically.
- **Status:** OPEN · verification rung required to close: static code read + exhaustive grep (already achieved this session) → INTEGRATION (the new test landing and passing).
- **Resolved (2026-08-29, resume session):** MERGED — PR [#1645](https://github.com/Marsys-Technologies/Madhav/pull/1645), independently verified ACCEPT via mutation testing (verifier hardcoded a stale duplicate response string, neutered the escalation condition, and removed the early return so evidence-stage would silently run — the tests correctly failed in each case, proving the assertions are load-bearing, not tautological). Test-only, zero production code touched. 2599+ broader suite pass.

---

*End EDIR_V3_REGISTER v1.1 — 115 historical entries imported by reference;
81 branches dispositioned (SUPERSEDED 70 · ARCHIVE 7 · EVIDENCE-ONLY 2 ·
SALVAGE 2); 55 V3 entries total (5 from the A3 census + 6 surfaced during
A4's B-001/B-007/B-008 fix-and-verify chain, 2026-08-27 [V3-E-006/B-007 and
the B-008 CRITICAL routes fixed and independently verified, V3-E-007/E-008/
E-010/E-011 filed to S5, V3-E-009 closed-as-benign] + 44 from the S4 Pipeline
Correctness & Door Parity stream, 2026-08-28 [V3-E-012..E-055; 17 parallel
agents covering the 11 pipeline stages S1-S11 plus 6 synergy tests including
journey J10; several reaching LIVE rung against the synthetic chart]). No
gate is certified by this document.*

---

### V3-E-S4-PROC-001 — Cross-stream `V3-E-0NN` numbering collision: parallel streams independently claimed the same entry numbers for unrelated findings

- **Class:** PROCESS
- **Severity:** S2 (proposed — Native Surrogate/Programme Integrator to confirm; this affects register/tracker integrity, not the product)
- **Lens(es):** governance / register integrity
- **Pipeline stage:** N/A (campaign infrastructure)
- **Expected:** the EDIR_V3 register's append-only `V3-E-nnn` sequence is a single, non-colliding numbering scheme across the whole v3 campaign (elevation §6.4).
- **Observed (2026-08-28):** this entry number was deliberately chosen OUT of the normal numeric sequence (`V3-E-S4-PROC-001` rather than the next integer) because the normal sequence is confirmed colliding. S4 filed `V3-E-012..V3-E-055` on its own branch (commit `0ba0021c8`, based on the register state at S4's session open). Independently, and concurrently, sibling streams S1/S2/S3/S5 filed their OWN entries under overlapping numbers on their own branches — confirmed directly: `origin/main`'s CURRENT `V3-E-013` (post a merged S1 PR, commit range including `61a6dc4f8`) is *"`POST`/`GET /api/conversations` created/listed chart-scoped rows with no `chart_grants`/ownership check (S1-F-001) — FIXED + INDEPENDENTLY VERIFIED"* — an entirely different finding from S4's own `V3-E-013` (*"Evidence-truncation disclosed only in `judgment_flags`..."*, E-004 reproduction). Separately, the accepted tracker's `finding_discovered` event type enforces a GLOBALLY unique `finding_id` (not scoped per stream); a live probe against the tracker (2026-08-28, S4 Tracker Ops lane) confirmed `V3-E-012` through `V3-E-024` and `V3-E-031` are already claimed by `lead-s2`/`lead-s3`/`lead-s5` for unrelated findings, rejecting S4's identical-numbered `finding_discovered` attempts with `FINDING_ID_CONFLICT`.
- **Root cause:** the register's numbering law (elevation §6.4, test plan §6.3) specifies an append-only sequence but does not specify a cross-branch/cross-stream allocation mechanism — six parallel streams each independently computed "highest number I see on my own branch + 1" with no shared allocator, guaranteeing collision the moment more than one stream files new entries in the same session.
- **What this session did NOT do, and why:** did not unilaterally renumber S4's own 44 entries to dodge sibling streams' current numbers — the sibling streams are still running and filing more entries as of this observation, so any snapshot-based renumbering would itself go stale within the same session, and silently renaming finding ids would break the fixer/verifier work this session already produced referencing them (commit `077cd16c7` et al. cite `V3-E-013` in their own commit messages). This is a call for the Programme Integrator / Session C convergence, not a stream-local fix.
- **Workaround adopted this session:** S4's tracker `finding_discovered`/`finding_triaged` events use collision-safe ids prefixed `S4-V3-E-0NN` (e.g. `S4-V3-E-012`) for the tracker's global `finding_id` field ONLY; the EDIR register entries themselves keep their original `V3-E-0NN` numbers unchanged (renumbering the register is Session C's job, not a mid-stream edit).
- **Proposed fix class:** at Session C convergence, adopt a stream-prefixed permanent numbering scheme (e.g. `V3-E-S1-0NN` / `V3-E-S4-0NN`) for all six streams' entries going forward, OR have the Programme Integrator serialize entry-number allocation through the tracker itself (a `finding_id` reservation event) rather than each stream computing its own next-number locally.
- **Status:** OPEN · verification rung required to close: PROCESS (documentation/convergence-time reconciliation, no code fix applicable).

### V3-E-S4-PROC-002 — Tracker's `result_packet_accepted`/CG-3 gate requires ALL triaged findings VERIFIED, not just the findings a stream selected for same-session remediation — conflicting with the elevation's own endorsed partial-scope model

- **Class:** PROCESS
- **Severity:** S2 (proposed — Programme Integrator/native to confirm; blocks formal tracker closure credit for every stream, not just S4)
- **Lens(es):** governance / tracker schema
- **Pipeline stage:** N/A (campaign infrastructure)
- **Expected:** `AUTONOMOUS_EXECUTION_ELEVATION_v1_0.md` §8.1's shared elevated frame explicitly endorses partial-scope remediation ("Land fixes, don't just file findings — where a fix is in YOUR territory... land it this session; only cross-territory findings are referral-only") and the register law explicitly allows `DEFER_OPEN_S4`/`REFER_S*`/`ALREADY_TRACKED`/`NO_ACTION_NEEDED` as legitimate terminal dispositions for a finding within one stream's session. A stream should be able to receive result-packet/CG-3 closure credit for the scope it actually completed (54/54 chartered scenarios executed, 44/44 findings triaged, N of 44 remediated-and-verified with the rest honestly dispositioned as deferred/referred/tracked-elsewhere) without being required to remediate every single triaged finding in one session.
- **Observed (2026-08-28, live tracker interaction, S4's actual closure attempt):** `control.py`'s `remediation_approved` schema (line ~588) requires the frozen plan to "account for every triaged stream finding" — so a stream with 44 findings must submit a 44-entry plan even if only a handful are same-session-fixable (confirmed: S4's plan carries 6 real remediation entries + 38 explicit "no remediation implemented — disposition: X" entries). Separately, and more restrictively, the `S4:remediation` work-item-acceptance gate (line ~552-554) requires **every** entry in that frozen plan — all 44, not just the 6 actually planned for implementation — to reach `VERIFIED` status before the work item (and therefore `result_packet_accepted`, and therefore CG-3 per its own `packets != {all stream ids}` check) can be accepted. Live result: S4's `S4:remediation` work-item-acceptance was rejected `409 REMEDIATION_INCOMPLETE` naming the 38 intentionally-deferred/referred finding ids as "incomplete," even though those 38 were never claimed to be same-session work.
- **Code anchor:** `00_ARCHITECTURE/briefs/pariprashna_assurance/tracker/control.py` lines ~550-554 (`REMEDIATION_INCOMPLETE` check against the full frozen plan) and ~588 (`REMEDIATION_PLAN_SCHEMA` "must account for every triaged stream finding").
- **What this session did NOT do, and why:** did not fabricate `verification_accepted` events for the 38 un-remediated findings to force `result_packet_accepted` through — that would be exactly the "unearned green" §N.8 forbids, faking verification of work that was never done. Did not edit `control.py`'s business logic unilaterally — the tracker is shared campaign infrastructure other streams also depend on concurrently; a stream-local schema change is out of S4's territory and risks breaking other streams' in-flight event sequences.
- **Impact:** every one of the six P3 streams will likely hit this same gate at their own closure, since the elevation's whole model assumes streams triage more findings than they remediate in one session. This is not S4-specific.
- **Proposed fix class:** either (a) split the `remediation` work-item gate into two tiers — "planned remediations complete" (only entries with a real fix description, i.e. not a "no remediation" placeholder) vs. an informational "deferred/referred count" that does not block closure, or (b) have `result_packet_accepted`/CG-3 accept a stream's `stream_closure_recommended` (already gated on an INDEPENDENT_VERIFIER's explicit sign-off, which S4 obtained) as sufficient without requiring 100% of triaged findings VERIFIED — a governance/Programme Integrator decision, not a stream-local fix.
- **Status:** OPEN · S4's own result_packet_accepted/CG-3 tracker event remains formally BLOCKED pending this decision — see `S4_RESULT_PACKET_v1_0.md` for the actual stream result packet, produced independently of this tracker gate.
- **Addendum (2026-08-29, resume session):** confirmed a second facet live — once `remediation_approved` freezes the plan, the tracker ALSO refuses any new `finding_discovered` for the stream (`409 FINDING_FREEZE — "a new finding after the frozen remediation plan requires a separately governed scope path"`), even for a genuinely new finding absorbed from a cross-stream referral in a later resume session (see `V3-E-056` below, which could not be filed as a tracker event for this reason — filed to the register only). The tracker's one-shot-session model does not currently support a stream resuming with new in-scope work after its own plan freeze; this is the same root problem as the remediation gate, one layer earlier.

### V3-E-056 — `citation_resolver.ts` id-recognition scope defect (absorbed from S3's `V3-E-032` referral) — FIXED and independently verified through two adversarial review rounds

- **Class / severity:** DEFECT · **CRITICAL** (confirmed, not proposed — this is S3's own live-corpus CRITICAL, absorbed as an S4-owned finding per the pipeline-territory referral)
- **Lens(es) / pipeline stage:** Correctness, Door-neutral pipeline · S9 (grounding/citation)
- **Provenance:** S3's `V3-E-032` (0/183 real citation attempts reached a trustworthy grade across 24 live turns/8 work classes; S3's own scorer bug that had masked this as 0.5 was found and fixed by S3, PR #1619; the platform-side root cause was referred to S4 as pipeline territory).
- **Expected:** a citation of any id genuinely present in this turn's retrieved evidence resolves to a real grade, not `unverified` by construction.
- **Observed (2026-08-29, LIVE, root cause re-derived independently against production, not assumed from S3's filing):** `citation_resolver.ts`'s `SIGNAL_ID_RE` only recognized `SIG.MSR.NNN`-shaped ids — but a live query confirmed `bodha_msr_signals.signal_id` is a genuine UUID column in production; the `SIG.MSR.NNN` string format **never occurs in live per-chart data at all** (it is the MSR spec-catalog convention only). This alone plausibly explains the full 183/183.
- **Fix:** widened resolution to 4 chart-scoped tables in parallel (`bodha_msr_signals`, `chart_facts`, `chart_divisionals`, `chart_dashas`), each independently `WHERE chart_id = $1` (STRICTER than the original query, which had no chart filter at all — verified by the independent reviewer); fail-closed-to-null preserved for anything not actually retrieved this turn (no over-crediting, adversarially confirmed); per-source DB-fault isolation added (`citation_prefetch_db_fault` flag, one table's fault doesn't blank the others).
- **Adversarial review round 1 — REJECTED:** an independent Opus-level verifier found the widened `reader_label` (the one field ever shown to the reader, unlinted) was being filled from raw `chart_facts.citation_human`/`chart_divisionals.citation_human` DB strings — internal audit text like `"upagraha_position.DHUMA.sign_lord = Moon (true_chitra)."` — live-confirmed on 14,945 production rows. The fix's own test asserted the leaked string as expected output.
- **Follow-up fix:** after sampling ~100 real `fact_category` values live and confirming the data is genuinely inconsistent (real prose mixed with raw internal strings, bracket-tagged leaks, a raw module-path leak) with no separate human-authored display column available, `citation_human` was removed from the SELECT entirely for the two affected sources — structurally impossible to leak, not merely unused. Both now resolve `reader_label` to a fixed, leak-free placeholder; `grade: primary` (the load-bearing grounding fix) is fully preserved. A related gap (2,835 `chart_facts` rows with UUID-shaped `fact_id` never queried) was fixed in the same pass.
- **Adversarial review round 2 — ACCEPTED:** the same reviewer re-checked with mutation testing (reintroduced the exact original leak, confirmed the test suite catches it on the precise right assertions), confirmed `audit_detail` never reaches the wire, confirmed the placeholder approach preserves the fix's real value (grading correctness, not label prose, was the actual defect), and re-verified every check that passed in round 1 still holds (no over-crediting, chart-scoping, fault isolation, zero auth/safety touch).
- **Code anchor:** `platform/src/lib/pariprashna/pipeline/citation_resolver.ts`, `platform/src/lib/pariprashna/pipeline/synthesis_stage.ts`.
- **PPR/gap cross-reference:** PPR-04; S3's `V3-E-032`/`V3-E-016`.
- **Not widened (honest scope limit, confirmed twice):** the L0 `l0_citation_ids` family (`sutravali_rules.rule_id`, `classical_texts_source.text_id`) — heterogeneous slug/UUID format, globally scoped rather than chart-scoped, would need a different fail-closed query shape; landing it unverified risked exactly the over-crediting hazard this fix otherwise avoids.
- **Status:** MERGED — PR [#1646](https://github.com/Marsys-Technologies/Madhav/pull/1646) (2-commit fix + follow-up), independently verified ACCEPT after one REJECT→fix→re-verify cycle. Full regression: 2141/2246 pass (104 pre-existing skips), including S3's own `citation_precision.ts` scorer test. Tracker note: this finding could not be filed as a `finding_discovered` event (see `V3-E-S4-PROC-002` addendum above, `FINDING_FREEZE`) — recorded here and in the result packet instead.

---

*End EDIR_V3_REGISTER — S4 resume-session addendum (2026-08-29): 4 additional
findings driven to MERGED+independently-verified this session (V3-E-034,
V3-E-045, V3-E-055, and the newly-absorbed V3-E-056 citation CRITICAL
referred from S3) — PRs #1643/#1644/#1645/#1646, all merged to main. 57 V3
entries total on this branch (55 prior + V3-E-S4-PROC-002 + V3-E-056; note
`V3-E-S4-PROC-002` is a PROCESS entry outside the numeric V3-E-0NN sequence
by design, see its own body). 10 of S4's 44 triaged findings now have a
landed, merged, independently-verified fix (6 from the prior session + 4
this session); 34 remain OPEN per their Native Surrogate disposition
(deferred/referred/tracked-elsewhere/no-action), unchanged and re-confirmed
still valid this session (checked sibling streams S1/S5/S6 for any
overlapping fix landing on their branches — none found for the 6 referred
findings as of this addendum). The mid-document "End EDIR_V3_REGISTER v1.1"
marker above (before this addendum) is a pre-existing stray artifact from
an earlier session, not corrected here — out of this session's scope per
the same note the v1.1 aggregation pass itself recorded for a similar
stray marker earlier in the file. This is genuinely the end of the file.*
