---
artifact: CLAUDECODE_BRIEF_BO_KARANAJALA_BIMBA_v1_0.md
canonical_id: BO_KARANAJALA_BIMBA_BRIEF
version: 1.2
status: FOR_NATIVE_REVIEW (Batch 2 — the CGM graph; the deepest-built asset)
v1_2_changes: >
  CROSS-SUBSYSTEM EDGES (native 2026-06-19 — closes a real gap: the graph's edge types were STRUCTURAL, so
  subsystems (nakshatra/medical/vastu/...) sat in the graph as nodes but were only INDIRECTLY connected via a
  shared structural entity — cross-subsystem relationships were not first-class/retrievable). §XS adds a
  cross-subsystem EDGE family, computed at L2 from existing L1 subsystem facts + L0's classical cross-discipline
  mappings (VERIFIED present: bg_nakshatra_medical = nakshatra→body-part; graha→dosha/dhatu; etc.). Bounded to
  GENUINE ties (shared-root or classically-defined link) — never every-pair noise. This makes cross-subsystem
  relationships STORED + retrievable, so bo_anveshana MINES them (not re-derives). No L1 reopening — L2 does the join.
v1_1_changes: >
  Folds in the JUDGMENT-substrate strategy (v1.1 FROZEN). The graph gains TWO strategic roles beyond its base:
  (1) it FEEDS the weight-of-evidence engine (its contradictions + convergence-paths are inputs to the CDLM
  domain ledgers — Move 1); (2) it IS the anti-tunnel-vision SAFETY NET (Move 5 §5.A): the graph-sweep that
  finds any high-salience signal reaching a domain's significators by ANY path — even one a lens template never
  anticipated. See §JUDGMENT.
authored_by: Cowork (grounded in live CGM schema + storage architecture) 2026-06-19
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
scope: >
  bo_karanajala (CGM edges + sub_graphs + motifs + topology + paths + bodha_contradictions) AND bo_bimba
  (CGM nodes). ONE brief because A12 is ONE igraph compute: a single heavy writer builds the whole graph;
  bo_bimba is the nodes-FACE on the same compute (per native decision — Cowork rec accepted). Depends on bo_laksana.
data_plane: ALWAYS prod via Cloud SQL Auth Proxy (127.0.0.1:5433)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
governing:
  - L2_BODHA_SCHEMA_REDESIGN_v1_0.md (the schema contract) + L2_BODHA_STORAGE_ARCHITECTURE_v1_0.md (S1/S4/S5)
  - L2_BODHA_OVERALL_APPROACH_v1_0.md (two pillars) + A12_CGM_SPEC_v1_0.md
  - feedback memories: bodha-completeness-axes (DEPTH=full chain, WIDTH=entity types), l1e-full-relationship-graph
  - ga_structural v2.0 — it ALREADY computed graph_centrality/dispositor_tree/significator_path/chart_center_of_gravity per-varga (PROJECT these, don't recompute)
  - ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2 (FROZEN WriterBase contract)
target_files:
  - platform/python-sidecar/pipeline/orchestrator/writers/bo_karanajala.py (the heavy igraph writer — builds everything)
  - platform/python-sidecar/pipeline/orchestrator/writers/bo_bimba.py (thin nodes-face on the same compute)
  - platform/python-sidecar/bodha_writers/formulas.py (centrality_formula_v1 — present; do not change)
  - migration(s): redefine the 7 CGM tables + bodha_contradictions to the enriched schema (empty — free)
  - platform/src/lib/retrieval/registry/layers/L2_bodha/ (CGM retrieval tools incl. the recursive-traversal primitive)
must_not_touch: FROZEN orchestrator contract; ga_* writers; bo_laksana; other fan-out writers.
---

# bo_karanajala + bo_bimba — the CGM graph (the deepest-built asset)

## §0 — What this is + why it's one writer
The CGM (Chart Graph Model) is the typed, signed, weighted, multi-entity relationship GRAPH of the chart —
the structure the synthesis LLM TRAVERSES to reason, not just look up. A12 is ONE igraph in-memory compute:
build the graph once, emit nodes + edges + sub_graphs + motifs + topology + paths together. **bo_karanajala**
is the heavy writer that does the whole compute + owns edges/sub_graphs/motifs/topology/paths/contradictions.
**bo_bimba** is a THIN nodes-only face that registers `bodha_cgm_nodes` from the same compute (it does not
recompute the graph). Build DEEPEST here — per the design philosophy, the graph is where deterministic meets deep.

## §1 — Non-negotiables
Deterministic-first (igraph compute is deterministic; no LLM); no audience tier; no silent drops; per-chart
isolation; **real fact_ids / signal_ids, never mock**; FROZEN orchestrator contract (`@register('bo_karanajala')`
+ `@register('bo_bimba')` WriterBase on ctx.db_conn, never commits, no asset_throughput); **Trap 1** (every edge
REFERENCES its underlying MSR signal_ids + L1 fact_ids, never restates a value); **Trap 2** (centrality_formula_v1
+ weight_formula — versioned deterministic; no narrative). count_sql = summed across all CGM tables; floors aspirational.

## §2 — Preconditions
1. Proxy up; main == prod; max migration number verified.
2. **bo_laksana built + anti-drift spine PASSED** (the graph is built FROM MSR signals — a broken root poisons the graph).
3. ga_structural v2.0 present (its per-varga graph-theoretic categories are the PROJECTION SOURCE for centrality/paths).
4. Apply the enriched CGM-tables migration (§3 + §ELEVATION). Empty tables — redefine freely. `igraph` available in the sidecar venv.

## §3 — The graph build (the core compute)

### §3.1 — NODES (bo_bimba face) — multi-entity (WIDTH)
Node set is NOT planet-only. Build a node per: graha (9), bhava/house (12) + house-lord, sign/rashi (12),
nakshatra (27) + nakshatra-lord, special points (arudhas/AL, chara+sthira karakas, karakamsa/swamsa, upagrahas,
sahams, special lagnas), AND **configurations as first-class nodes** (each fired yoga/dosha/conjunction →
a node; carries `msr_signal_id`). Per (chart, ayanamsha, snapshot). Populate ALL the schema's node columns —
`node_type`, `node_subject`, `strength_score`, `dignity_state`, the wide centrality set (§3.4), domain, hub,
tradition presence, cross_ayanamsha_presence_score, node_embedding_vec (the embedding model per the protocol).
**Every node also carries `source_subsystem`** (from the MSR signal's source_subsystem tag — bo_laksana §6) — this
is the axis the cross-subsystem edges (§XS) and bo_anveshana's per-subsystem mining key on. A node un-tagged with
its subsystem is a build error.

### §3.2 — EDGES (bo_karanajala) — the full value-vector
An edge per relationship: aspect (Parashari/Jaimini/Tajik), conjunction/co-tenancy, lordship/dispositor,
nakshatra-lordship, argala/virodha-argala, occupancy (graha-in-house/-sign/-nakshatra), participation
(graha→config), vargottama/cross-varga-correspondence, combustion/graha-yuddha, significator (KP/karaka),
comparative-strength, reinforce/contradict (config↔config). **Every edge carries the FULL VALUE VECTOR**
(schema columns + the elevation adds): `direction` (directed/mutual), `computed_strength` (weight_formula_version),
`relationship_class`, `edge_properties_jsonb`, `underlying_msr_signal_ids_array` (the Trap-1 reference),
`cancelled_flag` + `cancelled_by_jsonb`, `cross_ayanamsha_edge_stability_score`, `present_in_traditions_array`,
edge_betweenness, + ELEVATION: `valence` (benefic/malefic/mixed), `affected_domains_array`, `weight_varga_source`.

### §3.3 — Sub-graphs, motifs, topology
- `bodha_cgm_sub_graphs` — canonical sub-graphs / ego-networks / clusters (node+edge id arrays, density, centroid, classical_archetype_match, GraphML/GEXF export).
- `bodha_cgm_motifs` — the ~30–50 classical motif library detected over the graph (involved nodes/edges, motif_strength, classical_citation_id, fingerprint_hash).
- `bodha_cgm_chart_topology_summary` — the chart-level graph signature (hubs, central nodes, diameter, density, SCC count, dispositor_cycle, hub_dominance, fragmentation, per_graha_story_arc, topology_embedding_vec, GraphML/GEXF full export).

### §3.4 — Centrality computed WIDE at build (storage architecture S4)
Compute + store the FULL metric set the schema provides, not a subset: degree_in/out, betweenness, eigenvector,
pagerank, clustering_coefficient, closeness, harmonic, **core_number (k-core)**, + composite via
centrality_formula_v1. So a new structural question never forces a rebuild. (ga_structural already computed
graha_centrality per-varga — PROJECT it where present; compute the rest over the full multi-entity graph here.)

### §3.5 — PATHS = the DEEP relationship chains (DEPTH — the centerpiece)
`bodha_cgm_paths` holds the chains. Build them to FULL ASTROLOGICAL DEPTH (native decision — no hop cap):
- **dispositor chains** to their natural terminus (self-disposited graha = `is_final_dispositor`), with
  `convergence_count` (how many chains converge there = the chart's center of gravity). ga_structural's
  dispositor_tree + chart_center_of_gravity PROJECT here.
- **significator paths** (ga_structural significator_path projects here).
- **heterogeneous deep chains** — graha→sign-lord→nakshatra-lord→house→aspecting-graha→config→… following ONLY
  defined edges (the §3.2 edge types), each hop a genuine classical tie, to terminus. Store the full ordered
  `path_node_ids_array` + `path_edge_ids_array` + `path_length` + `path_strength` (product of edge strengths).
- **GUARD: cycle-detection only** (a chain revisiting a node closes there — the cycle IS the terminus; prevents
  infinite walk; NOT a depth cap). Depth bounded by the astrology, not a number.

### §3.6 — bodha_contradictions (owned here)
Contradiction-pairs (signals in structural tension) as first-class rows: signal_a/signal_b, tension_basis_jsonb,
tension_class, combined_salience, resolution_hint_jsonb. The drift guardrail + the "weight of evidence" surface.

## §4 — Anti-drift + verification (prove the graph is sound)
1. **Every edge's `underlying_msr_signal_ids_array` resolves to real bodha_msr_signals rows** (Trap 1; zero unresolved).
2. **Every node's `msr_signal_id` (where set) + `configuration_constituents_array` resolve.**
3. **Acharya check:** the top-centrality node + final-dispositor are astrologically coherent (e.g. for the native, Rahu is the top-degree hub in D1 per ga_structural §5 — the CGM must agree).
4. **Cross-ayanamsha:** edge/node stability scores populated (5/5 vs 2/5).
5. Idempotent (delete-then-insert per chart×ayanamsha×snapshot); no silent drops; FORENSIC unaffected.

## §5 — Retrieval (the retrievability half — built WITH the asset)
Extend `L2_bodha/`:
- node/edge/motif/topology/path fetch tools (chart/ayanamsha/snapshot/type filtered, paginated, full provenance return).
- **THE RECURSIVE-TRAVERSAL PRIMITIVE (storage S1):** `query_chart_graph_traverse(from_node, to_node|max_depth,
  edge_types[])` — a `WITH RECURSIVE` CTE over bodha_cgm_edges returning ad-hoc chains the LLM requests (NOT only
  pre-materialized paths), with a cycle-guard in the CTE. This is graph-DB-like traversal staying in Postgres.
- node semantic search (HNSW on node_embedding_vec); topology similarity (HNSW on topology vec).
- **`query_cross_subsystem(chart, entity|subsystem_pair?)`** — returns the cross-subsystem edges (§XS): "what
  cross-subsystem relationships involve Saturn / the 4th house" → the nakshatra↔medical↔career ties with their
  basis + provenance. This makes the cross-discipline relationship DIRECTLY retrievable (not only surfaced by discovery).
- coverage gate extended: every CGM table reachable; the cross-subsystem edge family reachable.

## §6 — Acceptance
- [ ] One igraph compute builds nodes+edges+sub_graphs+motifs+topology+paths+contradictions; bo_bimba is the nodes-face.
- [ ] Multi-entity nodes (WIDTH): grahas+houses+signs+nakshatras+special-points+CONFIGS; **every node carries source_subsystem** (no untagged node).
- [ ] **§XS CROSS-SUBSYSTEM EDGES:** the cross_subsystem_* edge family present (shared-root / classical-cross-discipline / shared-domain), each with cross_subsystem_basis + cited shared-entity/mapping fact_id; **noise guard holds** (edge count bounded; spot-check NO arbitrary every-pair edges); computed at L2 from L1 facts + L0 mappings (bg_nakshatra_medical etc.), no L1 reopening.
- [ ] Full edge value-vector incl. valence + affected_domains + weight_varga_source.
- [ ] Centrality computed WIDE (all metrics incl. k-core); ga_structural per-varga centrality/paths PROJECTED.
- [ ] **Deep chains to terminus (DEPTH): full-length, heterogeneous, cycle-guarded, no hop cap; final-dispositor + convergence_count present.**
- [ ] bodha_contradictions first-class.
- [ ] Anti-drift: every edge/node reference resolves to real MSR signals; acharya coherence check passes.
- [ ] Retrieval: fetch tools + the RECURSIVE-TRAVERSAL primitive + semantic/topology search; coverage gate green.
- [ ] Embedding protocol honored (shared model constant, stamped, 768-dim HNSW). FROZEN contract; migration fresh; summed count_sql.

---

# §XS — CROSS-SUBSYSTEM EDGES (the graph connects DISCIPLINES, not just structural entities)
**The gap (native 2026-06-19):** the graph's edge types (aspect/conjunction/dispositor/lordship/argala/...) are
STRUCTURAL — they connect grahas/houses/signs. So nakshatra, medical, vastu, yoga, ashtakavarga nodes sit in the
graph but are only INDIRECTLY connected (via a shared graha). A cross-subsystem RELATIONSHIP ("this nakshatra
vulnerability co-occurs with this medical weakness") is not a first-class, retrievable edge — only latent. Fix:
add a CROSS-SUBSYSTEM EDGE FAMILY, computed at L2.

**Where the cross-discipline links come from (VERIFIED — grounded, not invented):** the classical cross-discipline
mappings already live in L0: `bg_nakshatra_medical` (nakshatra→body-part), graha→dosha/dhatu/organ (ga_medical's
L0 source), and the analogous vastu/deity mappings. **CGM computes the cross-subsystem edges AT L2** by joining the
existing L1 subsystem facts through these L0 classical mappings. NO L1 reopening; L2 does the cross-discipline join.

**The edge types (bounded to GENUINE ties — NEVER every-pair noise):**
- **shared-root edge** — two subsystem-findings that trace to the SAME root entity (Saturn is a nakshatra
  vulnerability AND a medical body-part affliction AND a D10 career affliction → edges connecting those findings,
  citing the shared Saturn fact_id). This is the workhorse — deterministic, anti-drift-clean (cites the shared root).
- **classical-cross-discipline edge** — a tie DEFINED in the L0 classical corpus (Moon's nakshatra → its
  body-part via bg_nakshatra_medical; a graha → its vastu direction). The link is classically real, not statistical.
- **co-occurrence edge** — two subsystem-findings affecting the same house/domain (a vastu directional weakness +
  a structural affliction both hitting the 4th/career) — bounded to a SHARED house/domain, not arbitrary pairs.
**THE NOISE GUARD (load-bearing):** a cross-subsystem edge exists ONLY where there is a shared-root, a
classically-defined link, or a shared house/domain. Connecting every nakshatra fact to every medical fact = millions
of meaningless edges = FORBIDDEN. Each edge carries `cross_subsystem_basis` (which of the three) + the shared
entity/mapping fact_id (Trap 1). `edge_type = cross_subsystem_*`; the two endpoint nodes carry their `source_subsystem`.

**Acceptance addition:** cross-subsystem edges present, each with a genuine basis (shared-root / classical / shared-
domain) + cited provenance; NO every-pair noise (edge count bounded; spot-check no arbitrary pairs); retrievable
directly (a tool returns "what cross-subsystem relationships involve Saturn / the 4th house"). This is what
bo_anveshana MINES for its cross-subsystem CROWN-JEWEL discoveries (it no longer re-derives them — they're stored).

---

# §JUDGMENT — the graph's two strategic roles (FROZEN strategy v1.1)

## §JG.1 — The graph FEEDS the weight-of-evidence engine (Move 1)
The CGM is not an end in itself — it is the strongest INPUT to the domain evidence ledgers (CDLM/bo_sangati).
Ensure the graph emits what the ledgers need:
- **`bodha_contradictions`** (owned here) IS the "opposing evidence" surface — each pair feeds the ledger's
  oppose-side with its tension_basis + combined_salience.
- **convergence PATHS** — `bodha_cgm_paths` where multiple chains converge on one significator/domain = the
  "supporting evidence chains" the ledger weighs. Tag each path with the domain(s) it serves.
- **INDEPENDENCE evidence** — the ledger must avoid double-counting; the graph HELPS by exposing when two
  signals share an underlying node/edge (i.e. NOT independent). Expose `shared_substructure` so bo_sangati can
  dedup deterministically. (This is the graph paying off the independence-dedup in strategy §1.A.)

## §JG.2 — The graph IS the anti-tunnel-vision SAFETY NET (Move 5 §5.A)
The lens (bo_drishti) must never lose a far-from-template-but-significant signal. **The graph is the mechanism
that guarantees this.** Provide a deterministic capability the lens calls:
- **domain-reach query:** given a domain's significators (e.g. career → 10th-lord node + Saturn/Sun karaka
  nodes), return EVERY signal/node that reaches them by ANY relationship path (the recursive-CTE traversal,
  S1), regardless of whether a template anticipated it. This is THE wildcard sweep — the graph catches what
  the template misses.
- ensure high-salience nodes/edges are never pruned from the graph (no-drop); the safety net only works if the
  outlier is IN the graph to be found. A signal high in salience but low in template-fit MUST still be a node.
- expose `non_template_reachability` so the lens can flag a reaching-but-unexpected signal `non_template_significant`.
This is WHY we invest hardest in the graph: it is both the depth engine AND the completeness safety net.

---

# §ELEVATION — maximal depth + width + retrievability for the graph
*(Beyond the base. The schema is already strong; these fill the gaps for MAXIMAL. Each tagged.)*

- **G-D1 [depth] Path STRENGTH + WEAKEST-LINK, not just product.** path_strength = product of edge strengths is
  good, but ALSO store the weakest-link edge (a chain is only as strong as its weakest tie — acharya reasoning).
  Add `weakest_edge_id` + `weakest_edge_strength` to paths. Lets the LLM say "this chain breaks at X."
- **G-D2 [depth] Path VALENCE accumulation.** As a chain runs, benefic/malefic edges accumulate — store the
  chain's net valence + the turning points (where it flips benefic↔malefic). High narrative value.
- **G-D3 [depth] Multi-varga chain persistence.** A chain holding across many vargas is stronger than a D1-only
  one. Store `chain_varga_persistence_count`. (ga_structural is all-30-varga — this is computable.)
- **G-W1 [width] Sign + nakshatra as full nodes with their own edges,** not just labels on graha nodes — so
  "what relates to Scorpio / to Jyeshtha" is a first-class graph query.
- **G-W2 [width] Bhava-to-bhava edges via lords** (10th-lord in 5th → house10—house5 edge) — the house-reading spine.
- **G-W3 [width] Argala as a signed directional sub-graph** (intervention + counter-intervention as its own typed edges).
- **G-R1 [retrievability] "Reasoning chain" return shape.** The traversal tool returns each chain as an ORDERED,
  CITABLE, human-narratable sequence (node→edge→node with labels + fact_id per hop) — the LLM narrates the
  MECHANISM, not just endpoints.
- **G-R2 [retrievability] Sub-graph by domain.** Retrieve the sub-graph for a domain ("the career sub-graph") in
  one call — nodes+edges+paths touching that domain, pre-filtered.
- **G-R3 [retrievability] Graph-diff across ayanamshas.** Expose which edges/nodes are stable vs ayanamsha-specific,
  so the LLM can weight robust structure over fragile.
- **G-X1 [completeness] Coverage manifest.** Emit per-snapshot node/edge/path/motif counts + "every MSR signal is
  represented by ≥1 node or edge" check, so a silent graph gap is visible at build, not at the eval harness.

---
*End of BO_KARANAJALA_BIMBA v1.0. One igraph compute → the full multi-entity (WIDTH) typed/signed/weighted graph
with the full edge value-vector; centrality computed WIDE (S4); deep heterogeneous chains to terminus (DEPTH, no
hop cap, cycle-guard); sub-graphs/motifs/topology/contradictions; anti-drift edges referencing MSR signals;
retrieval incl. the recursive-CTE traversal primitive (S1) + semantic/topology search. ELEVATION adds path
weakest-link/valence/varga-persistence, sign/nakshatra/bhava/argala width, reasoning-chain + domain-subgraph +
graph-diff retrieval, coverage manifest. The deepest-built asset — invest hardest here.*
