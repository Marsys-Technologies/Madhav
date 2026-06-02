---
artifact: LAYER_0_PLAN_BRIEF_v1_0.md
canonical_id: LAYER_0_PLAN_BRIEF
version: 1.0
status: CLOSED 2026-06-02 (design baseline — sealed in M5_REARCHITECTURE_DESIGN_CLOSE_v1_0; build phase next)
authored_by: Claude (Cowork) 2026-06-02
supersedes_view: 00_ARCHITECTURE/LAYER_0_FOUNDATION_DESIGN_v1_0.md (this is the detailed plan built on it)
read_with:
  - 00_ARCHITECTURE/INFRASTRUCTURE_INVENTORY_v1_0.md (open infra decisions)
  - 00_ARCHITECTURE/LEGACY_TEARDOWN_KILL_LIST_v1_0.md (clean-slate precondition)
  - 00_ARCHITECTURE/BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md (the swarm that builds + verifies)
purpose: >
  The detailed build plan for Layer 0 (Foundation): eight global, build-once assets that form the
  research-grade substrate every chart rests on. Every decided value is baked in; every open
  decision is flagged in §K so nothing is lost. Turns into per-asset Antigravity execution briefs
  once §K is closed.
---

# Layer 0 — Plan Brief

## §A — Mission & scope

- Layer 0 = the **global, build-once, client-independent** foundation: astronomy + classical
  knowledge, elevated from "texts + fuzzy search" into a **structured reasoning substrate** fit
  for a Vedic-astrology **research** product.
- **Eight assets:** Ephemeris, Reference Library, Classical Texts, Text Index, Ontology, Rule
  Base, Concordance, Daily Almanac.
- **Clean slate:** built after the legacy teardown — no legacy data, code, tools, or migrations.
- **Deploy target:** Railway (per Infrastructure Inventory; specifics still open).

## §B — Governing rules (bind all Layer 0 work)

1. LEL stays fully isolated — never fed into or derived from any Layer 0 asset.
2. PyJHora is the engine source-of-truth (Layer 1); **no JH-parity oracle anywhere**; verification
   = internal consistency only.
3. No legacy dependency — anything touching the wiped system is rebuilt.
4. Classical texts stored **original (Sanskrit/source) + translation**.
5. Retrieval = **on-demand coherent bundles via tools**, never unlimited context; the agentic loop
   pulls depth adaptively.
6. **One capability tool per asset** (params for modes); a tool is part of the asset's contract —
   the asset isn't done until its tool exists.
7. **Provenance on every unit** — source + school + tier + confidence; everything citeable + reproducible.
8. **No Anthropic models in any production path.**

## §C — Tooling architecture (the standard for ALL layers)

**Certain consumers — the client is always an LLM in an agentic tool loop, via two transports:**
- **Internal (non-MCP):** the web consume loop's in-process LLM via provider adapters.
- **MCP:** external LLM agents/clients over the protocol.
- (Also: the verification swarm calls tools to audit.) Never a human directly; never build-code
  (build-code reads the DB directly).

**One canonical Tool Registry, two thin transports.**
- Each tool defined **once**: name · LLM-facing description (a contract — the model selects on it) ·
  typed input schema · output schema with a **provenance envelope** · handler.
- The MCP server and the internal loop are **auto-generated adapters** over the one registry — no
  divergence (the legacy failure was two separate tool sets that drifted).

**Three layers:** asset (Postgres/store) → **primitives** (internal typed functions; the real
"sub-tools", not LLM-facing) → **capability tools** (the registry; compose primitives). One
capability tool per asset, split into two only when intents differ (e.g. positions vs events).

**Designed for the agentic loop:**
- Token-economical outputs; large results → summary + stable IDs/handles + "fetch more" (on-demand bundles).
- Orthogonal + composable (chainable in the loop).
- Provenance on every output (source/version/school/confidence).
- Stateless, idempotent reads (reproducible).
- Instructive errors (loop self-heals).
- Tiering at the transport, not in tool logic (presentation in house-rules).
- A discovery **manifest** derived from the registry + capability metadata (asset/layer served,
  cost/latency class) for planning + observatory.

## §D — Storage philosophy

- **Store only the irreducible raw** (the ephemeris). **Derive everything else on read** —
  ayanamsha, sign/nakshatra, topocentric, exact events, panchang — **caching where reuse is high**.
- Reference/ontology/rule/concordance/text data are small-to-moderate and stored.
- Everything **content-addressed + version-pinned** → diffable, reproducible from raw.
- All structured data in Railway Postgres (+ pgvector for embeddings); blobs (text source files,
  uploads) in external object storage.

## §E — The eight assets (dependency order)

```
roots:   0.1 Ephemeris   0.2 Reference Library   0.3 Classical Texts   0.5 Ontology
derived: 0.4 Text Index  ← 0.3 (+0.5 tags)
         0.6 Rule Base   ← 0.3 + 0.5
         0.7 Concordance ← 0.6
         0.8 Almanac     ← 0.1 (+0.2)
```

## §F — Per-asset specifications

### 0.1 · Ephemeris — FULLY RESOLVED
- **Role:** the one global, geocentric, location-independent astronomical table; the raw everything
  derives from.
- **Library/source:** pyswisseph, ephemeris file **DE441** (full historical/future range); pinned.
- **Coverage:** **1800–2200**, **daily** sample at **00:00 UT**; record precise **Julian Day (TT)**.
- **Bodies (~14):** Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn; **Rahu + Ketu (mean) AND
  (true)** — default **mean**; **Uranus, Neptune, Pluto** (research/Western cross-ref).
- **Frame:** geocentric, **apparent** (light-time + aberration), **ecliptic of date**, stored in
  the **tropical** (canonical) frame.
- **Stored fields per body:** tropical longitude, latitude, distance, **longitudinal speed** (retro
  detection), **declination**.
- **Ayanamsha:** NOT baked into storage — applied **on read** from a versioned ayanamsha-definition
  table (Lahiri, KP/Krishnamurti, Raman, True Chitra, Surya Siddhanta, …). One dataset → all
  ayanamshas; new ayanamsha costs nothing; enables cross-ayanamsha + Jyotish-vs-Western comparison.
- **Topocentric:** geocentric stored; **topocentric applied on read** where a location exists
  (Moon parallax, ascendant/cusps, sunrise, KP — default topocentric inside KP work).
- **Granularity / events:** daily store for scanning; **exact events** (sign ingress, retrograde
  station, exact aspect/transit hit) computed **on demand** by root-finding between samples — NOT
  precomputed (avoids the stale-lifetime-table trap).
- **Precision/format:** high precision (microarcsecond integers / decimal strings) for **bit-stable**
  regeneration.
- **Determinism:** pin pyswisseph + DE441 + flags; **content-address** the dataset; record in
  provenance so any value is reproducible + blame-able.
- **Tools (2):** `ephemeris_positions(range, bodies, ayanamsha, frame)` ·
  `ephemeris_events(body, event_type{ingress|station|aspect|transit}, target, range)` — over shared primitives.
- **Consumers:** Daily Almanac, the Chart Engine (Layer 1), all transit/temporal work.
- **Acceptance:** dataset built 1800–2200 × 14 bodies; determinism (rebuild → identical hash);
  ayanamsha-on-read verified against known values; events root-find verified; tools live + provenance-bearing.

### 0.2 · Reference Library — DESIGN + open specifics
- **Role:** fixed classical lookup data as **versioned, queryable, cited DB tables** (no Python constants).
- **Tables:** ayanamsha definitions; dignity/exaltation/debilitation/moolatrikona; nakshatra
  attributes (lord, deity, gana, etc.); chakra grids — Sarvatobhadra (+vedha pairs), Sapta-Shalaka,
  Kalanala, Kota, CKN; Hadda/Ptolemaic bounds; Tajik aspect definitions; Mudda periods; year-lord
  (Panchadayadi) rules; aspect-angle definitions (Parashari/Western/Tajik).
- **Each row carries its source citation.** Tool: `reference.lookup(table, key)`.
- **OPEN:** final table list; DB tables vs versioned data-files-loaded-into-tables.

### 0.3 · Classical Texts — DESIGN + open specifics
- **Role:** primary-source corpus; citation ground-truth + raw material for rules. Drop all derived/legacy.
- **Canon (full):**
  - *Foundational:* BPHS, Jaimini Upadesha Sutras (all 4 Adhyayas), Brihat Jataka (+Bhattotpala),
    Saravali, Phaladeepika, Jataka Parijata, Sarvartha Chintamani, Hora Sara.
  - *Esoteric/high-signal:* Uttara Kalamrita, Prashna Marga, Daivajna Vallabha, Shatpanchashika,
    Yavana Jataka, Bhrigu Nandi Nadi, Chandra Kala Nadi/Deva Keralam, Saptarishi Nadi, Tajaka
    Neelakanthi (real edition) + a Varshaphala text, Muhurta Chintamani, Brihat Samhita.
- **Form:** **original (Sanskrit/source) + translation**, verse-addressable IDs (`BPHS.NN.NNN`),
  tiered, author/school/tradition/source provenance. Tool: `text.read(canonical_id | verse_ref)`.
- **OPEN:** final list + editions; untranslated/Sanskrit-only handling (translation/alignment pipeline); licensing per text.

### 0.4 · Text Index — DESIGN + open specifics
- **Role:** retrievable form of 0.3, one clean store (retire legacy dual stores).
- **Approach:** **hybrid** — verse-addressable exact lookup + lexical (BM25) + vector + cross-encoder
  **reranker**; tools return **coherent on-demand bundles** (topic rule-set, chapter, concordance set).
- **Embeddings:** pgvector + HNSW; multi-granularity (verse/chapter/principle). Tool:
  `corpus.search(query, filters{school,tier,topic}, bundle_mode)`.
- **OPEN:** embedding provider/model (Railway — managed vs self-hosted, see Infra §4); chunk
  granularity; reranker; bundle-size/fetch caps.

### 0.5 · Ontology — DESIGN + open specifics
- **Role:** shared controlled vocabulary across corpus, rules, reference, chart facts.
- **Contains:** canonical entities + stable IDs (grahas, rashis, bhavas, nakshatras, yogas, dashas,
  karakas, dignities, aspects, vargas) with synonyms/translations + relationships; fresh namespace
  (old FORENSIC §0 namespace wiped). Tool: `ontology.resolve(term)`.
- **OPEN:** depth/scope; formal graph vs controlled list + relations to start.

### 0.6 · Rule Base — DESIGN + open specifics
- **Role:** classical principles as reasoning units — the research multiplier.
- **Rule schema:** `{condition (chart pattern) → assertion (effect), source verse(s), school,
  scope/qualifiers, confidence, cross-refs}`; every rule traceable to its verse. Tool:
  `rules.match(chart_conditions)`.
- **OPEN:** extraction method (manual / LLM-assisted / hybrid) + review discipline; schema depth;
  coverage order (which texts first).

### 0.7 · Concordance — DESIGN + open specifics
- **Role:** map each topic across schools — agreement + divergence (the disagreements are the research value).
- **Contains:** per-topic entries linking rules across BPHS/Jaimini/KP/Tajaka/Nadi, tagged
  agree/qualify/conflict, with lineage. Tool: `concordance.lookup(topic)`.
- **OPEN:** topic taxonomy; conflict representation (surfaced, not flattened).

### 0.8 · Daily Almanac (Panchang) — RESOLVED as a Drik-Panchang SUPERSET
- **Role:** the panchang for any day **and any location** — computed off the global ephemeris at
  **local sunrise**; NOT a stored global table.
- **Mechanism:** function of **(date, location)** → compute local sunrise → sample ephemeris →
  derive all elements; **lazily computed + cached per (normalized-location, date)**; warm the cache
  per client location at chart build. Needs a **Locations table** (place_id → lat/lon/alt + IANA tz);
  robust sunrise (high-latitude/no-sunrise, DST history, half-hour zones).
- **Output — full Drik-Panchang superset (A–J mandatory; K optional):**
  - **A · Five limbs** with start/end + "next" rollovers: Tithi (+Paksha), Nakshatra, Yoga, Karana, Vara.
  - **B · Day markers:** Sunrise, Sunset, Moonrise, Moonset, day/night duration, Madhyahna.
  - **C · Calendar/frame:** lunar month (Amanta+Purnimanta), Ritu, Ayana, Samvatsara, Vikram &
    Shaka Samvat, Kali Ahargana, Sun-sign & Moon-sign rashi, Surya nakshatra.
  - **D · Auspicious muhurtas:** Abhijit, Amrit Kalam, Brahma Muhurta, Pratah/Sayahna Sandhya,
    Vijaya, Godhuli, Nishita; special yogas (Sarvartha Siddhi, Amrit Siddhi, Ravi, Dwipushkar/
    Tripushkar, Guru Pushya).
  - **E · Inauspicious:** Rahu Kalam, Yamaganda, Gulika, Dur Muhurtam, Varjyam, Baana, Gandanta,
    Bhadra/Vishti, Panchaka.
  - **F · Choghadiya:** day 8 + night 8, labelled.
  - **G · Hora:** 24 planetary hours.
  - **H · Bala:** Tarabalam (9-tara), Chandrabalam.
  - **I · Directional/classical:** Disha Shool, Nakshatra Shool, Anandadi Yoga, Shiva/Agni/Chandra
    Vas, Panchaka-rahita, Lagna timings through the day.
  - **J · Astronomical:** ayanamsha value, Sun/Moon longitudes, eclipse info.
  - **K (optional) · Festival/Vrat layer:** Ekadashi, Amavasya, Purnima, Sankashti, festivals, vrats, jayantis.
- **Exceeds Drik Panchang on:** all ayanamshas (not one), worldwide location, 1800–2200, raw-angle
  access, citeable + LLM-queryable integration with the chart.
- **NOT here:** birth-moment panchang (that's a Layer-1 chart fact).
- **Tool:** `almanac.query(date_range, location)`.
- **OPEN:** cache strategy (lazy vs warm-per-client); location-normalization granularity.

## §G — Build sequencing

1. **Ephemeris** (0.1) — root; everything astronomical depends on it.
2. **Reference Library** (0.2) + **Ontology** (0.5) — roots; parallel-safe.
3. **Classical Texts** (0.3) — root; then **Text Index** (0.4).
4. **Rule Base** (0.6) ← texts + ontology; then **Concordance** (0.7).
5. **Daily Almanac** (0.8) ← ephemeris (+reference).
- Each asset ships **with its capability tool + provenance + acceptance gate** (per the swarm charter).

## §H — Acceptance (per asset + layer)

- Per asset: built to spec; its capability tool live on **both transports** from the one registry;
  outputs carry provenance; internal-consistency checks pass; determinism where applicable.
- Layer: all eight assets green; tools discoverable in the manifest; the agentic loop can answer a
  Layer-0-only research query (e.g. "what do BPHS and Jaimini say about X, and where do they differ")
  end-to-end with citations.

## §I — Infrastructure

- Stay on **Google Cloud, cost-optimized scale-to-zero** (native decision 2026-06-02 — Railway
  reversed on cost). **Cloud Run** services (web, mcp, compute) with `min-instances=0`; **Cloud Run
  Jobs** for the worker/bootstrap/build; **Cloud SQL Postgres + pgvector** (no HA at this stage);
  **Vertex AI** embeddings; **GCS** for blobs; **Cloud Scheduler** for cron. No Anthropic models in
  prod. All specifics + the cost estimate tracked in `INFRASTRUCTURE_INVENTORY_v1_0.md`.

## §J — Provenance & verification

- Every stored/derived value + every tool output carries source + version + (school/tier/confidence
  where applicable). Verification is internal consistency only (no JH oracle). The build-guarantor
  swarm builds + audits each asset (Nirīkṣaka audit → Racayitā brief → build → review → deploy →
  runtime checks).

## §K — Consolidated OPEN decisions (close these → per-asset execution briefs)

1. **Ephemeris (0.1):** all resolved. ✓ (confirm DE441 vs DE440; date range 1800–2200 confirmed.)
2. **Reference Library (0.2):** final table list; DB-tables vs data-files.
3. **Classical Texts (0.3):** final canon + editions; untranslated-text handling; licensing.
4. **Text Index (0.4):** embedding provider/model; chunk granularity; reranker; bundle caps.
5. **Ontology (0.5):** depth + form (graph vs list+relations).
6. **Rule Base (0.6):** extraction method + review discipline; coverage order.
7. **Concordance (0.7):** topic taxonomy; conflict representation.
8. **Daily Almanac (0.8):** cache strategy; location normalization; whether K (festivals) is in scope.
9. **Tooling:** confirm one-registry / two-transport / capability-over-primitives as the standard. ✓ (native accepted)
10. **Infrastructure:** all items in `INFRASTRUCTURE_INVENTORY_v1_0.md` (Railway services, embeddings,
    object storage, jobs, CI/CD) — settled in one pass before execution.

---

*End of LAYER_0_PLAN_BRIEF v1.0 — DRAFT, 2026-06-02. 0.1 Ephemeris + 0.8 Panchang fully specified;
0.2–0.7 at design level with open items in §K. Close §K to generate per-asset Antigravity execution briefs.*
