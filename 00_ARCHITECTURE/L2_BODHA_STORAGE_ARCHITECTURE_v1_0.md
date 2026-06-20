---
artifact: L2_BODHA_STORAGE_ARCHITECTURE_v1_0.md
canonical_id: L2_BODHA_STORAGE_ARCHITECTURE
version: 1.0
status: DECISION_DOC (governs all 8 Bodha per-asset briefs)
authored_by: Cowork (verified against live schemas + writers) 2026-06-19
purpose: >
  The storage-architecture decision for the entire L2 Bodha projection layer + the embedding-consistency
  protocol. Records the verified substrate, why it fits what the assets are, and the native-adopted
  improvements (2026-06-19). Every per-asset brief inherits these rules.
verified_facts:
  - "Substrate = PostgreSQL (Cloud SQL) ONLY. No external store (Neo4j/Pinecone/Redis grep hits were venv/node_modules library code)."
  - "Graph stored as relational adjacency: bodha_cgm_nodes + bodha_cgm_edges (from/to UUID) + bodha_cgm_paths (pre-materialized ordered arrays). igraph computes at BUILD time; metrics flattened to columns; NO runtime traversal engine."
  - "Vectors = pgvector VECTOR(768) + HNSW (Bodha tables). L0 live corpus = classical_text_chunks, text-multilingual-embedding-002, 768-dim (verified in bg_texts writer)."
  - "classical_chunks (mig 158, text-embedding-004 + ivfflat) is a SEPARATE OLDER table NOT written by the bg_texts writer — likely superseded by the L0 rebuild. Cleanup item."
---

# L2 Bodha — Storage Architecture v1.0

## §1 — The substrate (verified) and why it is CORRECT for these assets
**One database: PostgreSQL, four capabilities** — relational tables; `jsonb`+GIN (flexible/array content);
`pgvector`+HNSW (768-dim embeddings); the graph as relational adjacency (nodes + edges + materialized paths).
No external store.

**Why single-Postgres is the right choice (not a compromise):**
1. **The data is bounded + per-chart.** A CGM graph is ~200–300 nodes / <100k edges per (chart, ayanamsha) —
   tiny. A graph DB earns its keep at millions of nodes with deep RUNTIME traversal; here the graph fits in
   memory and is computed once. A graph DB would be over-engineering + an external sync problem.
2. **Pre-compute, don't traverse.** igraph computes metrics at BUILD time; paths are materialized. The graph
   never changes post-build, so runtime traversal buys nothing. Postgres serving pre-structured rows is faster
   + simpler. (A12 spec: "no runtime graph traversal engine" — sound.)
3. **The retrieval pattern is "fetch pre-structured rows + vector similarity," not "walk a graph live."** That
   is exactly Postgres+pgvector's sweet spot (HNSW semantic + GIN array/jsonb + B-tree ordering, one query).
4. **One transactional substrate makes the ANTI-DRIFT SPINE a DB constraint, not a hope.** MSR, embeddings,
   graph, remedies all share the DB → foreign keys GUARANTEE a CGM node's msr_signal_id resolves. Split stores
   would destroy referential integrity across the boundary. Single Postgres = integrity is enforced.

**Verdict: the substrate is well-fitted to what these assets are. Do NOT change it.** The improvements below
are "use Postgres better," not "switch database."

## §2 — The asset connectivity (the continuity, for context)
bo_laksana (MSR) is the spine; every asset references `bodha_msr_signals.signal_id`:
- bo_sangati (CDLM) reads MSR → domain linkage cells.
- bo_karanajala/bo_bimba (CGM) turn MSR signals into nodes/edges (node carries msr_signal_id back-ref).
- bo_samskara: 1:1 with MSR (signal_id FK) → the vector.
- bo_upaya (RM): references MSR weakness-signals + CDLM patterns.
- bo_pramana_mapa: audits all.
Continuity = FK + shared-id referencing inside one DB. No cross-database joins, no sync problem.

## §3 — ADOPTED IMPROVEMENTS (native 2026-06-19 — all govern the briefs)

**S1 [retrievability] Recursive-CTE traversal as a first-class retrieval primitive.** Paths are materialized
for KNOWN path-types; the deep heterogeneous chains (full-length, multi-entity) may need AD-HOC traversal the
LLM requests. Postgres `WITH RECURSIVE` over `bodha_cgm_edges` does this natively + fast at this scale. ADD a
recursive-traversal retrieval tool (`query_chart_graph_traverse(from, to|depth, edge_types)`) so the LLM can
request ARBITRARY chains, not only pre-materialized ones — graph-DB-like traversal WITHOUT leaving Postgres.
(Owner: bo_karanajala brief + the L2_bodha retrieval layer. Cycle-guard in the CTE.)

**S2 [efficiency] Per-chart partitioning discipline.** Indexes already lead with chart_id (good). At MULTI-CHART
scale, partition the large `bodha_*` tables BY chart_id (as chart_dashas is partitioned by time). Not needed at
one chart — flagged as a multi-chart-readiness item; every brief keeps chart_id the leading index column so
partitioning is a later non-breaking change.

**S3 [retrievability/correctness] Standardize on HNSW; align the embedding regime L0↔L2.** All NEW Bodha vector
indexes use HNSW (correct). Retire/upgrade ivfflat where it sits in the LIVE path. The classical bridge requires
L0 + L2 vectors be COMPARABLE → same model + version + dimension + index family (see §4). This is a CORRECTNESS
item for the bridge, not tidiness.

**S4 [depth] Compute the graph WIDE at build time.** Flattening igraph metrics to columns is efficient, but a
NEW metric later needs a rebuild. So bo_karanajala computes a GENEROUS metric set up front — pagerank,
eigenvector, betweenness, closeness, harmonic centrality, degree, k-core, articulation points — so the graph
isn't under-provisioned and a new structural question doesn't force a rebuild. Storage is right; compute wide.

**S5 [efficiency] jsonb-vs-column discipline.** `configuration_jsonb` carries the variable per-category content
(correct for the category-agnostic model). But anything the LLM FILTERS or RANKS by frequently — domain,
fact_kind, valence, salience, source_l1_asset, varga, ayanamsha — MUST be a real INDEXED COLUMN, never
jsonb-only. Hold this line as the elevation fields are added (do NOT let valence/fact_kind slip into jsonb-only).

## §4 — THE EMBEDDING-CONSISTENCY PROTOCOL (the one real risk — make drift impossible)
**Principle:** two vectors are meaningfully comparable ONLY if same model + same version + same dimension.
Cross-model cosine is mathematically valid but SEMANTICALLY GARBAGE — it computes, the meaning is noise, every
test passes, retrieval silently corrupts. So make a mismatch IMPOSSIBLE, not merely currently-absent.

**Verified current state (good):** live L0 corpus `classical_text_chunks` = `text-multilingual-embedding-002`,
768-dim (bg_texts writer, pinned). L2 schema redesign specifies the SAME model + 768-dim + HNSW. The live path
is ALREADY consistent. The risk is FUTURE drift, not a present mismatch.

**The five mechanisms (all briefs comply):**
1. **One pinned shared constant.** Define `EMBEDDING_MODEL` + `EMBEDDING_MODEL_VERSION` + `EMBEDDING_DIM` in a
   SINGLE shared module; L0 (bg_texts) + L2 (bo_samskara) + every future embedder IMPORT it. None hardcode their
   own. A model change happens in one place or not at all.
2. **Stamp model + version on every embedded row.** classical_text_chunks + bodha_signal_embeddings already have
   embedding_model / embedding_model_version columns — POPULATE them always. Vectors become self-describing.
3. **Cross-layer consistency CI check (the guardrail).** Assert: every populated embedding column across L0 + L2
   carries the SAME model + version + dimension. bo_samskara embedding with a different model than
   classical_text_chunks FAILS loudly. This makes the bridge PROVABLY sound, not coincidentally sound.
4. **Dimension enforced by column type.** Keep every embedding column `VECTOR(768)` (same dim) — Postgres rejects
   a wrong-dim insert as a hard error, not a silent corruption.
5. **Version bump = rebuild BOTH sides together.** Changing the model re-embeds EVERY table in the shared vector
   space in the same migration/build (rebuild-all-or-nothing). The embedding model is a LAYER-SPANNING VERSIONED
   CONTRACT, not a per-table choice.

**CLEANUP:** verify whether `classical_chunks` (mig 158, text-embedding-004 + ivfflat) is dead. If no reader →
retire it (so no future session thinks two embedding regimes exist). If a reader exists → it's on the OLD corpus;
repoint it to `classical_text_chunks`. (Run this reverse-citation check before the bo_samskara brief.)

## §4B — MANDATORY: every per-asset brief carries an inline STORAGE-COMPLIANCE block
A storage rule only takes effect if it is IN the brief the executor reads. So EVERY bo_* brief MUST include a
"§STORAGE COMPLIANCE" block naming the specific S1–S5 + embedding-protocol rules that apply to that asset (not
all five everywhere — only the relevant ones). Propagation status (2026-06-19):
- bo_karanajala/bo_bimba — ✅ (S1 traversal, S4 compute-wide, HNSW, embedding protocol).
- bo_laksana — ✅ added v1.2 (§11B: S5, embedding-input awareness, S2).
- bo_sangati — ✅ added v1.0 (§6B: S5, S1 reuse, S2).
- bo_samskara — ✅ added v1.0 (§3 FULL embedding protocol #1–#5 + §3.6 classical_chunks cleanup + HNSW + 768-dim).
- bo_samvada — ✅ added v1.0 (§STORAGE: S1 zoom/reachability reuse, S5, S2; ELEVATED to thin-writer gestalt + view).
- bo_drishti (lens) — ⬜ S5 (lens columns indexed); S1 (the wildcard graph-sweep reuses the traversal tool).
- bo_upaya — ✅ added v1.0 (§STORAGE: embedding protocol for prescription_embedding_vec + S5 + S2).
- bo_pramana_mapa — ✅ added v1.0 (§STORAGE: audits embedding-consistency + ledger integrity; pass/fail = columns, violation lists = jsonb).

## §5 — What each brief inherits
- **bo_laksana:** S5 (valence/fact_kind/etc. as real columns); embedding-protocol #1–#2 awareness (it produces
  the signal_summary_text that bo_samskara embeds).
- **bo_karanajala/bo_bimba:** S1 (recursive-CTE traversal tool), S4 (compute wide), S5.
- **bo_samskara:** the FULL embedding protocol §4 (#1–#5) + the classical_chunks cleanup check; HNSW; 768-dim;
  shared model constant.
- **bo_upaya:** embedding protocol (prescription_embedding_vec must use the same model/dim).
- **all + retrieval layer:** S3 (HNSW alignment), the cross-layer consistency CI check.
- **bo_pramana_mapa:** can audit embedding-consistency as a scorecard metric.

---
*End of L2_BODHA_STORAGE_ARCHITECTURE v1.0. Substrate = single PostgreSQL (pgvector HNSW + jsonb/GIN + relational
graph + materialized paths) — verified correct + well-fitted; not changed. Adopted improvements: recursive-CTE
traversal primitive (S1), partitioning discipline (S2), HNSW + embedding-regime alignment (S3), compute-graph-wide
(S4), jsonb-vs-column discipline (S5). The embedding-consistency protocol (§4) makes model drift IMPOSSIBLE via a
shared pinned constant + per-row stamping + a cross-layer CI check + dimension-by-type + rebuild-all-on-version-bump
— the one real risk to the L0↔L2 classical/semantic bridge, now hardened. Cleanup: retire/repoint the stale
classical_chunks table.*
