---
title: Lane 9 — L2 Substrate Integrity (9a CGM Graph Leverage + 9b MSR Ingestion) — Child Brief
canonical_id: LANE9_SUBSTRATE_INTEGRITY_BRIEF
version: 1.0
status: DRAFT (Section 7 rubrics of the charter are gated on Cowork ratification — see below)
source_plan: 00_ARCHITECTURE/briefs/LLM_CONSUMPTION_AUDIT_PLAN_v1_0.md (§5 Lane 9, lines 245-270)
charter: 00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md (canonical_id LLM_CONSUMPTION_AUDIT_CHARTER)
generated_by: Brief Foundry session, 2026-07-11 (recovery build, 2026-07-12 — prior attempt failed on a
  transient API connection error; this is a from-scratch self-contained regeneration, not a patch)
---

# Lane 9 — L2 Substrate Integrity — SELF-CONTAINED CHILD BRIEF

**This brief is executable by a FRESH session that has read nothing else.** It is
self-contained: it cites the charter for doctrine/taxonomy/finding-schema/satisfaction
criteria/rubrics rather than re-deriving them, and it supplies everything else — both
sub-lanes' ledger scopes, protocol (transcribed in full, not summarized), deliverable spec,
coverage-declaration template, checkpoint/RESUME mechanics, and swarm decomposition —
standalone in this document.

Lane 9 covers **two sub-lanes under one lane conductor**: **9a** (CGM graph leverage audit)
and **9b** (MSR ingestion coverage + fidelity audit). Plan §5 frames both as auditing "the
two upstream engines everything else consumes — if either is broken, downstream lanes
measure symptoms of a single cause." They are treated as one lane (one conductor, one state
shard) because their findings are read together at consolidation, but they run as two
independent shard streams (Section 8 below) and may be worked in either order or fully in
parallel.

## 0 — Charter reference (READ THIS FIRST, then return here)

Before any work, read in full:
`/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/llm_consumption_audit/briefs/CHARTER.md`
(canonical_id `LLM_CONSUMPTION_AUDIT_CHARTER`, v1.0).

Do NOT re-derive or paraphrase these — the charter is binding by reference:
- **§1 Doctrine** (charter §1, = plan §2 + §2.1 verbatim) — the two completeness axes
  (width, depth) and the "examples are illustrative, never limiting" doctrine. For 9a this
  means: the graph's neighborhood grading (structural completeness) is judged against the
  full classical dispositor/yoga/temporal-hook space, not just the sampled nodes' obvious
  edges. For 9b this means: the L1→MSR ingestion matrix is judged against the FULL set of
  L1 fact_categories the DB actually holds (ledger-derived), never against a remembered or
  assumed subset.
- **§2 9-class failure taxonomy** (charter §2, = plan §4 verbatim) — every finding this
  lane logs gets exactly one primary class from this list (classes 1-9). Expect classes 1
  (UNREACHABLE), 4 (EMPTY SHELL), 6 (UNUSABLE FORM), 7 (DROWNED), and 9 (UNGOVERNED
  JUDGMENT) to dominate 9a; classes 1, 5 (DISHONEST SELF-DESCRIPTION), 6, and 7 to dominate
  9b, per the known evidence cited in the protocol below.
- **§3 Finding schema** (charter §3, = plan §6 verbatim) — every finding record's
  required fields: reproducible call, verbatim evidence excerpt, primary failure class,
  severity, suspected layer, dedupe check against the register (`MARSYS_DEFECT_GAP_REGISTER_
  v2_0.md`, anchor rows R-37..R-48 at lines 226-236).
- **§4 Satisfaction criteria** (charter §4, = plan §8 verbatim) — all five must hold.
  Criterion 1 (census completeness) binds 9b's ingestion-matrix rows to be DB-derived and
  exhaustive; criterion 3 (depth completeness) binds 9a's node-sample dossiers to the full
  facet space (Appendix B of the plan — 60 facet groups — is the depth reference for any
  node whose neighborhood is graded).
- **§5 RESUME protocol** (charter §5) — the general AUDIT_STATE / shard discipline this
  lane's RESUME mechanics (Section 6 below) instantiate, doubled for two shard streams.
- **§6 Execution DAG** (charter §6, = plan §12.7 verbatim) — this lane's place in the
  overall audit: `Lane9a` and `Lane9b` both run PARALLEL with every other lane during
  EXECUTION (no dependency edge forces either to wait); neither is a consolidation-only
  pass (unlike Lane 10's grading half) — both sub-lanes' findings land directly in the
  report and findings JSON from this brief's own execution.
- **§7 Judgment rubrics** — subsection **7.1 ("Usable form" rubric)** governs 9a's
  consumption-axis grading (can a graph neighborhood be retrieved and used in ≤2 calls, in
  usable form?) and 9b's fidelity grading (are ingested signals delivered in usable form?).
  Subsection **7.4 (Ranking-quality metrics, Lane 6)** is the reference metric set for 9b's
  salience-class grading (UNATTRIBUTED share, family-collapse coverage) since MSR salience
  tiers ARE a ranked surface in the sense §7.4 defines. Both are DRAFT, gated on Cowork
  ratification (Fable 5 + native) per plan §12 item 4 — this lane's conductor may run the
  full evidence-acquisition and matrix-building work now, but any verdict that depends on
  the DRAFT rubric thresholds must be flagged `PENDING-RUBRIC-RATIFICATION` in the finding
  record until the charter's status is updated, rather than silently assuming ratification.

## 1 — Ledgers

Lane 9 draws on **two ledger files**, one per sub-lane, both already built by the Brief
Foundry's ledger-enumeration pass:

### 1.1 — 9a ledger: `asset_promises.jsonl` (graph-owning assets slice)

`/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/llm_consumption_audit/ledgers/asset_promises.jsonl`

Full file: 67 rows (`AP-001`..`AP-067`), JSONL, one JSON object per row, row schema:
```json
{"row_id": "AP-###", "asset_id": "<asset_id>", "layer": "L0|L1|L2|L3|L4|L5|SERVICE",
 "promise_quote": "<verbatim quote or NOT FOUND>",
 "promise_source_citation": "<file:line or 'none'>",
 "asset_registry_row_present": true|false,
 "status": "pending|compiled|graded"}
```

9a's scope is the **graph-owning asset slice** of this ledger — the rows whose promise
text and/or backing tables constitute "the graph" (CGM = Chart Graph Model). As enumerated
at Foundry build time, this slice is:

| row_id | asset_id | promise (verbatim excerpt) |
|---|---|---|
| AP-024 | bo_karanajala | "the heavy writer that does the whole compute + owns edges/sub_graphs/motifs/topology/paths/contradictions" |
| AP-018 | bo_bimba | "a THIN nodes-only face that registers bodha_cgm_nodes from the same compute (it does not recompute the graph)" |
| AP-020 | bo_cgm_motifs | NOT FOUND (at Foundry build time — re-verify per the four-source search below before accepting) |
| AP-021 | bo_cgm_paths | NOT FOUND (at Foundry build time — re-verify per the four-source search below before accepting) |

These 4 rows are 9a's ASSET-IDENTITY reference only — they tell the conductor which
writers own which graph tables. 9a's actual audit unit is NOT an asset row but a **node
sample** (Section 8 below), queried directly against the backing tables:
`bodha_cgm_nodes`, `bodha_cgm_edges`, `bodha_cgm_sub_graphs`, `bodha_cgm_motifs`,
`bodha_cgm_paths`, `bodha_cgm_chart_topology_summary`, `bodha_contradictions` (all present
in `value_families.jsonl` under `table_name` values `bodha_cgm_*` plus `bodha_contradictions`
— 9a's conductor MAY cross-reference `value_families.jsonl` rows for these table names to
confirm column-level structure before dispatching node-sample workers, but the primary
ledger of record for 9a is this `asset_promises.jsonl` slice, per the brief's explicit
instruction).

Where a `promise_quote` is `NOT FOUND` (bo_cgm_motifs, bo_cgm_paths), 9a's conductor
independently re-runs the four-source search (build brief, `asset_registry` row, layer
handoff/closure doc, MCP tool description) before accepting `NOT FOUND` as final — same
discipline as Lane 10 (see `LANE10_PROMISE.md` §1 for the precedent; do not silently invent
a promise). This does NOT make 9a responsible for the asset_promises ledger's `status`
field — Lane 10 owns that field's lifecycle for ALL 67 rows, including these 4. 9a's
conductor records its own re-verification finding in ITS OWN shard trace (Section 8), and
MAY leave a note for the Lane 10 conductor if a materially different promise text is found,
but does not edit `asset_promises.jsonl` directly (that file's write ownership belongs to
Lane 10 per `LANE10_PROMISE.md` §8(d) — Lane 9 is READ-ONLY against this ledger).

### 1.2 — 9b ledger: `value_families.jsonl` (bodha_* families + chart_facts fact_category families)

`/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/llm_consumption_audit/ledgers/value_families.jsonl`

Full file: 3,058 rows (`VF-1`..`VF-3057` approx — row_ids are not necessarily contiguous
across table boundaries; treat the file as the source of truth, not the numeric range),
JSONL, row schema:
```json
{"row_id": "VF-####", "table_name": "<table>", "family_key": "<fact_category::fact_key
 or column_name or column_name=value>", "grain": "per-chart", "chart_ids_observed":
 ["482012f1-...", "1c826d5a-..."], "source": "<SQL or derivation note>", "status": "pending"}
```

9b's scope spans TWO slices of this one ledger, forming the two sides of the ingestion
matrix:

- **Production side — `table_name = "chart_facts"`**: 1,219 rows in `value_families.jsonl`
  whose `family_key` is of the form `<fact_category>::<fact_key>`. Extracting the distinct
  prefix before `::` yields **204 distinct L1 fact_categories** as of Foundry build time —
  this is the exhaustive, DB-derived denominator for "every L1 fact_category" in the
  protocol below (plan §12 item 2: ledger-driven, never from memory). Examples observed:
  `anumukha_shani_period`, `ashtakavarga_bindu`, `argala_natal_matrix`, `bhava_bala_lord`,
  `aspect_parashari_given` — the conductor derives the FULL 204-category list by scanning
  the ledger at shard-dispatch time (Section 8), not by copying this illustrative sample.
- **Consumption side — `table_name = "bodha_msr_signals"`**: 115 rows in
  `value_families.jsonl`, one per column/enum-value family of the MSR signal table (the
  "funnel" itself — bo_laksana's output). Columns directly relevant to the matrix's four
  required grading axes (protocol below) are already enumerated in this ledger slice:
  - **entity attribution** → `constituent_facts_array` (resolves back to `chart_facts.fact_id`
    per CLAUDE.md §I B.3 / §N.5 — this is the exact field R-44a's "298/300 UNATTRIBUTED"
    finding is about)
  - **salience class** → `signature_tier` (enum values observed in the ledger:
    `signature_tier=chart_defining`, `=major`, `=supporting`, `=background` — this is the
    exact field R-44b's "descriptive trivia at 'major' tier" finding is about)
  - **domain mapping** → `domains_affected_array`, `domain_salience_jsonb` (this is the
    exact surface KP-4's "domain-mapped to a default so they can never surface in wealth
    queries" finding is about)
  - **emergence count / provenance** → `source_l1_asset`, `signal_type_class` (enum values
    include `=yoga`, `=dosha`, `=panchanga`, `=varga_pattern`, `=karaka_alignment`,
    `=parivartana`, `=sade_sati`, `=tradition_specific`, `=composite_state`, `=annual` — the
    per-fact_category "emerging as how many signals" count is a COUNT of `bodha_msr_signals`
    rows whose `constituent_facts_array` resolves back to that fact_category, grouped by
    `signal_type_class`)
  Also present in this slice (available for grading dosha-attribution and cross-tradition
  breadth, relevant to R-42): `classical_sources_array`, `cross_system_consensus_count`,
  `source_corroboration_count_by_text`, `source_corroboration_count_by_verse`,
  `epistemic_tier` (enum values include `=classical_match`, `=computed_extension`,
  `=documented_approximation`, `=two_pass_verified`, `=single_pass`).
- Also present in `value_families.jsonl` but OUT OF 9b's primary matrix scope (available
  for cross-reference, not required rows): the remaining ~670 `bodha_*` rows across
  `bodha_anomalies`, `bodha_cdlm_*`, `bodha_cgm_*` (shared with 9a, read-only overlap — see
  Section 1.1), `bodha_chart_gestalt`, `bodha_contradictions`, `bodha_convergence`,
  `bodha_discoveries`, `bodha_pratijna`, `bodha_question_lenses`, `bodha_rm_*`,
  `bodha_signal_embeddings`, `bodha_triangulation`. 9b's conductor may consult these for
  context (e.g., `bodha_triangulation` / `bodha_convergence` when grading "emerging as how
  many signals" for a fact_category that feeds multi-signal convergence) but the matrix's
  REQUIRED grading columns are sourced from the `bodha_msr_signals` slice specifically,
  since MSR (`bodha_msr_signals`, written by `bo_laksana`) is explicitly named as "the
  funnel" in the protocol.

**Completeness is a count query on both ledger slices**: 9a is complete when every sampled
node (Section 8 shard key) has a completed shard trace; 9b is complete when all 204
fact_categories × the four grading axes have a matrix row with a non-pending verdict.

## 2 — Protocol (plan §5 Lane 9, lines 245-270, TRANSCRIBED IN FULL — verbatim, never
paraphrased; anti-softening discipline)

> ### Lane 9 — L2 substrate integrity: the graph and the MSR funnel (native review round 1)
>
> The two upstream engines everything else consumes — if either is broken, downstream lanes
> measure symptoms of a single cause. Both get first-class audits:
>
> **9a. CGM graph leverage audit.** The graph is one of the strongest assets: for any node
> it should yield the associated relevant data points a synthesis must consider. Audit:
> (i) structural — for a sample of nodes (each graha, key bhavas, active yogas), traverse
> the graph and grade the neighborhood for completeness (does Mercury's node reach its
> dispositor chain, its yogas, its bhava lords, its temporal hooks?) and correctness (edges
> cite L1 fact_ids per B.3); (ii) consumption — can the LLM actually retrieve and use a
> neighborhood in ≤2 calls, in usable form? (iii) leverage — does ANY serving instrument
> compose graph context into answers today, or is the graph a parked database? Known
> evidence: v2.2 chain-integrity rows; G-6 (no multi-hop chain signal class in MSR);
> zero graph-derived context received in the 2026-07-11 consumption session.
>
> **9b. MSR ingestion coverage + fidelity audit.** MSR is the funnel through which Gaṇita
> reaches every downstream consumer. Audit the funnel itself: build the **L1→MSR ingestion
> matrix** — every L1 fact_category × {consumed by bo_laksana? at what salience class? with
> what entity attribution? with what domain mapping? emerging as how many signals?}. Grade
> each mapping for design correctness from the consumer's perspective. Known evidence of
> indiscriminate ingestion: 298/300 top candidates UNATTRIBUTED (R-44a); descriptive trivia
> at "major" tier (R-44b); all doshas citing one constituent fact (R-42); KP categories
> domain-mapped to a default so they can never surface in wealth queries (KP-4). The lane
> answers the native's question directly: is MSR's read of the Gaṇita layer designed
> correctly, and is it being leveraged correctly for the LLM?

**This is the entirety of the plan's Lane 9 description. Nothing in it is optional, and
nothing below in this brief may weaken any clause above.** In particular, note the exact
three grading axes 9a requires per sampled node (structural / consumption / leverage — not
two, not a merged score) and the exact five columns 9b's ingestion matrix requires per
fact_category (consumed-by-bo_laksana? / salience class / entity attribution / domain
mapping / signal-emergence count — five distinct cells, not a single verdict).

### 2.1 — Known-evidence anchors this lane MUST independently rediscover

Per charter §3 ("Known-findings anchor set... the audit MUST independently rediscover them
via its lanes; any it misses indicates a lane-coverage hole"), Lane 9 carries direct
responsibility for rediscovering:
- **9a:** the v2.2 chain-integrity rows (locate and re-verify against current DB state);
  **G-6** (no multi-hop chain signal class in MSR — cross-check against 9b's
  `signal_type_class` enum list in Section 1.2, which as enumerated has no explicit
  multi-hop/chain category, consistent with G-6); **zero graph-derived context received in
  the 2026-07-11 consumption session** (this is a LEVERAGE-axis finding — 9a's audit item
  (iii) — and must be re-tested live, not assumed still true, since the consumption session
  predates this audit and serving code may have changed).
- **9b:** **R-44a** (298/300 top candidates UNATTRIBUTED — re-derive the current ratio via
  a `constituent_facts_array` emptiness/null check over `bodha_msr_signals` for both
  charts, do not assume the historical ratio still holds); **R-44b** (descriptive trivia at
  "major" tier — re-grade current `signature_tier=major` rows against the classical-canon
  weighting per charter §7.4 metric 3); **R-42** (all doshas citing one constituent fact —
  re-check `signal_type_class=dosha` rows' `constituent_facts_array` cardinality);
  **KP-4** (KP categories domain-mapped to a default — re-check `domain_salience_jsonb` /
  `domains_affected_array` for any `signal_tradition`/`signal_type_class` value associated
  with KP methodology, confirming whether wealth-domain (2nd/11th house significators)
  KP signals can in fact surface under a wealth-domain query today).

A miss on any of these six anchors is itself a class-9 (UNGOVERNED JUDGMENT) /
lane-coverage finding against THIS brief's own execution — log it in the coverage
self-declaration (Section 7) if it occurs.

## 3 — 9a extension: the three-axis grading discipline per sampled node

Plan line 252-257 names exactly three axes; do not collapse them into one score per node:

1. **Structural** — traverse the graph from the node outward and grade:
   - **Completeness**: for a graha node, does the neighborhood reach its dispositor chain
     (sign dispositor → nakshatra dispositor → navamsha dispositor → terminus, per plan
     Appendix B §B-V.32), its yoga memberships (§B-VI.41), its bhava lordships (§B-VI.37),
     and its temporal hooks (dasha lordship windows, §B-VII.44)? For a bhava node, does the
     neighborhood reach its occupants, its lord, its aspects received, and its arudha
     (§B-VI.40)? For a yoga node, does the neighborhood reach every participating graha and
     the yoga's cancellation/bhanga conditions if any (§B-II.11)?
   - **Correctness**: does every edge in the traversed neighborhood carry a resolvable
     citation back to an L1 `fact_id` (CLAUDE.md §I B.3 derivation-ledger mandate — query
     `bodha_cgm_edges` for a `constituent_fact` / citation-bearing column; if the column is
     absent or null for sampled edges, that is itself a class-2 (WRONG) or class-6
     (UNUSABLE FORM) finding depending on whether the edge's underlying claim is simply
     uncited or actively unverifiable)?
2. **Consumption** — for the SAME sampled node, attempt actual MCP-tool retrieval of its
   neighborhood exactly as a consuming LLM would (no prior schema knowledge beyond tool
   descriptions). Grade per charter §7.1 ("Usable form" rubric) and §7.2
   ("Synthesizability-as-received" rubric, applied on first contact): can the neighborhood
   be retrieved in **≤2 tool calls**? Is the returned form usable (resolvable IDs, no
   mid-clause truncation, disclosed budget, findable signal — not drowned under duplicate
   edges)? A neighborhood requiring 3+ calls, or requiring a call sequence not implied by
   any tool's description, fails this axis (log class 1 UNREACHABLE if no reachable path
   exists in ≤2 calls at all; log class 9 UNGOVERNED JUDGMENT for any undocumented-sequence
   instance per charter §7.2 PARTIAL-grade guidance).
3. **Leverage** — independent of whether the graph IS retrievable, test whether it actually
   IS leveraged: run a representative synthesis-style query (e.g., an orientation read, a
   domain reading, a Whole-Chart-Read per CLAUDE.md §I B.11) through whatever serving
   instrument currently exists, and check whether ANY graph-derived context (edges, motifs,
   paths, sub_graphs, contradictions) appears in the composed answer. If none does, the
   graph is a **parked database** for that surface — log as class 4 (EMPTY SHELL) at the
   SERVING layer (not the data layer — the data may be structurally sound per axis 1) plus
   a class-9 note if the failure to leverage forced the executor into ungoverned
   improvisation to answer the query without graph context.

### 3.1 — Node sample composition (the shard key, detailed in Section 8)

Per protocol line 252 ("each graha, key bhavas, active yogas"): the sample is not
open-ended. It is exactly:
- **Each graha**: Surya, Chandra, Mangala, Budha, Guru, Shukra, Shani, Rahu, Ketu (9 nodes;
  include both nodes and their Lagna-relative functional roles where the graph models
  them separately).
- **Key bhavas**: all 12 bhavas are in scope (the protocol says "key bhavas," not "all
  bhavas" — but per charter §1 doctrine's width axis and §2.1 "examples are illustrative,
  never limiting," the conductor does not silently narrow to a subjectively "key" subset;
  it samples all 12 and lets the grading results themselves show which bhavas are
  structurally thin — narrowing the SAMPLE, as opposed to narrowing what gets REPORTED, is
  itself the kind of silent width-cut the doctrine forbids).
- **Active yogas**: every yoga currently flagged present for EITHER chart in scope
  (Abhisek `482012f1-710e-4a25-994a-93821f5871aa`, Abhinandan `1c826d5a-41cb-4450-b4dc-
  59d440e5f75a`) per `bodha_msr_signals` rows where `signal_type_class=yoga` — this set is
  DB-derived at shard-dispatch time, not assumed from memory or from the plan's illustrative
  yoga list (Appendix B §B-VI.41 is the CATALOG reference for what a yoga finding should be
  graded against, not the sample-selection list itself).

## 4 — 9b extension: the ingestion-matrix build discipline per fact_category

For EACH of the 204 fact_categories (Section 1.2), the conductor's worker fills exactly
five cells, each independently verified against the DB (read-only SELECT):

1. **Consumed by bo_laksana?** — does AT LEAST ONE `bodha_msr_signals` row (for either
   chart in scope) have a `constituent_facts_array` entry resolving to a `chart_facts` row
   whose `fact_category` matches this category? YES/NO, with the resolving `signal_id`(s)
   as evidence if YES, or an explicit confirmation the category was checked and found
   absent if NO (absence is itself a finding — class 1 UNREACHABLE-by-omission from MSR,
   distinguished per charter §7.3 from UNREACHABLE-BY-NONEXISTENCE, since the fact DOES
   exist in `chart_facts` — it is MSR that failed to ingest it).
2. **At what salience class?** — for every resolving row from (1), record its
   `signature_tier` value(s) (`chart_defining` / `major` / `supporting` / `background`). If
   a fact_category's signals cluster entirely at `major` or `chart_defining` despite being
   low-decision-weight descriptive trivia by classical-canon weighting (charter §7.4 metric
   3 as adapted), that is the R-44b pattern — log it.
3. **With what entity attribution?** — for every resolving row, check
   `constituent_facts_array` cardinality and resolvability: is it non-empty AND does every
   entry resolve to a real `chart_facts.fact_id`? A category whose signals are systematically
   empty/null/unresolvable on this field is the R-44a pattern (298/300 UNATTRIBUTED anchor)
   — log the CURRENT ratio for this category, not the historical anchor number.
4. **With what domain mapping?** — for every resolving row, record `domains_affected_array`
   / `domain_salience_jsonb` contents. If a category's signals are ALWAYS mapped to the same
   default domain set regardless of the fact's actual domain relevance (the KP-4 pattern —
   e.g., 2nd/11th-house wealth significations that should map to the wealth domain but map
   to a generic default instead), log it as class 2 (WRONG) at minimum, with a note on
   whether it also produces a class-1 (UNREACHABLE) consequence for domain-filtered queries.
5. **Emerging as how many signals?** — the raw COUNT of `bodha_msr_signals` rows (per chart)
   whose `constituent_facts_array` resolves back to this fact_category, broken out by
   `signal_type_class`. A category that is heavily represented in `chart_facts` (many
   fact_keys) but emerges as zero or near-zero MSR signals is a funnel-narrowing finding in
   its own right (class 1, at the ingestion-design layer) — distinct from, but often
   correlated with, a NO answer on cell 1.

**Design-correctness grading** (protocol: "Grade each mapping for design correctness from
the consumer's perspective") is applied AFTER all five cells are filled for a category: does
the resulting salience/attribution/domain-mapping combination make the category's signal(s)
FINDABLE and TRUSTWORTHY to a consuming LLM composing an answer in that category's domain?
A category that scores well numerically (many signals) but whose signals are all
`UNATTRIBUTED` and mis-domain-mapped still fails design-correctness — the five cells are
diagnostic inputs to one qualitative verdict per category, not five independent pass/fails
to average.

## 5 — Extensions: type-specimen handling

Both R-44a/R-44b (9b) and the "zero graph-derived context" finding (9a) are TYPE SPECIMENS
(the term used identically in `LANE10_PROMISE.md` §4.2 for its own anchors) — they define
the shape of the failure mode the rest of the sample/matrix is checked against, and must
never be silently deferred. Additionally:
- **R-42** (all doshas citing one constituent fact) is a type specimen for 9b's
  `signal_type_class=dosha` slice specifically — when the worker for any fact_category that
  feeds a dosha signal reaches cell 3 (entity attribution), it MUST cross-check whether
  MULTIPLE dosha signals across DIFFERENT fact_categories all resolve to the SAME single
  `constituent_facts_array` entry (the R-42 pattern is a cross-category collapse, not a
  single-category defect — the conductor's merge step, not any one worker, is positioned to
  see this pattern; flag it explicitly in the merge summary, Section 8(a)).
- **G-6** (no multi-hop chain signal class in MSR) is a type specimen for 9a's structural
  axis AND for 9b's `signal_type_class` enum completeness check (Section 2.1) — both
  sub-lanes must independently confirm or refute it from their own evidence; a disagreement
  between the two sub-lanes' findings on this point is itself reportable (class 3
  INCONSISTENT, applied to the audit's own findings — an honest audit surfaces its own
  internal disagreements rather than silently picking one).

## 6 — Checkpoint / RESUME instructions

**State file (owned exclusively by this lane's conductor):**
`/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/llm_consumption_audit/state/LANE9.md`

Per charter §5 (RESUME protocol) and §6 ("State discipline under parallelism"):
- This file is a **shard** of the top-level `AUDIT_STATE.md` index, owned exclusively by
  the Lane 9 conductor. No other lane's conductor writes to it; this lane's conductor
  writes to no other lane's shard.
- **Atomic idempotent regeneration:** every write to `state/LANE9.md` is a full
  regeneration computed from (a) the count of completed 9a node-sample shard trace files
  and (b) the count of completed 9b fact_category shard trace files currently on disk
  (Section 8 below) — never a hand-edited diff. The conductor writes the ENTIRE shard file
  in one atomic write (write-to-temp-then-rename, or equivalent) each time. Re-running the
  same regeneration twice against the same on-disk shard-trace state produces byte-identical
  output.
- **RESUME pointer = last completed shard id**, tracked SEPARATELY per sub-lane stream
  (this lane has two independent shard id-spaces, unlike Lane 10's single stream):
  - 9a: the shard id is the node identifier (e.g., `graha-budha`, `bhava-07`,
    `yoga-<signal_id>`) — see Section 8(b) for the exact naming scheme.
  - 9b: the shard id is the fact_category string itself (e.g., `ashtakavarga_bindu`,
    `bhava_bala_lord`).
  A resumed/fresh conductor session:
  1. reads `state/LANE9.md` for the last-checkpointed summary (9a rows-done/total, 9b
     rows-done/total, findings-count for each);
  2. re-scans BOTH shard-trace directories directly (Section 8(d)) — never trusts the
     summary alone, the shard files on disk are truth;
  3. resumes dispatching workers only for node ids / fact_category ids without a completed
     shard trace file;
  4. never re-dispatches a worker for an id that already has a completed shard trace
     (idempotent skip).
- **Atomicity contract** (charter §5): every checkpoint write must leave the shard
  self-consistent — both sub-lanes' counts, the combined findings-count, and status all
  updated together in the same write. A torn/partial write is itself a defect to avoid, not
  a valid RESUME state.

### 6.1 — `state/LANE9.md` minimum content (regenerated each checkpoint)

```
# LANE9 (Substrate Integrity: 9a CGM graph + 9b MSR ingestion) — state
last_regenerated: <ISO8601 timestamp>

## 9a — CGM graph leverage audit
node_sample_total: <9 grahas + 12 bhavas + N active-yogas, N derived at dispatch>
node_sample_done: <count>
last_node_id_done: <e.g. graha-shani>
shard_trace_dir: state/LANE9/
findings_count: <N>

## 9b — MSR ingestion coverage + fidelity audit
fact_category_total: 204
fact_category_done: <count>
last_fact_category_done: <e.g. bhava_bala_lord>
shard_trace_dir: state/LANE9/
findings_count: <N>

## cross-sub-lane notes
notes: <e.g. R-42 cross-category collapse pattern status; G-6 agreement/disagreement
  between 9a and 9b findings; any PENDING-RUBRIC-RATIFICATION flags outstanding>
```

## 7 — Per-lane coverage self-declaration template (TAP-9 style)

Every surface this lane could plausibly touch is either AUDITED or explicitly DEFERRED
with reason — no silent gaps. Populate this table at lane close and carry it into the
final report per plan §7 deliverable 1 / §8 criterion 4 (Coverage honesty):

| surface | status (audited/deferred) | reason-if-deferred |
|---|---|---|
| 9a — graha nodes (9 of 9: Surya..Ketu) | audited / deferred | |
| 9a — bhava nodes (12 of 12) | audited / deferred | |
| 9a — active-yoga nodes (all `signal_type_class=yoga` rows, both charts) | audited / deferred | |
| 9a — structural axis (completeness + correctness) | audited / deferred | |
| 9a — consumption axis (≤2-call retrievability, usable form) | audited / deferred | |
| 9a — leverage axis (serving-instrument composition test) | audited / deferred | |
| 9a — v2.2 chain-integrity rows re-verification | audited / deferred | must never be deferred — known-evidence anchor |
| 9a — G-6 re-verification | audited / deferred | must never be deferred — known-evidence anchor |
| 9a — "zero graph-derived context" re-test (2026-07-11 anchor) | audited / deferred | must never be deferred — known-evidence anchor |
| 9b — chart_facts fact_category enumeration (204 of 204) | audited / deferred | |
| 9b — ingestion matrix cell 1 (consumed by bo_laksana?) | audited / deferred | |
| 9b — ingestion matrix cell 2 (salience class) | audited / deferred | |
| 9b — ingestion matrix cell 3 (entity attribution) | audited / deferred | |
| 9b — ingestion matrix cell 4 (domain mapping) | audited / deferred | |
| 9b — ingestion matrix cell 5 (signal-emergence count) | audited / deferred | |
| 9b — R-44a re-derivation (current UNATTRIBUTED ratio) | audited / deferred | must never be deferred — known-evidence anchor |
| 9b — R-44b re-derivation (major-tier trivia check) | audited / deferred | must never be deferred — known-evidence anchor |
| 9b — R-42 re-derivation (dosha single-constituent-fact check) | audited / deferred | must never be deferred — known-evidence anchor |
| 9b — KP-4 re-derivation (KP wealth-domain default-mapping check) | audited / deferred | must never be deferred — known-evidence anchor |
| both charts (Abhisek + Abhinandan) covered for every audited row above | audited / deferred | |

Any row left "deferred" without a reason fails plan §8 criterion 4 (Coverage honesty) —
do not leave the reason column blank for a deferred row.

## 8 — Swarm decomposition (plan §12.7, MANDATORY section)

**(a) Conductor + worker pattern.** This lane runs as ONE CONDUCTOR session plus a
worker-swarm of fresh sub-agent sessions, spanning BOTH sub-lanes. The conductor: reads
this brief and the charter once; owns and shards both the 9a node sample (derived from
`asset_promises.jsonl`'s graph-asset slice for identity plus a live DB query for the active-
yoga set) and the 9b fact_category list (derived from `value_families.jsonl`'s `chart_facts`
slice, Section 1.2); spawns one fresh sub-agent worker per shard (9a: one worker per node;
9b: one worker per fact_category), handing each worker ONLY (i) the relevant excerpt of
this brief (charter reference Section 0, plus Section 3 for a 9a worker OR Section 4 for a
9b worker) plus (ii) its single assigned node id or fact_category — never the full audit
context, so each worker has full attention on its narrow slice with zero context decay;
collects each worker's shard trace file on completion; merges results back into
`state/LANE9.md`; performs the cross-sub-lane pattern checks that only the conductor is
positioned to see (R-42 cross-category collapse, G-6 cross-sub-lane agreement, Section 5);
updates the RESUME pointers for both streams; and declares the lane done only when BOTH
streams report 100% shard completion. The conductor never does per-node or per-category
research itself in-band; that is the worker's job. The conductor's job is dispatch, shard
tracking, cross-sub-lane merge, and state regeneration.

**(b) Shard key: two distinct sub-shard streams under one lane conductor.**
- **9a by node sample**: one shard per node, shard id = `graha-<name>` (9 ids: `graha-surya`,
  `graha-chandra`, `graha-mangala`, `graha-budha`, `graha-guru`, `graha-shukra`,
  `graha-shani`, `graha-rahu`, `graha-ketu`), `bhava-<NN>` (12 ids: `bhava-01`..`bhava-12`),
  or `yoga-<signal_id>` (one id per distinct `bodha_msr_signals.signal_id` with
  `signal_type_class=yoga`, resolved at dispatch time against both charts). Each 9a worker
  performs all THREE grading axes (structural, consumption, leverage — Section 3) for its
  one node before returning.
- **9b by fact_category**: one shard per fact_category, shard id = the fact_category string
  itself (e.g., `ashtakavarga_bindu`), 204 ids total, enumerated fresh from
  `value_families.jsonl`'s `chart_facts` slice at dispatch time (Section 1.2). Each 9b
  worker fills all FIVE matrix cells (Section 4) for its one fact_category before returning.
  These are two DISTINCT id-spaces dispatched and tracked independently — a 9a worker never
  touches a 9b shard and vice versa; the conductor runs both streams under the SAME lane
  identity but never merges their shard-id namespaces.

**(c) Concurrency cap + throttling rule.** The conductor runs **5-10 concurrent workers**
at a time PER STREAM (subscription-limit-bounded, per charter §5 / plan §12.7's
"concurrency-capped batches, e.g. 5-10 workers, the conductor throttles to subscription
limits" — the project's standard default cap for per-row/per-node sharded lanes, applied
identically here). The conductor may run 9a and 9b streams CONCURRENTLY with each other
(they touch disjoint tables and disjoint shard-trace filenames, so there is no contention
risk between the two streams) — total concurrent workers across both streams should stay
within a combined cap of roughly 10 unless the conductor has explicit headroom, since the
5-10 figure is a subscription-wide constraint, not a per-stream allowance additive on top
of itself. Concretely: dispatch up to 10 workers total (e.g., 5 from 9a's queue + 5 from
9b's queue, or any split), wait for the batch to report completion, then dispatch the next
batch of pending shards from either queue. If the conductor observes rate-limit signals
(tool-call throttling, session-budget warnings, explicit rate-limit errors) during a batch,
it reduces the next batch's TOTAL concurrency (e.g., from 10 down to 5, or lower) before
continuing — adaptive downward on observed throttling, never adaptive upward beyond 10
without an explicit native/Fable-5 directive to raise it.

**(d) Merge protocol: workers write ONLY their own shard trace file, namespaced by
stream prefix, never a shared file.** Every worker writes to
`/Users/Dev/Vibe-Coding/Apps/Madhav/00_ARCHITECTURE/llm_consumption_audit/state/LANE9/shard-<id>.md`
where `<id>` is stream-prefixed to keep the two shard-id namespaces visually and
mechanically distinct within the one shard directory:
- 9a shard trace files: `state/LANE9/shard-9a-graha-budha.md`,
  `state/LANE9/shard-9a-bhava-07.md`, `state/LANE9/shard-9a-yoga-<signal_id>.md`.
- 9b shard trace files: `state/LANE9/shard-9b-ashtakavarga_bindu.md`,
  `state/LANE9/shard-9b-bhava_bala_lord.md`, etc.
A worker NEVER writes to `state/LANE9.md` directly, NEVER writes to another worker's shard
file, and NEVER writes to the other stream's shard files (a 9a worker never creates a
`shard-9b-*.md` file or vice versa). Each shard trace file records: the shard id, the full
evidence-acquisition trace (calls made, in what order, what was received — per charter §3
finding schema), the grading verdict(s) for its axes/cells (three axes for 9a, five cells
for 9b), any findings logged (with full §3 schema fields), and a completion marker. The
CONDUCTOR ALONE reads all completed shard trace files from BOTH streams, applies their
contents into `state/LANE9.md` (regenerating per Section 6's atomic idempotent discipline),
performs the cross-sub-lane checks (Section 5, Section 8(a)), and appends any genuinely new
findings to `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` and to the machine-readable findings JSON
(plan §7 deliverable 2) after the standard dedupe check (charter §3). No worker ever has
write access to `state/LANE9.md`, the register, or the findings JSON — this is what makes
concurrent workers across two streams safe: they only ever create NEW, uniquely-named,
stream-prefixed files, never edit a file another process (including the other stream's
workers) might also be touching.

**(e) Per-shard RESUME semantics: exact pointer format.** Each shard's completion is
self-evidenced by the EXISTENCE of its stream-prefixed trace file — this is the exact
per-shard RESUME pointer format, identical in kind to Lane 10's precedent but doubled
across two streams:
1. 9a RESUME: list all files matching `state/LANE9/shard-9a-*.md`; extract the set of node
   ids already completed from the filenames present (`graha-*`, `bhava-*`, `yoga-*`);
   cross-check against the full node-sample enumeration (9 + 12 + N active yogas, N
   re-derived fresh from the DB at resume time, since active-yoga membership could in
   principle change between sessions — re-derive, do not trust a stale cached N); any node
   id with neither a shard trace file nor a prior completion record is treated as
   not-yet-dispatched and re-queued.
2. 9b RESUME: list all files matching `state/LANE9/shard-9b-*.md`; extract the set of
   fact_category ids already completed from the filenames present; cross-check against the
   full 204-category enumeration (re-derived fresh from `value_families.jsonl` at resume
   time — the ledger is static so this re-derivation is cheap and removes any doubt); any
   fact_category with no shard trace file is treated as not-yet-dispatched and re-queued.
3. In both streams, the conductor never re-dispatches a worker for an id that already has a
   shard trace file on disk (idempotent skip — trust the filesystem artifact, not memory of
   what was "in flight" before the interruption). With 5-10 concurrent workers per batch,
   later-dispatched shards can complete before earlier ones, so RESUME logic MUST scan the
   full set of existing shard files rather than assume a contiguous prefix or a single
   "last completed id" counter — this holds for BOTH streams independently, and the
   `state/LANE9.md` summary fields (`last_node_id_done`, `last_fact_category_done`) are
   informational only, never the authoritative RESUME source (the shard directory listing
   is authoritative, per Section 6).

## 9 — Deliverable spec

Per plan §7 (Deliverables, lines 307-323), this lane is responsible for **deliverable 7**:

> 7. The **L1→MSR ingestion matrix** (Lane 9b) and the **graph-leverage report** (Lane 9a).

Concretely, this brief's execution produces:
- **The L1→MSR ingestion matrix** (9b): a table of 204 rows (one per fact_category) × 5
  columns (consumed-by-bo_laksana? / salience class / entity attribution / domain mapping /
  signal-emergence count) plus the qualitative design-correctness verdict (Section 4), for
  BOTH charts in scope, with every cell's evidence trace recoverable from the shard trace
  files (Section 8(d)).
- **The graph-leverage report** (9a): one dossier per sampled node (9 grahas + 12 bhavas +
  N active yogas) recording all THREE grading axes (Section 3) with evidence traces, plus a
  chart-level rollup answering the protocol's three headline questions verbatim: is the
  neighborhood structurally complete and correct? Is it consumable in ≤2 calls, usable
  form? Is it actually leveraged by any serving instrument today?

Both outputs feed directly into the report (plan §7 deliverable 1) and the machine-readable
findings JSON (deliverable 2) — this brief's conductor is responsible for ensuring every
finding logged during 9a/9b work carries the full §3 finding-schema fields so the
consolidation session never needs to re-derive them.

**Exact output locations**: the merged matrix and dossier content live in `state/LANE9.md`
(summary) plus the full shard trace files under `state/LANE9/shard-9a-*.md` and
`state/LANE9/shard-9b-*.md` (detail — these ARE deliverable 7's substrate, analogous to how
Lane 10's ledger file IS its own deliverable's substrate); any genuinely new register rows
go to `MARSYS_DEFECT_GAP_REGISTER_v2_0.md` per the standard dedupe discipline (charter §3).

---

*End of LANE9_SUBSTRATE_INTEGRITY.md v1.0. This brief cites `LLM_CONSUMPTION_AUDIT_CHARTER`
v1.0 for all doctrine/taxonomy/finding-schema/satisfaction-criteria/rubric content and does
not duplicate it. Its own scope is exhaustively self-contained: dual ledger scope
(Section 1), protocol verbatim (Section 2), 9a three-axis extension (Section 3), 9b
five-cell extension (Section 4), type-specimen handling (Section 5), checkpoint/RESUME
(Section 6), coverage-declaration template (Section 7), swarm decomposition with two
sub-shard streams (Section 8), and deliverable spec (Section 9).*
