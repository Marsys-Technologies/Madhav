---
artifact: KALA_SYNERGY_AMENDMENTS
canonical_id: KALA_SYNERGY_AMENDMENTS
version: "1.3"
status: PROPOSED_TO_THE_THREE_STREAMS
date: 2026-09-24
author: "L3 Kāla strategic session (madhav-fc)"
for: "each stream folds its section into its own brief (§4 semantic change, §6 proof matrix) and ruling sheet; nothing here edits a stream's files"
---

# Brief amendments — what each stream adopts from the binding, and the defects it fixes first

## Gochara family — adopt `KALA_SYNERGY_BINDING` §B1–B7; fix

1. **Declare inclusivity** on `[t_in, t_out]` (undeclared). The three columns are plain `timestamptz`, not a range; both endpoints are orb-threshold crossing instants, so the kernel's semantics say **`closed_closed`** — declare that, not `closed_open` (v1.0's default was wrong).
2. **CHECK-constrain `completeness_state`** to the six F06 states — the column's own comment (`1081:176`) promises six and neither live value (`qualified`/`unqualified`) is one. (`removed_by_ruling_N14` is a λ-decomposition dict key, not a column value — v1.0 was wrong.) CHECK-constrain `claim_grain` and `time_basis`; the kernel ledger carries both (`ledger.py:176-177,289`) but no production caller populates them with a vocabulary value — the one writer found is a WP4 test writing `exact_instant`, which matches neither vocabulary (your D-S4).
3. **Emit the three stamp columns** you promised the other two streams (`source_qualification`, `corpus_verifiable`, and the grain) on `kala_vedha_gochara` — today none exist and two packets adopted them.
4. **`coverage: None` on the non-Moon branch** (`engine.py:1755`) breaks your own §4.4 guarantee. Every branch returns the coverage row.
5. `services/gochara_grammar/primitives.py:193-194` still maps Rāhu/Ketu to `[120,180,240]` citing BPHS Ch.26. **Correction:** `nodal_drishti='removed'` already drops the w30 factor AND filters every Rāhu/Ketu `drishti_contact` row (`engine.py:1677-1690`); the entry survives only so the A-3 delta report can reproduce the legacy arm, and retires when `'4.0'` is accepted. Mark its BPHS Ch.26 comment refuted now.
6. `'4.0'` is the tranche-2 candidate, gated behind `PRODUCTION_TRANCHE_2_AUTHORIZED=false` by your own sequencing — say gated, not missing. `inapplicable` is excluded from `target_resolution_state` by ruling N-12, not by oversight. No L2 identity column until R8, as planned.
7. `window_ref` is **not** a new `target_type` (that would let a contact target a consumer's window and break R2). Consumers cite your contacts as `{asset_id:'ka_gochara', generation, id: contact_id}` against your existing PK — your form, adopted into binding B3, no schema change on your side. Saṅgam and Kṣetra then cite rather than re-derive; Kṣetra's `find_contact_episodes` is Kṣetra's to reconcile.

## Saṅgam — adopt §B1–B7; fix

1. **Persist all four R-6 components** (`activity, valence, applicability`) — computed at `engine.py:915-946`, dropped at `writer.py:990-999`. The §4.5 inheritance rule is unenforceable until they are columns.
2. **Rename `comparability_class` → `comparable_with`** and emit the binding's enum; today the brief says one vocabulary and the code emits `ka_sangam/{sig}`.
3. **Unify inclusivity** (daśā half-open at `engine.py:437`, vedha closed at `:672`) and declare it per row; take the tz offset at the **birth instant**; remove `date.today()` and the 29-Feb crash.
4. **Emit `coverage`** on every window and every empty result; when consuming Gochara events, join the producer's coverage by `window_ref`.
5. **Emit `independence_group`** (proposed) and rename the scalar to `declared_current_count`; then the seven named readers can inherit it — today zero read even the scalar.
6. **Land R-5 identity**: `convergence_id` is a bigint surrogate reissued every rebuild; nothing can cite a Saṅgam window across a rebuild.
7. **Declare the `ka_vedha_gochara` read** (undeclared today — confirmed live: it is absent from `ka_sangam`'s ten `depends_on` edges) as computational, F12 counterevidence. While there, resolve the two-source conflict: migration 224 still carries a single-edge `['ka_kalasutra']` version of your upstream that would be a cycle if it ever won.
8. **Scanner off `TRUE_NODE`** (`transit_search.py:10,64`) — M-1 rules mean; the contract binds and the scanner does not. This is the Gochara stream's N-7 kernel or the bounded amendment; until it lands, stamp `comparable_with = different_convention` against every Kṣetra row.
9. Your brief mandates removing `confidence_score`/`confidence_label`; the writer still emits both. Blast radius (measured by the Saṅgam session): `ka_bhavishya_lekha.py`, `ka_kala_darshana.py`, `ka_tulana/writer.py`, `ka_tulana/ranker.py`, `platform/src/lib/retrieval/registry/layers/register_d7_channel.ts`, plus the capability census — five readers and a serving layer, so removal is a coordinated change behind the §6.2 sentinel, not a writer edit. Packet and code must agree before the merge gate.

## Kṣetra — adopt §B1–B7; fix

1. **The t-axis — rank 0, ahead of G3.** *(Corrected by the Kṣetra session, verified live by the strategic session.)* The **entire knot set is J2000** — kinematics, primitives, clock boundaries — and the clip/horizon/decade constants are **birth-relative**; nothing converts. The kinematics roots are excluded from the segment knot set by design (`dhara_sweep.py:66`), so the roots are not the mechanism — **the clip is**. Live: `kala_field` spans `t` 0…36525 on the J2000 axis = **2000-01-01 → 2100-01-01**, 8.57 M rows; kinematics span 1984-02-05 → 2084-02-06. **The native's first sixteen years are missing from the field and the last sixteen are extrapolated.** Detector that fails on current data: `min(t_start)` must equal the birth instant and `max(t_end)` birth + 36525 on ONE declared convention. This is Phase 1 item zero of the stage-3 prompt and the plan's new rank-0.
2. **Serve instants, not float day-offsets**: convert through the birth instant with the tz-aware resolver; declare `inclusivity=closed_open`, which the code already does and the packet never says.
3. **Rename `precision_regime` → `claim_grain`**, `day_grade` → `date_grain` (alias one generation).
4. **Stop being a second producer**: retire `build_vedha_primitive` and `build_moorti_primitive` per rulings 8 and 4 (ratified, not executed); reconcile `find_contact_episodes` with the Gochara kernel — consume `kala_gochara_contacts` by `window_ref`, or declare your episodes `evaluation`-only with `comparable_with = different_convention`.
5. **Emit `coverage`** on every result (absent), and **inherit `independence_group`** from every witness (absent).
6. **Remove the `'v1'` COALESCE fall-through** at `writer.py:2330-2347` and `stage4_field.py:1386-1389`; cite the sweep corpus by `window_ref`.
7. Fix `_routes.path_edge_ids` (bigserial reassigned each rebuild) with the L2 natural key via L3-U01; publish `field_snapshot_id`; add `baseline_is_synthetic` to the row.

## Shared, all three

- Every claim in these amendments that names a file:line was read by a session that is not the
  stream's own. Verify at source before adopting; correct the audit where it is wrong.
- Conformance is proved in each brief's §6 with Layer tests 5, 6, 7 and 9, each with a negative
  fixture that makes the detector fire.
