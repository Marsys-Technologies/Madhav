# NIRMĀṆA M0-T7 — DAG edge audit v1.0

**Generated:** 2026-08-23T04:41:20.013140+00:00  
**Generators:** `00_ARCHITECTURE/control/dag_audit.py` (facts) · `render_m0t7.py` (this page)  
**Git:** `campaign/nirmana-autonomous` @ `b833c1adb6ca68d7e975795c63c2e45ced8bccfd`  
**Database access:** READ-ONLY (SELECT only, autocommit)  
**Status:** observations only. No edge was changed. No verdict is issued (I16 / charter H7).

## 0 — The graph, measured

| quantity | value | source |
|---|--:|---|
| `asset_registry` rows | 128 | live DB |
| `depends_on` edges (registry) | 284 | live DB |
| assets declaring ≥1 dependency | 94 | live DB |
| assets declaring none | 34 | live DB |
| asset entries in the seed .ts | 127 | `platform/scripts/seed/asset_registry_seed.ts` |
| `depends_on` edges (seed .ts) | 226 | same |
| coefficient edges (seed .ts) | 5 | same (`upstream_asset_id`/`downstream_asset_id`) |
| writer assets resolved from `@register` | 123 | sidecar sources |

## 1 — CURRENT assets depending on DRAFT assets

**3** instances. This is the contract violation the M0 exit criterion requires to be zero.

| CURRENT asset | layer | depends on | dependency status | dependency layer |
|---|---|---|---|---|
| `bo_laksana` | bodha | `ga_vichara` | DRAFT (is_active=True) | ganita |
| `ka_kshetra` | kala | `ka_dasha_kala` | DRAFT (is_active=True) | kala |
| `ka_taranga` | kala | `ka_sangam` | DRAFT (is_active=True) | kala |

Adjacent checks, kept separate because they are different defects:

- CURRENT → RETIRED edges: **0** _(none)_
- CURRENT → `is_active = false` edges: **0** _(none)_
- cycles in the registry DAG: **0** _(none)_
- self-edges: **0** · duplicate edges: **0**

## 2 — Dangling edges

A dangling edge is a `depends_on` entry naming an `asset_id` that has no registry row. The
M0-T1 census found a 138-id union against a 128-row registry, so the question is whether any
of those 10 extra ids is referenced as a dependency. Both declaration surfaces were checked.

- Dangling in the **live registry** (`depends_on` target absent from `asset_registry`): **0** — **zero**.
- Dangling in the **seed .ts** (target absent from the live registry): **0** — **zero**.
- Dangling **within the seed itself** (target absent from the seed's own asset list): **0** — **zero**.
- Seed coefficient edges with a dangling endpoint: **0** — **zero**.

**The 10 non-registry ids the census found do not appear as a dependency target anywhere.**
They are decorator-only test fixtures (`bad_infra_writer`, `fixture.*`, `test_infra_*`) and
migration-only tombstones (`ga_pyjhora_engine`, `ga_vastu_planet_direction_map`,
`ka_gochara_v2_materialize`, `ka_transit_almanac`) — none of them is on the left or right of
any edge. The 138-vs-128 gap is real, and it is not hiding in the DAG.

### Registry-vs-seed edge divergence (reported, not adjudicated)

- Edges present in the registry but not in the seed: **59** — expected, since post-seed migrations add edges.
- Edges present in the seed but not in the registry: **1** — `bo_pratijna`→`bg_ghatana`
- Seed assets absent from the registry: _none_
- Registry assets absent from the seed: `bg_gochara_citation_resolution`

## 3 — Over-declared edges (declared but not read) — evidence, not verdict

For each declared edge `A → B`, does `A`'s writer source show a textual read (`FROM`/`JOIN`)
of a table `B` produces? Two scan widths are reported because neither alone is honest:

- **tight** — only the file carrying `@register('A')`. Too narrow: most writers delegate
  their reads to a service package they import, so a tight miss means nothing on its own.
- **loose** — that file plus the local modules and service packages it imports (1 hop,
  whole-package). Too broad: a package pulled in for one helper contributes all its SQL.

| verdict | tight scan | loose scan |
|---|--:|--:|
| `read_evidence` | 167 | 268 |
| `mentioned_not_read` | 13 | 9 |
| `NO_TEXTUAL_READ_EVIDENCE` | 97 | 0 |
| `UNKNOWN_dep_declares_no_table` | 6 | 6 |
| `UNKNOWN_no_writer_source` | 1 | 1 |

**No edge lacks read evidence under the loose scan.** 97 edges
lack it under the tight scan and every one of them is explained by the writer delegating to an
imported service module. **I therefore cannot establish that any edge is over-declared, and I
am not claiming any is.** What I can report is the set of edges whose evidence is weakest —
the dependency's table is *mentioned* in the writer's source but never read from:

| edge | dependency tables | writer file |
|---|---|---|
| `bg_dasha_systems` → `bg_ontology` | `brahma_ontology` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_dasha_systems.py` |
| `bg_doshas` → `bg_ontology` | `brahma_ontology` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_doshas.py` |
| `bg_vidhi_floors` → `bg_vidhi_primitives` | `vidhi_primitives` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_vidhi_floors.py` |
| `bg_yogas` → `bg_ontology` | `brahma_ontology` | `platform/python-sidecar/pipeline/orchestrator/writers/bg_yogas.py` |
| `ka_gochara_v3_century_materialize` → `ka_moorti_nirnaya` | `kala_moorti_nirnaya` | `platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py` |
| `ka_gochara_v3_century_materialize` → `ka_kota_chakra` | `kala_kota_chakra` | `platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py` |
| `ka_sangam` → `ka_gochara` | `kala_gochara_windows` | `platform/python-sidecar/pipeline/orchestrator/writers/ka_sangam.py` |
| `ka_vighnakara` → `ka_gochara` | `kala_gochara_windows` | `platform/python-sidecar/pipeline/orchestrator/writers/ka_vighnakara.py` |
| `ph_muhurta` → `ka_gochara` | `kala_gochara_windows` | `platform/python-sidecar/pipeline/orchestrator/writers/ph_muhurta.py` |

And the edges this method cannot evaluate at all:

| edge | why |
|---|---|
| `bg_gochara_citation_resolution` → `bg_texts` | no `@register` writer source resolves for `bg_gochara_citation_resolution` |
| `ka_jivana_parva` → `ka_dasha_kala` | the dependency declares no `target_table` and no `count_sql` — there is no table whose read could be looked for |
| `ka_kshetra` → `ka_dasha_kala` | the dependency declares no `target_table` and no `count_sql` — there is no table whose read could be looked for |
| `ka_muhurta_seva` → `ka_graha_sancara` | the dependency declares no `target_table` and no `count_sql` — there is no table whose read could be looked for |
| `ka_sangam` → `ka_dasha_kala` | the dependency declares no `target_table` and no `count_sql` — there is no table whose read could be looked for |
| `ka_sangam` → `ka_muhurta_seva` | the dependency declares no `target_table` and no `count_sql` — there is no table whose read could be looked for |
| `ka_vighnakara` → `ka_muhurta_seva` | the dependency declares no `target_table` and no `count_sql` — there is no table whose read could be looked for |

## 4 — Method limits, stated plainly

- The over-declaration detector is a **regex over source text**. It cannot see dynamic SQL,
  ORM/query-builder access, a read performed by a module it failed to resolve, or a dependency
  that is a genuine *ordering* constraint rather than a data read. A dependency can be
  perfectly correct and produce no read at all.
- The **loose** scan pulls whole service packages, so `read_evidence` under loose does NOT
  prove *this writer* performs *that* read.
- `@register` resolution handles both a string literal and a module-level `ASSET_ID` constant.
  It resolved 123 writer assets; 5 registry rows have no resolvable writer source.
- The seed parser deliberately does **not** strip `/* */` blocks: the file contains prose
  strings holding glob patterns like `gochara_intensity/*`, and a naive block strip silently
  swallows 53 real entries between two of them. It also requires a left word boundary on
  `asset_id:` so `upstream_asset_id:` in the coefficient block is not miscounted as an entry.
  Both are corrections to a first version of this scan that got the seed counts wrong.
- Nothing here evaluates whether an edge *should* exist. Missing edges are the existing
  `pipeline/orchestrator/dag_edge_guard.py`'s question; this audit is its mirror image and
  does not re-run it.
