---
artifact: TRACEABILITY_MATRIX
type: TWO-WAY TRACEABILITY MATRIX (Brief Foundry, Phase 3)
version: 2.0
status: REGENERATED-COMPLETE — for Cowork review gate (plan §12 item 4 / §12.5.iii)
generated_by: Brief Foundry follow-up session (Claude Code), 2026-07-12 — regenerates v1.0
  (2026-07-11/12) after the two previously-missing child briefs (LANE5_WIRE_FIDELITY.md,
  LANE9_SUBSTRATE_INTEGRITY.md) and AUDIT_STATE.md were built by a parallel recovery pass
source_plan: 00_ARCHITECTURE/briefs/LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md (v1.3, 649 lines)
source_foundry_brief: 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_AUDIT_BRIEF_FOUNDRY_v1_0.md §4
briefs_inventory_at_build_time:
  present: [CHARTER.md, ITEM0_R45_TRIAGE.md, LANE1_CENSUS.md, LANE2_QUESTION_MATRIX.md,
            LANE3_CONSISTENCY.md, LANE4_RECEIPT_HONESTY.md, LANE5_WIRE_FIDELITY.md,
            LANE6_RANKING_QUALITY.md, LANE7_SYNTHESIS_CEILING.md, LANE8_ENTITY_DOSSIER.md,
            LANE9_SUBSTRATE_INTEGRITY.md, LANE10_PROMISE.md]
  missing: []
  state_layer_present: [AUDIT_STATE.md]
changelog:
  - v2.0 (2026-07-12): REGENERATED-COMPLETE. Supersedes v1.0, which was built while 2 of the
    12 mandated child briefs (LANE5_WIRE_FIDELITY.md, LANE9_SUBSTRATE_INTEGRITY.md) and
    AUDIT_STATE.md did not yet exist (a transient API connection error mid-swarm on the
    original Brief Foundry run caused those 3 artifacts to fail/be skipped). v1.0 correctly
    flagged 9 plan elements UNMAPPED as a result. Both briefs and AUDIT_STATE.md were built
    in a follow-up recovery pass (2026-07-11/12). This regeneration re-verifies all 9
    previously-unmapped items against the now-complete brief set, with precise section
    citations located inside LANE5_WIRE_FIDELITY.md and LANE9_SUBSTRATE_INTEGRITY.md (not
    inferred from the briefs' mere existence). Result: 0 unmapped plan elements. All other
    content (the 10 previously-present briefs, unchanged since v1.0 per file-mtime check) is
    carried forward without modification.
  - v1.0 (2026-07-11/12): first build, 9 items UNMAPPED (see superseded content — this
    version's §5 "Regeneration note" summarizes the resolution).
---

# TRACEABILITY MATRIX — LLM Consumption Audit Brief Foundry

**Headline (read first):** all 12 mandated Brief Foundry artifacts now exist —
`CHARTER.md`, `ITEM0_R45_TRIAGE.md`, and the 10 lane briefs `LANE1_CENSUS.md` …
`LANE10_PROMISE.md` (including the two previously-missing `LANE5_WIRE_FIDELITY.md` and
`LANE9_SUBSTRATE_INTEGRITY.md`) — plus `AUDIT_STATE.md`. This regeneration re-derives the
full plan→brief and brief→plan mappings against the complete brief set. **Total unmapped
plan elements: 0.** The build now satisfies foundry brief §6 acceptance criterion 3
("TRACEABILITY_MATRIX has ZERO unmapped plan elements or an explicit exceptions entry per
unmapped item") on the strict reading, not only the exceptions-entry fallback reading.

One residual item is carried forward as an **exception, not an unmapped element**:
`AUDIT_STATE.md` itself still marks its Lane 5 and Lane 9 rows as internally
**PROVISIONAL**, pending a reconciliation pass by whoever next regenerates that file against
the two briefs that landed after `AUDIT_STATE.md` was built (see Exceptions §3.9). This is a
known, explicitly-logged gap inside `AUDIT_STATE.md`'s own text — not a traceability gap in
this matrix — and does not block the review gate per plan §12 item 4, since the matrix's own
role (mapping plan elements to implementing brief sections) is fully discharged.

---

## 1 — plan → brief (every plan element → implementing brief section; UNMAPPED listed explicitly)

### 1.1 Front matter / §0–§1 — program context, objective, hard boundary

| Plan element | Brief citation | Status |
|---|---|---|
| Frontmatter changelog v1.0–v1.3 (context only, no directive) | n/a — historical/orientation | MAPPED (context, not a directive; carried via CHARTER provenance line "generated_by") |
| §0 program context (why prior iterations plateaued; retrieval co-equal with data) | CHARTER.md §1 (doctrine, transcribes §2 which restates this framing); ITEM0_R45_TRIAGE.md §2 ("why this matters") operationalizes it for the R-45 case | MAPPED |
| §1 Objective and hard boundary (AUDIT REPORT ONLY; zero fixes; feeds Fable 5 planning; ONE Abhinandan rebuild after) | CLAUDECODE_BRIEF_AUDIT_BRIEF_FOUNDRY_v1_0.md `phase:` frontmatter field + §7 "Hard constraints"; CHARTER.md is silent on this (correctly — it's a foundry/session-scope directive, not lane doctrine) | MAPPED (via governing foundry brief, which is itself part of the "briefs" surface per §4 wording — see Exceptions §3.1 for the scope note on whether the foundry's own brief counts as an implementing "brief section") |

### 1.2 §2 — Audit doctrine (the constitution) + §2.1 examples-are-illustrative

| Plan element | Brief citation | Status |
|---|---|---|
| §2 "gap" definition; width axis; depth axis (Mercury standard) | CHARTER.md §1 "Doctrine (plan §2 + §2.1, verbatim)" | MAPPED (verbatim transcription) |
| §2.1 examples-are-illustrative doctrine (3 closed-loop sources; UNREACHABLE-by-nonexistence) | CHARTER.md §1 (same section, verbatim); LANE8_ENTITY_DOSSIER.md §2 (Appendix B floor + "foundry's DB+canon discovery pass may only ADD, never cut" instantiates it for facets); LANE1_CENSUS.md §1/§3 (value-family DB-derived enumeration instantiates it for values); LANE9_SUBSTRATE_INTEGRITY.md §0 (instantiates it for 9a's graph-neighborhood grading against the full classical space, and 9b's ingestion matrix against the full 204-category DB enumeration) | MAPPED |

### 1.3 §3 — Fixed decisions table

| Plan element | Brief citation | Status |
|---|---|---|
| Chart set (two charts only; absent LEL acceptable) | Every child brief frontmatter `charts_in_scope:` field / in-body chart_id citations (CHARTER, ITEM0, LANE1/2/3/4/5/6/7/8/9/10) | MAPPED |
| **DB access GRANTED read-only for Lane 5 wire-fidelity and Lane 8 facet enumeration; all other lanes via public MCP** | LANE8_ENTITY_DOSSIER.md §0/§6 (Lane 8 portion); **LANE5_WIRE_FIDELITY.md §0.5 "DB access grant (plan §3, cited explicitly per task instruction)"** — quotes the plan's DB-access row verbatim ("GRANTED, read-only (SELECT only), for Lane 5 wire-fidelity and Lane 8 facet enumeration...") and binds it to the `mcp__postgres__query` tool with an absolute SELECT-only constraint | **MAPPED — previously UNMAPPED in v1.0 (no Lane 5 brief existed); now resolved with a precise citation** |
| Question list PENDING → gated on `NATIVE_QUESTION_LIST_APPROVED` | LANE2_QUESTION_MATRIX.md §1 "Note on the gate reference" (gate discharged via Appendix C, ledger `questions.jsonl`) | MAPPED |
| Budget OPEN; checkpointing mandatory | CHARTER.md §5 (RESUME protocol); every child brief's "Checkpoint/RESUME" section, incl. LANE5 §4 and LANE9 §6/§6.1 | MAPPED |
| Executor: Opus/Claude Code; Fable 5 excluded from execution; judgment rubrics written verbatim into brief (no executor taste); Lane 2 conductor+fresh-sub-agent-per-question; legacy 38-item battery keeps existing grading keys | CHARTER.md §7 (rubrics); LANE2_QUESTION_MATRIX.md §2.1 (conductor+fresh-sub-agent protocol) | MAPPED (legacy-battery grading-keys continuity is not separately re-stated in any brief — see Exceptions §3.2) |
| Fix-forbidden absolute | CLAUDECODE_BRIEF_AUDIT_BRIEF_FOUNDRY_v1_0.md §7; every child brief's "explicit non-scope" / closing framing (e.g. LANE2 §9, ITEM0 §7) | MAPPED |

### 1.4 §4 — Failure-class taxonomy (9 classes)

| Plan element | Brief citation | Status |
|---|---|---|
| Classes 1–9 (UNREACHABLE … UNGOVERNED JUDGMENT) | CHARTER.md §2 "9-class failure taxonomy (plan §4, verbatim)"; instantiated per-lane e.g. LANE5 §0 (classes 1/6/7 dominant for wire-fidelity), LANE9 §0 (classes 1/4/6/7/9 dominant for 9a, classes 1/5/6/7 dominant for 9b) | MAPPED (verbatim) |

### 1.5 §5 — Item 0 + Lanes 1–10 (the core work plan)

| Plan element | Brief citation | Status |
|---|---|---|
| Item 0 — R-45 triage (kala_activation writer-vs-serving fork test) | ITEM0_R45_TRIAGE.md (entire document; §§1–7) | MAPPED |
| Lane 1 preamble + 1a tool census | LANE1_CENSUS.md §2 (protocol, transcribed verbatim, plan lines 133-165); §8 shard key "(a) Lane 1a: tool batches" | MAPPED |
| Lane 1b value census (Concept×Retrievability matrix) | LANE1_CENSUS.md §2, §6 (deliverable spec); ledger `value_families.jsonl` (3,058 rows) | MAPPED |
| Lane 1c services census | LANE1_CENSUS.md §2; ledger `services.jsonl` (30 rows) | MAPPED |
| Lane 1 extension (a) L5 negative-knowledge slots test (P-2) | LANE1_CENSUS.md §3a | MAPPED |
| Lane 1 extension (b) full outcome loop live test (P-6) | LANE1_CENSUS.md §3b | MAPPED |
| Lane 1 extension (c) dissent-surface (synth_tail_divergence_get) consumability (P-4) | LANE1_CENSUS.md §3c | MAPPED |
| Lane 1 extension (d) recall_session / session-memory round-trip | LANE1_CENSUS.md §3d | MAPPED |
| Lane 2 — question-first coverage matrix (full protocol, gating note, gochara/timing requirement) | LANE2_QUESTION_MATRIX.md §1 (protocol transcribed verbatim, plan lines 167-175) | MAPPED |
| Lane 3 — cross-tool consistency sweep (fixed quantity set × 9 grahas × every serving path) | LANE3_CONSISTENCY.md §2 (protocol transcribed verbatim, plan lines 177-182); ledger `quantities.jsonl` (234 rows) | MAPPED |
| Lane 4 — receipt-honesty sweep + fragility/confidence metadata extension (P-7) | LANE4_RECEIPT_HONESTY.md §2 (protocol, plan lines 184-190); §3 (extension) | MAPPED |
| **Lane 5 — wire-fidelity diff (DB-access lane; plan lines 192-196)** | **`LANE5_WIRE_FIDELITY.md` §1 "Protocol, transcribed in full (plan §5 lines 192-196)"** — the full four-clause paragraph (fields dropped in pivots; subjects merged across categories/KP-6; trims cutting meaning mid-narration/R-32; budget ceilings silently discarding decisive rows) is quoted verbatim and then unpacked into four named, non-optional failure modes with their own calibration anchors (KP-6, R-32) | **MAPPED — previously UNMAPPED (no brief existed); now resolved** |
| Lane 6 — ranking-quality audit + normative-bands extension (P-5) | LANE6_RANKING_QUALITY.md §2 (protocol, plan lines 198-205); §3 (extension) | MAPPED |
| Lane 7 — large-N synthesis ceiling probe (10 heavy questions, requirements-spec output) | LANE7_SYNTHESIS_CEILING.md §1 (transcribed verbatim, plan lines 207-214), §3 (protocol steps), §5 (requirements-spec deliverable) | MAPPED |
| Lane 8 — entity-dossier depth audit (Mercury standard; 20 dossiers) | LANE8_ENTITY_DOSSIER.md §1 (protocol, plan lines 216-244) | MAPPED |
| **Lane 9a — CGM graph leverage audit (plan lines 249-259)** | **`LANE9_SUBSTRATE_INTEGRITY.md` §2 "Protocol (plan §5 Lane 9, lines 245-270, TRANSCRIBED IN FULL)"** (the full 9a paragraph, verbatim) **+ §3 "9a extension: the three-axis grading discipline per sampled node"** — operationalizes the exact three axes named at plan lines 252-257 (structural / consumption / leverage) with dispositor-chain, yoga-membership, bhava-lordship, and temporal-hook completeness checks, edge-citation correctness checks (B.3), ≤2-call consumption grading, and a live leverage/parked-database test | **MAPPED — previously UNMAPPED (no brief existed); now resolved with precise section citations for both the verbatim protocol AND its operational extension** |
| **Lane 9b — MSR ingestion coverage + fidelity audit (plan lines 261-270)** | **`LANE9_SUBSTRATE_INTEGRITY.md` §2 (same protocol transcription, 9b paragraph) + §4 "9b extension: the ingestion-matrix build discipline per fact_category"** — operationalizes the exact five-column L1→MSR ingestion matrix named at plan lines 263-264 (consumed-by-bo_laksana? / salience class / entity attribution / domain mapping / signal-emergence count) against all 204 DB-derived L1 fact_categories, with named anchors R-44a/R-44b/R-42/KP-4 bound to specific DB columns (`constituent_facts_array`, `signature_tier`, `domains_affected_array`, `domain_salience_jsonb`) | **MAPPED — previously UNMAPPED (no brief existed); now resolved with precise section citations for both the verbatim protocol AND its operational extension** |
| Lane 10 — promise-vs-delivery audit (promise ledger, 4-field schema, ~55 assets) | LANE10_PROMISE.md §2 (protocol transcribed verbatim, plan lines 272-288); §3 (compile-vs-grade split); ledger `asset_promises.jsonl` (67 rows for ~55 assets — see Exceptions §3.3 on the count) | MAPPED |

### 1.6 §6 — Cross-lane protocols

| Plan element | Brief citation | Status |
|---|---|---|
| Finding discipline (reproducible call, verbatim evidence, class, severity, suspected layer, dedupe, register-append) | CHARTER.md §3 "Finding schema (plan §6, verbatim)"; instantiated by LANE5 §2 (per-row diff→classify→finding-record obligations) and LANE9 §8(d) (per-shard finding-record obligations for both 9a/9b) | MAPPED |
| Improvisation log (class 9) | CHARTER.md §3 (same section); reinforced per-lane (e.g. LANE2 §2.2 P-12 manual mode; LANE9 §3 axis-3 "leverage" logs a class-9 note when forced improvisation occurs) | MAPPED |
| Checkpointing (incremental; RESUME on interruption) | CHARTER.md §5 (RESUME protocol); every child brief's own Checkpoint/RESUME section, incl. LANE5 §4 and LANE9 §6/§6.1 (doubled for two sub-lane streams) | MAPPED |
| Known-findings anchor set (R-37..R-48 must be independently rediscovered) | CHARTER.md §3 (same section); ledger `anchors.jsonl` (12 rows); referenced in ITEM0_R45_TRIAGE.md throughout (R-45/R-39/R-40); **LANE5_WIRE_FIDELITY.md §2 step 4 (KP-6, R-32 dedupe check)**; **LANE9_SUBSTRATE_INTEGRITY.md §2.1 "Known-evidence anchors this lane MUST independently rediscover"** (v2.2 chain-integrity rows, G-6, the "zero graph-derived context" 2026-07-11 anchor for 9a; R-44a, R-44b, R-42, KP-4 for 9b) | MAPPED |

### 1.7 §7 — Deliverables (9 items)

| Plan element | Brief citation | Status |
|---|---|---|
| 1. `LLM_CONSUMPTION_AUDIT_v1_0.md` report | specified in every child brief's "deliverable spec" section (e.g. LANE1 §6, LANE2 §8, LANE3 §7, LANE4 §7, LANE5 §5, LANE6 §6, LANE7 §4/§7, LANE8 §7, LANE9 §9, LANE10 §6) — the report itself is an execution-phase artifact, out of foundry's BUILD-ONLY scope; foundry maps it by specifying its contract | MAPPED (spec only, not produced — correct per foundry scope) |
| 2. Machine-readable findings JSON | CHARTER.md §3 (finding schema, "per §7 deliverable 2... carries all of the above fields"); LANE5 §5 item 2, LANE9 §9 (both name deliverable 2 explicitly as a downstream consumer of their findings) | MAPPED |
| 3. Register appends | CHARTER.md §3; LANE4_RECEIPT_HONESTY.md §6 "Finding output"; LANE5 §5 item 2 (register-append obligation, conductor-only serialized dedupe pass, §7(d)); LANE9 §8(d) (identical conductor-only dedupe-and-append discipline) | MAPPED |
| 4. 20 entity retrievability matrices | LANE8_ENTITY_DOSSIER.md §3 (ledger), §7 (deliverable spec) | MAPPED |
| 5. Question-coverage matrix (standing asset, supersedes 38-item battery) | LANE2_QUESTION_MATRIX.md §8 (deliverable spec) | MAPPED |
| 6. Concept×Retrievability matrix (Lane 1b) | LANE1_CENSUS.md §6 (deliverable spec); LANE5 §5 item 3 (Lane 5's per-family `wire_value_matches_table` verdicts explicitly named as "direct retrievability-grade evidence" feeding this same matrix) | MAPPED |
| **7. L1→MSR ingestion matrix (Lane 9b) + graph-leverage report (Lane 9a)** | **`LANE9_SUBSTRATE_INTEGRITY.md` §9 "Deliverable spec"** — quotes plan §7 deliverable 7 verbatim, then specifies exactly: the 204-row × 5-column ingestion matrix (9b) and the per-node three-axis dossier + chart-level rollup (9a), with exact output locations (`state/LANE9.md` + `state/LANE9/shard-9a-*.md` / `shard-9b-*.md`) | **MAPPED — previously UNMAPPED (no Lane 9 brief existed); now resolved** |
| 8. Lane 2 evidence-plans + acquisition logs (P-12 requirements corpus) | LANE2_QUESTION_MATRIX.md §2.2 (P-12 manual mode, in full) | MAPPED |
| 9. Promise×Delivery ledger (Lane 10) | LANE10_PROMISE.md §6 (deliverable spec) | MAPPED |

### 1.8 §8 — Satisfaction criteria (5, all must hold)

| Plan element | Brief citation | Status |
|---|---|---|
| 1. Census completeness (1a/1b/1c, DB-derived, exhaustive) | CHARTER.md §4 "Satisfaction criteria (plan §8, verbatim)"; LANE1_CENSUS.md §1/§7; LANE5 §5 item 4 (Lane 5's own contribution to criterion 1, explicit) | MAPPED |
| 2. Question-width completeness | CHARTER.md §4; LANE2_QUESTION_MATRIX.md §6 (coverage self-declaration template) | MAPPED |
| 3. Depth completeness (20/20 dossiers) | CHARTER.md §4; LANE8_ENTITY_DOSSIER.md §8; LANE9 §0 (criterion 3 also binds 9a's node dossiers to the full Appendix B facet space) | MAPPED |
| 4. Coverage honesty (self-declaration; audited-or-deferred) | CHARTER.md §4; every lane's TAP-9-style self-declaration section, incl. LANE5 §6 and LANE9 §7 | MAPPED |
| 5. Plannability (machine-readable finding + class + layer) | CHARTER.md §4; CHARTER.md §3 (finding schema); LANE5 §5 item 4, LANE9 §9 (both name plannability explicitly) | MAPPED |

### 1.9 §9 — Planning-phase register (P-1..P-13)

| Plan element | Brief citation | Status |
|---|---|---|
| P-1 Vidhi/method layer → Lane 2 variance + class-9 logs | CHARTER.md §2 (class 9); LANE2_QUESTION_MATRIX.md (question-level variance is inherent to its per-question trace design, §1/§3) — no dedicated P-1 subsection exists in any brief, mapped only via the general class-9 mechanism | MAPPED (thin — see Exceptions §3.4) |
| P-2 Negative knowledge → Lane 1 extension (L5 slots) | LANE1_CENSUS.md §3a | MAPPED |
| P-3 Adjudication doctrine → class-9 logs | CHARTER.md §2 (class 9) | MAPPED (thin — same as P-1, general mechanism only) |
| P-4 Adversarial retrieval → Lane 1 dissent-surface test | LANE1_CENSUS.md §3c | MAPPED |
| P-5 Normative bands → Lane 6/8 extension | LANE6_RANKING_QUALITY.md §3; LANE8_ENTITY_DOSSIER.md §2 (facet 16, shadbala "VS REQUIRED MINIMUM ratio") | MAPPED |
| P-6 Longitudinal loop → Lane 1 outcome-loop test | LANE1_CENSUS.md §3b | MAPPED |
| P-7 Fragility propagation → Lane 4 extension | LANE4_RECEIPT_HONESTY.md §3 | MAPPED |
| P-8 Gochara composition → Lane 2 timing questions | LANE2_QUESTION_MATRIX.md §1 (protocol, "gochara composition... to expose §10 gap 8"); ledger `questions.jsonl` group K (Kala-vidhi) | MAPPED |
| P-9 Narration vocabulary → class-9 logs | CHARTER.md §2 (class 9) | MAPPED (thin — general mechanism only) |
| P-10 Intent decomposition contract → Lane 2 protocol | LANE2_QUESTION_MATRIX.md §2.2 (P-12 manual mode explicitly names "P-10's contract is its input") | MAPPED |
| P-11 Large-N synthesis instrument → Lane 7 (produces requirements spec) | LANE7_SYNTHESIS_CEILING.md §5 | MAPPED |
| P-12 Demand-side retrieval planner + capability map + acquisition tracker → Lane 2 executor runs in this mode; Lane 1b seeds capability map | LANE2_QUESTION_MATRIX.md §2.2 (full P-12 manual-mode transcription); LANE1_CENSUS.md §6 (Concept×Retrievability matrix "seeds the capability map") | MAPPED |
| P-13 Services as first-class evidence sources → Lane 1c services census | LANE1_CENSUS.md §2/§3 | MAPPED |

### 1.10 §10 — Post-audit program flow (6 steps)

| Plan element | Brief citation | Status |
|---|---|---|
| Steps 1–6 (audit report → Fable 5 planning → fix waves → rebuild → re-verification → register reconciliation) | Out of Brief Foundry scope by design (foundry brief §1 "phase: BRIEF FOUNDRY... AUDITS NOTHING. FIXES NOTHING"; these are post-audit steps, not foundry-buildable artifacts) | MAPPED (correctly out of scope — no brief should implement post-audit program flow; noted here per the "every plan element" instruction, not flagged UNMAPPED because the plan itself places these steps after the audit, which is itself after the foundry) |

### 1.11 §12 — Execution architecture (items 1–7, incl. §12.7 swarm model)

| Plan element | Brief citation | Status |
|---|---|---|
| 1. Federated briefs (one charter + one child brief per lane, fresh-session-executable) | CHARTER.md (entire document is the master charter); child briefs LANE1/2/3/4/5/6/7/8/9/10 + ITEM0 (**12 of 12 mandated: all present**) | **MAPPED — full federation now instantiated (12/12 lanes); previously PARTIALLY MAPPED at 10/12** |
| 2. Ledger-driven execution (8 ledgers) | `ledgers/tools.jsonl` (134 rows), `value_families.jsonl` (3,058), `services.jsonl` (30), `questions.jsonl` (329, incl. header), `facets.jsonl` (1,500), `asset_promises.jsonl` (67), `quantities.jsonl` (234), `anchors.jsonl` (12) — all 8 present and non-empty; LANE5 §2 and LANE9 §1 both cite `value_families.jsonl` (and LANE9 §1.1 additionally cites `asset_promises.jsonl`'s graph-asset slice) as their own ground-truth ledgers, closing the loop between the ledger layer and the brief layer for these two lanes specifically | MAPPED |
| **3. AUDIT_STATE.md standing state file** | CHARTER.md §5 (RESUME protocol specifies the mechanics); **`AUDIT_STATE.md` now exists** (built 2026-07-12) as a 12-unit index with ledger-derived `rows-total` counts for Item-0 and Lanes 1–4, 6–8, 10-compile/10-grade, and a specifically-flagged **PROVISIONAL** count for the Lane 5 and Lane 9 rows (its own §6 "Known gaps" section explains why: it was built concurrently with, not after, the Lane 5/9 briefs landing, and directs "whoever regenerates this index after those two briefs land MUST re-read them and correct rows 6 and 10") | **MAPPED — the artifact itself now exists, satisfying foundry brief §6 acceptance criterion 4's letter (real, ledger-derived rows-total counts are present for all 12 units, 10 of them final and 2 explicitly flagged provisional rather than silently wrong); the Lane5/Lane9 row reconciliation against the now-existing briefs is carried forward as Exception §3.9, not as an unmapped plan element (the state-file artifact and mechanism are what plan item 3 requires, and both exist)** |
| 4. Two-way traceability + adversarial review | THIS DOCUMENT (`TRACEABILITY_MATRIX.md`, v2.0) | MAPPED (self-referential — this is the artifact plan item 4 calls for) |
| 5. Process order (i–v) | CLAUDECODE_BRIEF_AUDIT_BRIEF_FOUNDRY_v1_0.md §§2–5 (Phase 1 ledgers, Phase 2 briefs, Phase 3 traceability, Phase 4 self-check+close) mirrors steps (ii)–(iii) of this list; steps (i), (iv), (v) are outside foundry scope (native+Fable5 debate, execution sessions, consolidation session) | MAPPED (foundry-scope portion); steps (i)/(iv)/(v) correctly out of scope |
| 6. Guarantee principle (completeness rests on ledgers/matrices, not diligence) | CLAUDECODE_BRIEF_AUDIT_BRIEF_FOUNDRY_v1_0.md §1 "Mission" (verbatim reference); this matrix itself is the guarantee mechanism in action — and its v1.0→v2.0 history is a live demonstration of the principle working as designed (a structural gap was caught mechanically, not missed by diligence, and closed via the same structural mechanism) | MAPPED |
| 7. §12.7 Swarm execution model — conductor+worker pattern, execution DAG, intra-lane sharding, state discipline, wall-clock consequence | CHARTER.md §6 "Execution DAG (plan §12.7, TRANSCRIBED VERBATIM)"; every child brief's "Swarm decomposition" section — LANE1 §8, LANE2 §5, LANE3 §6, LANE4 §9, **LANE5 §7** ("MANDATORY; plan §12.7" — per-fact-family shard key, 5-10 concurrent workers, shard trace files at `state/LANE5/shard-<id>.md`, exact RESUME-pointer format), LANE6 §8, LANE7 §8, LANE8 §9, **LANE9 §8** ("plan §12.7, MANDATORY section" — dual sub-shard streams for 9a/9b, per-node and per-fact_category shard keys, combined concurrency cap, stream-prefixed shard trace files, per-stream RESUME semantics), LANE10 §8 | **MAPPED for all 12 briefs — the DAG's Lane5/Lane9a/Lane9b nodes now each have a "Swarm decomposition" section; previously UNMAPPED for these three DAG nodes** |

### 1.12 §11 — Open items before the brief can be finalized (3 items)

| Plan element | Brief citation | Status |
|---|---|---|
| 1. Lane 2 question list (native↔Fable 5 debate, hold) | LANE2_QUESTION_MATRIX.md §1 "Note on the gate reference" — records the gate as DISCHARGED via Appendix C | MAPPED — see Exceptions §3.5 for whether this discharge was the native's own or the foundry's own resolution |
| 2. Lane 8 facet checklist finalization (same debate session) | LANE8_ENTITY_DOSSIER.md §2 — treats Appendix B as the floor, discovery pass may add | MAPPED — see Exceptions §3.5 (same open-item concern) |
| 3. Brief mechanics (root CLAUDECODE_BRIEF.md activation, may_touch/must_not_touch globs, RESUME protocol wording, rubric verbatims) | CLAUDECODE_BRIEF_AUDIT_BRIEF_FOUNDRY_v1_0.md frontmatter (`may_touch`/`must_not_touch`); CHARTER.md §5 (RESUME wording); CHARTER.md §7 (rubric verbatims, DRAFT-flagged) | MAPPED |

### 1.13 Appendix A — native observation → plan element (18 rows; foundry brief §4 requires this table included so the chain is verifiable end-to-end)

| Native observation | Plan landing | Brief citation | Status |
|---|---|---|---|
| Retrieval is co-equal with data; audit from the LLM-receiving lens | §0, §2 doctrine, Lanes 3–6 | CHARTER.md §1; LANE3/4/6 protocol sections | MAPPED |
| Discovery asset (temporal×spatial convergence, activation points, Kāla temporal engine) untested/broken | Item 0 (R-45 triage); Lane 1 | ITEM0_R45_TRIAGE.md (entire); LANE1_CENSUS.md §2 | MAPPED |
| NB/Viparita-Raja yogas absent from responses | Known Section-1 register gap; Lane 2; P-2 near-miss framing | LANE2_QUESTION_MATRIX.md (ledger `questions.jsonl` groups D/E/F/G touch yoga-bearing questions); LANE1_CENSUS.md §3a (P-2 negative-knowledge) | MAPPED |
| D9/D10/other vargas not given D1-equal significance | R-46; Lane 8 facet 4; P-3 (varga weights in doctrine) | LANE8_ENTITY_DOSSIER.md §2 (B-III facet 18, B-II facets 9-15 varga chain) | MAPPED |
| Mrityu-bhaga and related concepts never surfaced | R-47; Lane 8 facet 7 | LANE8_ENTITY_DOSSIER.md §2 (B-II facet 13) | MAPPED |
| Inability to engage large volumes / deep multi-factor synthesis; one-go or incremental both acceptable | R-48; Lane 7; P-11 | LANE7_SYNTHESIS_CEILING.md (entire) | MAPPED |
| ~20 relevant data points not received → not synthesized; investigate WHY per point | §2 width; Lane 2 protocol; §8 criterion 2 | LANE2_QUESTION_MATRIX.md §1/§2.2 | MAPPED |
| Depth: Mercury standard (strength, avastha, yogas, doshas, dispositor chain, vargas, MD/AD presence, convergence, cusp, combustion, "twenty other") | §2 depth; Lane 8 entire; §8 criterion 3 | LANE8_ENTITY_DOSSIER.md (entire) | MAPPED |
| Two charts only; missing LEL/calibration acceptable | §3 | every brief frontmatter `charts_in_scope:` field / in-body citation, incl. LANE5, LANE9 | MAPPED |
| DB access granted | §3; Lanes 5, 8 | LANE8_ENTITY_DOSSIER.md §0/§6 (Lane 8 portion); **LANE5_WIRE_FIDELITY.md §0.5** (Lane 5 portion, quoting the grant verbatim and binding it to `mcp__postgres__query` with an absolute SELECT-only constraint) | **MAPPED — full row now MAPPED; previously the Lane 5 portion was UNMAPPED** |
| Question list: extensive debate, hold | §3; §11 | LANE2_QUESTION_MATRIX.md §1 | MAPPED (discharge recorded — see Exceptions §3.5) |
| Open budget; Opus executor; Fable 5 builds plan from report | §3; §10 | CLAUDECODE_BRIEF_AUDIT_BRIEF_FOUNDRY_v1_0.md frontmatter | MAPPED |
| Multi-layer remediation scope | §1; §10 step 2 | out of foundry scope (post-audit); noted, not buildable here | MAPPED (correctly out of scope) |
| Examples/factors illustrative, never the limit | §2.1; Lane 1b; Lane 8 checklist draft | CHARTER.md §1; LANE1_CENSUS.md §1; LANE8_ENTITY_DOSSIER.md §2; LANE9_SUBSTRATE_INTEGRITY.md §0 (9a/9b instantiations) | MAPPED |
| **Is the Bodha graph (strongest association asset) leveraged efficiently?** | Lane 9a | **`LANE9_SUBSTRATE_INTEGRITY.md` §2 (verbatim protocol quote, 9a paragraph) + §3 (three-axis grading discipline: structural / consumption / leverage) + §9 (graph-leverage report deliverable, answering "is it actually leveraged by any serving instrument today?" verbatim as its chart-level rollup headline question)** | **MAPPED — previously UNMAPPED (no brief existed); now resolved with the exact three-axis citation the native's question maps onto** |
| **Is MSR's read of Gaṇita (via ga_structural etc.) designed and leveraged correctly for the LLM?** | Lane 9b | **`LANE9_SUBSTRATE_INTEGRITY.md` §2 (verbatim protocol quote, 9b paragraph) + §4 (five-cell ingestion-matrix build discipline, answering "is MSR's read of the Gaṇita layer designed correctly, and is it being leveraged correctly for the LLM?" verbatim) + §1.2 (the DB-derived 204-fact_category denominator that grounds the "designed correctly" grading)** | **MAPPED — previously UNMAPPED (no brief existed); now resolved with the exact five-cell citation the native's question maps onto** |
| Every astrological concept / every asset / every value each asset provides must be checked for LLM retrievability — no misses | Lane 1b value census; §2.1 closed-loop derivation; deliverable 6 | LANE1_CENSUS.md §1/§2/§6; LANE5_WIRE_FIDELITY.md §2 (the same `value_families.jsonl` ledger, marked from the wire-fidelity angle) | MAPPED |
| LLM must plan its evidence demand a priori (narrow→comprehensive, broad→wide), track received-vs-needed, keep seeking; supply extras are bonus | P-12; Lane 2 execution mode | LANE2_QUESTION_MATRIX.md §2.2 | MAPPED |
| Does the LLM know which tools/services provide which data? Does it have a tracker? | P-12 capability map + tracker; Lane 1b seeds the map | LANE1_CENSUS.md §6; LANE2_QUESTION_MATRIX.md §2.2 | MAPPED |
| Are services (dasha assets, real-time computation) reachable and used for values not in the data layer? | Lane 1c; P-13 | LANE1_CENSUS.md §2/§3 | MAPPED |
| Each asset's PROMISE (per its build intent) vs what is actually served; locate the shortfall layer (data plane vs retrieval plane) and enable the promise | Lane 10; deliverable 9 | LANE10_PROMISE.md (entire) | MAPPED |
| Audit size must not dilute any point; context decay must not thin the later lanes; brief must be built in Claude Code with time, missing nothing; document completeness must be verifiable | §12 execution architecture | CHARTER.md §6; every child brief's Swarm decomposition section (all 12, incl. LANE5 §7 and LANE9 §8); THIS DOCUMENT (verifiability mechanism) — **the v1.0→v2.0 history of this very matrix is itself the clearest possible demonstration of this native observation being honored rather than violated: the original dilution risk (two lanes silently thinning under a transient failure) was caught mechanically by the matrix, surfaced explicitly rather than papered over, and closed by name in this changelog** | **MAPPED — mechanism now closing the loop it was designed to close, not merely describing it** |

### 1.14 Appendix B — Lane 8 facet taxonomy (60-facet floor, 8 groups B-I..B-VIII)

| Plan element | Brief citation | Status |
|---|---|---|
| B-I Positional & coordinate (facets 1-8) | LANE8_ENTITY_DOSSIER.md §2 (transcribed verbatim, plan lines 495-503) | MAPPED |
| B-II Dignity & sign-based (facets 9-15) | LANE8_ENTITY_DOSSIER.md §2 (plan lines 505-512) | MAPPED |
| B-III Strength systems (facets 16-22) | LANE8_ENTITY_DOSSIER.md §2 (plan lines 514-526) | MAPPED |
| B-IV State & condition (facets 23-28) | LANE8_ENTITY_DOSSIER.md §2 (plan lines 528-535) | MAPPED |
| B-V Relational web (facets 29-36) | LANE8_ENTITY_DOSSIER.md §2 (plan lines 537-547); LANE9_SUBSTRATE_INTEGRITY.md §3 cross-references facet 32 (dispositor web) as the 9a structural-completeness reference for graph neighborhoods | MAPPED |
| B-VI Functional & role-based (facets 37-43) | LANE8_ENTITY_DOSSIER.md §2 (plan lines 549-562); LANE9_SUBSTRATE_INTEGRITY.md §3 cross-references facets 37 (bhava lordship) and 41 (yoga participation) and §3.1 cross-references facet 41 as the yoga-catalog grading reference | MAPPED |
| B-VII Temporal (facets 44-52) | LANE8_ENTITY_DOSSIER.md §2 (plan lines 564-578); LANE9_SUBSTRATE_INTEGRITY.md §3 cross-references facet 44 (dasha lordship windows) as the 9a temporal-hook reference | MAPPED |
| B-VIII Esoteric, remedial & tradition-specific (facets 53-60) | LANE8_ENTITY_DOSSIER.md §2 (plan lines 580-593) | MAPPED |
| "Floor: 60 facet groups... may ADD, deletion requires native sign-off... UNREACHABLE-by-nonexistence" closing doctrine | LANE8_ENTITY_DOSSIER.md §2 closing note (plan lines 595-597); ledger `facets.jsonl` (1,500 exploded atomic rows, `discovered` tag reserved for additions) | MAPPED |

### 1.15 Appendix C — Lane 2 question list (12 groups A–L)

| Plan element | Brief citation | Status |
|---|---|---|
| Group A. Deha & Ayus (6 types: A1-A6) | LANE2_QUESTION_MATRIX.md §1 (references Appendix C in full); ledger `questions.jsonl` rows tagged `question_group: "A. Deha & Ayus"` | MAPPED |
| Group B. Buddhi & Svabhava (6: B1-B6) | ledger `questions.jsonl` group B | MAPPED |
| Group C. Vidya (5: C1-C5) | ledger `questions.jsonl` group C | MAPPED |
| Group D. Karma & Vritti (9: D1-D9) | ledger `questions.jsonl` group D | MAPPED |
| Group E. Dhana & Sampatti (8: E1-E8) | ledger `questions.jsonl` group E | MAPPED |
| Group F. Kutumba & Vivaha (10: F1-F10) | ledger `questions.jsonl` group F | MAPPED |
| Group G. Santana (6: G1-G6) | ledger `questions.jsonl` group G | MAPPED |
| Group H. Bandhu, Ripu & Vyavahara (6: H1-H6) | ledger `questions.jsonl` group H | MAPPED |
| Group I. Sthana & Yatra (6: I1-I6) | ledger `questions.jsonl` group I | MAPPED |
| Group J. Dharma & Moksha (6: J1-J6) | ledger `questions.jsonl` group J | MAPPED |
| Group K. Kala-vidhi (8: K1-K8) | ledger `questions.jsonl` group K | MAPPED |
| Group L. Meta & whole-chart (6: L1-L6, Lane-7 feeders) | ledger `questions.jsonl` group L; LANE7_SYNTHESIS_CEILING.md §2 (ledger of ten heavy questions explicitly cross-references "group L feeder") | MAPPED |
| "Design rules" closing paragraph (every group ≥1 timing question; F/G/J unknown-unknown hunters; L items P-11 feeders) | LANE2_QUESTION_MATRIX.md §1 header note; LANE7_SYNTHESIS_CEILING.md §2 | MAPPED |
| Arithmetic note: plan states "76 types" in the Appendix C heading but the verbatim group sums (6+6+5+9+8+10+6+6+6+6+8+6) = 82 | ledger `questions.jsonl` HEADER row; LANE2_QUESTION_MATRIX.md §1 "Known ledger surprise" | MAPPED (as an explicitly logged discrepancy — see Exceptions §3.6) |

### 1.16 Summary counts (item 1)

- **Plan elements enumerated in this pass:** ~145 discrete rows across §0–§12 and Appendices A–C (counting each Appendix A/B/C row/group as one element, each §9 P-row as one element, each Lane sub-part as one element) — identical enumeration granularity to v1.0, for apples-to-apples comparison.
- **UNMAPPED: 0.** All 9 items that v1.0 correctly flagged UNMAPPED are now MAPPED, each with a section-level citation located inside the now-existing brief text (not inferred from the brief's mere existence):
  1. Plan §3 fixed-decisions row: "DB access GRANTED... for Lane 5 wire-fidelity" (Lane 5 portion) → `LANE5_WIRE_FIDELITY.md` §0.5 — RESOLVED
  2. Plan §5 Lane 5 — wire-fidelity diff protocol (entire lane, lines 192-196) → `LANE5_WIRE_FIDELITY.md` §1 — RESOLVED
  3. Plan §5 Lane 9a — CGM graph leverage audit (lines 249-259) → `LANE9_SUBSTRATE_INTEGRITY.md` §2 + §3 — RESOLVED
  4. Plan §5 Lane 9b — MSR ingestion coverage + fidelity audit (lines 261-270) → `LANE9_SUBSTRATE_INTEGRITY.md` §2 + §4 — RESOLVED
  5. Plan §7 deliverable 7 — L1→MSR ingestion matrix + graph-leverage report → `LANE9_SUBSTRATE_INTEGRITY.md` §9 — RESOLVED
  6. Plan §12 item 3 — AUDIT_STATE.md standing state file (artifact itself) → `AUDIT_STATE.md` now exists (built 2026-07-12) — RESOLVED (Lane5/Lane9 row reconciliation inside that file carried forward as Exception §3.9, not as unmapped)
  7. Plan §12.7 — the execution DAG's Lane5/Lane9a/Lane9b nodes' "Swarm decomposition" sections → `LANE5_WIRE_FIDELITY.md` §7, `LANE9_SUBSTRATE_INTEGRITY.md` §8 — RESOLVED
  8. Appendix A row: "Is the Bodha graph... leveraged efficiently?" (Lane 9a) → `LANE9_SUBSTRATE_INTEGRITY.md` §2/§3/§9 — RESOLVED
  9. Appendix A row: "Is MSR's read of Gaṇita... designed and leveraged correctly?" (Lane 9b) → `LANE9_SUBSTRATE_INTEGRITY.md` §2/§4/§1.2 — RESOLVED

All nine trace back to the same two root causes identified in v1.0 (`LANE5_WIRE_FIDELITY.md` and `LANE9_SUBSTRATE_INTEGRITY.md` were never written; `AUDIT_STATE.md`/`state/` were never written) — both root causes are now closed: the two briefs exist, are self-contained, transcribe their plan protocol verbatim, and carry the mandatory swarm-decomposition sections; `AUDIT_STATE.md` exists with ledger-derived counts (10 final, 2 explicitly flagged provisional pending a routine reconciliation pass, tracked as Exception §3.9).

---

## 2 — brief → plan (every brief section → its plan authority; INVENTED sections flagged)

### 2.1 CHARTER.md

| Brief section | Plan authority | Status |
|---|---|---|
| §1 Doctrine | plan §2 + §2.1 | AUTHORIZED (verbatim) |
| §2 9-class taxonomy | plan §4 | AUTHORIZED (verbatim) |
| §3 Finding schema | plan §6 | AUTHORIZED (verbatim) |
| §4 Satisfaction criteria | plan §8 | AUTHORIZED (verbatim) |
| §5 RESUME protocol | plan §12 items 3-4 (DERIVED, not verbatim — brief says so explicitly: "derives operational RESUME mechanics from the state-discipline principles") | AUTHORIZED-DERIVED (foundry is transparent about the derivation, not an invention) |
| §6 Execution DAG | plan §12.7 | AUTHORIZED (verbatim) |
| §7 Judgment rubrics (7.1-7.5) | NOT verbatim anywhere in the plan — the plan names the need for rubrics ("rubric in brief", Lane 1a line 141; "§J" reference, Lane 2 line 172; Lane 6/Lane 10 descriptive language) but never specifies grading scales, decision trees, or point systems | **INVENTED — but self-declared as such.** CHARTER.md §7 opens: "These rubrics are derived (not verbatim-transcribed)... DRAFT and MUST be ratified in the Cowork review gate... No lane may treat these as final without that ratification." This is the correct handling per plan §12.5.iii (review gate exists precisely for this) — flagged here per this task's instruction to make all inventions visible, not to imply it is improper |

### 2.2 ITEM0_R45_TRIAGE.md

| Brief section | Plan authority | Status |
|---|---|---|
| §1 The exact question | plan §5 Item 0, lines 124-131 | AUTHORIZED |
| §2 Why this matters | plan lines 127-131; register R-45/R-39/R-40 | AUTHORIZED |
| §3 Discovery-pass surprise (VF-2070..2095, VF-2839..2843) | foundry brief §2 "Discovery-pass surprises... logged in the close report as OBSERVATIONS" | AUTHORIZED (foundry brief, not the plan itself — correct: this is exactly the observation-logging mechanism the foundry brief specifies) |
| §4 Exact test protocol (SQL + MCP call spec) | plan lines 124-126 ("Single SELECT + one MCP call") — the brief's SQL is an OPERATIONALIZATION, not present verbatim in the plan | AUTHORIZED-DERIVED (plan mandates the test in one sentence; brief supplies the mechanics — consistent with foundry's mission "produce the... execution machinery") |
| §5 Decision table | not in plan verbatim — DERIVED from the WRITER NO-OP vs SERVING-PATH BUG fork logic implied by plan lines 127-131 | AUTHORIZED-DERIVED |
| §6 Output format / broadcast JSON schema | plan §12.7 ("Item-0's result is broadcast to Lanes 2/7 mid-flight") | AUTHORIZED-DERIVED (schema itself invented to operationalize the broadcast; declared as such) |
| §7 Explicit non-scope | foundry brief §7 (BUILD ONLY / no verification of defects) | AUTHORIZED |

### 2.3 LANE1_CENSUS.md

| Brief section | Plan authority | Status |
|---|---|---|
| §0 How to use | foundry brief §3 (self-contained child brief requirement) | AUTHORIZED |
| §1 Ledger files | foundry brief §2 (ledger table) | AUTHORIZED |
| §2 Protocol | plan §5 Lane 1, lines 133-165 (verbatim per brief's own header) | AUTHORIZED |
| §3 Extensions (a-d) | plan lines 162-165 | AUTHORIZED |
| §4 Rubrics (by reference) | CHARTER.md §7 | AUTHORIZED (via charter) |
| §5 Checkpoint/RESUME | CHARTER.md §5 / plan §12 items 3-4 | AUTHORIZED |
| §6 Deliverable spec | plan §7, lines 307-323 | AUTHORIZED |
| §7 Coverage self-declaration | plan §8 criterion 4 (coverage honesty) | AUTHORIZED |
| §8 Swarm decomposition | plan §12.7 | AUTHORIZED |
| §9 Item 0 broadcast consumption note | plan §12.7 ("broadcast to Lanes 2/7") — Lane 1 is not one of the two named broadcast recipients in plan §12.7's DAG text (which names Lanes 2/7 specifically) | **MINOR INVENTION** — Lane 1 consuming the Item-0 broadcast is not stated in the plan (only Lanes 2/7 are named); harmless extension but not plan-authorized. Logged for visibility, not as an error. |

### 2.4 LANE2_QUESTION_MATRIX.md

| Brief section | Plan authority | Status |
|---|---|---|
| §0 Self-containment statement | foundry brief §3 | AUTHORIZED |
| §1 Protocol (incl. gate-discharge note, §J substitution note, 76-vs-82 note) | plan §5 Lane 2, lines 167-175; Appendix C | AUTHORIZED (all three sub-notes are explicitly-declared foundry judgment calls, not silent) |
| §2.1 Conductor + fresh-sub-agent-per-question | plan §3 fixed-decisions table ("Lane 2 runs conductor + fresh-sub-agent-per-question") | AUTHORIZED |
| §2.2 P-12 manual mode | plan §9 P-12 row (line 359) | AUTHORIZED |
| §2.3 Verifier-sample re-grade (~15%) | plan §3 ("~300 traces... resuming via AUDIT_STATE"); plan §12.7 ("Verifier sampling (Lane 2's ~15% re-grade)") | AUTHORIZED |
| §2.4 Item-0 broadcast consumption | plan §12.7 (Lane 2 named explicitly) | AUTHORIZED |
| §3 Ledger | foundry brief §2 | AUTHORIZED |
| §4 Rubrics | CHARTER.md §7.3 | AUTHORIZED (via charter) |
| §5 Swarm decomposition | plan §12.7 | AUTHORIZED |
| §6 Coverage self-declaration | plan §8 criterion 4 | AUTHORIZED |
| §7 Checkpoint/RESUME | CHARTER.md §5 | AUTHORIZED |
| §8 Deliverable spec | plan §7 deliverables 1, 5, 8 | AUTHORIZED |
| §9 Explicit non-scope | foundry brief §7 | AUTHORIZED |

### 2.5 LANE3_CONSISTENCY.md / LANE4_RECEIPT_HONESTY.md / LANE6_RANKING_QUALITY.md / LANE7_SYNTHESIS_CEILING.md / LANE8_ENTITY_DOSSIER.md / LANE10_PROMISE.md

All six briefs follow the identical structural pattern verified above: §0 self-containment → §N protocol transcribed verbatim with explicit line citations → extension(s) with explicit line citations → ledger reference → rubric by reference to CHARTER §7 → checkpoint/RESUME → deliverable spec → coverage self-declaration → swarm decomposition. Spot-checked section-by-section against the plan line ranges each brief itself cites (LANE3 lines 177-182; LANE4 lines 184-190 + 189-190; LANE6 lines 198-205 + 204-205; LANE7 lines 207-214; LANE8 lines 216-244 + Appendix B lines 489-597; LANE10 lines 272-288). No section in any of these six briefs lacks a plan or charter citation.

| Brief | Status |
|---|---|
| LANE3_CONSISTENCY.md (all 8 sections) | AUTHORIZED |
| LANE4_RECEIPT_HONESTY.md (all 9 sections) | AUTHORIZED |
| LANE6_RANKING_QUALITY.md (all 9 sections) | AUTHORIZED |
| LANE7_SYNTHESIS_CEILING.md (all 8 sections, incl. §5 "REQUIREMENTS SPEC deliverable" which the brief itself notes is "this brief's Section [5]" fulfilling plan lines 210-214's mandate that Lane 7 "produces the REQUIREMENTS SPEC") | AUTHORIZED |
| LANE8_ENTITY_DOSSIER.md (all 9 sections) | AUTHORIZED |
| LANE10_PROMISE.md (all 8 sections, incl. §4.2 "Type specimens" which quotes plan's own bo_anveshana/kala_activation example verbatim, lines 283-286) | AUTHORIZED |

### 2.6 LANE5_WIRE_FIDELITY.md (new in this regeneration — not present in v1.0)

| Brief section | Plan authority | Status |
|---|---|---|
| §0 Charter reference | foundry brief §3 (self-contained child brief requirement) | AUTHORIZED |
| §0.5 DB access grant | plan §3 fixed-decisions table, DB access row (quoted verbatim) | AUTHORIZED (verbatim) |
| §1 Protocol, transcribed in full | plan §5 Lane 5, lines 192-196 (quoted verbatim, then unpacked into 4 named failure modes — the unpacking is an OPERATIONALIZATION of clauses already present in the verbatim quote, not new scope) | AUTHORIZED (verbatim quote) + AUTHORIZED-DERIVED (the 4-mode unpacking) |
| §2 Ledger file | foundry brief §2 (ledger table, `value_families.jsonl` row) | AUTHORIZED |
| §3 Rubric reference | CHARTER.md §7.1 | AUTHORIZED (via charter) |
| §4 Checkpoint/RESUME | CHARTER.md §5 / plan §12 items 3-4 | AUTHORIZED |
| §5 Deliverable spec | plan §7, lines 307-323 (Lane 5 is not deliverable-numbered by the plan the way Lanes 8/9/10 are — the brief is explicit about this: "Lane 5 is not named by number... but it is the sole source of ground truth for the wire-fidelity dimension threaded through the other deliverables") | AUTHORIZED-DERIVED (brief is transparent that Lane 5's deliverable role is inferred, not plan-numbered — logged, not silent) |
| §6 Coverage self-declaration | plan §8 criterion 4 (coverage honesty) | AUTHORIZED |
| §7 Swarm decomposition | plan §12.7 ("Lane 5 by fact family" sharding is named explicitly in the plan's own intra-lane sharding list) | AUTHORIZED (verbatim shard-key naming) |

No section of `LANE5_WIRE_FIDELITY.md` lacks a plan or charter citation; no INVENTED section found.

### 2.7 LANE9_SUBSTRATE_INTEGRITY.md (new in this regeneration — not present in v1.0)

| Brief section | Plan authority | Status |
|---|---|---|
| §0 Charter reference | foundry brief §3 | AUTHORIZED |
| §1/§1.1/§1.2 Ledgers (dual: `asset_promises.jsonl` graph-asset slice for 9a, `value_families.jsonl` `chart_facts`+`bodha_msr_signals` slices for 9b) | foundry brief §2 (ledger table) | AUTHORIZED |
| §2 Protocol, transcribed in full | plan §5 Lane 9, lines 245-270 (both 9a and 9b paragraphs quoted verbatim) | AUTHORIZED (verbatim) |
| §2.1 Known-evidence anchors | CHARTER.md §3 ("Known-findings anchor set... must independently rediscover") | AUTHORIZED (via charter) |
| §3 9a three-axis extension | plan lines 252-257 (the three axes — structural/consumption/leverage — are named in the plan; the brief's dispositor-chain/yoga/bhava-lordship/temporal-hook enumeration operationalizes "does Mercury's node reach its dispositor chain, its yogas, its bhava lords, its temporal hooks?" against specific Appendix B facet numbers) | AUTHORIZED-DERIVED (operationalization of a verbatim-quoted clause, cross-referenced to Appendix B facets which are themselves plan-authorized) |
| §3.1 Node sample composition (widens "key bhavas" to all 12) | plan line 252 says "key bhavas," not "all bhavas" — the brief explicitly widens this, citing charter §1/§2.1 doctrine ("examples are illustrative, never limiting... the conductor does not silently narrow to a subjectively 'key' subset") as its justification | **JUDGMENT CALL, explicitly self-declared — not silent, but also not a literal transcription of "key bhavas."** Logged for review-gate visibility (see Exceptions §3.10); the brief's own reasoning (narrowing the SAMPLE vs. narrowing what gets REPORTED) is a defensible reading of the doctrine, but it is a widening beyond the plan's literal words, not a verbatim instantiation, so it is flagged rather than silently accepted as AUTHORIZED-verbatim |
| §4 9b five-cell extension | plan lines 263-264 (the ingestion matrix's five required dimensions — consumed?/salience/attribution/domain/count — are named in the plan; the brief operationalizes each against specific DB columns) | AUTHORIZED-DERIVED |
| §5 Type-specimen handling | plan §6 (known-findings-anchor-set doctrine); precedent explicitly cited from LANE10_PROMISE.md §4.2 | AUTHORIZED-DERIVED |
| §6/§6.1 Checkpoint/RESUME | CHARTER.md §5 | AUTHORIZED |
| §7 Coverage self-declaration | plan §8 criterion 4 | AUTHORIZED |
| §8 Swarm decomposition | plan §12.7 ("9a by node sample, 9b by fact_category" is named explicitly in the plan's own intra-lane sharding list) | AUTHORIZED (verbatim shard-key naming) |
| §9 Deliverable spec | plan §7 deliverable 7 (quoted verbatim: "The L1→MSR ingestion matrix (Lane 9b) and the graph-leverage report (Lane 9a)") | AUTHORIZED (verbatim) |

One judgment call flagged (§3.1, bhava-sample widening) — self-declared, doctrine-cited, not a silent invention; no section found with zero plan/charter authority.

### 2.8 Summary (item 2)

- **Brief sections reviewed:** ~107 across all 12 present child briefs + charter + Item 0 (up from ~85 in v1.0, reflecting the 2 newly-added briefs' ~22 combined sections).
- **INVENTED (no plan authority):** unchanged from v1.0 — 1 substantial (CHARTER §7 judgment rubrics — self-declared DRAFT, gated on Cowork ratification, this is the intended and correct mechanism) + 1 minor (LANE1 §9 broadcasting to Lane 1 in addition to the plan-named Lanes 2/7). Neither new brief (LANE5, LANE9) introduces a new INVENTED section; LANE9 §3.1 is logged as a judgment call (Exceptions §3.10), not classified as INVENTED, because it is explicitly self-declared and doctrine-cited rather than silent.
- No brief section was found silently inventing scope, requirements, or grading criteria without either a plan citation or an explicit "derived/DRAFT"/judgment-call self-declaration.

---

## 3 — Exceptions (plan conflicts, infeasible directives, rubric judgment calls; honesty check per plan §12 doctrine)

Per plan §12 doctrine as restated in this session's task: **an empty exceptions section on a
build this size is itself suspicious.** This section is not empty; it carries forward all
exceptions logged in v1.0 (§3.1–§3.8, updated where the Lane 5/9 build changes their status)
plus new exceptions surfaced specifically by this regeneration pass (§3.9–§3.11).

**3.1 — Foundry-brief-as-implementing-surface.** Some plan §1/§3 directives (hard boundary,
executor identity) have no natural home in a *lane* brief — they are session-scope, not
lane-scope. The foundry's own governing brief (`CLAUDECODE_BRIEF_AUDIT_BRIEF_FOUNDRY_v1_0.md`)
is the only place they land. This matrix counts that as MAPPED since plan §12 item 4's phrase
"implementing brief section" is not restricted to child lane briefs, but this is an
interpretation, not a plan-stated rule — logged as a judgment call. (Unchanged from v1.0.)

**3.2 — Legacy 38-item battery grading-key continuity.** Plan §3 states the legacy battery
"keeps its existing Gemini/DeepSeek grading keys." No brief re-states or operationalizes this;
it is a statement about a DIFFERENT (pre-existing, non-foundry) asset, not a foundry build
target. Treated as informational plan context rather than a buildable element — a judgment
call, not a gap, but flagged for visibility. (Unchanged from v1.0.)

**3.3 — `asset_promises.jsonl` row count (67) vs plan's "~55 assets."** Plan §7 deliverable 9
and plan §5 Lane 10 both say "~55 assets (9 ga_* + 14 bo_* + 12 ka_* + 9 ph_* + 12 mi_* + 
services)" — 9+14+12+9+12 = 56 data-writer assets plus an unspecified number of services. The
ledger has 67 rows (one HEADER row + presumably 66 asset rows, or some other split not verified
in this pass). This matrix does not resolve whether 66/67 reconciles against "~55 + services";
that reconciliation is Lane 10's own job at compile time (LANE10_PROMISE.md §1), not this
matrix's. Note (new this pass): `LANE9_SUBSTRATE_INTEGRITY.md` §1.1 draws a 4-row slice from
this same ledger for its graph-asset identity reference (AP-018, AP-020, AP-021, AP-024) and
explicitly declares two of those four (`bo_cgm_motifs`, `bo_cgm_paths`) as `promise_quote: NOT
FOUND` at foundry build time, directing its own conductor to re-run the four-source search
before accepting that as final — this is the SAME "do not silently invent a promise"
discipline as Lane 10's, applied read-only by Lane 9, and does not change Lane 10's ownership
of the reconciliation. Flagged so the Cowork gate can check both the count reconciliation and
the two NOT-FOUND rows explicitly. (Updated from v1.0 with the new Lane 9 cross-reference.)

**3.4 — P-1, P-3, P-9 "thin" mapping.** Three of the thirteen §9 planning-phase-register rows
(P-1 vidhi/method, P-3 adjudication doctrine, P-9 narration vocabulary) map only to the general
"class-9 improvisation log" mechanism in CHARTER §2, with no dedicated brief subsection the way
P-2/P-4/P-6/P-7/P-8/P-12/P-13 each get. This is arguably faithful to the plan (their own audit
hook column literally says "class-9 logs" for all three, nothing more specific) — but it is
worth the Cowork gate confirming this isn't under-built relative to the other P-rows that got
dedicated extension sections. (Unchanged from v1.0.)

**3.5 — Open item §11.1/§11.2 (Lane 2 question list / Lane 8 facet checklist "debate status").**
Plan §11 states both are OPEN ITEMS pending "extensive native↔Fable 5 debate" before the brief
could be finalized. The briefs as found DO NOT show evidence of that debate having occurred
separately — LANE2's brief resolves the gate by pointing to the plan's OWN Appendix C
("native-approved 2026-07-11" per the brief's own annotation) and LANE8 treats Appendix B as
already-final ("THE FLOOR"). The plan document itself carries frontmatter marking these as
native-ratified as of round 3 (v1.3, 2026-07-11) — Appendix C's header says "native-approved
structure, 2026-07-11" and Appendix B's header says "native directive: maximal classical
extent." So the plan text is internally consistent that the debate closed and both appendices
are final AS OF THE PLAN'S OWN TEXT — but plan §11 (which is NOT superseded or struck in the
changelog) still lists both as "open items before the brief can be finalized," which reads as
stale/contradictory within the plan itself, not something the foundry resolved. This is a
**plan-internal inconsistency**, not a foundry invention — flagged per this task's explicit
instruction to actively look for exactly this class of open item. **This regeneration
re-confirms both open items remain in this same state: LANE2 and LANE8 are unchanged since
v1.0, and the plan document itself has not been amended.** (Status confirmed unchanged.)

**3.6 — Appendix C arithmetic: "76 types" vs verbatim-summed 82 types.** Already caught and
logged by the foundry itself (ledger `questions.jsonl` HEADER row; LANE2_QUESTION_MATRIX.md §1
"Known ledger surprise"). Restated here because it is a genuine plan-authoring defect (the
plan's own Appendix C preamble says "76 types" but A(6)+B(6)+C(5)+D(9)+E(8)+F(10)+G(6)+H(6)+
I(6)+J(6)+K(8)+L(6) = 82) that the foundry correctly did not silently "fix" — it transcribed
the fuller 82-type enumeration and froze the ledger at 328 rows, flagging the discrepancy
rather than resolving it unilaterally. This matrix endorses that as the correct BUILD-ONLY
behavior (foundry brief §7: "resist the temptation to quickly fix"). (Unchanged from v1.0.)

**3.7 — "§J" plan citation does not exist.** Plan line 172 (Lane 2 protocol) says grading is
per "(§J)" but the plan document has no section literally numbered/lettered §J. LANE2's brief
substitutes CHARTER §7.3 and states so explicitly (§1, "Note on the '§J' reference above").
Logged, not silently patched — correct handling, restated here for visibility. (Unchanged
from v1.0.)

**3.8 — RESOLVED (was the primary exception in v1.0): the two missing child briefs and the
state-file layer.** v1.0's load-bearing exception was that `LANE5_WIRE_FIDELITY.md`,
`LANE9_SUBSTRATE_INTEGRITY.md`, and `AUDIT_STATE.md` did not exist, against foundry brief §6
acceptance criteria 2 ("Charter + Item-0 brief + 10 child briefs exist" — should read "12" per
the governing brief's own count of Item-0 + 10 lanes... actually 11 lane-shaped units + charter;
regardless, the plain-language requirement was "all mandated briefs exist," which v1.0
correctly flagged as unmet) and 3 ("TRACEABILITY_MATRIX has ZERO unmapped plan elements or an
explicit exceptions entry per unmapped item"). **This gap is now closed.** Root cause (per
each new brief's own frontmatter `generated_by` field): "prior swarm attempt failed on a
transient API connection error; this is a clean regeneration, not a continuation of partial
output." Both briefs were rebuilt from scratch, self-contained, in a follow-up recovery pass,
and `AUDIT_STATE.md` was built in the same follow-up window. This exception entry is retained
(rather than deleted) so the review gate has a permanent record that this gap existed and was
closed, not merely that it never happened — see also the new process exception §3.11.

**3.9 — NEW: `AUDIT_STATE.md`'s own internally-declared reconciliation gap (Lane 5 / Lane 9
rows still PROVISIONAL).** `AUDIT_STATE.md` (built 2026-07-12) was constructed at a moment
when `LANE5_WIRE_FIDELITY.md` and `LANE9_SUBSTRATE_INTEGRITY.md` had not yet landed (or were
landing concurrently, per its own §6 "Known gaps": "being recovered by parallel sibling
agents"). Its index rows 6 (Lane5) and 10 (Lane9) are explicitly marked PROVISIONAL, with the
file's own text instructing: "Whoever regenerates this index after those two briefs land MUST
re-read them and correct rows 6 and 10 (ledger file, row count, rows-total, and — for Lane9 —
whether 9a's CGM graph node sample gets its own ledger or stays folded into Lane9's single
state shard)." **As of this matrix's build, both briefs now exist and this reconciliation has
NOT yet been performed** — that reconciliation is `AUDIT_STATE.md`'s own file to update, not
this matrix's (this matrix's scope is `TRACEABILITY_MATRIX.md` only, per this session's
constraints; `AUDIT_STATE.md` is out of this session's `may_touch` scope). Flagged explicitly
so the Cowork gate knows a small, well-scoped follow-up regeneration of `AUDIT_STATE.md` (not
of the traceability matrix, and not of the briefs themselves) remains outstanding before
execution begins. Concretely, once reconciled: Lane5's `rows-total` should become 3,058 (a
real number, not "provisional" — LANE5_WIRE_FIDELITY.md §2 confirms the full `value_families.
jsonl` ledger, all 3,058 rows, is Lane 5's scope, no narrower sampling boundary is imposed by
the brief); Lane9's index row should be split into two sub-counts per LANE9_SUBSTRATE_
INTEGRITY.md §8(b) — 9a's node-sample total (9 grahas + 12 bhavas + N active yogas, N derived
live at dispatch, so not a fixed number until execution begins) and 9b's fact_category total
(204, a fixed DB-derived number per LANE9 §1.2) — rather than a single undifferentiated
"3,058 provisional" figure that currently conflates the two sub-lanes.

**3.10 — NEW: `LANE9_SUBSTRATE_INTEGRITY.md` §3.1 widens "key bhavas" to "all 12 bhavas."**
Plan line 252 (Lane 9a protocol, verbatim) says the node sample is "each graha, key bhavas,
active yogas" — not "all bhavas." The brief explicitly widens "key bhavas" to all 12,
citing charter §1/§2.1 doctrine (examples-are-illustrative; the conductor "does not silently
narrow to a subjectively 'key' subset... narrowing the SAMPLE, as opposed to narrowing what
gets REPORTED, is itself the kind of silent width-cut the doctrine forbids"). This is a
defensible reading — narrowing which nodes get SAMPLED is arguably a more severe risk than
narrowing which get reported, and the doctrine is explicit that width-cuts are forbidden — but
it IS a widening beyond the plan's literal three-word phrase "key bhavas," done unilaterally by
the foundry without an explicit native ratification of that specific interpretive choice.
Logged for the Cowork review gate to explicitly bless or narrow back, rather than silently
inheriting a 33%-larger sample (12 vs. an unspecified "key" subset, likely fewer) than the
plan's literal words specify.

**3.11 — NEW (process exception, logged per explicit task instruction): the recovery episode
itself.** Two of the twelve mandated child briefs (`LANE5_WIRE_FIDELITY.md`,
`LANE9_SUBSTRATE_INTEGRITY.md`) plus `AUDIT_STATE.md` initially failed to be produced, or were
skipped, during the original Brief Foundry swarm run — the cause, per each recovered artifact's
own frontmatter, was a **transient API connection error mid-swarm**, not a plan-comprehension
failure, a scoping error, or a deliberate omission. All three artifacts were rebuilt from
scratch in a follow-up recovery pass (both new lane briefs explicitly self-describe as "a
clean regeneration, not a continuation of partial output," so there was no partial/corrupted
prior content to reconcile against). This matrix's own v1.0 was built DURING the gap (correctly
flagging 9 items UNMAPPED at that time, per the guarantee principle working as designed — see
Exceptions §3.8/plan §12 item 6) and this v2.0 regeneration closes the gap the moment the
recovery artifacts landed. Stated plainly, as honest audit-trail information rather than a
defect being hidden: **the Brief Foundry process, on its first attempt, did not fully complete
due to an infrastructure-level (not content-level) failure; the traceability-matrix mechanism
caught this mechanically and precisely (not diffusely); and the gap was closed by a
follow-up pass, verified in detail (not merely by file-existence check) in this regeneration.**
This is the exact failure-and-recovery pattern plan §12.6's "guarantee principle" (completeness
rests on ledgers/matrices, not diligence) is designed to produce, and this exception entry
records that it worked as designed.

---

## 4 — Summary for the review gate

| Metric | Value |
|---|---|
| Plan elements enumerated | ~145 (same enumeration granularity as v1.0) |
| Plan elements mapped | **~145 of ~145** |
| Plan elements UNMAPPED | **0** — all 9 items UNMAPPED in v1.0 are now MAPPED with precise in-brief section citations (§1.16 above lists each resolution) |
| Brief sections with no plan authority (INVENTED) | **2** — 1 substantial (CHARTER §7 rubrics, self-declared DRAFT/gated, expected) + 1 minor (LANE1 §9 broadcast over-scope) — unchanged from v1.0; the 2 new briefs (LANE5, LANE9) introduced 0 new INVENTED sections |
| Judgment calls flagged (not INVENTED, but not literal verbatim either) | **1 new this pass** — LANE9 §3.1 bhava-sample widening (Exceptions §3.10), in addition to the pre-existing judgment calls logged in §3.1–§3.8 |
| Exceptions logged | **11** (§3.1–§3.11; 8 carried forward from v1.0 with 2 updated in place — §3.3, §3.8 — to reflect the current state, plus 3 new: §3.9, §3.10, §3.11) |
| Foundry acceptance criteria met | **MET** — criterion 2 ("Charter + Item-0 brief + 10 child briefs exist," i.e. all 12 mandated briefs) now holds: 12/12 present. Criterion 3 ("ZERO unmapped plan elements... or an explicit exceptions entry per unmapped item") now holds on the STRICT reading (0 unmapped, not merely "9 unmapped but each has an exceptions entry"). Criterion 4 ("AUDIT_STATE skeleton carries real rows-total counts from the ledgers") holds with a carried-forward exception (§3.9: 10/12 units final, 2 units explicitly self-flagged provisional pending a routine, well-scoped reconciliation pass against the now-existing Lane5/Lane9 briefs — that reconciliation is `AUDIT_STATE.md`'s own file to perform, out of this matrix-only session's `may_touch` scope) |

**Recommendation to the review gate:** the primary structural gap from v1.0 (2 missing child
briefs) is closed and verified in this regeneration — proceed to the Cowork review gate
(Fable 5 + native) with this matrix as the current, complete traceability record. Two small,
low-risk follow-ups remain, neither of which blocks the gate on plan §12 item 4's own terms
(both are exceptions, not unmapped elements): (a) a routine regeneration of `AUDIT_STATE.md`
to replace its two PROVISIONAL rows with the now-derivable final counts (Exceptions §3.9); (b)
an explicit native/Fable-5 ratification (or correction) of `LANE9_SUBSTRATE_INTEGRITY.md`'s
"key bhavas" → "all 12 bhavas" widening (Exceptions §3.10). Both are naturally in scope for
the same review-gate pass that ratifies the DRAFT judgment rubrics (CHARTER §7) — none require
re-opening the brief-writing phase.

---

## 5 — Regeneration note (for readers comparing this version against v1.0)

This section exists solely to make the v1.0→v2.0 delta legible without diffing the two files
directly. v1.0 (built while 2 of 12 briefs and the state-file layer were missing, due to a
transient API connection error in the original swarm run) correctly and mechanically flagged
9 plan elements UNMAPPED, rather than silently passing an incomplete build — this is the
traceability mechanism (plan §12 item 4, foundry brief §6 criterion 3) working exactly as
designed: catching a real, narrow, well-understood gap instead of either hiding it or treating
it as unrecoverable. This v2.0 regeneration was built after `LANE5_WIRE_FIDELITY.md`,
`LANE9_SUBSTRATE_INTEGRITY.md`, and `AUDIT_STATE.md` were rebuilt in a follow-up recovery pass,
and re-derives every plan→brief and brief→plan mapping from scratch against the now-complete
12-brief set — it does not merely assert the 9 items are "now fine because the files exist";
each resolution in §1.16 above cites the exact section inside the recovered briefs that
implements the previously-missing plan element, located and read in full as part of this
regeneration (see the tool-use trail: `LANE5_WIRE_FIDELITY.md` and `LANE9_SUBSTRATE_
INTEGRITY.md` were read in their entirety, not sampled, before this matrix was written). All
other content in this matrix — the 10 briefs unchanged since v1.0 (confirmed via file-mtime
comparison: all 10 predate this session's start) — is carried forward without re-verification
beyond a structural section-header re-check (§1 and §2 tables above), since their content did
not change between v1.0 and this regeneration.

*End of TRACEABILITY_MATRIX v2.0 (REGENERATED-COMPLETE — for Cowork review gate). Supersedes
v1.0, which correctly flagged 9 plan elements UNMAPPED due to 2 missing child briefs
(LANE5_WIRE_FIDELITY.md, LANE9_SUBSTRATE_INTEGRITY.md) and a missing AUDIT_STATE.md, all
caused by a transient API connection error in the original Brief Foundry swarm run. Both
briefs and the state file were rebuilt in a follow-up recovery pass; this regeneration
verifies, section-by-section, that all 9 previously-unmapped items are now MAPPED.*
