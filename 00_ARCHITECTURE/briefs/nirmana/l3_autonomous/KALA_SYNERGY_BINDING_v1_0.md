---
artifact: KALA_SYNERGY_BINDING
canonical_id: KALA_SYNERGY_BINDING
version: "1.0"
status: PROPOSED_FOR_ADOPTION_BY_THE_THREE_STREAMS
date: 2026-09-24
author: "L3 Kāla strategic session (madhav-fc), under the native's instruction to elevate the three critical assets synergistically"
binds: [ka_gochara family, ka_sangam, ka_kshetra]
shape: "Layer execution brief contract §5 (demand / offer / interplay) — one row per shared field"
derived_from: "Strategy §3 'Temporal context' and 'Search coverage' objects; blueprint §3.3; KALA_SYNERGY_AUDIT_v1_0.md"
authority_note: >
  Nothing here changes a ruling. It names the fields, vocabularies and keys each stream already
  claims in prose, fixes them to ONE spelling, and makes each a testable offer/demand. Where a
  packet and its code disagree, the binding sides with the ruled plan and names the code gap.
---

# The synergy binding — one language for the three critical assets

**Rule of adoption.** Each stream adds this artifact by reference to its brief §1 and proves each
row it OFFERS or DEMANDS in its brief §6 proof matrix, with a detector that fails when the row is
absent or misspelled. A stream that emits a differently-named field for the same concept is
non-conformant until it renames or aliases with a declared mapping.

## B1 — Temporal (Strategy §3 "Temporal context")

| field | type / vocabulary | Gochara | Saṅgam | Kṣetra |
|---|---|---|---|---|
| `t_start`, `t_end` | **`timestamptz`, UTC**, never a naive date, never a float day-offset as the *served* type | OFFERS (has `t_in/t_out`; alias) | MUST CONVERT (`DATE` → instant at the chart's tz-aware midnight; keep `peak_date` as a derived view) | MUST CONVERT (birth-relative float → instant via the birth instant; **first fix the J2000/birth-relative axis merge**) |
| `t_exact` / `t_peak` | `timestamptz` or NULL, never a sentinel | OFFERS | MUST CONVERT | MUST CONVERT |
| `inclusivity` | enum `{closed_closed, closed_open}` — **declared on every row** | MUST DECLARE (absent) | MUST DECLARE and **unify** (daśā/vedha split) | MUST DECLARE (half-open in code, unstated) |
| `time_basis` | enum `{event_instant, noon_ut_knot, date_grain_midpoint}` | OFFERS | MUST ADD | MUST ADD |
| `claim_grain` | enum `{instant_grain, date_grain, day_grade}` — **`day_grade` is admitted as an alias of `date_grain` for one generation, then retired** | MUST CHECK-CONSTRAIN (free text today) | MUST EMIT (inherited prose only) | MUST RENAME `precision_regime` → `claim_grain`, value `day_grade` → `date_grain` |
| tz source | the **birth instant's** offset, never `datetime.now()`; no `date.today()` anywhere | conformant | MUST FIX (W:897, W:558) | conformant |
| resolver | every stream imports `services/ka_temporal/date_resolver` for date↔instant; no private conversion | MUST ADOPT | MUST ADOPT | MUST ADOPT |

## B2 — Typed qualification (F04 / F06 / F12 + comparability)

| field | vocabulary (closed, CHECK-constrained) | Gochara | Saṅgam | Kṣetra |
|---|---|---|---|---|
| `epistemic_class` (F04) | as the Foundation defines | OFFERS | MUST ADD | MUST ADD |
| `completeness_state` (F06) | **exactly six**: `applied, inapplicable, unavailable, unqualified, contradictory_unresolved, unexplored` | MUST CONSTRAIN (two live values + one ad-hoc) | MUST EMIT (proposed only; today two-valued `computed/honest_empty`) | MUST EMIT (has `unavailable` on σ_t only) |
| `operator_role` (F12) | as the Foundation defines | OFFERS | MUST EMIT (assigned per edge in prose, not on rows) | MUST EMIT |
| **`comparable_with`** | **one name**: `comparable_with`; enum `{self, same_convention_same_inputs, same_convention_newer_inputs, different_convention}` | OFFERS (canonical) | MUST RENAME `comparability_class` → `comparable_with` and emit the enum, not `ka_sangam/{sig}` | MUST ADD |
| `tier_basis` | `{relative_uncalibrated, calibrated:<gate_id>}` | MUST ADD | OFFERS (hard-coded value is fine; the *name* is the contract) | OFFERS |
| `source_qualification` | `{verse_cited, algorithmic_approximation, unsourced}` **on the producer row** | MUST EMIT on `kala_vedha_gochara` (the three stamp columns Gochara §5.4 promised and no code has) | consumes | consumes |
| `corpus_verifiable` | boolean, producer row | MUST EMIT | consumes | consumes |
| R-6 separation | `activity, valence, applicability, availability` — **all four persisted**, never a product | n/a | MUST PERSIST (three of four dropped at INSERT) | MUST ADOPT for windows |

## B3 — Co-reference (the same window, addressable by any asset)

| field | rule | Gochara | Saṅgam | Kṣetra |
|---|---|---|---|---|
| per-asset stable id | **content-addressed sha256 over the natural key + method version**, never a bigint surrogate | OFFERS `contact_id` | MUST LAND R-5 (today `convergence_id` is new every rebuild) | OFFERS `window_id` |
| `generation` | on every row; part of the PK | OFFERS (`'4.0'` unimplemented — land it) | MUST ADD | MUST PUBLISH (`field_snapshot_id` dangling) |
| **`window_ref`** | **the cross-asset handle**: `{asset_id, generation, id}` — the only way one asset cites another's window | MUST ACCEPT as target_ref type | MUST EMIT on every window that cites a contact | MUST EMIT on every segment that cites a resonance target or a sweep window; **remove the `'v1'` fall-through** |
| L2 identity | natural key from Yojaka (DP06 ancestry), never a reassigned bigserial | MUST ADD (no L2 column) | MUST REPLACE `signal_id` FK with generation-bound identity | MUST FIX `_routes.path_edge_ids` |

## B4 — Inherited independence (Layer contract §7: shared inputs ≠ independent evidence)

| field | rule | Gochara | Saṅgam | Kṣetra |
|---|---|---|---|---|
| `independence_group` | jsonb `[{group_id, family, roots[], members[], basis:'declared_lineage'}]` — **basis is always declared, never "demonstrated"** | OFFERS (column exists) | MUST EMIT (proposed); rename `independent_current_count` → `declared_current_count` | MUST INHERIT: every segment carries the union of its witnesses' groups |
| downstream rule | any projection carrying a score carries `independence_group` + `comparable_with` | — | binding on its 7 named readers | binding |

## B5 — Coverage on every result (Strategy §3 "Search coverage")

| field | rule | Gochara | Saṅgam | Kṣetra |
|---|---|---|---|---|
| `coverage` | **on every result, including every empty result**: `{requested_horizon, completed_horizon, resolution, partitions_searched[], exclusions[], unsearched_regions[], completion_detector}` | OFFERS the table; **MUST fix `coverage: None` on non-Moon** | MUST EMIT (absent; empty = failure today); when consuming Gochara events, **join the producer's coverage row by `window_ref`** | MUST EMIT (absent) |
| empty result | a row **and** coverage, never "no row" | conformant when fixed | MUST | MUST |

## B6 — Single producer per verdict

| verdict | sole producer | everyone else | detector |
|---|---|---|---|
| house-vedha, laṭṭā, malefic scale | `ka_vedha_gochara` | consume by `window_ref`; Kṣetra retires `build_vedha_primitive` after one `evaluation` generation (ruling 8) | a test that fails if two writers emit a vedha verdict for one instant |
| mūrti | `ka_moorti_nirnaya` | Kṣetra retires `build_moorti_primitive` (ruling 4) | same |
| contact episodes | Gochara kernel (`contact_id`) | Kṣetra `stage0_kinematics.find_contact_episodes` becomes a **consumer** of `kala_gochara_contacts` or is declared `evaluation`-only with its own `comparable_with = different_convention` | same |
| node longitude | **mean** (M-1 / N-4a / ruling 7) | Saṅgam scanner off `TRUE_NODE`; both streams read one convention | the degree-level anchor (L0 item 6) plus a per-call `retflag`/node-mode assertion |

## B7 — What conformance proves (maps to Layer contract §9)

Tests 5 (duplicate/shared-root), 6 (missingness/wrong generation), 7 (boundary/timezone) and 9
(served-evidence sentinel) are the binding's own tests. Each stream's brief §6 names the fixture,
command and the negative case that makes the detector fire. A green run that could not go red does
not count.
