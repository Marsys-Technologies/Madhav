---
artifact: KALA_SYNERGY_AUDIT
canonical_id: KALA_SYNERGY_AUDIT
version: "1.4"
status: CURRENT
date: 2026-09-24
author: "L3 Kāla strategic session (madhav-fc), at the native's request"
question: "Are the three critical assets — Gochara family, Kṣetra, Saṅgam — synergistically elevated: aligned with the L3 strategy, aware of each other, and speaking one language?"
method: >
  Three parallel reads of the current packets (Kṣetra brief 4.9 / plan 1.13 / sheet 1.8 on main;
  Saṅgam brief 1.5 / plan 1.0 / sheet on sangam/stage3; Gochara plan 2.1 / sheet 2.0, read-only
  from that session's worktree) plus the emitting code, against one rubric: the five synergy
  contracts of the blueprint §3.3 and the Strategy §3 objects. Code-level cross-reads grepped
  independently on origin/main. Every cell cites file:line in the underlying reports.
verdict: "NOT_SYNERGISTIC_TODAY — cross-aware at the ruling level, unbound at the data level (v1.4: second-pass corrections folded in; see §4, §5, §6)"
---

# Are the three critical assets synergistic? — No. Here is the exact shape of the gap.

## 1. Verdict in one paragraph

The three streams have been reconciling **rulings** with each other all week — node frame ruled
once for both, the vedha admission rule made uniform, the AV source locked across Kṣetra S1 and
Saṅgam E2, N-14 answering D-6. That is real cross-awareness and it is worth keeping. But at the
level that matters to the person — the rows each asset emits and the fields a reconciling LLM
would have to line up — **they share no contract.** Three different temporal types, three
different qualification vocabularies with three different names for the same comparability
concept, no key by which any two can name the same window, an independence group emitted by one
and read by none, and a coverage object emitted by one, on one branch, and by neither of the
others. At the code level they share **four edges, every one pointing into the Gochara family, two of them undeclared**: Saṅgam calls five Gochara service methods and reads `kala_vedha_gochara`; Kṣetra reads Gochara's resonance map and its retired sweep corpus. **Kṣetra and Saṅgam share no edge at all**, and Gochara reads nothing from either. (v1.0–1.3 said "one edge" — my grep had gone through `head -10`; corrected at v1.4 by the second-pass verifiers.) And in two places the layer holds
**two producers for one verdict** — vedha and mūrti are computed both by their owning assets and
again inside Kṣetra, and contact episodes are produced both by the Gochara kernel and by Kṣetra's
stage 0. That is the opposite of synergy: the same instant, answered twice, by code that cannot
see it is disagreeing.

## 2. The matrix — five contracts × three assets, as measured

| contract | Gochara family | Saṅgam | Kṣetra |
|---|---|---|---|
| **1 Temporal** — one interval type, declared inclusivity, tz-explicit, no `date.today()` | `t_in / t_exact / t_out` — **three plain `timestamptz` columns** (v1.0 wrongly implied a range type; only the coverage horizons are `tstzrange`); kernel in JD floats; **inclusivity undeclared** — both endpoints are the interval solver's orb-threshold crossing instants, so the kernel's own semantics argue **closed_closed**; own `convention.py`; no `date.today()` | `window_start / window_end / peak_date` **DATE**; inclusivity **split** — daśā `[s,e)` at `engine.py:437`, vedha `s≤p≤e` at `engine.py:672` (v1.0 had the two addresses transposed; corrected by the Saṅgam session), recorded as unresolved; tz offset taken at **run time** not birth instant; `date.today()` horizon with a 29-Feb crash; own | `t_start / t_end / t_peak` **float days since birth**, dates derived naive, **no timezone on any column**; half-open in code, **unstated in packet**; own. **Defect, enlarged by the Kṣetra session and verified live by this session:** the **entire knot set is J2000** — kinematics (`stage0_kinematics.py:47,501-503,659`), primitives (`stage1_symbolization.py:183`), clock boundaries (`stage3_clocks.py:169-186,1050`); nothing re-bases (`stage4_field.py:1288-1345`). The clip to `[0, H]`, the horizon and the decade partitions are **birth-relative** constants (`dhara_sweep.py:75-99`, `stage4_field.py:880-896`, `writer.py:655-665`; migration 492 documents `t_start` as "days since birth"). Birth-relative arithmetic on J2000 knots. **Live, canonical chart:** `kala_field_kinematics` `t_days` −5808.75…30717 with `event_ts` 1984-02-05…2084-02-06 (birth − J2000 = −5809 d → J2000 confirmed); `kala_field` `t_start` 0 … `t_end` 36525, **8,570,075 rows** — on that axis **2000-01-01 → 2100-01-01, not birth → birth+100 y**; earliest `kala_field_windows` `t_start` 5.17 = 2000-01-06 (would be 1984-02-10 if birth-relative). **The native's first sixteen years are absent from the stored field; the last sixteen are extrapolated past the ephemeris; `mi_bhara/living_lel.py:113` reads `t` as days since birth, so any L5 bind would be sixteen years off.** Never served (held substrate), which is why nobody saw it; a W7 rebuild would reproduce it unchanged |
| shared `ka_temporal` resolver | no | no (`UNRESOLVED_USE`) | no (0 hits) |
| **2 Typed qualification** — F04/F06/F12 + comparability, one vocabulary | `epistemic_class`, `completeness_state`, `operator_role`, `claim_grain`, `time_basis`, `comparable_with` **(enum, 4 values)**; but `completeness_state` is free text whose **own column comment promises "six F06 states" (`1081:176`) while it carries two live values — `qualified`, which is not an F06 name, and `unqualified`, which is** (v1.3 said "neither"; wrong) (v1.0's "one ad-hoc value" was a dict key in the λ decomposition, not the column — corrected by the Gochara session); `claim_grain`/`time_basis` are carried by the kernel ledger (`gochara_kernel/ledger.py:176-177,289`) but the only writer found populating them is a WP4 test writing `exact_instant`, which matches neither vocabulary; `source_qualification` **absent from all Gochara code** (prose only; ordered at WP9) | R-6 four-way `activity·valence·applicability·availability` **computed, three of four dropped at INSERT**; `tier_basis` hard-coded; F06 six-state **proposed only**; `comparability_class` **brief says `A_B_contact…`, code emits `ka_sangam/{sig}`** | `precision_regime='day_grade'`; `confidence_tier` two values; F06 `unavailable` on σ_t; comparability **proposed only**; `baseline_is_synthetic` absent from row |
| the comparability concept's **name** | `comparable_with` | `comparability_class` | (none yet) |
| the grain concept's **vocabulary** | `date_grain` / `instant_grain` (prose; column unchecked) | `precision_regime='date_grain'` (inherited in prose, not emitted) | `precision_regime='day_grade'` — **emitted today** (`writer.py:337,979,1134`) |
| **3 Co-reference** — the same window addressable across assets | `contact_id` sha256 + `(chart, generation, contact_id)` PK + manifest id — **good**; `'4.0'` is the tranche-2 candidate, **gated** behind `PRODUCTION_TRANCHE_2_AUTHORIZED=false` by the plan's own sequencing (not missing); **no L2 column** until R8 | `convergence_id` **bigint surrogate, new every rebuild**; R-5 stable identity proposed; only `episode_uuid` landed | `window_id` sha256 — **good**; `field_snapshot_id` dangling; L2 edge ids **bigserial reassigned each rebuild** |
| a key any two assets share | **none** | **none** | **none** |
| **4 Inherited independence** — group emitted, downstream inherits | **emits** `independence_group` column; reads none | scalar `independent_current_count` only; group **proposed**; **zero `ka_*` readers** | **ABSENT** entirely |
| **5 Coverage on every result** | `kala_gochara_coverage` table with invariants — **but `coverage: None` on every non-Moon branch** (`engine.py:1755`) | **ABSENT**; empty result indistinguishable from failure | **ABSENT**; per-covariate `CoverageGap` for two named gaps only |
| determinism | no `date.today()` | `date.today()` + runtime tz | birth-relative, deterministic; J2000 mismatch is a correctness bug not a determinism one |

## 3. Duplicate authority — the same verdict computed twice inside one layer

| verdict | owning producer | second producer | status |
|---|---|---|---|
| house-vedha, laṭṭā, malefic scale | `ka_vedha_gochara` | Kṣetra `build_vedha_primitive` from L0 `bg_transit_rules` | Kṣetra **ruling 4** ratifies single producer; retire after one **cross-check** generation — **not executed** |
| mūrti | `ka_moorti_nirnaya` | Kṣetra `build_moorti_primitive` | same, ruling 4 — **not executed** |
| contact episodes | Gochara kernel (`contact_id`) | Kṣetra `stage0_kinematics.find_contact_episodes` with its own `episode_id` | **unreconciled in any packet**; plan says "Kṣetra consumes no directed contact events" while its stage 0 produces its own |
| node longitude *(a convention split, not a second producer)* | ruled **mean** (M-1/N-4a/ruling 7) | Saṅgam scanner **hard-coded TRUE** (`transit_search.py:10,64,246`); Kṣetra reads mean via `ephemeris_daily` | one longitude, two conventions, across two packets, **after** the ruling; the fix is Gochara's (N-7 kernel) |

## 4. Cross-edges — what actually connects them today (code, `origin/main`; corrected at v1.4)

- **Saṅgam → Gochara family (2 edges).** (a) `KaGocharaService` — **hard-imported** at `writers/ka_sangam.py:36` (the engine types it `Any`) — through **five** methods: `find_aspects`, `find_eclipse_proximity`, `find_ingresses` (×3), `find_stations`, `find_transit_to_transit`; declared as `ka_gochara` in `depends_on`. (b) `SELECT … FROM kala_vedha_gochara` at `writers/ka_sangam.py:1037-1060`, live SQL, **undeclared** (absent from the ten `depends_on` edges).
- **Kṣetra → Gochara family (2 edges).** (a) `gochara_resonance_map` — `ka_gochara_resonance`'s registered `target_table` — at `writer.py:2344, 2363`, declared. (b) `kala_gochara_windows` — `ka_gochara_sweep`'s registered `target_table` — at `stage4_field.py:1384` with the `'v1'` COALESCE at `:1389`, **undeclared**: Kṣetra's `depends_on` lists `ka_gochara_resonance` and not `ka_gochara_sweep`. The same defect the audit flags against Saṅgam.
- **Kṣetra ↔ Saṅgam: no data edge either way.** Saṅgam's windows are Kṣetra's ablation baseline, nothing more.
- **Gochara → anyone: nothing.** (`gochara_v3/context.py:510` reads `kala_moorti_nirnaya` — intra-family.) `ka_sangam/**`, `ka_kshetra/**` are in its `must_not_touch`.
- No cross-imports between the three families; only `gochara_v3 → gochara_grammar`.
- Shared upstream key that could serve as co-reference — refs to Yojaka/L2/snapshot ids: Kṣetra **76** (`services/ka_kshetra/`, nine files), Saṅgam **3** (all in `writers/ka_sangam.py`; `services/ka_sangam/` = 0), Gochara **0** (services and writers). No key any two share.
- **DAG record.** `ka_sangam.depends_on` (seed `:2323`, live registry identical) = ten edges; `ka_vedha_gochara` absent. Latent cross-source cycle: `supabase/migrations/224_…:85` sets `ka_sangam.depends_on = ['ka_kalasutra']` while the seed at `:2294` sets `ka_kalasutra.depends_on ∋ ka_sangam`. Not live (a recursive walk over the active DAG is acyclic); only re-seeding keeps it so.

## 5. Strategy alignment

Objects claimed: Gochara — Contact, Search coverage, Publication handoff (Structural binding
deferred to R8). Saṅgam — Temporal testimony, Engagement route, Search coverage (claimed, **not
emitted**). Kṣetra — Interval/trajectory segment only (Publication handoff de facto, 0 rows).
**No asset emits the Strategy's "Temporal context" object in full** — the one the strategy itself names as the *shared contract for all calculation* (§3 row 2). **Gochara emits the substantial majority of it** through `kala_gochara_convention` (`1081:58-77`: zodiac, ayanāṃśa, sidereal method, node model and source, epoch convention, time scale, house system, ephemeris backend, `.se1` checksums, method version) plus tz-aware instants and precision columns; absent from Gochara are varga convention, location, purpose and a *named* timezone. Saṅgam and Kṣetra emit almost none of it. (v1.3's "adopted by nobody" was unfair to Gochara — corrected at v1.4.) The L3 layer minimum (Layer contract §7) — *"shared
inputs ≠ independent temporal evidence"* — is the exact boundary contracts 4 and 5 enforce, and
neither is enforced.

## 6. What the "shared vocabulary" actually is (corrected at v1.4)

The phrase appears in Saṅgam's and Kṣetra's sheets as an adoption of Gochara plan §5.4, whose
construct is a **shared-consumer contract for three stamp columns on `kala_vedha_gochara` rows** —
`source_qualification`, `corpus_verifiable`, `precision_regime`. Column by column, in code:

- `source_qualification` — **zero hits** on `main`, on `sangam/stage3`, and in the Gochara worktree. Prose only.
- `corpus_verifiable` — **shipped**, but on `kala_gochara_contacts` (`1081:191`; `gochara_kernel/ledger.py:179,203,296`; `engine.py:1897`), not on the producer row the contract names.
- `precision_regime` — **emitted today by Kṣetra** (`writer.py:337`, INSERT lists at `:979`, `:1134`), value `day_grade`.

So v1.3's "exists in none of the three code bases" was **false for two of three**. What holds, and
is the actual defect: **`kala_vedha_gochara` — the one row the contract binds — carries none of the
three.** Two packets adopted a contract on a producer row that has no such columns.

## 7. Disposition

The three assets are individually well-elevated on correctness and are *not* elevated
synergistically. The remedy is not three brief edits. It is one **binding** — a single layer
contract every one of the three adopts by reference and proves by test — plus three short
amendments that each stream folds into its brief §4/§6 under the asset contract. The binding is
`KALA_SYNERGY_BINDING_v1_0.md`. The amendments are in `KALA_SYNERGY_AMENDMENTS_v1_0.md`.
