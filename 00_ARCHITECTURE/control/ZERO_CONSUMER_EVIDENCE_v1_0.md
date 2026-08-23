# NIRMĀṆA M0-T6 (Phase 0.8c) — Zero-Consumer Evidence Packets

**Generated:** 2026-08-23T04:45:12.456753Z  
**Source of every number below:** `00_ARCHITECTURE/control/CONSUMER_MAP.json` and `00_ARCHITECTURE/control/zero_consumer_evidence.json` (both machine-generated, read-only DB).  
**Method and its limits:** `00_ARCHITECTURE/control/CONSUMER_MAP.md` §1–§2. Read them before acting on any packet here — several findings below exist *because* of a named method limit.  
**Status:** evidence only. **No disposition is proposed and none is taken.** Promote / retire / reclassify is ADHIKĀRIN's G1 power (charter §1), on this evidence. This document certifies nothing (I16 / charter H7).

---

## 0 — Reconciliation with the plan's "13"

The plan states, in §1 (carried from v3.0 §1 and its Phase 0.8c row), that **13 assets have no detected consumer**. That figure was not re-derived here; it was checked, and it does not reconcile in either direction:

- **The plan's own per-asset annotation names 7, not 13.** `grep -c "No detected serving consumer (Phase 0.8c)" 00_ARCHITECTURE/NIRMANA_ELEVATION_PLAN_v4_0.md` returns **7**: `bg_cohort`, `bg_concordance`, `bg_gochara_arcs`, `bg_kota_chakra_rings`, `bg_kp_sublord_division`, `bg_sky_calendar`, `ka_gochara_v3_century_materialize`. The same grep against `NIRMANA_ELEVATION_PLAN_v3_0.md` also returns 7. The summary figure 13 and the per-asset annotation count 7 disagree *inside the plan itself*.
- **This pass finds 23**, by a method whose limits are written down. All 7 of the plan-annotated assets are in that set; the other 16 are additional.

Neither figure is asserted here to be the right one. What is asserted is that the plan's 13 is not a checkable number as it stands — it has no per-asset list behind it — and that a disposition decision should rest on the per-asset packets below rather than on any headline count. (This mirrors the V-2 finding pattern: a plan figure that does not survive re-derivation.)

## 1 — How to read a packet

Each packet carries five things: what the asset produces (measured, not claimed), what a consumer would plausibly be, what was searched and not found, the live DB shape, and a **reading of the absence**. The reading is one of five values, kept apart on purpose because they call for different decisions:

| reading | meaning |
|---|---|
| INPUT-ONLY | consumed by writers, not by a served surface. Absence of a serving consumer is the design. |
| NO CONSUMER FOUND | no writer, no surface, no capability, no view. The absence looks real. |
| METHOD-BLIND | a serving path plausibly exists that this method structurally cannot see. UNKNOWN, not zero. |
| SHADOWED | a served surface carrying the asset's name exists, but the code behind it does not read the asset. |
| BY DESIGN EMPTY / CATEGORY MISMATCH | the question as posed does not apply to the row in its current form. |

The reading is **this KĀRAKA's reading of the cited evidence**, not a verdict and not a disposition. Every packet's evidence is quoted with a file:line or a query result so the reading can be overturned cheaply.

## 2 — Summary

| asset | layer | status | kind | evidence class | reading |
|---|---|---|---|---|---|
| [`bg_cohort`](#bg-cohort) | brahmagyan | CURRENT | data | writer_consumer_only | INPUT-ONLY |
| [`bg_concordance`](#bg-concordance) | brahmagyan | CURRENT | data | statements_only_in_non_serving_buckets | NO CONSUMER FOUND |
| [`bg_ephemeris_engine`](#bg-ephemeris-engine) | brahmagyan | CURRENT | data | UNKNOWN_no_table_declared | BY DESIGN EMPTY / CATEGORY MISMATCH |
| [`bg_gochara_arcs`](#bg-gochara-arcs) | brahmagyan | CURRENT | data | writer_consumer_only | INPUT-ONLY |
| [`bg_kota_chakra_rings`](#bg-kota-chakra-rings) | brahmagyan | CURRENT | data | writer_consumer_only | INPUT-ONLY |
| [`bg_kp_sublord_division`](#bg-kp-sublord-division) | brahmagyan | CURRENT | data | writer_consumer_only | INPUT-ONLY |
| [`bg_panchanga`](#bg-panchanga) | brahmagyan | CURRENT | data | UNKNOWN_no_table_declared | METHOD-BLIND |
| [`bg_phaladeepika_latta`](#bg-phaladeepika-latta) | brahmagyan | CURRENT | data | writer_consumer_only | INPUT-ONLY |
| [`bg_reference`](#bg-reference) | brahmagyan | CURRENT | data | writer_consumer_only | INPUT-ONLY |
| [`bg_sarvatobhadra_grid`](#bg-sarvatobhadra-grid) | brahmagyan | CURRENT | data | writer_consumer_only | BY DESIGN EMPTY / CATEGORY MISMATCH |
| [`bg_sky_calendar`](#bg-sky-calendar) | brahmagyan | CURRENT | data | UNKNOWN_reads_exist_but_unattributed | METHOD-BLIND |
| [`bg_vedha_malefic_scale`](#bg-vedha-malefic-scale) | brahmagyan | CURRENT | data | writer_consumer_only | INPUT-ONLY |
| [`bg_vidhi_floors`](#bg-vidhi-floors) | brahmagyan | DRAFT | data | statements_only_in_non_serving_buckets | SHADOWED |
| [`bg_vidhi_primitives`](#bg-vidhi-primitives) | brahmagyan | DRAFT | data | statements_only_in_non_serving_buckets | SHADOWED |
| [`bo_cdlm_summary`](#bo-cdlm-summary) | bodha | DRAFT | data | writer_consumer_only | METHOD-BLIND |
| [`bo_samskara`](#bo-samskara) | bodha | CURRENT | data | writer_consumer_only | METHOD-BLIND |
| [`ka_dasha_kala`](#ka-dasha-kala) | kala | DRAFT | service | writer_consumer_only_via_code_module | SHADOWED |
| [`ka_gochara_v3_century_materialize`](#ka-gochara-v3-century-materialize) | kala | CURRENT | data | writer_consumer_only | INPUT-ONLY |
| [`ka_graha_sancara`](#ka-graha-sancara) | kala | DRAFT | service | writer_consumer_only_via_code_module | METHOD-BLIND |
| [`ka_kshetra`](#ka-kshetra) | kala | CURRENT | data | writer_consumer_only | METHOD-BLIND |
| [`ka_muhurta_seva`](#ka-muhurta-seva) | kala | DRAFT | service | writer_consumer_only_via_code_module | SHADOWED |
| [`ka_tulana`](#ka-tulana) | kala | DRAFT | service | UNKNOWN_no_table_declared | SHADOWED |
| [`mi_jivanaghatana`](#mi-jivanaghatana) | mimamsa | DRAFT | data | writer_consumer_only | METHOD-BLIND |

Reading distribution: **INPUT-ONLY** 8 · **METHOD-BLIND** 7 · **SHADOWED** 5 · **BY DESIGN EMPTY / CATEGORY MISMATCH** 2 · **NO CONSUMER FOUND** 1.

## 3 — Packets

### bg_cohort

`bg_cohort` — layer `brahmagyan` · `CURRENT` · `asset_kind=data` · `is_active=True` · `scope=global` · target_table `bg_synthetic_cohort`

**What it produces.** 10,000 synthetic reference charts (sign/nakshatra grain) as a statistical base-rate population. Floor 10,000, measured 10,000 — met.

| relation | kind | total rows | rows on `482012f1` |
|---|---|--:|--:|
| `bg_synthetic_cohort` | table | 10000 | n/a — table is not chart-scoped |

**What would plausibly read it.** A rarity / base-rate serving surface — "how unusual is this configuration". No such capability is registered.

**What was searched, and what was not found.**

- table-name scan: 23 textual references, of which 8 read-context and 1 write-context statements; **0 serving consumers**, 1 writer consumers, 0 unattributed.
- non-serving buckets: `ops_script` ×1, `own_writer` ×1, `registry_declaration` ×1.
- asset-id name-mentions: 0 in surface files, 0 in capability modules, 5 in writers, 0 in scripts, 3 in other modules.
- code-module detector: 1 owning modules; importers — 0 surface, 0 writer (none), 0 script, 0 other.
- DB view indirection: no view or matview in the live database reads this asset's table(s).

**Evidence.**

- The one detected reader is `ka_kshetra`, and the registry itself declares `ka_kshetra` as the downstream dependent — code and catalogue agree.
- `platform/python-sidecar/services/ka_kshetra/cohort_client.py:171` — `FROM bg_synthetic_cohort`; also `:317`, `:322`, `:346` (denominator/numerator counts) and `writer.py:2146`.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| (chart-independent) | `lit` | — | 2026-08-02 13:49:30 |

**Registry-declared downstream dependents:** `ka_kshetra`  
**Registry `depends_on`:** _none_

**Reading of the absence.** **INPUT-ONLY** — consumed, but by writers rather than by a served surface. The absence of a serving consumer is what the asset is for, not a defect.

_No disposition proposed. G1 decision, on this evidence._

---

### bg_concordance

`bg_concordance` — layer `brahmagyan` · `CURRENT` · `asset_kind=data` · `is_active=True` · `scope=global` · target_table `classical_attributions`

**What it produces.** Cross-school chunk-pointer index per (topic, school) in `classical_attributions`. Floor 800, measured 720 — 90 % of floor.

| relation | kind | total rows | rows on `482012f1` |
|---|---|--:|--:|
| `classical_attributions` | table | 720 | n/a — table is not chart-scoped |

**What would plausibly read it.** A classical-attribution lookup capability. One exists by name — `classical_attribution_lookup` (`platform/src/lib/contract/tool_metadata.ts:923`) — but it does not query this table.

**What was searched, and what was not found.**

- table-name scan: 21 textual references, of which 5 read-context and 3 write-context statements; **0 serving consumers**, 0 writer consumers, 0 unattributed.
- non-serving buckets: `ops_script` ×2, `own_writer` ×5, `registry_declaration` ×1.
- asset-id name-mentions: 0 in surface files, 0 in capability modules, 1 in writers, 0 in scripts, 2 in other modules.
- code-module detector: 1 owning modules; importers — 0 surface, 0 writer (none), 0 script, 0 other.
- DB view indirection: no view or matview in the live database reads this asset's table(s).

**Evidence.**

- `platform/src/lib/router/retrieval_capability_spec.ts:406` states verbatim: "L8 — classical_attributions/classical_chunks/classical_texts retired WS-0; stub returns …". That is the code's own record of a retirement, not an inference.
- Zero read-context matches for `classical_attributions` anywhere under `platform/src`, `platform-mcp/src` or the sidecar routers/services. The only SQL statements are in its own writer and in `platform/scripts/m9/run_coverage_audit.py` (an audit script).
- No view or SQL function in the live DB references the table.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| (chart-independent) | `lit` | 720 | 2026-08-07 18:10:05 |

**Registry-declared downstream dependents:** _none_  
**Registry `depends_on`:** `bg_rules`

**Reading of the absence.** **NO CONSUMER FOUND** — no writer, no surface, no capability, no view. The absence looks real on this evidence. A prior serving path is documented as deliberately retired.

_No disposition proposed. G1 decision, on this evidence._

---

### bg_ephemeris_engine

`bg_ephemeris_engine` — layer `brahmagyan` · `CURRENT` · `asset_kind=data` · `is_active=True` · `scope=global` · target_table `(none)`

**What it produces.** Nothing of its own — the registry row describes the Swiss Ephemeris / pyswisseph engine plus the DE441 kernel. No `target_table`; census S2 finds no production writer.

**What would plausibly read it.** Everything that computes a position. The declared API `swisseph.calc_ut` — matched on its last token `calc_ut` — occurs in 24 non-test files, one of which is a surface (`platform/src/app/api/chat/spike/route.ts`). Token occurrence, not a proven call.

**What was searched, and what was not found.**

- table-name scan: 0 textual references, of which 0 read-context and 0 write-context statements; **0 serving consumers**, 0 writer consumers, 0 unattributed.
- asset-id name-mentions: 0 in surface files, 0 in capability modules, 0 in writers, 0 in scripts, 1 in other modules.
- DB view indirection: no view or matview in the live database reads this asset's table(s).

**Evidence.**

- Its single `asset_throughput` row is in state `error` (2026-06-18) and it is the only L0 asset in that state.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| (chart-independent) | `error` | — | 2026-06-18 18:47:04 |

**Registry-declared downstream dependents:** _none_  
**Registry `depends_on`:** _none_

**Reading of the absence.** **BY DESIGN EMPTY / CATEGORY MISMATCH** — the consumer question as posed does not apply to this row in its current form. This row registers a third-party engine dependency as an asset; "which surface reads its table" has no referent.

_No disposition proposed. G1 decision, on this evidence._

---

### bg_gochara_arcs

`bg_gochara_arcs` — layer `brahmagyan` · `CURRENT` · `asset_kind=data` · `is_active=True` · `scope=global` · target_table `bg_gochara_arcs`

**What it produces.** 34,553 chart-independent graha-longitude arc rows over the 1900–2150 ephemeris epoch. Floor 34,553, measured 34,553 — met.

| relation | kind | total rows | rows on `482012f1` |
|---|---|--:|--:|
| `bg_gochara_arcs` | table | 34553 | n/a — table is not chart-scoped |

**What would plausibly read it.** A gochara/transit surface. Those exist in quantity, but they read `kala_gochara_windows` (the materialized per-chart product), never the arc substrate.

**What was searched, and what was not found.**

- table-name scan: 33 textual references, of which 2 read-context and 0 write-context statements; **0 serving consumers**, 1 writer consumers, 0 unattributed.
- non-serving buckets: `registry_declaration` ×1.
- asset-id name-mentions: 0 in surface files, 0 in capability modules, 2 in writers, 1 in scripts, 4 in other modules.
- code-module detector: 1 owning modules; importers — 0 surface, 1 writer (`ka_gochara`), 0 script, 0 other.
- DB view indirection: no view or matview in the live database reads this asset's table(s).

**Evidence.**

- Declared downstream dependent `ka_gochara`; detected writer consumer `ka_gochara`. Catalogue and code agree.
- Zero read-context matches under `platform/src` or `platform-mcp/src`.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| (chart-independent) | `lit` | 34553 | 2026-08-09 23:55:23 |

**Registry-declared downstream dependents:** `ka_gochara`  
**Registry `depends_on`:** _none_

**Reading of the absence.** **INPUT-ONLY** — consumed, but by writers rather than by a served surface. The absence of a serving consumer is what the asset is for, not a defect.

_No disposition proposed. G1 decision, on this evidence._

---

### bg_kota_chakra_rings

`bg_kota_chakra_rings` — layer `brahmagyan` · `CURRENT` · `asset_kind=data` · `is_active=True` · `scope=global` · target_table `bg_kota_chakra_rings`

**What it produces.** 27 Kota-Chakra ring-partition rows (stambha/durgantara/prakara/bahya). Floor 27, measured 27 — met.

| relation | kind | total rows | rows on `482012f1` |
|---|---|--:|--:|
| `bg_kota_chakra_rings` | table | 27 | n/a — table is not chart-scoped |

**What would plausibly read it.** A Kota-Chakra reading surface. `ka_kota_chakra` produces `kala_kota_chakra`, and that is what a surface would read.

**What was searched, and what was not found.**

- table-name scan: 32 textual references, of which 5 read-context and 2 write-context statements; **0 serving consumers**, 1 writer consumers, 2 unattributed.
- non-serving buckets: `registry_declaration` ×2.
- asset-id name-mentions: 0 in surface files, 0 in capability modules, 2 in writers, 0 in scripts, 3 in other modules.
- code-module detector: 1 owning modules; importers — 0 surface, 0 writer (none), 0 script, 0 other.
- DB view indirection: no view or matview in the live database reads this asset's table(s).

**Evidence.**

- `platform/python-sidecar/services/ka_kota_chakra/writer.py:89` — `FROM bg_kota_chakra_rings`, with `:90` selecting `MAX(table_version)`.
- Two unattributed statements remain, both in `platform/python-sidecar/brahmagyan/l0_kota_chakra_rings.py` (an older standalone builder that INSERTs into the table) — a second writer path, not a consumer.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| (chart-independent) | `lit` | — | 2026-08-02 13:50:51 |

**Registry-declared downstream dependents:** `ka_kota_chakra`  
**Registry `depends_on`:** _none_

**Reading of the absence.** **INPUT-ONLY** — consumed, but by writers rather than by a served surface. The absence of a serving consumer is what the asset is for, not a defect.

_No disposition proposed. G1 decision, on this evidence._

---

### bg_kp_sublord_division

`bg_kp_sublord_division` — layer `brahmagyan` · `CURRENT` · `asset_kind=data` · `is_active=True` · `scope=global` · target_table `bg_kp_sublord_division`

**What it produces.** 249 KP sub-lord division rows. Floor 249, measured 249 — met.

| relation | kind | total rows | rows on `482012f1` |
|---|---|--:|--:|
| `bg_kp_sublord_division` | table | 249 | n/a — table is not chart-scoped |

**What would plausibly read it.** `ganita_kp_cusps_get`. It exists, and it reads `chart_facts` (`platform/src/lib/retrieval/registry/layers/L1_ganita/get_kp_cusps.ts:136`) — i.e. the derived per-chart facts, not this substrate.

**What was searched, and what was not found.**

- table-name scan: 32 textual references, of which 3 read-context and 1 write-context statements; **0 serving consumers**, 2 writer consumers, 0 unattributed.
- non-serving buckets: `registry_declaration` ×1.
- asset-id name-mentions: 1 in surface files, 0 in capability modules, 1 in writers, 0 in scripts, 3 in other modules.
- code-module detector: 1 owning modules; importers — 0 surface, 0 writer (none), 0 script, 0 other.
- DB view indirection: no view or matview in the live database reads this asset's table(s).

**Evidence.**

- `platform/python-sidecar/services/ka_kshetra/stage3_clocks.py:624` — `FROM bg_kp_sublord_division`; also consumed by `ga_nakshatra`.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| (chart-independent) | `lit` | 249 | 2026-08-05 11:37:13 |

**Registry-declared downstream dependents:** `ga_nakshatra`  
**Registry `depends_on`:** _none_

**Reading of the absence.** **INPUT-ONLY** — consumed, but by writers rather than by a served surface. The absence of a serving consumer is what the asset is for, not a defect.

_No disposition proposed. G1 decision, on this evidence._

---

### bg_panchanga

`bg_panchanga` — layer `brahmagyan` · `CURRENT` · `asset_kind=data` · `is_active=True` · `scope=global` · target_table `(none)`

**What it produces.** No table. The registry row declares the deterministic panchanga computation service, `provides_apis` naming `panchanga_instant(...)` and `panchanga_day(...)`.

**What would plausibly read it.** The panchanga serving path. It exists and is live: `POST /api/compute/panchanga` (`platform/python-sidecar/routers/panchang.py:165`), reached from `platform/src/app/api/panchang/route.ts:33`, `platform/src/app/panchang/page.tsx:41`, the ICS feeds, the daily-refresh cron, and the `call_panchanga_service` capability.

**What was searched, and what was not found.**

- table-name scan: 0 textual references, of which 0 read-context and 0 write-context statements; **0 serving consumers**, 0 writer consumers, 0 unattributed.
- asset-id name-mentions: 0 in surface files, 0 in capability modules, 0 in writers, 0 in scripts, 2 in other modules.
- DB view indirection: no view or matview in the live database reads this asset's table(s).

**Evidence.**

- `routers/panchang.py` imports `compute_panchang` / `panchang_range` from `panchang_engine`, not the `panchanga_instant` / `panchanga_day` names the registry declares. Those two names are found in the corpus, but at `platform/python-sidecar/pipeline/orchestrator/service_probes.py:116/125` (the service probe) and in `writers/ph_muhurta.py`.
- That naming gap is an observation about the registry row, not a claim that the service is dead.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| (chart-independent) | `lit` | 0 | 2026-06-18 18:47:04 |

**Registry-declared downstream dependents:** _none_  
**Registry `depends_on`:** _none_

**Reading of the absence.** **METHOD-BLIND** — a serving path plausibly exists that a table-name scan cannot see. Recorded as UNKNOWN, not as zero. The serving path is real; what this method cannot confirm is that the endpoint reaches *these* two named functions.

_No disposition proposed. G1 decision, on this evidence._

---

### bg_phaladeepika_latta

`bg_phaladeepika_latta` — layer `brahmagyan` · `CURRENT` · `asset_kind=data` · `is_active=True` · `scope=global` · target_table `bg_phaladeepika_latta`

**What it produces.** 8 Lattā (obstruction-point) rows transcribed from Phaladeepika Adh. XXVI. Floor 8, measured 8 — met.

| relation | kind | total rows | rows on `482012f1` |
|---|---|--:|--:|
| `bg_phaladeepika_latta` | table | 8 | n/a — table is not chart-scoped |

**What would plausibly read it.** A vedha/gochara surface. One exists — `query_vedha_gochara` — and it names this table in its provenance comment while querying `kala_vedha_gochara` instead.

**What was searched, and what was not found.**

- table-name scan: 20 textual references, of which 2 read-context and 1 write-context statements; **0 serving consumers**, 2 writer consumers, 0 unattributed.
- non-serving buckets: `registry_declaration` ×1.
- asset-id name-mentions: 0 in surface files, 1 in capability modules, 1 in writers, 0 in scripts, 2 in other modules.
- code-module detector: 1 owning modules; importers — 0 surface, 0 writer (none), 0 script, 0 other.
- DB view indirection: no view or matview in the live database reads this asset's table(s).

**Evidence.**

- `platform/python-sidecar/services/ka_vedha_gochara/writer.py:123` — `FROM bg_phaladeepika_latta`.
- Named (not read) at `platform/src/lib/retrieval/registry/layers/L3_kala/query_vedha_gochara.ts:154` — the serving capability records its lineage back to this table.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| (chart-independent) | `lit` | — | 2026-08-02 13:50:51 |

**Registry-declared downstream dependents:** `ka_vedha_gochara`  
**Registry `depends_on`:** _none_

**Reading of the absence.** **INPUT-ONLY** — consumed, but by writers rather than by a served surface. The absence of a serving consumer is what the asset is for, not a defect.

_No disposition proposed. G1 decision, on this evidence._

---

### bg_reference

`bg_reference` — layer `brahmagyan` · `CURRENT` · `asset_kind=data` · `is_active=True` · `scope=global` · target_table `reference_nakshatras`

**What it produces.** 15 typed reference tables. Floor 1,485; the registry `count_sql` returns 1,242 (84 %). Largest members: `reference_topic_tags` 481, `reference_glossary` 364, `reference_yogas` 229, `reference_constants` 203.

| relation | kind | total rows | rows on `482012f1` |
|---|---|--:|--:|
| `reference_nakshatras` | table | 27 | n/a — table is not chart-scoped |
| `reference_aspects` | table | 19 | n/a — table is not chart-scoped |
| `reference_constants` | table | 203 | n/a — table is not chart-scoped |
| `reference_dasha_systems` | table | 19 | n/a — table is not chart-scoped |
| `reference_doshas` | table | 79 | n/a — table is not chart-scoped |
| `reference_glossary` | table | 364 | n/a — table is not chart-scoped |
| `reference_houses` | table | 12 | n/a — table is not chart-scoped |
| `reference_karakas` | table | 77 | n/a — table is not chart-scoped |
| `reference_planets` | table | 11 | n/a — table is not chart-scoped |
| `reference_signs` | table | 12 | n/a — table is not chart-scoped |
| `reference_strength_systems` | table | 33 | n/a — table is not chart-scoped |
| `reference_topic_tags` | table | 481 | n/a — table is not chart-scoped |
| `reference_upagrahas` | table | 11 | n/a — table is not chart-scoped |
| `reference_vargas` | table | 19 | n/a — table is not chart-scoped |
| `reference_yogas` | table | 229 | n/a — table is not chart-scoped |

**What would plausibly read it.** The `ref_*` MCP tool family. Those tools exist and are live — but they read `reference_nakshatra` (SINGULAR, `bg_nakshatra`'s table, `platform-mcp/src/tools/register_p1_reference.ts:534`), `brahma_yoga_catalog`, `brahma_dosha_catalog`, `bg_dignity_reference` and friends. Not one of the 15 `reference_*` tables in this asset has a read-context match anywhere in the serving corpora.

**What was searched, and what was not found.**

- table-name scan: 210 textual references, of which 38 read-context and 15 write-context statements; **0 serving consumers**, 14 writer consumers, 12 unattributed.
- non-serving buckets: `ops_script` ×5, `registry_declaration` ×14.
- asset-id name-mentions: 0 in surface files, 0 in capability modules, 2 in writers, 3 in scripts, 3 in other modules.
- code-module detector: 2 owning modules; importers — 0 surface, 121 writer (`bg_class_lifetime_counts`, `bg_class_priors`, `bg_cohort`, `bg_compendium_index`, `bg_concordance`, `bg_dasha_systems`, `bg_dignity_reference`, `bg_doshas`, `bg_ephemeris`, `bg_formula_constants`, `bg_ghatana`, `bg_gochara_arcs`, `bg_kota_chakra_rings`, `bg_kp_sublord_division`, `bg_medical_mappings`, `bg_muhurta_lattice`, `bg_nakshatra`, `bg_nakshatra_medical`, `bg_ontology`, `bg_parihara_rules`, `bg_phaladeepika_latta`, `bg_prashna_rules`, `bg_remedies`, `bg_rules`, `bg_sign_medical`, `bg_sky_calendar`, `bg_text_index`, `bg_texts`, `bg_transit_engine`, `bg_transit_rules`, `bg_vastu_directions`, `bg_vedha_malefic_scale`, `bg_vidhi_floors`, `bg_vidhi_primitives`, `bg_yogas`, `bo_anveshana`, `bo_arudha`, `bo_bimba`, `bo_cdlm_summary`, `bo_cgm_motifs`, `bo_cgm_paths`, `bo_chart_gestalt`, `bo_drishti`, `bo_karanajala`, `bo_laksana`, `bo_laksana_rerank`, `bo_nakshatra_semantic`, `bo_pramana_mapa`, `bo_pratijna`, `bo_samskara`, `bo_samvada`, `bo_sangati`, `bo_special_lagna`, `bo_sudarshana`, `bo_upaya`, `bo_vargottama_dhana`, `bo_yantra_mechanism`, `ga_ayurdaya`, `ga_condition`, `ga_dashas`, `ga_medical`, `ga_nakshatra`, `ga_panchanga`, `ga_positions`, `ga_prashna`, `ga_sade_sati`, `ga_sensitive`, `ga_sensitive_degree`, `ga_strength`, `ga_structural`, `ga_tajaka`, `ga_transit_anchors`, `ga_vargas`, `ga_vastu`, `ga_vichara`, `ga_yoga`, `ka_avadhi`, `ka_bhavishya_lekha`, `ka_dasha_kala`, `ka_gochara`, `ka_gochara_resonance`, `ka_gochara_sweep`, `ka_gochara_v3_century_materialize`, `ka_graha_sancara`, `ka_jivana_parva`, `ka_kala_darshana`, `ka_kalasutra`, `ka_kota_chakra`, `ka_kshetra`, `ka_moorti_nirnaya`, `ka_muhurta_seva`, `ka_sangam`, `ka_sudarshana_varsha`, `ka_taranga`, `ka_tithi_pravesha`, `ka_tulana`, `ka_vedha_gochara`, `ka_vighnakara`, `ka_yojaka`, `mi_abhilekha`, `mi_adhilepa`, `mi_bhara`, `mi_bhavisya`, `mi_darshana`, `mi_gunanaka`, `mi_jivanaghatana`, `mi_kula`, `mi_pariksha`, `mi_pramana`, `mi_sambandha`, `mi_seva`, `mi_vistara`, `ph_muhurta`, `ph_nimitta`, `ph_phaladesa`, `ph_pramana`, `ph_pratikara`, `ph_rectification`, `ph_sankrama`, `ph_sodhana`, `ph_suddha_sodhana`), 11 script, 8 other.
- DB view indirection: no view or matview in the live database reads this asset's table(s).

**Evidence.**

- The near-collision `reference_nakshatra` (27 rows, `bg_nakshatra`, SERVED) vs `reference_nakshatras` (27 rows, `bg_reference`, not served) is a real hazard: the two names differ by one character and hold the same row count.
- Detected writer consumers: `ga_dashas`, `ga_sensitive`, `ga_nakshatra`, `ga_structural`, `ga_yoga`, `ga_ayurdaya`, `ga_sensitive_degree`, `bg_dasha_systems`, `bg_doshas`, `bg_yogas`, `bg_text_index`, `bg_concordance`, `bg_compendium_index`, `bo_pratijna`.
- The registry declares only `bg_compendium_index` and `ga_sensitive` as downstream dependents — the code shows 14. The dependency edge set is under-declared.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| (chart-independent) | `lit` | 1485 | 2026-08-07 17:43:37 |

**Registry-declared downstream dependents:** `bg_compendium_index`, `ga_sensitive`  
**Registry `depends_on`:** _none_

**Reading of the absence.** **INPUT-ONLY** — consumed, but by writers rather than by a served surface. The absence of a serving consumer is what the asset is for, not a defect. The reading is not "nothing uses it" — 14 L0/L1 writers do — but nothing *serves* it.

_No disposition proposed. G1 decision, on this evidence._

---

### bg_sarvatobhadra_grid

`bg_sarvatobhadra_grid` — layer `brahmagyan` · `CURRENT` · `asset_kind=data` · `is_active=True` · `scope=global` · target_table `bg_sarvatobhadra_grid`

**What it produces.** 0 rows, and the registry says so on purpose: "registered DELIBERATELY EMPTY … SBC grid geometry varies by Jyotish tradition". Floor 0, measured 0.

| relation | kind | total rows | rows on `482012f1` |
|---|---|--:|--:|
| `bg_sarvatobhadra_grid` | table | 0 | n/a — table is not chart-scoped |

**What would plausibly read it.** A Sarvatobhadra-chakra surface — which cannot exist meaningfully until the table is populated.

**What was searched, and what was not found.**

- table-name scan: 16 textual references, of which 2 read-context and 0 write-context statements; **0 serving consumers**, 1 writer consumers, 0 unattributed.
- non-serving buckets: `registry_declaration` ×1.
- asset-id name-mentions: 0 in surface files, 1 in capability modules, 1 in writers, 0 in scripts, 3 in other modules.
- DB view indirection: no view or matview in the live database reads this asset's table(s).

**Evidence.**

- `platform/python-sidecar/services/ka_vedha_gochara/writer.py:115` — `FROM bg_sarvatobhadra_grid`; the consumer exists and reads zero rows.
- Named at `.../L3_kala/query_vedha_gochara.ts:26` in a comment about the empty school_tag.
- This is the census §"zero rows (by design)" specimen; the `volume_explanation` required by charter G4 is present.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| (chart-independent) | `lit` | 0 | 2026-08-09 22:11:34 |

**Registry-declared downstream dependents:** `ka_vedha_gochara`  
**Registry `depends_on`:** _none_

**Reading of the absence.** **BY DESIGN EMPTY / CATEGORY MISMATCH** — the consumer question as posed does not apply to this row in its current form.

_No disposition proposed. G1 decision, on this evidence._

---

### bg_sky_calendar

`bg_sky_calendar` — layer `brahmagyan` · `CURRENT` · `asset_kind=data` · `is_active=True` · `scope=global` · target_table `bg_sky_events`

**What it produces.** A chart-independent sky-event diary. Floor 31,064; the registry `count_sql` returns 31,059 — but the rows are in `bg_sky_calendar`, NOT in the `target_table` the registry names.

| relation | kind | total rows | rows on `482012f1` |
|---|---|--:|--:|
| `bg_sky_events` | **absent from the live DB** | — | — |
| `bg_sky_calendar` | table | 31059 | n/a — table is not chart-scoped |

**What would plausibly read it.** An eclipse / ingress / station surface, and `ka_gochara_v3_century_materialize` (the declared downstream dependent), whose W26 eclipse mechanism cites this table by name.

**What was searched, and what was not found.**

- table-name scan: 34 textual references, of which 3 read-context and 1 write-context statements; **0 serving consumers**, 0 writer consumers, 2 unattributed.
- non-serving buckets: `own_writer` ×1, `registry_declaration` ×1.
- asset-id name-mentions: 0 in surface files, 0 in capability modules, 3 in writers, 0 in scripts, 1 in other modules.
- code-module detector: 1 owning modules; importers — 0 surface, 0 writer (none), 0 script, 0 other.
- DB view indirection: no view or matview in the live database reads this asset's table(s).

**Evidence.**

- **`target_table = bg_sky_events` does not exist in the live database.** It is the only asset of 128 whose `target_table` is neither a table nor a view (`information_schema` + `pg_class` both empty for that name). The real relation is `bg_sky_calendar` (31,059 rows), which is what `count_sql` actually counts.
- The two references found are prose in `platform/python-sidecar/services/gochara_v3/mechanisms/w26_real_eclipses.py:6` and `:27` ("actual eclipse events sourced from bg_sky_calendar") — the mechanism describes reading it; the SQL that would do so was not located by this scan.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| (chart-independent) | `lit` | — | 2026-08-02 13:50:01 |

**Registry-declared downstream dependents:** `ka_gochara_v3_century_materialize`  
**Registry `depends_on`:** _none_

**Reading of the absence.** **METHOD-BLIND** — a serving path plausibly exists that a table-name scan cannot see. Recorded as UNKNOWN, not as zero. Two statements could not be attributed and the registry's own table pointer is broken, so a real reader may exist behind a name this scan did not follow.

_No disposition proposed. G1 decision, on this evidence._

---

### bg_vedha_malefic_scale

`bg_vedha_malefic_scale` — layer `brahmagyan` · `CURRENT` · `asset_kind=data` · `is_active=True` · `scope=global` · target_table `bg_vedha_malefic_scale`

**What it produces.** 5 malefic-count → effect-grade rows from Phaladeepika Adh. XXVI PG353. Floor 5, measured 5 — met.

| relation | kind | total rows | rows on `482012f1` |
|---|---|--:|--:|
| `bg_vedha_malefic_scale` | table | 5 | n/a — table is not chart-scoped |

**What would plausibly read it.** The vedha suppression grading in the gochara engine — which is exactly what reads it.

**What was searched, and what was not found.**

- table-name scan: 27 textual references, of which 5 read-context and 1 write-context statements; **0 serving consumers**, 3 writer consumers, 0 unattributed.
- non-serving buckets: `registry_declaration` ×1.
- asset-id name-mentions: 0 in surface files, 1 in capability modules, 1 in writers, 0 in scripts, 4 in other modules.
- code-module detector: 1 owning modules; importers — 0 surface, 0 writer (none), 0 script, 0 other.
- DB view indirection: no view or matview in the live database reads this asset's table(s).

**Evidence.**

- `platform/python-sidecar/services/gochara_v3/context.py:485` — `FROM bg_vedha_malefic_scale`, prefetched for "W1.3 suppression grading" (`context.py:101`); also `services/ka_vedha_gochara/writer.py:128`.
- Named at `.../L3_kala/query_vedha_gochara.ts:154`.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| (chart-independent) | `lit` | — | 2026-08-02 13:50:51 |

**Registry-declared downstream dependents:** `ka_vedha_gochara`  
**Registry `depends_on`:** _none_

**Reading of the absence.** **INPUT-ONLY** — consumed, but by writers rather than by a served surface. The absence of a serving consumer is what the asset is for, not a defect.

_No disposition proposed. G1 decision, on this evidence._

---

### bg_vidhi_floors

`bg_vidhi_floors` — layer `brahmagyan` · `DRAFT` · `asset_kind=data` · `is_active=True` · `scope=global` · target_table `vidhi_floor_items`

**What it produces.** Per-intent-class floor rows in `vidhi_floor_items` — 286 rows live. Floor 11; last build wrote 77. Floor, live count and last write disagree three ways.

| relation | kind | total rows | rows on `482012f1` |
|---|---|--:|--:|
| `vidhi_floor_items` | table | 286 | n/a — table is not chart-scoped |

**What would plausibly read it.** The vidhi/floor compiler and the MCP vidhi resource face.

**What was searched, and what was not found.**

- table-name scan: 11 textual references, of which 2 read-context and 1 write-context statements; **0 serving consumers**, 0 writer consumers, 0 unattributed.
- non-serving buckets: `own_writer` ×2, `registry_declaration` ×1.
- asset-id name-mentions: 0 in surface files, 0 in capability modules, 0 in writers, 2 in scripts, 1 in other modules.
- code-module detector: 1 owning modules; importers — 0 surface, 0 writer (none), 0 script, 0 other.
- DB view indirection: no view or matview in the live database reads this asset's table(s).

**Evidence.**

- Both `platform/src/lib/vidhi/registry_data.ts` and `platform-mcp/src/resources/vidhi/registry_data.ts` hold the floors as TypeScript literals. The platform copy's own header says the DB is the runtime source ("at runtime (post V-2 wiring) the MCP resource face reads these rows from the DB (`vidhi_primitives` / `vidhi_intent_floors` / `vidhi_floor_items`, migration 440)"), but a read-context search for those three table names across `platform/src` and `platform-mcp/src` returns **no match**.
- This is an observation about what the scan can see, not a verdict on the V-2 wiring — a runtime read built by string concatenation would be invisible here. It is flagged precisely because the doc-comment and the greppable code disagree.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| (chart-independent) | `lit` | 77 | 2026-08-02 13:50:03 |

**Registry-declared downstream dependents:** _none_  
**Registry `depends_on`:** `bg_vidhi_primitives`

**Reading of the absence.** **SHADOWED** — a served surface carrying this asset's name exists, but the code behind it does not read this asset. The name and the data path have come apart.

_No disposition proposed. G1 decision, on this evidence._

---

### bg_vidhi_primitives

`bg_vidhi_primitives` — layer `brahmagyan` · `DRAFT` · `asset_kind=data` · `is_active=True` · `scope=global` · target_table `vidhi_primitives`

**What it produces.** Versioned vidhi primitive atoms in `vidhi_primitives` — 52 rows live. Floor 48; last build wrote 37.

| relation | kind | total rows | rows on `482012f1` |
|---|---|--:|--:|
| `vidhi_primitives` | table | 52 | n/a — table is not chart-scoped |

**What would plausibly read it.** Same as `bg_vidhi_floors`.

**What was searched, and what was not found.**

- table-name scan: 10 textual references, of which 1 read-context and 1 write-context statements; **0 serving consumers**, 0 writer consumers, 0 unattributed.
- non-serving buckets: `own_writer` ×1, `registry_declaration` ×1.
- asset-id name-mentions: 0 in surface files, 0 in capability modules, 1 in writers, 2 in scripts, 1 in other modules.
- code-module detector: 1 owning modules; importers — 0 surface, 0 writer (none), 0 script, 0 other.
- DB view indirection: no view or matview in the live database reads this asset's table(s).

**Evidence.**

- Same TS-literal shadow: `registry_data.ts` in both packages carries the 52 primitives inline (its header: "52 versioned primitives"), with `live_tool` / `fallback_face` fields pointing at MCP tool names.
- The only SQL statements against `vidhi_primitives` are its own writer and two governance scripts.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| (chart-independent) | `lit` | 37 | 2026-08-02 13:50:02 |

**Registry-declared downstream dependents:** `bg_vidhi_floors`  
**Registry `depends_on`:** _none_

**Reading of the absence.** **SHADOWED** — a served surface carrying this asset's name exists, but the code behind it does not read this asset. The name and the data path have come apart.

_No disposition proposed. G1 decision, on this evidence._

---

### bo_cdlm_summary

`bo_cdlm_summary` — layer `bodha` · `DRAFT` · `asset_kind=data` · `is_active=True` · `scope=per_chart` · target_table `(none)`

**What it produces.** Per-chart cross-domain linkage summary. `bodha_cdlm_chart_summary` holds 15 rows total, 5 on the native chart. Registry floor 1. A matview `mv_cdlm_static_summary` exists and holds 0 rows.

| relation | kind | total rows | rows on `482012f1` |
|---|---|--:|--:|
| `bodha_cdlm_chart_summary` | table | 15 | 5 |
| `mv_cdlm_static_summary` | materialized view | 0 | 0 |

**What would plausibly read it.** `query_cdlm_summary` — the capability exists (`.../L2_bodha/query_cdlm_summary.ts`) and its default tier is named `chart_summary`, but no read-context match for `bodha_cdlm_chart_summary` was found in it or anywhere else in the serving corpora.

**What was searched, and what was not found.**

- table-name scan: 14 textual references, of which 4 read-context and 2 write-context statements; **0 serving consumers**, 13 writer consumers, 0 unattributed.
- non-serving buckets: `own_writer` ×3, `registry_declaration` ×1.
- asset-id name-mentions: 0 in surface files, 0 in capability modules, 0 in writers, 2 in scripts, 1 in other modules.
- code-module detector: 1 owning modules; importers — 0 surface, 0 writer (none), 0 script, 0 other.
- DB view indirection: `mv_cdlm_static_summary` (on `bodha_cdlm_chart_summary`).

**Evidence.**

- **The 13 "writer consumers" reported for this asset are an artefact and should not be read as 13 readers.** Every one traces to the same line: `platform/python-sidecar/bodha_writers/_idempotency.py:190`, `DELETE FROM bodha_cdlm_chart_summary WHERE chart_id = %s AND ayanamsha_id = %s` — the shared §N.3 idempotency helper that all 13 bodha writers import. It is a delete, not a read.
- The matview `mv_cdlm_static_summary` is built on this table and is empty.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| 1c826d5a… | `lit` | 40 | 2026-08-12 16:27:32 |
| 482012f1… | `lit` | 70 | 2026-08-12 15:24:28 |
| cb73cd3d… | `stale` | 40 | 2026-07-27 11:37:38 |

**Registry-declared downstream dependents:** _none_  
**Registry `depends_on`:** `bo_sangati`

**Reading of the absence.** **METHOD-BLIND** — a serving path plausibly exists that a table-name scan cannot see. Recorded as UNKNOWN, not as zero.

_No disposition proposed. G1 decision, on this evidence._

---

### bo_samskara

`bo_samskara` — layer `bodha` · `CURRENT` · `asset_kind=data` · `is_active=True` · `scope=per_chart` · target_table `bodha_signal_embeddings`

**What it produces.** 768-dim signal embeddings. `bodha_signal_embeddings` holds 150,081 rows total, 50,104 on the native chart against a floor of 60,000 (84 %).

| relation | kind | total rows | rows on `482012f1` |
|---|---|--:|--:|
| `bodha_signal_embeddings` | table | 150081 | 50104 |

**What would plausibly read it.** A semantic/vector search surface over MSR signals.

**What was searched, and what was not found.**

- table-name scan: 38 textual references, of which 9 read-context and 4 write-context statements; **0 serving consumers**, 14 writer consumers, 3 unattributed.
- non-serving buckets: `own_writer` ×2, `registry_declaration` ×1.
- asset-id name-mentions: 0 in surface files, 1 in capability modules, 1 in writers, 3 in scripts, 2 in other modules.
- code-module detector: 1 owning modules; importers — 0 surface, 0 writer (none), 0 script, 0 other.
- DB view indirection: no view or matview in the live database reads this asset's table(s).

**Evidence.**

- `platform/src/lib/retrieval/registry/layers/L2_bodha/traverse_chart_graph.ts:472` says in terms: "Full semantic-search path goes via bo_samskara/python-sidecar." That is the serving layer stating that the read happens on the far side of the sidecar HTTP boundary this method cannot cross.
- Registry declares `bo_anveshana`, `bo_pramana_mapa`, `ph_nimitta` downstream; `ph_nimitta/engine.py:374` names "bodha_signal_embeddings precedent search" in a comment.
- As with `bo_cdlm_summary`, most of the 14 writer-consumer edges trace to the shared bodha idempotency helper — treat the count as an upper bound.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| 482012f1… | `lit` | 50104 | 2026-08-12 23:43:59 |
| cb73cd3d… | `lit` | 49875 | 2026-08-07 15:11:33 |
| 1c826d5a… | `lit` | 50171 | 2026-08-07 14:52:33 |

**Registry-declared downstream dependents:** `bo_anveshana`, `bo_pramana_mapa`, `ph_nimitta`  
**Registry `depends_on`:** `bo_laksana`

**Reading of the absence.** **METHOD-BLIND** — a serving path plausibly exists that a table-name scan cannot see. Recorded as UNKNOWN, not as zero.

_No disposition proposed. G1 decision, on this evidence._

---

### ka_dasha_kala

`ka_dasha_kala` — layer `kala` · `DRAFT` · `asset_kind=service` · `is_active=True` · `scope=per_chart` · target_table `(none)`

**What it produces.** No table; `asset_kind = service`; every `asset_throughput` row records `rows_written = 0` across all three charts. Registry floor 0.

**What would plausibly read it.** `call_dasha_eligibility` — the capability exists and names this service in its header (`.../L3_kala/call_service_wrappers.ts:8`).

**What was searched, and what was not found.**

- table-name scan: 0 textual references, of which 0 read-context and 0 write-context statements; **0 serving consumers**, 0 writer consumers, 0 unattributed.
- asset-id name-mentions: 0 in surface files, 1 in capability modules, 4 in writers, 1 in scripts, 6 in other modules.
- code-module detector: 6 owning modules; importers — 0 surface, 1 writer (`ka_sangam`), 0 script, 1 other.
- DB view indirection: no view or matview in the live database reads this asset's table(s).

**Evidence.**

- That capability's handler does **not** call the service: it runs its own SQL, `FROM chart_dashas`, inside the TypeScript module. The python package `services/ka_dasha_kala/` (6 modules) is imported only by the `ka_sangam` writer and by `services/ph_nimitta/dasha_consensus.py`.
- Registry declares `ka_jivana_parva`, `ka_kshetra`, `ka_sangam` downstream; only `ka_sangam` is detected in code.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| 482012f1… | `lit` | 0 | 2026-08-08 00:28:57 |
| 1c826d5a… | `lit` | 0 | 2026-08-06 04:12:49 |
| cb73cd3d… | `lit` | 0 | 2026-07-27 13:58:16 |

**Registry-declared downstream dependents:** `ka_jivana_parva`, `ka_kshetra`, `ka_sangam`  
**Registry `depends_on`:** `ga_dashas`

**Reading of the absence.** **SHADOWED** — a served surface carrying this asset's name exists, but the code behind it does not read this asset. The name and the data path have come apart.

_No disposition proposed. G1 decision, on this evidence._

---

### ka_gochara_v3_century_materialize

`ka_gochara_v3_century_materialize` — layer `kala` · `CURRENT` · `asset_kind=data` · `is_active=True` · `scope=per_chart` · target_table `kala_gochara_windows_v2`

**What it produces.** `kala_gochara_windows_v2` — 1,938 rows total, 997 on the native chart. The registry `count_sql` (filtered to `generation LIKE 'g3_%'`) returns 914. Registry floor 0. Its native throughput row is in state `error` (2026-08-21).

| relation | kind | total rows | rows on `482012f1` |
|---|---|--:|--:|
| `kala_gochara_windows_v2` | table | 1938 | 997 |

**What would plausibly read it.** A gochara-window surface. Those read `kala_gochara_windows` (the v1/production relation), never the `_v2` staging surface.

**What was searched, and what was not found.**

- table-name scan: 60 textual references, of which 6 read-context and 5 write-context statements; **0 serving consumers**, 2 writer consumers, 0 unattributed.
- non-serving buckets: `ops_script` ×8, `registry_declaration` ×2.
- asset-id name-mentions: 1 in surface files, 0 in capability modules, 0 in writers, 5 in scripts, 3 in other modules.
- code-module detector: 1 owning modules; importers — 0 surface, 0 writer (none), 0 script, 0 other.
- DB view indirection: no view or matview in the live database reads this asset's table(s).

**Evidence.**

- Named at `platform-mcp/src/tools/retrieval/register_gochara_windows.ts:588`, in a description of `kala_gochara_windows` — i.e. the serving tool names this writer while reading the other table.
- This is one of the 7 assets the plan itself annotates "No detected serving consumer (Phase 0.8c)".
- Charter P1 note: this asset sits next to the unrecoverable v1 gochara corpus. Nothing here touches it; this packet is read-only evidence.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| 482012f1… | `error` | 914 | 2026-08-21 13:37:44 |
| 1c826d5a… | `stale` | 0 | 2026-08-11 21:48:23 |

**Registry-declared downstream dependents:** _none_  
**Registry `depends_on`:** `ka_gochara_resonance`, `ka_vedha_gochara`, `ka_moorti_nirnaya`, `ka_kota_chakra`, `ka_tithi_pravesha`, `bg_sky_calendar`

**Reading of the absence.** **INPUT-ONLY** — consumed, but by writers rather than by a served surface. The absence of a serving consumer is what the asset is for, not a defect. The writer's own docstring calls `kala_gochara_windows_v2` a "calibration/staging surface", which is consistent with nothing serving it.

_No disposition proposed. G1 decision, on this evidence._

---

### ka_graha_sancara

`ka_graha_sancara` — layer `kala` · `DRAFT` · `asset_kind=service` · `is_active=True` · `scope=global` · target_table `(none)`

**What it produces.** No table; `asset_kind = service`; `rows_written = 0`. Provides positions for 9 grahas at an arbitrary instant.

**What would plausibly read it.** `POST /api/compute/ephemeris_at_t` — which exists (`platform/python-sidecar/routers/ephemeris.py:147`) and is called by the `call_ephemeris_at_t` capability (`call_service_wrappers.ts:219`).

**What was searched, and what was not found.**

- table-name scan: 0 textual references, of which 0 read-context and 0 write-context statements; **0 serving consumers**, 0 writer consumers, 0 unattributed.
- asset-id name-mentions: 2 in surface files, 2 in capability modules, 4 in writers, 1 in scripts, 12 in other modules.
- code-module detector: 3 owning modules; importers — 0 surface, 4 writer (`ka_kota_chakra`, `ka_moorti_nirnaya`, `ka_sudarshana_varsha`, `ka_vedha_gochara`), 0 script, 2 other.
- DB view indirection: no view or matview in the live database reads this asset's table(s).

**Evidence.**

- `platform/python-sidecar/main.py:89-91` documents the wiring explicitly: "W2 dark-set wiring — ka_graha_sancara (GT-50) … Retrieval call_ephemeris_at_t capability calls /api/compute/ephemeris_at_t".
- Four writers import the package: `ka_sudarshana_varsha`, `ka_vedha_gochara`, `ka_kota_chakra`, `ka_moorti_nirnaya`.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| (chart-independent) | `lit` | 0 | 2026-08-02 13:50:52 |

**Registry-declared downstream dependents:** `ka_muhurta_seva`  
**Registry `depends_on`:** `bg_ephemeris`

**Reading of the absence.** **METHOD-BLIND** — a serving path plausibly exists that a table-name scan cannot see. Recorded as UNKNOWN, not as zero. A live serving path exists across the sidecar HTTP boundary; whether it reaches this asset's own package was not established.

_No disposition proposed. G1 decision, on this evidence._

---

### ka_kshetra

`ka_kshetra` — layer `kala` · `CURRENT` · `asset_kind=data` · `is_active=True` · `scope=per_chart` · target_table `kala_field`

**What it produces.** `kala_field` — **11,012,657 rows total, 8,599,775 on the native chart**. Registry floor 0. Native throughput row is `stale` (last build wrote 11,069,325 rows, 2026-08-15).

| relation | kind | total rows | rows on `482012f1` |
|---|---|--:|--:|
| `kala_field` | table | 11012657 | 8599775 |

**What would plausibly read it.** A temporal-field / hazard-rate surface. The MCP Kāla views know about it and report it as unavailable.

**What was searched, and what was not found.**

- table-name scan: 45 textual references, of which 8 read-context and 1 write-context statements; **0 serving consumers**, 1 writer consumers, 0 unattributed.
- non-serving buckets: `ops_script` ×4, `own_writer` ×1, `registry_declaration` ×1.
- asset-id name-mentions: 3 in surface files, 2 in capability modules, 4 in writers, 18 in scripts, 11 in other modules.
- code-module detector: 41 owning modules; importers — 0 surface, 0 writer (none), 0 script, 0 other.
- DB view indirection: no view or matview in the live database reads this asset's table(s).

**Evidence.**

- `platform-mcp/src/lib/kala_ritual_resonance.ts:19` carries the serving layer's own status line: "temporal_intensity | the field's λ — kala_field_windows | not_computed (field empty — ka_kshetra has written no rows; the N_e critical path)". `platform-mcp/src/tools/kala_views/ritual.ts:781` repeats it.
- **That serving-layer claim and the database disagree.** The relation the MCP layer names is `kala_field_windows`; the relation `ka_kshetra` writes is `kala_field`, which holds 8.6 M rows on the native chart. Whether `kala_field_windows` exists as a separate empty relation, or the name is simply wrong, is not settled by this packet — but "ka_kshetra has written no rows" is not true of `kala_field`.
- The only detected reader is the `mi_bhara` writer (`platform/python-sidecar/services/mi_bhara/db.py:87`, `:99`). Registry declares `mi_bhara` and `mi_sankalpa` downstream.
- This is the largest asset in the zero-serving set by three orders of magnitude, and therefore the most expensive one to get wrong in either direction.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| 482012f1… | `stale` | 11069325 | 2026-08-15 06:28:11 |
| 1c826d5a… | `lit` | 837992 | 2026-08-12 22:26:27 |
| cb73cd3d… | `error` | — | 2026-08-07 15:11:37 |

**Registry-declared downstream dependents:** `mi_bhara`, `mi_sankalpa`  
**Registry `depends_on`:** `ka_dasha_kala`, `ka_gochara_resonance`, `ga_panchanga`, `bo_pratijna`, `bo_sangati`, `bo_upaya`, `bg_cohort`, `bg_class_lifetime_counts`

**Reading of the absence.** **METHOD-BLIND** — a serving path plausibly exists that a table-name scan cannot see. Recorded as UNKNOWN, not as zero.

_No disposition proposed. G1 decision, on this evidence._

---

### ka_muhurta_seva

`ka_muhurta_seva` — layer `kala` · `DRAFT` · `asset_kind=service` · `is_active=True` · `scope=global` · target_table `(none)`

**What it produces.** No table; `asset_kind = service`; `rows_written = 0`.

**What would plausibly read it.** `POST /api/compute/muhurta_score` — which exists (`platform/python-sidecar/routers/muhurta_score.py:72`) and is called by `call_muhurta_score` (`call_service_wrappers.ts:463`).

**What was searched, and what was not found.**

- table-name scan: 0 textual references, of which 0 read-context and 0 write-context statements; **0 serving consumers**, 0 writer consumers, 0 unattributed.
- asset-id name-mentions: 3 in surface files, 2 in capability modules, 3 in writers, 1 in scripts, 9 in other modules.
- code-module detector: 4 owning modules; importers — 0 surface, 2 writer (`ka_sangam`, `ka_vighnakara`), 0 script, 0 other.
- DB view indirection: no view or matview in the live database reads this asset's table(s).

**Evidence.**

- `routers/muhurta_score.py` imports `panchang_engine.muhurat` (`score_muhurat`, `EVENTS_MVP`), not `services/ka_muhurta_seva/`. Its own docstring says it "Reuses `panchang_engine.muhurat.score_muhurat()` … the SAME scoring primitive `ph_muhurta` calls internally, not a second scoring engine."
- The package `services/ka_muhurta_seva/` is imported only by the `ka_sangam` and `ka_vighnakara` writers.
- The same docstring records that the `call_muhurta_score` descriptor's event enum "never had a live caller (the handler unconditionally errored before this wave)" — the code's own account of a previously dead surface.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| (chart-independent) | `lit` | 0 | 2026-08-02 13:50:52 |

**Registry-declared downstream dependents:** `ka_sangam`, `ka_vighnakara`  
**Registry `depends_on`:** `ka_graha_sancara`

**Reading of the absence.** **SHADOWED** — a served surface carrying this asset's name exists, but the code behind it does not read this asset. The name and the data path have come apart. A live endpoint named for this asset exists; the asset's own package is not on its path.

_No disposition proposed. G1 decision, on this evidence._

---

### ka_tulana

`ka_tulana` — layer `kala` · `DRAFT` · `asset_kind=service` · `is_active=True` · `scope=per_chart` · target_table `(none)`

**What it produces.** No table; `asset_kind = service`; `rows_written = 0` on all three charts. Registry describes it as a "Serve-time QT-4 ranking engine".

**What would plausibly read it.** `kala_priority_ranking_get` / `pact_query` → `marsys://tool/L3/call_priority_ranking`. All three exist and are live MCP surfaces.

**What was searched, and what was not found.**

- table-name scan: 0 textual references, of which 0 read-context and 0 write-context statements; **0 serving consumers**, 0 writer consumers, 0 unattributed.
- asset-id name-mentions: 1 in surface files, 1 in capability modules, 0 in writers, 6 in scripts, 3 in other modules.
- code-module detector: 4 owning modules; importers — 0 surface, 0 writer (none), 0 script, 0 other.
- DB view indirection: no view or matview in the live database reads this asset's table(s).

**Evidence.**

- `callPriorityRankingCapability` (`.../L3_kala/call_service_wrappers.ts:482`) describes itself as "(ka_tulana service)" and then does the ranking itself in SQL: `FROM bodha_msr_signals m` at `call_service_wrappers.ts:654`, with no `fetch()` anywhere after line 480 of that file — unlike its three sibling `call_*` wrappers, which do call `/api/compute/...` (`:138`, `:219`, `:463`).
- **No production module imports the `services/ka_tulana/` package** (4 modules: `__init__.py`, `ranker.py`, `writer.py`, plus the orchestrator writer). Zero non-test importers — not a surface, not another writer, not a script. The only importer found anywhere is its own unit test, `platform/python-sidecar/tests/l3/test_ka_tulana.py:8` (`from services.ka_tulana.ranker import ...`).
- A serve-time engine that nothing imports and that writes no rows is the one case in this set where both detectors return empty.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| 482012f1… | `lit` | 0 | 2026-08-13 01:15:55 |
| 1c826d5a… | `lit` | 0 | 2026-08-12 17:09:23 |
| cb73cd3d… | `stale` | 0 | 2026-07-27 14:21:47 |

**Registry-declared downstream dependents:** _none_  
**Registry `depends_on`:** `ka_sangam`, `ka_vighnakara`, `ka_kala_darshana`

**Reading of the absence.** **SHADOWED** — a served surface carrying this asset's name exists, but the code behind it does not read this asset. The name and the data path have come apart. This is the clearest specimen in the set.

_No disposition proposed. G1 decision, on this evidence._

---

### mi_jivanaghatana

`mi_jivanaghatana` — layer `mimamsa` · `DRAFT` · `asset_kind=data` · `is_active=True` · `scope=per_chart` · target_table `mimamsa_event_provenance`

**What it produces.** `mimamsa_event_provenance` — 64 rows, all on the native chart. Two views read it: `vw_mimamsa_admissible_clean` (51 rows) and `vw_mimamsa_held_out` (13 rows). Registry floor 0.

| relation | kind | total rows | rows on `482012f1` |
|---|---|--:|--:|
| `mimamsa_event_provenance` | table | 64 | 64 |
| `vw_mimamsa_admissible_clean` | view | 51 | 51 |
| `vw_mimamsa_held_out` | view | 13 | 13 |

**What would plausibly read it.** A calibration / held-out-evaluation surface, or the client learning tab.

**What was searched, and what was not found.**

- table-name scan: 11 textual references, of which 5 read-context and 1 write-context statements; **0 serving consumers**, 2 writer consumers, 0 unattributed.
- non-serving buckets: `own_writer` ×2, `registry_declaration` ×1.
- asset-id name-mentions: 1 in surface files, 0 in capability modules, 0 in writers, 0 in scripts, 2 in other modules.
- code-module detector: 1 owning modules; importers — 0 surface, 0 writer (none), 0 script, 0 other.
- DB view indirection: `vw_mimamsa_admissible_clean` (on `mimamsa_event_provenance`), `vw_mimamsa_held_out` (on `mimamsa_event_provenance`).

**Evidence.**

- `platform/src/app/api/clients/[id]/learning/route.ts:146` names the asset — but to TRIGGER it, not to read it: `void triggerProvenanceResync(chartId)` → `fetch(${sidecarUrl}/mimamsa/provenance-resync)` (`:160`). That is a write-side trigger across the sidecar boundary.
- Neither the base table nor either view has a read-context match in `platform/src`, `platform-mcp/src` or the sidecar routers.
- Detected writer consumers `mi_pramana` and `mi_pariksha` match the registry's declared downstream (`mi_bhavisya`, `mi_darshana`, `mi_pramana`) only partially.

| throughput chart | state | rows_written | last_built_at |
|---|---|--:|---|
| 482012f1… | `lit` | 64 | 2026-08-08 00:18:13 |
| 1c826d5a… | `lit` | 0 | 2026-07-26 21:18:01 |

**Registry-declared downstream dependents:** `mi_bhavisya`, `mi_darshana`, `mi_pramana`  
**Registry `depends_on`:** `bg_ghatana`

**Reading of the absence.** **METHOD-BLIND** — a serving path plausibly exists that a table-name scan cannot see. Recorded as UNKNOWN, not as zero.

_No disposition proposed. G1 decision, on this evidence._

---

## 4 — What these packets do NOT establish

- They do not establish that any asset is unused. They establish what a documented static method found and did not find.
- They do not settle any of the five SHADOWED / METHOD-BLIND cases. Each names the specific further check that would settle it (usually: exercise the endpoint, or read the sidecar side of an HTTP call).
- They propose no promotion, retirement or reclassification, and they set no floor.
- They certify nothing. Verification belongs to PARĪKṢAKA (I16); disposition to ADHIKĀRIN (G1).

