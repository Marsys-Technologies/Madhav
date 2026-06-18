---
artifact: CLAUDECODE_BRIEF_FOUNDATION_SESSION_2_GA_STRUCTURAL
type: CLAUDECODE_BRIEF (STAGED — promote to project-root CLAUDE_BRIEF.md AFTER Session 1 status:COMPLETE)
version: 2.0
status: STAGED (do not run until Session 1 is COMPLETE + prod-verified)
authored_by: Cowork 2026-06-18 (v2.0 — rebuilt around the "pure relational generator" principle)
session_type: claude_code_autonomous (documented-defaults; native reviews at end)
phase: pre-L2 — ga_structural re-architecture into a PURE RELATIONAL GENERATOR
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
depends_on: Session 1 COMPLETE (catalogs settled bg_yogas=144/bg_doshas=79 + bg_rules mined; prod-verified)
may_touch:
  - platform/python-sidecar/ga_writers/ga_structural_writer.py
  - platform/python-sidecar/pipeline/orchestrator/writers/ga_structural.py     # thin adapter / depends_on only
  - platform/scripts/seed/asset_registry_seed.ts                               # ga_structural depends_on update
  - platform/migrations/**
  - 00_ARCHITECTURE/**
must_not_touch:
  - platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py        # bo_laksana PROJECTION = later (L2 Wave 3)
  - any L2 bo_* asset
  - the FROZEN orchestrator contract (writer-internal logic + depends_on metadata only — NO contract change)
acceptance_criteria:
  - ga_structural computes ZERO values; every value is referenced from its canonical L1 owner by fact_id
  - ga_structural generates relationships over the COMPLETE referenced value-set (all enriched assets ingested)
  - ga_structural depends_on all value-assets; upstream rebuild cascades it stale (DAG update)
  - rebuilt ONCE against settled catalogs; FORENSIC 7/7; endpoint-green; floor = achieved
---

# CLAUDE CODE — Session 2: ga_structural → PURE RELATIONAL GENERATOR (autonomous; documented defaults)

**PRECONDITION: only run if Session 1 is `status: COMPLETE` and prod-verified.** Read CLAUDE.md §C +
`GA_STRUCTURAL_INGEST_MAP_v1_0.md` + the memory `feedback-ga-structural-pure-relational-generator` FIRST.

## THE ONE PRINCIPLE THIS SESSION IMPLEMENTS (native-ratified)

**ga_structural is a PURE RELATIONAL GENERATOR. It computes NO values. It REFERENCES every raw value from that
value's CANONICAL OWNER (the dedicated L1 asset) by fact_id, and GENERATES only RELATIONSHIPS over those
referenced values.** Every change below is one rule: **is this a VALUE or a RELATIONSHIP? VALUE → reference the
canonical owner, never compute/store/proxy. RELATIONSHIP → ga_structural generates it from referenced values.**

This dissolves the dual-compute problem: ga_structural keeps NO private copy of any value, so nothing can diverge;
it reads canonical values + generates the edges fresh each build. NO orchestrator contract change (writer-internal
logic + depends_on metadata only — HALT if a contract change seems needed). bo_laksana PROJECTION is LATER —
do NOT touch bo_laksana.

**STANDING RAILS:** computed-and-cited; canonical-or-floor; deterministic-first; L1-is-authority (reference
fact_id, NEVER restate/recompute a value); L1 delete-then-insert idempotency; surgical migration + ledger;
seed-consistency; ENDPOINT-verify (`?chart_id=482012f1`); floors = ACHIEVED (query live per-category counts at
execution — never build against a number from any doc); only 482012f1; FORENSIC 7/7.

---

## PART 0 — Q1 yoga_label/ga_yoga fork: INVESTIGATE FIRST (read-only), confirm, THEN build (native-ruled GATE)

**Do this BEFORE any rebuild. It gates Part B's yoga ruling.** ga_structural is set to become the SOLE writer of
`yoga_label` (a yoga firing = relational config = ga_structural's per the three-tier boundary). But ga_yoga ALSO
writes yoga_label today, and L2 bo_samskara reads ga_yoga. Confirm the canonical-source decision on EVIDENCE, not
the default:
1. **Head-to-head (read-only):** query ga_structural's `yoga_label` (catalog-fired against the now-144-core
   bg_yogas — audit showed ~409 rows) vs ga_yoga's `ga_yoga_firings` (5 rows; its evaluator has `return None`
   stubs, lines 812-825). Compare: same yogas? does ga_structural's carry richer detail (real constituent
   fact_ids, per-ayanamsha, citations)? does ga_yoga produce ANYTHING ga_structural does not (e.g. a firing
   semantic ga_structural lacks)?
2. **Confirm or override the default:** DEFAULT = ga_structural is canonical (richer, catalog-driven, single
   relational source); ga_yoga becomes per-chart firing-DETAIL or is repointed (bo_samskara reads ga_structural's
   yoga_label). PROCEED on the default ONLY IF the head-to-head confirms ga_structural is a superset / richer and
   ga_yoga adds nothing unique. If ga_yoga HAS a unique semantic → HALT and flag for native (don't silently drop it).
3. Same investigation for `aspect_tajik` (ga_structural vs ga_tajaka's 1,200 tajik_hadda_lord): confirm
   ga_structural generates the tajik RELATIONSHIPS referencing ga_tajaka's VALUES; ga_tajaka isn't dropping a
   relationship ga_structural won't regenerate.
Output a short `GA_STRUCTURAL_YOGA_FORK_FINDING.md` with the head-to-head + the confirmed decision. THEN proceed
to Part A–E. (This replaces the prior "apply default + flag" with "investigate → confirm → build" per native ruling.)

---

## PART A — STOP COMPUTING VALUES (replace every inline value with a canonical reference)

Audit `ga_structural_writer.py` for EVERY place it computes/derives a VALUE inline, and replace it with a
reference to the canonical owner's fact_id. Known sites (confirm + find any others by reading the writer):

- **Per-varga strength / dignity PROXY → reference ga_strength.** ga_structural currently computes inline dignity
  proxies for edge-weights. STOP. Reference ga_strength's authoritative per-varga Shadbala + ashtakavarga_bindu_
  per_varga values as the edge-weights. (`_build_shadbala_extension_rows`, `_build_vimsopaka_ext_rows`,
  `_build_anubindu_rows`, and any dignity-proxy in the aspect/relationship builders — these should REFERENCE, not
  RE-DERIVE.)
- **vargottama placement → reference chart_divisionals.** Drop the inline longitude-arithmetic recompute; read the
  authoritative placement; generate only the vargottama-RELATIONSHIP.
- **aspect_tajik hadda-lords → reference ga_tajaka.** Stop recomputing tajik values; reference ga_tajaka's 1,200
  tajik_hadda_lord rows; generate the tajik aspect-RELATIONSHIPS over them.
- **nakshatra placements → reference ga_nakshatra.** Stop computing its own nakshatra positions; reference
  ga_nakshatra's canonical placements. (The dispositor CHAIN it generates over them stays — that's a relationship,
  PART B.)
For each: the relationship row's `constituent_facts_array` must carry the REAL fact_id of the canonical value it
referenced (the L1-is-authority back-reference must resolve). Verify a sample edge-weight resolves to a
ga_strength fact_id, not a recomputed number.

## PART B — GENERATE RELATIONSHIPS OVER THE COMPLETE REFERENCED VALUE-SET (ingest what it's blind to)

ga_structural ignores enriched assets. Make it reference them and generate their relationships:

- **GAP 1 — enriched ga_sensitive (6 Tier-1 categories).** `_load_special_points` (line 2847) reads ONLY
  `fact_category='upagraha_position'`. Extend it to ALSO reference: `sensitive_point_gulika_mandi`,
  `sun_derived_upagraha`, `special_lagna`, `esoteric_point_sphuta_fertility`, `esoteric_point_yogi`, `arudha_pada`
  (confirm exact category names on prod). Then `_build_special_point_relationship_rows` generates the graha↔point
  aspect + conjunction RELATIONSHIPS over all of them. (Highest ROI — mostly one loader change.)
- **GAP 3 — per-varga avasthas from ga_condition.** Reference ga_condition's per-varga baladi/deepta avastha
  values; the composite-state RELATIONSHIP generates over them (not D1-only).
- **Dispositor chains (both rashi AND nakshatra) — relationships, generate both.** rashi-dispositor chain over
  referenced sign-placements; nakshatra-dispositor chain over referenced ga_nakshatra placements. Both are
  RELATIONSHIPS ga_structural generates — keep BOTH (two genuine witnesses), no divergence (both read canonical
  placements, neither stores a placement-value).
- **yoga_label / dosha_label — relational configurations, ga_structural generates (catalog-driven from L0's now-
  complete 144/79).** A yoga firing IS a relationship (a configuration of referenced placements). ga_structural
  generates it. **CONSEQUENCE for the deferred fork (DEFAULT, flag for native override):** ga_yoga must NOT
  duplicate yoga_label — ga_yoga owns per-chart firing-DETAIL or is repointed; ga_structural is the single writer
  of the yoga_label RELATIONAL configuration. (Same logic: aspect_tajik relational config = ga_structural;
  ga_tajaka owns the tajik VALUES.) FLAG these prominently in the close for native override before L2 bo_samskara.

## PART C — DAG: ga_structural becomes the LAST L1 asset (native-ratified)

Because ga_structural now references every value-asset, it is strictly DOWNSTREAM of all of them. Update the
orchestrator DAG / `asset_registry.depends_on` (+ seed) so ga_structural `depends_on` = [ga_positions, ga_vargas,
ga_strength, ga_sensitive, ga_condition, ga_nakshatra, ga_tajaka, ga_dashas, ga_panchanga, + any other value-
producer it references]. Effect: ga_structural always builds AFTER them, and rebuilding ANY of them CASCADES →
flags ga_structural stale/for-rebuild (closes the staleness gap — relationships never sit on stale referenced
values). This is metadata (depends_on) — NOT an orchestrator contract change. Verify the cascade: rebuild an
upstream value-asset, confirm ga_structural flags stale.

## PART D — REBUILD ONCE + VERIFY

Rebuild ga_structural for 482012f1 ONCE against the Session-1-settled catalogs. Verify via ENDPOINT:
- ga_structural lit; FORENSIC 7/7 holds.
- ZERO inline-computed values remain (spot-check: every edge-weight + placement in a sample of rows resolves to a
  canonical fact_id; no recomputed proxy).
- The enriched categories now generate relationship rows (sensitive Tier-1 edges, per-varga avastha composite,
  both dispositor chains).
- depends_on updated; cascade works.
- floor = new achieved count (migration + seed).
NO bo_laksana change.

## PART E — CLOSE

Write `GA_STRUCTURAL_REARCHITECTURE_CLOSE.md`: the value→reference conversions (Part A), the relationships now
generated over the complete set (Part B), the DAG/depends_on + cascade (Part C), the rebuild verification
(endpoint JSON + FORENSIC 7/7), and — FLAGGED PROMINENTLY for native override — the yoga_label/aspect_tajik
single-writer default decisions. Update CURRENT_STATE + OPEN_ITEMS. Set this brief `status: COMPLETE`.

**NEXT after this:** bo_laksana PROJECTION wiring (project ga_structural's now-complete relational surface into
MSR signals) + L2 Bodha open — a later session, NOT this one.

---

## DOCUMENTED DEFAULTS (applied autonomously; native may override at review)
- ga_structural computes NO values — references all, generates only relationships. (The governing principle.)
- VALUE → reference canonical owner's fact_id; RELATIONSHIP → ga_structural generates. (The decision rule for every case.)
- Both dispositor chains (rashi + nakshatra) kept — both are relationships, no divergence.
- yoga_label single-writer = ga_structural (relational config); ga_yoga = firing-detail/repointed. aspect_tajik
  single-writer = ga_structural; ga_tajaka owns tajik values. FLAG both for native override before L2 bo_samskara.
- ga_structural = LAST L1 asset, depends_on all value-producers, cascade-on-upstream-rebuild.
- bo_laksana projection = OUT OF SCOPE (later). Touch nothing in bo_laksana. No orchestrator contract change.
