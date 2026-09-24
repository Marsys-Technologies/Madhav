---
artifact: KALA_SYNERGY_BINDING
canonical_id: KALA_SYNERGY_BINDING
version: "2.3"
status: PROPOSED_FOR_NATIVE_RULING_THEN_ADOPTION
date: 2026-09-24
author: "L3 Kāla strategic session (madhav-fc)"
binds: [ka_gochara family, ka_sangam, ka_kshetra]
shape: "Layer execution brief contract §5 (demand / offer / interplay), per shared field, with Grain · Use · Failure · Proof stated per section and an interplay map in §B9"
posture: >
  v2.0 replaces v1.1 after an independent governance check found v1.1's own claim "nothing here
  changes a ruling" to be false in seven places and its MUSTs to reach into L0, L2 and Pūrṇa.
  v2.0 IMPOSES only on the three streams' own L3 tables and code; it DEMANDS of other layers through
  named interface packets; it RENAMES no column that a ruling names; it lists every new decision in
  §B8 for the native rather than embedding it as a requirement; and each stream's kernel semantics
  are recorded as findings, not dictated.
verdict_tier: "Conformance proves COMPUTATIONAL_CORRECTNESS only (Layer contract §9). It proves no explanatory value and no empirical performance."
---

# The synergy binding — one language for the three critical assets (v2.0)

**Rule of adoption.** Each stream cites this artifact in its brief §1 and proves each row it OFFERS
or MUST in its brief §6 with a detector that fails when the row is absent, misspelled or
mis-valued. A stream that emits a differently-named field for a concept below is non-conformant
until it aliases with a declared mapping. Rows marked DEMAND are addressed to another layer through
the named packet and bind nothing until that layer accepts. Rows marked DECISION are the native's
(§B8) and bind nothing until ruled.

## B1 — Temporal (Strategy §3 "Temporal context")

| field | rule | Gochara | Saṅgam | Kṣetra |
|---|---|---|---|---|
| `t_start`, `t_end` | served type **`timestamptz` UTC**; never a naive date or a float day-offset as the *served* value | OFFERS (`t_in`/`t_out`, alias) | MUST CONVERT `DATE` → instant at the chart's tz-aware midnight; `peak_date` stays as a derived view | MUST CONVERT birth-relative float → instant via the birth instant, **after** the J2000/birth-axis defect is fixed (amendments Kṣetra 1) |
| `t_exact` / `t_peak` | `timestamptz` or NULL, never a sentinel | OFFERS | MUST CONVERT | MUST CONVERT |
| `inclusivity` | enum `{closed_closed, closed_open}`, **declared on every row by the asset, stating its own kernel's semantics** — the binding records findings and dictates none | finding: orb-crossing endpoints → `closed_closed`; MUST DECLARE | finding: split (daśā `[s,e)` at `engine.py:437`, vedha closed at `:672`); MUST UNIFY and DECLARE | finding: `closed_open` in code, unstated; MUST DECLARE |
| `time_basis` | enum `{event_instant, noon_ut_knot, date_grain_midpoint}` | OFFERS (column exists; no production caller populates it — D-S4) | MUST ADD | MUST ADD |
| **`precision_regime`** — the ruled name (Kṣetra ruling 8, Gochara G-9, Saṅgam M-3 all name it) | **no rename.** Values unified to enum `{instant_grain, date_grain}`; `day_grade` aliased to `date_grain` until the successor condition of Saṅgam D-7 is met (every dependent claim has an authorized successor), **not for a count of generations**. Gochara's contacts table names the same concept `claim_grain`; **Gochara's D-S4 now recommends renaming it to the ruled `precision_regime`** in 1081, the ledger, the kernel dataclasses and tests before the migration is ever applied (it exists only in disposable DBs), so no alias generation is needed — still the native's, B8-9 | D-S4 → rename recommended | MUST EMIT (inherited in prose only today) | OFFERS the column; MUST re-value `day_grade` → `date_grain` |
| tz source | the **birth instant's** offset, never `datetime.now()`; no `date.today()` | conformant | MUST FIX (`writer.py:897`, `:558-559`) | conformant |
| resolver | every stream converts date↔instant through `services/ka_temporal/date_resolver`; no private conversion | MUST ADOPT | MUST ADOPT | MUST ADOPT |

*Grain:* per row, subject = chart, instant/interval as above. *Use:* the receiving finding is any
cross-asset alignment of two windows (Saṅgam ↔ Kṣetra ↔ Gochara) — none exists today; the first
one is the proof. *Failure:* a row without `inclusivity` or with a naive instant is rejected at
write. *Proof:* Layer test 7 (boundary/timezone) with a fixture at a DST edge and at a chart
whose birth tz differs from the run tz.

## B2 — Typed qualification (F04 / F06 / F12 + comparability)

| field | vocabulary (closed, CHECK-constrained) | Gochara | Saṅgam | Kṣetra |
|---|---|---|---|---|
| `epistemic_class` (F04) | as the Foundation defines | OFFERS | MUST ADD | MUST ADD |
| `completeness_state` (F06) | **exactly six**: `applied, inapplicable, unavailable, unqualified, contradictory_unresolved, unexplored` | MUST CONSTRAIN — column comment (`1081:176`) promises six; live values are `qualified` (not an F06 name) and `unqualified` (is one) | MUST EMIT (proposed; today `computed`/`honest_empty`) | MUST EMIT |
| `operator_role` (F12) | as the Foundation defines | OFFERS | MUST EMIT | MUST EMIT |
| **`comparable_with`** | **a RELATION** between this row and a reference row's conventions and inputs. Values pinned by Gochara at WP1 (N-7); enum `{self, same_convention_same_inputs, same_convention_newer_inputs, different_convention}` — **stays at four** (D-S6): never a property of one row (an unstable key is `NOT_RUN`-with-reason on the comparison record, F06 `unqualified` on the row, or an additive `id_basis` on the asset's own table) | OFFERS | MUST ADD (**implemented, pending merge**) | MUST ADD |
| **`comparability_class`** | **a PARTITION KEY**, not a relation — *v2.0–2.2 wrongly ordered this renamed to `comparable_with`; corrected by Saṅgam.* Saṅgam's `ka_sangam/<signature_class>` says what a projection may **rank within**: every top-N partitions by it, cross-class pairs are `incomparable` and never ranked (Saṅgam brief :183, :225, :266; `exposure.py:65`). Both fields coexist | n/a (contacts are one class) | OFFERS; keep the current value form | MUST ADD, or declare a single class, before any ranking over Kṣetra windows |
| `tier_basis` | `{relative_uncalibrated, calibrated:<gate_id>}` | MUST ADD | OFFERS | PROMISED (brief 333-334); MUST EMIT |
| `source_qualification` · `corpus_verifiable` · `precision_regime` on the **producer row** (`kala_vedha_gochara`) | the three stamps Gochara §5.4 promised; **none exist on that table today** (`corpus_verifiable` exists on `kala_gochara_contacts`; `precision_regime` is emitted by Kṣetra) | MUST EMIT (L3's own table, WP9) | consumes | consumes |
| R-6 separation `activity, valence, applicability, availability` | all four **persisted**, never a product | n/a | MUST PERSIST (M-7; three of four dropped at `writer.py:990-999`) | DECISION B8-7 — not ruled for Kṣetra |

*Grain:* per row. *Use:* the reconciling reader weighs rows only within `comparable_with` classes
and only at `completeness_state = applied`. *Failure:* a value outside the enum is rejected at
write; an F06 state absent is `unexplored`, never NULL. *Proof:* Layer test 1 (qualification/source
scope) and test 4 (order/presentation control).

## B3 — Co-reference

| field | rule | Gochara | Saṅgam | Kṣetra |
|---|---|---|---|---|
| per-asset stable id | content-addressed sha256 over the natural key + method version, never a bigint surrogate (**DECISION B8-1** to ratify the pattern) | OFFERS `contact_id` | MUST LAND R-5 (`convergence_id` reissued every rebuild) | OFFERS `window_id` |
| `generation` | on every row; PK membership is **DECISION B8-2** | OFFERS (`'4.0'` is the tranche-2 candidate, gated) | MUST ADD | MUST PUBLISH (`field_snapshot_id` dangling) |
| **`window_ref`** | the cross-asset handle `{asset_id, generation, id}`, resolving against the cited asset's **existing PK**; **not** a `target_type`; a producer never targets a consumer's window (Gochara R2). Ratifying it as *the* handle is **DECISION B8-3** | n/a as producer | MUST EMIT on every window that cites a contact | MUST EMIT on every segment that cites a resonance target or a sweep window; remove the `'v1'` fall-through |
| L2 identity | natural key from Yojaka (DP06) | **DEMAND on L2 via L3-U01**; lands at R8 as planned | DEMAND: replace `signal_id` FK with generation-bound identity | DEMAND: `_routes.path_edge_ids` |

*Failure:* an unresolvable `window_ref` sets `completeness_state = unavailable` and appears in the
citing row's `coverage.exclusions`; it never silently drops. *Proof:* Layer test 10
(revision/replay/rollback): the same `window_ref` resolves identically after a rebuild of the cited
asset at the same generation and fails loudly at a different one.

## B4 — Inherited independence (Layer contract §7: shared inputs ≠ independent evidence)

| field | rule | Gochara | Saṅgam | Kṣetra |
|---|---|---|---|---|
| `independence_group` | jsonb `[{group_id, family, roots[], members[], basis}]`; `basis` is always `declared_lineage`, never "demonstrated" (**shape is DECISION B8-4**) | OFFERS (column) | MUST EMIT; rename `independent_current_count` → `declared_current_count` | MUST INHERIT the union of its witnesses' groups |
| downstream rule | any projection carrying a score carries `independence_group` + `comparable_with`, and **partitions by `comparability_class`** | — | binding on its seven named readers | binding |

*Proof:* Layer test 5 (duplicate/shared-root) and test 8 (omission challenge: dropping a witness's
group must change the union, never pass silently).

## B5 — Coverage on every result (Strategy §3 "Search coverage")

| field | rule | Gochara | Saṅgam | Kṣetra |
|---|---|---|---|---|
| `coverage` | on every result **including every empty result**; proposed shape `{requested_horizon, completed_horizon, resolution, partitions_searched[], exclusions[], unsearched_regions[], completion_detector}` — beyond A-1's "requested horizon", the full shape is **DECISION B8-5** | OFFERS the table; MUST fix `coverage: None` on non-Moon (`engine.py:1755`) | MUST EMIT; when consuming Gochara events, join the producer's coverage by `window_ref` | MUST EMIT |
| empty result | a row **and** coverage, never "no row" | — | MUST | MUST |

*Proof:* Layer test 6 (missingness) and test 8 (omission): an unsearched partition must appear in
`unsearched_regions`, and its absence must fail.

## B6 — Single producer per verdict

| verdict | sole producer | everyone else | detector | status |
|---|---|---|---|---|
| house-vedha, laṭṭā, malefic scale | `ka_vedha_gochara` | consume by `window_ref`; Kṣetra retires `build_vedha_primitive` **after one cross-check generation (ruling 4)** and once every dependent claim has a successor | a test that fails if two writers emit a vedha verdict for one instant | ruled |
| mūrti | `ka_moorti_nirnaya` | Kṣetra retires `build_moorti_primitive` (ruling 4) | same | ruled |
| contact episodes | Gochara kernel (`contact_id`) | Kṣetra `find_contact_episodes` becomes a consumer, or is declared `evaluation`-only with `comparable_with = different_convention` | same | **DECISION B8-6 — no ruling covers this** |
| node longitude | **mean** (M-1 / N-4a / ruling 7) — a convention split, not a second producer | **Gochara owns the fix** — vehicle is packet S-1/S-2: `services/ka_gochara/service.py` returns kernel episodes (mean node, N-4) through a new `find_episodes`, and Saṅgam stops bypassing the service. **`pipeline/transit_search.py` stays `must_not_touch` for every stream**; "kernel path" never means editing that file. Saṅgam consumes; interim: every Saṅgam row stamps `comparable_with = different_convention` against Kṣetra | **L0's degree-level anchor — already applied (L0 item 6)** — plus a per-call node-mode assertion inside each L3 reader | ruled; fix in flight |

## B7 — What conformance proves

Required: Layer contract §9 tests **1, 5, 6, 7, 8, 9, 10**, each with a negative fixture that makes
the detector fire. Scheduled, not gated: test **12** (simpler baseline) once `KALA_BASELINE_v1_0.md`
exists (D-J). Out of scope: test 11 (serving is Pūrṇa's). **Verdict tier: `COMPUTATIONAL_CORRECTNESS`
only.** Nothing here proves a better reading or an outcome.

## B8 — Decisions this binding needs from the native (not requirements)

1. Ratify content-addressed sha256 ids as the per-asset identity pattern (B3).
2. `generation` as a PK member on every L3 row (B3).
3. `window_ref` `{asset_id, generation, id}` as the only cross-asset handle (B3; Gochara's form).
4. The `independence_group` jsonb shape and `declared_current_count` (B4).
5. The seven-field `coverage` shape (B5).
6. **Contact episodes: one producer** — Gochara kernel, with Kṣetra as consumer or evaluation-only (B6).
7. R-6 four-way separation extended to Kṣetra windows (B2).
8. The `time_basis` and `tier_basis` vocabularies (B1/B2).
9. Whether Gochara's `claim_grain` aliases to the ruled `precision_regime` or the reverse (Gochara D-S4).
10. Kṣetra's re-rank of the t-axis defect ahead of ruling 9's G3 (Kṣetra's own delegated call; record it).

## B9 — Interplay map (who does what to each shared field)

| field | defines | computes | enriches | projects/serves | records | evaluates |
|---|---|---|---|---|---|---|
| temporal (B1) | `ka_temporal` resolver | each producer | — | Pūrṇa (interface packet) | producer row | test 7 |
| qualification (B2) | Foundation F04/F06/F12; WP1 for `comparable_with` | each producer | `ka_vedha_gochara` stamps | Pūrṇa | producer row | test 1 |
| co-reference (B3) | this binding + B8-1..3 | each producer | — | any citing asset | producer PK | test 10 |
| independence (B4) | Saṅgam (group) | Saṅgam, Gochara | Kṣetra (union) | Pūrṇa | producer row | tests 5, 8 |
| coverage (B5) | this binding + B8-5 | each search asset | consumer joins by `window_ref` | Pūrṇa | producer row | tests 6, 8 |
| single producer (B6) | rulings 4, 7, 8; B8-6 | the named producer | — | — | — | the B6 detector |
