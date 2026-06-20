# ga_structural Relational-Hub INGEST MAP — read-only ground-truth investigation (paste into Antigravity)

**Purpose:** ga_structural is the relational hub — MSR/bo_laksana derives its relational value from what
ga_structural emits. But ga_structural was built against the OLD, smaller L1. The layer has since GROWN: ga_sensitive
was enriched (Tier-1 classical points — Gulika, upagrahas, special lagnas, sphutas, ~8,610 rows), ga_strength got
per-varga Shadbala/Ashtakavarga (~11,936), ga_nakshatra added a PARALLEL NAKSHATRA CHART (dispositor graph,
KP-249, nakshatra-as-second-zodiac, ~1,802), plus ga_medical, ga_vastu, ga_condition (per-varga avasthas), ga_tajaka,
ga_sade_sati. **The question this investigation answers (read-only, NO changes): for EVERY L1 asset, what relational
value does it hold, does ga_structural currently INGEST it and derive relationships from it, and what relationship-
type SHOULD it derive?** This produces the MAP. The native decides the re-architecture FROM the map afterward.

**CRITICAL:** the prior audit (`L0_L1_STRATEGIC_DEEP_AUDIT_v1_0.md` Q4.5) CLAIMED ga_sensitive + ga_vargas are
"dual-captured" and ga_sade_sati/panchanga appropriately single-capture. **DO NOT trust that claim** — it was
agent-reported and may not account for the ENRICHED versions or the parallel nakshatra chart. Re-establish ground
truth by reading the code + querying prod. Cite every finding (file:line or SQL result). Connect to prod
(`amjis-db-password/3`), chart `482012f1`. Output: `GA_STRUCTURAL_INGEST_MAP_v1_0.md`.

---

## STEP 1 — What ga_structural CURRENTLY ingests (the truth, from code)

Read `platform/python-sidecar/ga_writers/ga_structural_writer.py` IN FULL (it's the 4,351-line active writer;
the orchestrator file is a 36-line adapter). For EVERY `_build_*_rows` / `_load_*` function, document:
- WHICH L1 source it reads (chart_facts category? chart_divisionals? a specific ga_* asset's table/category?).
- WHAT it does with it (derives a relationship? just copies? aspect/conjunction/edge-weight/graph-node?).
- Produce a table: ga_structural function × source-asset-read × relationship-derived × output-category.

Specifically confirm by reading the code (not assuming):
- Does it read the ENRICHED ga_sensitive categories — the NEW Tier-1 points (gulika_mandi, sun_derived_upagraha,
  special_lagna, esoteric_point_sphuta_fertility, yogi/dagdha)? Or only the OLD sensitive categories
  (upagraha_position, arudha_pada) that existed when it was written? (`_build_special_point_relationship_rows`
  reads `upagraha_position` per the audit — does it read the NEW ones?)
- Does it read the PER-VARGA ga_strength enrichment (per-varga Shadbala, per-varga Ashtakavarga) as edge-weights,
  or only D1 strength?
- Does it read the PARALLEL NAKSHATRA CHART from ga_nakshatra (nakshatra_dispositor chain, nakshatra exchange/
  conjunction/cogravity, KP-249) and derive a nakshatra-graph — OR does it only emit its OWN `nakshatra_dispositor`
  (200 rows) computed independently? (Is there duplication / divergence between ga_structural's nakshatra_dispositor
  and ga_nakshatra's?)
- Does it read ga_medical / ga_vastu / ga_condition (per-varga avasthas) / ga_tajaka relationally at all?

## STEP 2 — What relational value EACH L1 asset HOLDS (the opportunity side)

For EVERY L1 asset, document the relational value it contains that a hub COULD weave into the graph:
- ga_positions, ga_vargas, ga_strength (D1 + per-varga), ga_sensitive (old + enriched Tier-1), ga_nakshatra
  (placement + parallel chart + KP-249), ga_condition (D1 + per-varga avasthas), ga_dashas, ga_panchanga,
  ga_sade_sati, ga_medical, ga_vastu, ga_tajaka, ga_yoga.
- Per asset: what ENTITIES it introduces (e.g. ga_sensitive → sensitive-point entities; ga_nakshatra → nakshatra
  entities + parallel-zodiac) and what RELATIONSHIPS are derivable (e.g. graha↔sensitive-point aspect; per-varga
  strength as an edge-weight on every varga relationship; nakshatra-graph-vs-rashi-graph corroboration/contradiction;
  medical graha→dhatu edges; vastu graha→direction edges).

## STEP 3 — THE GAP MAP (cross-reference 1 against 2)

The deliverable. A table: L1 asset × relational-value-it-holds × ga_structural-ingests-it-today? (YES/PARTIAL/NO,
with evidence) × relationship-type-it-SHOULD-derive × data-science-rationale × jyotish-rationale × MSR-leverage ×
priority. Flag especially:
- ENRICHED assets ga_structural was NOT built to ingest (built against old L1): the new ga_sensitive Tier-1 points,
  per-varga ga_strength, the parallel nakshatra chart. These are the suspected gaps the native raised.
- DUPLICATION/DIVERGENCE: anywhere ga_structural computes something an enriched asset ALSO computes (e.g.
  nakshatra_dispositor) — is ga_structural's version now stale/redundant vs the canonical ga_nakshatra one? (Single-
  source-of-truth concern — L1-is-authority: ga_structural should REFERENCE the asset's fact_id, not recompute.)
- The dual-capture verdict per asset: should ga_structural INGEST it relationally (and bo_laksana also project it
  natively = dual capture), OR is single-capture-via-bo_laksana correct (temporal/condition facts that aren't
  graph edges)? Re-decide each from first principles, do not inherit the audit's verdict.

## STEP 4 — Architectural options framing (NOT a decision — options for the native)

Frame (don't choose) the re-architecture options the map implies:
- Option A — EXTEND ga_structural to ingest the enriched/new assets + derive their relationships (re-open the
  writer's internal logic; NO orchestrator contract change; delete-then-insert rebuild). The "complete hub" option.
- Option B — leave ga_structural, have bo_laksana project the enriched assets DIRECTLY (native-grained) alongside
  ga_structural's relational rows (lean on dual-capture's second leg). The "thin hub + fat projection" option.
- Option C — hybrid per asset (some relationships belong in the hub, some project directly).
For each option: what relational value is gained/lost, the rebuild cost, the L1-is-authority/duplication
implications, and the effect on MSR signal richness. Tie each to the dual-capture model
([[feedback-bodha-dual-capture-model]]) and the L2 design philosophy (the graph is where deterministic-meets-deep,
invest hardest there).

---

## DELIVERABLE

`GA_STRUCTURAL_INGEST_MAP_v1_0.md`: Step-1 current-ingest table, Step-2 per-asset relational-value inventory,
Step-3 THE GAP MAP (the core artifact), Step-4 architectural options. Every claim code-cited or query-backed.
NO changes — this is the map the native decides the ga_structural re-architecture from. End with a one-page
summary: which enriched/new assets ga_structural does NOT currently weave in, the highest-value missing
relationships, any stale-duplication (ga_structural recomputing what an asset now owns canonically), and the
recommended architectural option WITH the reasoning (as a recommendation, not a decision).
