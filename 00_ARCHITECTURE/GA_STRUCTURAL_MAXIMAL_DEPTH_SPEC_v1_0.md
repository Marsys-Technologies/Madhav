---
artifact: GA_STRUCTURAL_MAXIMAL_DEPTH_SPEC_v1_0.md
canonical_id: GA_STRUCTURAL_MAXIMAL_DEPTH_SPEC
version: 1.0
status: CURRENT — native-ratified design (2026-06-18)
authored_by: Cowork 2026-06-18
purpose: >
  The definitive "how deep ga_structural goes" design. ga_structural = the PURE RELATIONAL GENERATOR built to
  MAXIMAL Tier-2 completeness: every deterministic relationship between 2+ entities, by a fixed rule, with NO
  life-meaning judgment. Governed by the three-tier boundary. This is the Phase-2 depth spec; Phase-1 (reference
  values + ingest the complete entity set, the Session-2 brief) is the prerequisite.
governing_principle: feedback-three-tier-relational-boundary + feedback-ga-structural-pure-relational-generator
---

# ga_structural — Maximal Relational Depth Spec v1.0

## §0 — The governing boundary (the line, made permanent)

Place ANY candidate by ONE test = (entity count) × (life-meaning judgment?):

| entities | meaning-judgment? | TIER |
|---|---|---|
| 1 | no | **L1 value-asset** (ga_strength/sensitive/nakshatra/condition/tajaka/positions/vargas) |
| 2+ | **no** | **ga_structural** ← everything in this spec |
| 2+ | **yes** (life-domain / salience / outcome / weight-of-evidence) | **L2 MSR (bo_*)** |

**ga_structural scope = ALL of (2+ entities, fixed rule, no meaning). Maximal Tier-2 completeness.** The depth
lives here (deterministic, meaning-free); the meaning lives in L2. The boundary is "fact vs meaning," NOT "simple
vs complex" — so EVERY deep/graph-theoretic relationship is ga_structural, however sophisticated.

**Anti-test (what ga_structural must NEVER do):** assign a life-domain ("this is your marriage"), rank salience
("most important"), claim an outcome ("strong career"), or weigh evidence toward a conclusion. The MOMENT a
computation maps a relationship to life-meaning, it has crossed into L2. ga_structural emits the relationship +
its objective properties; L2 maps it to meaning.

---

## §1 — The relational-depth AXES (the framework for completeness)

A chart's relationships have depth along 5 axes. Maximal ga_structural = complete along ALL 5:

- **Axis 1 — ORDER:** 1st (pairwise) → 2nd (chains) → Nth (network/graph properties). *Depth = beyond pairwise.*
- **Axis 2 — TYPE:** the full set of relationship KINDS (aspect, conjunction, exchange, dispositor, argala,
  sambandha, configuration, …). *Depth = every classical relationship type, none missing.*
- **Axis 3 — ARITY:** 2-entity → N-entity configurations (3+ grahas in mutual relationship as first-class).
  *Depth = n-way, not only pairwise.*
- **Axis 4 — VALENCE/PROVENANCE VECTOR:** every edge carries strength (referenced) + benefic/malefic valence +
  directionality + varga-provenance. *Depth = rich edges, not boolean exists/not.*
- **Axis 5 — META-RELATIONSHIP:** relationships ABOUT relationships (same edge across N vargas; convergence
  COUNTS; cycle membership). *Depth = the relational structure of the relationships themselves.*

---

## §2 — The COMPLETE Tier-2 relationship inventory (maximal target)

Every item below is (2+ entities, fixed rule, no meaning) → ga_structural. Grouped by axis. ✓=has today,
✗=missing/thin (the elevation), R=reference-value-from-canonical-owner.

### §2.1 — Pairwise relationships (Axis 1 order-1; Axis 2 types) — mostly HAS, complete the set
- Aspects: Parashari graha-drishti ✓ · special aspects (Mars 4/8, Jup 5/9, Sat 3/10) — confirm full ✓ · sign-aspect (rashi-drishti / Jaimini) ✓ · Tajik aspects (R from ga_tajaka) ✗→R.
- Conjunction (all pairs, NO orb-drop — emit wide-orb at low strength) ✓ (fix orb-drop).
- Parivartana / exchange — ALL types: Maha (kendra/trikona), Khala (3/6/10/11), Dainya (dusthana) — graded ✓ (confirm all 3 types).
- Graha-yuddha (planetary war) ✓ · combustion-relationship (R real-Sun from ga_positions) ✓.
- **Sambandha — the graded 4-fold relationship** (conjunction + mutual-aspect + exchange + mutual-reception),
  scored as a composite "how related are these two" ✗ ADD. (The classical true-relatedness metric.)
- Aspect VALENCE per edge (benefic/malefic-casting) + directionality (who aspects whom) ✗ ADD to every edge.

### §2.2 — Chains (Axis 1 order-2) — HAS, complete both witnesses
- Rashi-dispositor chain → terminus ✓ · **Nakshatra-dispositor chain** (R placements from ga_nakshatra) ✓
  (both kept — two witnesses). · Composite-dispositor strength (R from ga_strength) ✗→R.
- **Dispositor TREE** (full tree not just chain — branching, depth, who-disposits-whom forest) ✗ ADD.

### §2.3 — House/lord web (Axis 2 type; bhava relationships) — HAS matrix, deepen
- House-lord matrix (lord-in-house, lord-aspects-lord) ✓.
- **Bhava-to-bhava significance web** — lord of house X placed in / aspecting house Y, as the classical
  house-link (5th-lord in 9th = trikona link; 6/8/12 links) — as first-class relational edges ✗ ADD.
- **Karaka↔bhava concordance** — natural karaka (Jup=5th-things) vs the bhava-lord: do they agree or conflict?
  (a relationship between two significator SYSTEMS, fixed rule, no meaning) ✗ ADD.
- Argala + virodhargala (all 144) ✓ · **NET argala** (resolved = argala − virodhargala; which intervention
  wins) ✗ ADD.

### §2.4 — N-WAY configurations (Axis 3 arity) — MOSTLY MISSING, high value
- Yoga/dosha firings = n-way configs, catalog-driven (R catalog from L0's 144/79) ✓ (ga_structural is the single
  writer — see §4 fork).
- **Generic n-way configurations as first-class** — NOT only named yogas: "grahas {A,B,C} in mutual kendras",
  "all benefics in {trikonas}", "3+ grahas in one sign (stellium)", "kendra-trikona lord clusters" — emitted as
  `n_way_configuration` rows with their member fact_ids, INDEPENDENT of whether a named yoga matches ✗ ADD.
  (This is the structural realization of "capture the configuration even with no classical name.")
- **Uncatalogued-configuration** (a real config matching no catalog entry) ✗ ADD (the prior finding's Fix 4.2 —
  gap-detection; a config is present, no name fires → emit it so absence becomes presence).

### §2.5 — GRAPH-THEORETIC (Axis 1 order-N) — THE BIGGEST ELEVATION, mostly absent
All deterministic graph algorithms over the chart-graph (nodes=entities, edges=§2.1-2.4 relationships). No
acharya computes these by hand; all are meaning-free → ga_structural:
- **Final dispositor / chart center-of-gravity** (the node all chains terminate at) ✗ ADD.
- **Weighted centrality** per graha (degree + betweenness + eigenvector over the edge-weighted graph) ✗ ADD.
- **Parivartana / dispositor CYCLES** (A→B→C→A closed loops) ✗ ADD.
- **Path analysis** — shortest/all paths between any two significators (e.g. 5th-lord ↔ 7th-lord) as a relational
  chain ✗ ADD.
- **Connected components / clusters** (which grahas form a tightly-bound subgraph) ✗ ADD.
- Graph emitted as a queryable node+edge structure (so L2/MSR + the CGM consume it directly) ✗ ADD.

### §2.6 — VALENCE/PROVENANCE VECTOR (Axis 4) — enrich EVERY edge
Every relationship row, regardless of type, carries: `strength` (R from ga_strength) · `valence`
(benefic/malefic) · `directionality` · **`varga_provenance`** (the set of vargas this same relationship holds in
— D1 only vs D1+D9+D10 etc.) · `constituent_facts_array` (real fact_ids — L1-authority). ✗ ADD the full vector.

### §2.7 — META-RELATIONSHIPS (Axis 5) — relationships about relationships
- **Varga-provenance meta-edge** — "relationship R holds across vargas {D1,D9,D10}" as its OWN fact (multi-varga
  confirmation = the relational structure of the relationship; deterministic, no meaning) ✗ ADD.
- **Convergence COUNT** (purely the count: N edges incident on house/sign/graha X) — the COUNT is meaning-free
  (Tier-2); mapping X→life-domain is L2. Emit the raw counts; L2 maps to domains. ✗ ADD (counts only).
- **Contradiction PAIR detection** (two edges with opposite valence on the same target) — detecting the
  opposed-pair is structural (Tier-2); judging which "wins for the life-domain" is L2. Emit the pairs; L2 weighs. ✗ ADD (pairs only).

---

## §3 — The L1/L2 split table (the hard cases, ruled)

| Candidate | ga_structural emits (Tier-2, no meaning) | L2 MSR does (Tier-3, meaning) |
|---|---|---|
| Final dispositor | the node + that chains terminate there | "your chart's center of gravity means…" |
| Centrality | the centrality NUMBER per graha | "the MOST CONSEQUENTIAL planet in your life" |
| Net argala | resolved argala value on a house | "your career house is blessed" |
| Convergence | the COUNT (N edges on house 7) | "house7=marriage → strong marriage prospects" |
| Contradiction | the opposed-edge PAIR | "marriage is supported but afflicted → caution" |
| Path 5th↔7th lord | the path exists + its hops | "children will shape your marriage" |
| Varga-provenance | "holds in D1+D9+D10" | "very reliable because multi-varga" (salience) |
| Sambandha | the 4-fold grade Sun↔Saturn | "Sun-Saturn tension defines your father-relationship" |

**Pattern: ga_structural emits the deterministic relational FACT; L2 adds the life-MEANING.** The depth is
entirely in L1; L2 never re-computes a relationship, only interprets ga_structural's.

---

## §4 — Single-writer rulings (no duplication; each category one owner)
- `yoga_label` / `dosha_label` (relational configs) → ga_structural is the SOLE writer (catalog-driven from L0).
  ga_yoga = per-chart firing-DETAIL or repointed; never duplicates the category. **FLAG for native confirm before L2 bo_samskara.**
- `aspect_tajik` relational configs → ga_structural; ga_tajaka owns the tajik VALUES (hadda lords). ga_structural references them.
- `nakshatra_dispositor` → ga_structural generates the CHAIN (relationship); ga_nakshatra owns the placements (values).
- vargottama → placement referenced from chart_divisionals; ga_structural generates the vargottama-relationship.

---

## §5 — Build phasing (why two phases, the dependency)
- **PHASE 1 (Session-2 brief, prerequisite):** pure-relational-generator re-architecture — reference all values
  from canonical owners + generate EXISTING relationships over the COMPLETE ingested entity set + DAG (ga_structural
  last, depends_on all value-assets, cascade). The complete graph must EXIST first.
- **PHASE 2 (this spec):** add the missing depth — sambandha, dispositor-tree, bhava-web, karaka-concordance,
  net-argala, n-way + uncatalogued configs, the FULL graph-theoretic layer (final-dispositor/centrality/cycles/
  paths/components), the valence-provenance vector on every edge, and the meta-relationships (varga-provenance,
  convergence-counts, contradiction-pairs). **Phase 2 depends on Phase 1** (can't compute graph-centrality or
  multi-varga-provenance until every entity + every per-varga relationship is ingested).

Each Phase-2 relationship = a versioned deterministic formula (sambandha_formula_v1, centrality_formula_v1, …) —
"why is this the center / why grade 3?" always has a reproducible auditable answer (the research-instrument
property; an acharya reviews the METHOD).

---

## §6 — Acceptance (maximal Tier-2 completeness)
ga_structural is COMPLETE when: every relationship type in §2 is generated; the graph-theoretic layer exists as a
queryable node+edge structure; every edge carries the full valence/provenance vector with real constituent
fact_ids; n-way + uncatalogued configs are emitted; meta-relationships (varga-provenance, convergence-counts,
contradiction-pairs) exist as facts; ZERO values are computed inline (all referenced); and NOTHING crosses into
life-meaning (the L2 anti-test holds). At that point L2 MSR is a pure interpretive transform over a complete,
deep, deterministic relational graph — your stated objective: every possible depth of relationship captured in L1.

*End. Maximal Tier-2: capture every deterministic 2+-entity relationship to full graph-theoretic depth; leave
all life-meaning to L2. The boundary (fact vs meaning) makes "as deep as it goes" precise and the L1/L2 line permanent.*
