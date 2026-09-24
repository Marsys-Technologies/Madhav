---
artifact: KALA_SYNERGY_AMENDMENTS
canonical_id: KALA_SYNERGY_AMENDMENTS
version: "2.2"
status: PROPOSED_TO_THE_THREE_STREAMS
date: 2026-09-24
author: "L3 Kāla strategic session (madhav-fc)"
for: "each stream folds its section into its own brief (§4 semantic change, §6 proof matrix) and ruling sheet; nothing here edits, or orders an edit to, another stream's or another layer's files"
posture: >
  v2.0 removes every instruction v1.3 gave a stream about a file it does not own (transit_search.py,
  migration 224, a Pūrṇa serving file, L2 keys) and restates them as interface demands or flags. It
  removes the precision_regime rename (a ruled column name). It restores ruled retirement
  conditions. Every file:line was read by a session that is not the stream's own; verify at source
  before adopting and correct the audit where wrong.
---

# Brief amendments — what each stream adopts from the binding v2.0, and the defects it fixes first

## Gochara family

1. **Declare inclusivity** on `[t_in, t_out]`. Three plain `timestamptz` columns, orb-threshold crossing endpoints → your kernel's semantics are `closed_closed`; declare that on every row (B1 records it as a finding, does not dictate it).
2. **CHECK-constrain `completeness_state`** to the six F06 states. The column comment (`1081:176`) promises six; live values are `qualified` (not an F06 name) and `unqualified` (is one). CHECK-constrain `time_basis` and the grain column too; the kernel ledger carries both (`ledger.py:176-177,289`) but no production caller populates them — your D-S4, which also decides whether `claim_grain` aliases to the ruled `precision_regime` or the reverse.
3. **Emit the three stamp columns on `kala_vedha_gochara`** — `source_qualification`, `corpus_verifiable`, `precision_regime` — the shared-consumer contract of your §5.4 that Kṣetra and Saṅgam adopted. Today that table has none of them (`corpus_verifiable` exists on `kala_gochara_contacts`, not there). WP9 as you ordered it.
4. **`coverage: None` on the non-Moon branch** (`engine.py:1755`) breaks your §4.4 guarantee. Every branch returns the coverage row.
5. `services/gochara_grammar/primitives.py:193-194` still maps Rāhu/Ketu to `[120,180,240]` citing BPHS Ch.26. `nodal_drishti='removed'` already drops w30 and filters every node `drishti_contact` row (`engine.py:1677-1690`); the entry survives for the A-3 legacy arm and retires at `'4.0'` acceptance, per your sequencing. Mark the Ch.26 comment refuted when you next touch the file.
6. `'4.0'` is gated behind `PRODUCTION_TRANCHE_2_AUTHORIZED=false` by your own sequencing — gated, not missing. `inapplicable` is excluded from `target_resolution_state` by N-12. L2 identity lands at R8 as planned; the binding demands it of L2 via L3-U01, not of you.
7. `window_ref` is **not** a `target_type` (your R2 argument, adopted). Consumers cite `{asset_id:'ka_gochara', generation, id: contact_id}` against your PK. No change on your side beyond documenting it.
8. **You own the node fix** (N-7 kernel path). Saṅgam may not edit `transit_search.py`; until your kernel lands, Saṅgam stamps `comparable_with = different_convention` against Kṣetra rows. L0's degree-level anchor is already applied; add a per-call node-mode assertion in your own readers.
9. **Binding rows not itemized above that you still carry:** `tier_basis` MUST ADD (B2).

## Saṅgam

1. **Persist all four R-6 components** — **code-complete on `sangam/stage3` pending merge**: `activity`, `valence`, `applicability` are now in the INSERT (`writer.py:1132`, migration 1088) alongside `availability`. The finding closes on merge.
2. ~~Rename `comparability_class` → `comparable_with`~~ **Withdrawn — v2.0/2.1 were wrong, and you caught it.** `comparability_class` is your partition key (rank-within); `comparable_with` is a relation to a reference row. Keep both; you have implemented both (`writer.py:1132-1135`). The brief's `A_B_contact · C_residence · D_ingress` vocabulary versus the code's `ka_sangam/{sig}` is still a packet-vs-code mismatch on the *partition key's* values, and is yours to reconcile — but it is not the rename.
3. **Unify inclusivity** (daśā half-open at `engine.py:437`, vedha closed at `:672`) and declare it per row; take the tz offset at the **birth instant** (`writer.py:897`); remove `date.today()` and the 29-Feb crash (`:558-559`).
4. **Emit `coverage`** on every window and every empty result; when consuming Gochara events under N-7, join the producer's coverage by `window_ref`, and **emit `window_ref`** `{asset_id:'ka_gochara', generation, id}` on every window that cites a contact.
5. **Emit `independence_group`** (proposed) and rename the scalar to `declared_current_count`; then your seven named readers can inherit it — today zero read even the scalar.
6. **Land R-5 identity**: `convergence_id` is a bigint surrogate reissued every rebuild; nothing can cite a Saṅgam window across a rebuild.
7. **Declare the `ka_vedha_gochara` read** (`writer.py:1037-1060`, live SQL, absent from your ten `depends_on` edges) as computational, F12 counterevidence. *Flag, do not fix:* migration 224 still carries a single-edge `['ka_kalasutra']` version of your upstream that would be a cycle with the seed's `ka_kalasutra → ka_sangam`; not live; a registry-owner item.
8. **The `TRUE_NODE` scanner is Gochara's to fix** (N-7 kernel); `transit_search.py` is frozen against your edits (S-I). Until it lands, stamp `comparable_with = different_convention` against every Kṣetra row.
9. Your brief mandates removing `confidence_score`/`confidence_label`; the writer still emits both (`:944-946`). Five `ka_*` readers plus `register_d7_channel.ts` consume them — the serving file is **Pūrṇa's**, so the removal is an **interface packet** plus a coordinated L3 change behind your §6.2 sentinel, not a writer edit.
10. **Binding rows not itemized above that you still carry:** `t_start`/`t_end`/`t_exact` conversion to `timestamptz` (B1); `time_basis` and `precision_regime` MUST EMIT (B1); `epistemic_class`, `operator_role`, six-state `completeness_state` (B2); `generation` on every row (B3); the resolver (B1).

## Kṣetra

1. **The t-axis — your rank 0.** The entire knot set is J2000 (kinematics, primitives, clock boundaries); the clip/horizon/decade constants are birth-relative; nothing converts; the clip is the mechanism. Live: `kala_field` spans 2000-01-01 → 2100-01-01, 8.57 M rows, not birth → birth+100 y. Your detector (`min(t_start)` = birth, `max(t_end)` = birth+36525, one declared convention) is right. *You placed this ahead of ruling 9's G3 under your own delegation; record that re-rank on your sheet (B8-10).*
2. **Serve instants, not float day-offsets**: convert through the birth instant with the shared resolver; declare `inclusivity = closed_open`, which your code already does and the packet never says.
3. **Re-value `precision_regime`** `day_grade` → `date_grain` (alias until every dependent claim has a successor). No rename — the column name is ruled.
4. **Stop being a second producer**: retire `build_vedha_primitive` and `build_moorti_primitive` per ruling 4, **after one cross-check generation**. `find_contact_episodes` is a second contact producer alongside the Gochara kernel, reconciled in no packet: until the native rules B8-6, declare your episodes `evaluation`-only with `comparable_with = different_convention`.
5. **Emit `coverage`** on every result (absent), **inherit `independence_group`** from every witness (absent), and **emit `window_ref`** on every segment that cites a resonance target or a sweep window.
6. **Two undeclared-or-fragile Gochara reads.** The `'v1'` COALESCE fall-through at `writer.py:2330-2347` and `stage4_field.py:1386-1389`; and — **new finding** — your `depends_on` does not cover the `kala_gochara_windows` read at `stage4_field.py:1384`, so it is **undeclared** (the same defect flagged against Saṅgam). **Do not declare `ka_gochara_sweep`**: it is RETIRED and migration 569 removed that edge by ruling — v2.0 said otherwise and was wrong. Declare an **evaluation-role edge on the table**, generation resolved through `kala_gochara_authority`, cited by `window_ref`, never a λ contributor, alongside removing the `'v1'` fall-through. *Note:* your interim `comparable_with = unstable_key` for the surrogate key is not in the binding's proposed enum; the enum is Gochara's to pin at WP1 — propose it there or use `different_convention`.
7. `_routes.path_edge_ids` is a bigserial reassigned each rebuild — the L2 natural key is a **demand on L2 via L3-U01**, not yours to change; publish `field_snapshot_id`; add `baseline_is_synthetic` to the row.
8. **Binding rows not itemized above that you still carry:** `time_basis` (B1); `epistemic_class`, `operator_role`, six-state `completeness_state`, `comparable_with`, `tier_basis` as your brief promised (B2).

## Shared, all three

- Conformance is proved in each brief's §6 with Layer tests 1, 5, 6, 7, 8, 9, 10, each with a negative fixture that makes the detector fire; test 12 once the baseline exists.
- Nothing above changes a ruling. Where an item depends on a decision only the native can take, it says so and points at binding §B8.
