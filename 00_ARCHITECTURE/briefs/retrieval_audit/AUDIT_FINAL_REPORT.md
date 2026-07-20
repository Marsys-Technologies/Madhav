---
artifact: AUDIT_FINAL_REPORT.md
canonical_id: RETRIEVAL_AUDIT_FINAL_REPORT
version: 1.0
status: COMPLETE — final deliverable of the six-lane retrieval-plane audit (brief §F.3)
authored_by: Claude (conductor, final-report pass), 2026-07-19
governing_brief: 00_ARCHITECTURE/briefs/RETRIEVAL_AUDIT_EXECUTION_BRIEF_v1_0.md §F.3
audit_subject: RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md (audited at v1.2; amended to v1.3)
inputs:
  - LANE_A_REPORT.md .. LANE_F_REPORT.md (six-lane code audit)
  - GROUND_TRUTH_REGISTER.md (v1.0 — §F.1 adjudication, 37 §1 claims + 17 new-gaps + 52 feasibility notes)
  - RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md v1.3 (§F.2 amendment — changelog + §8.5 C-1..C-6)
  - STATE.md (conductor transition ledger)
---

# Retrieval-Plane Audit — Final Report

## 1. Executive summary

The Retrieval-Plane Elevation Plan (v1.2) was a design document asserting the
current state of the MARSYS retrieval plane — catalog topology, envelope
adoption, planner wiring, multi-LLM adaptation, trust seams, data-plane
coverage — as the factual baseline for a multi-phase rebuild aimed at the
settled Paripraśna target architecture. This audit ran six parallel lanes
(A–F) of read-only code inspection against that baseline, then reconciled the
lane findings into a ground-truth register, absorbed the corrections into the
plan (now v1.3), and produced this report. Aggregate finding: **the plan's
planner/taxonomy section was highly accurate (Lane C: 7/7 confirmed), but its
catalog, envelope, and data-plane sections carried real staleness** — 13 of 37
§1 factual claims required correction, and 17 genuine defects the plan never
claimed were newly surfaced. None of the corrections invalidate the plan's
direction; they sharpen scope (the single largest is R-3.1's re-scope from a
flat superset enum to a decomposed scope tuple) and one item is already done.

Separately, Lane F cross-checked the plan against the Paripraśna target
architecture and surfaced **six genuine architectural tensions (C-1..C-6)** —
a `depth` parameter D-15 abolished, a live `audience_tier` violation the plan
edits around but does not excise, missing reader-facing signal prose, a
verbosity knob on the D-15 line, a missing third planner outcome, and the
load-bearing consumer contract sequenced last. These are **raised, not
resolved** — they are decisions for the native to rule on, not defects the
audit could adjudicate. The plane baseline is now trustworthy to build from;
the six rulings gate the phases that touch the Paripraśna boundary.

## 2. Per-lane verdict counts

| Lane | Territory | Model / effort | Verdict breakdown | Headline finding |
|---|---|---|---|---|
| A | Catalog & registration reality | sonnet, default | 4 CONFIRMED / 3 STALE-CORRECTED / 1 PARTIALLY-CONFIRMED / 1 UNVERIFIABLE | The "three-catalog" claim conflates two tables — catalog #2 is a **6-entry served `ToolContract` catalog**, not the cited 76-row `ToolReconciliationEntry` audit table; and `getCatalog()`↔`route.ts` bootstrap **disagree live** (118 vs 122), the same D9/D10 bug class the plan calls fixed. |
| B | Envelope & budget reality | sonnet, default | 6 CONFIRMED / 2 CORRECTED / 1 WRONG / 1 CONFIRMED-BUT-UNDERSTATED | `result_clipper.ts` is **NOT orphaned** (live caller `bulk_context/bundler.ts:47`); `still_over_budget` is dead on every path; `chart_header` fails silently twice with zero flag; unclamped surface is ~36/115 tools, not "reference tools." |
| C | Planner & taxonomy reality | opus, high | **7/7 CONFIRMED** (2 with precision nuance), 0 stale/wrong | Most accurate section of the plan. **Structural finding:** the three intent taxonomies are three orthogonal axes, not dialects of one vocabulary — R-3.1's flat superset enum **cannot** unify them; must re-scope to a decomposed scope tuple with `IntentClass` derived. |
| D | MCP edge & adaptivity reality | sonnet, default | 7 CONFIRMED / 2 CORRECTED / 0 WRONG | Description leakage is **11 instances / 8 files**, not 3 — including `ephemeris_cache_native_lifetime.ts` leaking the native's **full PII** (name/DOB/birth time/place); fail-open dev token is a **13-file** duplicated pattern; `parity_check.ts` may be dead code. |
| E | Data-plane & service coverage reality | opus, high | CONFIRMED / STALE / all counts **UNVERIFIABLE-NO-DSN** (source-inspection fallback) | `ka_graha_sancara` (arbitrary-datetime ephemeris) is a **live in-code dark service** blocking all date-parameterized position queries, named nowhere in plan/strategy; L0 stratum is **~39 physical tables, not 13**; `kala_timeline` is built-but-unwired (one-line fix). |
| F | Paripraśna rebuild interface | opus, high/xhigh | 15 requirements: **8 COVERED / 4 UNDER-SPECIFIED / 3 CONTRADICTED** | Six contradictions raised (C-1..C-6), none adjudicated per brief §D.4. Headline C-1: R-5's `prashna_ask` contract carries a `depth` param **D-15 explicitly abolished** (cheap fix — tool unbuilt); plus a live `audience_tier` violation R-3.2 edits around. |

## 3. Top-10 corrections (ranked by load-bearing weight for an implementer)

1. **[GT-24, Lane C] Orthogonal-taxonomies structural finding — R-3.1 re-scope.**
   The three intent vocabularies (DR-8 technique+domain / Vidhi domain×depth-fused
   / pipeline epistemic answer-mode) are **not dialects of one taxonomy** but
   three orthogonal axes. A flat superset-rename enum cannot unify them; the only
   faithful unification is a decomposed scope tuple
   `{answer_mode × domain × depth × horizon (× intervention × entitlement)}` with
   `IntentClass` **derived**, not a peer enum. *The single biggest plan
   correction* — it changes what R-3.1 must build.
2. **[GT-3, Lane A] The three-catalog claim conflates two differently-typed tables.**
   Catalog #2's 76 `tool_metadata.ts` rows are typed `ToolReconciliationEntry` (an
   audit/coverage map, not served). The actually-served contract catalog is
   `TOOL_CONTRACTS` in `lib/contract/registry.ts` = **6 entries**. R-1's compiler
   must absorb the real 6 and separately retire the 76-row audit table.
3. **[GT-4/GT-40, Lane A] The D9/D10 bootstrap bug class is LIVE, not historical.**
   `getCatalog()` and `route.ts` still disagree today: D6-synergy (2 caps) + MARO
   (3 caps) are in `route.ts` but absent from `catalog.ts`; `synth_compose_large_n`
   is the reverse. The exact failure class the plan says is fixed — unfixed for 6
   capabilities. R-1.3 must enumerate all 6, not only D9/D10.
4. **[GT-32/GT-42, Lane D] Description-leakage severity undercount, incl. native PII.**
   Leakage is 11 instances across 8 files, not the plan's 3; the strongest is
   `ephemeris_cache_native_lifetime.ts:24-29` embedding the native's full
   name/DOB/birth-time/birthplace verbatim in a served resource description — a
   PII leak, not just a row-count leak. R-1.6's hygiene scan must reach beyond
   `description:` fields.
5. **[GT-17, Lane B] `result_clipper.ts` is NOT orphaned.** It has a live caller
   (`adapters/bulk_context/bundler.ts:47`) on the bulk-context path and is a
   narrower-purpose LLM-context clipper, not dead code. R-2's "evict
   result_clipper" must preserve this live consumer.
6. **[GT-1, Lane A/B] The "123 descriptors" count is not a reproducible invariant.**
   `getCatalog()`→118, `route.ts`→122, `server.tool(`→115, typed consts→116. Use
   "≈118, census must be codegen-derived"; no single grep reproduces one number.
7. **[GT-1/GT-51, Lane E] The L0 table-count undercount.** The "13 tables" L0
   stratum is actually **~39 physical tables**; and the census's single-directory
   grep mis-flagged served tables (`chart_panchanga`, `bg_dignity_reference`,
   `bg_sign_medical`) as dark. R-1.5's harness must grep all three serving paths.
8. **[GT-18/GT-45, Lane B] `still_over_budget` is dead on every path**, not "unread
   by four callers" — even `finalizeMcpBudget` recomputes its own check rather than
   reading it.
9. **[GT-19/GT-48, Lane B] Unclamped surface is ~36/115 tools** (15 of 21
   registration files), materially bigger than the plan's "reference tools."
10. **[GT-21, Lane C] B.11 injection pushes only `pattern_register` live;
    `cluster_atlas` is a dead constant** (lives in the detection membership list,
    never in a `.push()`). Plan's naming needs the fix; the substance (a dead tool
    reaches the floor) holds.

## 4. Top-10 new gaps (defects the plan never claimed)

1. **[GT-50, Lane E] `ka_graha_sancara` is a live in-code dark service.**
   `call_service_wrappers.ts:200-208` returns "not yet wired to a compute sidecar
   endpoint" — blocking ALL date-parameterized "positions at time T" retrieval.
   Named nowhere in plan or strategy. → absorbed R-1.5.
2. **[GT-49, Lane E] `kala_timeline` is built-but-unwired.** A complete handler
   (`platform-mcp/src/tools/kala_timeline.ts`, `registerKalaTimeline`) is never
   imported into `server.ts`. One-line wiring fix, mis-grouped with build items —
   R-1.5.2 must split "dark-unbuilt" from "dark-unwired."
3. **[GT-56, Lane C] `registry_data.ts`'s two TS copies have already drifted**
   (type-import line `'./types'` vs `'./types.js'`) with no parity gate — the
   triple-copy risk materializing now, in the floors R-3.3 will extend.
4. **[GT-47, Lane B] `chart_header` fails silently with no flag in two layers** —
   inner (`chart_header.ts:90-93` swallows DB errors, fields stay null) and outer
   (3 `registry_bridge.ts` sites catch→null) — contradicting the §N.6 honesty
   discipline the same files apply elsewhere. → R-2.1 (fail-loud).
5. **[GT-46, Lane B] Two handler files emit static `judgment_flags: []`**
   (`register_p1_synthesis.ts:82`, `register_p1_reference.ts:87`) — field present,
   no honest-gap machinery at all. → R-2.2.
6. **[GT-44, Lane D] The fail-open dev token is a 13-file duplicated pattern**, not
   a one-liner. R-0.5 must extract a shared `validateServiceToken` or enumerate all
   sites.
7. **[GT-36, Lane D] `parity_check.ts` may be dead code** — no CI/test/script
   invokes `checkParity()`/`runParityCheck()`; a newer
   `scripts/manifest/parity_validator.ts` may be the live successor. R-0.5 must
   confirm the file is even in the enforcement path before "fixing" it.
8. **[GT-42/GT-54, Lane D] `empty_reason` / resource-description leak paths** — d8's
   `TEMPORAL_EMPTY_REASON` leaks a native-derived count ("0/13,364 dated on lahiri")
   in a served `empty_reason` string; same leak class as descriptions, different
   code path. → R-1.6 (widen scan).
9. **[GT-43, Lane D] `get_dashas.ts:123` embeds 601,443 rows**, which disagrees with
   CLAUDE.md's canonical seal (chart_dashas=536,471) — leaked AND apparently
   stale/wrong. → R-1.6 + flag for L1 seal cross-check.
10. **[GT-55, Lane A] The one CI "completeness" test is blind to ~63 of ~120 tools.**
    `m8_e2e_proof.test.ts` "G12 — REGISTERED_TOOL_COUNT is truthful" checks a
    locally-redefined 57 against a partial subset; plus stale hand-counts
    (`registry_bridge.ts` census says 20 vs 25; `register_p1_synthesis.ts` header
    says 3 vs 6). → R-1.2d (codegen census kills all hand-counts).

*(Full 17-item set: GT-40..GT-56 in GROUND_TRUTH_REGISTER.md Part B. GT-41 —
`register_d4_graph.ts` dead code; GT-52 — `reference_*` vs `bg_*` supersession
(retire, not wire-up); GT-53 — `finalizeMcpBudget` cross-cutting flag emitter.)*

## 5. The Paripraśna alignment table (Lane F, 15 requirements)

**8 COVERED / 4 UNDER-SPECIFIED / 3 CONTRADICTED** (F-R4, F-R5, F-R14a).

| # | Requirement (PARIPRASHNA §/decision) | Verdict | Plan phase | Gap detail | Severity |
|---|---|---|---|---|---|
| F-R1 | Engine headless-callable (§4/§6.5; A-07) | UNDER-SPECIFIED | R-5.1 consumes | Plan consumes headless callability at R-5 but never builds it; extraction is PARIPRASHNA P2', no cross-cite. | Blocks R-5; latent |
| F-R2 | `density_contract` mandatory on every descriptor (A-05, §8.6) | COVERED | R-1.1 + R-2.5 | Aligned. | — |
| F-R3 | One loop, two doors — `prashna_ask` (A-07, §6.3, T-2) | COVERED (seq. tension) | R-5.1 | Correctly specified; but the most load-bearing consumer is scheduled last. See C-6. | Sequencing |
| F-R4 | **Provenance stamp, NOT session pin** (D-16, §11.4) | **CONTRADICTED** | §0 diagram + R-5.2 | Plan retains the retired construct by name and session-state shape D-16(b) abolished. | Blocks R-5 correctness |
| F-R5 | **No `depth`/`tier` parameter** (D-15, §13.4) | **CONTRADICTED** | R-5.1 contract | `prashna_ask` contract carries `depth` — direct D-15 violation, and redundant (`scope_tuple?` derives depth). See C-1. | Cheap fix now |
| F-R6 | `register` block for reader labels (A-18, §8.7) | COVERED | R-1.1 + R-2.3a | Strong alignment. | — |
| F-R7 | NO-LEAKAGE four ways (A-19, §14.10) | UNDER-SPECIFIED | R-1.1 / R-5.2 | Arms 2 & 4 (registry `calibration_context_only` exclusion + CI canary) not spelled out; `prashna_ask` exposes the loop tool set, so arm-2 exclusion is a hard precondition. | Med-high |
| F-R8 | D-14 supply side — reader-legible signal content (§13.6) | UNDER-SPECIFIED | R-2.3a | Token labels covered; the `signal_reader_text` editorial pass (PARIPRASHNA P5') is absent — cited signal content is still internal-register text. See C-3. | High (honesty claim) |
| F-R9 | Prediction-detection hooks (§14.2) | COVERED | R-2 §8.6/§8.7 + R-2.3 | Plane-side supply explicitly covered; detection is engine-side. | — |
| F-R10 | Engine never branches on which door (§6.5) | COVERED | §0 + R-4.1-4.2 | Projection selection at the edge; door-agnostic. | — |
| F-R11 | Clarification as a third planner outcome (A-29, §6.6) | UNDER-SPECIFIED | R-3 | R-3 preserves the two-outcome shape; no `ClarificationRequest`, no pre-plan ledger check. See C-5. | Med |
| F-R12 | One registry, many generated projections (D-08/OT-7) | COVERED | §2 + R-0.1/R-1/R-4 | The plan's spine; fully aligned. | — |
| F-R13 | Mutation capability class; sidecars into registry (A-04) | COVERED | R-1.1 + R-2.5 | Aligned; home for NO-LEAKAGE arm 2. | — |
| F-R14 | D-15 forbids tier-differentiated content (§13.4, §13.7) | **CONTRADICTED (a) + PARTIAL (b)** | R-3.2 + §7.6 | (a) R-3.2 rewrites the exact `consult/route.ts` block holding the live `audience_tier` stamp (`:459`,`:616`) without excising it. (b) §7.6 `verbosity` knob near the D-15 line. See C-2/C-4. | High (a) / Low-med (b) |
| F-R15 | MCP-consult vs MCP-expert are NOT audience tiers (§6.5.1) | COVERED | R-0.2 / R-4.1-4.2 | Consistent; nit — plan should quote the §6.5.1 disclaimer. | Low (docs) |

**The six contradictions (plan §8.5, phrased for native consumption):**

- **C-1 (CONTRADICTED):** `prashna_ask`'s R-5.1 contract carries a `depth` param
  D-15 forbids and `scope_tuple?` already derives — both forbidden and redundant.
  Cheap to fix now (tool unbuilt).
- **C-2 (CONTRADICTED by omission):** R-3.2's `consult/route.ts` edit rewrites the
  exact block carrying a live `audience_tier` D-15 violation (`:459`,`:616`)
  without excising it (excision assigned to PARIPRASHNA P2'); the floor could land
  D-15-dirty.
- **C-3 (UNDER-SPECIFIED):** cited signal *content* is still internal-register
  text; `bodha_msr_signals` has no reader-facing column, and the
  `signal_reader_text` editorial pass sits in no plan phase.
- **C-4 (CONTRADICTED, potential):** the `verbosity: concise|detailed` knob (§7.6)
  vs D-15 "never a parameter of the ask" — "a depth axis wearing a token-budget
  costume."
- **C-5 (UNDER-SPECIFIED):** R-3's planner preserves two outcomes
  (`PlanReceipt | fault`); the rebuild needs three (add `ClarificationRequest` +
  pre-plan ledger check).
- **C-6 (SEQUENCING TENSION):** the load-bearing consumer contract (`prashna_ask`)
  is sequenced last (R-5), yet PARIPRASHNA T-2 makes it a core bet and §19.1 fault 1
  is "the core bet was validated last."

## 6. Open questions for the native

**Six Paripraśna-alignment rulings (C-1..C-6)** — full statements at plan §8.5
and `LANE_F_REPORT.md` §3; adjudication table at `GROUND_TRUTH_REGISTER.md`
Part C. Plus two under-specified plane items deserving attention: **F-R1**
(headless-engine callability — consumed by R-5, owned by neither workstream)
and **F-R7** (`calibration_context_only` NO-LEAKAGE exclusion + CI canary).

**Genuine ambiguities/unresolved divergences** flagged (not silently resolved)
in `GROUND_TRUTH_REGISTER.md` Part E — the reconciliation was instructed to
flag rather than pick a side:

- **GT-AMBIG-1 — the catalog count.** Lanes count different objects (118/122/115/116);
  no single grep is an invariant. Resolved as CORRECTED-APPROX; census must be
  codegen-derived. *Do not treat any single count as an invariant.*
- **GT-AMBIG-2 — MCP aggregate tool count.** Genuinely unresolved: wrapper-indirection
  defeats grep; `REGISTERED_TOOL_COUNT`=120, floor ≈145, no lane had budget for a
  full AST pass. **The true live MCP tool count is unknown to ±30 today** — R-1 must
  derive it from AST/runtime.
- **GT-AMBIG-3 — "retired aliases = 4" (plan R-1.4).** No lane found a retire ledger;
  UNVERIFIABLE. A `git log` archaeology pass or native ruling could resolve.
- **GT-AMBIG-4 — PARIPRASHNA target doc internal staleness.** Its own §6.1 topology
  diagram still shows `prashna_ask(…, depth)` and "session pin," superseded by
  D-15/D-16 *in the same doc*. The plan inherited C-1/F-R4 from that stale diagram.
  Out of this audit's write scope (brief forbids touching PARIPRASHNA) — flagged
  for the native: correcting the diagram at source would prevent re-inheritance.

## 7. Full commit ledger

All commits in this worktree (`ret/strategy-s1`), chronological (oldest first),
from the Phase-0 doc base through this report. **The reconciliation agent stall
noted in commit `47d3debe` is a real, recorded event** — the first §F.2 agent
(opus) completed §F.1 (the ground-truth register, `f4ef3137`) then stalled 600s
into the §F.2 plan amendment with no progress; per brief §D failure discipline
it was respawned once with narrowed scope, and the narrowed respawn succeeded
(plan v1.3, `faa5b936`). The final report was deliberately deferred to a third,
separate task (this one) so no single agent call was large enough to stall again.

| # | Hash | Message |
|---|---|---|
| 1 | `9c358819` | docs(retrieval): strategy+plan+consult v1 set, PARIPRASHNA target arch, MCP handoff, RS-4 governance amendments (CLAUDE.md v6.4, PROJECT_ARCHITECTURE B.11/H.4) — *Phase-0 base* |
| 2 | `a17127e8` | docs(ret-audit): STATE.md opened, Phase 0 verification recorded (main-branch deviation logged) |
| 3 | `4304d006` | docs(ret-audit): lanes A-F spawned in parallel, model/effort ledger recorded |
| 4 | `fe3f709f` | docs(ret-audit): lane B report — envelope & budget reality |
| 5 | `829ec6b6` | docs(ret-audit): STATE.md — lane B landed |
| 6 | `263a26b7` | docs(ret-audit): lane D report — MCP edge & adaptivity reality |
| 7 | `1c75014d` | docs(ret-audit): STATE.md — lane D landed |
| 8 | `2401baf4` | docs(ret-audit): lane C report — planner & taxonomy reality |
| 9 | `8b28179f` | docs(ret-audit): STATE.md — lane C landed |
| 10 | `0ae17b23` | docs(ret-audit): lane F report — Paripraśna rebuild interface alignment |
| 11 | `1f8453f1` | docs(ret-audit): STATE.md — lane F landed |
| 12 | `fe061cd7` | docs(ret-audit): lane A report — catalog & registration reality |
| 13 | `a0774de9` | docs(ret-audit): STATE.md — lane A landed |
| 14 | `bc0f6de6` | docs(ret-audit): lane E report — data-plane & service coverage reality |
| 15 | `bdf273e7` | docs(ret-audit): STATE.md — lane E landed, all six lanes complete |
| 16 | `f4ef3137` | docs(ret-audit): ground truth register *(§F.1 — first reconciliation agent)* |
| 17 | `47d3debe` | docs(ret-audit): STATE.md — record reconciliation-agent stall + narrowed respawn *(the stall event)* |
| 18 | `faa5b936` | docs(ret-audit): plan v1.3 — ground-truth corrections absorbed, R-3.1 re-scoped, six contradictions added as open rulings *(§F.2 — narrowed respawn)* |
| 19 | `60b49a9a` | docs(ret-audit): STATE.md — plan v1.3 landed |
| 20 | *(this commit)* | docs(ret-audit): audit final report *(§F.3)* |

## 8. Total model / effort / cost accounting

Figures are taken from each lane report's own "Model/effort ledger" section.
**No lane self-reported exact tool_use counts, wall-clock duration, or token
totals** — the ledgers report model, effort, and approximate grep/read call
counts only. Missing figures are marked "not self-reported" rather than
invented.

| Lane / pass | Model | Effort | Tool-use count | Duration | Tokens |
|---|---|---|---|---|---|
| A — catalog & registration | sonnet | default | ~60–70 grep/awk/python invocations (self-reported approx) + 2 files written | not self-reported | not self-reported |
| B — envelope & budget | sonnet | default | ~25 grep/read calls (self-reported); no writes to source | not self-reported | not self-reported |
| C — planner & taxonomy | opus (4.8, 1M) | high | not self-reported as a count (files-read-in-full list given); 0 DB queries | not self-reported | not self-reported |
| D — MCP edge & adaptivity | sonnet | default/medium | not self-reported as a count (representative file/grep list given); 0 writes | not self-reported | not self-reported |
| E — data-plane & coverage | opus (4-8[1m]) | high | not self-reported as a count (source-touched list given); 0 DB (NO-DSN) | not self-reported | not self-reported |
| F — Paripraśna interface | opus (4-8[1m]) | high/xhigh | not self-reported as a count; 3 grep confirmations + full-doc reads; time split ~70% judgment / ~30% mechanical | not self-reported | not self-reported |
| Reconciliation §F.1 — ground-truth register | opus | high | not self-reported (247-line register produced) | ~stalled after (see §F.2) | not self-reported |
| Reconciliation §F.2 — plan v1.3 (narrowed respawn) | opus | high | not self-reported (343 insertions / 91 deletions) | first attempt stalled ~600s, respawn succeeded | not self-reported |
| §F.3 — this final report | opus (4.8, 1M) | default | ~12 tool calls (reads + 2 bash + 1 write + 1 commit) | single pass | not self-reported |

**Total tool-use accounting:** partially reconstructable only. A + B self-report
~85–95 combined grep/read calls; C/D/E/F/reconciliation report file lists and
qualitative effort splits but no integer tool-use counts; **no lane or pass
self-reported duration or token totals**, so no meaningful grand total can be
computed without inventing numbers. What is certain: **6 audit lanes + 1
two-part reconciliation pass (with one stall + narrowed respawn) + this report**,
split **4 sonnet-default / 5+ opus-high** by design (mechanical verification →
sonnet; adjudication/synthesis → opus, per STATE.md T1 rationale).

---

*End AUDIT_FINAL_REPORT v1.0 — final deliverable (§F.3) of
RETRIEVAL_AUDIT_EXECUTION_BRIEF_v1_0. Baseline reconciled; six Paripraśna
rulings (C-1..C-6) + four ambiguities open for the native.*
