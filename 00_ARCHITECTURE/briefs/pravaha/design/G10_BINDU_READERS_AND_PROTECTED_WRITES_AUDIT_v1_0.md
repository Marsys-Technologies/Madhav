---
artifact: G10_BINDU_READERS_AND_PROTECTED_WRITES_AUDIT
version: "1.0"
status: AUDIT (read-only; nothing changed) — answers steward M20261002T114945-8c9e for the L0/L1 owner (Suvarṇa)
date: 2026-10-02
author: Stream B (Śāstra), item B6.0
method: "git grep over origin/main (code as merged) and Stream A's integration tree (the v5 writer and kernel stores); file:line cites are on those refs. Production facts none needed."
---

# (1) Who reads `ashtakavarga_bindu_contributor` — and what each does while the rows are absent
**Bottom line: every Pravāha reader of these rows handles absence by a NAMED state or a refusal; none substitutes a silent default.** Two behaviours deserve Suvarṇa's eye (marked ◆). When the rows first exist (earliest 2026-10-04) four readers change behaviour from "named unavailable" to "resolved" — none of them writes back, so no stored Pravāha row changes until a **rebuild**.

| # | reader (file:line, origin/main) | reads | when the rows are ABSENT today | kind |
|---|---|---|---|---|
| 1 | `scripts/kala_gochara_cutover/step06a_class_context.py:111–155` `fetch_av_donor_matrix` (called `:497`, stored `:523`, emitted `:587–589`) | the per-chart SET of `{GRAHA}-CONTRIBUTOR_{DONOR}-SIGN_{N}` keys, `fact_key='bindus'`, pinned to `lahiri_chitrapaksha` | `available_keys: []`, `row_count: 0`; a DB error is recorded in `error` and **resolves nothing** ("never silently treated as present"); duplicate-key conflicts are excluded and listed. The document names the operand `av_donor_matrix` as unresolved | **named missing input** |
| 2 | `step06b_windows_projection.py:1055–1073` `p5c_operand_state` (used `:1366–1380`, declared `:1017–1024`) | the key set from reader 1, per kakṣyā-crossing contact only | key not in the set ⇒ `state: "unresolved"`, `operand: "av_donor_matrix:<key>"`, and the window's outcome is `unqualified` with the operand named (O-TV-3). ◆ If the context document carries **no** matrix block at all (old documents / rehearsal) the state is `"not_probed"` (named, but distinct from unresolved) unless a legacy chart-level declaration named the operand | **named missing input** (◆ one legacy path says `not_probed`) |
| 3 | `services/gochara_grammar/primitives.py:759–816` `_fetch_kakshya_donor_bindu`; `:819–851` `kakshya_donor_bindu_detail` | one donor row by exact subject | returns `None` — the docstring: "the honest 'unavailable', never a fabricated 0 or 1"; detail carries `donor_bindu_state: "unavailable"`, `donor_row_key` | **named missing input**. (grep finds **no caller outside tests** for `kakshya_donor_bindu_detail`) |
| 4 | `services/gochara_v3/context.py:807–880` `_fetch_bindu_contributor_rows` (stored `:265, :342, :367`) | all rows for the chart | an empty tuple (a failed fetch is logged at info, an empty tuple results; conflicting rows are excluded) | **named (empty set)** |
| 5 | `services/gochara_v3/engine.py:1556–1560, 1603–1625` (kakṣyā-cell crossing, flag `kakshya_bindu_interim`, default **off**; the `'4.1'` manifest records it **on**) | `contributor_lookup` built from reader 4 | donor path resolves nothing ⇒ ◆ the **sign-grain interim** (`_bindu_interim_detail`) is applied, **labelled as the coarser P5a qualification**, with `donor_bindu: None`, `donor_bindu_state: "unavailable"`, `donor_row_key` set. This is a *named degraded substitution*, not a silent default — but it is a value from a different, coarser operand | **named, labelled fallback** |
| 6 | `services/gochara_rules/ashtakavarga.py:105–120` `p5c`, `:123–135` `p5c_resolve_donor` | a `donor_matrix` dict **supplied by the caller** (the rules package reads no `chart_facts`) | `None` ⇒ `{"form":"P5c","state":DISABLED,"reason":P5C_DISABLED_REASON}`; a key missing from a supplied matrix ⇒ `UNRESOLVED` with the operand text | **named / refusal** |

**Readers that do NOT read these rows (checked):** the governed `'5.0'` family — `services/gochara_kernel/*` (inventory, records, windows, verification job), `pipeline/orchestrator/writers/ka_gochara_v5.py`, `gochara_rules` P5 declaration (`ka_gochara_av_polarity_declaration` carries **polarity**, not bindu rows). P5 is held (ST-P5-HOLD-20261001), so no P5 form is evaluated. `services/ka_gochara_resonance/writer.py`: no reference. `services/ka_kshetra` (Suvarṇa-owned): `stage1_symbolization.py:338–350` names the bindu source only as a pointer ("never a fabricated bindu score"); `hazard.py:93` lists an `av_kaksha_gate` signal name — neither reads the category.

**Silent defaults found: none** in Pravāha's readers. **Correction (steward M20261002T121926-da0b; my first wording wrongly spoke of "stored `'4.1'` rows" — none exist yet):** the governed `'4.1'` run happens AFTER step 3, i.e. after Suvarṇa's base-layer rebuild creates these rows, so the `'4.1'` diagnostic will be built **with donor-resolved P5c**, whereas `gochara_v3` with `kakshya_bindu_interim` falls back to the sign-grain interim **only when the rows are absent**. A `'4.1'` run made before the rows exist and one made after are **different candidates and must never be compared as one**. Consequence enforced in the freeze tooling: the **presence and content identity of these rows is a NAMED, typed, frozen input of the Stage-1 freeze** (row count per ayanāṁśa and a digest, read at freeze time; the freeze record states which behaviour the frozen run uses; the live rows are reconciled against it before any window row is read) — see `measurement/STAGE1_FREEZE_PREP_4_1_v1_0.md` v1.5 and PR #2923.

# (2) Does any Kāla/Gochara writer insert into an L1 or L2 PROTECTED table? — **No**
Method: every file under `services/ka_*`, `services/gochara_*`, `services/w2g*`, `pipeline/orchestrator/writers/ka_*`, `pipeline/ka_*` containing `INSERT INTO` / `DELETE FROM` / `UPDATE <table>` (36 files on origin/main) plus Stream A's v5 writer and kernel stores; table names resolved (constants and f-string tables followed). **Protected set checked: `chart_facts`, `chart_dashas`, `chart_divisionals`, `bodha_*`, `mimamsa_*`, `phala_*` — no hit in any write statement.**
| writer | tables written |
|---|---|
| `ka_gochara.py` / `ka_gochara_v3_century_materialize.py` | `kala_gochara_windows_v2` (+ `kala_gochara_windows` promotion), `kala_gochara_v2_build_state` |
| `ka_gochara_v4_41_candidate.py` | writes through `ledger.py` / the window writer: `kala_gochara_windows`, `kala_gochara_contacts`, `kala_gochara_coverage`, `kala_gochara_publication`, `kala_gochara_convention` |
| `ka_gochara_v5.py` + kernel stores (Stream A) | `ka_gochara_sky_convention`, `_physical_object`, `_sky_event`, `_contact`, `_contact_identity`, `_convention_bridge`, `_relationship_record`, `_record_prerequisite`, `_eval_window`, `_eval_window_record`, `_search_input_snapshot`, `_search_inventory`, `_search_obligation`, `_search_interval`, `_search_path_pin`; the verification job: `ka_gochara_eval_window_verification`, `ka_gochara_search_inventory_verification` |
| `ka_gochara_sweep` | `kala_gochara_windows`, `build_substep_progress` |
| `ka_gochara_resonance` | `gochara_resonance_map` |
| `ka_vedha_gochara`, `ka_moorti_nirnaya`, `ka_kota_chakra` | `kala_vedha_gochara`, `kala_moorti_nirnaya`, `kala_kota_chakra` |
| `ka_sangam` | `kala_convergence`, `build_substep_progress` |
| `ka_kshetra` (Suvarṇa) | `kala_field*` family, `kala_insights`, `kala_timeline_spec` |
| `ka_avadhi`, `ka_bhavishya_lekha`, `ka_jivana_parva`, `ka_kala_darshana`, `ka_kalasutra`, `ka_taranga`, `ka_vighnakara`, `ka_yojaka`, `ka_sudarshana_varsha`, `ka_tithi_pravesha` | their own `kala_*` tables |
| `ka_dasha_kala`, `ka_muhurta_seva`, `ka_tulana`, `ka_graha_sancara` | `asset_registry` (service health) only |
So migration 1035's L1/L2 capture triggers have nothing of ours to reject. **Reads** of `chart_facts` / `chart_dashas` are everywhere (the writers consume L1); the verifier and sealer reads are the open owner item of the grants work.
