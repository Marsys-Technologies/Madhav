---
artifact: PARIPRASHNA_EDIR_V3_REGISTER
version: 1.0
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
- **CLOSED-BY-TRIAGE (2026-08-28, S5 stream):** all ~39 candidate routes (30
  original + 3 addendum + 6 surfaced during triage cross-referencing)
  individually triaged with cited file:line verdicts. Result: 4
  VULNERABLE-HIGH (`cockpit/runs/active`, `cockpit/sse`, `mcp/session`,
  `build/continue`), 3 VULNERABLE-MEDIUM (`clients/[id]/learning` write/read
  split, `build/data-readiness`, `build/pyramid-layers`), 1 flagged for
  follow-up (`mcp/db/query` — 15+ platform-mcp call sites not individually
  verified, worst case capped to SELECT-only), 2 latent-not-yet-exploitable
  gaps noted (`projects/route.ts` chart_id field currently inert downstream),
  1 addendum claim REFUTED (`cockpit/runs/[id]/assets` is correctly
  super_admin-gated), remainder CONFIRMED-SAFE with cited reasons. Fixes for
  the 4 HIGH + `learning`/`data-readiness`/`pyramid-layers` MEDIUMs dispatched
  as PRs #1617/#1618 (branch lanes e013/e014) — see V3-E-022 below for the
  consolidated fix tracking of the confirmed-HIGH subset (`mcp/session`'s
  fix is in #1618, tracked under its own remediation entry S5-R-003 alongside
  V3-E-011; see the corrected result packet for the durable PR link).
  `mcp/db/query`'s 15+ call-site sweep and the two latent gaps remain open
  leads for a future session.

### V3-E-017 — `DELETE /api/auth/session` (logout) never revokes server-side; no same-day session revocation path exists

- **Class / severity:** DEFECT · S3 (MEDIUM)
- **Lens / stage:** L-CODE · CROSS
- **Observed (2026-08-28, S5 stream):** the logout handler clears the
  `__session` cookie client-side only (`maxAge: 0`); it never calls Firebase
  Admin's `revokeRefreshTokens(uid)`. The cookie's TTL is 14 days
  (`SESSION_DURATION_MS`). A captured/leaked cookie (XSS, stolen device, log
  leak) therefore remains valid server-side for up to 14 days after the
  legitimate user "logs out." Repo-wide grep confirms `revokeRefreshTokens` is
  called nowhere in the app. The underlying verification path IS already
  wired to respect revocation (`verifySessionCookie(cookie, true)` — the
  `checkRevoked` flag) — only the trigger is missing.
- **Proposed fix class:** make `DELETE /api/auth/session` resolve the caller's
  uid from the incoming cookie and call `revokeRefreshTokens(uid)` before
  clearing the cookie, reusing the existing Admin SDK singleton.
- **Status:** FIXED, INDEPENDENTLY VERIFIED ACCEPT (Opus), MERGED to main —
  PR #1616 (branch `pariprashna/v3-s5-e017-session-revocation-on-logout`),
  TDD red-then-green, merged 2026-08-28T00:37:32Z.

### V3-E-018 — `clients/[id]/layout.tsx`'s `generateMetadata` is ALSO unguarded — same defect class as V3-E-007, broader blast radius

- **Class / severity:** DEFECT · S2 (HIGH — parent layout of every
  `/clients/[id]/*` route, ten sibling routes, not just one page)
- **Lens / stage:** L-CODE · CROSS
- **Observed (2026-08-28, discovered by V3-E-007's independent verifier during
  adversarial sweep):** `platform/src/app/clients/[id]/layout.tsx` (~line 15)
  runs `SELECT name FROM charts WHERE id=$1` in `generateMetadata` with no
  auth check and no `.catch()`. `resolveChartPageAccess` is imported in this
  file but used only in the page body, not the layout's metadata function —
  the exact V3-E-007 pattern, one level up the tree. Since every
  `/clients/[id]/*` route (nirmana, timeline, pariprashna, samiksha, etc.)
  shares this layout, the blast radius is the entire client-chart route
  family, not the single page V3-E-007 fixed.
- **Proposed fix class:** identical to V3-E-007's fix — call
  `resolveChartPageAccess` inside `generateMetadata` and fall back to a
  generic title when access is denied/absent.
- **Status:** OPEN, filed to stream **S5** — not fixed this session (V3-E-007's
  fixer/verifier pass surfaced this as a sibling gap after V3-E-007 itself was
  already merged; landing it is the natural next-session action). Close rung:
  LIVE unauthenticated-denial proof, same as V3-E-007.

### V3-E-019 — `timeline/layout.tsx` + `timeline/page.tsx` use a divergent, weaker authz model that ignores `chart_grants`

- **Class / severity:** DEFECT · S2 (MEDIUM — functional bug + drift risk, not
  itself a cross-tenant leak)
- **Lens / stage:** L-CODE · CROSS
- **Observed (2026-08-28, discovered by V3-E-007's independent verifier):**
  both files use raw `getServerUser()` plus an inline
  `profile.role !== 'super_admin' && chart.client_id !== user.uid` check,
  bypassing the canonical `resolveChartPageAccess`/`authorizeChartAccess`
  brain entirely and ignoring `chart_grants` — a legitimate view-grantee is
  incorrectly denied (functional regression relative to every sibling route),
  and the hand-written duplicate is exactly the "two copies drift" risk class
  B-007/B-008 already flagged once.
- **Proposed fix class:** replace both inline checks with
  `resolveChartPageAccess`/`authorizeChartAccess`, matching all nine sibling
  `/clients/[id]/*` routes.
- **Status:** OPEN, filed to stream **S5** — not fixed this session (surfaced
  late in an independent-verifier sweep; no live exploit, functional-parity
  fix only). Close rung: INTEGRATION (a view-grantee can reach the page) is
  sufficient; no live-denial proof needed since this is an over-restriction,
  not a leak.

### V3-E-020 — `assets/[chart_id]/[asset_key]` (fixed for AUTHZ by V3-E-010/PR #1613): the underlying `chart_facts` query is not chart-scoped — a landmine for the route's next repair

- **Class / severity:** PROCESS · S2 (MEDIUM — not currently exploitable, see
  below, but a real earned-signal gap)
- **Lens / stage:** L-CODE · CROSS
- **Observed (2026-08-28, discovered by V3-E-010's independent verifier via a
  real mutation-testing probe):** the route's `chart_facts` SQL filters on
  `category = $1` only, never `chart_id` — authorization is now correctly
  chart-scoped (V3-E-010's fix), but the DATA READ itself is not. The
  fixer's ALLOW tests assert `200` + content but never assert the returned
  rows belong to the authorized chart — exactly the §N.8 earned-signal defect
  class (a green suite that doesn't measure the claim). **Currently NOT
  exploitable**: the route's column names (`category`, `value_text`,
  `divisional_chart`, ...) predate the 2026-06-03 `chart_facts` schema
  rebuild (migration 204: `fact_category`/`fact_value_text`/`computed_at`)
  and the route is already broken against the live schema (500s) — confirmed
  against the most recent schema artifact
  (`verification_artifacts/PARISESA_V4_GA3_REBUILD_20260821/rehearsal_schema.sql`).
- **Proposed fix class:** whoever repairs the broken column names next MUST
  add `AND chart_id = $N` alongside the column fix, or the repair silently
  reopens a live cross-tenant read with V3-E-010's own test suite staying
  green throughout.
- **Status:** OPEN, filed to stream **S5** as a landmine flag for the future
  schema-repair session — not itself remediated this session (no live
  exploit exists to fix against; the fix belongs with the schema repair, not
  before it). Close rung: whenever the column-name repair lands, its own
  ALLOW tests must assert row-level chart_id scoping.

### E-001 (PPR-26) narrowed-proof: `amjis_app` audit_log DELETE/TRUNCATE revocation, migration ready, NOT applied

**Correction (post-triage):** this entry was originally headed `V3-E-021` in
this file. That id is RETIRED here to avoid collision -- the tracker's own
finding id for this item, registered by the S5 stream at discovery, is
`E-001` (not `V3-E-021`); separately, stream **S2** independently registered
its own, unrelated tracker finding under the id `V3-E-021` (filed
23:55:32Z, before this section was written) -- a genuine cross-stream id
namespace collision, since S1-S6 each hold an isolated worktree copy of this
same register file. Anything citing `EDIR_V3_REGISTER_v1_0.md#V3-E-021`
should resolve to **S2's** finding, not this one. This section is retitled
by its correct tracker id, `E-001`, to end the collision.

- **Class / severity:** DEFECT · S1 (HIGH proposed by the finder;
  **REVISED to MEDIUM by the S5 Native Surrogate at triage, tracker event
  seq 28** -- rationale: the privilege is exercisable only by a principal
  already holding the `amjis_app` serving credential, which already implies
  full app-data compromise (not a boundary crossing for any unauthenticated
  or ordinary authenticated user); and `amjis_app` OWNS `audit_log` and
  inherits `cloudsqlsuperuser`, so the proposed REVOKE is trivially
  self-reversible by the very principal it constrains (`GRANT ... TO
  amjis_app` is one statement away) -- capping this at defense-in-depth, not
  a hard control. The downgrade lowers the claim, not the remediation
  priority.)
- **Lens / stage:** L-DB · CROSS
- **Observed (2026-08-28, S5 stream, live re-confirmation):** read-only query
  against production (`information_schema.role_table_grants`) reconfirms
  `amjis_app` (the live serving credential) holds DELETE, UPDATE, INSERT,
  SELECT, TRIGGER, TRUNCATE, and REFERENCES on `audit_log` — an audit trail
  should be append-only. `writer.ts`'s `ON CONFLICT DO UPDATE` upsert is a
  legitimate, actively-used idempotent-retry pattern (UPDATE is needed); no
  legitimate DELETE/TRUNCATE caller was found anywhere in the repo after a
  thorough search.
- **Proposed fix class:** migration 634 — `REVOKE DELETE, TRUNCATE ON TABLE
  public.audit_log FROM amjis_app`, leaving UPDATE/INSERT/SELECT untouched.
- **Status:** NARROWED PROOF LANDED, BLOCKER STILL OPEN — PR #1615, TDD
  red-then-green on a scratch DB, `migration-guard` reviewed SAFE (two minor
  advisory fixes applied). **NOT applied to production** — this stream's
  charter requires Native Surrogate + integrator sign-off before any
  migration merges (a migration merge auto-deploys and auto-runs against
  production per `MIGRATION_AND_MERGE_PROTOCOL_v1_0.md §5`), and that
  sign-off has not been sought within this autonomous run. Flagged for native
  review at session close.

### V3-E-022 — cockpit/runs/active, cockpit/sse, build/continue: three confirmed VULNERABLE-HIGH routes from the V3-E-011 sweep (fix tracking)

- **Class / severity:** DEFECT · S1 (HIGH, independently confirmed by the S5
  Native Surrogate at triage)
- **Lens / stage:** L-CODE · CROSS
- **Observed (2026-08-28, S5 stream):** same defect family as B-001/B-007/
  B-008 -- caller-supplied `chart_id` trusted after only `getServerUser()`.
  `cockpit/runs/active` (cross-tenant `build_runs`/`build_run_assets` read),
  `cockpit/sse` (cross-tenant live SSE build-event stream), `build/continue`
  (cross-tenant `build_events` write, resumes another tenant's build).
- **Status:** FIXED, INDEPENDENTLY VERIFIED ACCEPT -- PR #1617 (branch
  `pariprashna/v3-s5-e013-runs-active-sse-build-continue-authz`), TDD
  red-then-green (7 DENY cases red pre-fix, mutation-tested by the verifier),
  full suite green. **MERGED to main** at 2026-08-28T00:49:32Z (confirmed
  via live `gh pr view 1617`).
- **Note (overlap with V3-E-011):** this entry's content is the
  confirmed-HIGH subset of V3-E-011's own sweep table -- filed separately
  per the tracker's finding-id bookkeeping (V3-E-011 the umbrella sweep,
  V3-E-022 the three routes with this PR's fix), not a duplicate defect.

### Open disagreement, recorded honestly: `mcp/session/route.ts` severity

The V3-E-011 sweep's original finder traced a full exploit chain through
`session_recall` (`platform-mcp/src/tools/session_tools.ts`) and rated
`mcp/session/route.ts` VULNERABLE-HIGH, reasoning that any caller holding a
valid MCP API key could pass an unauthorized `chart_id` and read another
tenant's provenance metadata. The S5 Native Surrogate, reviewing
independently at triage time (tracker seq 28, remediation plan freeze), read
`lib/mcp/service_token.ts` directly, noted the route IS gated by a
constant-time-compared internal token, and wrote explicitly: **"re-triage
this route before writing a fix."** A fixer was ALREADY dispatched and had
already written a fix by the time this instruction was recorded (timing
race inherent to running fixer/triage lanes in parallel this session) --
so the surrogate's re-triage instruction was, in effect, superseded rather
than followed. This is recorded here plainly rather than silently omitted:
**the fix (PR #1618, adding an `authorizeChartAccess` gate keyed on the
`x-mcp-user` header, mirroring `mcp/bundles/[name]/route.ts`'s established
pattern -- additive only, does not touch or loosen the existing
`X-MCP-Internal-Token` authentication gate) was independently Opus-verified
ACCEPT** (the verifier traced the exact exploit chain, confirmed the
principal cannot be forged, confirmed the untouched `active_chart_id` write
path does not amplify into a read, per its own report in this session's
tracker events) **and queued for merge without the surrogate's requested
re-triage having formally occurred.** This is an authentication-vs-
authorization distinction, not necessarily a refutation of the original
finding: the finding's substance was that an *authenticated* MCP caller had
no *per-chart authorization* check, which the surrogate's own reading does
not contradict -- but the exact severity (reachable by any external
integration holding an MCP key, vs. a narrower internal-service-only
surface) remains unresolved between the two independent reads. The FIX
itself is unaffected by this dispute (additive-only, safe regardless of the
final severity call, and independently verified) but both the severity
disagreement AND the overtaken-instruction process gap are flagged here for
native/integrator review, not silently resolved or hidden in either
direction.

### New lead, NOT filed as a formal tracker finding: stale/pre-fix MCP session pins

PR #1618's independent verifier (reviewing the `mcp/session` fix above) traced
a MEDIUM-severity residual that the fix does not close: `state_json.pins`
(`platform/src/lib/mcp/sessions.ts:77`) stores a chart-id-keyed pin map that
both `GET`/`POST /api/mcp/session` return in full, unfiltered by the new
authorization gate -- a pin written for an unauthorized chart BEFORE this fix
(or after a since-revoked grant) is still stored and still returned in that
raw object. **Contained today only because it is a projection, not a gate**:
`platform-mcp`'s `session_recall`/`session_list` tools drop `state_json`
before returning to the caller, so nothing currently forwards the stale pin
-- but any future change that does would make this live. Proposed
remediation: filter `state_json.pins` to entitled charts on read, plus a
one-off remediation sweep of existing `mcp_sessions.state_json` rows.
**This is NOT filed as a `V3-E-0NN` tracker finding**: the S5 Native
Surrogate froze the stream's remediation plan (tracker seq 28) before this
residual surfaced, and `finding_discovered` is now locked
(`FINDING_FREEZE`) until a governed scope-change path re-opens it. Recorded
here in the register per the one-register rule (register captures finding
bodies even when the tracker's formal intake is temporarily closed) so it is
not silently dropped; a future session should register it as a proper V3
entry and route it through the scope-change process before remediating.

### Session disclosures (S5, added at close per independent stream-closure review)

Stated plainly, not buried in prose elsewhere:

- **Nothing this session fixed is serving production traffic.** `amjis-web`
  remained at `cafa894ee...` (stale, missing even the pre-session B-007/B-008
  fixes) for this entire run; the deploy pipeline itself failed again during
  the session (re-checked via `gcloud run services describe` at close). As
  of 2026-08-28T00:49:32Z (live `gh pr view` check, the freshest available):
  FOUR PRs merged to `main` (#1611 00:20:31Z, #1613 00:27:38Z, #1616
  00:37:32Z, #1617 00:49:32Z), ONE independently verified ACCEPT and still
  queued in the merge queue, not yet merged (#1618) — none are live
  regardless of merge state, since `amjis-web` has not redeployed.
- **Model.** The tracker's `work_started` payload records this stream's main
  loop as `claude-sonnet-5`. The charter recommends Opus for S5 specifically
  ("Opus-led ... this is the stream where that discipline matters most");
  Sonnet is within the harness §5 floor for this role (never a downshift
  below Sonnet), not a violation, but it is disclosed here rather than left
  implicit. The five independent verifications and the Native Surrogate
  triage/freeze pass were run on Opus, per the charter's mandatory-Opus rule
  for security-class verification and gate-adjacent judgment.
- **Verification attestation was recorded post-hoc, not live.** The five
  Opus independent-verifier subagents dispatched this session produced real,
  substantive, adversarial reviews (full transcripts summarized inline in
  this register and in the tracker's `verification_accepted` events, seq
  32/34/36/38/40) — but those subagents were not issued their own tracker
  actor credentials, so their verdicts were NOT recorded as tracker events
  at the moment each review completed. The Stream Lead recorded them
  afterward, using the `verifier` actor token, citing the real PR and the
  real verdict. This is disclosed as a process gap for a future harness
  revision (subagents performing a governed role should hold and use their
  own tracker credentials directly), not concealed as if it had happened
  natively.
- **Denominator honesty.** 45 scenarios were frozen at session open; 11
  `scenario_executed` events were recorded against that denominator (well
  short of 45), plus a separate 9 `finding_discovered` / 9 `finding_triaged`
  / 1 `remediation_approved` (9 plan entries) / 5 paired
  `remediation_implemented`+`verification_accepted` events documenting real
  work outside the scenario count itself. This
  session claims PARTIAL credit, not full closure of the §9 battery — the
  work concentrated on the highest-value lanes (the systemic authz sweep,
  LIVE-proven J4 enforcement, a real restore drill, a LIVE roles/grants
  audit, B-002's caution-preserving re-confirmation) rather than checking
  off every enumerated §9 sub-item as a separate event.

---

### V3-E-012 — Quality corpus (`fixtures.ts`) grounds 11 of its 12 existing fixtures in the native's real chart, not the synthetic default

- **Class / severity:** PROCESS · S3 (MEDIUM, proposed — this is a
  test-data-law compliance question about already-committed, baseline-frozen
  content, not a proven violation or a live-probe incident)
- **Lens / stage:** L-CODE · S3 corpus territory
- **Expected:** per the test plan's frontmatter `test_data_law`, "all live
  probes default to the synthetic consented chart `1c826d5a-...`. The
  native's real chart (`482012f1`) is used only where a scenario specifically
  requires it AND the native has authorized that specific use." S3's own
  launch instructions and elevation §3.2 item 2 name real-chart use as the
  reserved residue that self-pauses a stream if introduced un-authorized.
- **Observed (2026-08-28, S3 stream-open):** `platform/src/lib/pariprashna/corpus/fixtures.ts`
  (committed on `origin/main`, present unmodified at this stream's baseline
  SHA — not introduced by this session) imports `CANONICAL_CHART_ID`
  (`= '482012f1-710e-4a25-994a-93821f5871aa'`, the native's real chart) from
  `types.ts` and sets it as `chartId` on **11 of the corpus's 12 existing
  fixtures** (`factual-001`, `interpretive-001`, the `timing`, `cross-domain`,
  `remedial`, `sensitive`, `incomplete-evidence`, `returning-conversation`,
  `disagreement`, `prediction`, and `door-parity` fixtures all use
  `CANONICAL_CHART_ID`; only `ambiguous-001-will-i-be-successful` uses
  `SYNTHETIC_CHART_ID`). `types.ts`'s own docblock (line 73-76) frames this as
  intentional: the real chart is used "for anything that cites real chart
  content," with a synthetic id reserved for "anything that must not touch
  canonical chart data during test authoring" — i.e. the module's author
  already drew this distinction deliberately, but no authorization citation
  is attached to any individual fixture confirming the native specifically
  authorized each real-chart use per the test-data law's own conjunctive
  test ("specifically requires it AND the native has authorized that
  specific use").
- **Why this is not treated as a live self-pause trigger:** the precedent
  PROCESS finding for this exact issue class, historical **E-010** ("Live
  probe used the native's real chart without specific need"), is recorded
  CLOSED-AS-CODIFIED (2026-08-24, via the plan v2.0 test-data law itself) —
  its closure mechanism was writing the very rule this finding is now
  checked against, not leaving the question open. E-010's framing is also
  specifically about a *live probe*, not a *static, already-committed
  fixture* grounding choice — a materially different act. This finding is
  therefore filed for native/Native-Surrogate confirmation of the existing
  fixtures' authorization basis, not as a blocking violation. Consistent
  with this, S3 proceeded to open the stream and expand the corpus, with the
  explicit constraint that **every new fixture authored this session uses
  `SYNTHETIC_CHART_ID` (`1c826d5a-...`) exclusively, no exceptions** — the
  question this finding raises is scoped strictly to the 11 pre-existing
  fixtures, never to new S3 work.
- **Proposed fix class:** either (a) the native/Surrogate confirms the
  existing real-chart grounding was an intentional, in-scope authorization
  (test-data-law's "specifically requires it" clause — richer/fully-built
  L1-L5 data on the real chart vs. the synthetic chart's likely-sparser
  build is a plausible legitimate reason), in which case this closes
  CLOSED-AS-CODIFIED like its precedent with that rationale recorded inline
  per-fixture; or (b) if not authorized, the 11 fixtures are re-grounded
  against the synthetic chart as a remediation PR, filed as S3's own
  in-territory fix (the corpus is squarely S3's file territory) once ruled.
- **Status:** OPEN, filed to native/Native-Surrogate for the authorization
  ruling. Close rung: STATIC (a documented ruling, or a landed
  re-grounding PR with independent verification if ruled unauthorized).

---

### V3-E-016 — CRITICAL: deployed web door hallucinates the native's real, specific chart facts when answering an unrelated synthetic-chart factual query, and serves them with undisclosed confidence

- **Class / severity:** DEFECT · S3-discovered, filed to **S4** (primary —
  grounding/validation pipeline root cause) and **S5** (privacy/disclosure
  angle: real, specific, sensitive personal astrological data about the
  native surfaced in an unrelated synthetic-chart response) · **CRITICAL**
  (reproducible, live production, factual-integrity + confidence-honesty
  double violation, with a plausible privacy-disclosure reading)
- **Lens / stage:** L-LIVE (deployed web door) · pipeline S9 Grounding/Safety
  Validation (`validation_stage.ts`, `streaming_citation_validator.ts`) ·
  overlaps S3's own dimension 1 (Factual integrity) and dimension 5
  (Confidence honesty)
- **Expected:** per test plan §1.3 principle 4 ("Honest absence… a gap,
  empty state, degraded provider, or unfinished turn is stated plainly,
  never filled with plausible-looking content") and CLAUDE.md §N.7/§B.10
  ("Claude never invents numerical chart values"), a query against chart
  `1c826d5a` (Abhinandan, the synthetic test chart) for its Moon's
  nakshatra should either (a) return `1c826d5a`'s real, ground-truth L1
  fact — **Ardra**, sign **Gemini**, longitude 73.2278°, confirmed live via
  `ganita_positions_get(chart_id=1c826d5a, planet=Moon)` this session — or
  (b) honestly disclose it lacks grounded data for this fact.
- **Observed (2026-08-28, S3 stream-open, reproduced twice):** two
  independent, freshly-authenticated live turns against the deployed web
  door (`POST https://amjis-web-qm256lasva-el.a.run.app/api/pariprashna`,
  via the existing `platform/scripts/probe/ask.ts` harness, `chartId:
  "1c826d5a-41cb-4450-b4dc-59d440e5f75a"` explicitly present in both POST
  bodies and echoed correctly in both turns' own `turn.open` SSE event) both
  answered "the Moon in this chart is placed in **Purva Bhadrapada**
  nakshatra… **27°02′48″** in the sign of **Aquarius**" — verbatim,
  degree-for-degree identical across both independent runs. This is **not**
  chart `1c826d5a`'s data (ground-truthed above as Ardra/Gemini) — it is the
  native Abhisek Mohanty's own FORENSIC canonical Moon fact (CLAUDE.md §B:
  "Moon = Purva Bhadrapada", chart `482012f1`), reproduced with enough
  precision (the exact degree) that this reads as memorized real content,
  not a generic plausible-sounding guess. The literal string `482012f1`
  never appears anywhere in either turn's SSE stream or receipt — the leak
  is in the *content*, not a chart-id mix-up in the request/turn-tracking
  layer itself.
  - **The turn's own streamed receipt (`receipt.define` SSE event) already
    detects this dishonestly**: `evidence_grades.hallucination_count: 2`,
    both cited facts (`NAK.PURVA_BHADRAPADA`, `PLN.MOON`) graded
    `"unverified"` (0 primary/supporting/contextual grades). The receipt's
    own `coverage` block discloses the root condition honestly:
    `"served": 5, "empty": 9, "floor_item_total": 14, "channel_note": "9 of
    14 floor items have NO web-executable retrieval tool (MCP↔web namespace
    gap); 5 served, 9 empty, 0 dark."` — i.e. the web door lacks a real
    retrieval path for this fact type, and rather than disclosing the gap
    (which the receipt's own `honest_gaps` field is structurally built to
    carry), the synthesis layer filled it with specific, confident,
    plausible-looking — and, disturbingly, *correct-for-a-different-chart*
    — content. The served prose shows plain, unflagged footnote markers
    (`[1]`, `[2]`); nothing in the reader-facing text discloses
    `unverified`/hallucinated status.
  - `platform/src/lib/pariprashna/pipeline/validation_stage.ts` (the S9
    grounding/safety validation stage) contains **zero** references to
    `hallucination_count` — confirmed by direct grep this session — meaning
    nothing in the validation stage currently gates, downgrades, or
    discloses on this signal even though the receipt computes it correctly.
    The detector is honest; nothing downstream acts on it.
  - Evidence: `platform/scripts/probe/out/24ba8c23-9bde-4c27-9f69-70e6bfd1e9d4.json`,
    `platform/scripts/probe/out/8b9486f2-dabc-469e-873b-b27afc49cbb5.json`
    (both worktree-local, not committed — reference by path for the
    assigned stream to pull), plus the live `ganita_positions_get` ground-
    truth call this session.
- **Why not fixed in S3:** root cause is either the grounding/retrieval
  coverage gap itself (pipeline stage territory, S4) or the missing
  validation-stage gate on `hallucination_count`/`evidence_grades` before
  serving (S9, also S4 primarily, S5 for the disclosure angle) — both
  outside S3's charter territory (quality corpus / rubric harness /
  synthesis prompts). This is exactly the "collateral finding while
  verifying something unrelated" class the shared elevated frame's §6
  instructs surfacing, not silently fixing across a territory boundary.
- **Proposed fix class:** (a) wire `validation_stage.ts` (or
  `streaming_citation_validator.ts`) to gate on `evidence_grades.
  hallucination_count > 0` — at minimum forcing an explicit low-confidence/
  unverified disclosure into the served prose, at maximum blocking the
  claim and falling back to the `honest_gaps` disclosure path that already
  exists structurally in the receipt; (b) separately, investigate whether
  this is reproducible for other fact types/charts (systemic, like
  V3-E-011's ~30-route sweep) or specific to the MCP↔web namespace gap for
  nakshatra-class facts.
- **Status:** OPEN, filed to **S4** (primary) and **S5** (privacy angle),
  flagged CRITICAL for expedited triage given the reproducible real-data
  disclosure content. Close rung: LIVE (a seeded reproduction of this exact
  query turning honest/gapped instead of hallucinated, against the deployed
  route).

---

### V3-E-032 — CRITICAL: live corpus sample shows 0 of 80 citation attempts reach a trustworthy grade across 10 turns/6 work classes on the deployed web door; S3 scorer bug that had masked this as 0.5 found and fixed; adversarially reviewed and CORRECTED

**Corrected 2026-08-28 after a 3-way blinded Opus adversarial refuter panel
(elevation R-2, `SURROGATE-SCORED — pending native rubric`) found real errors
in this entry's first-filed version. Corrections applied inline below rather
than silently — see "Adversarial review" at the end.**

- **Class / severity:** DEFECT (corroborating/quantifying V3-E-016 at corpus
  scale) filed to **S4** (primary — root cause narrowed by the refuter panel
  to `platform/src/lib/pariprashna/pipeline/citation_resolver.ts`, not the
  broader "grounding/retrieval pipeline" this entry originally named) · plus
  an S3 in-territory scorer-harness DEFECT, found and FIXED this session ·
  **CRITICAL**
- **Lens / stage:** L-LIVE (deployed web door, `scripts/probe/ask.ts`,
  synthetic chart `1c826d5a` only) · S3 quality-corpus scoring harness
  (`platform/src/lib/pariprashna/corpus/dimensions/citation_precision.ts`)
- **Observed (2026-08-28, S3 stream, live corpus run):** ran a 16-fixture
  live sample (2 fixtures × 8 single-turn-compatible work classes:
  factual, interpretive_whole_chart, cross_domain_contradiction,
  incomplete_evidence, remedial, sensitive, timing, ambiguous_clarification;
  the 3 conversation-history-seeded classes — disagreement,
  returning_conversation_drift, prediction_capture_outcome — need a
  `priorTurns` seeding capability the runner does not yet have wired to a
  live door, an honest disclosed gap, not run this pass) against the
  deployed route via `platform/scripts/pariprashna/s3_live_corpus_run.ts`
  (new driver script, this session, wiring the existing
  `probe_output_adapter.ts` + `runCorpus` to `scripts/probe/ask.ts` per one
  call per fixture). 10 of 16 turns produced a measured `evidence_grades`
  block (the other 6 were short/blocked/degenerate responses, reported
  `not_yet_measurable`, not silently dropped). Across all 10 measured turns:
  `primary=supporting=contextual=prior_reading=0` — zero citations, across
  **80** total citation attempts (the per-turn `unverified` counts summed:
  1+8+13+9+5+7+16+8+10+3 = 80), ever reached a real verification tier; all
  80 graded `unverified`. (First-filed version of this entry stated "160" —
  wrong, and wrong in a self-incriminating way: 160 is exactly the
  double-counted denominator the scorer fix below removes. Corrected here.)
- **Scorer bug found and fixed (S3 in-territory, `citation_precision.ts`):**
  `citations/rewriter.ts`'s `resolveSentinel` has exactly one branch for an
  unresolvable reference, and that single branch both assigns
  `grade: 'unverified'` AND increments the hallucination counter
  (`rewriter.ts:263-278`) — `grade_counts.unverified` and
  `hallucination_count` are the SAME event, always exactly equal by
  construction, never disjoint (independent-verifier-confirmed by tracing
  every path into both counters, not just empirically — see stream result
  packet). The scorer previously computed `resolved` as the sum of ALL
  `grade_counts` (including `unverified`) and then added
  `hallucination_count` again as a separate denominator term — double-
  counting every unresolvable citation and mathematically forcing the score
  toward ~0.5 for any turn with zero genuinely-verified citations,
  regardless of true severity. This MASKED the true 0.0 (zero citations ever
  reached primary/supporting/contextual/prior_reading) behind a falsely
  reassuring midpoint score. Fixed via TDD: 2 new tests, confirmed RED
  against the old implementation, GREEN after; full corpus suite re-run
  clean (104/104, zero regressions). Independent verifier additionally
  proved algebraically that the fix is strictly non-lenient versus the old
  formula for all inputs (`score_new ≤ score_old` always). The evidence
  report this entry originally cited
  (`platform/scripts/pariprashna/out/s3_live_corpus_report_s3batch02.json`)
  was committed in the SAME commit as the fix WITHOUT being regenerated —
  it still showed the pre-fix `0.5` and pre-fix finding-string wording,
  making "0.0" a re-derivation, not a filed measurement, when first written.
  **Regenerated** (same path, same 16 captured turns, current scorer) —
  now correctly shows `citation_precision: 0`.
- **Root cause, narrowed by the refuter panel:** the original filing
  attributed this to "the grounding/retrieval pipeline" generally (same
  framing as V3-E-016). Refuter #2 traced the actual mechanism further:
  `citation_resolver.ts:36` — `const SIGNAL_ID_RE = /SIG\.MSR\.\d{3}/g` — the
  resolver's prefetch ONLY recognizes `SIG.MSR.NNN`-shaped ids. The synthesis
  prompt (`pariprashna_synthesis_prompt_v1.ts`) instructs the model to cite
  "the exact reference id as it appears in the retrieved context" —
  ANY retrieved id, not only MSR signal ids (L1 `ga_*` fact_ids, yoga ids,
  dasha row ids are all valid retrieved-context ids per the fixtures'
  own grounding notes throughout `fixtures.ts`). A citation of any
  non-MSR-signal id — even one that is perfectly, verifiably grounded in
  what the turn actually retrieved — resolves to `null` and grades
  `unverified` **by construction**, independent of whether retrieval
  coverage was good or bad. This is a resolver SCOPE bug (recognizes one id
  family, silently fails closed on all others), not proof of a sparse-
  retrieval/grounding-coverage problem per se — though `fetchCandidateSignalLabels`
  also fails closed to an empty map on any DB fault (`citation_resolver.ts:83-88`),
  which independently produces the exact same uniform-zero signature. Both
  mechanisms point at `citation_resolver.ts` specifically, not the broader
  pipeline. Uniform 0.0 across 10 heterogeneous turns fits ONE binary
  wiring/scope failure better than a partial, query-dependent retrieval gap
  (V3-E-016's own turn showed a partial 9/14 gap, not a total one) — the
  two findings likely share upstream lineage but are not proven to be
  literally the same defect; S4 should investigate `citation_resolver.ts`'s
  id-recognition scope as the primary lead, not assume V3-E-016's fix alone
  resolves this.
- **Sample-scope caveats (added per adversarial review):** single synthetic
  chart (`1c826d5a`) only — no control/comparison chart run, so a thin-data
  confound specific to this chart is disclosed, not excluded. 8/10 measured
  turns also showed `cross_domain.status` unavailable with reason
  "plan.domains was not populated by the planner" (see the companion
  `b11_coverage` finding below) — consistent with one common upstream
  planner/retrieval-wiring cause manifesting repeatedly, not ten
  independent failures. "Systemic" is downgraded here from "across the
  door" to "reproducible across this test chart's 10 measured turns,
  spanning 6 work classes, plausibly one common upstream cause" — still
  release-blocking as a user-visible defect (every citation in the sample
  rendered unverified/hallucinated to the reader), not weakened in
  severity, only in the breadth of the causal claim.
- **Why not fixed further in S3:** the citation_precision.ts scorer bug IS
  S3's own territory and IS fixed (above). `citation_resolver.ts` is
  `pipeline/` code — S4 territory, referral only, never a cross-territory
  fix.
- **Proposed fix class:** S4 investigates widening `citation_resolver.ts`'s
  id recognition beyond `SIG.MSR.NNN` (or resolving against a broader id
  catalog matching what the synthesis prompt actually instructs the model
  to cite), and hardening `fetchCandidateSignalLabels`'s fail-closed-to-
  empty-map path to distinguish "genuinely nothing to cite" from "DB fault
  swallowed" (the latter should not silently present as the former). V3-E-016's
  `validation_stage.ts` gating recommendation still applies as a
  defense-in-depth disclosure layer regardless of root cause.
- **Status:** OPEN, filed to **S4** with the narrowed root cause above,
  CRITICAL. The S3-territory half (the scorer bug) is CLOSED — fix landed
  this session (PR #1619), independently verified per harness §6.2 (ACCEPT
  verdict, see stream result packet). Close rung for the platform defect:
  LIVE (a re-run of this same batch against a fixed `citation_resolver.ts`
  showing citation_precision materially above 0).
- **Tracker:** `finding_discovered` event `ef457619-6ea3-4b85-a052-b3334b37c153`
  (S3 stream_seq 5), `root_cause_group: V3-E-016` (kept for now; S4 should
  confirm or split once `citation_resolver.ts` is actually investigated).

**Adversarial review (elevation R-2, `SURROGATE-SCORED — pending native
rubric`, 3-way blinded Opus panel, 2026-08-28):** all three refuters
independently confirmed the underlying defect is real and release-blocking
(exact 0.5 on all 10 pre-fix turns is only possible if
`primary+supporting+contextual+prior_reading=0` on every one — algebraically
forced, not inferable-away) while each independently catching the same "160
vs 80" arithmetic error and the same "report never regenerated post-fix"
gap — convergent, high-confidence findings, now corrected above. Refuter #2
additionally supplied the `citation_resolver.ts` root-cause narrowing.
Refuter #3 additionally found a second, DISTINCT scorer defect in
`b11_coverage.ts` — filed separately as V3-E-033 below, not folded into this
entry.

---

### V3-E-033 — S3 scorer harness: `b11_coverage.ts` penalizes low `served` count directly, contradicting its own docblock

- **Class / severity:** DEFECT · S3 scorer harness (in-territory, not fixed
  this session — see rationale below) · **MEDIUM** (a measurement-accuracy
  defect in a not-yet-release-blocking-on-its-own scorer, not a live
  user-facing defect itself)
- **Lens / stage:** L-CODE · S3 quality-corpus scoring harness
  (`platform/src/lib/pariprashna/corpus/dimensions/b11_coverage.ts`)
- **Observed (2026-08-28, found by refuter #3 during the V3-E-032
  adversarial panel, independently confirmed by direct code read this
  session):** `b11_coverage.ts`'s own docblock (line 13-18): "The RS-4
  proportionality carve-out... means this scorer does not penalize a low
  `served` count on its own; it penalizes `coverage`/`cross_domain` being
  `unavailable`... which is the actual failure mode B.11 exists to catch."
  But the implementation (line 44):
  `coverageComponent = total > 0 ? Math.min(1, served / total) : 1` — a
  direct, linear penalty on a low `served`/`total` ratio, exactly what the
  docblock says this scorer does NOT do. Under the documented (intended)
  behavior, `coverageComponent` should be non-zero (arguably 1) whenever
  `coverage.status === 'measured'` regardless of the served/total ratio,
  penalizing only `'unavailable'` status. Re-scoring the S3 16-fixture live
  batch (V3-E-032's evidence) under a spec-faithful interpretation would
  raise the `b11_coverage` mean from `0.237` to roughly `0.55` — direction
  unchanged (still below the 0.75 qualification bar), but the magnitude
  V3-E-032 originally reported was inflated ~2.3x by this bug (V3-E-032
  corrected to note this).
- **Compounding framing error (also refuter #3):** V3-E-032 reported
  `b11_coverage` as a mean across all 16 fixtures. Only **10 of 16** actually
  produce a `b11_coverage` score: `sensitive` fixtures are exempt from
  `B11_COVERAGE_REQUIREMENT` per `bars.ts`, and `ambiguous_clarification`
  fixtures are excluded from all 4 qualification work classes entirely per
  `work_classes.ts` (`workClass: null`) — neither gets a b11 score to
  average in the first place. The denominator was misstated.
- **Why not fixed this session:** resolving which side is authoritative
  (the docblock's stated intent, or the current code) requires real design
  judgment this stream did not have time to responsibly exercise under
  adversarial-panel time pressure — specifically, `bars.ts` requiring
  `b11_coverage >= 0.75` for the `factual` work class may itself already be
  in tension with the RS-4 carve-out the docblock cites (RS-4 says a
  `factual`-class fixture should satisfy B.11 differently/more leniently,
  via a frame-check rather than the SAME full-floor-coverage bar every
  other class is held to) — a `bars.ts` design question, not just a
  one-line `b11_coverage.ts` code fix. Fabricating a rushed fix to one side
  of a two-file design tension risked getting it wrong in a worse way than
  leaving it honestly open. §N.4 "floors aspirational, not gates" and
  §N.8 apply: an honest open finding beats an invented resolution.
- **What the underlying data actually shows, spec-faithful (the real
  release-blocking signal here):** `cross_domain.status: 'unavailable'`
  (reason: `"plan.domains was not populated by the planner"`) on **8 of 10**
  measured turns in the V3-E-032 batch — this IS exactly the failure mode
  `b11_coverage.ts`'s own docblock says the dimension exists to catch,
  independent of the `coverageComponent` dispute above. This is the number
  worth citing toward a gate, not the disputed pooled mean.
- **Proposed fix class:** (a) a native/Native-Surrogate ruling on whether
  `bars.ts`'s `factual` requirement should apply `b11_coverage` at the
  general 0.75 threshold or an RS-4-adjusted one; (b) once ruled,
  `b11_coverage.ts`'s `coverageComponent` computation brought into line with
  whichever side the ruling settles on (code-to-match-docblock, or
  docblock-to-match-code-plus-bars.ts-adjustment); (c) separately and
  regardless of (a)/(b): investigate why the planner fails to populate
  `plan.domains` on 8/10 turns — likely S4 pipeline territory (the planning
  stage), referral not a cross-territory fix.
- **Status:** OPEN, S3-owned (scorer-harness territory), not release-gating
  on its own — the `plan.domains` planner gap it surfaces IS potentially
  release-relevant and is the number to carry forward, not the disputed
  mean. Close rung: STATIC (a documented ruling + landed fix + independent
  verification, same pattern as V3-E-012).
- **Tracker:** `finding_discovered` event `875dea20-6fe4-4a60-89ec-58f4995bdacd`
  (S3 stream_seq 6).

---

**Cross-stream id collision note (merge from `origin/main`, 2026-08-28):**
the two entries immediately below (titled "V3-E-012" and "V3-E-013" by S1)
collide in NUMBER ONLY with this document's own S3-filed `V3-E-012` above.
Verified against the tracker's `/api/projection` (the globally-unique
authority per elevation §5.5): `finding_id "V3-E-012"` is registered to
**S3** (`lead-s3`, MEDIUM, event `481df17a-b499-4f3d-a080-b20d1ce85398`) —
S1's two entries below were never submitted through the tracker's
`finding_discovered` event type at all (S1's own entry text says its
finding intake was `FINDING_FREEZE`-rejected after `S1-F-001`'s remediation
plan froze it, so these are document-only prose numbers, not tracker-
registered ids). Per elevation §5.5's one-register rule, this divergence is
recorded here rather than silently resolved by either stream renumbering
its own tracker-authoritative entries — Session C convergence should assign
S1's two entries fresh, tracker-registered ids. Kept below verbatim,
unmodified from `origin/main`.

---

### V3-E-012 (S1 document numbering — see collision note above; not a tracker-registered id) — History sidebar has no real cross-session/cross-load persistence: every reload loses "past readings" entirely, and every reload also mints a brand-new conversation id

<!-- --- merged from origin/main (2nd sync, 2026-08-28) --- -->

### V3-E-021 — Composer's "Deep dive" depth override is silently ignored server-side; scope resolves to `standard` regardless

*(renumbered from a draft `V3-E-012` 2026-08-28: the tracker rejected that id
with `FINDING_ID_CONFLICT` — stream S3 had independently claimed `V3-E-012`
on its own branch, an inevitable id-collision risk of parallel streams
appending to one register file across unmerged branches, not itself
investigated further here.)*

- **Class / severity:** DEFECT · S1 major (proposed — reader-visible
  disagreement between what the composer says it asked for and what the
  chart was actually read at; provenance: historical E-110/E-112, reproduced
  fresh on the current build)
- **Lens(es):** L-USER + L-WIRE
- **Pipeline stage:** S1 (intent/scope classification) / S4 (scope
  resolution) — NOT S2; S2's own UI component is disclosing the truth
  correctly (see below)
- **Journey:** J2
- **Provenance:** historical `E-110`/`E-112` (test plan §4.1 S4 row) —
  independently reproduced live, not re-cited from the old register.
- **Expected:** selecting "Deep dive" in the composer (label reads
  "acharya-grade · deep dive override") should cause the resolved
  `scope_tuple.depth` to be `deep`/`deep_dive`, or the composer should not
  claim an override took effect.
- **Observed (2026-08-27, LIVE, deployed `amjis-web@cafa894ee`, chart
  `1c826d5a`, S2-territory code at this commit is byte-identical to current
  `origin/main` HEAD `28a157fb1` — zero S2-territory commits landed between
  the stale deploy pin and HEAD, confirmed via
  `git log --oneline cafa894ee..28a157fb1 -- platform/src/components/pariprashna platform/src/lib/pariprashna`
  returning 0 commits, so this LIVE proof is representative of current main):
  - Request body: `{"chartId":"1c826d5a-...","reading_depth":"deep_dive",...}`
    — the composer correctly sent the override (S2's own composer→API wiring
    is NOT the defect).
  - Wire response `grade` event: `{"subject":"reading_depth_received","grade":"standard","detail":"scope_tuple: intent=dasha_timing width=standard depth=standard"}`
    — the server resolved `depth=standard` regardless of the request.
  - S2's own UI (composer chip's "Depth the last reading actually received"
    indicator) correctly and honestly displayed "depth received: standard"
    — this component is functioning as designed; the disagreement is real,
    not a rendering bug.
- **Code anchor:** `platform/src/lib/vidhi/scope_classifier.ts`
  (`ScopeTupleSchema` resolution — test plan §4.1 S4 row); MCP-side twin
  `platform-mcp/src/resources/vidhi/scope_resolver.ts`.
- **Cross-reference:** test plan §4.1 S4 row; GAP-8.
- **Proposed fix class:** owning-stream fix in the web scope resolver so an
  explicit composer override actually reaches `scope_tuple.depth`, or (if
  intentionally gated) the composer must not present "Deep dive" as a live
  option / must disclose why the override didn't apply before the turn runs,
  not only after via the small "depth received" indicator.
- **Status:** OPEN, filed to stream **S4** (pipeline scope-resolution
  territory) — not fixed by S2; S2's own composer/indicator component is
  confirmed correct and not the defect.
- **Close rung required:** REPLAY or LIVE (a fixture/turn where "Deep dive" is
  selected and `scope_tuple.depth` resolves to `deep`).

### V3-E-030 — The settle announcement claimed "Grounded" for a turn whose own receipt recorded `hallucination_count: 4` and whose own `citation_gate` fired an ERROR

- **Class / severity:** DEFECT · S1 blocking (proposed — a confidence-honesty
  violation on the single reader-facing (and screen-reader-facing) summary of
  an entire reading)
- **Lens(es):** L-USER + L-WIRE + L-CODE
- **Pipeline stage:** SURFACE (S2, working-region/settle-announcement) +
  S8/S9 (synthesis + citation-gate — S4 territory for the root generation
  defect; S2 territory for the surface's failure to disclose it)
- **Journey:** J2
- **Observed (2026-08-27, LIVE, deployed `amjis-web@cafa894ee` — S2-territory
  code confirmed byte-identical to current HEAD, see V3-E-021):** asked
  "What does the current dasha period mean for my career, and how does it
  interact with transiting Saturn?" (turn `ad4228a2-ec12-450e-85c3-52b5398ed2ad`).
  Full SSE trace:
  - `grade` event: `{"subject":"citation_gate","grade":"ERROR","detail":"prescriptive query (predictive) produced 0 citations — guidance must be grounded"}`
    and the paired `flag` event `citation_gate_error`.
  - `receipt.define`'s `evidence_grades`: `{"grade_counts":{"unverified":4,...all others 0},"hallucination_count":4}`.
  - All 4 `citation.define` events carried `"grade":"unverified"` and a
    literal placeholder `snippet`/`reader_label` of `"[unverified citation N]"`
    (see V3-E-014).
  - `turn.commit`: `"status":"ok"` — no degraded/error status propagated.
  - Settled UI (`role="status"`, the one `aria-live="polite"` settle
    announcement `GroundingRegion.tsx` documents as "the settle announcement
    for assistive tech"): **"Reading complete. Grounded in 4 chart factors.
    7/21 floor items served."** — no qualifier, no mention of `unverified`,
    `hallucination_count`, or the citation_gate ERROR anywhere in the
    surfaced text. A screen-reader user hears only "Grounded."
  - Root cause confirmed by code read: `GroundingRegion.tsx` built its
    summary from `turn.grounding.factorCount` (a raw, grade-blind citation
    tally, `s1LiveAdapter.ts:286` `factorCount = citationsSeen - classicalSeen`)
    and never read the ALREADY-COMPUTED, already-correctly-worded
    `turn.grounding.gradeSummaryLabel` (`state/groundingRollup.ts`'s honest
    WELL-GROUNDED / SUPPORTED / CATALOG-ONLY — UNVERIFIED / HONEST-GAP
    rollup, purpose-built to prevent exactly this — see its own doc comment).
    `gradeSummaryLabel` was computed and stored on every turn but had ZERO
    production readers (the same "computed then discarded" defect class as
    E-073's `unmappedPrimitives`/`compileFailed`, §N.8).
  - Test plan cross-reference: §4.3 item 2 (degradation propagation
    honesty — "never absorbed into a confident-looking answer"); §7
    Confidence honesty ("never exceed the evidence"); test principle 4
    (honest absence, "never filled with plausible-looking content").
- **Proposed fix class:** additive, in-territory (S2) — read
  `gradeSummaryLabel` in the settle announcement; only announce an
  unqualified "Grounded in N…" when the rollup itself says WELL-GROUNDED.
- **Fix landed (2026-08-28, S2, this session):** `GroundingRegion.tsx` now
  branches on `gradeSummaryLabel === GRADE_SUMMARY_WELL_GROUNDED`; when not
  well-grounded, the announcement leads with the honest rollup label instead
  of the bare word "Grounded". Demonstrated-can-fail: new test
  `platform/src/components/pariprashna/__tests__/GroundingRegion.test.tsx`
  is RED against the pre-fix component (asserts the announcement discloses
  `unverified`/`catalog-only` for a CATALOG-ONLY rollup; failed with
  `"Reading complete. Grounded in 4 chart factors. (Estimated..." ` before
  the fix) and GREEN after. Full territory suite
  (`vitest run src/components/pariprashna src/lib/pariprashna`): 1523
  passed, 0 regressions. Commit `c06d19486`.
  **Not yet fixed in this pass:** `WorkingBand.tsx`'s compact sealed-band
  label (`renderSealCompleteLabel`, `lexicon.ts:161`, "Grounded in N sources
  · Ts") has the identical grade-blind-count defect and is the ONE thing a
  sighted user sees at the moment of settle (before opening the dock) — it
  was left unchanged this pass to keep the fix narrowly scoped and reviewable
  in one sitting; carried forward as the next unit of this same defect class.
- **Status:** FIXED (`GroundingRegion.tsx` only) — PR pending, independent
  verification pending. `WorkingBand.tsx`'s sealed-band label: OPEN, same
  stream (S2), not yet fixed. The upstream root cause (why every citation on
  a predictive query resolves to `unverified` with placeholder content) is
  filed separately to S4 as V3-E-014.
- **Close rung required:** LIVE re-proof of `GroundingRegion.tsx`'s fix
  against a deployed build once merged and synced.

### V3-E-014 — `citation.define`'s `snippet`/`reader_label` for `structural_prior`-tier signals is the literal unfilled placeholder string `"[unverified citation N]"`

- **Class / severity:** DEFECT · S2 major (proposed — every citation chip in
  the dock for a query with only structural-prior signals is uninformative by
  construction, defeating the dock's core proof requirement)
- **Lens(es):** L-WIRE + L-USER
- **Pipeline stage:** S8 (synthesis) / S9 (citation assembly) — S4 territory
- **Journey:** J2
- **Observed (2026-08-27, LIVE):** all 4 `citation.define` events on the
  turn cited in V3-E-030 carried, verbatim: `"snippet":"[unverified citation 1]","reader_label":"[unverified citation 1]"`
  (and 2/3/4). The dock (`GroundingCard.tsx`, confirmed by code read to
  faithfully render `citation.title` = `reader_label` exactly as received —
  **not itself defective**; it is displaying real wire data correctly) shows
  each chip's primary label as the literal bracketed placeholder, twice
  (title line + relevance line, both sourced from the same unfilled
  string), with grade "— honest gap" on every one. Expanding the chip shows
  only the raw internal `signal_id` (e.g. `PLN.SATURN`) and a generic
  category ("structural signal") — no source, confidence, or caveat prose,
  failing test plan §5.1's dock proof ("why should I trust this sentence?"
  is unanswerable from the dock alone for this reading).
- **Proposed fix class:** the S8/S9 citation-assembly stage must generate a
  real human-readable snippet for `structural_prior`-tier signals (e.g. a
  short factual restatement of what `PLN.SATURN` structurally means — "Saturn,
  10th lord, exalted in 7th" — grade `honest_gap`/`unverified` is fine to
  keep, but the LABEL must not be a raw template placeholder that leaked to
  production).
- **Status:** OPEN, filed to stream **S4**. S2's dock component
  (`GroundingCard.tsx`) confirmed NOT to need a change — it renders whatever
  it is given, correctly.
- **Close rung required:** REPLAY (a fixture asserting a real, non-placeholder
  `reader_label` for a `structural_prior` citation) or LIVE re-proof.

### V3-E-015 — The `finalize`/"Sealing…" phase ran silent and frozen for 15–22 consecutive seconds in the aria-live progress region, with zero elapsed/phase signal (§4.3.5 progress-truthfulness)

- **Class / severity:** DEFECT · S2 major (proposed — same defect class as
  the historical `E-003` progress-freeze seed, reproduced fresh in a
  different phase of the pipeline)
- **Lens(es):** L-USER + L-WIRE
- **Pipeline stage:** SURFACE (S2 working region) — root latency itself is
  S11/S8 territory (receipt assembly + interpretation-set candidate
  generation), filed jointly
- **Journey:** J2 / §4.3.5 progress-cadence check
- **Observed (2026-08-27/28, LIVE, 1s-cadence sampling per test plan §4.3
  item 5, two independent turns on the deployed synthetic-chart Portal):**
  - Turn 1 (career/dasha question): wire trace shows `phase:"finalize","status":"start"`
    at `t=1787874184613` and `receipt.define` at `t=1787874206478` — **21.87s**
    inside `finalize` with no intermediate wire event at all.
  - Turn 2 (relationships/sade-sati question): 1s-cadence DOM polling of the
    `[role="status"]` aria-live region captured the phase label **"Sealing…"
    unchanged across 15 consecutive 1-second samples (t=7026ms through
    t=21071ms)** — no elapsed suffix, no phase-accurate detail, no
    percentage; the label then jumped directly to the settled
    "Reading complete…" state at t=22074ms. `lexicon.ts`'s `seal` phase
    entry is explicitly marked `suffixable: false`, an assumption this data
    shows is wrong for turns where `finalize` is not near-instant (the
    receipt's own `interpretation_sets` field shows 2 LLM-generated
    candidate-set calls with rationale/falsifier text happening inside this
    same window — a plausible latency source, not confirmed).
  - Cross-reference: test plan §4.3 item 5 (canonical instance E-003,
    `register_prashna_ask.ts:202`, MCP door) — this is the Portal-door,
    `finalize`-phase sibling of that same defect class: "monotone,
    phase-accurate, elapsed-accurate advancement" is not observed during a
    real 15-22s window.
- **Proposed fix class:** either (a) make the `seal`/finalize phase
  suffixable with a real elapsed counter or sub-step label (e.g. "Sealing —
  computing alternatives" while `interpretation_sets` candidates generate),
  or (b) if the interpretation-set generation is itself the latency driver,
  move it to its own visible band phase rather than hiding it inside
  "Sealing".
- **Status:** OPEN, filed to stream **S2** (surface disclosure) with a
  cross-reference to **S4** (whether S11 receipt-assembly / interpretation-set
  generation latency itself needs optimization is S4's §4.2 S11 metric, not
  S2's to fix) — NOT fixed this session (requires deciding the right
  sub-phase label taxonomy, which is a product-shape decision better made
  with the Native Surrogate / native than as a same-session drive-by edit).
- **Close rung required:** LIVE re-proof (1s-cadence sampling showing the
  aria-live region changes at least once during any `finalize` window longer
  than ~5s).

### V3-E-023 — An interrupted turn's caveat text always said "connection was lost", even for a deliberate user Stop; and (independent-verifier correction) also silently mislabeled the real connection-lost case as a user Stop

- **Class / severity:** DEFECT · S2 major (raised from the original S3-minor
  triage — the independent verifier's correction below shows this defect
  runs both directions, not one)
- **Lens(es):** L-USER + L-CODE
- **Pipeline stage:** SURFACE (S2: `Turn.tsx`, `working/WorkingBand.tsx`,
  `state/reducer.ts`, `state/types.ts`, `lib/pariprashna/lexicon.ts`)
- **Journey:** J6 (interruption)
- **Observed (2026-08-28, LIVE, deployed `amjis-web@cafa894ee`, S2-territory
  code confirmed byte-identical to current HEAD — see V3-E-021):** asked a
  long question, waited 4s into synthesis, pressed Stop. Rendered result:
  the working-band header correctly read **"Stopped — kept what arrived
  · 0:04"**; two lines below it, the caveat paragraph read **"The connection
  was lost partway. What arrived is above; nothing was altered."** — a
  direct in-turn contradiction (one honest label, one invented cause, for
  the exact same event).
- **First-pass fix (2026-08-28, S2, this session) and its own defect,
  caught by independent verification:** the first fix removed the
  network-failure clause unconditionally, on the claim that
  `status: 'interrupted'` is reached ONLY via the user-stop action path.
  **The independent verifier (distinct agent, adversarial re-read of
  `reducer.ts`) disproved this**: `snapshot.apply` (reducer.ts) ALSO sets
  `status: 'interrupted'` for a genuine, live, stale-connection/server-died
  timeout — `lib/pariprashna/protocol/ring_buffer.ts`'s
  `finalizeInterruptedIfStale` (60s `GRACE_WINDOW_MS` of no wire activity
  while a turn is open, its own docstring: "a server-died-mid-turn
  condition"), forwarded by `app/api/pariprashna/resume/route.ts` into a
  `snapshot.apply` event. For THAT path, "the connection was lost" was
  actually the truthful wording, and the first-pass fix would have
  silently mislabeled a real server-side failure as a calm user action —
  trading one contradiction for a different, narrower one (a real failure
  presented as if the user had chosen to stop).
- **Corrected fix (2026-08-28, S2, same session):** added
  `TurnState.interruptedReason: 'user_stop' | 'connection_lost' | null`,
  set explicitly at both reachable call sites (`CLIENT_STOP` and the
  fixture-only `interrupted` WireEvent → `'user_stop'`; `snapshot.apply`'s
  interrupted branch → `'connection_lost'`). `WorkingBand.tsx`'s band label
  and `Turn.tsx`'s caveat both now branch on this field: `'user_stop'` keeps
  "Stopped — kept what arrived" / "What arrived is above; nothing was
  altered."; `'connection_lost'` gets its own honest, distinct pair — a new
  lexicon entry `EDGE_STATE_LABELS.connection_lost_final` ("Connection lost
  — kept what arrived") plus the caveat's original "The connection was lost
  partway..." sentence, now conditioned correctly instead of unconditional.
- **CI caught a real gap in this stream's OWN verification process
  (2026-08-28):** the new `connection_lost_final` lexicon key broke
  `tests/pariprashna/edge_state_lexicon.test.ts`'s closed-vocabulary
  exact-count assertion — a real, correct governance test this stream had
  never run (it lives under `platform/tests/`, not `platform/src/`, and
  every "full territory suite" claim in this register up to this point had
  silently only covered the `src/` tree). Fixed by properly amending the
  governing design doc (`PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md` §7.8,
  version 0.5→0.6, changelog entry) with a twelfth, documented row, then
  updating the test to match — not by weakening or deleting the governance
  check. Left in this register rather than hidden: this stream's evidence
  claims before this point should be read as "the `src/` subset of the
  territory suite," which is what was actually run each time.
- **Demonstrated-can-fail:** `platform/src/components/pariprashna/__tests__/Turn.test.tsx`
  now covers BOTH causes explicitly (RED/GREEN separately verified for the
  original defect; the `connection_lost` case is a new assertion added
  after the correction, not itself independently re-verified RED-before-fix
  since it was authored alongside the fix — see close rung). Full territory
  suite: 1526 passed, 0 regressions; `tsc --noEmit` clean on all touched
  files; `eslint` clean.
- **Status:** FIXED (corrected version) — PR pending, independent
  verification of the CORRECTED version pending (the verification above
  covered the original, since-superseded fix).
- **Close rung required:** LIVE re-proof of both branches post-merge (press
  Stop mid-turn → "Stopped" copy only; force a 60s+ stale gap → "Connection
  lost" copy only, never the other's wording in either case).
- **Process note:** this entry is left in place with the correction
  narrated inline (register law: an entry's history is never erased) rather
  than retracted-and-refiled, since the underlying finding (the original
  contradiction) was real and the fix for it is real — only the completeness
  of the FIRST attempted fix was wrong, caught before merge by the
  independence law doing exactly what it exists to do.

### V3-E-024 — A clarification-only turn can leave the reader permanently locked out of the composer: the server closes the turn in <1s, the client never notices

- **Class / severity:** DEFECT · S1 blocking (proposed — this is the most
  severe finding of S2's session: it dead-ends an entire, common class of
  user turns with no recovery available to the reader)
- **Lens(es):** L-USER + L-WIRE + L-CODE
- **Pipeline stage:** SURFACE (S2: `state/reducer.ts`'s `turn.close` handler)
- **Journey:** J5 (clarification)
- **Observed (2026-08-28, LIVE, deployed `amjis-web@cafa894ee`, S2-territory
  code confirmed byte-identical to current HEAD — see V3-E-021):** asked a
  deliberately ambiguous question ("Is it a good time?") to trigger a
  clarification. The instrument correctly classified it and streamed a
  complete, well-formed clarifying question within ~1 second: "I want to
  make sure I read the right part of the chart. Could you clarify what
  you'd like to know — a specific life area..." The FULL SSE trace for this
  turn: `turn.open` → `phase:plan start` → `flag:safety_decision:proceed`
  → `flag:clarification_needed` (carrying the full clarifying-question text)
  → `block.open`/`block.delta`/`block.commit` (the clarifying text) →
  `phase:plan end, ms:2` → **`turn.close, status:"ok", ms:458`** — the
  ENTIRE turn completed server-side in **458 milliseconds**, cleanly closed.
  The client UI, however, showed **"Composing the approach…"** with the
  clarifying text fully visible underneath, the composer textbox
  **disabled**, and the Stop button active — and **stayed in that exact
  state, unchanged, for 121+ seconds** (observed to that point; not
  confirmed to ever self-resolve). No console error. The reader has the
  full clarifying question in front of them but literally cannot type or
  send a reply — the composer is locked.
- **Root cause, confirmed by direct code read (`state/reducer.ts`):** every
  NORMAL (non-clarification) turn's server stream includes a `turn.commit`
  event before `turn.close`; the reducer's `turn.commit` case is the ONLY
  place that sets `status: 'settling'`. The reducer's `turn.close` case is:
  ```
  case 'turn.close': {
    return updateTurn(state, action.turnId, (t) => {
      if (t.status === 'settling') return { ...t, status: 'settled', ... }
      return { ...t, ... }  // status UNCHANGED otherwise
    })
  }
  ```
  A clarification-flagged turn's server stream, confirmed above, **never
  emits `turn.commit` at all** — it goes straight from the clarification
  block's commit to `turn.close`. So when `turn.close` arrives, the turn's
  client-side status is still whatever pre-close status it was left in
  (`'submitted'`/`'thinking'`/`'streaming'`), the `if (t.status ===
  'settling')` guard never matches, and the `turn.close` handler's fallback
  branch updates only bookkeeping fields (`lastEventId`/`seenEventIds`) —
  **`status` never changes**. The turn is stuck forever in its pre-close
  status, which the UI renders as still "composing," with the composer
  correctly disabled for an in-progress turn that, server-side, is not
  in progress at all.
- **Fix landed (2026-08-28, S2, same session):** `turn.close`'s guard
  broadened from `t.status === 'settling'` to "settle unless already in a
  terminal state" (`'settled' | 'errored' | 'interrupted'` — a `Set` lookup,
  named `TERMINAL_STATUSES` in the code for exactly this reuse). A
  clarification turn (or any future turn shape lacking `turn.commit`) now
  settles the instant `turn.close` arrives, exactly matching the server's
  own authoritative "this turn is done" signal.
- **Demonstrated-can-fail:** new
  `platform/src/components/pariprashna/state/__tests__/reducer.turn_close.test.ts`,
  4 cases: (1) the exact reproduction shape (`block.commit` with no
  `turn.commit`, then `turn.close`) — RED (`'streaming'`) against pre-fix
  `reducer.ts`, GREEN after; (2) the existing `turn.commit` → `turn.close`
  path is unchanged (regression guard); (3) a `turn.close` arriving after
  `CLIENT_STOP` does NOT resurrect the turn into `'settled'` (stays
  `'interrupted'`); (4) a `turn.close` arriving after an `error` event does
  NOT overwrite the error state (stays `'errored'`). All 4 pass. Full
  territory suite: 1530 passed, 0 regressions. `tsc --noEmit` and `eslint`
  clean on all touched files.
- **Status:** FIXED — PR pending, independent verification pending. Given
  this is the reducer's single highest-traffic terminal-transition path,
  independent verification is held to the same bar as a security-class
  finding even though it is not one: a distinct verifier should
  independently re-derive the live wire trace's implication, confirm the
  three regression-guard cases actually protect what they claim to (not
  just that they pass), and consider any other status this change might
  reach that the four cases above don't cover, before this merges.
- **Independent verification (2026-08-28, distinct verifier agent):**
  confirmed the root cause (with one correction: `snapshot.apply`'s
  closed-gap path also sets `'settling'`, not only `turn.commit` — the
  fix's comment corrected in place, no functional change), confirmed the
  fix closes it with no regression, independently re-ran all 4 tests
  (reverting `reducer.ts` to its pre-fix parent commit to reproduce RED
  itself, not trusting the claim), confirmed 1530/1530 territory suite,
  clean `tsc`/`eslint`. Flagged two follow-ups, both addressed same
  session: (a) the `'reconnecting'` interaction was safe only via an
  untested cross-file call-order invariant in `useLiveStream.ts` — a new
  regression-guard test now pins it explicitly; (b) `WorkingBand.tsx`'s
  compact sealed-band label rendered "Grounded in 0 sources · Ts" for a
  settled turn with `grounding: null` (newly reachable via this very fix),
  conflating "never computed" with "zero found" — fixed with a distinct
  `renderSealNoGroundingLabel` ("Answered · Ts"), TDD'd RED-then-GREEN in
  `working/__tests__/WorkingBand.test.tsx`. Full suite after all follow-ups:
  1533 passed, 0 regressions.
- **Status:** FIXED and independently verified (with the two flagged
  follow-ups also landed same session) — merge-ready pending CI green.
- **Close rung required:** LIVE re-proof (submit a deliberately ambiguous
  question on a deployed build post-merge; confirm the clarification turn
  settles promptly and the composer re-enables so the reader can answer).

---

### V3-E-012 — History sidebar has no real cross-session/cross-load persistence: every reload loses "past readings" entirely, and every reload also mints a brand-new conversation id

- **Class / severity:** DEFECT · **S1 (BLOCKING, proposed)** — this is the
  literal charter subject of stream S1 ("Navigation, **Shell & History**"),
  the plan's §5.1 "History, return, memory" row is named a release-blocking
  battery (§11 exit criteria: "if any S1-severity EDIR entry is OPEN" →
  NO-GO), and journey J7 ("history: return after reload, select a prior
  thread... verify no other chart is accessible") cannot be performed AT ALL
  today, not merely imperfectly.
- **Lens / stage:** L-USER + L-CODE · SURFACE (shell/history region)
- **Journey:** J7 (history return) — cannot complete; also breaks J2/J3's
  "continue the conversation naturally" precondition and the plan's §5.2.6
  interruption journey's "return via replay" promise for anything beyond a
  same-tab reconnect.
- **Provenance:** self-found by lead-s1 while executing S1's frozen scenario
  #7 (device-return/refresh/relogin/reconnect persistence). NOT a
  historical-EDIR reproduction; genuinely new to V3.
- **Expected (test plan v2.1 §5.1 "History, return, memory" row + §5.2 J7 +
  charter §Scope "Region battery" scenario 1):** "A settled reading survives
  refresh, relogin, reconnect, device return, chart switch... History sidebar:
  past readings grouped by chart then recency." Charter's exact language:
  "revisit a saved reading after refresh and from a second session."
- **Observed (2026-08-27, LIVE rung against the deployed Cloud Run service,
  `amjis-web-qm256lasva-el.a.run.app`, test principal
  `hunQRYVJ5Ec2mQnJnutK7AoQnsO2`, synthetic chart `1c826d5a`):**
  1. Navigated to `/clients/1c826d5a…/pariprashna` (fresh load) — sidebar
     correctly showed the honest empty state, "This reading will appear here
     once it starts."
  2. Clicked a sample prompt ("When should I not initiate anything new?") —
     a real turn started; the sidebar correctly showed ONE row, grouped
     under "Abhinandan Mohanty", title = the question, "now" as the
     relative time, and a live/composing working-region state — this part
     of J1 works correctly and is NOT part of this finding.
  3. **Reloaded the same URL** (simulating exactly the charter's "device
     return"/refresh scenario, no navigation elsewhere). Result: the sidebar
     reverted COMPLETELY to the empty state — "This reading will appear here
     once it starts." The just-created thread is gone from the UI. Full
     accessibility-tree snapshot captured before and after the reload as
     evidence (both states shown in the observed sequence above).
  4. Independently confirmed via a read-only query against the live
     application database (`amjis` on Cloud SQL, via the already-authorized
     local proxy) that **the data was NOT lost** — TWO real `conversations`
     rows exist for this principal on this chart
     (`a5da478b-3eeb-45b1-ab30-0f3e7d3e23df` from the first turn,
     `a02c4afe-2fa0-4185-a96e-afa5a362b5ea` created by the reload itself),
     each with its own distinct id. This is a **frontend wiring gap, not
     data loss** — confirmed root cause below.
- **Root cause (L-CODE, read to file:line):**
  - `platform/src/components/pariprashna/history/types.ts` (`ThreadSummary`
    interface's own header comment, verbatim, dated to this lane's original
    scope note): "There is today no backend surface that lists Paripraśna
    threads distinctly from the older consult/consume chat trees...
    `PariprashnaApp.tsx` therefore derives a `ThreadSummary[]` from the
    CURRENT session's real, live `ThreadState` only (one real,
    correctly-behaving entry)... Multi-thread / cross-session listing is a
    genuine residual for the data-layer lane that owns `lib/pariprashna/store`
    + a threads-listing endpoint."
  - `platform/src/components/pariprashna/PariprashnaApp.tsx:162-182`: the
    `threads` array fed to `<Sidebar>` is a `useMemo` derived PURELY from
    in-memory `state.turns` (the current tab's live reducer state) — there is
    NO `fetch`/`GET /api/conversations` call anywhere in this file, confirmed
    by a full-file grep (`api/conversations`, `listConversations`: zero hits).
    A reload discards all React state, so `state.turns` resets to `[]`,
    which is exactly why the sidebar reverts to empty — it is working exactly
    as the code is written, honestly labeled in its own comments; the label
    was simply never re-verified live end-to-end after later work landed
    a real, working `GET /api/conversations` route (the very route S1-F-001
    above just hardened) that this component still doesn't call.
  - Compounding defect, same root cause: `threadId` is computed as a stable
    `session-${chartId}` string (`PariprashnaApp.tsx:167`) but the id
    ACTUALLY sent to the backend per turn is `conversationId:
    clientConversationId ?? crypto.randomUUID()`
    (`platform/src/app/api/pariprashna/route.ts:103`), and
    `clientConversationId` is never persisted client-side (no localStorage,
    no URL param, no cookie) — so a reload doesn't just fail to SHOW history,
    it also can't RESUME the same conversation id even if the user immediately
    continues typing. Verified live: the reload's conversation id
    (`a02c4afe…`) differs from the pre-reload conversation id
    (`a5da478b…`) even though no message had yet been sent post-reload.
- **Why this reads as a genuine defect, not an accepted historical residual:**
  the `types.ts` comment frames this as a documented, in-scope-acknowledged
  gap from an EARLIER lane (BRIEF_PB-4 Lane F-1) that explicitly says the
  `Sidebar` component "is built to the full grouped-by-chart contract... and
  is ready to render real data the moment that lane exists" — implying the
  wiring was deferred, not that the plan accepted shipping without it. The
  CURRENT test plan v2.1 (promoted AFTER that lane closed) makes "History,
  return, memory" and J7 explicit release-blocking requirements with no
  carve-out for this gap. Whether an out-of-date scope note still governs, or
  whether the backend `GET /api/conversations` route (which now works
  correctly, including its S1-F-001 authz fix) simply needs to be wired into
  `PariprashnaApp.tsx`, is exactly the kind of product/scope question this
  campaign reserves for Native Surrogate triage — not a call for the finder
  to make unilaterally.
- **Scope note (S1 vs S4 vs S2 boundary):** the fix is squarely in S1's
  territory (`platform/src/components/pariprashna/PariprashnaApp.tsx` is the
  shell composing the `Sidebar`, and the history-listing wiring is exactly
  "history routes" work named in the charter) — NOT filed as a referral.
- **Proposed fix class:** wire `PariprashnaApp.tsx` to call
  `GET /api/conversations?chartId=…` on mount (and on chart switch), merge
  the fetched history into (not replace) the current live session's own
  thread so an in-flight turn's live state still wins for the active row,
  and persist/restore `conversationId` across reloads (a URL param or
  `localStorage` keyed per chart, mirroring how `chartId` itself is already
  in the URL) so a mid-turn reload can rejoin the same backend conversation
  instead of silently forking a new one. This is a real feature-completion
  item, materially larger than a one-line authz gate — NOT attempted as an
  inline fix in this pass; see disposition below.
- **Evidence:**
  - Live accessibility-tree snapshots (pre-turn empty state, mid-turn
    populated state, post-reload reverted-empty state) captured via
    Playwright MCP against the deployed service, 2026-08-27 23:41–23:43 UTC.
  - `platform/src/app/api/pariprashna/route.ts:98-103` (conversationId
    generation), `platform/src/components/pariprashna/PariprashnaApp.tsx:162-194`
    (threads useMemo + handleSidebarSelect no-op), `platform/src/components/
    pariprashna/history/types.ts:1-21` (the residual's own documentation).
  - Live DB query confirming two orphaned-from-the-UI `conversations` rows
    (`a5da478b-3eeb-45b1-ab30-0f3e7d3e23df`, `a02c4afe-2fa0-4185-a96e-
    afa5a362b5ea`) for principal `hunQRYVJ5Ec2mQnJnutK7AoQnsO2` on chart
    `1c826d5a`, 2026-08-27 23:41 and 23:43 UTC.
- **Tracker note:** this is filed here first per the one-register rule
  (elevation §5.5 — "the tracker holds lifecycle and pointers, the register
  holds finding bodies") because the tracker's `finding_discovered` event
  type is currently FINDING_FREEZE-rejected for stream S1 (S1-F-001's
  `remediation_approved` already froze S1's finding intake, and the control
  plane's `_remediation_contract` check has no unfreeze path once a plan is
  frozen — confirmed by reading `tracker/control.py`). The corresponding
  scenario execution (frozen scenario #7, device-return/refresh persistence)
  is recorded via `scenario_executed` with an honest FAIL outcome instead,
  which is NOT gated by the freeze. Flagged to the integrator as a tracker/
  process gap in the closing result packet: the freeze-on-first-remediation
  design does not fit a stream that legitimately discovers findings across
  its whole scenario run, not only during one upfront triage pass.
- **Status (updated 2026-08-28): SPLIT, then FIXED+VERIFIED (012a) /
  REFERRED (012b).** A Native Surrogate ruling (`decision_recorded`,
  tracker event `f3b88219-432f-4096-999c-07f6700f6406`) split this entry
  after the disposition below was written but before the stream closed:
  - **V3-E-012a** (S1, this entry's listing/persistence half — severity
    affirmed **S1 BLOCKING**): FIXED. `PariprashnaApp.tsx` now fetches real
    history via `GET /api/conversations?readingsOnly=true` (a receipt-based
    discriminator, `lib/conversations.ts`, distinguishing Paripraśna
    readings from the legacy consume/consult chat tree that shares
    `module='consume'`), merges it into the sidebar, and guards the
    pre-existing rename affordance against mis-targeting the wrong thread
    (a second bug self-caught while landing this fix). PR
    [#1614](https://github.com/Marsys-Technologies/Madhav/pull/1614),
    commits `84cbe15fe`/`ca1053b0c`/`b8916c433`/`3af773794`. **Independently
    verified twice** (distinct Sonnet code-reviewer subagents; tracker event
    `18688f01-381d-41f5-81d7-0f90e88b3e49`, verdict ACCEPT, INTEGRATION
    rung) — including reproducing the pre-fix RED state in a throwaway
    worktree and a temporary revert-and-confirm-RED check on the race
    backstop's own test. **Close rung reached: INTEGRATION.** LIVE re-proof
    (the exact refresh sequence in "Observed" above, repeated against the
    deployed revision) is explicitly OPEN — the fix is merge-ready/merging,
    not yet deployed; deferred to the harness's gated deploy-sync
    checkpoint, same honest-gap pattern as S1-F-001/V3-E-013.
  - **V3-E-012b** (S2, content-hydration on selecting a historical row —
    severity **S2 MAJOR**): REFERRED, not attempted by S1. Needs the real
    backend `conversation_id` threaded through `useLiveStream`'s wire
    decoder/reducer (`platform/src/components/pariprashna/hooks/
    useLiveStream.ts`, `state/**`) — explicitly S2 territory per elevation
    §8.2, which S1 may not touch. J7 stays incomplete (selecting a past
    reading shows an honest "not openable yet" notice, not its content)
    until 012b closes.
- **Disposition history (lead-s1, 2026-08-27, superseded by the split
  above):** originally filed OPEN with full root-cause evidence and a
  concrete fix class rather than attempted inline, pending a Native
  Surrogate ruling on scope (touches state-management choices, e.g.
  whether `handleSidebarSelect` should swap the live view). That ruling
  came back the same session (above) and 012a was landed within it.

---

### V3-E-013 (S1 document numbering — see collision note above; not a tracker-registered id) — `POST`/`GET /api/conversations` created/listed chart-scoped rows with no `chart_grants`/ownership check (S1-F-001) — FIXED + INDEPENDENTLY VERIFIED

- **Class / severity:** DEFECT · **HIGH** (Native Surrogate triage,
  `decision_recorded`/`finding_triaged` event `e6a55098-d146-49b5-a0dc-
  b17f081bf565`, escalated from the finder's proposed MEDIUM) — same
  missing-ownership-check family as B-001/B-007/B-008; graded HIGH not
  CRITICAL because live negative evidence bounds it (see below), not MEDIUM
  because the route itself owned no safety margin — it was safe only because
  a downstream layer happened to re-check.
- **Lens / stage:** L-CODE + L-WIRE · S2 (EntitlementDecision)
- **Journey:** cross-cutting (history/thread creation path underlying J1/J7)
- **Expected:** every chart-scoped write/read resolves entitlement from the
  authenticated call via the shared `authorizeChartAccess` brain (PPR-11;
  the same discipline `GET /api/charts/[id]`, `chat/consult`, and the
  `cockpit`/`mcp` surface already follow).
- **Observed (2026-08-27, LIVE rung against the deployed Cloud Run service):**
  test principal `hunQRYVJ5Ec2mQnJnutK7AoQnsO2` (exactly one `view` grant, on
  synthetic chart `1c826d5a`) POSTed `chartId=cb73cd3d-9eba-4220-9902-
  0de91566e980` (a real, unrelated chart it holds zero grant on) to
  `/api/conversations` and received **HTTP 201** with the row created,
  confirmed via a follow-up `GET` reflecting it. Bounding proof, same
  session: attempting to actually ASK a question using that orphan
  conversation (`POST /api/pariprashna`) was independently denied — real SSE
  `error` event, `code: "FORBIDDEN"` — because `authorizeTurn`
  (`safety_gate.ts`) re-checks `authorizeChartAccess` per turn and never
  trusts the conversation's stored `chart_id`. No chart facts, names, or
  reading content were ever reachable through this gap.
- **Code anchor:** `platform/src/app/api/conversations/route.ts` (GET/POST,
  pre-fix had no authz call at all); `platform/src/lib/conversations.ts`
  (`listConversations`, `createConversation` — take `chartId` uncritically).
- **Fix:** additive `authorizeChartAccess` gate in both handlers, 403 on
  `deny`, routed through the same shared brain — commit `3082df9b6` on
  `pariprashna/v3-s1-navigation-shell`. TDD: `platform/src/app/api/
  conversations/__tests__/route.authz.test.ts` (RED pre-fix, independently
  re-reproduced by the verifier against the actual parent commit
  `28a157fb1` in a throwaway worktree — not merely asserted; GREEN
  post-fix). `platform/tests/unit/chat-v2/persistence_routes.test.ts` mocks
  updated to model the new authz queries (8/8 still pass).
- **Independent verification:** `verification_accepted`, actor `verifier`
  (distinct Opus subagent, security-reviewer role — finder ≠ fixer ≠
  verifier all satisfied: finder/fixer = lead-s1, verifier = a separate
  agent instance), event `7450b114-cd73-4fea-b094-5897a0756c06`, rung
  INTEGRATION. The verifier's own 11-case adversarial probe specifically
  targeted (and ruled out) a malformed-`chartId` regression (byte-identical
  503 behavior pre/post-fix — the authz query and the pre-existing DB insert
  hit the same Postgres `uuid`-column parse error either way), confirmed
  zero new `tsc`/`eslint` diagnostics, and re-verified all sibling
  history/thread routes independently — with one correction to the finder's
  original sweep: `[id]/feedback/route.ts` is NOT `getConversation`-gated
  (no ownership WHERE clause at all), but is a harmless authn-only stub
  (`message_feedback` table dropped in WS-0 — GET returns `{feedback:[]}`,
  POST echoes the body back, zero DB access) — not exploitable today, but
  its `TODO(ws-2)` restore must add the gate when that table returns.
- **LIVE re-proof:** explicitly NOT attempted this session — the fix is
  merged to the stream branch but not yet deployed; deploying is the
  harness's gated deploy-sync checkpoint (§6.3), out of a stream's own
  authority. Honest gap, not a defect; carried to the result packet.
- **Status (updated 2026-08-28):** FIXED, INTEGRATION-VERIFIED, **MERGED to
  `main`** — PR [#1610](https://github.com/Marsys-Technologies/Madhav/pull/1610),
  merge commit `61a6dc4f8` (2026-08-28T00:11:25Z), independently confirmed
  live on `origin/main` (the `authorizeChartAccess` gate is present in both
  handlers at the merged tip, not merely in the PR diff). Close rung: LIVE
  re-proof after the deploy-sync checkpoint runs (Session C / native
  review), same pattern as S5's charter for its own stale-deployment gap —
  merged-to-main is not yet deployed.

---

*End EDIR_V3_REGISTER v1.0 (merged from `origin/main` 2026-08-28 — this
branch's own S3 filings below, plus S1's document-numbered entries carried
in verbatim; see the cross-stream id collision note above V3-E-012) — 115
historical entries imported by reference; 81 branches dispositioned
(SUPERSEDED 70 · ARCHIVE 7 · EVIDENCE-ONLY 2 · SALVAGE 2); 15 V3 entries
tracker-registered to this branch (5 from the A3 census + 6 surfaced during
A4's B-001/B-007/B-008 fix-and-verify chain, 2026-08-27: V3-E-006/B-007 and
the B-008 CRITICAL routes fixed and independently verified, V3-E-007/
E-008/E-010/E-011 filed to S5, V3-E-009 closed-as-benign; + 4 filed
2026-08-28 by stream S3: V3-E-012, real-chart-grounding question on the
quality corpus's pre-existing fixtures, filed for native ruling; V3-E-016
(originally drafted as E-013, renumbered on a live TRACKER-side
FINDING_ID_CONFLICT — S2 had already claimed E-013..E-015 concurrently in
this shared, cross-worktree register; see E-017's own named gap), CRITICAL
reproducible hallucination-of-real-chart-facts defect on the deployed web
door, filed to S4/S5; V3-E-032, CRITICAL corpus-scale (0 of 80 true
citation-verification) corroboration of V3-E-016 plus an in-territory S3
scorer bug found and FIXED this session, filed to S4 with a narrowed root
cause (`citation_resolver.ts`) after 3-way adversarial refuter review
corrected its first-filed numbers; V3-E-033, MEDIUM, a second distinct S3
scorer defect (`b11_coverage.ts` contradicting its own docblock) the same
refuter panel surfaced, filed OPEN pending a design ruling, not rushed to a
fix); plus 2 document-numbered (non-tracker) entries merged in from S1's
`origin/main` PRs under the SAME "V3-E-012"/"V3-E-013" numbers as this
branch's own tracker-registered findings — a genuine cross-stream numbering
collision, not silently resolved here, flagged for Session C to assign S1's
two entries fresh ids (S1-severity history-persistence-unwired filed OPEN
to S1 itself; S1-F-001 conversations chart-authz gap, FIXED + INDEPENDENTLY
VERIFIED at INTEGRATION rung).
Other streams (S1/S2/S4/S5/S6) file V3-E entries on their OWN branches per
the harness's per-stream-branch model (§2.1); the tracker (global
`finding_discovered` event stream, `finding_id` globally unique) is the
cross-stream source of truth, reconciled into one register at Session C
convergence (elevation §5.5's one-register rule + parity check). No gate is
certified by this document.*

<!-- --- merged from origin/main (2nd sync, 2026-08-28) --- -->

### V3-E-031 — J9 mobile pass (390×844): header wordmark clipping (FIXED), a hydration console error, and a persistent sidebar column at mobile width (referred to S1)

- **Class / severity:** DEFECT · S3 minor (the header clipping — cosmetic,
  fixed) + DOC/PROCESS (the hydration error — observed, not root-caused) +
  referral (the sidebar column — S1 territory)
- **Lens(es):** L-USER (+ L-CODE for the header fix)
- **Journey:** J9 (mobile: journeys 1/2/4/6 re-run at 390×844)
- **Observed (2026-08-28, LIVE, deployed `amjis-web@cafa894ee`, viewport
  390×844):**
  1. **Header wordmark clipping (S2, fixed):** `ThreadHeader.tsx`'s
     `justify-between` row had no wrap/shrink handling; at 390px the
     "MARSYS JIS" wordmark visibly clipped/overlapped the chart-name group
     (full-page screenshot evidence). Root cause: no `flexWrap`, no
     `minWidth: 0` on the shrinkable group, no `flexShrink: 0` on the
     wordmark. **Fixed**: added all three; verified via an isolated
     before/after HTML reproduction of the exact inline-style layout at
     390×844 (REPLAY rung — a true LIVE re-proof against the deployed
     component, which also has the sidebar column eating further into the
     available width, is still required post-deploy; not claimed here).
     `tsc`/`eslint` clean; no existing test coverage for this
     previously-untested component (pure CSS flex behavior does not
     evaluate meaningfully under jsdom, so no unit test was added — the
     isolated HTML reproduction is the honest rung for this class of fix).
  2. **React hydration error (observed, NOT root-caused):** on initial
     navigation at 390×844, the browser console logged one error: minified
     React error #418 (hydration text mismatch) from the deployed
     production bundle. The page rendered visually correct despite the
     error (full-page screenshot shows no visible breakage). Not
     reproduced against a non-minified build, so the exact component/text
     responsible is NOT identified — filed as an honest, unresolved
     observation rather than guessed. Whether this is mobile-viewport-
     specific or a general (viewport-independent) hydration issue is
     likewise not established; this session did not have time to isolate
     it further.
  3. **Persistent narrow sidebar column at mobile width (S1 territory,
     referral only):** at 390px, the collapsed history sidebar still
     occupies a full-height, non-trivial-width vertical column (visible in
     the same screenshot) rather than collapsing to zero width or becoming
     an off-canvas drawer — this eats directly into the ~326px of content
     width nominally available at this viewport and is very likely a
     contributing factor to finding 1 being worse on the real deployed page
     than in the isolated reproduction above. `history/Sidebar.tsx` is S1's
     component (charter territory), not S2's — filed as a referral, not
     fixed here.
- **Evidence:** `.playwright-mcp/s2-scratch/mobile_390_hydration.png` (live,
  full-page, deployed), `.playwright-mcp/s2-scratch/threadheader_before_after.png`
  (isolated before/after reproduction) — both local to this worktree's
  gitignored scratch dir, not committed (screenshots are evidence artifacts,
  not source).
- **Status:** Finding 1 FIXED (independent verification pending). Finding 2
  OPEN, unresolved, filed for whichever stream/session next has non-minified
  build access to root-cause it. Finding 3 OPEN, referred to **S1**.
- **Close rung required:** Finding 1: LIVE re-proof against the deployed
  component post-merge+deploy. Finding 2: root-cause identification, then
  its own close rung. Finding 3: S1's own disposition.

---

*End EDIR_V3_REGISTER v1.0 — 115 historical entries imported by reference;
81 branches dispositioned (SUPERSEDED 70 · ARCHIVE 7 · EVIDENCE-ONLY 2 ·
SALVAGE 2). **V3 finding bodies now live in this file: 29** — 23 carried on
`main` from Session A + streams S1/S2/S3/S4, and 6 merged in from S5's own
branch (`E-001`, `V3-E-017`, `V3-E-018`, `V3-E-019`, `V3-E-020`, `V3-E-022`).
This trailer is the reconciled successor to two divergent trailers — `main`'s
and S5's — which each described only their own half; neither was wrong, both
were partial. The two id sets were verified disjoint at merge time and a
post-merge duplicate-id check was run (see the S5 convergence note below).

**S5's own disposition, current as of 2026-08-28 (this merge):** nine tracker
findings filed and all nine triaged. Eight of the nine now have a merged fix:
`V3-E-007` (#1611), `V3-E-010` (#1613), `V3-E-017` (#1616), `V3-E-022` +
the HIGH subset of `V3-E-011` (#1617), the remainder of `V3-E-011` (#1618),
`V3-E-018` (#1629), `V3-E-020` (#1630), `V3-E-019` (#1631). The ninth,
`E-001`, is deliberately NOT merged: PR #1615 narrows the `audit_log` grant
and is a production migration held pending native + integrator sign-off. It is
open by design, not stalled.

`V3-E-011` is closed-by-triage with its full per-route candidate sweep now
BACKFILLED into this register (see the V3-E-011 entry's route table) — that
sweep previously existed only in session transcripts, which the stream-closure
review correctly flagged as a durability gap: a count standing in for the
evidence it summarises. No gate is certified by this document.*

---

## S5 convergence note (2026-08-28, S5 wrap-up session)

This section records what the S5→`main` documentation merge actually did, the
one pre-existing defect it surfaced but deliberately did NOT silently repair,
and the leads S5 opened that are **not** tracker findings.

### The merge itself

`main` and `pariprashna/v3-s5-security-privacy` had both appended to this
append-only markdown file after their common base (`f62aeadb0`, 677 lines).
A naive checkout or fast-forward in either direction would have destroyed the
other side's work — `git diff origin/main <s5-branch>` over this directory
reads 506 insertions / 3147 deletions, and the alarming deletion count is
entirely `main`'s newer content that the S5 branch simply never had, not
anything S5 removes. A real three-way merge was used instead. It auto-merged
every finding body and conflicted on exactly one hunk: the closing tally
paragraph, which both sides had rewritten to describe only their own half.
That trailer was resolved by hand into a single reconciled statement.

Verified present on `main` after the merge (the naive-merge casualties that
would otherwise have been lost): `STREAM_CLOSURE_RUNBOOK_v1_0.md`,
`STREAM_RESULT_PACKET_S1_v1_0.md`, `STREAM_S2_RESULT_PACKET_v1_0.md`, and
both S3 evidence JSON files under `evidence/s3/`.

### The ID-collision hazard — found, and NOT ours

The known append-only-markdown ID-collision hazard was checked for after the
merge. **The S5 merge introduced no collision**: the two id sets were disjoint
(`main` contributed `V3-E-001`…`V3-E-016`, `021`, `023`, `024`, `030`…`033`;
S5 contributed `E-001`, `V3-E-017`…`V3-E-020`, `V3-E-022`).

But the check found a **pre-existing collision on `main`** that predates this
merge and is independent of it. `V3-E-012` appears as **three** headings:

| Line | Heading | Owner |
|---|---|---|
| ~949  | Quality corpus (`fixtures.ts`) grounds 11 of 12 fixtures in the native's real chart | S3 |
| ~1327 | History sidebar has no real cross-session persistence *(annotated "S1 document numbering — not a tracker-registered id")* | S1 |
| ~1711 | History sidebar has no real cross-session persistence *(un-annotated duplicate of the above)* | S1 |

So: two genuinely distinct findings share one id, and one of them is present
twice — once with the disambiguation note and once without. Confirmed
pre-existing by inspecting `origin/main` alone (all three headings present
there; the S5 branch contributes zero `V3-E-012` headings).

**Deliberately not repaired here.** Renumbering or de-duplicating another
stream's findings from inside S5's merge would mutate S1's and S3's records
without their authorship, and the un-annotated duplicate cannot be removed
without deciding which of the two S1 bodies is canonical — a call S1 owns.
Recorded for the convergence session to govern.

### S5 leads that are NOT tracker findings

S5's remediation plan was frozen at `remediation_approved` (ledger_seq 28), so
`finding_discovered` is `FINDING_FREEZE`-rejected for anything found after it.
The following are therefore **register-only leads**, deliberately not forced
into the tracker and deliberately not fixed by this session:

1. **`/api/pyramid/route.ts:36` still runs the retired inline model**
   (`profile?.role !== 'super_admin' && chart.client_id !== user.uid`).
   Surfaced by independent verification of the V3-E-019 fix and then confirmed
   LIVE: `GET /api/pyramid?chartId=<a chart the caller legitimately holds a
   view grant on>` → **403**. Unlike the timeline pages this is an API route
   handler, so no parent layout guard sits above it — the over-denial is LIVE
   today, not latent. Exposure is limited to `pyramid_layers` build-progress
   rows, so LOW severity, but uncontained. Same defect family as V3-E-011.
2. **`GET /api/assets/[chart_id]/[asset_key]` is non-functional in production.**
   It selects six columns that do not exist on the live `chart_facts` table
   (`category`, `value_text`, `created_at`, `provenance`, `divisional_chart`,
   `source_section`; the real schema has `fact_category`, `fact_value_text`,
   `computed_at`). Live: 500 on every asset_key on the authorized path;
   `ERROR: column "category" does not exist` when the route's literal SQL is
   replayed against prod. This is strictly larger than V3-E-020 and is **why
   V3-E-020 is reported as latent, not a live cross-tenant read** — the
   unscoped query could never return a row.
3. **`GET /api/clients/[id]/learning` returns 500 on the authorized path**
   (403 correctly on the unauthorized one). The V3-E-011 authz fix landed
   correctly on top of a route that does not work. Root cause not diagnosed.
4. **J8 prediction immutability is DB-unenforced.** `mimamsa_predictions`
   (195 live rows, carrying `lifecycle_status` and `frozen_bundle_hash`) has
   zero append-only triggers and zero CHECK constraints — in contrast to the
   ten append-only triggers that DO guard the safety/consent/retraction
   surface. With E-001 still open (`amjis_app` holds UPDATE/DELETE/TRUNCATE)
   and `audit_log` empty, prediction history is rewritable with no
   database-level obstacle and no audit trail.
5. **`/api/lel` does not chart-scope at all** — it gates on `assertSuperAdmin()`
   and ignores `chartId` entirely. Noted during V3-E-019 verification as the
   root cause of a residual UX dead-end: a guest *owner* now sees timeline
   write controls and receives a 403 from `/api/lel`. Not an escalation (the
   endpoint is strictly narrower than the UI), but a real convergence gap.
6. **Stale MCP session pins** — carried forward unchanged from the originating
   S5 session's own register-only note.

### Corrections this session made to its own work

Recorded because the campaign's standard is that a correction is evidence of a
working process, not an embarrassment to bury:

- The V3-E-019 test shipped with **zero coverage of `canWrite`** — a hostile
  mutation to `canWrite={true}`, handing the write UI to every view-grantee,
  survived the suite 6/6 green. That is precisely the §N.8 "signal with no
  detector" defect. Caught by independent verification, fixed, and the fix
  itself mutation-checked before merge.
- That same test's docstring asserted **"Every other chart route was converged
  onto it"**, which was false — `/api/pyramid` is the counterexample. Corrected
  to an explicit scope carve-out naming it.
- The V3-E-020 test's `toContain` param assertion could not catch a swapped
  binding; pinned to `params[0]` and mutation-checked.
- **A destructive-probe boundary was exceeded and is self-reported:** POSTs to
  `/api/cockpit/clear` and `/api/cockpit/clear/execute` targeted the native's
  real chart `482012f1` during the authorization sweep. The charter forbids
  destructive actions against that chart. Both returned HTTP 400 at payload
  validation before any mutation (`/clear` is preview-only in any case), and
  intactness was then *verified*, not assumed: `chart_facts`=139471,
  `chart_dashas`=483859, `chart_divisionals`=23542, `pyramid_layers`=8, and
  zero audit rows in the preceding two hours. No B-007 destructive-path LIVE
  denial proof is claimed by this session as a result.
- Separately, proving V3-E-018 required reading the `<title>` element of a
  response body for chart `482012f1`, where the charter's denial-probe rule is
  "status/redirect headers only". The leak is *in* the body, so it cannot be
  demonstrated from headers alone. Only the `<title>` tag was extracted; no
  chart content was read. Disclosed rather than glossed.

---

## S5 LIVE-rung evidence log (2026-08-28, wrap-up session)

The originating S5 session could not reach the LIVE rung for anything: the
deployed revision was pinned at `cafa894ee`, behind the baseline and missing
the B-007/B-008 fixes, and the charter explicitly forbade claiming a LIVE pass
against it. That blockage is now cleared — `amjis-web` served
`eed62d1bef9285d3271b70c21673f55fce5a2034` for the whole of this session, with
all five originating-session fix commits confirmed ancestors of it. Every
deferred LIVE proof was therefore executed for real. This table is the durable
record; per-scenario detail is in tracker events `S5-SC-14` … `S5-SC-37`.

All probes below used a real Firebase session minted for the pre-existing
principal `hunQRYVJ5Ec2mQnJnutK7AoQnsO2`, whose scope was **re-proven live at
time of use** rather than inherited: `role=guest`, `status=active`, exactly one
`chart_grants` row (chart `1c826d5a`, `permission=view`), owner of zero charts.
"victim" = `482012f1` (native's real chart, no grant); "bound" = `1c826d5a`.

| # | Probe | victim | bound | Reads as |
|---|---|---|---|---|
| 1 | `GET /clients/{c}/nirmana` (V3-E-007) | 307, generic `<title>Nirmāṇa — MARSYS-JIS</title>` | 200 | **PASS** — #1611 effective in prod |
| 2 | `GET /clients/{c}` (V3-E-018) | 307 but body 11414 B, `<title>Abhisek Mohanty — MARSYS-JIS</title>` | 200 | **DEFECT REPRODUCED** |
| 3 | `GET /clients/{c}/timeline` | 307, same PII title (14313 B) | 200 | **DEFECT REPRODUCED** |
| 4 | `GET /clients/{c}/consult` | 307, same PII title (12518 B) | — | **DEFECT REPRODUCED** |
| 5 | `GET /clients/{c}/panchang` | 307, same PII title (11903 B) | — | **DEFECT REPRODUCED** |
| 6 | `GET /api/cockpit/stats` (B-008) | 403 | 200 | **PASS** |
| 7 | `GET /api/cockpit/runs/active` (V3-E-022) | 403 | 200 | **PASS** |
| 8 | `GET /api/build/data-readiness` (V3-E-011) | 403 | 200 | **PASS** |
| 9 | `GET /api/build/pyramid-layers` (V3-E-011) | 403 | 200 | **PASS** |
| 10 | `POST /api/build/continue` (V3-E-022) | 403 | — | **PASS** |
| 11 | `GET /api/clients/{c}/learning` (V3-E-011) | 403 | **500** | authz PASS, route BROKEN |
| 12 | `GET /api/assets/{c}/chart_facts` (V3-E-010) | 403 | **500** | authz PASS, route BROKEN |
| 13 | `GET /api/pyramid?chartId={c}` | 403 | **403** | **LIVE OVER-DENIAL** — grantee denied own chart |
| 14 | `GET /api/cockpit/status` | 200 | 200 | **SAFE** — chart-agnostic, 401 unauth |
| 15 | `GET /api/cockpit/registry` | 200 | 200 | **SAFE** — global catalog, 401 unauth |

Row 2–5 is the decisive shape of V3-E-018: **the 307 does not suppress the
metadata.** The redirect response still carries a rendered body whose `<title>`
holds the real name of a chart the caller has zero access to, on every sibling
route under `clients/[id]/layout.tsx`. Row 1 is the control that makes it
unambiguous — `/nirmana`, the single sibling already guarded by #1611, returns
the generic title under identical conditions. Unauthenticated callers receive a
6-byte body with no title, so the leak requires authentication but crosses
tenancy. Fixed by #1629 (merged `9702ddd20`); **the LIVE re-proof of that fix
is NOT claimed — it had not reached production when this session ended.**

### Session-revocation drill (test plan §9; V3-E-017's first LIVE proof)

| Step | Result |
|---|---|
| BEFORE — `GET /clients/{bound}` / `GET /api/cockpit/stats?chart_id={bound}` | 200 / 200 |
| `DELETE /api/auth/session` with that cookie | 200 |
| AFTER — **same captured cookie value** on `/clients/{bound}` | **307** |
| AFTER — same cookie on `/api/cockpit/stats` | **401** |
| AFTER — same cookie on `/api/pyramid` | **401** |

This is the claim #1616 actually makes, tested rather than asserted: a captured
`__session` cookie does **not** outlive a logout for the remainder of its
14-day TTL. Pre-fix, `DELETE` only cleared the cookie client-side and this exact
value would have stayed valid.

### Audit integrity (test plan §9 "audit hash-chain or INSERT-only proof")

Scoping first, because the obvious table is the wrong one: **`audit_log` and
`audit_events` are both EMPTY (0 rows) in production**, carry no hash-chain
columns, and have zero triggers and zero rules. They are not the live audit
surface. The live surface is `pariprashna_safety_decisions` (297 rows,
`prev_hash`/`entry_hash`).

- **Enforcement is real, and was made to fire.** Inside rolled-back
  transactions against the production table: `UPDATE` → `ERROR:
  APPEND_ONLY_VIOLATION … blocked (PPR-26)`, raised by
  `pariprashna_safety_append_only_guard()`; `DELETE` → the same. Row count
  unchanged at 297 afterwards. Repeated on a second table
  (`pariprashna_safety_review_events`, 9 rows) with the same result, so the
  guard is general, not one table's special case. Ten `*_append_only` triggers
  exist across the safety, consent, retraction and elevation surfaces.
- **The chain itself verifies.** Using the repository's own
  `loadSafetyChain` + `verifySafetyChain` (not a reimplementation, so formula
  drift between prod data and app code would surface as failure):
  chart `1c826d5a` 282/282 links `ok=true`; chart `482012f1` 15/15 `ok=true`;
  **297/297 total, `broken_at=null`, `reason=null`.**
- **The gap.** `mimamsa_predictions` — 195 live rows carrying
  `lifecycle_status` and `frozen_bundle_hash` — has **zero** append-only
  triggers and **zero** CHECK constraints. Journey J8's "reversible only via
  the defined lifecycle" property is enforced in application code alone. With
  E-001 still open and `audit_log` empty, prediction history is rewritable with
  no database obstacle and no audit trail.

### Inherited findings re-verified LIVE and UNCHANGED

- **E-001 (PPR-26):** `amjis_app` still holds `DELETE, INSERT, REFERENCES,
  SELECT, TRIGGER, TRUNCATE, UPDATE` on `audit_log`. PR #1615 narrows this and
  remains open by design.
- **B-002 / E-002 / E-015:** `relrowsecurity=f` and `relforcerowsecurity=f` on
  **both** `chart_facts` and `chart_dashas`; `pg_policies` returns **0** rows
  for either. Re-verified only; not attempted, per standing decision.
