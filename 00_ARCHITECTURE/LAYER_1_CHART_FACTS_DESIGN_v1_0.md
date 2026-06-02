---
artifact: LAYER_1_CHART_FACTS_DESIGN_v1_0.md
canonical_id: LAYER_1_CHART_FACTS_DESIGN
version: 1.0
status: CLOSED 2026-06-02 (design baseline — scope SEALED §E★ + storage in LAYER_1_STORAGE_STRATEGY; sealed in M5_REARCHITECTURE_DESIGN_CLOSE_v1_0; build phase next)
authored_by: Claude (Cowork) 2026-06-02
read_with:
  - 00_ARCHITECTURE/LAYER_0_FOUNDATION_DESIGN_v1_0.md (the foundation L1 sits on)
  - 00_ARCHITECTURE/LAYER_0_PLAN_BRIEF_v1_0.md (tooling + storage standards)
  - 00_ARCHITECTURE/ASSET_RECONCILIATION_v1_0.md (why L1 is 1 engine + 2 projections)
  - 00_ARCHITECTURE/FACT_ENGINE_A1_SCOPE_ANALYSIS_v1_0.md (the superset-of-v8.0 requirement)
purpose: >
  The full detailed design of Layer 1 (Chart Facts): the per-chart, deterministic fact layer — one
  engine computation projected two ways — that every higher layer rests on. Clean slate; no v8.0,
  no legacy chart_facts.
---

# Layer 1 — Chart Facts · Detailed Design

> **Project Brahma · external name: Gaṇita / Chart Facts.** Per BUILD_WORKFLOW_AND_TOOLING_DESIGN_v2_0 +
> BRAHMA_BUILD_UX_SPEC_v1_0: user-facing surfaces show "Gaṇita / Chart Facts" — never "L1" or asset codenames
> (internal docs keep L1 for precision). Gaṇita is the first layer a *client* build runs (over the global
> Brahmagyan). Its assets are built **with their retrieval tool(s)** — per-asset primitives close to the
> source (e.g. `query_positions`, `query_divisional`, `query_dasha`, `query_strength`, `query_sensitive_points`,
> `query_panchanga`) + composite tools (`query_chart_facts`) — deployed to web + MCP and tested against fresh
> data in the same swarm arc; verifies only when assets **and** tools pass, with a volume-floor amber gate
> scaled by the ayanamsha set.

## §A — What Layer 1 is

> **🔒 SCOPE LOCKED (2026-06-02).** The L1 content/asset scope is sealed: §E★ is the complete
> PyJHora fact surface (every `horoscope/*` + `panchanga/*` module accounted for; interpretive +
> unfinished modules explicitly excluded). No asset is to be added or dropped without re-opening
> this lock. What remains is *how* it's stored/structured + infrastructure — discussed next.

- **Per-chart + deterministic.** Everything here is computed for one chart from its birth data +
  Layer 0; nothing interpretive (that's Layer 2). Keyed by **(chart_id, ayanamsha_id, build_id)**.
- **Multi-ayanamsha by USER SELECTION.** The guest chooses which / how many ayanamshas at client
  creation (new-client form has an ayanamsha multi-select; default Lahiri ± KP). The engine computes
  the full fact set for exactly the selected set — build cost scales with the count. (Layer 0's
  ephemeris is tropical-at-source, so any selected ayanamsha is derivable.)
- **One computation, two projections.** The engine computes the complete fact set once → emits one
  **canonical JSONL** (the source of truth) → projected to a **Forensic Document** (read) and a
  **Fact Store** (query). A5–A9 and the deterministic temporal (old A18–A21, negative-space) are
  *fact categories of the engine*, not separate writers.
- **Clean slate.** No FORENSIC v8.0, no static `CHART_FACTS_EXTRACTION` YAML — both wiped. The new
  facts come only from the engine.

## §B — Governing rules

1. **PyJHora is the source of truth by construction** — no JH-parity oracle anywhere; verification
   is internal consistency only.
1a. **PyJHora-boundary rule (cross-layer):** PyJHora is invoked ONLY in the deterministic build layer
   — the L1 chart engine (+ the L0 location-almanac). It is **forbidden in the L2/L3 synthesis/
   derivation path** (those consume L1 facts, never the engine). L1 computes PyJHora's COMPLETE
   single-chart output; any PyJHora-derived calculation currently downstream **moves up to L1**.
   PyJHora's relational (compatibility) + dynamic (prasna, eclipse-finder, transit-window) functions
   are L1-OWNED capabilities exposed as tools/jobs — computed on demand, not stored per-chart facts.
2. **LEL stays isolated** — never an input to or output of any L1 fact.
3. **One computation → JSONL → two projections** (no fact parsed back out of a rendered doc — the
   old chart_facts-from-render bug never returns).
4. **Multi-ayanamsha, multi-location, multi-native** — chart_id + ayanamsha_id first-class.
5. **Provenance on every fact** (engine version, ephemeris version, ayanamsha, inputs hash, source rule).
6. **Tooling per the Layer 0 standard** — one registry, two transports (MCP + internal), capability
   tools over primitives.
7. **Content-addressed + deterministic** — rebuild → identical fact payload hash.

## §C — The three assets + architecture

```
birth data {datetime, lat, lon, tz}  +  Layer 0 (ephemeris, reference, ontology)
        │
        ▼
1.1  CHART ENGINE (PyJHora)  → computes the COMPLETE deterministic fact set → canonical JSONL
        │                                            (the source of truth)
        ├────────────► 1.2  FORENSIC DOCUMENT   (projection → markdown, read surface)
        └────────────► 1.3  FACT STORE          (projection → DB rows, query surface)
```

## §D — Per-asset detail

### 1.1 · Chart Engine (the keystone)
- **Role:** from birth data + Layer 0, compute the **complete deterministic per-chart fact set** and
  emit canonical JSONL.
- **Input contract:** `{ local civil datetime + IANA timezone (or UTC offset), latitude, longitude,
  altitude, place_label }` — generalized beyond IST; tz carried in provenance.
- **Engine:** PyJHora (the JH calculation logic in Python), pinned + content-addressed; wrapped in a
  typed adapter (no raw output reaches JSONL un-normalized).
- **Computes:** the full catalog in §E (positions → strength → dashas → KP → sensitive points →
  karakas → aspects → yogas → special charts → birth-panchang → Tajaka → merged temporal).
- **Engine ↔ Layer 0 boundary (design decision):** the engine computes **natal** facts directly
  (precise at the birth moment); the **lifetime/temporal** facts (bhrigu transits, exact-aspect
  lifetime, vedha firing, year-lords) **read Layer 0's ephemeris** rather than recompute — that's
  the dedup. Natal = engine; over-time = ephemeris.
- **Output:** one **canonical JSONL** per chart — one typed fact per line:
  `{fact_id, chart_id, ayanamsha_id, category, divisional_chart, value, unit, tier:"T1",
  provenance:{engine, engine_version, ephemeris_version, ayanamsha, inputs_hash, computed_at, source_rule}}`.
- **Multi-ayanamsha:** the full fact set is emitted per ayanamsha (ayanamsha_id on every fact).
- **Topocentric:** geocentric base; topocentric applied for natal Moon + ascendant/cusps + KP where precision matters.
- **Runs as:** a Cloud Run Job (scale-to-zero), deterministic, content-addressed; not an LLM-facing tool.
- **OPEN:** the exact enumerated fact catalog (§E is the draft — confirm scope); JSONL schema; which
  dasha systems beyond the core three; node default (mean); per-ayanamsha vs tropical-derive at engine level.

### 1.2 · Forensic Document
- **Role:** the human/LLM-readable rendered chart report — the successor to v8.0 (built fresh, not
  inherited), and it must **exceed** old v8.0's coverage.
- **Source:** a pure **projection of the engine JSONL** → markdown, section-organized, verse/ID-stable.
- **Presentation only:** no new computation at render time (the old render-time Jaimini matrix moves
  into the engine). Per ayanamsha (or a combined multi-ayanamsha document — open).
- **Tool:** `chart.read_document(chart_id, ayanamsha_id)`.
- **OPEN:** section structure; per-ayanamsha vs combined; whether it's stored (GCS) or rendered on demand.

### 1.3 · Fact Store
- **Role:** the same facts as **queryable DB rows** — the primary structured surface the synthesis
  tools read. Successor to `chart_facts`, **re-sourced from the engine JSONL** (never the old static YAML).
- **Keying:** (chart_id, ayanamsha_id, build_id, fact_id); typed `value_text/number/json` + category + provenance.
- **Loader:** deterministic JSONL → rows; schema-identical reload (a schema change re-runs the loader, not the engine).
- **Tool:** `chart.query_facts(chart_id, ayanamsha_id, category|fact_id, filters)`.
- **OPEN:** schema + category taxonomy; index strategy; how it aligns with the ontology (0.5) vocabulary.

## §E — The complete fact catalog (what the engine must compute)

Draft superset — exceeds old FORENSIC v8.0's 27 sections; this is the scope to confirm.

- **G1 · Positions & lagnas:** D1 graha positions (9 grahas + mean & true nodes + outers: lon, sign,
  degree, nakshatra, pada, house, retro, speed, dignity, avastha, combustion, graha-yuddha);
  ascendant + special lagnas (Hora, Ghati, Bhava, Vighati, Varnada, Shree, Pranapada, Indu).
- **G2 · Houses:** bhava cusps (Sripathi), whole-sign, bhava-chalit, house lords, chalit kinetic shifts.
- **G3 · Divisional charts (Shodasavarga):** D2–D60 (D2,3,4,7,9,10,12,16,20,24,27,30,40,45,60) positions;
  vargottama; D9 detail; cross-varga dignity / Vimsopaka Bala.
- **G4 · Strength:** Shadbala (6 components + totals/ranks), Bhava Bala, Ishta/Kashta Phala,
  Ashtakavarga (BAV per planet + SAV + Shuddha Pinda), Saturn kakshya.
- **G5 · Dashas:** Vimshottari (MD/AD/PD/SD), Yogini, Jaimini Chara; additional systems (Ashtottari,
  Kalachakra, …) — scope TBD.
- **G6 · KP system:** 12 cusps + star/sub/sub-sub lords, planetary significators, house significators, ruling planets.
- **G7 · Sensitive points:** Upagrahas (Gulika, Mandi, Yamaghantaka, Ardhaprahara, Dhuma, Vyatipata,
  Parivesha, Indrachapa, Upaketu), Bhrigu Bindu, Yogi/Avayogi, 36 Sahams, Arudhas (AL + A2–A12 + UL).
- **G8 · Chara Karakas:** 7-karaka + 8-karaka systems; Sthira Karakas.
- **G9 · Aspects:** Parashari graha drishti, Jaimini rasi drishti, Western tight-orb, Bhav-Madhya.
- **G10 · Yogas & Doshas:** full register (Raj/Dhan/Pancha-Mahapurusha/Nabhasa/Parivartana/etc. + doshas + cancellations).
- **G11 · Special charts & diagnostics:** Chandra chart, Kota chakra, Sarvatobhadra firing, Navatara
  (9-tara), Avastha schemes, Deity assignments, Longevity (Kalachakra Paramayush / Ayurdaya).
- **G12 · Birth panchang:** tithi, vara, nakshatra, yoga, karana at the birth moment + Avakahada chakra.
- **G13 · Tajaka / Varshaphal:** annual charts, Muntha, year-lord, Hadda, annual Sahams.
- **G14 · Merged deterministic temporal (folded from old A18–A21 + negative-space — read Layer 0 ephemeris):**
  Bhrigu Bindu lifetime transits, per-graha exact-aspect lifetime, Vedha firing windows, Tajik
  year-lords lifetime, structural negative-space (absence detection).
- **G15 · Full dasha suite (~36–40 systems, per PyJHora):** Vimshottari, Ashtottari, Yogini,
  Shodasottari, Dwadasottari, Dwisatpathi, Panchottari, Satabdika, Chaturaseeti-sama, Shashtisama,
  Shattrimsa-sama, Naisargika, Tara, Karaka, Narayana, Kendradi-rasi, Sudasa, Drig, Nirayana-Shoola,
  Kendradi-karaka, Chara, Lagnamsaka, Padanadhamsa, Mandooka, Sthira, Brahma, Varnada, Yogardha,
  Navamsa, Paryaya, Trikona, Kalachakra, Ashtakavarga-dasha (graha+rasi), + tithi/yoga/kaala variants.
- **G16 · Sphuta family:** tri, chatur, pancha, prana, deha, mrityu, sooshma-tri, beeja, kshetra,
  tithi, yoga, yogi, avayogi, rahu-tithi sphutas.
- **G17 · Full bala decomposition:** Harsha bala + sapthavargaja, ojayugma, uccha-rashmi, hadda,
  pancha/dwadasa-vargeeya, cheshta-rashmi, and all bhava balas (beyond G4's core shadbala).
- **G18 · Yoga register — 284 named yogas** (incl. 186 B.V. Raman) + raja-yoga module + doshas/cancellations.
- **G19 · Extended charts:** custom Dn + mixed/sub-divisional (DmxDn) charts; amsa rulers; Vaiseshikamsa
  varga bala; 10 house systems (Equal, Sripati, KP, Placidus, Koch, Porphyrius, Regiomontanus, Campanus,
  Alcabitus, Morinus).
- **G20 · Chakras:** kota, kaala, sarvatobhadra, surya-kalanala, chandra-kalanala, shoola, tripataki.
- **G21 · Conception & returns:** Nisheka (conception) time; tithi-pravesha (annual return).

**L1-owned PyJHora capabilities (computed on demand via L1 tools, NOT stored per-chart facts):**
transit/gochara engine (entry/transit dates, conjunctions, retrograde paths, stationary detection,
planet-entry-into-varga); eclipse finder (solar/lunar, type, local/global); prasna/horary (Prasna
Lagna 108 / KP 249 / Naadi 1800); marriage compatibility (Ashta Koota + South Indian — relational,
two-chart); vratha/festival finder + combo date-search (overlaps the L0 almanac K layer);
nisheka (conception); tithi-pravesha (annual return); Pancha Pakshi Sastra. Hijri/Tamil calendars optional.

## §E★ — DEFINITIVE PyJHora fact catalog (AUTHORITATIVE — supersedes the draft groups above)

Built from the full PyJHora module tree (`jhora/horoscope/*` + `jhora/panchanga/*`). This is the
complete stored-fact surface; the draft groups G1–G21 are consolidated here.

STORED L1 FACTS (deterministic, chart-intrinsic), by source module:
- **charts.py:** all divisionals (16 standard + custom Dⁿ + mixed Dmx·Dⁿ); combustion/retrograde/
  stationary/planetary-war; amsa rulers; Vaiseshikamsa varga bala; bhava chart (3 house systems:
  Whole-Sign, Sripati, Placidus); 64th navamsa; 22nd drekkana; graha drekkana; outers (U/N/P).
- **house.py:** Parashari graha drishti; Jaimini rasi drishti; stronger planet/rasi; chara karakas
  (7+8); Marana Karaka Sthana.
- **strength.py:** planetary relationships (natural + temporal + compound Panchadha-Maitri); Shadbala;
  Harsha / Pancha-Vargeeya / Dwadasa-Vargeeya; Bhava bala; Ishta/Kashta.
- **ashtavarga.py:** BAV, SAV, Trikona Sodhana, Ekadhipatya Sodhana, Sodhya Pinda, Kakshya.
- **sphuta.py:** tri, chatur, pancha, prana, deha, mrityu, sooshma-tri, beeja, kshetra, tithi, yoga, rahu-tithi.
- **arudhas.py:** Arudha padas (AL, A2–A12, UL); Argala; Virodhargala.
- **yoga.py / raja_yoga.py / dosha.py:** 284 yogas; raja-yoga sub-types (Dharma-Karmadhipati,
  Vipareeta, Neecha-Bhanga); 8 doshas (Kala Sarpa, Manglik, Pitru, Guru Chandala, Ganda Moola,
  Kalatra, Ghata, Shrapit).
- **dhasa/:** the 12 selected (nakshatra: Vimshottari, Yogini, Kalachakra, Tara; rasi/Jaimini: Chara,
  Narayana, Sudasa, Mandooka, Sthira, Brahma, Trikona, Kendradi-Rasi) to **MD/AD/PD/SD** depth; plus
  **Sudarshana Chakra dasha**, **Aayu dasha**, and Tajaka annual **Mudda + Patyayini**.
- **transit/tajaka.py + tajaka_yoga.py + saham.py:** annual/monthly/60-hour charts; Muntha; vargeeya
  balas; year/month/hour lords; Tajaka yogas (Ithasala, Ishrafa…); deeptamsa; 36 Sahams.
- **panchanga/drik.py (birth):** 5 limbs at birth; 12 special tithis; Avakahada; nava/special thaara;
  karaka tithi/yogam; triguna; upagrahas; Bhrigu Bindu; Yogi/Avayogi; special lagnas.
- **longevity:** Kalachakra Paramayush; structural Ayur; Sahasra Chandrodaya.

OUT (interpretive/experimental — not L1): prediction/ (general, longevity, naadi_marriage — experimental);
khanda_khaadyaka + surya_sidhantha (not fully implemented). KP "dasha" = Vimshottari (already in) read
through the KP system (G6) on the KP ayanamsha — no separate algorithm.

## §F — Tooling (per Layer 0 standard)

- **Capability tools (LLM-facing, both transports):** `chart.query_facts` · `chart.read_document` ·
  plus targeted facet tools only where intent differs (e.g. `chart.dashas`, `chart.divisional`,
  `chart.strength`) — kept minimal, backed by primitives over the Fact Store.
- **The engine build itself is a Job, not a tool** (it writes facts; it isn't queried by the LLM).
- Outputs carry provenance; token-economical; on-demand bundles.

## §G — Build mechanics

- The engine runs per chart as a **Cloud Run Job** (scale-to-zero), per ayanamsha, content-addressed,
  deterministic (rebuild → identical hash). Emits JSONL → loader → Fact Store; renderer → Forensic Document.
- Consumes Layer 0 (ephemeris, reference, ontology) + birth input. Writes keyed by (chart_id, ayanamsha_id, build_id).

## §H — Provenance & verification

- Every fact carries engine/ephemeris/ayanamsha/inputs-hash provenance. Verification = internal
  consistency only (row/coverage counts vs the §E catalog, schema, structural invariants — Rahu/Ketu
  opposition, 120-yr Vimshottari span, vargottama rules — determinism, cross-asset FK). No JH oracle.
- Built + audited by the build-guarantor swarm (Nirīkṣaka → Racayitā → build → review → runtime checks).

## §I — Open decisions (to debate, then bake into the Layer 1 plan brief)

1. **Fact catalog (§E):** confirm the full scope; any domains to add/cut; which dasha systems (G5);
   how deep the yoga register (G10).
2. **JSONL schema** + the Fact Store schema/category taxonomy + ontology alignment.
3. **Engine ↔ Layer 0 boundary** — confirm natal=engine, temporal=ephemeris.
4. **Multi-ayanamsha model** at engine level (per-ayanamsha compute vs tropical-derive); node default.
5. **Forensic Document:** section structure; per-ayanamsha vs combined; stored vs on-demand.
6. **Topocentric** for natal Moon/ascendant/KP — confirm.
7. **Tool surface** — the minimal capability-tool set for L1.
8. **Input contract** — confirm local-civil + IANA tz (multi-native generality).

## §J — Storage strategy (LOCKED 2026-06-02)

> **Authoritative detail: `LAYER_1_STORAGE_STRATEGY_v1_0.md`** — full data-engineering spec (the typed
> category-organized Postgres schema, the JSONL format, the loader, relationships as first-class rows,
> the per-category retrieval tools). The summary below points there.

Four representations, each with a defined job; **RAG is NOT used for L1 facts** (the legacy
JSONL→MD→chunk→RAG path is rejected — every downstream consumer does exact structured retrieval).

1. **JSONL → GCS** — canonical artifact, content-addressed per (chart_id, ayanamsha_id, build_id);
   source of truth; loaded, never queried at runtime.
2. **Fact Store → Cloud SQL Postgres** (loaded from JSONL) — **the primary downstream surface**; a
   **typed, category-organized schema** (NOT a generic key-value table) — ~20 tables by category
   (positions, houses, vargas, dashas, strength, ashtakavarga, aspects, yogas, doshas, …) keyed by
   (chart_id, ayanamsha_id, build_id), with **relationships as first-class rows** (aspects/friendships)
   traversed via recursive SQL. The L2 rule engine, L3, and the per-category L1 tools read this. (Full
   spec in `LAYER_1_STORAGE_STRATEGY_v1_0.md`.)
3. **Forensic MD → GCS** (rendered from JSONL) — human report + optional LLM full-context bundle;
   not a chunking source.
4. **RAG/embeddings → reserved for L0 texts, not L1 facts.** Optional: embed forensic-MD sections
   only for a narrative fallback; default off.

**Dasha depth — LOCKED to SUKSHMA (SD):** all 12 dashas stored MD/AD/PD/SD (native, 2026-06-02;
mandatory — the PD-store/SD-on-demand option was considered and rejected). This is the volume driver
(~80–90k dasha-period rows / chart / ayanamsha).

**Volume:** ~60,000–100,000 fact rows / chart / ayanamsha (~15–30 MB Postgres) + ~10–30 MB GCS
artifacts. At research scale (~20 clients × 2 ayanamshas) ≈ a few GB Postgres — within the GCP
envelope; Cloud SQL storage grows linearly. Per-chart build ≈ a few cents on a Cloud Run Job.

---

*End of LAYER_1_CHART_FACTS_DESIGN v1.0 — DRAFT for native review, 2026-06-02. Same drill as Layer 0:
debate §I, close each, then the Layer 1 plan brief.*
