---
artifact: L3_DEPENDS_ON_AUDIT_v1_0.md
canonical_id: NIRMANA_L3_DEPENDS_ON_AUDIT
version: "1.0"
status: COMPLETE
produced_on: 2026-09-05
layer: L3
definition_revision: t0-2026-09-01-0e5b06fb
campaign_id: nirmana-elevation
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
authorized_by: >
  Conductor rulings D-CND-07 / D-CND-09 on issue #1734 (declared-vs-actual depends_on
  audit made a binding per-layer deliverable). Non-edge arbitration for
  ka_kshetra/mi_bhara per issue #1743. depends_on immutability per issue #1744 —
  this artifact is a REGISTER, not a change request.
scope: 23 L3 Kāla assets (ka_*)
mode: READ-ONLY (SELECT only; no repo write outside this file)
---

# L3 KĀLA — DECLARED-vs-ACTUAL `depends_on` AUDIT

**Verdict distribution: CLEAN 7 · HIDDEN 4 · FALSE 7 · BOTH 5 (23/23 assets, none skipped).**
36 hidden edges and 17 false edges across the layer. Every hidden edge whose target is an
L1/L2/L3/L4 asset points at an asset that **is not frozen** — because as of this audit *no asset
outside L0 has ever been frozen* (§6). Nine L3 assets are therefore HELD under D-CND-07 regardless
of what the E-gate reports.

---

## §0 — Method, and what it can and cannot see

### §0.1 What was actually run

1. **Declared side.** `SELECT asset_id, depends_on, target_table FROM asset_registry WHERE asset_id
   LIKE 'ka\_%'` — 23 rows, transcribed verbatim into §1/§2/§3. Plus the full owner map
   `SELECT target_table, string_agg(asset_id) FROM asset_registry GROUP BY target_table` (98 owned
   tables).
2. **Actual-read side, SQL.** The universe of 377 live tables was pulled from
   `information_schema.tables`, turned into a longest-match-first alternation, and grepped
   case-insensitively as `\b(from|join|update|into|delete from)\s+<table>\b` over each asset's
   writer **and** its service package. Matching against the real table universe (rather than a
   generic `FROM \w+` pattern) is what kept English prose — "derived **from** the lagna", "**join**
   via LATERAL" — out of the result set.
3. **Docstring/comment filtering.** Every hit in a shared service package was re-read at its exact
   line before being counted as a read. This mattered: **9 hits that a grep would have counted as
   edges are docstrings or comments**, and three declared edges survive or die on that distinction
   (`bg_sky_calendar`, `l1_tajik_varsha_year_lords`, `kala_tithi_pravesha` for
   `ka_gochara_v3_century_materialize`; `convergence_scores` for `ka_sangam`;
   `chart_dashas` for `ka_taranga`'s kernel). Any row in §2/§3 marked ✔ was re-read this way.
4. **Actual-read side, Python.** `grep -rnE "(from|import)\s+.*(services\.|writers\.)"` over the
   same file set, then each hit classified into three kinds — **service call** (one asset invoking
   another asset's computed output; a real DAG edge), **constant import** (module-level tuples such
   as `NAKSHATRAS`, `SIGNS`; *not* a DAG edge), and **intra-package** (an asset importing its own
   modules; not an edge). §3 states the kind for every false edge.
5. **Shared service packages were resolved by import, not by name.** Five L3 assets keep their real
   logic in packages whose directory name does not match the asset id — `ka_gochara_v3_century_
   materialize` → `services/gochara_v3/`, `ka_gochara` → `services/{gochara_grammar,w2g,
   gochara_intensity}/`, `ka_gochara_sweep` → `services/{gochara_intensity,gochara_grammar}/`,
   `ka_taranga` → `services/taranga_kernel/`, `ka_sangam` → `services/kala_trigger/`, and
   `ka_{kalasutra,yojaka,vighnakara}` → `services/ka_temporal/`. An audit that scanned only
   `services/<asset_id>/` would have missed **every** finding in those six assets.
6. **`chart_facts` owner resolution.** For each read, the query's `fact_category` (and `fact_key`
   where it narrows further) was extracted, then the emitting writer located in
   `platform/python-sidecar/ga_writers/` by the literal category string at the emission site. Where
   a query carried no category pin, the pin was resolved *empirically* against production
   (`SELECT fact_category … WHERE fact_subject=… AND fact_key=…`) and marked **inferred**, not ✔.

### §0.2 What this method cannot see (stated plainly)

- **Runtime-only edges.** Any table named through an f-string, a config value, or a `psql`/ORM
  builder is invisible. No such construction was found in L3, but absence of evidence is the honest
  claim here, not evidence of absence.
- **Transitive service depth.** Python-call edges were followed one hop into the named package. A
  package that imports a *fourth* package that queries a table is not counted.
- **Write-vs-read.** The grep counts `INSERT INTO` / `DELETE FROM` alongside `SELECT`. Every such
  hit was checked to be the asset's own target table (self-write, not an edge). None were mixed up,
  but the pattern itself does not distinguish them.
- **`chart_facts` producers are not resolvable through `asset_registry` alone.** `chart_facts` has
  **5** registry owners (`ga_ayurdaya, ga_nakshatra, ga_panchanga, ga_positions,
  ga_sensitive_degree`) but **at least 9** real producers. Four of them — **`ga_sensitive`,
  `ga_strength`, `ga_structural`, `ga_sade_sati`** — carry `target_table IS NULL` in the registry
  and are therefore *unreachable by target_table resolution in either direction*. Every owner
  attribution to those four in §2 was made from the writer source, not from the registry. This is a
  finding about the registry, not about L3.
- **A read is not proof of consumption.** Several L3 mechanisms fetch a row set into a context
  object whose dataclass has no field to receive it (§4.6). This audit reports the *read*; whether
  the value reaches a decision is W1's question, not this one.

### §0.3 Correction to the brief's worked example

The task brief cites `ka_gochara_resonance`'s `_FETCH_ARUDHA_FACTS_SQL`
(`fact_category='arudha_pada'`) as resolving to **`bo_arudha` (L2)**. **Re-derived from source, it
resolves to `ga_sensitive` (L1), not `bo_arudha`.** Three independent confirmations:

1. `platform/python-sidecar/ga_writers/ga_sensitive_writer.py:1478` emits
   `_make_row("arudha_pada", subj, "sign", …)` into `chart_facts` — the only `arudha_pada` emission
   site in the codebase.
2. Production provenance: `SELECT DISTINCT source_calculation FROM chart_facts WHERE
   fact_category='arudha_pada'` → `pyjhora_adapter.sensitive/pyjhora/1.0.0`, single value.
3. `bo_arudha`'s `target_table` is `bodha_msr_signals`, and `bo_arudha.py` contains no `chart_facts`
   reference at all — it cannot be the producer of a `chart_facts` row.

`bo_arudha` does emit `signal_type_class='arudha'` rows into `bodha_msr_signals` (25 for the
canonical chart) — that is a *different* table on a *different* layer, and `ka_gochara_resonance`
does not read it. The edge is recorded in §2 as `ka_gochara_resonance → ga_sensitive (L1)`.
Flagging this explicitly because a register built on an unverified relay is the failure mode this
deliverable exists to prevent.

---

## §1 — Summary table

`declared` = `len(depends_on)`. `hidden` = distinct *resolvable* undeclared owner assets read
(unowned-table reads are counted in §4, not here). `false` = declared assets with neither a SQL read
nor a Python service call.

| asset | declared | hidden | false | verdict |
|---|---:|---:|---:|---|
| `ka_avadhi` | 3 | 1 | 0 | **HIDDEN** |
| `ka_bhavishya_lekha` | 4 | 0 | 1 | **FALSE** |
| `ka_dasha_kala` | 1 | 0 | 0 | CLEAN |
| `ka_gochara` | 2 | 0 | 0 | CLEAN |
| `ka_gochara_resonance` | 1 | 5 | 0 | **HIDDEN** |
| `ka_gochara_sweep` | 1 | 3 | 0 | **HIDDEN** |
| `ka_gochara_v3_century_materialize` | 6 | 4 | 4 | **BOTH** |
| `ka_graha_sancara` | 1 | 0 | 0 | CLEAN |
| `ka_jivana_parva` | 5 | 0 | 1 | **FALSE** |
| `ka_kala_darshana` | 3 | 0 | 1 | **FALSE** |
| `ka_kalasutra` | 3 | 1 | 1 | **BOTH** |
| `ka_kota_chakra` | 3 | 0 | 0 | CLEAN |
| `ka_kshetra` | 8 | 11 | 4 | **BOTH** |
| `ka_moorti_nirnaya` | 3 | 0 | 1 | **FALSE** |
| `ka_muhurta_seva` | 1 | 0 | 1 | **FALSE** |
| `ka_sangam` | 10 | 1 | 0 | **HIDDEN** |
| `ka_sudarshana_varsha` | 1 | 0 | 0 | CLEAN |
| `ka_taranga` | 5 | 0 | 1 | **FALSE** |
| `ka_tithi_pravesha` | 1 | 0 | 0 | CLEAN |
| `ka_tulana` | 3 | 0 | 1 | **FALSE** |
| `ka_vedha_gochara` | 6 | 0 | 0 | CLEAN |
| `ka_vighnakara` | 4 | 2 | 1 | **BOTH** |
| `ka_yojaka` | 7 | 3 | 1 | **BOTH** |
| **TOTAL** | **79** | **36** | **17** | 7 CLEAN / 4 HIDDEN / 7 FALSE / 5 BOTH |

Read structurally: **16 of 23 L3 assets (70%) have a `depends_on` that misdescribes their real
reads in at least one direction.** The seven CLEAN assets are, without exception, the small
single-purpose overlays and services (`ka_dasha_kala`, `ka_graha_sancara`, `ka_kota_chakra`,
`ka_sudarshana_varsha`, `ka_tithi_pravesha`, `ka_vedha_gochara`, `ka_gochara`) — assets with one or
two inputs and no shared service package. Correctness of the declaration tracks the *simplicity* of
the asset, not its importance: `ka_kshetra`, the layer's heaviest asset, has the worst declaration
in the layer in both directions simultaneously.

All paths below are relative to `platform/python-sidecar/`.

---

## §2 — Section A: undeclared-but-read (hidden edges)

| asset | reads, undeclared | resolved owner (+layer) | evidence (file:line) | status |
|---|---|---|---|---|
| `ka_avadhi` | `chart_facts` pinned `fact_category='graha_position'` | **`ga_positions`** (L1) | `pipeline/orchestrator/writers/ka_avadhi.py:135,137`; producer `ga_writers/ga_positions_writer.py:19,303` | ✔ verified |
| `ka_gochara_resonance` | `brahma_event_ontology` | **`bg_ghatana`** (L0) | `services/ka_gochara_resonance/writer.py:369` | ✔ verified |
| `ka_gochara_resonance` | `chart_facts` pinned `fact_category='sensitive_degree_check'` | **`ga_sensitive_degree`** (L1) | `services/ka_gochara_resonance/writer.py:382-383`; producer `ga_writers/ga_sensitive_degree_writer.py` (prod `source_calculation` = `ga_sensitive_degree_writer/*`) | ✔ verified |
| `ka_gochara_resonance` | `chart_facts` pinned `fact_category='arudha_pada'` | **`ga_sensitive`** (L1) — *not* `bo_arudha`, see §0.3 | `services/ka_gochara_resonance/writer.py:389-390`; producer `ga_writers/ga_sensitive_writer.py:1478` | ✔ verified |
| `ka_gochara_resonance` | `ga_yoga_firings` | **`ga_yoga`** (L1) | `services/ka_gochara_resonance/writer.py:396` | ✔ verified |
| `ka_gochara_resonance` | `chart_dashas` | **`ga_dashas`** (L1) | `services/ka_gochara_resonance/writer.py:412` | ✔ verified |
| `ka_gochara_sweep` | `chart_dashas` (own writer + `gochara_grammar.dasha_data`) | **`ga_dashas`** (L1) | `services/ka_gochara_sweep/writer.py:626`; `services/gochara_grammar/dasha_data.py:50` | ✔ verified |
| `ka_gochara_sweep` | `brahma_event_ontology` (own sweep + `gochara_intensity`) | **`bg_ghatana`** (L0) | `services/ka_gochara_sweep/sweep.py:151`; `services/gochara_intensity/engine.py:81`; `services/gochara_intensity/valence.py:96` | ✔ verified |
| `ka_gochara_sweep` | `chart_facts` pinned `fact_category='graha_position'` | **`ga_positions`** (L1) | `services/gochara_intensity/enrichment.py:137-138` (imported at `services/ka_gochara_sweep/sweep.py:123`) | ✔ verified |
| `ka_gochara_v3_century_materialize` | `brahma_event_ontology` | **`bg_ghatana`** (L0) | `pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py:860,967`; `services/gochara_v3/threshold.py:173` | ✔ verified |
| `ka_gochara_v3_century_materialize` | `chart_facts` pinned `fact_category='graha_position'` | **`ga_positions`** (L1) | `services/gochara_v3/context.py:270,272` | ✔ verified |
| `ka_gochara_v3_century_materialize` | `chart_facts` pinned `fact_category IN ('sade_sati_cycle','sade_sati_phase')` | **`ga_sade_sati`** (L1) | `services/gochara_v3/context.py:386,388`; producer `ga_writers/ga_sade_sati_writer.py:943` | ✔ verified |
| `ka_gochara_v3_century_materialize` | `bg_vedha_malefic_scale` | **`bg_vedha_malefic_scale`** (L0) | `services/gochara_v3/context.py:485` | ✔ verified |
| `ka_kalasutra` | `chart_dashas` via `services.ka_temporal` | **`ga_dashas`** (L1) | import `pipeline/orchestrator/writers/ka_kalasutra.py:16`; SQL `services/ka_temporal/date_resolver.py:244,334,350` | ✔ verified |
| `ka_kshetra` | `bg_kp_sublord_division` | **`bg_kp_sublord_division`** (L0) | `services/ka_kshetra/stage3_clocks.py:624` | ✔ verified |
| `ka_kshetra` | `bg_transit_rules` | **`bg_transit_rules`** (L0) | `services/ka_kshetra/stage0_kinematics.py:721` | ✔ verified |
| `ka_kshetra` | `bodha_cgm_nodes` | **`bo_bimba`** (L2) | `services/ka_kshetra/stage2_promise.py:327` | ✔ verified |
| `ka_kshetra` | `bodha_cgm_edges` | **`bo_karanajala`** (L2) | `services/ka_kshetra/stage2_promise.py:338` | ✔ verified |
| `ka_kshetra` | `bodha_msr_signals`, no producer filter | **`bo_laksana`** + 6 co-owners (L2) — see §4.1 | `services/ka_kshetra/stage2_promise.py:397` | ✔ read verified / owner **inferred** |
| `ka_kshetra` | `brahma_event_ontology` | **`bg_ghatana`** (L0) | `services/ka_kshetra/stage4_field.py:1188`; `services/ka_kshetra/writer.py:1480` | ✔ verified |
| `ka_kshetra` | `chart_dashas` | **`ga_dashas`** (L1) | `services/ka_kshetra/stage3_clocks.py:400,414,428,509,518,1014,1159`; `services/ka_kshetra/uncertainty.py:256` | ✔ verified |
| `ka_kshetra` | `chart_facts` pinned `fact_category='graha_position'` | **`ga_positions`** (L1) | `services/ka_kshetra/stage0_kinematics.py:686`; `services/ka_kshetra/stage3_clocks.py:361`; `services/ka_kshetra/uncertainty.py:217` | ✔ verified |
| `ka_kshetra` | `chart_facts` pinned `fact_category='graha_sign_attributes'` | **`ga_positions`** (L1) | `services/ka_kshetra/stage3_clocks.py:384`; producer `ga_writers/ga_positions_writer.py:303` | ✔ verified |
| `ka_kshetra` | `ephemeris_daily` | **`bg_ephemeris`** (L0) | `services/ka_kshetra/stage0_kinematics.py:635,966` | ✔ verified |
| `ka_kshetra` | `kala_gochara_windows` | **`ka_gochara_sweep`** (L3) — co-owner `ka_gochara` is stale, see §4.4 | `services/ka_kshetra/stage4_field.py:1384`; `services/ka_kshetra/writer.py:2186` | ✔ read verified / owner **inferred** |
| `ka_kshetra` | `phala_rectification` — **L3 reading L4** | **`ph_rectification`** (L4) | `services/ka_kshetra/uncertainty.py:191` | ✔ verified |
| `ka_sangam` | `chart_facts` pinned `fact_category='saham_position'` via `services.kala_trigger` | **`ga_sensitive`** (L1) | import `pipeline/orchestrator/writers/ka_sangam.py:38`; SQL `services/kala_trigger/trigger.py:256,259`; producer `ga_writers/ga_sensitive_writer.py:1192` | ✔ verified |
| `ka_vighnakara` | `kala_activation_predicates` | **`ka_yojaka`** (L3) | `pipeline/orchestrator/writers/ka_vighnakara.py:414` | ✔ verified |
| `ka_vighnakara` | `chart_dashas` via `services.ka_temporal` | **`ga_dashas`** (L1) | import `pipeline/orchestrator/writers/ka_vighnakara.py:27`; SQL `services/ka_temporal/date_resolver.py:350` | ✔ verified |
| `ka_yojaka` | `chart_facts` pinned `fact_category='lord_in_house_per_varga'` | **`ga_structural`** (L1) | `pipeline/orchestrator/writers/ka_yojaka.py:370-371`; producer `ga_writers/ga_structural_writer.py:5020` | ✔ verified |
| `ka_yojaka` | `chart_facts` pinned `fact_category IN ('yoga_label','dosha_label',…)` | **`ga_structural`** (L1) | `pipeline/orchestrator/writers/ka_yojaka.py:548,550`; producers `ga_writers/ga_structural_writer.py:2321,3090` | ✔ verified |
| `ka_yojaka` | …same query's third category `'graha_position'` | **`ga_positions`** (L1) | `pipeline/orchestrator/writers/ka_yojaka.py:550`; producer `ga_writers/ga_positions_writer.py:19` | ✔ verified |
| `ka_yojaka` | `ga_yoga_firings` | **`ga_yoga`** (L1) | `pipeline/orchestrator/writers/ka_yojaka.py:507` | ✔ verified |

**36 hidden edges; 34 marked ✔ verified from source, 2 marked read-verified/owner-inferred** (both
are shared-table reads with no producer filter — §4.1 and §4.4).

### §2.1 — The shape of the hidden set

- **`chart_dashas` → `ga_dashas` is hidden 5 times** (`ka_gochara_resonance`, `ka_gochara_sweep`,
  `ka_kalasutra`, `ka_kshetra`, `ka_vighnakara`) while being *correctly declared* by six other L3
  assets. The same table, in the same layer, is declared by some readers and not others.
- **`chart_facts` → `ga_positions` is hidden 5 times.** Two of those five assets
  (`ka_gochara_sweep`, `ka_kalasutra`/`ka_vighnakara` via `ka_temporal`) reach it only through a
  shared service package, which is exactly the read a directory-name-matching audit misses.
- **Three of the four registry-invisible L1 producers appear as hidden edges** — `ga_sensitive`
  (twice), `ga_structural` (twice), `ga_sade_sati` (once). No L3 asset declares any of them, and no
  L3 asset *could* have found them through `target_table`.
- **One layer inversion:** `ka_kshetra` (L3) reads `phala_rectification` (L4). This is the only
  downward-layer read in L3 and the only hidden edge that inverts the build arc.

---

## §3 — Section B: declared-but-unread (false edges)

Every row was checked for a Python-call edge before being called false, per the brief. "Call edge
found: none" means: no import of the target's service module, no reference to the target's
`target_table`, and no reference to the target asset id outside comments.

| asset | declares, unread | owner's table (+layer) | evidence of absence (file:line) | Python-call edge? | status |
|---|---|---|---|---|---|
| `ka_bhavishya_lekha` | `ka_vighnakara` | `kala_obstruction` (L3) | no occurrence of `kala_obstruction` or `ka_vighnakara` anywhere in `pipeline/orchestrator/writers/ka_bhavishya_lekha.py` (267 lines, whole-file grep) | **none** | ✔ verified false |
| `ka_gochara_v3_century_materialize` | `ka_moorti_nirnaya` | `kala_moorti_nirnaya` (L3) | table named only in YAML prose — `services/gochara_v3/grammar_v3_registry.yaml:58,65,69`; the mechanism is documented to read it "pre-fetched in ClassContext", and `ClassContext` has **no** moorti field (`services/gochara_v3/context.py:110-175` field list) | **none** | ✔ verified false |
| `ka_gochara_v3_century_materialize` | `ka_kota_chakra` | `kala_kota_chakra` (L3) | same pattern — `services/gochara_v3/grammar_v3_registry.yaml:142,146`; `services/gochara_v3/mechanisms/w25_kota_chakra.py:19` states the v1 table "was never read"; no `ClassContext` field | **none** | ✔ verified false |
| `ka_gochara_v3_century_materialize` | `ka_tithi_pravesha` | `kala_tithi_pravesha` (L3) | `services/gochara_v3/mechanisms/w27_annual_stack.py:24,30` — "ClassContext is the sole data source (no DB access)"; the named field `context.tithi_pravesha_rows` does not exist on the dataclass | **none** | ✔ verified false |
| `ka_gochara_v3_century_materialize` | `bg_sky_calendar` | `bg_sky_calendar` (L0) | `grep -n "SELECT\|FROM\|execute" services/gochara_v3/mechanisms/w26_real_eclipses.py` → **zero matches**; every `bg_sky_calendar` mention in the tree is a docstring or YAML line | **none** | ✔ verified false |
| `ka_jivana_parva` | `ka_dasha_kala` | *(service asset, no table)* (L3) | no `ka_dasha_kala` / `KaDashaKala` reference in `pipeline/orchestrator/writers/ka_jivana_parva.py`; the writer reads `chart_dashas` directly at `:75,:263` | **none** | ✔ verified false |
| `ka_kala_darshana` | `ka_kalasutra` | `kala_activation` (L3) | no `kala_activation` reference in `pipeline/orchestrator/writers/ka_kala_darshana.py`; its only reads are `kala_convergence:24` and `kala_obstruction:38` | **none** | ✔ verified false |
| `ka_kalasutra` | `bo_laksana` | `bodha_msr_signals` (L2) | no `bodha_msr_signals` reference in `pipeline/orchestrator/writers/ka_kalasutra.py` | **none** | ✔ verified false |
| `ka_kshetra` | `ka_dasha_kala` | *(service asset, no table)* (L3) | `ka_dasha_kala` appears only in comments — `services/ka_kshetra/stage3_clocks.py:30`, `services/ka_kshetra/stage0_kinematics.py:52`; the package reads `chart_dashas` directly (8 sites) | **none** | ✔ verified false |
| `ka_kshetra` | `ga_panchanga` | `chart_facts` `panchanga_*` (L1) | no `chart_facts` query in the package pins any `panchanga_*` category (all pins enumerated: `graha_position`, `graha_sign_attributes`, `lagna`) | **none** | ✔ verified false |
| `ka_kshetra` | `bo_sangati` | `bodha_cdlm_cells` (L2) | no `bodha_cdlm_cells` reference anywhere in `services/ka_kshetra/` | **none** | ✔ verified false |
| `ka_kshetra` | `bo_upaya` | `bodha_rm_resonances` (L2) | no `bodha_rm_resonances` reference anywhere in `services/ka_kshetra/` | **none** | ✔ verified false |
| `ka_moorti_nirnaya` | `bg_transit_rules` | `bg_transit_rules` (L0) | the string appears once, inside a log message — `services/ka_moorti_nirnaya/writer.py:187`: `"bg_transit_moorti is empty — run bg_transit_rules (L0 seed) first"`. The writer reads `bg_transit_moorti` (`:84`), never `bg_transit_rules`. **Build-order rationale is real** (the L0 writer seeds the table this asset reads), but the *read* is of a different table — see §4.3 | **none** | ✔ verified false (as a read) |
| `ka_muhurta_seva` | `ka_graha_sancara` | *(service asset, no table)* (L3) | the asset's own package docstring says so: `services/ka_muhurta_seva/__init__.py:27` — `"Depends on: ka_graha_sancara (planned)"`. Its only SQL is `asset_registry` at `services/ka_muhurta_seva/writer.py:295` (service-health self-write) | **none** | ✔ verified false |
| `ka_taranga` | `ka_avadhi` | `kala_avadhi` (L3) | zero occurrences of `kala_avadhi` in `pipeline/orchestrator/writers/ka_taranga.py` or `services/taranga_kernel/` | **none** | ✔ verified false |
| `ka_tulana` | `ka_vighnakara` | `kala_obstruction` (L3) | no `kala_obstruction` reference in `services/ka_tulana/`; `ranker.py` reads `kala_convergence:58,211` and `kala_darshana:69` only | **none** | ✔ verified false |
| `ka_vighnakara` | `ka_gochara` | `kala_gochara_windows*` (L3) | `grep -rn "ka_gochara\|GocharaTransit\|kala_gochara" pipeline/orchestrator/writers/ka_vighnakara.py` → **zero matches** | **none** | ✔ verified false |
| `ka_yojaka` | `bg_transit_rules` | `bg_transit_rules` (L0) | zero occurrences of `bg_transit_rules` in `pipeline/orchestrator/writers/ka_yojaka.py` or `services/ka_yojaka/` | **none** | ✔ verified false |

**17 false edges, all ✔ verified, all with no Python-call edge behind them.** Not one false edge in
L3 turned out to be a call edge invisible to SQL grep.

### §3.1 — Python-call edges that ARE real (and are correctly declared)

Recorded here so the register shows the method found them, not only the misses:

| caller | callee | kind | evidence |
|---|---|---|---|
| `ka_sangam` | `ka_dasha_kala` | **service call** (`KaDashaKalaService`) | `pipeline/orchestrator/writers/ka_sangam.py:35` — declared ✔ |
| `ka_sangam` | `ka_gochara` | **service call** (`KaGocharaService`/`GocharaTransitService`) | `pipeline/orchestrator/writers/ka_sangam.py:36` — declared ✔ |
| `ka_sangam` | `ka_muhurta_seva` | **service call** (`KaMuhurtaSevaService`) | `pipeline/orchestrator/writers/ka_sangam.py:37` — declared ✔ |
| `ka_vighnakara` | `ka_muhurta_seva` | **service call** (`KaMuhurtaSevaService`, lazy) | `pipeline/orchestrator/writers/ka_vighnakara.py:202` — declared ✔ |

`ka_sangam` is the only L3 asset whose ten declared edges are **all** justified — seven by SQL, three
by service call. It is the layer's one correct declaration of a non-trivial asset.

### §3.2 — Python imports that are NOT edges (recorded so they are never mistaken for one)

Four assets import module-level **constants** (`ALL_GRAHAS`, `NAKSHATRAS`, `NAK_SIZE_DEG`, `SIGNS`)
from `services/ka_graha_sancara/engine.py`. These are frozen tuples, not the service's computed
output; they create a Python import edge and **no build-order dependency**, and none of the four
declares `ka_graha_sancara`. Recorded as *correctly undeclared*, not as hidden edges:

- `services/ka_kota_chakra/writer.py:56` · `services/ka_moorti_nirnaya/writer.py:49` ·
  `services/ka_sudarshana_varsha/writer.py:34` · `services/ka_vedha_gochara/writer.py:60`.

If a future definition freeze chooses to treat constant imports as edges, these four rows are where
that decision lands. This audit does not treat them as edges.

---

## §4 — Ambiguous reads

Reads that could not be resolved to exactly one owning asset. Each is itself a finding.

### §4.1 — `bodha_msr_signals` read with no producer filter (4 assets)

`bodha_msr_signals` has **seven** registry owners: `bo_arudha, bo_laksana, bo_laksana_rerank,
bo_nakshatra_semantic, bo_special_lagna, bo_sudarshana, bo_vargottama_dhana`. Four L3 assets read it
with `WHERE chart_id = %s` or `WHERE signal_id = ANY(...)` and **no `signal_type_class` predicate**,
so every read touches all seven producers' rows:

- `pipeline/orchestrator/writers/ka_yojaka.py:81` — `WHERE chart_id = %s`, unfiltered.
- `pipeline/orchestrator/writers/ka_sangam.py:286,343` — `LEFT JOIN … ON s.signal_id = p.signal_id`.
- `pipeline/orchestrator/writers/ka_bhavishya_lekha.py:68` — `WHERE signal_id IN (…)`.
- `services/ka_kshetra/stage2_promise.py:397` — `WHERE signal_id = ANY(%s)`.

Measured distribution for the canonical chart (`SELECT signal_type_class, count(*) FROM
bodha_msr_signals WHERE chart_id='482012f1-…' GROUP BY 1`): `composite_state` 37,215 ·
`karaka_alignment` 5,958 · `sade_sati` 2,871 · `varga_pattern` 1,304 · `tradition_specific` 1,169 ·
`panchanga` 590 · `annual` 315 · `parivartana` 219 · `configuration` 145 · `yoga` 74 ·
`bhavat_bhavam_amplifier` 60 · `sudarshana_agreement` 45 · `nakshatra_semantic` 45 · `dosha` 26 ·
`arudha` 25 · `special_lagna` 20 · `dhana_axis` 10 · `varga_ratification_divergence` 9 ·
`vargottama_amplification` 4. **`bo_laksana` is the majority producer but demonstrably not the sole
one** — `arudha`, `nakshatra_semantic`, `special_lagna`, `sudarshana_agreement`, `dhana_axis` and
`vargottama_amplification` rows come from six sibling writers. Three of the four readers declare
`bo_laksana`; `ka_kshetra` declares none of the seven. **Ambiguous: a `bo_laksana` declaration
under-states the read by six assets.**

### §4.2 — `chart_facts` reads with no `fact_category` pin (3 sites, 2 assets)

Category-only or subject-only selection is the §N.7 item 2 defect class. Three L3 reads carry no
category pin at all:

- `pipeline/orchestrator/writers/ka_sangam.py:761` — `WHERE fact_subject='MOON' AND fact_key IN
  ('nakshatra','sign')`. Resolved **empirically**: production has exactly one category carrying that
  subject/key pair (`graha_position`, 15 rows each) → `ga_positions`. **Inferred, not verified** —
  the query does not pin it, and a future writer emitting a second `MOON`/`nakshatra` category would
  silently change what this reads.
- `pipeline/orchestrator/writers/ka_sangam.py:1113` — `WHERE fact_subject='LAGNA' AND
  fact_key='sign' LIMIT 1`, no `ORDER BY`. Resolves empirically to `graha_position` → `ga_positions`.
  The bare `LIMIT 1` over an unordered set is non-deterministic across `build_id` generations. The
  code's own fallback (`lagna_sign = 'Aries'`, `:1109`) is this native's value — a §N.7 item 6 hazard,
  noted but out of scope here.
- `services/ka_kshetra/writer.py:953` and `:2056` — `WHERE fact_id = ANY(%s)` with ids inherited from
  L2 promise edges. **Genuinely unresolvable**: the fact ids can originate from any `chart_facts`
  producer, and the query is a resolvability check by design. Correctly ambiguous.

### §4.3 — Reads of tables with NO registry owner (7 tables)

These reads cannot be resolved to *any* asset because no `asset_registry` row claims the table:

| table | read by | evidence |
|---|---|---|
| `bg_combustion_orbs` | `ka_vighnakara` | `pipeline/orchestrator/writers/ka_vighnakara.py:307` |
| `bg_transit_moorti` | `ka_moorti_nirnaya` | `services/ka_moorti_nirnaya/writer.py:84` |
| `bg_transit_av_gates` | `ka_gochara_v3_century_materialize`, `ka_gochara` | `services/gochara_v3/context.py:336`; `services/gochara_grammar/primitives.py:736` |
| `bg_synthetic_cohort_md` | `ka_kshetra` | `services/ka_kshetra/cohort_client.py:179,338` |
| `kala_gochara_authority` | `ka_kshetra` | `services/ka_kshetra/stage4_field.py:1388`; `services/ka_kshetra/writer.py:2171` |
| `charts` (`public.charts`) | `ka_vighnakara`, and `ka_{kalasutra,yojaka,vighnakara}` via `ka_temporal` | `pipeline/orchestrator/writers/ka_vighnakara.py:342`; `services/ka_temporal/date_resolver.py:313` |
| `ka_kshetra_tier_basis`, `kala_gochara_v2_build_state`, `kala_field_*` (13 sub-tables), `kala_insights`, `kala_timeline_spec` | self-writes by `ka_kshetra` / `ka_gochara_v3` | e.g. `services/ka_kshetra/stage3_clocks.py:1096` |

The last row is benign (an asset's own auxiliary tables). The first six are not: a reader of
`bg_combustion_orbs` or `bg_transit_moorti` has a genuine build-order dependency on *whatever seeds
that table*, and no registry row expresses it. `ka_moorti_nirnaya`'s own log line names the seeder
(`bg_transit_rules`) — so the declared edge in §3 encodes a **true** build-order fact through a
**false** read claim. That is the cleanest example in the layer of why a `depends_on` audit must
report both directions and let the Conductor rule, rather than proposing a fix.

### §4.4 — `kala_gochara_windows` has two registry owners, one of which is stale

`asset_registry` gives `kala_gochara_windows` two owners: `ka_gochara` and `ka_gochara_sweep`. But
`ka_gochara`'s writer states across nine separate lines that it never touches that table —
`pipeline/orchestrator/writers/ka_gochara.py:37,41,56,59` — and its actual DELETE/INSERT target is
`kala_gochara_windows_v2` (`:120` `TABLE = "kala_gochara_windows_v2"`, `:141`, `:287`). So
`ka_kshetra`'s read of `kala_gochara_windows` (§2) resolves to **`ka_gochara_sweep`** in reality,
while the registry offers two candidates. Marked *inferred*.

Symmetrically, `kala_gochara_windows_v2` is registered to `ka_gochara_v3_century_materialize` but is
written by **two** assets (`ka_gochara` at `:141`, generation `'2.0'`; `ka_gochara_v3` at `:1738`).
Both facts are `target_table` defects, not `depends_on` defects — recorded here because they are the
mechanism by which a `depends_on` resolution goes wrong, and because §0.2's limit ("owner resolution
is only as good as `target_table`") is concrete here.

### §4.5 — One read that resolves to zero rows in production (`ka_vighnakara`)

`pipeline/orchestrator/writers/ka_vighnakara.py:374-385` (`_fetch_natal_lagna_lon`) selects
`WHERE fact_subject='LAGNA' AND fact_key='longitude' AND ayanamsha_id='lahiri_chitrapaksha'
LIMIT 1`. Measured: `SELECT count(*) FROM chart_facts WHERE fact_subject='LAGNA' AND
fact_key='longitude'` → **0 rows**. Production carries `LAGNA` under eleven categories, none with
`fact_key='longitude'`. The declared `ga_positions` edge is therefore *intent-correct and
read-dead*: papakartari and combustion detection run on `natal_lagna_lon = None` on every chart.
Recorded as ambiguous-by-emptiness — the read names no category, and the owner it would resolve to
emits nothing matching it. **A behavioural defect, filed here as evidence, not fixed.**

The same shape appears at `services/ka_kshetra/writer.py:1653-1659`, which pins
`fact_category='lagna'` — a category with **0 rows** anywhere in `chart_facts` (the real category is
`lagna_position`, cf. `pipeline/writers/chart_facts_writer_a3.py:168`). Also read-dead.

### §4.6 — Reads that exist but cannot reach a consumer

`services/gochara_v3/mechanisms/w25_kota_chakra.py`, `w27_annual_stack.py` and the moorti mechanism
all document themselves as reading rows "pre-fetched in `ClassContext`". The `ClassContext`
dataclass (`services/gochara_v3/context.py:110-175`) declares exactly: `chart_id, event_class,
resonance_targets, promise, promise_detail, dasha_periods, relevant_grahas, relevant_signs,
temporal_shape, valence, is_adverse, beta_e, weight_by_target_ref, natal_facts, av_gate_rows,
av_gate_fetch_error, sade_sati_phases, vedha_rows, malefic_scale`. **No moorti, kota,
tithi_pravesha, tajaka or sudarshana field exists.** This is why the four `ka_gochara_v3` edges in
§3 are false rather than merely SQL-invisible, and it independently corroborates
`L3_W1_ANALYSIS_INDEX_v1_0.md §2.2`.

---

## §5 — Deliberate non-edges

### §5.1 — `ka_kshetra` ↔ `mi_bhara` is a VERSION PIN, never a DAG edge, in either direction

`ka_kshetra` reads `kala_field_weight_versions` at `services/ka_kshetra/stage4_field.py:1099`
(and the weights themselves at `:1112`). `asset_registry` gives that table's owner as **`mi_bhara`
(L5)**. A naive `target_table` resolution therefore proposes the edge `ka_kshetra → mi_bhara`.

**That edge must never be added, and must not be recorded in this register as a missing edge.**
Reasoning, as arbitrated with the L5 session on issue #1743:

1. `assert_no_weights_cycle` (`services/mi_bhara/weights.py:263`) exists specifically to reject this
   relation. L5's `mi_bhara` derives its weights *from* L3 field output; an L3→L5 edge closes the
   loop the assertion is written to catch.
2. `topoSort` would then reject **every** build plan containing either asset — not just plans
   building both. The failure is not a degraded ordering; it is a total refusal to plan.
3. The read is not a data dependency. `kala_field_weight_versions` is a **version pin**: `ka_kshetra`
   reads it to stamp *which* weight generation it computed against, so a later run can tell whether
   the weights moved underneath it. The row it reads was written by a prior, already-complete L5
   pass — a provenance stamp, not an input the current build must wait for.

Recorded as: **deliberate non-edge, both directions, permanently.** Any future automated
`depends_on` derivation must carry an explicit exclusion for this pair, because every purely
mechanical resolution will re-propose it.

### §5.2 — `ka_graha_sancara` constant imports (4 assets)

Per §3.2 — four assets import frozen tuples from `services/ka_graha_sancara/engine.py`. Recorded as
a deliberate non-edge: a constant import is not a build-order dependency, and treating it as one
would add four edges to the DAG that constrain ordering for no data reason. Listed rather than
silently dropped so a future freeze can rule on it explicitly.

### §5.3 — Infrastructure-table reads are not edges (4 assets)

`asset_registry` (`services/ka_dasha_kala/writer.py:88,94`;
`pipeline/orchestrator/writers/ka_graha_sancara.py:192,197`;
`services/ka_muhurta_seva/writer.py:295`; `services/ka_tulana/writer.py:66,71`) and
`build_substep_progress` (`services/ka_gochara_sweep/writer.py:342,651,666`;
`services/ka_kshetra/writer.py:2277,2290,2302`; `pipeline/orchestrator/writers/ka_sangam.py:435,491,510`)
are orchestrator/service-health infrastructure, owned by no asset. Not counted as reads in §1/§2.

---

## §6 — Consequences: which hidden edges point at assets that are NOT frozen

### §6.1 — The measurement

```sql
SELECT layer, count(DISTINCT entity_id)
FROM nirmana_evidence.nirmana_elevation_campaign_events
WHERE event_type = 'asset_frozen' GROUP BY 1;
```
→ **`L0 | 29`. One row. No other layer appears.**

The 29 frozen assets, in full: `bg_class_lifetime_counts, bg_class_priors, bg_dignity_reference,
bg_ephemeris, bg_ephemeris_engine, bg_formula_constants, bg_ghatana, bg_gochara_citation_resolution,
bg_kota_chakra_rings, bg_kp_sublord_division, bg_medical_mappings, bg_muhurta_lattice, bg_nakshatra,
bg_nakshatra_medical, bg_ontology, bg_panchanga, bg_phaladeepika_latta, bg_prashna_rules,
bg_reference, bg_remedies, bg_sarvatobhadra_grid, bg_sign_medical, bg_sky_calendar, bg_texts,
bg_transit_engine, bg_transit_rules, bg_vastu_directions, bg_vedha_malefic_scale,
bg_vidhi_primitives`.

**Therefore: every L1, L2, L3, L4 and L5 asset in the system is unfrozen.** Under D-CND-07, a hidden
edge into any of them holds the depending asset regardless of the E-gate's verdict. The gate cannot
see these edges — that is what makes them hidden — so the gate will report open on assets that are
held.

### §6.2 — The HELD list (operationally load-bearing)

**Nine L3 assets carry at least one hidden edge into an unfrozen asset. The L3 session may not
dispatch any of them on the E-gate's word alone.**

| HELD asset | hidden edge(s) into UNFROZEN assets | unfrozen targets | also hidden into frozen L0 (does not hold) |
|---|---:|---|---|
| `ka_gochara_resonance` | 4 of 5 | `ga_sensitive_degree`, `ga_sensitive`, `ga_yoga`, `ga_dashas` (all L1) | `bg_ghatana` |
| `ka_kshetra` | 7 of 11 | `bo_bimba`, `bo_karanajala`, `bo_laksana`+6 (L2); `ga_dashas`, `ga_positions` (L1); `ka_gochara_sweep` (L3); **`ph_rectification` (L4)** | `bg_kp_sublord_division`, `bg_transit_rules`, `bg_ghatana`, `bg_ephemeris` |
| `ka_yojaka` | 3 of 3 | `ga_structural`, `ga_positions`, `ga_yoga` (all L1) | — |
| `ka_gochara_sweep` | 2 of 3 | `ga_dashas`, `ga_positions` (L1) | `bg_ghatana` |
| `ka_gochara_v3_century_materialize` | 2 of 4 | `ga_positions`, `ga_sade_sati` (L1) | `bg_ghatana`, `bg_vedha_malefic_scale` |
| `ka_vighnakara` | 2 of 2 | `ka_yojaka` (L3), `ga_dashas` (L1) | — |
| `ka_avadhi` | 1 of 1 | `ga_positions` (L1) | — |
| `ka_kalasutra` | 1 of 1 | `ga_dashas` (L1) | — |
| `ka_sangam` | 1 of 1 | `ga_sensitive` (L1) | — |

**Not held by a hidden edge** (the other 14): `ka_bhavishya_lekha`, `ka_dasha_kala`, `ka_gochara`,
`ka_graha_sancara`, `ka_jivana_parva`, `ka_kala_darshana`, `ka_kota_chakra`, `ka_moorti_nirnaya`,
`ka_muhurta_seva`, `ka_sudarshana_varsha`, `ka_taranga`, `ka_tithi_pravesha`, `ka_tulana`,
`ka_vedha_gochara`.

### §6.3 — The sharper statement, which the table above under-sells

The HELD list is the answer to the question as posed — *which hidden edges point at unfrozen
assets*. But the honest operational reading is broader, and the L3 session should have it stated
rather than inferred:

**Because nothing outside L0 is frozen, every L3 asset with any L1/L2/L3/L4 dependency at all —
declared or hidden — depends on unfrozen ground.** Of the 79 declared L3 edges, 40 point at
non-L0 assets. Only three L3 assets (`ka_kota_chakra`, `ka_vedha_gochara`, and `ka_graha_sancara`)
have dependency sets that are *entirely* L0-frozen once their hidden edges are folded in — and the
first two reach L1 `ga_positions` through a declared edge, so strictly only `ka_graha_sancara`
(declares `bg_ephemeris`, reads `ephemeris_daily`, nothing else) stands on wholly frozen ground.

The nine-asset HELD list is therefore the *minimum* hold implied by D-CND-07's hidden-edge clause,
not the full extent of the layer's exposure. **Ruling that a hidden edge into an unfrozen asset
holds the depender, while a declared one does not, would hold nine assets and release fourteen that
rest on exactly the same unfrozen L1 — a distinction the freeze state does not currently support.**
That asymmetry is surfaced for the Conductor's campaign-wide remedy; this register does not resolve
it and proposes no `depends_on` change (issue #1744).

### §6.4 — Two consequences that survive any freeze ruling

1. **`ka_kshetra` → `ph_rectification` inverts the layer arc.** An L3 asset reading an L4 table
   (`services/ka_kshetra/uncertainty.py:191`) is the one hidden edge whose problem is not freeze
   state. Whatever the freeze remedy, this edge points *forward* in the build order and cannot be
   satisfied by ordering. Flagged for the Conductor as distinct in kind from the other 35.
2. **Four L1 `chart_facts` producers cannot be declared even if someone wanted to.** `ga_sensitive`,
   `ga_strength`, `ga_structural` and `ga_sade_sati` carry `target_table IS NULL`, so no
   table-driven derivation can find them and no reader can resolve a `chart_facts` read to them
   without reading `ga_writers/` source. Five of L3's hidden edges (§2.1) land on three of these
   four. A future definition freeze that derives `depends_on` from `target_table` will reproduce
   these five hidden edges exactly, in L3 and in every other layer that reads `chart_facts`.

---

*End of L3 declared-vs-actual `depends_on` audit v1.0. 23/23 assets; 36 hidden edges (34 ✔ verified
from source, 2 read-verified/owner-inferred); 17 false edges (17 ✔ verified, none masking a
Python-call edge); 2 deliberate non-edge classes; 9 HELD assets under D-CND-07. No `asset_registry`
row was modified, and no correction to `depends_on` is proposed — `depends_on` is immutable for the
remainder of the campaign per the ruling on #1744.*
