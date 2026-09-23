---
artifact: KALA_SYNERGY_AUDIT
canonical_id: KALA_SYNERGY_AUDIT
version: "1.0"
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
verdict: NOT_SYNERGISTIC_TODAY — cross-aware at the ruling level, unbound at the data level
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
others. At the code level they share **one edge**: Saṅgam calls Gochara's contact service. Kṣetra
reads nothing from either; Gochara reads nothing from either. And in two places the layer holds
**two producers for one verdict** — vedha and mūrti are computed both by their owning assets and
again inside Kṣetra, and contact episodes are produced both by the Gochara kernel and by Kṣetra's
stage 0. That is the opposite of synergy: the same instant, answered twice, by code that cannot
see it is disagreeing.

## 2. The matrix — five contracts × three assets, as measured

| contract | Gochara family | Saṅgam | Kṣetra |
|---|---|---|---|
| **1 Temporal** — one interval type, declared inclusivity, tz-explicit, no `date.today()` | `t_in / t_exact / t_out` **timestamptz UTC**; kernel in JD floats; **inclusivity ABSENT**; own `convention.py`; no `date.today()` | `window_start / window_end / peak_date` **DATE**; inclusivity **split** — daśā `[s,e)`, vedha `s≤p≤e`, recorded as unresolved; tz offset taken at **run time** not birth instant; `date.today()` horizon with a 29-Feb crash; own | `t_start / t_end / t_peak` **float days since birth**, dates derived naive, **no timezone on any column**; half-open in code, **unstated in packet**; own. **Defect:** `stage0_kinematics` `t_days` is days-since-**J2000**, merged into the birth-relative axis with **no offset** (`stage4_field.py:1361-1369` → `writer.py:2049`) |
| shared `ka_temporal` resolver | no | no (`UNRESOLVED_USE`) | no (0 hits) |
| **2 Typed qualification** — F04/F06/F12 + comparability, one vocabulary | `epistemic_class`, `completeness_state`, `operator_role`, `claim_grain`, `time_basis`, `comparable_with` **(enum, 4 values)**; but `completeness_state` free text with **two** live values + one ad-hoc; `source_qualification` **absent from all Gochara code** (prose only) | R-6 four-way `activity·valence·applicability·availability` **computed, three of four dropped at INSERT**; `tier_basis` hard-coded; F06 six-state **proposed only**; `comparability_class` **brief says `A_B_contact…`, code emits `ka_sangam/{sig}`** | `precision_regime='day_grade'`; `confidence_tier` two values; F06 `unavailable` on σ_t; comparability **proposed only**; `baseline_is_synthetic` absent from row |
| the comparability concept's **name** | `comparable_with` | `comparability_class` | (none yet) |
| the grain concept's **vocabulary** | `date_grain` / `instant_grain` (prose; column unchecked) | `precision_regime='date_grain'` (inherited, not emitted) | `precision_regime='day_grade'` |
| **3 Co-reference** — the same window addressable across assets | `contact_id` sha256 + `(chart, generation, contact_id)` PK + manifest id — **good**; `'4.0'` unimplemented; **no L2 column** | `convergence_id` **bigint surrogate, new every rebuild**; R-5 stable identity proposed; only `episode_uuid` landed | `window_id` sha256 — **good**; `field_snapshot_id` dangling; L2 edge ids **bigserial reassigned each rebuild** |
| a key any two assets share | **none** | **none** | **none** |
| **4 Inherited independence** — group emitted, downstream inherits | **emits** `independence_group` column; reads none | scalar `independent_current_count` only; group **proposed**; **zero `ka_*` readers** | **ABSENT** entirely |
| **5 Coverage on every result** | `kala_gochara_coverage` table with invariants — **but `coverage: None` on every non-Moon branch** (`engine.py:1755`) | **ABSENT**; empty result indistinguishable from failure | **ABSENT**; per-covariate `CoverageGap` for two named gaps only |
| determinism | no `date.today()` | `date.today()` + runtime tz | birth-relative, deterministic; J2000 mismatch is a correctness bug not a determinism one |

## 3. Duplicate authority — the same verdict computed twice inside one layer

| verdict | owning producer | second producer | status |
|---|---|---|---|
| house-vedha | `ka_vedha_gochara` | Kṣetra `build_vedha_primitive` from L0 `bg_transit_rules` | Kṣetra ruling 8 ratifies single producer; retire after one cross-check generation — **not executed** |
| mūrti | `ka_moorti_nirnaya` | Kṣetra `build_moorti_primitive` | same, ruling 4 — **not executed** |
| contact episodes | Gochara kernel (`contact_id`) | Kṣetra `stage0_kinematics.find_contact_episodes` with its own `episode_id` | **unreconciled in any packet**; plan says "Kṣetra consumes no directed contact events" while its stage 0 produces its own |
| node longitude | ruled **mean** (M-1/N-4a/ruling 7) | Saṅgam scanner **hard-coded TRUE** (`transit_search.py:10,64`); Kṣetra reads mean via `ephemeris_daily` | one longitude, two conventions, across two packets, **after** the ruling |

## 4. Cross-edges — what actually connects them today (code, `origin/main`)

- Saṅgam → Gochara: `gochara_service.find_aspects` (duck-typed, in-process), the **only** live edge. Saṅgam also reads `ka_vedha_gochara` **undeclared**.
- Kṣetra → Gochara: reads `gochara_resonance_map` (declared) and the retired sweep as evaluation corpus with a **`'v1'` COALESCE fall-through at two sites**.
- Kṣetra ↔ Saṅgam: **no data edge either way.** Saṅgam's windows are Kṣetra's ablation baseline, nothing more.
- Gochara → anyone: reads nothing; `ka_sangam/**`, `ka_kshetra/**` in its `must_not_touch`.
- Shared upstream key that could serve as co-reference: Kṣetra 76 refs to Yojaka/L2/snapshot ids, Saṅgam 3, Gochara **0**.

## 5. Strategy alignment

Objects claimed: Gochara — Contact, Search coverage, Publication handoff (Structural binding
deferred to R8). Saṅgam — Temporal testimony, Engagement route, Search coverage (claimed, **not
emitted**). Kṣetra — Interval/trajectory segment only (Publication handoff de facto, 0 rows).
**No asset emits the Strategy's "Temporal context" object** — the one the strategy itself names as
the *shared contract for all calculation* (§3 row 2: subject, instant/interval, calendar, tz,
ayanāṃśa/frame/node/house conventions, input precision, method versions). That row is the temporal
contract, already defined, adopted by nobody. The L3 layer minimum (Layer contract §7) — *"shared
inputs ≠ independent temporal evidence"* — is the exact boundary contracts 4 and 5 enforce, and
neither is enforced.

## 6. What the "shared vocabulary" actually is

The phrase "shared vocabulary across the three packets" appears in Saṅgam's and Kṣetra's sheets as
an adoption of Gochara plan §5.4. In the Gochara plan the construct is a **"shared-consumer
contract (three readers: century, Saṅgam, Kṣetra)"** for three stamp columns on
`kala_vedha_gochara` rows — `source_qualification`, `corpus_verifiable`, `precision_regime`. It is
real, it is narrow (one producer's rows), and **it exists in none of the three code bases** —
Gochara's own sheet records the table has none of the three columns. Two packets adopted a
vocabulary that a third packet describes and no code emits. That is the mechanism of every failure
this week, at the layer level.

## 7. Disposition

The three assets are individually well-elevated on correctness and are *not* elevated
synergistically. The remedy is not three brief edits. It is one **binding** — a single layer
contract every one of the three adopts by reference and proves by test — plus three short
amendments that each stream folds into its brief §4/§6 under the asset contract. The binding is
`KALA_SYNERGY_BINDING_v1_0.md`. The amendments are in `KALA_SYNERGY_AMENDMENTS_v1_0.md`.
