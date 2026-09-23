---
artifact: GOCHARA_SYNERGY_RESPONSE
canonical_id: GOCHARA_SYNERGY_RESPONSE
version: "1.0"
status: VERIFIED_AT_SOURCE — decisions D-S1..D-S5 await the native
date: 2026-09-24
responds_to: "KALA_SYNERGY_AUDIT_v1_0.md / KALA_SYNERGY_BINDING_v1_0.md / KALA_SYNERGY_AMENDMENTS_v1_0.md §Gochara (strategic session madhav-fc, commit 63b5fb429 on l3/kala-elevation-readiness; corrections below accepted into audit 1.3 / binding 1.1 / amendments 1.3 on that branch, 2026-09-24)"
branch: "l3/gochara-autonomous-wp0-7 — verified against HEAD 9250741cc (+ the executor's three uncommitted WP8 files, untouched)"
method: "Every file:line the audit cites was re-read at source on this branch; line numbers drifted by the executor's commits and are restated as they stand now. Labels: [S] source at HEAD · [R] repository record · [J] judgment."
authority: "Nothing here changes a ruling, the brief, or its two production flags. The binding is PROPOSED; adopting it, and the five decisions below, are the native's. This file is the verified input for that decision."
---

# Gochara family — verified response to the synergy audit

## 0. What the audit got right, in one line each `[S]`

- No code emits `source_qualification` / `corpus_verifiable` / a grain stamp on `kala_vedha_gochara`: migration `platform/supabase/migrations/526_kala_vedha_gochara.sql` creates the table and no later migration adds any of the three.
- `find_episodes` returns `{"episodes": …, "coverage": None}` on the non-Moon branch: `services/gochara_v3/engine.py:1756` (the audit's :1755).
- Inclusivity on `[t_in, t_out]` is declared nowhere: `kala_gochara_contacts` carries `t_in`, `t_exact`, `t_out` as three `TIMESTAMPTZ` columns (migration 1081:161-163) and no `inclusivity` column.
- `completeness_state` and `claim_grain` are `TEXT NOT NULL` with no CHECK (1081:176, :180); `comparable_with` IS CHECK-constrained to the four values (1081:182).
- `services/gochara_grammar/primitives.py:193-194` still maps Rāhu/Ketu to `[120, 180, 240]` with a "BPHS Ch.26" comment.
- `pipeline/orchestrator/writers/ka_gochara.py:107, :362` write `GENERATION_V2` (`'2.0'`); no `'4.0'` writer exists; no L2 identity column exists on any Gochara table.
- Kṣetra's `services/ka_kshetra/stage0_kinematics.py:329 find_contact_episodes` is a second contact-episode producer.

## 1. Corrections to the audit, each verified `[S]`

| audit claim | what the source says | correction |
|---|---|---|
| "TSTZRANGE's `[)` is implicit only" | there is no TSTZRANGE anywhere in 1081; the interval is three `TIMESTAMPTZ` columns. Nothing implies `[)`. `t_in`/`t_out` are the orb-threshold crossing instants the interval solver finds (`interval_solver.py:530-549`), i.e. both endpoints are in-orb boundary instants | the mechanism is wrong; the gap is real. The kernel's own semantics argue for **`closed_closed`**, not the `closed_open` the amendment suggests as default |
| "`completeness_state` … two live values plus one ad-hoc `removed_by_ruling_N14`" | the two live values `qualified`/`unqualified` are the WP1 §3.1 pinned vocabulary and reach the column via `gochara_kernel/ledger.py:256-289`. `removed_by_ruling_N14` is written at `engine.py:924` into the `w30_detail` dict of the λ decomposition — a different surface; it never reaches the `completeness_state` column | the ad-hoc value is a λ-detail key, not a column value. The deeper defect stands: 1081:176's own comment says "six F06 states" and neither live value is an F06 name (`qualified` ≈ F06 `applied`) |
| "`claim_grain` … prose only, column unchecked" | more precisely: `gochara_kernel/ledger.py:176-177, :289` handles `claim_grain` and `time_basis` as columns in a production path, but no production caller populates them with a vocabulary value (0 literals under `services/gochara_*`); the only caller that does is `tests/l3/gochara/test_wp4_decomposed.py:612`, which writes `"exact_instant"` — a value in neither the prose (`date_grain`/`instant_grain`) nor the binding | the column is handled but unpinned: no production caller supplies a value, and the one test value matches neither vocabulary |
| "the plan's `inapplicable` is rejected by the `target_resolution_state` CHECK" | by ruling: N-12 / WP3c R-1 removes negative-result sensitive rows at the resonance layer, so `inapplicable` is deliberately not a stored state; migration 1080's header says so in its own words | not a defect. If F06 `inapplicable` is wanted on **contacts**, it belongs on `completeness_state` (D-S2), not on `target_resolution_state` |
| "only the w30 factor was retired" (N-14) | `nodal_drishti='removed'` drops the w30 term (`engine.py:864-865`, `:1036-1037`) **and** filters every `drishti_contact` row with body ∈ {Rahu, Ketu, RAH_MEAN, KET_MEAN} (`engine.py:1677-1690`) | wrong. Both were retired under the flag. The primitives entry survives only because the ratified design (A-3: one candidate, flags recorded, factor-level delta report; N-14 rides `ka_gochara`'s `'4.0'` candidate) needs `enabled` to reproduce the legacy λ for the delta report. Retiring the entry now would make the legacy arm unmeasurable |
| "`'4.0'` is unimplemented — land it" | `'4.0'` is the WP10 tranche-2 candidate build (brief §7; `PRODUCTION_TRANCHE_2_AUTHORIZED: false`); the served writer keeps `'2.0'` until then by the plan's own sequencing (§4.7: `'3.0'` is the rollback surface, never regenerated) | scheduled and gated, not missing. The audit's row should say "gated at tranche 2", not "unimplemented" |
| "the vocabulary you promised … exists in no code" — implied: unscheduled | brief §5.1 (WP9) schedules exactly that additive migration on `kala_vedha_gochara` and `kala_moorti_nirnaya`; the executor run is at WP8 and has not reached it | true as of code, already ordered in the plan of record. **But** brief §5.1 names the grain stamp `precision_regime ∈ {date_grain, instant_grain}` (the name agreed with the Kṣetra session on 2026-09-23, plan §5.4) while `kala_gochara_contacts` names it `claim_grain` — the two-names-for-one-concept the binding objects to exists inside this family too (D-S4) |
| "Gochara reads nothing from either" (listed as a gap) | plan R2: one-way dependency, no Kṣetra/Saṅgam import — a ratified rule, not an omission | cross-awareness at the data level must therefore run **towards** Gochara (they cite us), never from it (D-S5) |

## 2. Disposition of the seven items

| # | item | status | disposition |
|---|---|---|---|
| 1 | three stamp columns on `kala_vedha_gochara` | **already scheduled** — brief §5.1 (WP9), not yet reached | no new work; name of the grain column is D-S4 |
| 2 | `coverage: None` on the non-Moon branch of `find_episodes` | **real gap** against plan §4.4 ("every no-window and no-contact answer served carries this object") — not yet served by any route, so latent today | fix in this run once authorized (D-S1). Note `kala_gochara_coverage.partition_kind` CHECK admits only `body_target`, `event_class`, `moon_on_demand` (1081:228): a general on-demand search needs either per-body `body_target` rows or a fourth kind |
| 3 | inclusivity undeclared | **real gap**; mechanism corrected above | D-S1: declare `inclusivity = 'closed_closed'` per row (CHECK ∈ {closed_closed, closed_open}), because both endpoints are in-orb crossing instants |
| 4 | `completeness_state` / `claim_grain` unconstrained; F06 six named nowhere | **real gap**, deeper than stated (no production caller populates `claim_grain`; live `qualified` is not an F06 name) | D-S2: adopt the six F06 names on `completeness_state` with `qualified → applied`, CHECK both columns, pin `claim_grain ∈ {instant_grain, date_grain}` and `time_basis` in `WP1_CONTRACTS.md` §3.1 and in the kernel dataclasses. `inapplicable` stays out of `target_resolution_state` (ruled) |
| 5 | primitives Rāhu/Ketu entry | **ruled otherwise** (N-14 behind a flag; A-3 delta report needs the legacy arm) | keep the entry until the `'4.0'` candidate is accepted and the flag default flips; meanwhile correct its comment: the BPHS Ch.26 citation is refuted (F-29) and the entry is "retained for the legacy arm of flag `nodal_drishti` only" (D-S1, comment-only) |
| 6 | `'4.0'` writer; L2 identity column | **scheduled and gated** (tranche 2; R8 = plan row 7, brief §6 packets) | nothing to change |
| 7 | accept `window_ref` as a `target_type` | **new contract ask**; as phrased for Gochara ("MUST ACCEPT as target_ref type") it would let a contact target another asset's window and so **breaks R2**. WP1 §5.3's `target_type` is a closed 8-kind vocabulary of resonance-map targets | D-S5: no new `target_type`. Publish the citation form instead — `window_ref = {asset_id: 'ka_gochara', generation, id: contact_id}` resolves against the existing PK `(chart_id, generation, contact_id)` (1081:197) with no schema change. Kṣetra's `find_contact_episodes` reconciliation (consume, or declare `evaluation`-only with `comparable_with='different_convention'`) is Kṣetra's item |

## 3. Decisions for the native (nothing executes on this file alone)

| id | decision | recommendation `[J]` | cost |
|---|---|---|---|
| **D-S1** | Fold the conformance fixes into the remainder brief as a §4.13 block: coverage row on every `find_episodes` branch; `inclusivity` column + CHECK; primitives comment correction | **yes** — each is conformance to our own ratified plan/contract, not new doctrine | one migration on the disposable DB (additive to 1081; new file numbered by scan, ≥1082), ~40 lines of engine code, tests |
| **D-S2** | Rename `qualified → applied` and CHECK-constrain `completeness_state` to the six F06 names; CHECK `claim_grain` and `time_basis`; pin both in WP1 §3.1 | **yes**, with the rename done in the same migration as D-S1 and the `w30_detail` key mapped `removed_by_ruling_N14 → inapplicable` + `removed_by_ruling: 'N-14'` | touches `ledger.py`, `episodes.py`, `interval_solver.py`, `resolution_hierarchy.py`, 9 test files; nothing served changes (contacts are unserved until tranche 2) |
| **D-S3** | Adopt `KALA_SYNERGY_BINDING_v1_0` B1–B7 by reference in the brief §1, with each OFFER/DEMAND proved in the WP7 packet tests | **yes for B1–B5, B7; B6 as written** (Gochara is the sole contact producer; Kṣetra's episodes are Kṣetra's to reconcile) | adds the binding's tests 5/6/7/9 to the packets' proof matrix |
| **D-S4** | One name for the grain: `claim_grain` on the vedha/moorti stamp too (brief §5.1 currently says `precision_regime`), with `precision_regime`/`day_grade` accepted as read-aliases for one generation | **yes** — but plan §5.4 records the `precision_regime` name as agreed with the Kṣetra session, so this is a cross-stream rename the native should confirm with Kṣetra, not a Gochara-only edit | brief §5.1 + plan §5.4 wording; Kṣetra's own rename is theirs |
| **D-S5** | `window_ref`: no new `target_type`; publish the citation form in WP1_CONTRACTS §5 and in packet C-1's contract; R2 stands | **yes** | prose + one test that resolves a `window_ref` against the PK |

## 4. What this file does not do

It does not edit the brief, the ruling sheet, WP1_CONTRACTS, any code, or the audit on the other branch. The executor run on this worktree is idle since 03:18 IST at WP8 M-1 (three uncommitted test files); its instruction set is left unchanged until the native rules on D-S1..D-S5, so that a resumed run reads one consistent brief.
