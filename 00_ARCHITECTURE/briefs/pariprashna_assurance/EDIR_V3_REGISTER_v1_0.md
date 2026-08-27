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
  - "1.1 (2026-08-28, verification-closeout session): §1 gains a
    post-census reconciliation paragraph. An independent check found 87
    live unmerged branches matching the census's own two patterns against
    the census's stated 81; re-running the census's exact method confirmed
    87 (68 pariprashna/* + 19 codex/pariprashna-*) and showed the delta is
    fully explained — 0 of the 81 census branches were deleted/merged away,
    and 6 new branches (the P2-B-001/B-002/B-004/B-007/B-008 fix branches
    plus the session-a-governance-docs branch) were created after the
    census's own stated snapshot and are already squash-merged onto main.
    No coverage gap found; no new V3 entry opened. §3's per-branch table and
    the 81 baseline are left as the historically accurate count at the
    census's own timestamp, not restated as a live figure."
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

**Post-census reconciliation (verification-closeout session, 2026-08-28,
later same day).** An independent check after this census counted 87
unmerged branches matching `origin/pariprashna/*` OR
`origin/codex/pariprashna-*` live (68 for `pariprashna/*` alone), against
this section's 81 — reconciled here rather than left as an unexplained
drift. **Method re-run exactly as stated above:** `git fetch origin --prune`
against current `origin/main` (`b63abc7592233536757c5f1ffa0103f86247ee43`,
descendant of this census's `cc6b1a55e` baseline), then the same two-pattern
`git branch -r` match. Result: 87 (68 + 19), matching the independent
check's own figure exactly. Diffing the live 87 against this census's named
81 (`comm` on the sorted branch-name lists): **all 81 census branches are
still present — zero were merged-and-deleted or otherwise disappeared.**
The gap is entirely additive: 6 branches not in the original 81 —
`pariprashna/p2-b001-chart-authz-fix`, `pariprashna/p2-b002-narrowed-proof`,
`pariprashna/p2-b004-mcp-turn-record`, `pariprashna/p2-b007-cockpit-clear-authz`,
`pariprashna/p2-b008-cockpit-authz-sweep`, `pariprashna/session-a-governance-docs`
— were created 2026-08-28 between 00:25 and 03:03 IST, i.e. **after** this
census's stated `census_taken: 2026-08-28` snapshot, as the P2-B-001/B-002/
B-004/B-007/B-008 fix branches and the Session A governance-docs branch
themselves (see B00x outcome docs and PR #1597/#1599/#1602/#1603). Per-branch
`git diff --numstat` against current main confirms all 6 are byte-identical
to main on every file they touch — each was squash-merged (their head
commits are not ancestors of `origin/main` by `git merge-base
--is-ancestor`, confirming squash rather than fast-forward/merge-commit, but
content parity confirms the squash landed cleanly) and origin never deleted
the source branch ref post-merge. **Arithmetic: 81 (census) − 0 (deleted
since) + 6 (created after the census's own stated snapshot, now fully
merged) = 87 (current), which balances exactly.** No branch that existed at
census time was missed by the census's coverage; the discrepancy is fully
explained by the census's own stated timestamp predating six branches this
same campaign created afterward. **This is not filed as a V3 entry**: §4's
threshold is a genuine, unexplained divergence, and none survives here — see
the register's own preamble ("severity is assigned at triage," not asserted
by the checker who merely confirms arithmetic balances). Any future reader
comparing this section's "81" against a live `git branch -r` count should
expect a similarly growing, fully-explained delta as further P2+ work opens
branches — re-run the method above rather than treat "81" as a live
invariant.

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

### V3-E-012 — Two V3-E-011 candidates upgraded from code-read match to PoC-confirmed exploitable: `cockpit/runs/active`, `cockpit/sse`

- **Class / severity:** DEFECT · S2 (MEDIUM, proposed — read-disclosure of
  another user's chart build-state and live progress, not destructive; same
  tier as V3-E-010's two members and the `GET /api/cockpit/runs` history
  disclosure B-008 itself fixed)
- **Lens / stage:** L-CODE · CROSS
- **Provenance:** V3-E-011's addendum already named these two (plus
  `cockpit/runs/[id]/assets`) as members of the same defect family, on the
  strength of the B-008 verifier's code-reading judgment ("share the same
  auth-only-no-ownership shape"). This entry is the independent evidence
  upgrade the register's own §N.8-equivalent standard (a claim needs a real
  detector behind it, not an assertion) calls for — it does not report a new
  discovery.
- **Observed (2026-08-28, verification-closeout session, gap-2 B-007/B-008
  re-verification):** a freshly-briefed, context-isolated Independent-
  Verifier subagent — given only the PR numbers/merge SHAs and the fix
  description, with no access to the original verifier's notes or this
  register — was tasked to try to break the merged B-007/B-008 fixes and
  hunt for adjacent bypasses. It found no defect in the B-007/B-008 fixes
  themselves (both independently re-reproduced pre-fix and re-confirmed
  fixed on current main, including parameter-shape confusion, grant-record
  edge cases, and enumeration-oracle checks — all ruled out), but
  independently rediscovered these same two V3-E-011 candidates and, unlike
  the original scan, verified them at PoC level:
  - `GET /api/cockpit/runs/active` (`platform/src/app/api/cockpit/runs/active/route.ts:11-16`):
    calls only `getServerUser()` — no `requireChartPermission`/
    `authorizeChartAccess` call, no `charts`/`chart_grants` query anywhere in
    the file. A written-and-executed proof-of-concept request (attacker uid,
    no ownership/grant relationship, arbitrary `chart_id`) returned **HTTP
    200** with the victim chart's full active-run `plan` array,
    `current_asset_id`, and per-asset `state`/`error` strings — confirmed via
    mock-call inspection that no ownership-scoping query ever runs. No
    `__tests__` directory exists for this route at all, unlike every route
    B-008 did fix. The PoC test was removed after confirming the result;
    `git status` on the verifier's worktree showed zero residual diff.
  - `GET /api/cockpit/sse` (`platform/src/app/api/cockpit/sse/route.ts:15-20`):
    same pattern — only `getServerUser()`, `chart_id` taken from the query
    string with no ownership check, streaming `run.state_change` and
    `asset.progress` (including live `rows_written`) for that chart
    indefinitely to any authenticated caller. Its own test file
    (`sse/__tests__/route.test.ts`) asserts only the 401-unauthenticated and
    400-missing-param cases — no ownership test exists, corroborating that
    this route was never in either PR's diff.
  Both remain live and exploitable on current `origin/main` as of this
  entry's date. `cockpit/runs/[id]/assets` (V3-E-011's third named member)
  was not re-examined by this session and remains at its prior evidence
  level.
- **Why this is NOT fixed in this session:** per this closeout session's own
  brief, a re-verification finding is filed, not silently patched, and
  anything touching live authorization/data-exposure triggers elevation §10
  self-pause rather than in-session remediation — the same discipline
  V3-E-010/E-011 were already held to when Session A found them. Fixing two
  more routes is exactly the kind of scope growth the elevation's
  bounded-scope discipline (§5.3) reserves for the owning stream, not an
  ad hoc verification pass.
- **Proposed fix class:** identical, already-proven pattern —
  `requireChartPermission({access:'read'})` on both routes, placed after the
  existing `getServerUser()` and required-`chart_id` checks and before any
  DB read or stream subscription, mirroring `runs/route.ts` GET and
  `stats/route.ts` exactly as B-008 already did for their siblings.
- **Status:** OPEN, filed to stream **S5** (V3-E-011's existing destination —
  this is an evidence upgrade to two of its named candidates, not a new
  stream assignment). Close rung: both routes gated and each carrying a
  passing DENY/ALLOW authz test, per the same bar every other cockpit route
  in this family was held to.

---

*End EDIR_V3_REGISTER v1.0 — 115 historical entries imported by reference;
81 branches dispositioned (SUPERSEDED 70 · ARCHIVE 7 · EVIDENCE-ONLY 2 ·
SALVAGE 2); 11 V3 entries (5 from the A3 census + 6 surfaced during A4's
B-001/B-007/B-008 fix-and-verify chain, 2026-08-27: V3-E-006/B-007 and the
B-008 CRITICAL routes fixed and independently verified, V3-E-007/E-008/E-010/
E-011 filed to S5, V3-E-009 closed-as-benign). No gate is certified by this
document.*
