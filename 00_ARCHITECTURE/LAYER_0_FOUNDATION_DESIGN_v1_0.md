---
artifact: LAYER_0_FOUNDATION_DESIGN_v1_0.md
canonical_id: LAYER_0_FOUNDATION_DESIGN
version: 1.0
status: CLOSED 2026-06-02 (design baseline — sealed in M5_REARCHITECTURE_DESIGN_CLOSE_v1_0; build phase next)
authored_by: Claude (Cowork) 2026-06-02
purpose: >
  The full, detailed design of Layer 0 (Foundation) for the clean-slate rebuild: the global,
  build-once, client-independent substrate every chart rests on, elevated from "raw texts +
  fuzzy embeddings" into a structured classical-knowledge substrate fit for a research product.
  This is the design we turn into the executable Layer 0 plan brief.
---

# Layer 0 — Foundation · Detailed Design

> **Project Brahma · external name: Brahmagyan / Foundation.** Per BUILD_WORKFLOW_AND_TOOLING_DESIGN_v2_0 +
> BRAHMA_BUILD_UX_SPEC_v1_0: user-facing surfaces show "Brahmagyan / Foundation" — never "L0" or asset
> codenames (internal docs keep L0 for precision). **Brahmagyan is a one-time global build:** the native
> builds it + the GCP data infrastructure **once**; every later account sees it already green and stands on
> it — no user rebuilds the foundation. Its assets are built **with their retrieval tool(s)** (rule-base,
> concordance, text-index, remedy-corpus, almanac tools — per-asset primitives + composite capability tools),
> deployed to web + MCP and tested against the built data in the same swarm arc; verifies only when assets
> **and** tools pass, with a volume-floor amber gate.

## §A — What Layer 0 is

- **Global + build-once.** Everything here is chart-independent and shared by every client. Built
  once, reused; rebuilt only when a source changes — never per chart.
- **The bedrock.** Every downstream layer (Chart Facts → Synthesis → Time & Patterns) rests on it.
- **The elevation.** Not just data to retrieve — a **reasoning substrate**: primary texts +
  structured rules + cross-school concordance + a shared vocabulary, all queryable and citeable.
- **Clean slate.** Built fresh after the legacy teardown; no legacy data, code, tools, or
  migrations inherited.

## §B — Governing rules (apply to all Layer 0 work)

- LEL stays fully isolated — never fed into or derived from any Layer 0 asset.
- PyJHora is the engine source-of-truth (Layer 1); no JH-parity oracle anywhere; verification is
  internal consistency only.
- No legacy dependency — if it touches the wiped system, it's rebuilt.
- Classical texts stored **original (Sanskrit/source) + translation**.
- Retrieval is **on-demand coherent bundles via tools**, not unlimited context; the agentic loop
  pulls depth adaptively.
- **One tool per asset** — an asset isn't done until its layer-appropriate retrieval tool exists.
- Provenance on every unit: source + school + tier + confidence; everything citeable.

## §C — The eight Layer 0 assets + dependency order

```
roots:   0.1 Ephemeris   0.2 Reference Library   0.3 Classical Texts   0.5 Ontology
derived: 0.4 Text Index      ← 0.3 (+0.5 tags)
         0.6 Rule Base        ← 0.3 + 0.5
         0.7 Concordance      ← 0.6 (across schools)
         0.8 Daily Almanac    ← 0.1
```

---

## §D — Per-asset detail

### 0.1 · Ephemeris (Global Ephemeris)
- **Role:** raw sidereal/astronomical positions over time — the astronomical bedrock.
- **Contains:** for each body, longitude/latitude/speed/retrograde + derived sign/nakshatra/pada
  over the full date range; the one truly global, geocentric, location-independent table.
- **Source / build:** Swiss Ephemeris (pyswisseph, DE440) via a clean bootstrap; deterministic,
  content-addressed, pinned versions.
- **Scope:** global by `(date, body[, frame])`; no chart, no location.
- **Consumers:** Daily Almanac (0.8), the Chart Engine (Layer 1), all transit/temporal work.
- **Tool:** `ephemeris.query(date_range, bodies, ayanamsha)`.
- **OPEN DECISIONS:**
  - **Ayanamsha at source** — store one canonical frame (raw sidereal or tropical) and derive each
    ayanamsha on read, *or* precompute every ayanamsha into rows? (flexibility vs size)
  - **Node type** — resolve TRUE vs MEAN Rahu/Ketu once, or store both?
  - **Granularity** — daily + on-demand exact crossings, or finer (hourly) precompute?
  - **Bodies** — 9 grahas only, or include outers / key asteroids / Upagrahas at source?

### 0.2 · Reference Library (Classical Reference Tables)
- **Role:** fixed classical lookup data — identical for everyone, no computation.
- **Contains:** the chakra grids (Sarvatobhadra + vedha pairs, Sapta-Shalaka, Kalanala, Kota, CKN),
  Hadda/Ptolemaic bounds, Tajik aspect definitions, Mudda periods, year-lord rules, aspect-angle
  defs, dignity/exaltation tables, nakshatra attributes — everything currently hardcoded in code.
- **Source / build:** transcribe from the classical texts; seed as versioned data.
- **Structure:** proper **queryable DB tables**, each row carrying its source citation (no Python
  constants).
- **Scope:** global, no chart/location.
- **Consumers:** the Chart Engine + temporal/muhurta logic across all layers.
- **Tool:** `reference.lookup(table, key)`.
- **OPEN DECISIONS:** final list of reference tables; whether reference data lives in DB tables or
  versioned data files loaded into tables.

### 0.3 · Classical Texts (Primary-Source Corpus)
- **Role:** the source scriptures — citation ground-truth and the raw material for rules.
- **Contains (full canon — drop all derived/legacy):**
  - *Foundational primaries:* BPHS, Jaimini Upadesha Sutras (all 4 Adhyayas), Brihat Jataka
    (+Bhattotpala), Saravali, Phaladeepika, Jataka Parijata, Sarvartha Chintamani, Hora Sara.
  - *Esoteric / high-signal:* Uttara Kalamrita, Prashna Marga + Daivajna Vallabha + Shatpanchashika,
    Yavana Jataka, Bhrigu Nandi Nadi, Chandra Kala Nadi / Deva Keralam, Saptarishi Nadi, Tajaka
    Neelakanthi (real edition) + a Varshaphala text, Muhurta Chintamani, Brihat Samhita.
- **Form:** **original (Sanskrit/source) + translation**, verse-addressable IDs (e.g. `BPHS.NN.NNN`),
  tiered, each unit carrying author/school/tradition/source provenance.
- **Source / build:** real primary editions (public-domain scans + reputable translations); a clean
  ingestion + structuring pipeline; no M9-derived synthetic corpus.
- **Scope:** global.
- **Consumers:** Text Index (0.4), Rule Base (0.6).
- **Tool:** `text.read(canonical_id | verse_ref)`.
- **OPEN DECISIONS:** final text list + editions; handling of untranslated/Sanskrit-only texts
  (translation/alignment pipeline); licensing per text.

### 0.4 · Text Index (Retrieval Index)
- **Role:** make the corpus retrievable for grounding the LLM at query time.
- **Contains:** the chunked, embedded, lexically-indexed form of 0.3 — one clean store (retire the
  legacy dual stores).
- **Approach (the elevation):** **hybrid** — verse-addressable exact lookup + lexical (BM25) +
  vector embeddings + a cross-encoder **reranker**; tools return **coherent on-demand bundles**
  (a full topic's rules, a chapter, a concordance set) sized to need, not 5 stray chunks.
- **Embeddings:** domain/multilingual model (model choice TBD); pgvector + HNSW; multi-granularity
  (verse / chapter / principle).
- **Scope:** global (chart-independent).
- **Consumers:** the synthesis loop (Layer 2/3 query time) via the kept agentic loop + MCP.
- **Tool:** `corpus.search(query, filters{school,tier,topic}, bundle_mode)`.
- **OPEN DECISIONS:** embedding model; chunk granularity; reranker choice; bundle-size/fetch-budget caps.

### 0.5 · Jyotish Ontology (Controlled Vocabulary)
- **Role:** one shared entity language across corpus, rules, reference data, and chart facts.
- **Contains:** canonical entities + stable IDs — grahas, rashis, bhavas, nakshatras, yogas, dashas,
  karakas, dignities, aspects, divisional charts, etc., with synonyms/translations and relationships.
- **Source / build:** define fresh (the old FORENSIC §0 namespace is wiped); author from the texts +
  classical standards.
- **Scope:** global, cross-cutting (tags everything).
- **Consumers:** every other Layer 0 asset + all downstream layers + tools (shared vocabulary).
- **Tool:** `ontology.resolve(term) → canonical entity`.
- **OPEN DECISIONS:** scope/depth of the ontology; whether it's a formal graph or a controlled list +
  relations to start.

### 0.6 · Rule Base (Classical Principle Layer)
- **Role:** turn the corpus from text-to-retrieve into reasoning units — the research multiplier.
- **Contains:** extracted rules, each = `{condition (chart pattern) → assertion (effect), source
  verse(s), school, scope/qualifiers, confidence, cross-refs}`.
- **Source / build:** extract from 0.3 using 0.5's vocabulary (LLM-assisted + human-reviewed, or
  staged); each rule traceable to its verse.
- **Scope:** global.
- **Consumers:** synthesis (surfaces which rules fire for a chart + cites them), Concordance (0.7),
  the hypothesis→falsification loop.
- **Tool:** `rules.match(chart_conditions) → firing rules`.
- **OPEN DECISIONS:** extraction method (manual / LLM-assisted / hybrid) + review discipline; rule
  schema depth; coverage target (which texts first).

### 0.7 · Concordance (Cross-School Agreement & Divergence Index)
- **Role:** map the same topic across schools — where BPHS / Jaimini / KP / Tajaka / Nadi agree and
  where they contradict. For research, the disagreements are the value.
- **Contains:** per-topic concordance entries linking rules (0.6) across schools, tagged agree /
  qualify / conflict, with lineage notes.
- **Source / build:** derived from the Rule Base across schools.
- **Scope:** global.
- **Consumers:** synthesis (honest multi-school answers), divergence surfacing, research queries.
- **Tool:** `concordance.lookup(topic) → cross-school stances`.
- **OPEN DECISIONS:** topic taxonomy; how conflicts are represented/resolved (surfaced, not flattened).

### 0.8 · Daily Almanac (Location-Parameterized Panchang)
- **Role:** the five limbs (tithi/vara/nakshatra/yoga/karana) + day-quality windows for any day —
  but now **per location**, not fixed to one city.
- **Contains:** panchang derived from the global ephemeris at a given place's local sunrise; the
  enrichment windows (choghadiya, hora, rahu/yama/gulika, special yogas).
- **Approach:** a **function of (date, location)** computed off 0.1 — compute local sunrise, sample
  the ephemeris, derive limbs; **cached per normalized location** (place_id / rounded lat-lon).
  Not one global table.
- **Handles:** IANA timezone + historical DST, half-hour zones, high latitudes (no-sunrise days),
  altitude.
- **Scope:** shared per-location (build-once-per-place), not per-chart. (Birth-moment panchang is a
  chart-specific fact → Layer 1, not here.)
- **Consumers:** muhurta, panchang queries, any time-of-day reasoning.
- **Tool:** `almanac.query(date_range, location)`.
- **OPEN DECISIONS:** cache strategy (precompute-per-location vs pure on-demand); location
  normalization granularity.

---

## §E — Layer 0 retrieval model (how the agent uses it)

- Every asset exposes a **layer-appropriate tool** (above); no monolithic tool stack.
- The kept agentic loop + MCP shell call these tools; the loop **pulls coherent bundles on demand**
  and loops for more depth — no unlimited context.
- Hybrid retrieval (exact verse + lexical + vector + rerank) for the corpus; deterministic lookups
  for ephemeris/reference/almanac; structured matches for rules/concordance.
- Everything returned carries provenance (source + school + tier + confidence) for citation.

## §F — Open decisions to settle in / before the plan brief

1. Ephemeris: ayanamsha-at-source model · node type · granularity · bodies (0.1).
2. Classical corpus: final text list + editions · untranslated-text handling (0.3).
3. Text Index: embedding model · granularity · reranker · bundle caps (0.4).
4. Ontology depth + form (0.5).
5. Rule Base extraction method + review discipline + coverage order (0.6).
6. Concordance topic taxonomy (0.7).
7. Almanac cache strategy + location normalization (0.8).
8. Build sequencing across the eight (roots first; index/rules/concordance after).

---

*End of LAYER_0_FOUNDATION_DESIGN v1.0 — DRAFT for native review, 2026-06-02. Next: the Layer 0
plan brief turns this into sequenced, gated build steps.*
