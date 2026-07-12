---
artifact: CLAUDECODE_BRIEF_AUDIT_BRIEF_FOUNDRY_v1_0
type: CLAUDECODE_BRIEF
version: 1.1  # v1.1 (2026-07-11): swarm execution model per plan v1.3 §12.7 — foundry Phase 1/2 parallelized via sub-agents; child briefs must each carry their swarm decomposition section
status: COMPLETE  # foundry session closed 2026-07-12: 8 ledgers + 12 briefs + AUDIT_STATE + TRACEABILITY_MATRIX (0 unmapped) + FOUNDRY_CLOSE_REPORT v2.0 all built; see 00_ARCHITECTURE/llm_consumption_audit/FOUNDRY_CLOSE_REPORT.md
authored_by: Cowork (Fable 5) + native, 2026-07-11
session_type: claude_code_autonomous (Opus; native subscription; open time budget)
program: LLM Consumption Audit (governing plan: 00_ARCHITECTURE/briefs/LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md, v1.2)
phase: BRIEF FOUNDRY — builds the audit's ledgers + briefs + state + traceability. BUILDS ONLY. AUDITS NOTHING. FIXES NOTHING.
charts_in_scope:
  - 482012f1-710e-4a25-994a-93821f5871aa  # Abhisek
  - 1c826d5a-41cb-4450-b4dc-59d440e5f75a  # Abhinandan
may_touch:
  - 00_ARCHITECTURE/llm_consumption_audit/**        # ALL foundry output lands here (new directory)
  - 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_AUDIT_BRIEF_FOUNDRY_v1_0.md   # own status field at close
  - CLAUDECODE_BRIEF.md                             # this root copy: status field at close
must_not_touch:
  - platform/**                                     # NO code changes of any kind
  - 01_FACTS_LAYER/**, 025_HOLISTIC_SYNTHESIS/**    # no canonical-artifact edits
  - 00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md   # foundry logs NO findings; register belongs to execution sessions
  - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md           # session-close appends only per governance, not foundry content
  - any DB write of any kind                        # DB access is READ-ONLY (SELECT); no DDL/DML ever
acceptance_criteria: see §6
---

# BRIEF FOUNDRY — build the LLM Consumption Audit's execution machinery

## §0 — Mandatory reading, in order (before any other action)

1. `00_ARCHITECTURE/briefs/LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md` (v1.2) — THE GOVERNING
   PLAN. Read it in FULL, including §2.1, §12, Appendix A, Appendix B (60-facet floor),
   Appendix C (76-question list). Every sentence of it is in scope for traceability (§4
   below). This brief never overrides the plan; on any conflict, the plan wins and the
   conflict is logged in the traceability matrix's exceptions section.
2. `CLAUDE.md` §N (build standards), §L (do-nots) — orientation only.
3. `00_ARCHITECTURE/MARSYS_DEFECT_GAP_REGISTER_v2_0.md` — sections 1–8 headers + rows
   R-37..R-48 (the calibration anchor set) — read-only context for writing child briefs.
4. `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — the tool/asset catalog source.
5. `platform/` MCP server tool-definition source (read-only) — to enumerate the actual
   tool surface (~150 tools incl. aliases) with parameter schemas.

## §1 — Mission

Produce the complete, ledger-grounded execution machinery for the LLM Consumption Audit:
enumeration ledgers (from DB + manifest, never from memory), one master charter, ten
child lane briefs + an Item-0 brief, the AUDIT_STATE skeleton, and the two-way
traceability matrix. The guarantee principle (plan §12.6): completeness rests on ledgers
and traceability, not diligence.

Output directory (create): `00_ARCHITECTURE/llm_consumption_audit/`
```
  ledgers/        # machine-checkable ground truth (CSV or JSONL, one row per unit)
  briefs/         # charter + item0 + 10 child briefs
  AUDIT_STATE.md  # standing state file (skeleton)
  TRACEABILITY_MATRIX.md
  FOUNDRY_CLOSE_REPORT.md
```

## §2 — Phase 1: build the ledgers (DB + manifest grounding; the dry run)

**Execute this phase as a PARALLEL SUB-AGENT SWARM (plan §12.7): spawn one ledger-builder
sub-agent per ledger (8 concurrent), each writing ONLY its own ledger file; the conductor
(you) merges nothing — ledgers are disjoint — and verifies row counts on collection.**

Each ledger: one row per auditable unit, stable row_id, status column (pending/…), and a
`source` column citing where the row was enumerated from. Row counts go in the close
report. DB access is READ-ONLY.

| Ledger | Contents | Source |
|---|---|---|
| `tools.jsonl` | every MCP tool + alias, param schema hash, category | manifest + MCP server source |
| `value_families.jsonl` | every fact_category × fact_key in chart_facts; every column/row-family of chart_dashas, chart_divisionals, bodha_*, kala_*, phala_*, mimamsa_* tables; every L0 catalog family | live DB enumeration (SELECT DISTINCT), both charts |
| `services.jsonl` | every real-time computation service + the compute-on-demand test spec per service (7 dasha systems, transits, panchanga, muhurta, varshaphal, prashna, natal-compute, ephemeris) | manifest + tool source |
| `questions.jsonl` | plan Appendix C verbatim: 76 types × {narrow,broad} × 2 charts = ~304 rows | plan Appendix C (FROZEN at foundry time; note native may have appended) |
| `facets.jsonl` | plan Appendix B floor (60 groups, exploded to atomic facet rows) PLUS the discovery pass: per-graha fact families found in DB/L0 not covered by B — ADD rows, tag `discovered`; never delete B rows | Appendix B + DB/L0 discovery pass |
| `asset_promises.jsonl` | per asset (~55: ga_*/bo_*/ka_*/ph_*/mi_* + services): verbatim promise quote(s) with file+line citation from its build brief (00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_<asset>_*.md), asset_registry row, layer closure/handoff docs, MCP tool description | repo docs + DB asset_registry |
| `quantities.jsonl` | Lane 3 fixed quantity set: {dignity, house, sign, nakshatra+pada, shadbala, dasha-lord metadata} × 9 grahas × 2 charts × every serving path that carries it | derived from tools.jsonl × value_families.jsonl |
| `anchors.jsonl` | R-37..R-48 with their reproduction calls | register v2.4 rows |

Discovery-pass surprises (tables/categories that don't exist, empty tables, enumeration
anomalies — e.g. kala_activation row count, which doubles as Item-0 pre-data) are logged
in the close report as OBSERVATIONS, not findings — execution sessions convert them.

## §3 — Phase 2: write the charter + briefs

**Master charter** (`briefs/CHARTER.md`): doctrine (plan §2 + §2.1 verbatim), the 9-class
failure taxonomy (§4 verbatim), finding schema (§6), satisfaction criteria (§8), RESUME
protocol, and the JUDGMENT RUBRICS written out verbatim (no executor taste), including at
minimum: "usable form" rubric, "synthesizability-as-received" rubric, evidence-sufficiency
grading scale for Lane 2, ranking-quality metrics for Lane 6, promise-shortfall layer
attribution rules for Lane 10. Rubrics are DRAFT-flagged for the Cowork review gate.

**Item-0 brief** (`briefs/ITEM0_R45_TRIAGE.md`): the kala_activation writer-vs-serving
fork test (plan §5 Item 0), sequenced before all lanes.

**Execute brief-writing as a PARALLEL SWARM: one writer sub-agent per child brief,
spawned as soon as that brief's ledger lands; charter written first (it is every child's
dependency); traceability matrix is the sequential tail (needs all briefs).**

**Ten child briefs** (`briefs/LANE1_CENSUS.md` … `LANE10_PROMISE.md`): each SELF-CONTAINED
— charter by reference + everything its executor needs: its ledger file, its protocol from
plan §5 (transcribed fully, not summarized — anti-softening rule), its extensions, its
rubrics, its checkpoint/RESUME instructions, its deliverable spec, its per-lane coverage
self-declaration template. Lane 2's brief additionally carries the conductor+fresh-
sub-agent-per-question protocol and the P-12 manual mode (evidence plan BEFORE any call;
acquisition tracking; class-9 improvisation logging) with the verifier-sample re-grade
step (~15%).

**MANDATORY per-child-brief section — "Swarm decomposition" (plan §12.7):** each child
brief MUST specify: its conductor+worker pattern; its shard key (Lane 1a: tool batches ·
1b: table × fact_category · 1c: per service · Lane 2: question rows in concurrency-capped
batches of 5–10 · Lane 3: per graha · Lane 4: per tool · Lane 5: per fact family · Lane 6:
per ranked surface · Lane 7: per heavy question · Lane 8: per dossier (20 workers) · Lane
9a: per node sample / 9b: per fact_category · Lane 10: per asset for promise-compilation,
grading pass deferred to consolidation); its concurrency cap + throttling rule
(subscription limits); its merge protocol (workers write own shard traces only; conductor
merges; no shared-file writes); its per-shard RESUME semantics. The execution DAG in plan
§12.7 is transcribed into the charter verbatim: all lanes parallel; Item-0 broadcast to
Lanes 2/7 mid-flight; Lane-10 grading is the single sequential edge at consolidation.

**AUDIT_STATE skeleton** — parallelism-safe form per plan §12.7: top-level
`AUDIT_STATE.md` is a regenerable INDEX (counts only, idempotent regeneration) over
per-lane shard files `state/LANE<k>.md`, each owned exclusively by its lane conductor;
atomic-update instructions; RESUME pointer format per shard.

## §4 — Phase 3: two-way traceability

`TRACEABILITY_MATRIX.md`:
- **plan→brief**: EVERY plan element (every §, directive, lane extension, appendix row
  group, Appendix A row) → the implementing brief section(s). Any unmapped element =
  foundry NOT complete (hard gate). Include the plan's Appendix A so the chain
  native-directives → plan → briefs is verifiable end-to-end.
- **brief→plan**: every brief section → its plan authority; sections with no authority are
  flagged INVENTED for the review gate (inventions are not necessarily wrong — they must
  be visible).
- **Exceptions section**: plan conflicts, infeasible directives, rubric judgment calls —
  honestly listed for the Cowork gate. An empty exceptions section on a build this size is
  itself suspicious; report honestly.

## §5 — Phase 4: self-check + close

1. Ledger sanity: row counts vs independent recount (fresh queries); zero-row ledgers are
   a HALT (something is wrong with enumeration, not with the world).
2. Anti-softening pass: diff each child brief's protocol section against plan §5 text —
   every plan sentence must be present or strengthened, never paraphrased into vagueness.
3. `FOUNDRY_CLOSE_REPORT.md`: ledger row counts, discovery-pass observations (incl.
   kala_activation counts), exceptions summary, rubric-draft list for review, and the
   explicit statement that NO audit was performed and NO fix was made.
4. Set this brief's `status: COMPLETE`. Do NOT begin any lane execution — the review gate
   (Cowork: Fable 5 + native, plan §12.5.iii) stands between foundry and execution.

## §6 — Acceptance criteria (all must hold)

1. All 8 ledgers exist, non-empty, DB/manifest-sourced, with per-row provenance.
2. Charter + Item-0 brief + 10 child briefs exist; each child brief passes the
   anti-softening diff.
3. TRACEABILITY_MATRIX has ZERO unmapped plan elements (or an explicit exceptions entry
   per unmapped item).
4. AUDIT_STATE skeleton carries real rows-total counts from the ledgers.
5. FOUNDRY_CLOSE_REPORT complete; no audit performed; no fix made; no DB write made.
6. Session-close per governance (SESSION_CLOSE template + SESSION_LOG append).

## §7 — Hard constraints (repeat of the non-negotiables)

- BUILD ONLY. The temptation to "quickly verify" a defect or patch an obvious bug is the
  known failure mode of prior campaigns (plan §1) — resist it; log an observation instead.
- DB = SELECT only. Prod MCP may be CALLED only where a ledger row requires a schema/
  shape confirmation, never for systematic auditing (that is the execution sessions' job).
- Plan is authority; this brief is its executor; Cowork review gate is the exit.

*End of CLAUDECODE_BRIEF_AUDIT_BRIEF_FOUNDRY_v1_0.*
