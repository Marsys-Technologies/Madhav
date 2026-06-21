---
artifact: CLAUDECODE_BRIEF_BO_SAMSKARA_v1_0.md
canonical_id: BO_SAMSKARA_BRIEF
version: 1.0
status: FOR_NATIVE_REVIEW (Batch 2 — signal embeddings; the semantic-retrieval enabler)
authored_by: Cowork (grounded in live embeddings schema + storage protocol) 2026-06-19
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
scope: bo_samskara ONLY — real Vertex AI embeddings for every MSR signal (bodha_signal_embeddings, 1:1 with bo_laksana). Depends on bo_laksana. REPLACES the placeholder_hash scaffold with real semantic embeddings.
data_plane: ALWAYS prod via Cloud SQL Auth Proxy (127.0.0.1:5433)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
governing:
  - L2_BODHA_STORAGE_ARCHITECTURE_v1_0.md §4 (THE EMBEDDING-CONSISTENCY PROTOCOL — this asset's spine) + §4B
  - L2_BODHA_SCHEMA_REDESIGN_v1_0.md + L2_BODHA_OVERALL_APPROACH_v1_0.md (the L0↔L2 semantic bridge)
  - GA_STRUCTURAL_REBUILD_VERIFY_v2_1.md (L1 authority) ; bg_texts writer (the L0 embedding precedent to MATCH)
  - ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2 (FROZEN WriterBase)
target_files:
  - platform/python-sidecar/pipeline/orchestrator/writers/bo_samskara.py (replace placeholder_hash with real Vertex embeddings)
  - a NEW shared embedding constant module (imported by bg_texts AND bo_samskara — see §3.1)
  - migration: (bodha_signal_embeddings schema is already correct — verify only) + the cross-layer consistency CI check
  - platform/src/lib/retrieval/registry/layers/L2_bodha/ (semantic retrieval tools)
must_not_touch: FROZEN orchestrator contract; ga_* writers; bo_laksana; other bo_* writers. (May ADD the shared embedding constant + repoint bg_texts to import it — that is a deliberate, declared cross-asset alignment, §3.1.)
---

# bo_samskara — real signal embeddings (the semantic-retrieval enabler)

## §0 — What this is + the one job that matters
One embedding row per MSR signal (1:1, `bodha_signal_embeddings`), so signals are retrievable by MEANING, not
just column filter. The current merged writer uses `placeholder_hash_v1` — a deterministic but SEMANTICALLY
OPAQUE hash (two "career instability" signals land randomly far apart). **The job: replace it with REAL Vertex AI
embeddings of bo_laksana's `signal_summary_text`, in the SAME vector space as L0's classical corpus — so a signal
can be similarity-matched to its classical sources (the L0↔L2 bridge).** The schema is already correct
(VECTOR(768) + model/version columns + HNSW); the WRITER is what changes.

## §1 — Non-negotiables
Deterministic-first — **a real embedding model is a DETERMINISTIC TRANSFORM (same text + same pinned model →
same vector); it is NOT a generative LLM and does NOT violate deterministic-first** (native-ratified; L0's
bg_texts already embeds via Vertex in the build). No audience tier; no silent drops; per-chart isolation; FROZEN
orchestrator contract (`@register('bo_samskara')` WriterBase on ctx.db_conn, never commits, no asset_throughput);
1:1 with MSR (UNIQUE(signal_id)); floors aspirational. NO generative LLM anywhere.

## §2 — Preconditions
1. Proxy up; main == prod. Verify `bodha_signal_embeddings` schema is the correct one (VECTOR(768) + embedding_model
   + embedding_model_version + HNSW) — it is per migration 226; confirm on prod.
2. **bo_laksana built** with `signal_summary_text` populated (the embedding INPUT — must be lossless + stable).
3. Vertex AI reachable from the sidecar (the bg_texts writer's genai client path is the precedent — reuse it).

## §3 — THE EMBEDDING-CONSISTENCY PROTOCOL (storage §4 — this asset's spine; all 5 mechanisms)
The L0↔L2 semantic bridge only works if L0 + L2 vectors are COMPARABLE: same model + version + dimension.
Cross-model cosine is semantically GARBAGE (computes fine, meaning is noise, every test passes). Make drift
IMPOSSIBLE:

### §3.1 — Mechanism 1: ONE pinned shared constant
Create a single shared module (e.g. `platform/python-sidecar/shared/embedding_config.py`):
`EMBEDDING_MODEL = "text-multilingual-embedding-002"`, `EMBEDDING_MODEL_VERSION = "<pinned>"`, `EMBEDDING_DIM = 768`.
bo_samskara imports it. **Repoint bg_texts to import the SAME constant** (it currently hardcodes the model) — a
declared cross-asset alignment so L0 + L2 can NEVER diverge. No writer hardcodes its own model.

### §3.2 — Mechanism 2: stamp model + version on every row
Populate `embedding_model` + `embedding_model_version` from the shared constant on EVERY embedding row. Vectors become self-describing.

### §3.3 — Mechanism 3: the cross-layer consistency CI check (the guardrail)
Add a CI/test assertion: every populated embedding column across L0 (classical_text_chunks) AND L2
(bodha_signal_embeddings + any other vector column) carries the SAME model + version + dimension. If bo_samskara
ever embeds with a different model than classical_text_chunks → FAIL loudly. This makes the bridge PROVABLY sound.

### §3.4 — Mechanism 4: dimension enforced by column type
Every embedding column stays VECTOR(768) — Postgres rejects a wrong-dim insert as a hard error, not a silent corruption.

### §3.5 — Mechanism 5: version bump = rebuild BOTH sides together
Changing the model re-embeds EVERY table in the shared vector space (L0 chunks + L2 signals + CGM nodes + RM
prescriptions) in the same build. The embedding model is a LAYER-SPANNING VERSIONED CONTRACT, not a per-table choice. Document this rule in the shared module.

### §3.6 — CLEANUP (do this before/with the build)
Run a reverse-citation check on `classical_chunks` (mig 158, text-embedding-004 + ivfflat — a SEPARATE OLDER
table NOT written by the bg_texts writer). If NO live reader → retire it (so no future session thinks two
embedding regimes exist). If a reader exists → it's on the OLD corpus; repoint it to `classical_text_chunks`. Report which.

## §4 — The build
- Fetch every MSR signal for the native chart × 5 ayanamshas; embed its `signal_summary_text` via the shared Vertex
  model (batch like bg_texts; respect rate limits). Write 1:1 to bodha_signal_embeddings with model/version stamped.
- `embedding_input_summary` = the (truncated for storage) text actually embedded — so the input is auditable.
- Idempotent: delete-then-insert (or ON CONFLICT(signal_id) DO UPDATE) per chart×ayanamsha.

## §5 — Anti-drift + verification
1. **1:1:** count(bodha_signal_embeddings) == count(bodha_msr_signals) for the chart (every signal embedded; none orphaned).
2. **REAL semantics (the proof the placeholder couldn't pass):** two astrologically-related signals (e.g. two
   "career weakness" signals) are cosine-NEAR; two unrelated ones are far. Spot-check a known related pair — a
   hash CANNOT achieve this; a real embedding must. `[verify-against: prod]`
3. **Consistency:** model + version + dim match classical_text_chunks (the CI check §3.3 passes).
4. **Bridge works:** a signal's embedding retrieves its relevant classical_text_chunks by cosine similarity (the L0↔L2 bridge is live).
5. Idempotent; no silent drops; FORENSIC unaffected.

## §6 — Retrieval (semantic search — the payoff)
Extend `L2_bodha/`: `query_signals_semantic(chart, query_text|signal_id, top_k)` — HNSW cosine search over
bodha_signal_embeddings returning semantically-near signals WITH full provenance (the signal's fact_ids,
citation, salience, epistemic state). AND `query_signal_to_classical(signal_id)` — the bridge: a signal's nearest
classical_text_chunks (same vector space). Coverage gate: the embedding table + the semantic tools reachable.

## §STORAGE COMPLIANCE (storage §4B)
- **FULL embedding-consistency protocol §3 (#1–#5)** — this asset's spine.
- **HNSW** (already in schema) for cosine search; **768-dim** enforced by column type.
- **classical_chunks cleanup** (§3.6).
- chart_id leads indexes (S2). No jsonb-vs-column issue (this table is columnar + one vector).

## §7 — Acceptance
- [ ] placeholder_hash REPLACED with real Vertex `text-multilingual-embedding-002` embeddings of signal_summary_text.
- [ ] **1:1 with MSR** (every signal embedded; UNIQUE(signal_id)).
- [ ] **Real semantics proven** (related signals cosine-near; the test a hash fails).
- [ ] **Consistency protocol:** shared constant imported by bg_texts + bo_samskara; model/version stamped per row; cross-layer CI check passes; VECTOR(768); version-bump rule documented.
- [ ] **Bridge live:** signal → nearest classical_text_chunks works.
- [ ] classical_chunks cleanup done (retired or repointed; reported).
- [ ] Semantic retrieval tools + coverage gate; FROZEN contract; idempotent.

---

# §ELEVATION (toward supreme)
- **E-1 [retrievability] Embed more than the summary** — optionally a SECOND embedding per signal over the
  signal's classical citation text (so "find signals whose CLASSICAL meaning resembles this" works). Same model/space.
- **E-2 [retrievability] Domain/concept anchor embeddings** — pre-embed canonical concept phrases ("career
  instability", "sudden wealth", "marital discord") so the LLM can pull all signals near a CONCEPT in one call.
- **E-3 [depth] Embed the CGM nodes + topology too** (the schema already has node_embedding_vec + topology vec) —
  coordinate the SAME model so node-similarity + chart-topology-similarity share the space. (bo_karanajala owns
  those columns; bo_samskara/the protocol governs the model.)
- **E-4 [retrievability] Similarity-threshold provenance** — every semantic return states its cosine score so the
  LLM can distinguish "strongly related" from "loosely related" (calibrated retrieval).

---
*End of BO_SAMSKARA v1.0. Replace the placeholder hash with REAL Vertex text-multilingual-embedding-002 embeddings
of bo_laksana's signal_summary_text — 1:1 with MSR, in L0's vector space so signals bridge to their classical
sources. The full embedding-consistency protocol (one shared pinned constant + per-row stamping + cross-layer CI
check + dimension-by-type + rebuild-on-version-bump) makes model drift IMPOSSIBLE — the one real risk to the
semantic bridge. Proof the placeholder couldn't pass: related signals are cosine-near. Plus the classical_chunks
cleanup. ELEVATION: citation embeddings, concept anchors, coordinated CGM-node embeddings, similarity provenance.*
