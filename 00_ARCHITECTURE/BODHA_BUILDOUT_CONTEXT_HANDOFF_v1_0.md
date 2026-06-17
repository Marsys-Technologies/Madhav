---
artifact: BODHA_BUILDOUT_CONTEXT_HANDOFF_v1_0.md
canonical_id: BODHA_BUILDOUT_CONTEXT_HANDOFF
version: 1.0
status: CURRENT
authored_by: Cowork 2026-06-16
purpose: >
  SELF-CONTAINED context handoff for a fresh L2 Bodha build-out conversation. Read THIS document
  and the artifacts it cites — you do not need any prior conversation history. It carries the
  built-state of L0/L1/orchestrator, the locked L1↔L2 architecture, the Bodha design philosophy,
  the 8-asset DAG, every locked decision, the two documented traps, the current prod baseline, and
  the open frontier. Conversation/cleanup baggage (git ops, cockpit display fixes, CI hygiene) is
  deliberately OMITTED — only what informs Bodha build decisions is here.
audience: the Bodha build-out conversation (Cowork plans → Claude Code in Antigravity executes)
read_next_in_order:
  - 00_ARCHITECTURE/L2_BODHA_BUILD_CAMPAIGN_v1_0.md (the governing master campaign — §13 philosophy, §3 decisions, §14 spec→table map)
  - 00_ARCHITECTURE/L1_L2_RELATIONSHIP_ARCHITECTURE_DECISION_v1_0.md (the projection model — the single most important read)
  - 00_ARCHITECTURE/A10_MSR_SPEC (v1.2) + A11_CDLM + A12_CGM + A13_RM + A14_UCN_RETIRED_TO_UCD (the LOCKED per-asset specs)
  - 00_ARCHITECTURE/ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2 (FROZEN WriterBase contract) + §5 (conformance checklist)
  - 00_ARCHITECTURE/MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0.md (Trap 1) + MSR_UCN_CONTAMINATION_AUDIT_v1_0.md (Trap 2)
  - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md §2 (live "you are here" — always verify against this + git, never a frozen doc)
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_WAVE3_4_RETRIEVAL_AND_BODHA_v1_0.md (the B1–B5 phase plan — already authored)
---

# L2 Bodha Build-Out — Context Handoff v1.0

## §0 — The mission in one paragraph
MARSYS-JIS is an LLM-operated Jyotish instrument for the native **Abhisek Mohanty (1984-02-05,
10:43 IST, Bhubaneswar; canonical chart_id `482012f1-710e-4a25-994a-93821f5871aa`)**. It is built
as six deterministic data layers: **L0 Brahmagyan** (global classical knowledge), **L1 Gaṇita**
(this chart's computed facts), **L2 Bodha** (synthesis — THIS build-out), L3 Kāla (time), L4 Phala
(prediction), L5 Mīmāṃsā (cross-chart learning). Two founding pillars: **(1) data completeness**
(capture every deterministic fact, never pre-drop) and **(2) retrievability** (every stored fact
reachable by the LLM). L0 and L1 are SEALED and built in prod; the orchestrator is FROZEN. **Bodha
is next, and its code is already scaffolded but NOT yet run — the tables are empty.**

---

## §1 — What is BUILT and SEALED below Bodha (the foundation Bodha sits on)

### L0 Brahmagyan — global classical knowledge (SEALED, built, all CURRENT)
14 assets, **851,910 rows**. The global reference Bodha labels/cites against. Key for Bodha:
- `bg_ephemeris` (825,084 raw positions 1900–2150, pyswisseph DE441) — the computational floor.
- `brahma_yoga_catalog` (409 yoga_labels) + `brahma_dosha_catalog` (85 dosha_labels) — **the NAME+citation source Bodha/L1 use to LABEL enumerated configurations** (NOT a firing gate).
- `brahma_remedy_corpus` (260 remedies) — what `bo_upaya` (RM) grounds remedies to (every remedy carries a classical citation; none invented).
- `bg_texts` (8,193 classical chunks + embeddings), `bg_rules` (1,976 verse-traceable rules), `bg_ontology`, `bg_reference` (15 typed vocab tables), `bg_doshas`, `bg_dasha_systems` (18).
- Two service engines: `bg_panchanga` (Pañcāṅga Gaṇanā) + `bg_ephemeris_engine` (Druk Ephemeris).
- **Eliminated:** `bg_signal_type_registry` (G52) — G52 ELIMINATED 2026-06-16 (native directive); no table, no seed, no dependency. Do NOT build Bodha as a predicate registry.

### L1 Gaṇita — this chart's computed facts (SEALED, built, all CURRENT, promoted from DRAFT 2026-06-16)
10 assets, **~654,999 rows** into `chart_facts` (+ `chart_dashas`, `chart_divisionals`). The
deterministic fact base Bodha PROJECTS. Canonical built counts (verified live on the native chart):
- `ga_positions` (Graha-sthāna), `ga_vargas` (Varga, 21,635), `ga_dashas` (Daśākrama, 536,471),
  `ga_strength` (Balatva, 2,184), `ga_sensitive` (Sūkṣmabindu, 8,055), `ga_panchanga` (221),
  `ga_sade_sati` (11,019), `ga_tajaka` (240), and the keystone **`ga_structural`** (74,644).
- Service: `ga_pyjhora_engine` (the engine; PyJHora replaced the old natal_engine — trust its
  outputs, verify by internal consistency only, NO Jagannatha-Hora parity gate anywhere).
- **FORENSIC 7/7** on all 5 ayanamshas (Sun=Capricorn, Moon=Purva Bhadrapada, Lagna=Aries, Tithi=
  Shukla Tritiya, Vara=Ravivara, Yoga=Shiva, Karana=Garaja). FORENSIC is the L1 authority surface.

### `ga_structural` — THE KEYSTONE Bodha depends on (read this carefully)
`ga_structural` is the **complete deterministic relational fabric** and is the single most
important input to Bodha. It was rebuilt to maximal completeness (the old version leveraged only
~5% of L1, D1-only). It now holds, by EXHAUSTIVE ENUMERATION (not predicate-matching):
- Every aspect / conjunction / dispositor-chain / parivartana / argala / composite-state / avastha,
  **across all 30 vargas × 5 ayanamshas**, with Rahu/Ketu in every loop.
- Each relationship's **INTRINSIC strength** (yoga_strength_score, graha_in_house_composite_strength,
  karakatva_strength) and its classical **NAME label** (from brahma_yoga_catalog — a label OVER the
  enumeration, never a firing gate; unnamed configurations are still recorded).
- 8 relationship families added in the completeness amendment (node-aspects, Kala Sarpa/Amrita,
  special-point relationships, house-lord matrix, jaimini-per-varga, karaka web, graha yuddha,
  combustion/retrograde).
- **Real fact_ids** (sha256-derived, resolvable), two-pass verification, no silent drops.
- **Disambiguation hard requirement:** every relationship row is fully qualified by varga + sign +
  ayanamsha + houses/degrees. "Jupiter-Venus conjunction in D1 Sagittarius lahiri" is a DISTINCT row
  from the same pair in D9. No relationship row exists without full context.
- **Retrieval nuance Bodha must respect:** D1's structural facts are SPLIT across two naming
  conventions — base categories (e.g. `aspect_parashari_given`, `argala_natal_matrix`) ∪ the D1 slice
  of the 6 `_per_varga` categories. "All of D1's structural facts" = base ∪ D1-per_varga. A query
  filtering only `%_per_varga` UNDER-COUNTS D1.

### Orchestrator — FROZEN (Bodha onboards by conforming, never by extending it)
The build orchestrator was built once and is FROZEN (`ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2`).
Every Bodha writer:
- is a `@register('bo_<asset>')` **`WriterBase` subclass**;
- implements `run(ctx) -> WriterResult` (light) OR `plan_substeps(ctx)` + `run_substep(ctx, step)` (heavy);
- runs on **`ctx.db_conn` and NEVER commits or closes it** — the orchestrator owns the transaction + per-substep savepoint;
- does **NOT** write `asset_throughput` (the orchestrator is the sole build-state writer);
- gets `chart_id` + `birth_params` from `ctx.config`.
- **If a writer seems to need a contract change → STOP and raise with the native. The freeze is deliberate.**
The "Build" / "Rebuild" buttons in the cockpit drive any chart's assets in DAG dependency order via
this contract. Bodha is driven by `POST /api/cockpit/runs scope=layer/bodha`.

---

## §2 — The LOCKED L1↔L2 architecture (the most important section — read twice)

This is the native-reasoned model (2026-06-12, doc `L1_L2_RELATIONSHIP_ARCHITECTURE_DECISION_v1_0`)
that governs the whole Bodha build. Get this right and the rest follows.

**Two legacy artifacts are PURGED from the reasoning — do NOT invoke them when building Bodha:**
1. **B.1** (the old PROJECT_ARCHITECTURE "Facts/Derivation/Interpretation, derivations at the
   L1/L2.5 boundary") is LEGACY GOVERNANCE that predates the clean L0–L5 model and was the SOURCE
   of L1-vs-L2 ambiguity. Do NOT place layers by B.1.
2. **SIG.MSR.377** is a historical note about data no longer in any DB. Not a live constraint.

**The decisive line — INTRINSIC vs POPULATION-LEVEL** (the test: computable from chart geometry
alone, or does it need the whole relationship set to exist first?):
- **L1 `ga_structural` = INTRINSIC.** Every relationship + its intrinsic strength + classical name,
  computed from geometry alone, exhaustively enumerated. Computed once, stored, ID'd, never
  re-decided. Two-pass verification lives HERE.
- **L2 Bodha (MSR etc.) = POPULATION-LEVEL.** Holds NO new fact about what exists — holds
  SIGNIFICANCE over what exists: top_k_salience_rank, domain_salience, cross_domain_shared_factor_count,
  system_convergence_count, contradicts_signals_array, computed_salience. These are operations OVER
  the whole population — structurally impossible at L1. "The forest the trees can't see."

**Bodha is a PURE PROJECTION, not a re-firing engine:**
- `bo_laksana` (MSR) **INHERITS** firing + intrinsic strength from `ga_structural` by referencing its
  `fact_id` — it does **NOT** re-fire predicates and does **NOT** re-derive strength (those would be
  redundant copies, the exact thing to avoid). It **ADDS ONLY** rank / convergence / contradiction /
  domain-salience / retrieval-shape.
- **NO predicate registry.** A predicate/registry (the old G52 "500–700 rules") fires only what's
  authored → bounded → can never cover every relationship. Enumeration (already done in
  `ga_structural`) is bounded only by the chart's finite combinatorics → complete by construction.
  So: the relational base is exhaustive enumeration (L1); named yogas/doshas are a LABEL pass over it
  (from L0 catalog); Bodha projects + enriches. **G52 is ELIMINATED ENTIRELY (native directive 2026-06-16).**

**THE ANTI-DRIFT SPINE (the load-bearing acceptance for the whole layer):** every Bodha signal's
`constituent_facts_array` MUST resolve to real `chart_facts.fact_id` rows. A Bodha signal that
restates an L1 computed value as its own truth, or whose fact_id doesn't resolve, is a HALT-WORTHY
bug — not a stored divergence (Trap 1). This is the single most important thing to verify when the
build runs.

**A10 was respecced to v1.3** to match this: prime_directive = population-level enrichment over
`ga_structural` enumeration; `depends_on ga_structural` PRIMARY; G52 eliminated entirely (native directive 2026-06-16); §0 mission rewritten from "evaluate predicates against atoms" to
"project ga_structural + compute population enrichment."

---

## §3 — The Bodha design philosophy (native-ratified 2026-06-10; what Bodha is FOR)

L1 = storage completeness. **L2 Bodha = LEVERAGE: deterministic data-engineering over L1's atoms**
to find relationships / chains / convergences / contradictions / graph-structure, stored optimized
for LLM retrievability. Five locked principles:

1. **Statistical line (protects determinism):** L2 = WITHIN-chart deterministic structural stats
   ONLY — cross-ayanamsha consistency (5/5 vs 2/5), convergence density per domain, graph centrality,
   confidence intervals under perturbation. All reproducible from THIS chart's own facts. **Cross-chart
   / across-many-people correlations = EMPIRICAL inference → defer entirely to L5 Mīmāṃsā.** Never
   compute cross-chart correlation in L2 — it contaminates the deterministic base (Trap 2).
2. **Convergence + contradiction = FIRST-CLASS** (the ceiling-raiser, beyond pairwise CDLM/CGM):
   compute and store convergence-density-per-domain (N independent L1 signals → one life domain =
   weight of evidence) AND contradiction-pairs (signals in tension) as their own salience-ranked
   artifacts. The acharya-grade move (weight of evidence, not isolated rules). Contradiction-detection
   doubles as the drift guardrail.
3. **Retrieval = "rich pre-computed relational ingredients, LLM synthesizes at query" (NOT
   pre-answered questions).** Store granular signals AND the deterministic RELATIONSHIPS among them
   (convergence counts, contradiction pairs, graph properties, salience rankings) as first-class,
   citable, provenance-bearing rows. Query-time LLM synthesizes narrative from this pre-structured
   set — flexible NARRATION, not flexible COMPUTATION. Determinism + research-instrument flexibility.
4. **Every judgment = a VERSIONED deterministic FORMULA, not a stored opinion** (`salience_formula_v1`,
   `convergence_formula_v1`, `centrality_formula_v1`, `resonance_score_v1`). "Why is this top?" always
   has a reproducible auditable answer. Improve method → bump version → rebuild → clean before/after.
   This is the architectural fix for the contamination trap (no human/LLM judgment leaks into which
   signals fire or how strong).
5. **The graph is where deterministic meets deep — invest hardest** (`bo_bimba` nodes + `bo_karanajala`
   edges / CGM): compute graph-theoretic properties no acharya computes by hand but are deterministic —
   final-dispositor (chart's center of gravity), parivartana cycle structure, weighted centrality
   (most consequential factor), path analysis between domain significators (the reasoning chain).

**IMPORTANT — these EXTEND the LOCKED A10–A14 specs:** convergence-density + contradiction-pairs as
their OWN first-class tables (`bodha_convergence`, `bodha_contradictions`, `bodha_cgm_paths`) + the
new formulas (`convergence_formula_v1`, `centrality_formula_v1`) were APPROVED as §13.1 extensions
(native sign-off 2026-06-12). The base A10–A14 specs scope only pairwise CDLM/CGM links; these
extensions add the population-level depth. They are part of the build.

**Quality bar:** acharya-grade. An independent senior Jyotish acharya reviewing the corpus should
reach "this is my level / above my level / reveals things I wouldn't have seen on first pass."

---

## §4 — The 8-asset Bodha DAG + spec→table map (already wired, migration 224)

Tables are `bodha_*` (mirrors `bg_*`/`ga_*`; the specs' `l25_*` names are read as `bodha_*`). All
`scope: per_chart` except `bo_pramana_mapa` (global). DAG (`depends_on` already in the registry):

```
bo_laksana (MSR, A10)             depends_on: [bg_rules + ga_structural PRIMARY]   ← ROOT; everything fans from it
 ├─ bo_bimba (CGM nodes, A12)     depends_on: [bo_laksana]
 ├─ bo_karanajala (CGM edges,A12) depends_on: [bo_laksana]
 ├─ bo_sangati (CDLM, A11)        depends_on: [bo_laksana]
 ├─ bo_samvada (UCD, A14)         depends_on: [bo_laksana]    ← read-side join, NOT a UCN writer (§5)
 └─ bo_samskara (embeddings)      depends_on: [bo_laksana]
bo_upaya (RM, A13)                depends_on: [bo_laksana, bo_sangati]
bo_pramana_mapa (scorecard)       depends_on: []  (global)
```

| `bo_` asset | spec | tables the writer populates |
|---|---|---|
| `bo_laksana` | A10 MSR | `bodha_msr_signals` (~50 cols) + 3 MVs (top_signals / recurring_patterns / domain_summary) |
| `bo_sangati` | A11 CDLM | `bodha_cdlm_cells`, `_domain_rollups`, `_chart_summary`, `_pattern_clusters` + `bodha_convergence` (§13.1) + MVs |
| `bo_bimba` | A12 CGM nodes | `bodha_cgm_nodes` |
| `bo_karanajala` | A12 CGM edges+struct | `bodha_cgm_edges`, `_sub_graphs`, `_motifs`, `_chart_summary` + `bodha_contradictions` + `bodha_cgm_paths` (§13.1) |
| `bo_upaya` | A13 RM | `bodha_rm_resonances`, `_remedy_prescriptions` + remaining A13 tables (6 total), grounded to brahma_remedy_corpus |
| `bo_samskara` | embeddings | `bodha_signal_embeddings` (pgvector, 1:1 with MSR signals) |
| `bo_samvada` | A14 UCD | read-side `vw_chart_digest` + `query_ucd` tool (Option A — NOT a writer; or thin writer for ~5 folded UCD cols) |
| `bo_pramana_mapa` | scorecard | `synthesis_quality_scorecard` (global) + Trap-1 audit |

**Build order:** `bo_laksana` first (root) → fan-out (`bo_bimba ∥ bo_karanajala ∥ bo_sangati ∥
bo_samvada ∥ bo_samskara`) → `bo_upaya` (needs MSR + CDLM) → `bo_pramana_mapa`. The orchestrator
self-orders from `depends_on`.

> Note on `bo_bimba`/`bo_karanajala`: A12 CGM is ONE igraph compute (nodes + edges + sub_graphs +
> motifs together). Recommended: one heavy `bo_karanajala` writer emits everything; `bo_bimba` is a
> thin nodes-only registry face on the same compute. Confirm against the DAG executor at brief time.

**count_sql basis (native 2026-06-12):** a multi-table asset's cockpit headline count =
the chart-scoped row count SUMMED over ALL its tables (e.g. `bo_sangati` = cdlm_cells + domain_rollups
+ chart_summary + pattern_clusters + bodha_convergence, all `WHERE chart_id=$1`). `target_floor` =
the achieved SUM after first build (floors are aspirational, NOT gates — never fabricate to hit a number).

---

## §5 — Locked decisions (settled at campaign open — do NOT relitigate mid-build)

1. **Table naming = `bodha_*`** (the specs' `l25_*` are read as `bodha_*`).
2. **LOCKED A10–A14 specs win over the coarse 8-row seed placeholders.** Build the rich multi-table
   spec architecture (~17 `bodha_*` tables, ~50-col schemas), not 8 flat tables. The asset-id grain
   stays at 8 `bo_` assets (one writer populates many tables, like `ga_dashas`).
3. **§13.1 philosophy extensions APPROVED** — `bodha_convergence` / `bodha_contradictions` /
   `bodha_cgm_paths` + `convergence_formula_v1` / `centrality_formula_v1` are part of the build.
4. **`bo_samvada` = Option A** — UCD is a read-side join (`vw_chart_digest` + `query_ucd` tool),
   NOT the retired UCN narrative writer. (UCN is retired per A14.)
5. **Phase-0 table reconciliation = REPOINT-NOT-DROP, prod-gated, table-by-table.** The legacy
   `bodha_signals` table has a LIVE READER (`consult/route.ts`); the `l25_*` tables are live
   (migration 137). Repoint any reader to the spec table (or a compat view) BEFORE retiring a legacy
   table. Never blind-DROP — run a reverse-citation check first.
6. **G52 predicate registry is ELIMINATED ENTIRELY** (native directive 2026-06-16; see §2). Do NOT build a signal_type_registry
   as a Bodha prerequisite — the old A10 §5/§12 requirement for it is superseded by the projection model.
   (`L2_BODHA_BUILD_CAMPAIGN §3.4` has been updated to reflect this elimination; the projection model in §2 here governs.)
7. **No audience tier** anywhere (no client/acharya/super_admin gating in writers — serve-time governs access).
8. **Deterministic-first:** Python over LLM for all build-time computation. Embeddings are a
   deterministic transform and are fine; generative LLM for curation is NOT.

---

## §6 — The two documented traps (Bodha must not repeat them)

- **Trap 1 — Computed-value authority inversion** (`MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0.md`): an
  L2 signal must NEVER restate an L1 computed value as its own truth. It REFERENCES the L1 `fact_id`
  and inherits L1's value. If a signal's derivation disagrees with the L1 fact it cites → HALT, it's a
  bug. The `constituent_facts_array` MUST resolve to real `chart_facts` rows. FORENSIC-anchored
  signals must inherit L1 values (e.g. Muntha = Libra/7H/Venus, not re-derived). This is the anti-drift spine.
- **Trap 2 — Interpretation contamination of the deterministic base** (`MSR_UCN_CONTAMINATION_AUDIT_v1_0.md`):
  no human/LLM judgment may leak into which signals fire or how strong they are. Everything is a
  versioned deterministic formula (§3.4). No narrative in the asset — interpretation is serve-time only.

---

## §7 — Current prod baseline (verify against CURRENT_STATE + git, not this frozen doc)

- **main HEAD = merge commit `b9bb3a84`** (2026-06-16): L0/L1 closure + Nirmāṇa page rename +
  retrievability layer + the 8 `bo_*` writer SCAFFOLDS + cockpit fixes, all merged. 396 tests pass.
- **Migrations through 236 are committed.** Bodha-relevant ones already applied to prod in earlier
  sessions: `226_bodha_spec_tables` (the `bodha_*` spec tables), `230_bodha_registry_reconcile`.
  **VERIFY prod == files before building** (the seed→prod path has diverged before — confirm 226 +
  230 actually applied, and that the `bodha_*` tables exist at full spec schema).
- **The retrievability pillar (Wave 3) is DONE:** 19 L1 grouped retrieval tools + 4 L0 corpus tools =
  100% coverage of stored categories; a CI coverage gate (`tests/retrieval/coverage_gate.test.ts`)
  enforces it. Bodha's outputs will need their own retrieval tools added to this layer + the gate.
- **PyJHora is the engine.** Trust its outputs; verify by internal consistency only; no JH-parity gate.
- **Data plane is ALWAYS prod** via the Cloud SQL Auth Proxy (`platform/scripts/start_db_proxy.sh`,
  port 5433). Localhost runs the Next.js code plane; DB + GCS always go to prod. The proxy must be up
  to run the Bodha build.

---

## §8 — The Bodha frontier — what is and isn't done, and the first move

**Status: Bodha code is CODE-COMPLETE but the BUILD HAS NOT RUN. The `bodha_*` tables are EMPTY.**
All 8 `@register('bo_*')` WriterBase subclasses are written and merged (scaffolds):
`bo_laksana` (heavy, `salience_formula_v1`, fact_id-referencing), `bo_bimba`, `bo_karanajala`
(edges + contradictions), `bo_sangati` (cdlm + convergence), `bo_samskara` (`placeholder_hash_v1`
768-dim — a DETERMINISTIC PLACEHOLDER, not real semantic embeddings; flag when real embeddings
matter for retrieval), `bo_upaya` (RM grounded to brahma_remedy_corpus), `bo_pramana_mapa`
(scorecard + Trap-1 audit), `bo_samvada` (= `vw_chart_digest` view). Plus `query_ucd.ts`, migration
`230_bodha_registry_reconcile`, and a DRAFT `L2_BODHA_CLOSE_v1_0` (with the L3 Kāla onboarding §4).

**The load-bearing acceptance is UNVERIFIED** because the writers haven't run: that `bo_laksana`'s
`constituent_facts_array` RESOLVES to real `chart_facts` rows (the anti-drift spine), that
FORENSIC-anchored signals inherit L1 values, and that counts are real. Code-right ≠ data-built.
**L2 is NOT sealed; `L2_BODHA_CLOSE` stays DRAFT until the build passes.**

**The first move (= phase B5 of the already-authored `CLAUDECODE_BRIEF_WAVE3_4_RETRIEVAL_AND_BODHA`):**
1. Bring the Cloud SQL proxy up; confirm migrations 226 + 230 applied to prod (the `bodha_*` tables exist at spec).
2. `POST /api/cockpit/runs scope=layer/bodha` for the native chart — orchestrator runs the DAG in order.
3. **Verify the anti-drift spine first, before fanning out:** every `bo_laksana` signal's
   `constituent_facts_array` resolves to a real `chart_facts.fact_id`; signal count tracks the
   `ga_structural` fact count (NOT a predicate catalog — proving the projection model, not re-firing);
   FORENSIC-anchored signals inherit L1 values.
4. Then verify the fan-out: convergence + contradiction are first-class ROWS (not just columns); CGM
   graph metrics present; embeddings 1:1 with MSR; RM remedies each carry a classical citation.
5. Cockpit/Atlas: 8 `bo_` assets lit, counts = summed `count_sql` per §4; `target_floor` = achieved.
6. Then promote `bo_*` DRAFT→CURRENT (the same flip L1 just had — only AFTER the build verifies),
   reconcile the registry, and seal `L2_BODHA_CLOSE` with the L3 onboarding contract.

**Recommended approach (Cowork's read):** even though a Wave-4 brief exists, start the new
conversation by re-deriving B1 (`bo_laksana` as pure projection) from THIS document + the
architecture decision, and **prove the anti-drift spine on `bo_laksana` before building any
downstream asset.** That spine resolving is the whole point of the projection model; everything
downstream inherits from it. If it doesn't resolve, stop and fix the projection — do not fan out
onto a broken root.

**Out of scope for Bodha (named so they're not pulled in):** L3 Kāla / dasha-temporal activation
(when a relationship is active/dormant by period — deferred to the time layer); any `ga_structural`
re-amendment (it is complete at 74,644 rows); cross-chart correlation (L5 Mīmāṃsā). Do NOT
reintroduce the predicate-firing model or G52 in any form.

---
*End of BODHA_BUILDOUT_CONTEXT_HANDOFF v1.0. Self-contained: foundation built-state (L0 851,910 /
L1 654,999 / ga_structural keystone 74,644 / FROZEN orchestrator), the LOCKED projection architecture
(L1 intrinsic enumeration → L2 population-level projection, no predicates, no re-firing, anti-drift
spine = constituent_facts_array resolving to real fact_ids), the 5-point design philosophy + §13.1
extensions, the 8-asset DAG + spec→table map, the locked decisions, the two traps, the current prod
baseline (main b9bb3a84), and the frontier (code-complete, build-not-run; first move = run + verify
anti-drift spine on bo_laksana before fan-out). Read the cited specs + the architecture decision next.*
