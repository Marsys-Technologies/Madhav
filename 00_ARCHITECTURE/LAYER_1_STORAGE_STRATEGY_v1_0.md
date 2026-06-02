---
artifact: LAYER_1_STORAGE_STRATEGY_v1_0.md
canonical_id: LAYER_1_STORAGE_STRATEGY
version: 1.0
status: CLOSED 2026-06-02 (design baseline — sealed in M5_REARCHITECTURE_DESIGN_CLOSE_v1_0; build phase next)
authored_by: Claude (Cowork) 2026-06-02
supersedes_summary: LAYER_1_CHART_FACTS_DESIGN_v1_0.md §J (which now points here)
read_with:
  - 00_ARCHITECTURE/LAYER_1_CHART_FACTS_DESIGN_v1_0.md (the locked fact catalog §E★)
  - 00_ARCHITECTURE/LAYER_2_SYNTHESIS_DESIGN_v1_0.md (the rule engine / synthesis consumers)
  - 00_ARCHITECTURE/INFRASTRUCTURE_INVENTORY_v1_0.md (GCP / Cloud SQL)
purpose: >
  The complete data-engineering + storage specification for Layer 1 chart facts: how PyJHora's JSONL
  output is engineered, stored, related, and served to the downstream consumers (the L2 rule engine,
  L3 temporal, and the query-time LLM via L1's own retrieval tools over MCP + API). Self-contained:
  consumers, formats, the typed schema, relationships, the loader, tools, volumes, cost, and the
  options rejected with reasons.
---

# Layer 1 — Storage & Data-Engineering Specification

## §1 — Context & the design constraint

L1 is the per-chart deterministic fact layer (catalog locked in `LAYER_1_CHART_FACTS_DESIGN §E★`).
Its storage exists to serve three consumers, and *their* access patterns dictate the design:

1. **The L2 rule engine (MSR).** At build time it evaluates thousands of classical rules (from the L0
   Rule Base) against one chart's facts. A rule is a **typed predicate over structured fields** plus
   **relationship traversal** (dispositor chains, "what aspects house N," yoga membership). Batch,
   per chart, per ayanamsha.
2. **L3 temporal.** Structured reads of specific facts + the L0 ephemeris.
3. **The query-time LLM, via L1's own retrieval tools (MCP + internal API).** Exact lookups,
   category/house-scoped fetches, and relationship queries — token-economical, provenance-bearing.

**The common denominator: all three do typed, structured, relationship-aware querying. None does
semantic search over facts.** That single fact drives every decision below.

## §2 — Decisions (and the options rejected)

| Option | Decision |
|---|---|
| Generic key-value table (old `chart_facts`) | **REJECTED** — awkward for a rule engine + typed tools; nothing typed; relationships not first-class. |
| Document/JSONB-per-chart only | **REJECTED as the primary** — clumsy for complex predicates + traversal (used only for nested detail *within* typed tables). |
| Graph database (Neo4j etc.) | **REJECTED** — a chart's graph is tiny (≈9 planets, 12 houses); Postgres recursive CTEs cover traversal; a graph DB adds non-GCP infra for no gain. |
| RAG / embeddings over facts | **REJECTED** — facts are precise; structured retrieval wins; RAG reserved for L0 texts. |
| **Typed, category-organized relational schema + JSONB for nesting + first-class relationship rows** | **ADOPTED.** |

Engine: **Cloud SQL for PostgreSQL** (GCP-native; relational + JSONB + recursive CTEs; serves the
batch rule engine and the point-query tools alike).

## §3 — The pipeline (end to end)

```
PyJHora (Cloud Run Job, per chart × selected ayanamshas)
   │   computes the full §E★ catalog
   ▼
canonical JSONL  ──────────────►  GCS (content-addressed: hash(engine_ver+ephem_ver+ayanamsha+inputs))
   │  (also loaded in-memory by the L2 rule engine at build time)
   ▼
deterministic LOADER  ─────────►  TYPED FACT STORE (Cloud SQL Postgres)   [the queryable truth]
   │
   └── deterministic RENDERER ──►  FORENSIC MD  ─────────►  GCS            [human / full-context]
```

- **JSONL has a dual role:** the audit/reproducibility artifact **and** the L2 rule engine's direct
  build-time input (loaded into memory; rules evaluate in-process — no per-rule DB round-trips).
- The DB is a **reproducible projection** of the JSONL; a schema change re-runs the loader, not the engine.

## §4 — The canonical JSONL format

Newline-delimited JSON, **one typed fact per line** (diffable, blame-able, content-addressed):

```json
{"fact_id":"PLN.MERCURY.D1.LON_DEG","chart_id":"<uuid>","ayanamsha_id":"lahiri",
 "category":"positions","subject":"mercury","key":"lon_deg","divisional_chart":"D1",
 "value":283.4471122,"unit":"deg","value_type":"number",
 "provenance":{"engine":"pyjhora","engine_version":"x.y.z","ephemeris_version":"de441",
   "ayanamsha":"lahiri","inputs_hash":"<sha256>","computed_at":"<iso>","source_rule":"drik.sidereal_longitude"}}
```

- `value_type` ∈ number | text | bool | json. Nested/composite facts carry `value_type:"json"`.
- Exact astronomical values stored as **decimal strings or integer micro-arcseconds** for bit-stable
  regeneration. The loader routes each record to its typed table by `category` (+ `subject`/`key`).

## §5 — The typed Fact Store schema

**Every table is keyed by `(chart_id, ayanamsha_id, build_id)`** plus its natural key, and carries a
`provenance jsonb` column. Typed columns for the queryable dimensions; `extra jsonb` for nested detail.

| Table | Grain (one row per …) | Key typed columns |
|---|---|---|
| **positions** | graha | graha, sign, sign_id, lon_deg, lat_deg, speed, retrograde, nakshatra, nak_pada, nak_lord, house_ws, house_chalit, dignity, combust, combust_orb, graha_yuddha_with, declination |
| **lagnas** | special lagna | lagna_type (ascendant/bhava/hora/ghati/vighati/varnada/shree/pranapada/indu), sign, lon_deg, house |
| **houses** | (house, system) | house_num, system (whole_sign/sripati/placidus), cusp_deg, sign, sign_lord, bhava_bala, sav_score, occupants(jsonb) |
| **vargas** | (varga, graha) | varga (D1…D60, custom), graha, sign, sign_id, house, vargottama, dignity |
| **dashas** | period | system, level (MD/AD/PD/SD), lord, start_jd, end_jd, start_date, end_date, parent_period_id |
| **strength** | (graha, bala) | graha, bala_type (shadbala comp / harsha / pancha-vargeeya / dwadasa-vargeeya / ishta / kashta / cheshta…), value, unit |
| **ashtakavarga** | (graha, sign) + reductions | graha, sign, bindus; sav_total; trikona_sodhana, ekadhipatya_sodhana, sodhya_pinda (jsonb) |
| **aspects** *(relationship)* | aspect edge | src_type, src, tgt_type, tgt, system (parashari/jaimini/western/bhav-madhya), kind (full/special/angle), orb, strength |
| **yogas** | yoga | yoga_name, yoga_type (raja/dhana/nabhasa/mahapurusha/raja-subtype…), present, strength, citation, constituents(jsonb) |
| **doshas** | dosha | dosha_name (kala_sarpa/manglik/pitru/guru_chandala/ganda_moola/kalatra/ghata/shrapit), present, severity, constituents(jsonb), cancellation(jsonb) |
| **sphutas** | sphuta | sphuta_type (tri/chatur/pancha/prana/deha/mrityu/sooshma/beeja/kshetra/tithi/yoga/rahu_tithi), lon_deg, sign, nakshatra |
| **karakas** | (role, system) | system (7/8), role (AK/AmK/BK/MK/PiK/PK/GK/DK / sthira), graha, lon_deg |
| **sensitive_points** | point | point_type (upagraha/bhrigu_bindu/yogi/avayogi), name, sign, lon_deg, house |
| **sahams** | saham | saham_name (36 types), sign, lon_deg, house, lord |
| **arudhas** | arudha | arudha_name (AL/A2…A12/UL), sign, house; argala/virodhargala(jsonb) |
| **relationships** *(relationship)* | (graha_a, graha_b) | graha_a, graha_b, natural, temporal, compound_panchadha |
| **special_points** | point | kind (64th_navamsa / 22nd_drekkana / marana_karaka_sthana), graha/house, detail(jsonb) |
| **chakras** | chakra | chakra_type (chandra/kota/sarvatobhadra/navatara), payload(jsonb) |
| **birth_panchang** | chart | tithi, paksha, vara, nakshatra, yoga, karana, special_tithis(jsonb), avakahada(jsonb), thaara(jsonb) |
| **tajaka** | varsha_year | year, annual_chart_ref, muntha_sign, muntha_lord, year_lord, hadda_lord, vargeeya_balas(jsonb), tajaka_yogas(jsonb), annual_sahams(jsonb) |
| **longevity** | chart | kalachakra_paramayush, ayur_scheme, sahasra_chandrodaya, detail(jsonb) |
| **misc_facts** | fact | category, subject, key, value_*, — minimal generic catch-all for true long-tail only |

Indexes: every table on `(chart_id, ayanamsha_id, build_id)`; plus query-shaped indexes — e.g.
`positions(house_ws)`, `positions(sign_id)`, `dashas(system, level, start_date)`,
`dashas(parent_period_id)`, `aspects(tgt_type, tgt)`, `yogas(present)`, `vargas(varga, graha)`.

## §6 — Relationships as first-class rows (no graph DB)

The relationships the rule engine and LLM need are **rows**, not a separate store:
- **aspects** — every drishti/aspect edge (graha→house, graha→graha, by system).
- **rulership** — derivable (`houses.sign_lord`, sign→lord reference) → a view, not a table.
- **relationships** — natural/temporal/compound planetary friendships.

Multi-hop traversal (dispositor chains, "everything connected to the 10th") is done with **recursive
CTEs** over these rows. Example — Mercury's dispositor chain:

```sql
WITH RECURSIVE chain AS (
  SELECT graha, sign, sign_lord FROM positions p JOIN ref_sign_lord r USING(sign)
  WHERE p.graha='mercury' AND p.chart_id=$1 AND p.ayanamsha_id=$2
  UNION ALL
  SELECT p.graha, p.sign, p.sign_lord FROM chain c JOIN positions p ON p.graha=c.sign_lord …)
SELECT * FROM chain;
```

A chart's relationship set is tiny, so this is fast — no graph database is warranted.

## §7 — The deterministic loader

- **Idempotent upsert** by natural key + `(chart_id, ayanamsha_id, build_id)`; re-running a build with
  the same inputs is a no-op (content-addressed).
- **Schema-validated** against the JSONL fact schema before insert; unknown categories → `misc_facts`
  + a loader warning (never silently dropped).
- **Atomic per build:** load into staging, validate row counts vs the §E★ catalog (per-ayanamsha
  expected counts), then swap. A failed validation aborts the build (no partial chart).
- A schema migration re-runs the loader from the stored JSONL — the engine is not re-invoked.

## §8 — The Forensic MD projection

- A separate deterministic renderer off the same JSONL → a section-organized markdown report in GCS,
  per (chart_id, ayanamsha_id). Human report + an optional "full-context" bundle the LLM can pull when
  it explicitly wants everything. **Not chunked, not embedded, not a query source.**

## §9 — L1 retrieval tools (the LLM's interface)

L1 is **self-contained** — it ships its own retrieval tools (it does not depend on L2 to be queried).
Per the L0 tooling standard: defined once in the canonical registry, exposed via **MCP + internal API**,
capability-over-primitives, typed I/O with a provenance envelope, token-economical bundles.

- **Per-category capability tools** (one family per typed table): `query_positions`, `query_houses`,
  `query_vargas`, `query_dashas`, `query_strength`, `query_ashtakavarga`, `query_aspects`,
  `query_yogas`, `query_doshas`, `query_sphutas`, `query_karakas`, `query_sensitive_points`,
  `query_sahams`, `query_arudhas`, `query_relationships`, `query_chakras`, `query_birth_panchang`,
  `query_tajaka`, `query_longevity`. Each: filter by the typed dimensions, return rows + provenance.
- **A traversal tool:** `query_chart_relationships` (recursive CTE over aspects/rulership/relationships).
- **On-demand PyJHora capability tools (compute, not stored):** `transit`, `eclipse_finder`,
  `prasna`, `compatibility`, `vratha_finder`, `tithi_pravesha`, `nisheka` — these invoke the engine
  on demand (per the PyJHora-boundary rule, the engine is L1-owned).
- A **read-document** tool returns the Forensic MD (full-context bundle).

## §10 — Multi-ayanamsha & keying

- The guest selects the ayanamsha set at client creation; the engine computes the full catalog per
  selected ayanamsha; every fact row carries `ayanamsha_id`. Tools default to the chart's primary
  ayanamsha and accept an explicit `ayanamsha_id` to compare across ayanamshas (a research feature).
- `build_id` versions every build; the latest build per (chart_id, ayanamsha_id) is the active one;
  prior builds retained for audit/diff.

## §11 — Volume & cost (recap)

- ~60,000–100,000 fact rows / chart / ayanamsha; **dashas to SD depth are the driver** (~80–90k of it).
- ~15–30 MB Postgres / chart / ayanamsha (with indexes); JSONL+MD artifacts ~10–30 MB in GCS.
- Research scale (~20 clients × 2 ayanamshas): a few GB Postgres, within the GCP cost envelope
  (~$55–95/mo); Cloud SQL storage grows linearly; per-chart build a few cents on a Cloud Run Job.

## §12 — Provenance & verification

- Every row carries `provenance` (engine/ephemeris/ayanamsha/inputs_hash/source_rule).
- Verification = internal consistency only: per-category row counts vs §E★, schema/constraint checks,
  structural invariants (Rahu–Ketu opposition, 120-yr Vimshottari span, vargottama rules),
  determinism (rebuild → identical payload hash), FK integrity. No JH oracle. Audited by the swarm.

---

*End of LAYER_1_STORAGE_STRATEGY v1.0 — DRAFT for native review, 2026-06-02. Authoritative L1
storage/data-engineering spec; supersedes the §J summary in the L1 design view.*
