---
artifact: KALA_SYNERGY_AMENDMENTS
canonical_id: KALA_SYNERGY_AMENDMENTS
version: "1.0"
status: PROPOSED_TO_THE_THREE_STREAMS
date: 2026-09-24
author: "L3 Kāla strategic session (madhav-fc)"
for: "each stream folds its section into its own brief (§4 semantic change, §6 proof matrix) and ruling sheet; nothing here edits a stream's files"
---

# Brief amendments — what each stream adopts from the binding, and the defects it fixes first

## Gochara family — adopt `KALA_SYNERGY_BINDING` §B1–B7; fix

1. **Declare inclusivity** on `[t_in, t_out]` (absent). Pick `closed_open` unless the kernel's bracket semantics say otherwise; say which.
2. **CHECK-constrain `completeness_state`** to the six F06 states; migrate the ad-hoc `removed_by_ruling_N14` to `inapplicable` with the ruling id in a reason column. CHECK-constrain `claim_grain`.
3. **Emit the three stamp columns** you promised the other two streams (`source_qualification`, `corpus_verifiable`, and the grain) on `kala_vedha_gochara` — today none exist and two packets adopted them.
4. **`coverage: None` on the non-Moon branch** (`engine.py:1755`) breaks your own §4.4 guarantee. Every branch returns the coverage row.
5. **`primitives.py:193-194`** still maps Rāhu/Ketu to `[120,180,240]` citing BPHS Ch.26 — the citation F-29 refuted and the aspects N-14 removed. Retire the entry, not just the w30 factor.
6. Accept `window_ref` as a `target_type`; add the L2 identity column at R8 as planned.

## Saṅgam — adopt §B1–B7; fix

1. **Persist all four R-6 components** (`activity, valence, applicability`) — computed at `engine.py:915-946`, dropped at `writer.py:990-999`. The §4.5 inheritance rule is unenforceable until they are columns.
2. **Rename `comparability_class` → `comparable_with`** and emit the binding's enum; today the brief says one vocabulary and the code emits `ka_sangam/{sig}`.
3. **Unify inclusivity** (daśā half-open vs vedha closed) and declare it per row; take the tz offset at the **birth instant**; remove `date.today()` and the 29-Feb crash.
4. **Emit `coverage`** on every window and every empty result; when consuming Gochara events, join the producer's coverage by `window_ref`.
5. **Emit `independence_group`** (proposed) and rename the scalar to `declared_current_count`; then the seven named readers can inherit it — today zero read even the scalar.
6. **Land R-5 identity**: `convergence_id` is a bigint surrogate reissued every rebuild; nothing can cite a Saṅgam window across a rebuild.
7. **Declare the `ka_vedha_gochara` read** (undeclared today) as computational, F12 counterevidence.
8. **Scanner off `TRUE_NODE`** (`transit_search.py:10,64`) — M-1 rules mean; the contract binds and the scanner does not. This is the Gochara stream's N-7 kernel or the bounded amendment; until it lands, stamp `comparable_with = different_convention` against every Kṣetra row.
9. Your brief mandates removing `confidence_score`/`confidence_label`; the writer still emits both. Packet and code must agree before stage-3 close.

## Kṣetra — adopt §B1–B7; fix

1. **The two t-axes.** `stage0_kinematics` emits days-since-J2000; `stage4_field.load_kinematics_breakpoints` merges them into the birth-relative axis with **no offset** (`stage4_field.py:1361-1369` → `writer.py:2049`). This is a correctness defect on every field row that uses kinematic breakpoints, and it is unmentioned in the packet. Fix before anything else in this list.
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
