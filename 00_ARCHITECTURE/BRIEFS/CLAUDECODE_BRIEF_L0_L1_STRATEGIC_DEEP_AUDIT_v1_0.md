# L0+L1 Strategic Deep Audit — Pre-L2 Foundation Analysis (paste into Claude Code / Antigravity)

**This is a DEEP-RESEARCH pass, not a quick audit. Four linked questions, one comprehensive report.
Ground EVERYTHING in the live prod DB + the actual writer code — NOT in closure docs (they have repeatedly
diverged from reality this project). Where a closure/finding doc makes a claim, VERIFY it against current code
before repeating it.** Connect to prod (Cloud SQL proxy, `amjis-db-password/3`), chart `482012f1`. Output:
`00_ARCHITECTURE/L0_L1_STRATEGIC_DEEP_AUDIT_v1_0.md`. Read-only except where it says to verify by query.

Standards context: computed-and-cited hard gate; canonical-or-floor; L1-is-authority (fact_id references);
FROZEN orchestrator contract (@register WriterBase, owns_conn guard); no-threshold-drop (strength is a column,
never a gate); MSR/bo_laksana = deterministic transform projecting EVERY ga_structural fact.

PRIOR ART to verify (do not trust blindly — these predate the L1 closure + enrichment):
- `GA_STRUCTURAL_COMPLETENESS_FINDING_v1_0.md` (2026-06-12, "native review pending") — claims ga_structural
  HARDCODES 24 yogas / 15 doshas (`YOGA_LIBRARY`/`DOSHA_LIBRARY`), reads `brahma_yoga_catalog` ZERO times, and
  silently drops uncatalogued configs + over-orb aspects. **VERIFY each claim against the CURRENT
  ga_structural_writer.py — is the hardcode still there post-closure, or was it fixed?**
- `CLAUDECODE_BRIEF_BODHA_L1E_GA_STRUCTURAL_ENRICHMENT_v1_0.md` — read for the prior enrichment intent.

---

## QUESTION 1 — Orchestrator-autonomy audit: will "Build/Rebuild" run every asset?

For EVERY L0 (`bg_*`) and L1 (`ga_*`) asset, produce a table: asset × [in asset_registry CURRENT?] × [in
asset_registry_seed.ts?] × [build-state correct (asset_throughput state=lit, last_built_at non-null,
build_state_stale=false via the stats ENDPOINT param `chart_id=`)?] × [has a conformant @register WriterBase
writer?] × [orchestrator get_writer resolves it?] × VERDICT (autonomous-ready / NOT).

Specifically confirm the @register + WriterBase conformance per asset (the FROZEN contract): does each have a
`@register('<asset_id>')` class implementing run(ctx) OR plan_substeps+run_substep, using ctx.db_conn WITHOUT
committing (owns_conn guard), getting chart_id/birth_params from ctx.config? **KNOWN GAPS to confirm/refute:**
the L0 closure logged DEFER-001/002 — `bg_transit_engine` + `bg_nakshatra_medical` had NO WriterBase writer
(migration-seeded only, NOT orchestrator-reproducible). Are they STILL writer-less? If yes, a "Rebuild" would
NOT regenerate them — flag as autonomy gaps with the fix (write the @register writer). Do the same check for
EVERY asset; report any other migration-seeded-but-writer-less assets.

Output Q1: the full per-asset autonomy table + a list of any asset that "Build/Rebuild from runtime" would NOT
correctly (re)build, with the specific remediation each needs.

---

## QUESTION 2 — Under-reporting bug hunt + per-asset enrichment audit

**2A — UNDER-REPORTING / COMPLETENESS REGRESSION (bug hunt — the native's integrity concern):**
For each asset, compare its CURRENT row count (via its count_sql on prod) against the HISTORICAL counts recorded
in: the L1/L0 closure records, `SIX_SUBSYSTEM_BUILD_CLOSE_v1_0.md` (e.g. ga_structural was 75,168 there but
74,034 at L1 close — INVESTIGATE that drop specifically), the git history of seed floors, and the enrichment
registers. For ANY asset whose count is LOWER than a prior reported value, determine WHY:
- legitimate (BUG-1 count_sql scope-fix correctly REMOVED double-counted rows — a corrected count, not lost data), OR
- a real REGRESSION (rows that should exist are missing — silent data loss, the thing that defeats completeness).
The distinction is critical: a lower count_sql number after a scope fix is GOOD; fewer actual rows in the table
is BAD. For each flagged asset, query the actual table row count (not just count_sql) across all 5 ayanamshas and
confirm no ayanamsha is short, no category silently empty (the txn-poison/floored-silently class). Report a
table: asset × prior count × current count × actual-table-rows × verdict (corrected / REGRESSION) × evidence.

**2B — PER-ASSET ENRICHMENT AUDIT (strategic, every asset, focus the new ones):**
For EACH L0 + L1 asset, against its master plan + classical scope: is it at FULL computable+citable depth, or is
there more deterministic+citable content it COULD hold? Per asset list: what the tradition offers (deterministic
+ citable), what's captured now, the GAP, and a value rating. Apply the hard gate (a gap counts only if genuinely
computable + citable, not interpretive). Known candidate gaps to assess: bg_yogas 175-of-250 (the catalog is
incomplete — does completing it matter, and is it citable?); bg_rules extracted from only ~8% of text chunks;
ga_medical lacking house-health + sign-body-part per-chart derivation; bg_doshas at 50; Saham 70-vs-36-classical.
Output: per-asset enrichment table + a prioritized "build now / log for v2 / not worth it" verdict each.

---

## QUESTION 3 — Prashna subsystem strategy (ga_prashna is empty by design)

ga_prashna shows 0 rows / NOT BUILT. This is CORRECT for a natal chart (Vimarśaka RT-7: a Prashna asset only
produces data when a horary question is cast at a specific moment — `chart_id` must be in `prashna_charts`).
Read `ga_prashna_writer.py` + `bg_prashna_rules` + the Prashna subsystem master plan. Answer STRATEGICALLY:
1. What IS the Prashna activation model — how does a Prashna chart get created (the question-moment chart-creation
   entry point), and how does ga_prashna populate then?
2. Is the entry-point plumbing actually BUILT (can a user/system cast a Prashna question today), or is only the
   rules layer (bg_prashna_rules) present with no way to trigger a Prashna chart?
3. STRATEGIC OPTIONS for the empty asset: (a) leave it registered-but-dormant (correct, populates on first
   horary query) + ensure the cockpit renders 0-rows-valid not red; (b) build the Prashna chart-creation
   entry-point now so it's demonstrable; (c) defer the whole Prashna activation to a later phase. Recommend one,
   with reasoning tied to where Prashna sits relative to L2 Bodha (does Bodha need Prashna data? — likely no,
   Prashna is its own namespace, never mixed with natal).
Output Q3: the Prashna activation model explained + the 3 options assessed + a recommendation.

---

## QUESTION 4 — ga_structural relational elevation (THE highest-value question — exhaustive)

ga_structural is the relational hub; MSR/bo_laksana derives its ENTIRE relational value from what ga_structural
emits. So ga_structural's completeness ceilings the whole instrument's relational intelligence. Do this
exhaustively, from BOTH a data-science (graph-completeness, what MSR needs as ingredients) and Jyotish-domain
(which relationships are classically load-bearing) perspective.

**4A — What ga_structural CURRENTLY ingests/emits (ground truth):** read `ga_structural_writer.py` in full +
query its actual emitted fact_categories on prod. List every category it emits and every L1 asset/source it
reads. Confirm/refute the prior finding's claims (hardcoded 24 yogas, ignores brahma_yoga_catalog, silent drops).

**4B — The COMPLETE target set it SHOULD ingest (the exhaustive taxonomy).** Map ga_structural against EVERY L1
asset and EVERY classically-load-bearing relationship type. For each, state: does ga_structural currently capture
it, and if not, should it (computable + citable + relationally valuable for MSR)? The taxonomy to assess in full:

ENTITIES it should relate (multi-entity graph): grahas · houses · signs · nakshatras (← ga_nakshatra: is the
nakshatra-dispositor/parallel-graph ingested? prior memory says ga_structural MISSES ga_nakshatra) · vargas
(← per-varga dignity/strength from the enrichment — does ga_structural ingest the new per-varga Ashtakavarga /
per-varga dignity / per-varga avastha rows?) · special/sensitive points (← ga_sensitive: upagrahas, arudhas,
sphutas, Gulika, special lagnas — does ga_structural relate these into the graph? prior memory says it MISSES
ga_sensitive ~19,295 rows) · configs-as-nodes (yogas/doshas as first-class nodes).

RELATIONSHIP TYPES it should emit (assess each for presence + completeness): conjunction (all pairs, no orb
drop) · aspect (Parashari graha-drishti + sign-aspect, Jaimini rashi-drishti, Tajik) · parivartana (exchange,
all types: maha/khala/dainya) · dispositor chains (rashi AND nakshatra dispositors → termini → center-of-gravity)
· argala + virodhargala (all 144) · yoga-firing (catalog-driven from L0's 175, NOT a hardcoded 24) · dosha-firing
(from L0's 50) · per-varga strength relationships (Vimsopaka, per-varga shadbala/AV — the enrichment) · per-varga
dignity spread · avastha relationships · sade-sati relational anchors (← ga_sade_sati) · medical relational
mappings (← ga_medical: graha→dhatu/dosha as graph edges) · vastu directional relationships (← ga_vastu) ·
nakshatra-graph as parallel CGM (rashi-vs-nakshatra agreement = corroboration / divergence = contradiction) ·
tajik/varsha relationships (← ga_tajaka) · KP significator chains · bhava-bala / graha-bala as edge-weights.

**4C — The MSR-leverage analysis (data-science):** MSR signals project ga_structural facts. For the instrument's
relational intelligence to be maximal, ga_structural must emit, as first-class citable rows: the full edge set
(every relationship above) WITH edge-value vectors (strength + valence + domain + directionality +
varga-provenance), graph-theoretic properties (centrality, final-dispositor convergence, parivartana cycles,
path-analysis between domain significators), and convergence/contradiction structure. Assess which of these
ga_structural emits today and which are the high-leverage additions. Frame each addition by: "MSR signal X
becomes possible / richer because ga_structural now emits edge Y."

**4D — Dual-capture model check:** prior memory (`feedback_bodha_dual_capture_model`) says the governing L1/L2
architecture is (1) enrich ga_structural to INGEST the 4 missing L1 assets (ga_sensitive, ga_sade_sati,
panchanga, + the per-varga enrichment) and derive their RELATIONAL value, AND (2) bo_laksana projects the WHOLE
of L1 (ga_structural relational + individual assets native-grained). Confirm whether ga_structural currently
ingests those 4, and specify exactly what relational derivation each needs.

Output Q4: (a) current ga_structural emission map, (b) the EXHAUSTIVE gap table (entity × relationship × present?
× should-add? × data-science rationale × Jyotish rationale × MSR-leverage), (c) a prioritized elevation plan
(what to add to ga_structural, in value order), (d) explicit confirmation of which prior-finding claims are still
live vs fixed.

---

## DELIVERABLE

One report `L0_L1_STRATEGIC_DEEP_AUDIT_v1_0.md` with Q1/Q2/Q3/Q4 sections, every claim backed by a query result
or a code citation (file:line). Flag clearly: which findings are VERIFIED-LIVE-DEFECTS vs already-fixed vs
strategic-recommendations-needing-native-sign-off. This report is the input to the native's L0/L1 strategic
decisions before L2 Bodha opens. Do NOT make changes — this is analysis; the native decides what to build from it.
End with a one-page EXECUTIVE SUMMARY: the autonomy gaps, the real regressions (if any), the top enrichment
opportunities, the Prashna recommendation, and the ga_structural elevation headline.
