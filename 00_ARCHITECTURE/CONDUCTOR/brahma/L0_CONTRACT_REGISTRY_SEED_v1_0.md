---
artifact: L0_CONTRACT_REGISTRY_SEED_v1_0.md
canonical_id: L0_CONTRACT_REGISTRY_SEED
version: 1.0
status: CURRENT (the L0/Brahmagyan plan the autonomous swarm consumes)
project_codename: Brahma
authored_by: Claude (Cowork) 2026-06-03
grounds_in: LAYER_0_FOUNDATION_DESIGN_v1_0.md (the 8 assets + deps + tools)
governed_by: BUILD_GUARANTOR_SWARM_CHARTER_v1_0 (§F schema) + BUILD_GUARANTOR_AUTONOMOUS_MODE_v1_0
purpose: >
  Seeds the Asset Contract Registry for Layer 0 (Brahmagyan) and defines the session queue. This is
  the FUEL: the Conductor walks the queue; for each unit the swarm's Racayitā drafts the build brief
  from this contract + the L0 design, Śilpī builds it, the Review Swarm reviews, Pratiṣṭhā deploys,
  Gate-3 verifies — autonomously, per AUTONOMOUS_MODE. Foundational open-decisions are pre-resolved
  here (marked ✓) so the swarm builds to a settled spec; genuine spikes are explicit gated sub-steps.
---

# Brahmagyan (L0) — Contract Registry Seed + Session Queue

## §A — Pre-resolved foundational decisions (so the swarm doesn't guess)

- **Ephemeris frame ✓** ayanamsha-invariant at source: store raw tropical longitude/lat/speed; derive each
  ayanamsha on read (per MASTER_ARCHITECTURE L1 split). **Nodes ✓** store BOTH true + mean. **File ✓** DE441
  via pyswisseph, pinned. **Bodies ✓** full set — 9 grahas + outers + the upagrahas/sensitive points the
  FORENSIC benchmark carries. **Granularity ✓** daily rows + on-demand exact crossings.
- **Embedding model** — GATED on the C4 spike (sub-step in 0.4); default `text-multilingual-embedding-002`
  pending the spike's verdict. Do not bulk-embed before the spike passes.
- **Rule extraction ✓ method** — LLM-assisted extraction with a **gold-standard pilot on ONE text (BPHS)**
  first (the keystone gate); confidence = textual-strength + cross-text corroboration (not a guess). Full
  canon only after the pilot clears its quality bar.
- **Verification ✓** internal consistency + the astronomical ground-truth check (PyJHora/Swiss vs JPL) for
  0.1; no JH-parity oracle. **Provenance ✓** every unit carries source · school · tier · confidence.
- **External name ✓** every user-facing string = "Brahmagyan / Foundation"; never "L0".

## §B — The session queue (topological; parallel where independent)

```
WAVE 1 (roots — parallel):   0.1 Ephemeris · 0.2 Reference Library · 0.3 Classical Texts · 0.5 Ontology
WAVE 2 (derived):            0.4 Text Index (←0.3,0.5) · 0.6 Rule Base (←0.3,0.5) · 0.8 Almanac (←0.1)
WAVE 3 (derived):            0.7 Concordance (←0.6)
```
A unit is released the moment its `depends_on` are verified-green (dependency-gated, not wave-locked).

## §C — Per-asset contracts

### 0.1 · Ephemeris  (`brahmagyan.ephemeris`)
- depends_on: [] · owns: raw astronomical positions over time · build_mode: fresh
- code_contract: bootstrap writer (pyswisseph DE441) → typed `ephemeris` tables; tool `ephemeris.query`; MCP resource; tests
- deploy_contract: web + MCP; data to Cloud SQL
- runtime_contract: every body × date in range present; tropical-at-source; true+mean nodes; **astronomical ground-truth spot-check vs JPL passes**; tool returns provenance envelope
- acceptance_gate: `pytest tests/l0/ephemeris` + ground-truth check + tool smoke
- volume_floor: full date range × bodies (no gaps)
- tools: `ephemeris.query(date_range, bodies, ayanamsha)`

### 0.2 · Reference Library  (`brahmagyan.reference`)
- depends_on: [] · owns: fixed classical lookup tables (chakra grids, bounds, aspect defs, dignities, nakshatra attrs) · fresh
- code_contract: seed writer → versioned `reference_*` DB tables (each row cites its source); tool `reference.lookup`; resource; tests
- runtime_contract: every table populated; every row has source_citation; no Python-constant residue
- acceptance_gate: row-count per table ≥ floor + citation-non-null + tool smoke
- tools: `reference.lookup(table, key)`

### 0.3 · Classical Texts  (`brahmagyan.texts`)
- depends_on: [] · owns: primary-source corpus (original + translation, verse-addressable) · fresh
- code_contract: ingestion pipeline → `classical_texts/_chunks` with verse IDs + provenance (author/school/tier); tool `text.read`; resource; tests
- runtime_contract: each text present as original+translation; verse-addressable IDs resolve; provenance on every unit
- acceptance_gate: per-text presence + verse-ref resolution + tool smoke; **licensing cleared per text (hard-blocker)**
- tools: `text.read(canonical_id | verse_ref)`
- note: licensing of real editions is a tracked hard-blocker — park any text whose edition isn't cleared.

### 0.5 · Ontology  (`brahmagyan.ontology`)
- depends_on: [] · owns: controlled vocabulary (canonical entities + stable IDs + synonyms/relations) · fresh
- code_contract: author from texts+standards → `ontology` store; tool `ontology.resolve`; resource; tests
- runtime_contract: every core entity class has canonical IDs + synonyms; resolves terms across languages
- acceptance_gate: entity-coverage check + resolve smoke
- tools: `ontology.resolve(term) → entity`

### 0.4 · Text Index  (`brahmagyan.text_index`)
- depends_on: [0.3, 0.5] · owns: retrievable hybrid index over the corpus · fresh
- **gated sub-step: embedding-model spike (C4) — run + pass before bulk embed**
- code_contract: chunk+embed+lexical-index writer (pgvector+HNSW, BM25, reranker); tool `corpus.search` (bundle mode); resource; tests
- runtime_contract: hybrid retrieval (verse-exact + lexical + vector + rerank) returns coherent bundles sized to need; provenance on results
- acceptance_gate: retrieval quality on a golden query set + bundle-coherence + tool smoke
- tools: `corpus.search(query, filters{school,tier,topic}, bundle_mode)`

### 0.6 · Rule Base  (`brahmagyan.rules`)
- depends_on: [0.3, 0.5] · owns: extracted classical rules (condition→assertion, cited) · fresh
- **gated sub-step: gold-standard extraction pilot on BPHS — pass the quality bar before full canon**
- code_contract: extraction pipeline (LLM-assisted + review) → `rules` store, each rule verse-traceable + confidence; tool `rules.match`; resource; tests
- runtime_contract: rules carry {condition, assertion, source_verse, school, scope, confidence}; every rule traces to a verse; confidence has principled origin
- acceptance_gate: pilot quality bar + per-rule verse-traceability + tool smoke
- tools: `rules.match(chart_conditions) → firing rules`

### 0.8 · Daily Almanac  (`brahmagyan.almanac`)
- depends_on: [0.1] · owns: location-parameterized panchang (5 limbs + day-quality windows) · fresh
- code_contract: function of (date, location) off the ephemeris (local sunrise → limbs + choghadiya/hora/rahu-yama-gulika/special yogas); cache per normalized location; tool `almanac.query`; resource; tests
- runtime_contract: correct limbs vs a known reference day; handles IANA tz/DST, half-hour zones, high latitudes; per-location cache
- acceptance_gate: panchang spot-check vs a reference + tz/edge-case tests + tool smoke
- tools: `almanac.query(date_range, location)`

### 0.7 · Concordance  (`brahmagyan.concordance`)
- depends_on: [0.6] · owns: cross-school agreement/divergence index over the rules · fresh
- code_contract: derive per-topic cross-school stances (agree/qualify/conflict + lineage) from the Rule Base; tool `concordance.lookup`; resource; tests
- runtime_contract: per-topic entries link rules across schools; conflicts surfaced (not flattened); provenance/lineage present
- acceptance_gate: topic-coverage + conflict-surfacing check + tool smoke
- tools: `concordance.lookup(topic) → cross-school stances`

## §D — Layer-complete gate (Brahmagyan verifies)

Brahmagyan is green only when all 8 assets **and** their tools pass their acceptance gates, every tool is
live on web + MCP with the provenance envelope, and the layer-tower shows the bedrock band lit. Then the
one-time `brahma-foundation-bootstrap` job has produced the global foundation, and L1 (Gaṇita) is released.

## §E — How the autonomous swarm consumes this

Per AUTONOMOUS_MODE: the Conductor walks §B; for each released unit, Racayitā drafts the brief from this
contract + the L0 design, Śilpī builds the writer+tool+schema+tests, the Review Swarm ×5 reviews, Pratiṣṭhā
deploys (web+MCP), Gate-3 verifies data+tool against the acceptance_gate. Pass → green → next; fail →
bounded auto-fix → park. The two gated sub-steps (embedding spike, rule pilot) are hard quality gates the
swarm must clear before bulk work. No human in the loop; §C safety rails on.

---

*End of L0_CONTRACT_REGISTRY_SEED v1.0 — the Brahmagyan plan. Drop this + the queue into the Conductor;
the autonomous swarm builds Brahmagyan from it.*
