---
artifact: LLM_CONSUMPTION_AUDIT_PLAN_v1_0
type: PLAN (pre-brief master plan; the CLAUDECODE_BRIEF derives from this document)
version: 1.0
status: DRAFT — under native review (Cowork session 2026-07-11)
authored_by: Cowork (Fable 5) + native, 2026-07-11
program: LLM Consumption Audit → Fable 5 planning → multi-layer remediation → Abhinandan rebuild
executor_model: Opus (Claude Code session)
planning_model: Fable 5 (Cowork session, post-report)
charts_in_scope:
  - 482012f1-710e-4a25-994a-93821f5871aa  # Abhisek (native)
  - 1c826d5a-41cb-4450-b4dc-59d440e5f75a  # Abhinandan
changelog:
  - v1.4 (2026-07-12): Cowork review-gate corrections — §11 marked CLOSED (Exceptions
    §3.5); Appendix C count corrected 76→82 (Exceptions §3.6); "§J" citation clarified to
    CLAUDE.md §J (Exceptions §3.7). Gate record:
    00_ARCHITECTURE/llm_consumption_audit/GATE_RATIFICATION_v1_0.md.
  - v1.3 (2026-07-11): native review round 3 — §12.7 swarm execution model: parallel
    sub-agent-driven implementation everywhere possible, sequential only where dependency
    edges force it; explicit execution DAG; sharded ledgers + merge discipline; per-lane
    conductor+worker-swarm pattern; foundry Phase 1 parallelized.
  - v1.2 (2026-07-11): native review round 2 — (a) new Lane 10: promise-vs-delivery audit
    (every asset's declared promise traced to where it falls short — data plane or
    retrieval plane); (b) new §12: execution architecture (federated briefs, ledger-driven
    execution, AUDIT_STATE, two-way traceability + adversarial review, Brief Foundry
    process); (c) deliverables + Appendix A extended.
  - v1.1 (2026-07-11): native review round 1 — (a) examples-are-illustrative doctrine
    (§2.1); (b) new Lane 9: L2 substrate integrity (CGM graph leverage + MSR ingestion
    coverage); (c) Lane 1 upgraded to a full concept-and-value census incl. services
    sub-census; (d) P-12 demand-side retrieval planner + capability map + tracker;
    (e) P-13 services reachability; Appendix A extended.
  - v1.0 (2026-07-11): first consolidation of the full Cowork discussion — session findings
    (R-37..R-48), native observations, the seven original lanes + Lane 8 depth audit,
    the acharya-gap analysis (10 gaps), 9-class failure taxonomy, satisfaction criteria.
---

# LLM CONSUMPTION AUDIT — CONSOLIDATED MASTER PLAN

## §0 — Program context: why prior iterations plateaued

Three to four prior elevation campaigns (R5 → R5.1 → R5.2 → R5.3; TAP audits) were
**fix-oriented and tool-side**: run a frozen battery of known questions, grade against a
gate, patch failures, re-grade. That finds regressions in known territory. It structurally
cannot find what this Cowork session found in three conversations of *real consumption*
(bo_anveshana serving noise R-37; kala_activation serving nothing R-45; receipt dishonesty
R-38/R-41), and audits that verified "data exists in the table" kept passing things that
die between the table and the LLM.

**The correction (native directive, 2026-07-11): the audit lens is the perception of the
LLM receiving — not the presence of data in a layer.** If data exists but is not retrieved
accurately, consistently, and in usable form, there is no meaning to having the data. The
retrieval system is co-equal with the data plane.

## §1 — Objective and hard boundary

- The session produces an **AUDIT REPORT ONLY**. Zero fixes. Zero code changes. Zero data
  writes except: the report, the machine-readable findings file, register appends, and the
  retrievability matrices.
- Rationale: every prior session that could fix things collapsed into patching the first
  ten findings instead of finding the hundredth.
- The report feeds a **Fable 5 planning session** which designs the remediation across ALL
  layers — data plane, data layers (L0–L5 writers), retrieval/serving layer, MCP layer,
  and any **new supporting layers** the gaps demand (synthesis instrument, doctrine layer,
  gochara composition, narration vocabulary). Architecture changes, tweaks, and everything
  between are all in scope for the plan — the audit does not prejudge remediation shape.
- After remediation: ONE Abhinandan rebuild as the verification event (not before — most
  known findings are code defects a rebuild would reproduce identically). Then re-verify
  with the frozen battery AND the new question matrix.

## §2 — Audit doctrine (the constitution)

A **gap** is anything that prevents the consuming LLM from receiving **correct, complete,
consistent, usable, and proportionate** evidence over the wire. Data that exists but does
not arrive is absent. Data that arrives wrong, or twice contradicting itself, or as 300
unranked duplicates, or as raw IDs with no text, or as an un-budgeted 181KB dump, is a gap
of equal standing.

**Completeness has two axes (native directive):**
- **Width** — the span of data points relevant to a question. If ~20 relevant data points
  exist that the LLM never receives, the audit must find each and root-cause WHY it is not
  received.
- **Depth** — the full dossier of any entity that enters a synthesis (the Mercury
  standard, §5 Lane 8): strength, avastha, yoga/dosha membership, dispositor chain,
  varga-wise placement, temporal presence (MD/AD/PD), structural×temporal convergence
  past/near-future, bhava-sandhi/cusp flavor, combustion, and every other facet the system
  holds. Considering Mercury without its dossier is not synthesis.

### §2.1 — Examples are illustrative, never limiting (native directive, review round 1)

Every example given in this plan — the Mercury facet list, the "~20 missing data points",
the draft question themes — is ILLUSTRATIVE. The audit derives the full factor space from
three closed-loop sources and must never treat a native-supplied example list as the
boundary: (1) the classical canon (shastra concept inventory — every concept an acharya
could weigh, whether or not the system implements it); (2) the system's own asset
inventory (every asset × every fact_category × every value each asset emits, enumerated
from the DB and CAPABILITY_MANIFEST, not from memory); (3) the L2/L3 derived surfaces
(signals, graph, convergence, windows). Where (1) exceeds (2), that delta is itself a
finding (UNREACHABLE-by-nonexistence). Where (2) exceeds what any tool serves, that is
UNREACHABLE. The completeness test is against the union, never against the examples.

## §3 — Fixed decisions (native rulings, 2026-07-11)

| Decision | Ruling |
|---|---|
| Chart set | The two charts only (Abhisek 482012f1, Abhinandan 1c826d5a). No other charts this round. Absent LEL on a chart is acceptable — uncalibrated/structural serving IS the audited surface; calibration absence is by design (L5 STRUCTURAL mode). |
| DB access | GRANTED, read-only (SELECT only), for Lane 5 wire-fidelity and Lane 8 facet enumeration. All other lanes consume the public MCP channel exclusively. |
| Question list (Lane 2) | PENDING — to be debated extensively native↔Fable 5 BEFORE the session. The brief ships with Lane 2 gated on `NATIVE_QUESTION_LIST_APPROVED`. |
| Budget | OPEN — no call/time cap, as long as value is added. Checkpointing mandatory (§6). |
| Executor | Opus via Claude Code, on the native's subscription (conductor + ALL sub-agents; no separate API billing). Fable 5 is EXCLUDED from execution — it serves only in Cowork for planning, the traceability review gate, and post-report remediation planning. All judgment rubrics must be written into the brief verbatim (no executor taste). Lane 2 runs conductor + fresh-sub-agent-per-question (§12); ~300 traces spread across sessions within subscription usage windows, resuming via AUDIT_STATE. Legacy 38-item battery re-run (regression baseline) keeps its existing Gemini/DeepSeek grading keys. |
| Fix-forbidden | Absolute. Findings only. |

## §4 — Failure-class taxonomy (every finding gets exactly one primary class)

1. **UNREACHABLE** — exists in a table, no tool serves it (KP-3, mrityu-bhaga R-47 class).
2. **WRONG** — value served ≠ L1 truth (R-43 dignity class).
3. **INCONSISTENT** — two tools serve the same quantity differently (D-1/G-7/R-43 class).
4. **EMPTY SHELL** — tool advertises an analysis stage that returns nothing (R-39/R-40/R-45 class).
5. **DISHONEST SELF-DESCRIPTION** — receipts/counters/flags contradict the payload (R-38/R-41 class).
6. **UNUSABLE FORM** — arrives but cannot be synthesized: IDs without text, truncated narration, un-budgeted dumps (R-40/R-30/R-44c class).
7. **DROWNED** — correct data buried under duplication walls or trivia ranked as chart-defining (R-37/R-44a/b class).
8. **UN-SYNTHESIZABLE AT SCALE** — the question needs N-hundred factors and no path composes them (R-48/C-6 class).
9. **UNGOVERNED JUDGMENT** — the executor LLM had to improvise where the system should have governed: method/krama choice, evidence adjudication, question decomposition, taxonomy→life-language translation (§10 gaps 1/3/9/10). Logged every single time it happens; these findings are the requirements spec for the doctrine/method layers.

Class determines suspected remediation layer — that is what makes the report plannable.

## §5 — Work plan: Item 0 + eight lanes

### Item 0 (sequenced FIRST, before all lanes): R-45 triage
Is `kala_activation` / `kala_activation_predicates` empty for both charts (ka_* writer
no-op during build) or populated (serving-path query bug)? Single SELECT + one MCP call.
Decides whether the planned rebuild is even a meaningful verification event, and is the
suspected single root cause behind R-39 (judgment_query timing_hooks empty) and R-40
(assess_wealth activations=0). Also covers the native's named concern: the
temporal×spatial convergence / activation-points asset — the first-built temporal engine
in Kāla — has never worked in consumption.

### Lane 1 — Full concept-and-value census (upgraded per native review round 1)
Three nested censuses; nothing stays untested at ANY of the three grains:

**1a. Tool census (first-contact protocol).** Every MCP tool (~150), called ≥1× per chart
with realistic arguments. Record: response shape, byte size, honesty markers,
synthesizability-as-received (rubric in brief). Base rate observed so far: assets FAIL on
first contact (bo_anveshana R-37, kala_activation R-45 — both failed the first time anyone
consumed them).

**1b. Value census (per-asset, per-value retrievability).** The native directive: "every
single asset we have, every single value each asset provides, across the layers — is it
being successfully retrieved appropriately by the LLM?" Method: enumerate from the DB
(access granted) the complete value inventory — every fact_category × fact_key in
chart_facts; every column/row family in chart_dashas, chart_divisionals, bodha_*, kala_*,
phala_*, mimamsa_* tables; every L0 catalog family — then for EACH value family attempt
wire retrieval and grade it against §4. Output: the master **Concept×Retrievability
matrix** (deliverable 6), the audit's most important artifact. Sampling within a family is
permitted only where the family is homogeneous (identical serving path); the family list
itself is exhaustive, never sampled.

**1c. Services census (real-time computation reachability).** Every SERVICE (as opposed to
stored-data asset) — ga_chart_service, natal-positions compute, ephemeris/retrograde/
transit services, panchanga service, muhurta finder, tajaka/varshaphal, dasha services
across all 7 systems (Vimshottari/Yogini/Ashtottari/Chara/Narayana/Shoola/Kalachakra),
prashna — tested for: can the consuming LLM reach it, invoke it with a real computed-on-
demand request (data NOT in the data layer), and receive a usable result? (Native
directive: values that must be calculated at real time are as much a part of completeness
as stored values.)

**Extensions folded in:** (a) L5 negative-knowledge slots consumption test (§9 P-2);
(b) the FULL outcome loop live: mimamsa_outcome_record → re-retrieve → does it reach the
next orientation context (§9 P-6); (c) dissent surfaces (synth_tail_divergence_get)
consumability (§9 P-4); (d) recall_session / session-memory round-trip.

### Lane 2 — Question-first coverage matrix (GATED on native question list)
~60–80 acharya question types (marriage timing, progeny, health crisis windows,
litigation, property, foreign settlement, muhurta, remedial priority, career pivots,
wealth magnitude, death-of-parent timing, spiritual inflection, …) — list to be fixed in
the native↔Fable 5 debate. Each attempted end-to-end exactly as the consuming LLM would.
Graded NOT "did tools return rows" but "did the retrievable evidence suffice to answer at
acharya grade" (CLAUDE.md §J, the acharya-grade quality standard — dangling citation
clarified at gate v1.4 per foundry Exceptions §3.7; operationalized by CHARTER §7.3).
Every chain break is a finding. This is the unknown-unknowns lane —
questions no tool was designed for. Timing questions deliberately include gochara
composition (dasha × transit × natal, double-transit) to expose §10 gap 8.

### Lane 3 — Cross-tool consistency sweep
Fixed quantity set — dignity, house, sign, nakshatra+pada, shadbala, dasha-lord
denormalized metadata — per graha × per chart, pulled through EVERY path that serves it
(chart_facts, dashas, judgment_query, graha_portrait, signals, snapshot, orientation).
Any diff is a finding. Mechanical, scriptable, exhaustive. (R-43 proved this class is
still live post-D-1/G-7 "FIXED" status — fixed rows regress.)

### Lane 4 — Receipt-honesty sweep
Every self-descriptive claim any tool makes — receipts, verdict counters, coverage blocks,
provenance notes, "✓" marks, judgment_flags — checked against its own payload in the same
response. (R-38: varga_confirmed "D10✓" with zero varga rows; R-41: verdict says 0 fired
while content serves 32 rows.) **Extension:** fragility/confidence metadata presence check
— which serving paths carry ayanamsha_fragility, rectification-confidence, birth-time
sensitivity at all (§10 gap 7).

### Lane 5 — Wire-fidelity diff (the DB-access lane)
For sampled fact families: read-only comparison of table contents vs what arrives over the
wire. Fields dropped in pivots, subjects merged across categories (KP-6), trims cutting
meaning mid-narration (R-32), budget ceilings silently discarding decisive rows. Direct
implementation of the native's "data exists but is not retrieved" concern.

### Lane 6 — Ranking-quality audit
For each ranked surface (orientation top-signals, domain readings, signals, discoveries,
convergence): is the top-K what an acharya would put first? Measured: duplication rate,
identical-score walls, descriptive-trivia share, family-collapse coverage, UNATTRIBUTED
share (R-44: 298/300 unattributed; R-37: top-30 of discoveries = 1 unique finding).
**Extension:** normative-bands check — strength values must arrive WITH their classical
reference thresholds (shadbala required-minimum rupas, vimsopaka bands, ishta/kashta
framing); a bare "7.96 rupas" fails the rubric (§10 gap 5).

### Lane 7 — Large-N synthesis ceiling probe
Ten deliberately heavy questions (the wealth-magnitude question is the template). Document
precisely where composition fails: what the LLM needed, what it could actually get, in how
many calls, what got trimmed, where flat top-K walls replaced discrimination. This lane
produces the REQUIREMENTS SPEC for the synthesis capability (R-48) that the planning
session will design — including whether volume is handled in one pass or incrementally,
per the native's framing: either is acceptable, but a strong system for high-volume
multi-factor synthesis must exist.

### Lane 8 — Entity-dossier depth audit (the Mercury standard; native directive)
For each of 9 grahas + Lagna × 2 charts = 20 dossiers: FIRST enumerate from the data plane
(DB) every facet the system holds about the entity; THEN attempt to retrieve each facet
over the MCP wire as a consuming LLM would. Output: per-entity **retrievability matrix** —
facet × {held in DB? | reachable via wire? | reachable in ≤2 calls? | arrives in usable
form?}. Every held-but-not-received facet is root-caused into §4 classes ("WHY is the LLM
not receiving this" is the lane's entire question).

Facet checklist: **superseded by Appendix B (60-facet floor, v2, native-directed maximal
extent)** — the 10-group draft below is retained for audit trail only:
1. Position — sign, house, degree, **bhava-sandhi / cusp proximity** (e.g. Mercury on the
   9th/10th cusp carries both flavors), nakshatra + pada + their lords.
2. Strength — shadbala six-fold breakdown, ishta/kashta, vimsopaka, bhava bala of owned houses.
3. State — avastha sets (baladi / jagradadi / deepta-adi), **combustion** (e.g. Mercury
   with Sun — combust or not), retrogression, graha yuddha, graha sandhi.
4. Varga chain — D1→D60 dignity per varga, vargottama, own-varga counts, operative-varga condition.
5. Relational — conjunctions, aspects cast/received, **dispositor chain position** (who
   disposits it, what it disposits, chain terminus).
6. Participation — **every yoga it constitutes, every dosha it constitutes**, karaka roles
   (naisargika + Jaimini chara), arudha involvement.
7. Sensitive degrees — mrityu-bhaga, pushkara bhaga/navamsha, gandanta proximity (R-47:
   currently computed nowhere per graha).
8. Temporal — is it current MD/AD/PD lord; its next period windows; current transit
   position; **structural×temporal convergence, recent past + near future** (R-45 dependency).
9. Contextual — lordships and condition of owned bhavas; placement as seen from Moon, Sun,
   and karaka lagnas.
10. Derived — KP star/sub/sub-sub roles, tara bala, its L2 signal family, its CGM graph
    neighborhood.

### Lane 9 — L2 substrate integrity: the graph and the MSR funnel (native review round 1)

The two upstream engines everything else consumes — if either is broken, downstream lanes
measure symptoms of a single cause. Both get first-class audits:

**9a. CGM graph leverage audit.** The graph is one of the strongest assets: for any node
it should yield the associated relevant data points a synthesis must consider. Audit:
(i) structural — for a sample of nodes (each graha, key bhavas, active yogas), traverse
the graph and grade the neighborhood for completeness (does Mercury's node reach its
dispositor chain, its yogas, its bhava lords, its temporal hooks?) and correctness (edges
cite L1 fact_ids per B.3); (ii) consumption — can the LLM actually retrieve and use a
neighborhood in ≤2 calls, in usable form? (iii) leverage — does ANY serving instrument
compose graph context into answers today, or is the graph a parked database? Known
evidence: v2.2 chain-integrity rows; G-6 (no multi-hop chain signal class in MSR);
zero graph-derived context received in the 2026-07-11 consumption session.

**9b. MSR ingestion coverage + fidelity audit.** MSR is the funnel through which Gaṇita
reaches every downstream consumer. Audit the funnel itself: build the **L1→MSR ingestion
matrix** — every L1 fact_category × {consumed by bo_laksana? at what salience class? with
what entity attribution? with what domain mapping? emerging as how many signals?}. Grade
each mapping for design correctness from the consumer's perspective. Known evidence of
indiscriminate ingestion: 298/300 top candidates UNATTRIBUTED (R-44a); descriptive trivia
at "major" tier (R-44b); all doshas citing one constituent fact (R-42); KP categories
domain-mapped to a default so they can never surface in wealth queries (KP-4). The lane
answers the native's question directly: is MSR's read of the Gaṇita layer designed
correctly, and is it being leveraged correctly for the LLM?

### Lane 10 — Promise-vs-delivery audit (native review round 2)

Every asset across the five layers was built against a DECLARED PROMISE — the value it
committed to fulfill, recorded in its build brief (00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_
<asset>_v*.md), the asset_registry row, the layer handoff/closure documents, and the MCP
tool description that fronts it. The audit compiles, per asset, a **promise ledger**:
(1) what was promised — verbatim, with source citation; (2) what the consuming LLM
actually receives today — from the other lanes' evidence; (3) where the shortfall sits —
data plane (never computed/written), retrieval plane (computed but unreachable/unusable),
or ranking/form (reachable but drowned/mangled); (4) the finding refs that explain it.
Grading is against the asset's OWN declared intent, not a generic rubric — an asset that
delivers exactly its promise passes even if modest; an asset whose promise is served
nowhere fails even if its tables are full (bo_anveshana R-37 and kala_activation R-45 are
the type specimens: both promised "acharya-grade discoveries" / "activation points" and
both fail at the consumption plane). Output: the **Promise×Delivery ledger** for all
~55 assets (9 ga_* + 14 bo_* + 12 ka_* + 9 ph_* + 12 mi_* + services), the planning
session's asset-level prioritization input.

## §6 — Cross-lane protocols

- **Finding discipline:** every finding carries — reproducible call (exact tool + args),
  verbatim evidence excerpt, primary failure class (§4), severity, **suspected layer**
  (data plane / L-writer / serving-query / envelope-trim / ranking / MCP contract /
  architecture), dedupe check against the existing ~200 register rows (incl. R-37..R-48).
  Genuinely new rows appended to MARSYS_DEFECT_GAP_REGISTER_v2_0.md.
- **Improvisation log (class 9):** the executor logs EVERY act of ungoverned judgment it
  performs while consuming — method/krama choice, conflict adjudication, silent question
  decomposition, taxonomy→life-language translation. First-class findings.
- **Checkpointing:** each lane writes findings incrementally to the report file; a session
  interruption never loses completed work; a RESUME protocol lets a follow-on session
  continue mid-lane. Open budget makes this mandatory, not optional.
- **Known-findings anchor set:** R-37..R-48 (this session) serve as calibration anchors —
  the audit MUST independently rediscover them via its lanes; any it misses indicates a
  lane-coverage hole (audit-of-the-audit).

## §7 — Deliverables

1. `LLM_CONSUMPTION_AUDIT_v1_0.md` — the report: per-lane findings, §4 class distribution,
   per-lane coverage self-declaration (TAP-9 style: every surface audited or explicitly
   deferred with reason).
2. Machine-readable findings file (JSON): one record per finding with all §6 fields — the
   direct input to the Fable 5 planning session (cluster/sort/prioritize without re-reading prose).
3. Register appends (new rows only, deduped).
4. 20 entity retrievability matrices (Lane 8).
5. The question-coverage matrix (Lane 2) — retained as a standing asset; it becomes the
   future acceptance surface, superseding the 38-item battery's role.
6. The **Concept×Retrievability matrix** (Lane 1b) — every asset × every value family ×
   retrievability grade; doubles as the seed data for the P-12 capability map.
7. The **L1→MSR ingestion matrix** (Lane 9b) and the **graph-leverage report** (Lane 9a).
8. Lane 2 evidence-plans + acquisition logs (the P-12 requirements corpus).
9. The **Promise×Delivery ledger** (Lane 10) — per asset: promise (cited) → delivered →
   shortfall layer → finding refs.

## §8 — Satisfaction criteria (all five must hold; "complete" ≠ "no gaps remain" — it
means NO GAP REMAINS FOR LACK OF LOOKING)

1. **Census completeness** — 100% of tools (1a), 100% of enumerated value families (1b),
   and 100% of services (1c) have retrievability records on both charts; the value-family
   enumeration itself is DB-derived and exhaustive, never from memory.
2. **Question-width completeness** — 100% of the approved question list traced end-to-end
   with an evidence-sufficiency verdict; every missing-but-relevant data point root-caused.
3. **Depth completeness** — 20/20 entity dossiers with full facet matrices; every
   held-but-not-received facet root-caused.
4. **Coverage honesty** — self-declaration lists every known surface as audited or
   explicitly deferred with reason.
5. **Plannability** — every finding machine-readable with class + suspected layer +
   reproducible evidence; the planning session never needs to re-derive.

## §9 — Planning-phase register (NOT audit items — target-architecture gaps the report
must carry forward verbatim to the Fable 5 planning session)

From the acharya-chair analysis (Cowork 2026-07-11). The audit measures their symptoms
(via class 9 logs and lane extensions); their remediation is design work:

| # | Gap | Essence | Audit hook |
|---|---|---|---|
| P-1 | **Vidhi / method layer** | No served reading procedure per question class → readings are irreproducible across sessions | Lane 2 variance + class-9 logs |
| P-2 | **Negative knowledge** | Absence-with-evidence not first-class retrievable ("no dhana yoga, and here is the near-miss distance") | Lane 1 extension (L5 slots) |
| P-3 | **Adjudication doctrine** | No served conflict-resolution canon (tradition precedence, varga weights) → LLM's priors wearing the system's data; the single largest threat to the calibration mission | Class-9 logs |
| P-4 | **Adversarial retrieval** | No claim-conditioned counter-evidence instrument (cross-examine own conclusions) | Lane 1 dissent-surface test |
| P-5 | **Normative bands** | Magnitude questions lack served scales (value-vs-classical-threshold) | Lane 6/8 extension |
| P-6 | **Longitudinal loop** | Outcome recording exists but consumption of it (next-session context) unproven; calibration mission dies without it | Lane 1 outcome-loop test |
| P-7 | **Fragility propagation** | Birth-time sensitivity / rectification confidence / ayanamsha fragility not attached to served claims | Lane 4 extension |
| P-8 | **Gochara composition** | No dasha × transit × natal composition instrument (double-transit etc.) | Lane 2 timing questions |
| P-9 | **Narration vocabulary** | Taxonomy→life-language translation ungoverned, uncited, unversioned | Class-9 logs |
| P-10 | **Intent decomposition contract** | Compound questions arrive undecomposed; intent_classify returns a class, not an evidence contract | Lane 2 protocol |
| P-11 | **Large-N synthesis instrument** | R-48: staged retrieval-with-aggregation over L2 pre-computed surfaces (convergence/CDLM/CGM), narrative with derivation ledger; one-pass or incremental — native accepts either, but the capability must exist | Lane 7 (produces its requirements spec) |
| P-12 | **Demand-side retrieval planner + capability map + acquisition tracker** (native, review round 1 — flagship capability). The LLM must NOT be driven by whatever data arrives (supply-side). Per question it generates an a-priori extensive evidence plan from the shastra — narrow question → narrow but comprehensive item list; broad question → wide comprehensive list — then retrieves against the plan, TRACKS received-vs-needed, and keeps seeking through tools/services until each item is fetched or honestly exhausted. Anything extra the tools volunteer is bonus, never the frame. Requires: (a) a machine-readable **capability map** — concept → which tool/service serves it (does not exist today; MCP_USAGE_GUIDE is prose, not keyed by concept); (b) an in-conversation **acquisition tracker** (does not exist); (c) the per-question evidence-plan generator (P-10's contract is its input). Ensures every essential factor — critical or tail — enters the synthesis | Lane 2 executor RUNS in exactly this mode manually: writes the evidence plan BEFORE any call, tracks acquisition, and logs every place the capability map knowledge was missing/wrong and every plan item no tool could satisfy. Lane 1b's Concept×Retrievability matrix IS the capability map's seed data |
| P-13 | **Services as first-class evidence sources** — real-time computation (multi-system dashas, transits, panchanga, muhurta, varshaphal, prashna) must be reachable and composable by the consuming LLM for values not in the data layer | Lane 1c services census |

## §10 — Post-audit program flow

1. Audit report (this plan's session, Opus) →
2. **Fable 5 planning session**: cluster findings by root cause; decide per cluster —
   data-plane fix / writer fix / serving fix / MCP-contract fix / new supporting layer;
   sequence into remediation brief(s) →
3. Fix wave(s) (Claude Code) →
4. ONE Abhinandan rebuild (verification event; also clears stale-state) →
5. Re-verification: frozen battery + new question matrix + Lane-8 matrices re-run →
6. Register reconciliation + CURRENT_STATE update.

## §12 — Execution architecture (anti-dilution / anti-context-decay; binding on the Brief Foundry)

At this scale the failure mode shifts from plan gaps to EXECUTION gaps — an executor
holding nine lanes in one decaying context silently thins the later lanes. Completeness is
made STRUCTURAL, never attentional:

1. **Federated briefs** — one master charter (doctrine §2/§2.1, taxonomy §4, finding
   schema §6, satisfaction criteria §8, RESUME protocol) + one self-contained child brief
   per lane, each executable in a FRESH session. No session ever holds the whole audit.
2. **Ledger-driven execution** — before any auditing, a foundry step enumerates ground
   truth into machine-checkable ledger files: tool list (manifest), value-family inventory
   (DB: every fact_category × fact_key per table), services list, question list, facet
   checklist, asset-promise list. Lanes execute AGAINST their ledger, marking rows;
   completeness becomes a count query, not a judgment.
3. **AUDIT_STATE.md** — standing state file: lane × status × rows-done/rows-total ×
   findings-count, updated atomically at every checkpoint (CURRENT_STATE pattern). Any
   fresh/resumed session reads it and knows exactly where the audit stands; no lane can be
   silently skipped because its zero-count is visible.
4. **Two-way traceability + adversarial review** — the Brief Foundry emits a plan→brief
   coverage matrix (every plan section/directive/appendix row → implementing brief
   section; unmapped = build incomplete, mechanically) and the inverse brief→plan check
   (catches inventions). A SEPARATE fresh session (or Fable 5 in Cowork) red-teams the
   diff for SOFTENING — dilution is usually not omission but vagueness. Chain verified
   end-to-end: native directives → plan (Appendix A) → briefs (coverage matrix).
5. **Process order** — (i) native+Fable 5 close question list + facet checklist (ledger
   inputs); (ii) Brief Foundry session (Opus, open time): builds ledgers from DB/manifest
   (a grounding dry-run that catches enumeration surprises early), writes charter + child
   briefs + AUDIT_STATE skeleton + traceability matrix; BUILDS ONLY, AUDITS NOTHING;
   (iii) review gate: traceability matrix verified line-by-line in Cowork (Fable 5 +
   native) before execution; (iv) execution: fresh session per lane (mechanical lanes
   1a/1c/3/4 may parallelize as sub-agents; judgment-heavy lanes 2/7/8 get dedicated
   sessions), each checkpointing to AUDIT_STATE; (v) consolidation session: merge, dedupe
   vs register, run the calibration-anchor test (R-37..R-48 must be independently
   rediscovered; any miss = lane hole), emit report + findings JSON.
6. **Guarantee principle** — completeness never rests on the builder's or executor's
   diligence; it rests on ledgers, traceability matrices, and review gates. Diligence is
   hoped for; structure is verified.

7. **Swarm execution model (native directive, review round 3) — parallel by default,
   sequential only where a dependency edge forces it; sub-agent-driven throughout.**

   **Pattern:** every phase and lane runs as a CONDUCTOR + WORKER-SWARM. The conductor
   owns the lane's ledger, shards it, spawns fresh sub-agents per shard (each worker gets
   only the charter excerpt + its shard — full attention, zero context decay), collects
   trace files, merges, updates state. Workers never write shared files; each writes its
   own shard trace, the conductor merges — no write contention.

   **Execution DAG (edges are the ONLY sequencing; everything else is parallel):**
   ```
   FOUNDRY:  [8 ledger builders — PARALLEL sub-agents]
                └→ [charter + 11 briefs — PARALLEL per brief once its ledger lands]
                     └→ [traceability matrix + anti-softening diff]  (sequential tail)
   REVIEW GATE (Cowork; sequential by nature)
   EXECUTION: Item-0 ∥ Lane1a ∥ Lane1b ∥ Lane1c ∥ Lane2 ∥ Lane3 ∥ Lane4 ∥ Lane5 ∥
              Lane6 ∥ Lane7 ∥ Lane8 ∥ Lane9a ∥ Lane9b ∥ Lane10-compile
                — ALL PARALLEL, each a conductor+swarm; Item-0's result is broadcast to
                  Lanes 2/7 mid-flight (timing verdicts annotated, not blocked)
              Lane10-grade  ← the ONE hard sequential edge: promise-vs-DELIVERY grading
                  consumes the other lanes' evidence, so its grading pass runs at
                  consolidation (its promise-ledger COMPILATION runs parallel, per asset)
   CONSOLIDATION (sequential): merge → dedupe vs register → calibration-anchor test
              (R-37..R-48 rediscovery) → Lane10-grade → report + findings JSON
   ```

   **Intra-lane sharding:** Lane 1a by tool batches; 1b by table × fact_category; 1c by
   service; Lane 2 by question rows (concurrency-capped batches, e.g. 5–10 workers, the
   conductor throttles to subscription limits); Lane 3 by graha; Lane 4 by tool; Lane 5 by
   fact family; Lane 6 by ranked surface; Lane 7 one worker per heavy question; Lane 8 one
   worker per dossier (20 workers); Lane 9a by node sample, 9b by fact_category; Lane 10
   compile by asset.

   **State discipline under parallelism:** AUDIT_STATE.md becomes an index over per-lane
   state shards (`state/LANE<k>.md`), each owned exclusively by its lane conductor;
   the top-level index is regenerated by whichever conductor checkpoints (counts only,
   derived from shards — regeneration is idempotent, so concurrent regeneration is safe).
   Verifier sampling (Lane 2's ~15% re-grade) runs as parallel verifier workers.

   **Wall-clock consequence:** with worker swarms, the audit compresses from a chain of
   long sessions to a few conductor sessions bounded mainly by subscription usage windows;
   RESUME semantics unchanged (any conductor resumes from its shard).

## §11 — Open items — ALL CLOSED (2026-07-11; retained for audit trail; flagged stale by
foundry traceability Exceptions §3.5, corrected at the Cowork review gate v1.4)

1. **Lane 2 question list** — CLOSED: debated and approved same session; frozen as
   Appendix C; ledger `questions.jsonl`.
2. **Lane 8 facet checklist** — CLOSED: Appendix B ratified as the 60-group floor.
3. Brief mechanics — CLOSED: foundry executed 2026-07-11/12; see
   `00_ARCHITECTURE/llm_consumption_audit/`.

## Appendix A — Traceability: every native observation → plan element

| Native observation (session 2026-07-11) | Where it lands |
|---|---|
| Retrieval is co-equal with data; audit from the LLM-receiving lens | §0, §2 doctrine, Lanes 3–6 |
| Discovery asset (temporal×spatial convergence, activation points, Kāla temporal engine) untested/broken | Item 0 (R-45 triage); Lane 1 |
| NB/Viparita-Raja yogas absent from responses | Known Section-1 register gap; Lane 2 evidence-sufficiency will re-surface with priority; P-2 near-miss framing |
| D9/D10/other vargas not given D1-equal significance | R-46; Lane 8 facet 4; P-3 (varga weights in doctrine) |
| Mrityu-bhaga and related concepts never surfaced | R-47; Lane 8 facet 7 |
| Inability to engage large volumes / deep multi-factor synthesis; one-go or incremental both acceptable | R-48; Lane 7; P-11 |
| ~20 relevant data points not received → not synthesized; investigate WHY per point | §2 width; Lane 2 protocol; §8 criterion 2 |
| Depth: Mercury standard (strength, avastha, yogas, doshas, dispositor chain, vargas, MD/AD presence, convergence, cusp, combustion, "twenty other") | §2 depth; Lane 8 entire; §8 criterion 3 |
| Two charts only; missing LEL/calibration acceptable | §3 |
| DB access granted | §3; Lanes 5, 8 |
| Question list: extensive debate, hold | §3; §11 |
| Open budget; Opus executor; Fable 5 builds the plan from the report | §3; §10 |
| Multi-layer remediation scope (data plane → data layers → retrieval → MCP → new supporting layers) | §1; §10 step 2 |
| Prior iterations unsatisfactory; this time take time, get close to perfection | §0; §8 (operational satisfaction) |
| Examples/factors given are illustrative, never the limit — derive the full factor space | §2.1 doctrine; Lane 1b; Lane 8 checklist marked draft |
| Is the Bodha graph (strongest association asset) leveraged efficiently? | Lane 9a |
| Is MSR's read of Gaṇita (via ga_structural etc.) designed and leveraged correctly for the LLM? | Lane 9b |
| Every astrological concept / every asset / every value each asset provides must be checked for LLM retrievability — no misses | Lane 1b value census; §2.1 closed-loop derivation; deliverable 6 |
| LLM must plan its evidence demand a priori (narrow→comprehensive, broad→wide), track received-vs-needed, keep seeking; supply extras are bonus | P-12; Lane 2 execution mode |
| Does the LLM know which tools/services provide which data? Does it have a tracker? | P-12 capability map + tracker; Lane 1b seeds the map |
| Are services (dasha assets, real-time computation) reachable and used for values not in the data layer? | Lane 1c; P-13 |
| Each asset's PROMISE (per its build intent) vs what is actually served; locate the shortfall layer (data plane vs retrieval plane) and enable the promise | Lane 10; deliverable 9 |
| Audit size must not dilute any point; context decay must not thin the later lanes; brief must be built in Claude Code with time, missing nothing; document completeness must be verifiable | §12 execution architecture |

## Appendix B — Lane 8 facet taxonomy v2 (THE FLOOR; native directive: maximal classical
extent, beyond project data; the foundry's DB+canon discovery pass may only ADD, never cut)

Supersedes the 10-facet draft in §5 Lane 8. Applies per graha; §B-VIII.9 extends the Lagna
dossier. Every facet is a ledger row: held? → wire-reachable? → ≤2 calls? → usable form?

### B-I. Positional & coordinate
1. Sign, degree-minute-second; bhoga traversed
2. House by whole-sign AND bhava-chalit (Sripati/Placidus) — divergence flagged
3. Bhava madhya distance; bhava/rashi/nakshatra sandhi proximity; cusp dual-flavor
4. Nakshatra, pada, nakshatra lord; KP star/sub/sub-sub
5. Navatara class from Moon AND from Lagna (janma/sampat/vipat/kshema/pratyak/sadhana/naidhana/mitra/parama-mitra)
6. Declination (kranti), celestial latitude (shara); rise/set state (udaya/asta); oriental/occidental of Sun
7. Speed, speed-ratio to mean, stationary proximity; retrograde/direct phase geometry
8. Ayana placement (uttarayana/dakshinayana); gola

### B-II. Dignity & sign-based
9. Exaltation/debilitation with exact deep-degree distance; ucha-abhilashi (approaching)
10. Mulatrikona / own / panchadha compound relation (natural × temporal) with sign lord
11. Neecha-bhanga condition enumeration (all classical grounds, each with evidence)
12. Vargottama; pushkara bhaga; pushkara navamsha
13. Mrityu bhaga (per-sign degree check); yogatara proximity
14. Dagdha / tithi-shunya / mrityu rashi ownership effects
15. Sign-type flavor: chara/sthira/dvisvabhava, odd/even, tattva, prishtodaya/sirshodaya/ubhayodaya

### B-III. Strength systems (full battery)
16. Shadbala complete tree: sthana (uccha/saptavargaja/ojayugma/kendradi/drekkana), dig,
    kala (nathonnatha/paksha/tribhaga/abda/masa/vara/hora/ayana/yuddha), cheshta,
    naisargika, drik — each component + total VS REQUIRED MINIMUM ratio (normative band)
17. Ishta/Kashta phala
18. Vimsopaka (shadvarga/saptavarga/dashavarga/shodashavarga) + vaiseshikamsha ladder
    (parijata→devaloka) with amsha counts
19. Bhava bala of houses owned and occupied
20. Pancha-vargiya bala (Tajaka context); dwadash-vargiya where computed
21. **Ashtakavarga**: BAV per-sign bindus + total; bindus in occupied sign; kaksha lord at
    its degree; SAV of occupied + owned houses; sodhya pinda (post-shodhana); transit
    ashtakavarga filter
22. Sapta-vargaja dignity tally; own-varga counts

### B-IV. State & condition
23. Combustion with orb, applying/separating; graha yuddha (winner/loser, method)
24. Grahan yuti (node + luminary eclipse association)
25. Avastha sets — ALL FIVE: baladi (5), jagradadi (3), deepta-adi (9), lajjitadi (6, with
    causal grahas), shayanadi (12, with sub-components)
26. Gandanta (rashi-nakshatra junction) proximity
27. Upagraha contact: gulika, mandi, dhuma, vyatipata, parivesha, indrachapa, upaketu; kala-vela lords
28. Saham contacts (Tajaka sahams: punya, vidya, vivaha, mrityu, karma, …)

### B-V. Relational web
29. Conjunctions (orb-aware); parashari aspects cast/received with sputa-drishti values
    (full/¾/½/¼); special aspects (Ma/Ju/Sa)
30. Rashi drishti (Jaimini) cast/received
31. Sambandha classification with each graha (exchange, mutual aspect, mutual kendra, one-way)
32. Dispositor web: sign dispositor, nakshatra dispositor, navamsha dispositor, final-dispositor
    chain position + terminus, reception loops
33. Papa/shubha kartari on its position
34. Argala on its positions: shubha/papa/virodha, given and received
35. Vedha: Sarvatobhadra chakra vedhas on its nakshatra; nakshatra vedha pairs; latta
36. Tara bala from Moon (and chandra kriya/vela/avastha for the Moon dossier)

### B-VI. Functional & role-based (lagna-dependent)
37. Lordships from Lagna, Moon, Sun; functional benefic/malefic/neutral; yogakaraka status
38. Kendradhipati dosha; badhaka/badhakesh status; maraka lordship/association
39. Naisargika karaka portfolio; sthira karaka; chara karaka (AK/AmK/BK/MK/PK/GK/DK) +
    karakamsha relation
40. Arudha involvement: AL lord, arudhas of owned houses, graha arudha positions
41. Yoga participation — EVERY catalog family: raja (house-lord), dhana, mahapurusha,
    nabhasa (correct single member per sankhya), chandra yogas (sunapha/anapha/durudhara/
    kemadruma), surya yogas (vesi/vasi/ubhayachari), parivartana (maha/khala/dainya),
    viparita raja, neecha-bhanga raja, adhi, gaja-kesari, kartari, kala-sarpa/kala-amrita,
    arishta + bhanga, sanyasa yogas
42. Dosha participation: mangal (from lagna/Moon/Venus), shrapit, pitru, grahan,
    guru-chandal, angarak, kemadruma, daridra, and full L0 catalog
43. 22nd drekkana (khareshwara) and 64th navamsha lord status; sarpa/pasha/nigala drekkana occupancy

### B-VII. Temporal (the graha as time-lord)
44. Vimshottari lordship now (MD/AD/PD/sookshma/prana) + next windows at each level;
    dasha-sandhi proximity
45. Dasha-quality context: dignity/house of each running lord FROM this graha and vice versa
46. Other dasha systems: yogini role; chara/narayana rashi-dasha periods of its signs;
    ashtottari; kalachakra deha/jeeva relation
47. Transit now: sign/house from natal Moon and Lagna, gochara quality + vedha points,
    murthi at ingress; ashtakavarga bindu filter in transited sign
48. Sade-sati/dhaiya involvement (Saturn dossier; Moon dossier as receiver)
49. Double-transit (Saturn+Jupiter) participation on natal points
50. Varshaphal role: year-lord candidacy, muntha relation, tajaka aspect set (ithasala,
    easarapha, kamboola, khallasara, rudda, …), tripataki vedha
51. Upcoming/recent eclipses and stations on its natal degree
52. Structural×temporal convergence: which of its yogas/promises are temporally ripe,
    recent past + near future (the R-45 asset)

### B-VIII. Esoteric, remedial & tradition-specific
53. KP significator ladder roles (house-wise); ruling-planet membership
54. Nadi roles (jeeva/karma pairs, bhrigu-bindu relation) where computed
55. Deity web: nakshatra deity, adhidevata/pratyadhidevata; ishta-devata indication path
    (karakamsha 12th etc.)
56. Remedial mapping: gemstone, beeja/vedic mantra, yantra, dana, vrata-vara, deity —
    AND whether served remedial priority reflects its actual afflictions
57. Medical: avayava/body-part, dhatu, vata-pitta-kapha, disease significations from its
    afflictions (L0 medical mappings)
58. Sambandha table: varna, guna, tattva, gender, direction, season, taste, metal, grain, color
59. Nodal axis relations (every graha): nodal dispositor, placement in node's star, node
    delivering its results (agency rules)
60. Special-lagna relations (esp. for Lagna dossier): bhava/hora/ghati/varnada/sree/indu
    lagna + pranapada — graha's house from each where doctrine uses it

Floor: 60 facet groups. The foundry discovery pass (DB + L0 catalogs + canon) may ADD
rows; deletion requires native sign-off. Facets absent from the system entirely are
UNREACHABLE-by-nonexistence findings feeding the Section-6 concept-completeness register.

## Appendix C — Lane 2 question list v1 (native-approved structure, 2026-07-11; **82 types**
× {narrow, broad} variants × 2 charts (ledger: 328 trace rows + header). The preamble
originally said "76" — an authoring arithmetic error caught by the foundry (traceability
Exceptions §3.6); the per-group enumeration below (6+6+5+9+8+10+6+6+6+6+8+6 = 82) is
authoritative and the frozen ledger follows it.)

**A. Deha & Ayus (6):** A1 vitality/constitution · A2 longevity band · A3 health-crisis
timing windows · A4 chronic-disease propensity by system · A5 accident/injury propensity+
windows · A6 recovery capacity.
**B. Buddhi & Svabhava (6):** B1 personality portrait · B2 mental-health resilience/
vulnerability windows · B3 intelligence character · B4 moral fiber + blind spots · B5
fears/psychological knots · B6 maturation arc.
**C. Vidya (5):** C1 education level + interruptions · C2 field aptitude · C3
competitive-exam timing · C4 foreign education · C5 higher/spiritual learning.
**D. Karma & Vritti (9):** D1 nature of profession [anchor: 2026-07-11 session] · D2
service vs business vs practice · D3 rise timing · D4 crisis/fall windows + recovery · D5
job-change timing · D6 authority relationship · D7 fame/recognition · D8 retirement
character · D9 parallel-income patterns.
**E. Dhana & Sampatti (8):** E1 wealth magnitude [anchor] · E2 income/retention/
volatility decomposition · E3 windfall/speculation · E4 debt cycles · E5 property/vehicle
timing · E6 inheritance · E7 losses/theft/litigation erosion · E8 charity/expenditure
disposition.
**F. Kutumba & Vivaha (10):** F1 marriage timing · F2 spouse nature/direction/background
· F3 marital quality + crisis windows · F4 second marriage · F5 divorce/separation risk ·
F6 in-law dynamics · F7 romance vs arranged · F8 extramarital risk · F9 engagement vs
consummation muhurta · F10 dampatya remedial priority.
**G. Santana (6):** G1 children yes/count band · G2 conception windows · G3 santana dosha
+ remedial path · G4 children's wellbeing from parent chart · G5 later-life relation with
children · G6 adoption indication.
**H. Bandhu, Ripu & Vyavahara (6):** H1 sibling relations/fortunes · H2 friendship/
alliance reliability · H3 open + hidden enemies · H4 litigation outcome + timing · H5
betrayal/cheating windows · H6 employee/servant troubles.
**I. Sthana & Yatra (6):** I1 foreign settlement vs visits · I2 relocation timing +
direction · I3 native-place vs away prosperity · I4 pilgrimage/spiritual travel · I5
property abroad · I6 return-to-homeland timing.
**J. Dharma & Moksha (6):** J1 spiritual inclination depth/type · J2 guru arrival timing
· J3 ishta-devata indication · J4 renunciation potential · J5 karmic-debt framing (under
disclosure tiers) · J6 moksha-marga maturity.
**K. Kala-vidhi (8):** K1 varshaphal "how is this year" · K2 current-period quality · K3
muhurta: best window next N months for X [T-15 sits here] · K4 double-transit
confirmation for named bhava · K5 sade-sati status/phase · K6 dasha-sandhi risk periods ·
K7 "when does the current difficulty end" · K8 retrospective period explanation
(LEL-anchored where available).
**L. Meta & whole-chart (6, Lane-7 feeders):** L1 whole-life arc narrative · L2 five
strongest + five weakest promises ranked · L3 central tension/contradiction · L4 notable
ABSENCES (negative knowledge) · L5 whole-chart remedial stack · L6 unprompted acharya
warnings.

Design rules: every group ≥1 timing question (forces the temporal engines everywhere,
per R-45); F/G/J include never-pointed-at territory (unknown-unknown hunters); L items
are unanswerable without large-N synthesis (P-11 requirements feeders).

*End of LLM_CONSUMPTION_AUDIT_PLAN_v1_0 (DRAFT for native review).*
