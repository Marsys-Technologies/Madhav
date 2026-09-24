---
artifact: GOCHARA_REMAINDER_EXECUTION_BRIEF
version: "1.0"
status: READY_TO_RUN
date: 2026-09-23
executes: "Everything left after WP0–WP7 (FINAL_REPORT_v1_0.md) under the native-ratified GOCHARA_RULING_SHEET_v2_0.md: point-1 residuals (rulings that still need code or evidence), point 2 (the eight receiving-contract packets), point 3 (WP9 overlays), point 4 (WP10 — prepared and rehearsed here; executed only when the flags in §0 are set), point 5 (loose ends)."
branch: "l3/gochara-autonomous-wp0-7 @ /Users/Dev/madhav-l3/gochara-wp0-7 — the same branch and worktree WP0–WP7 ran in; HEAD at brief time 367087bb7 (+ this brief's commit)"
authorization_flags:
  PRODUCTION_TRANCHE_1_AUTHORIZED: true    # AUTHORIZED 2026-09-24 by the native via GOCHARA_NATIVE_RULINGS_2026-09-24_v1_0.md §3. Guards are NOT weakened: steps 0 and 5 still BUILD the (table,generation) guard, the Clear is_active filter and EXPLICIT_CLEAR_OPS. Evidence preconditions unchanged.
  PRODUCTION_TRANCHE_2_AUTHORIZED: true    # AUTHORIZED 2026-09-24, same ruling §3. Still requires tranche 1 evidence green, P-1 merged, WP9 §5.2 merged, N-19 on main, M-1 ratified (ruling §2). A failed flip gate yields a NEW candidate, never a patch.
scope_extension: "By the native's instruction of 2026-09-23 ('build a detailed brief implementation plan which I will paste into Kimi Code to execute … points 2 to 5'), this run is the IMPLEMENTATION OWNER for the eight WP7 packets (P-1, P-2, P-3, P-4, S-1/S-2, T-1, C-1, V-1, K-1). Their target files are IN SCOPE for this run — under every other constraint below. This does not name this run the independent reviewer (§9), and it does not extend scope to anything in §3's hard list."
---

# Gochara — remainder execution brief (points 1-residual, 2, 3, 4, 5)

You are continuing a **ratified, reviewed campaign** on the branch it has always run on. Read this
whole document before doing anything. Then read, in this order and in full:
`GOCHARA_RULING_SHEET_v2_0.md` (NATIVE_RATIFIED — every decision this brief implements),
`GOCHARA_RULING_SHEET_v1_0.md` (the earlier rulings it builds on), `GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md`
(§4 design, §5.3 target contract, §6 downstream contracts, §9 runbook, §10 proof matrix),
`../gochara_wp0_7/FINAL_REPORT_v1_0.md`, `../gochara_wp0_7/wp7_packets/00_INDEX.md` and all ten
packet files, `ESCALATIONS.md`, and `KIMI_AUTONOMOUS_EXECUTION_PROMPT_GOCHARA_v1_0.md` §2, §3, §6
(the autonomy contract and stop conditions — they govern this run unchanged).

**Standard:** acharya-grade astrology, staff-grade engineering. Every classical claim traces to a
cited text or is labelled `uncited_extension=true`; every engineering claim is tested, not asserted;
every number in a report is printed by a passing test.

## 0. Authority, flags, and the one rule that keeps this run safe unattended

- The ruling sheet v2.0 is ratified. **What** to build is settled. This brief settles **how** and
  **in what order**. If the sheet and this brief disagree, the sheet wins and you write an
  escalation.
- **Two authorization flags live in this file's frontmatter, both `false`.** Every task in §7 (WP10)
  that would touch a shared or production database, the live registry, the authority table, a
  deployment, or a real chart's served rows is **gated on the corresponding flag being `true` in
  this file at the moment you reach that step**. If it is `false`, you do everything that does not
  require it (scripts, tests, rehearsal on a disposable database, an authorization-request file with
  evidence) and **stop that task there** — you do not ask, you do not wait, you move to the next
  in-scope task. The native flips the flag by editing this file and re-running you.
- **Autonomy contract (unchanged from the WP0–WP7 prompt):** in-scope implementation choices are
  yours — decide, record the reason, continue. Anything out of scope, any §3 stop condition, or any
  in-scope task that turns out to need an out-of-scope action → a dated entry in `ESCALATIONS.md`
  (continue the E-numbering) and move on. The run ends when every task is done or parked, never
  because a boundary was hit.

## 1. Where you are

Worktree `/Users/Dev/madhav-l3/gochara-wp0-7`, branch `l3/gochara-autonomous-wp0-7`, off `main`.
**First three actions, in order:** `git rev-parse --abbrev-ref HEAD` + `git worktree list` (stop with
a message if not this worktree/branch); `git log --oneline -20` + `cat ESCALATIONS.md`; from
`platform/python-sidecar`: `python3 -m pytest tests/l3/gochara/ -q` — expect **96 passed** before you
add anything. Do not create another worktree. Do not write to `/Users/Dev/Vibe-Coding/Apps/Madhav` or
any other checkout of this repository — a previous session did, by mistake, and it cost a day.

Done and committed (do not redo): WP0, WP1, WP2, WP3a (kernel), WP3b, WP3c (R-1..R-6), WP4, WP5
(H-1a/H-2/H-3/H-4/H-6), WP6 (ledger on a disposable DB; migrations **1080/1081** — renumbered twice, see §3 and ESCALATIONS.md E-007 addendum),
WP7 (sentinel chain + eight design packets). Ratified since: the sheet v2.0 (M-1..M-8 parameters
and semantics; N-15..N-22; A-1..A-3; O-1..O-3; G-6..G-10).

## 2. Task order (the critical path), and why

```
§4 point-1 residuals (A-class, in-branch)          ─┐
§5 WP9 overlays + M-8 + stamp columns (A-class)      ├─ can run in parallel where files don't overlap
§6 the eight packets (scope extended; A-class)      ─┘
§8 loose ends (N-18 push/PR, N-19, N-20, G-9 file, G-10)
§7 WP10 preparation + rehearsal (A-class) → STOP at the flags → (flags true) tranche 1 → tranche 2
```

Inside §4, do **N-16 first** (it is a detector every later λ change is measured against), then N-17,
N-22, the M-6 contract rows, then the flag-gated scoring changes (M-1 shape, M-3 split, N-14, N-15)
**behind recorded flags in the input generation vector, defaulting to "off = today's behaviour"**,
then the WP8 evidence batteries. Nothing in §4 changes what a build produces until the candidate
generation of WP10 step 6 turns the flags on — that is the sheet's own discipline (every served-λ
change rides the first `'4.0'` candidate, never a patch over live rows).

## 3. Hard constraints (all of the WP0–WP7 prompt's, plus these)

- **Protected data:** `kala_gochara_windows WHERE generation IN ('v1','3.0')` and
  `kala_gochara_windows_v2 WHERE generation LIKE 'g3_%'` — never read-with-mutation, never written,
  by anything you write or run.
- **Still outside scope even with the extension:** `platform-mcp/src/tools/kala_views/**`;
  `pipeline/transit_search.py`; `brahmagyan/l0_ephemeris.py`; `services/ka_dasha_kala/**`;
  `platform/scripts/seed/asset_registry_seed.ts`; `.github/workflows/deploy.yml`;
  `kala_gochara_authority` (flipped only at WP10 step 8 under tranche-2 authority);
  `services/ka_kota_chakra/**`. Saṅgam's and Kṣetra's own engines stay theirs: V-1 and K-1 are
  **declaration and pinning changes** in their registry rows and read sites only (the packets say
  exactly which lines) — you do not refactor their algorithms.
- **Migrations:** files only, numbered by **scanning every `origin/*` head across BOTH
  `platform/migrations/` and `platform/supabase/migrations/`** (`git fetch --all` first; the next free
  number after 1081 at the 2026-09-24 amendment is **1082** — re-scan at run time; five branches have already collided on 1071–1079, and `origin/l0/vedha-and-frame-repair` (PR #2727) holds 1075–1079 in `platform/supabase/migrations/` with all five (1075–1079) APPLIED to production (2026-09-23 21:07–22:03 UTC), which is why this branch's pair moved 1075/1076 → 1080/1081; see ESCALATIONS.md E-007 addendum).
  Applied only to a disposable database you provision and tear down (`docker` Postgres, as WP6 did;
  name it `gochara-remainder-disposable`; **tear it down at the end of the run** — WP6's container was
  found still running two hours after its work finished). **Never renumber a migration after it has
  been applied anywhere**: the runner (`platform/scripts/migrate.ts`) tracks by filename + sha256 +
  `sql_identity`, so a renumbered-after-apply file looks new.
- **FROZEN orchestrator contract:** any writer-shaped code stays `WriterBase`-ready (`@register`,
  `run(ctx)`/`plan_substeps`+`run_substep`, `ctx.db_conn` never committed or closed, no
  `asset_throughput` writes, `chart_id`/`birth_params` from `ctx.config`). Needing to change it is a
  stop condition.
- **Corpus rule (F-32):** the admitted corpus is the served table `classical_text_chunks`, which this
  checkout **cannot query**. You therefore make **no new absence or presence claim** about any text.
  Every citation you write is one the ruling sheet, the plan, or a packet already carries with its
  page anchor; anything else is `uncited_extension=true`. The OCR files under `SOURCE_DATA/` may be
  read to check what an already-cited BPHS passage says, never to establish a new citation.
- **No real chart, no person data**, anywhere in fixtures or tests. The canonical chart id and the
  second chart id appear only in WP10 scripts, which do not run without the flags.
- **Identity:** exactly one identity scheme — `services/gochara_kernel/ids.py`. Never add a second
  `contact_id`/`independence_group`-shaped function anywhere (the WP5 reconciliation found and removed
  one).
- **Honesty:** `NOT_RUN` is a result; a green with no detector is not. Every `[U]` stays `[U]`.
- **Commit discipline:** small commits, one concern each, on this branch; never `git add -A`; never
  commit the disposable DB's data or any `.env`; commit messages name the sheet item they implement.

## 4. Point-1 residuals — rulings that still need code or evidence (A-class)

| # | Task | Implements | Exit gate |
|---|---|---|---|
| 4.1 | **N-16 wiring detector.** A test in `tests/l3/gochara/` that fails whenever three sources disagree: `scripts/kala_admission/w44_weight_fitting.py::MECHANISM_ENGINE_WIRED`, `services/gochara_v3/mechanism_register.yaml`'s mechanism set, and `services/gochara_v3/engine.py`'s mechanism imports + the λ product (`:700`). Today it **must fail** (w23 is multiplied while marked `False`; w30 is in the product but in neither the dict nor the register). Then make it pass by making the dict **derived** from `engine.py` (or by correcting the dict and register to the truth, with the test as the permanent guard) — your choice, recorded. Fold a citation-drift sweep: every `engine.py:NNN` reference in `WP3b_CLASSIFICATION.md`, `ESCALATIONS.md`, `GOCHARA_DECISION_RECOMMENDATIONS_v1_0.md` re-pointed to HEAD lines | N-16 | test red-then-green committed separately; any w44 re-fit code path documented as "must not run before this test is green" |
| 4.2 | **N-17 cap-free admission.** In `services/gochara_v3/resolution_hierarchy.py`: `retain_candidates_pooled` persists every admitted peak (`MAX_PEAKS_PER_ERA_WINDOW` removed from admission), plateau ties all rank 1 (kernel `peaks.admit_peaks` semantics); the **90-day separation filter moves to a serve-time trim policy** (expose it as a parameter the serving layer passes, default = no trim, with the pre-trim count returned); re-pin `test_f10_peak_cap_truncation` (WP3b A-5) as *legacy baseline, superseded*, and add the new golden test | N-17, H-5 | 96 + new tests green; WP6's ledger writes all admitted peaks |
| 4.3 | **N-22 / N-13 sign-level bindu interim.** A kakṣyā crossing whose transiting graha has **no resolvable bindu in the transited sign** (`chart_facts` `ashtakavarga_bindu_sign` for that graha × sign) contributes **no activity** and carries `completeness_state='unqualified'`; where a bindu count resolves, the crossing is qualified by it (the sign-level BAV, declared as the coarser qualification — `qualification_grain='sign'`). Behind a recorded flag `kakshya_bindu_interim` in the input generation vector, default **off** | N-13, N-22, M-7 interim | fixture: graha with 0 bindus in the sign → unqualified, no activity; with 4 → qualified; flag off → today's behaviour byte-identical |
| 4.4 | **M-6 target-contract rows.** Extend `WP1_CONTRACTS.md` §2.2 and the resolver in `services/gochara_intensity/enrichment.py` / resonance writer with: (a) **Gulika/Māndi derived points** — the sign-distance target (*"as far from Māndi as Māndi is from the 8th lord"*, Phaladīpikā XVII `PG220:C1` śl.26) and the Yamakaṇṭaka-difference rāśi/navāṃśa spans (`PG214:C1` śl.6–8, `PG217:C1` śl.14) — emitted **only for the māraka/death and acute-illness classes**, from L1 `sensitive_point_gulika_mandi` and the 8th-lord `graha_position`; (b) **bhāva-ārūḍhas** (`bhava_arudha` category, 14 subjects) as **interval** targets, `uncited_extension=true`. Special lagnas, Prāṇapada, nakṣatra-pāda points: **not emitted** (deferred by ruling) | M-6 | golden fixtures per new row; the 27-class completeness gate still passes; no point target ever derived from a cusp placeholder |
| 4.5 | **M-1 shape, behind a flag.** Implement linear-in-separation activity `1 − |Δ|/orb_max_deg` with **no time box**, orb per WP1 §7 `orb_source`, as a projection option `activity_shape ∈ {legacy_box, linear_no_box}` with `orb_max_deg` parameterised; default `legacy_box`. Do **not** remove `_ACTIVITY_MAX_ORB_DEG` (`engine.py:222`) or its mirrors yet — mark them with a comment naming the ratification step that retires them | M-1 (shape) | fixture reproducing WP4's numbers: box 0.80000, no-box×5.0° 0.7888, no-box×1.0° 0.74415 at +4 d, speed 0.017454°/d |
| 4.6 | **WP8 battery for M-1 (evidence, not a ruling).** Run the six arms — legacy box ±5 d · no-box×5.0° · ×2.0° · ×1.0° · ×0.5° — on the two pre-declared workloads: **marriage-2013** and **ordinary quarter 2027-03→05**, built as **synthetic** fixtures (the shape of those walkthroughs from plan §3 F-02, with invented chart data — no real chart). Score: anchor recall with λ-margin; active-day count ≤ legacy; distinct windows for the 13 envelope-only classes; dynamic range; plateau stability across 0.5×/2× of each candidate. Write `WP8_M1_ORB_BATTERY_v1_0.md` with every number printed by a test; **recommend, do not ratify** | M-1 (values) | report exists; a narrower orb is recommended only if it beats 5.0°-no-box on recall and range |
| 4.7 | **M-2 retrograde qualifier + battery.** `branch`/`station_flag` already exist on episodes; add `intensity_qualifier='retrograde_malefic'` on vedha rows (done in §5.2); **pre-declare** one Saturn and one Mars retrograde season as synthetic ablation windows in `WP8_M2_RETROGRADE_WINDOWS_v1_0.md` before any ablation code exists; then run with/without a retrograde weight and report. Dwell: **no weight** — confirm `dwell_days` is geometry-only | M-2 | windows declared before the ablation; report with numbers; no weight shipped |
| 4.8 | **M-3 Moon channel split, behind a flag.** `moon_channel ∈ {blended(legacy), separate}`; when `separate`: the Moon is excluded from the century λ's activity term; a `find_episodes(..., moon=True)` path serves Moon-scale classes on demand and writes a `moon_on_demand` coverage partition; tārā-bala and mūrti qualifiers still enter slow-body windows at the instant. The channel's own doctrine content stays `[U]` — no citation invented; Sade-Sati testimony is **not** in the Moon channel | M-3 | fixture: Moon contacts absent from century λ when `separate`; coverage partition written even for zero Moon contacts |
| 4.9 | **N-14 w30 removal, behind a flag.** `nodal_drishti ∈ {enabled(legacy), removed}`; when `removed`: `drishti_contact` emits no rows with `body ∈ {Rahu, Ketu}` (nodes stay agents/targets for conjunction, ingress, kakṣyā, return); `w30_modifier` leaves the product; the removed term is **kept one generation as a labelled non-scoring annotation** (`term_breakdown.w30_annotation`); absence recorded as `completeness_state`. Default `enabled` | N-14 (three conditions) | fixture: node dṛṣṭi rows absent and w30 absent from λ when `removed`; annotation present; flag off → byte-identical |
| 4.10 | **N-15 Sade-Sati to testimony, behind a flag.** `sade_sati_mode ∈ {permission_weight(legacy), testimony}`; when `testimony`: `sade_sati` is **dropped from `SYSTEM_WEIGHTS` and `total_weight` renormalised** (`engine.py:1367-1374, :1411-1413`) — never a zero-weight row; the phase becomes typed testimony on the window (`epistemic_class` per F04, `corpus_verifiable=false`, citation = the nāḍī rows `PG1334`/`PG786`/`PG1333` at MEDIUM provenance per N-21); the **global permission lift is computed and reported** as a first-class delta | N-15, N-21 | fixture: permission fraction changes at an instant with no Sade-Sati active (denominator effect) and the delta is reported; flag off → byte-identical |
| 4.11 | **Factor-level delta report.** A test-driven report generator that, given two projection configurations (flag sets), emits the delta per factor (promise / permission incl. denominator shift / activity / tārā / w30 / quality_gates), peak counts, and slices by relation × body — the instrument A-3 requires for the first candidate. Run it on the synthetic workloads for every flag individually and all together | A-3 condition (ii) | `WP8_FACTOR_DELTA_REPORT_v1_0.md` with numbers from tests |
| 4.12 | **N-21 standing rule** recorded in `WP1_CONTRACTS.md` §6 vocabulary notes: nāḍī attestation → testimony, never weight, without primary corroboration | N-21 | text present; `corpus_verifiable`/`source_qualification` semantics reference it |

## 5. Point 3 — WP9 overlays on the kernel (A-class; A-1 authorized)

| # | Task | Exit gate |
|---|---|---|
| 5.1 | **Stamp columns migration** for `kala_vedha_gochara` (and `kala_moorti_nirnaya`): `source_qualification ∈ {verse_cited, algorithmic_approximation, unsourced}`, `precision_regime ∈ {date_grain, instant_grain}`, `corpus_verifiable BOOLEAN` — additive, with a down-migration; applied to the disposable DB only. Writers populate them (house_vedha: `verse_cited` via `bg_transit_rules` + Phaladīpikā XXVI, `corpus_verifiable=true` **only once G-9's re-citation is on the row**, else `false`; sarvatobhadra: `algorithmic_approximation` exactly when `grid_basis` says so; latta: `verse_cited`, Ketu excepted) | migration file numbered per §3; three consumers' contract (plan §5.4) satisfied; Vedha integrity conjuncts (a)–(j) still green |
| 5.2 | **M-8 in `services/ka_vedha_gochara/`.** (a) General mutual exclusions Sun↔Saturn and Moon↔Mercury in every house pair → **no vedha row**, coverage records `searched, exception_applied`; (b) **vipareeta**: row kept, `cancelled=true`, `cancelled_by`, `cancelled_from`/`cancelled_until` (companionship interval), `suppression_factor=1.0`; (c) `intensity_qualifier='retrograde_malefic'` where a malefic is retrograde in vedha position; evaluation order exceptions → vipareeta; `source_qualification` on vipareeta rows says translator-commentary. On the DATE-grain overlap path stamp `precision_regime='date_grain'` — never an instant claim on day-grain evidence | fixtures: Saturn-in-9th vs Sun-in-3rd → no row; companion joins → cancelled interval; retrograde malefic → qualifier; all existing Vedha tests green |
| 5.3 | **Vedha + Moorti on the kernel.** Coverage = **requested horizon** (not the ±460 d window; F-11); every gap → `unavailable` in the coverage manifest, never `quality_gates=1.0` by default; **Moorti graded at the true ingress instant** (kernel `sign_ingress` episode), with the day-grade misclassification rate measured and reported; `independence_group` on Vedha so one obstruction root attenuates once (A08) | fixtures per plan §10 "Negative" and "Overlay at instant" rows; error-rate report |
| 5.4 | **Kota:** untouched (proposed-use; M-4 w25 row). Record only | — |

## 6. Point 2 — the eight receiving-contract packets (scope extended by the native; A-class)

Implement each packet **exactly as its design file specifies**; every packet already carries the
file:line anchors, the change, and its acceptance tests. Order: **C-1 → P-1 → P-2 → K-1/V-1 → P-4 →
P-3 → S-1/S-2 → T-1**. Each packet is one PR-sized commit series with its packet's acceptance tests
green; each ends with a short **review-request note** (`wp7_packets/REVIEW_REQUEST_<id>.md`) for the
independent reviewer (§9) — you do not self-certify a packet.

| Packet | File | What lands (summary — the packet is normative) |
|---|---|---|
| **C-1** | `platform/src/lib/cockpit/assetClearSpec.ts` (+ `app/api/cockpit/clear/**` tests) | `EXPLICIT_CLEAR_OPS['ka_gochara']`: three generation-scoped DELETEs in dependency order (coverage → contacts → windows, `WHERE chart_id=$1 AND generation='4.0'`); **refusal** when the target generation is the chart's authoritative one unless the release authority cascades an authority reset + manifest `cleared`; no JOIN; `clear_tables` display value with the F-24 display-only caveat. Test: Clear of `'4.0'` leaves zero rows in all three relations |
| **P-1** | `platform-mcp/src/tools/retrieval/register_gochara_windows.ts` (+ `/api/mcp/db/query` whitelist) | **manifest-driven** provenance and coverage for any generation with a `kala_gochara_publication` row (never a literal `'4.0'` string); `v1`/`'3.0'`/`g3_*` branches kept as legacy fallbacks; the `'v1'` COALESCE default removed — absent authority row → `unpublished` coverage object; `computeGocharaCoverage` reads `kala_gochara_coverage` when present and routes `'4.x'` substeps to `asset_id='ka_gochara'`; **H-5 serving rule** (P-1e): cap-free admission, serve-time trim with `trimmed:true` + pre-trim count, never re-rank; whitelist entries for the two new relations. Test: a `'4.0'` authority chart names `ka_gochara` and still does after a republish as `'4.1'` |
| **P-2** | `platform/src/lib/retrieval/registry/layers/reading_checklist.ts` | `fetchGocharaSweep` carries `contact_id`s (via `active_sentences`), `completeness_state`, `peak_basis` through its cap/trim; confirmed-vs-context counts served separately (§N.6); the H-5 boundary folded in |
| **K-1** | Kṣetra's registry row + read sites named in the packet (`stage4_field.py:1386-1389`, `writer.py:952,1063,2328-2330`) | declare `→ka_gochara` (+ `→ka_vedha_gochara` after one cross-check generation); pin provenance edges by `(generation, id)`; remove the `'v1'` fall-throughs → `unpublished` |
| **V-1** | Saṅgam's registry row + `ka_sangam.py:1057-1065` | declare `→ka_vedha_gochara` (`counterevidence`); re-type `→ka_gochara` as `service` |
| **P-4** | new read capability (retrieval registry) | density-layered read over `kala_gochara_contacts` + `kala_gochara_coverage`: confirmed episodes on a `hard_floor`, catalog-only rows in a separate context layer, `searched_horizon` exposed for `moon_on_demand`; `density_contract` declared |
| **P-3** | L5 claim/prediction ledger | nullable `contact_id` (`sha256:` id) so frozen claims keep identity across rebuild/republish/rollback via `contact_id → window_id → manifest_id`; the `lel/prospective_ledger.ts` filing path per the packet |
| **S-1 / S-2** | `services/ka_gochara/service.py` | `find_aspects` keeps its exact shape (adapter over episodes) for `kala_trigger` `:96/:150/:199`, `currents.py:59`, `ka_sangam/engine.py:464`; new `find_episodes(chart_id, targets, horizon, *, bodies, relations, moon) -> EpisodeBatch` returning solved episodes with grain, coverage, `contact_id`; **S-2**: directed contact events as kernel episodes — per-graha Parāśari angles, **no node dṛṣṭi (N-14)**, `planets` as a list, absent when nothing fires, never a zero row. Test: all five existing callers run unchanged; `find_episodes` returns coverage even for zero contacts |
| **T-1** | note only, to the `kala_trigger` owner | fold this run's measured `find_episodes` numbers into `PACKET_T1_kala_trigger.md` v1.2; **do not** modify `services/kala_trigger/**` |

## 7. Point 4 — WP10: prepare and rehearse now; execute only under the flags

**7.A Preparation (A-class, always runs):** for each runbook step 0–10 (plan §9, sheet A-2/A-3),
write the executable script or migration it needs, its **gate test**, and its evidence template,
under `scripts/kala_gochara_cutover/` — never pointed at a shared database by default (connection
string must be an explicit argument; the scripts refuse the production instance name unless the
matching flag in this file is `true`). Specifically: step 0 consumes `origin/l3/kala-p1-1-b1-clear-guard`
(the Clear `is_active` filter and the (table, generation) guard already exist there — **do not
duplicate them**; reference or cherry-pick with attribution); step 1 the SELECT grant SQL; step 2 the
restore-drill script with row-by-row digest equality and the 2,667-uncovered-id report (runs
`NOT_RUN` here — no dump is available locally); step 3 `is_active=false` for the century (N-6a) with
its reversal — **and note, because another stream's record (`KALA_DELEGATED_DECISIONS_v1_0.md` D-C, since WITHDRAWN in full at `dfcb2b25b` on `l3/kala-elevation-readiness` after this correction) briefly read it otherwise: N-14 does NOT require the century writer to run.** The `'4.0'` candidate that carries N-14 is built by `ka_gochara` (N-5: the served owner; N-6: the century's engine is donated as the projection); `'3.0'` is the rollback surface and is never regenerated (plan §4.7). N-6a therefore blocks nothing the sheet rules for, and it makes D-C's own item 2 ("no unattended build may include the asset") structural rather than procedural. the one surviving part of D-C — declare `kala_gochara_windows` in the century's `clear_tables` (F-30) — is step 5's registry work here; the strategic session has left its SQL in its record as this runbook's step 5; step 4 apply/verify **1075/1076** (+ any migration this run adds) with an
`information_schema` diff; step 5 the registry re-pin migration (plan §6.3: `count_sql`, `depends_on`
incl. `bg_transit_rules`, integrity conjuncts (a)–(k), N-9 (iii)–(v)); step 6 the candidate-build
invocation with **all §4 flags on** and the input generation vector recorded; step 7 the four flip
gates as tests against the (deployed) tools; step 8 the flip + manifest `published`; step 9 the soak
checklist and the second-chart birth-epoch fixture (#2534 class); step 10 N-11's delete-under-own-scope
and the 1018 digest retirement. **Rehearse the whole sequence on the disposable database** with
synthetic data and write `WP10_REHEARSAL_v1_0.md` (what ran, what was `NOT_RUN` and why).

**7.B Tranche 1 (steps 0–5) — runs only if `PRODUCTION_TRANCHE_1_AUTHORIZED: true`.** Preconditions
the script checks itself: N-18 merged to `main`; C-1 merged; each step's evidence file written before
the next step starts; the standing order acknowledged in the evidence header. Any failed gate → stop
the tranche, write the evidence, escalate; never proceed past a red gate.

**7.C Tranche 2 (steps 6–10) — runs only if `PRODUCTION_TRANCHE_2_AUTHORIZED: true` AND tranche 1's
evidence file exists and is green AND P-1 is merged AND (WP8 M-1 ratified by the native in the sheet
OR the declared fallback `no-box × 5.0°` is used) AND WP9 §5.2 is merged AND N-19's artifacts are on
`main`.** The first `'4.0'` candidate carries N-14, N-15, N-17, N-22, M-1's shape, M-8's rows — each
flag recorded in the input generation vector — and the **factor-level delta report vs `'3.0'`** from
§4.11 is attached to the manifest. A failed flip gate yields a **new candidate**, never a patch. The
authority flip is the last act of step 8 and is logged with `evidence_ref = manifest_id`.

## 8. Point 5 — loose ends

| # | Task | Exit gate |
|---|---|---|
| 8.1 | **N-18 push + PR.** Push `l3/gochara-autonomous-wp0-7`; open the PR to `main` (title `feat(l3-gochara): …`; body states: merge lands code only, no build runs under the 2026-08-21 standing order, R-1..R-6 take effect only at a resonance rebuild sequenced at WP10 step 6, migrations 1080/1081 unapplied to any shared DB, the number collisions (1071–1074 on four branches; 1075–1079 on the L0 repair branch, all five of which (1075–1079) are applied to production since 2026-09-23) and their resolution). End the body with the attribution line the repo's PR convention uses | PR URL recorded in the final report |
| 8.2 | **N-19.** Bring `KALA_COST_PROFILE_v1_0.md` and `KALA_BASELINE_v1_0.md` onto this branch from `origin/l3/kala-setup-phase01` (`bb7857b07`, `de2a7f269`) with attribution in the commit; make the plan §10 Value row's CI gate real (test asserts presence; `NOT_RUN` otherwise) | files present; test green |
| 8.3 | **N-20.** Reader-inventory update: add the ten WP0 consumers (`WP0_FINDINGS.md`) to plan §6.1's table in `GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md` (a v2.2 changelog entry), cross-reference w44 ↔ N-16; no guard for the W41–W45 `_v2` scripts | table updated |
| 8.4 | **G-9 repair as a migration file (L0 data; file only).** From `KSHETRA_L0_VEDHA_ROW_FIXES_v1_0.md` (PR #2725 @ `3b5821bcd` — fetch and read it; **attributed, so verify each before/after SELECT against the OCR-independent evidence the spec carries before writing**): re-cite 32 rows to `phaladeepika:PG322:C1`/`PG323:C1`; UPDATE `vedha_house` on ids 35→1, 44→5, 45→11 (never delete); INSERT the Mercury 8th-house pair (vedha from the 1st, `PG323:C1`); strike `"BPHS Ch.29"` from every `classical_citation` (G-8); the six Rāhu/Ketu rows (187–189, 196–198) → `uncited_extension=true` + a note that their disposition follows N-14 (do not delete). Down-migration included. Applied to the disposable DB only; its verification test asserts the before/after row states the spec prints | migration file numbered per §3; test green on the disposable DB |
| 8.5 | **G-10 (L1) — design + migration + writer change, carefully.** Per-contributor BAV matrix (8 contributors × 12 signs × 7 grahas per ayanāṃśa) as a new `chart_facts` category `ashtakavarga_bindu_contributor`, written by `ga_writers/ga_strength_writer.py`. **Caution:** an unauthorized edit to this writer by another stream this week caused a build-fatal `NameError`; every change here runs the full L1 test suite (`tests/` for `ga_strength`) green before commit, and the writer stays `WriterBase`-conformant. The nāḍī rows (`PG1615`, `PG1616`) are the attested model (testimony grade, N-21) | L1 tests green; the matrix's fixture matches BPHS ch.66's dot/rekha semantics for one synthetic chart |
| 8.6 | **Reviewer for Kṣetra rulings 7/8/9** — not yours; note in the final report that it remains the native's to name |

## 9. Review discipline
You are the implementation owner, not the reviewer. For each of: §4 as a whole, §5, each §6 packet,
§7.A, §8.4, §8.5 — write a `REVIEW_REQUEST_<id>.md` (what changed, tests, the sheet item it
implements, what you are unsure of). The native runs the Kimi K3 review + reconciliation loop on
those, as was done for the plan and the decisions. Do not mark anything `REVIEWED`.

## 10. Final report
`REMAINDER_FINAL_REPORT_v1_0.md` next to `FINAL_REPORT_v1_0.md`: state reached per task (§4–§8),
unreached states (explicitly: which flags were `false` and what stopped there; the 7/8/9 reviewer;
anything `NOT_RUN`), every `ESCALATIONS.md` entry summarised, confirmation that protected data and
the §3 hard list were untouched and that no shared database was written to, the disposable DB torn
down, the PR URL, and the artifact list.

## 11. Start here
1. `git rev-parse --abbrev-ref HEAD`; `git worktree list` — confirm the worktree/branch.
2. `git log --oneline -20`; `cat ESCALATIONS.md`; `cat 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/GOCHARA_RULING_SHEET_v2_0.md`.
3. `cd platform/python-sidecar && python3 -m pytest tests/l3/gochara/ -q` — 96 passed.
4. `git fetch --all`; scan both migration directories across every `origin/*` head; record the next
   free number in `ESCALATIONS.md` before writing any migration.
5. Read the frontmatter flags of **this** file; note their values in your first log line.
6. Execute §4 → §5 → §6 → §8 → §7.A; then §7.B/§7.C only as the flags allow. Escalate, never ask.

---

## 12. DELTA of 2026-09-24 — read this before you do anything else

> **STATUS 2026-09-24 13:00 (annotated 13:50 — see the end of this banner) — THIS ENTIRE §12 IS UNEXECUTED.** The first run of this brief closed at
> `ce7fc29da`, 12:50:13 IST, reporting `PRODUCTION_TRANCHE_1/2_AUTHORIZED: false`. Both flags were set
> **true** at `e93112eb0`, 12:37:04 IST — **thirteen minutes before that close.** The run reported a flag
> value it had cached at session open instead of re-reading the file it was told to treat as authoritative,
> and skipped §7.B and §7.C on that stale read. It also pre-dates M-1's ratification and every task in
> §12.3, §12.4, §12.5 and §12.9, none of which it saw. Audited at 13:00: `engine.py:1756` still returns
> `coverage: None`; `1081` has no `inclusivity` column and no F06 CHECK; `claim_grain` is still named
> `claim_grain`; the vedha writer still has no upstream fingerprint; `1086` still carries its wrong `l0_`
> basename. **Nothing in §12 was done.** That is not a failure of the work that *was* delivered — §§1–11
> are genuinely complete — it is the reason this section exists and must be executed by the next run,
> which must **re-read this file from disk before acting on any flag or number in it.**
>
> **13:50 UPDATE:** the native asked the L3 session to execute this delta directly. Done so far, each in
> its own commit: **12.10b** (writer honesty — `4d8f83050`) and **12.5** (detector, cause unknown).
> Everything not named here is still open. The 13:00 audit sentence "the polluting test is among the 52
> skips" was wrong and is retracted (see §12.5).


Everything in §§1–11 stands. This section is **added** work and **two changed answers**, ruled by the
native on 2026-09-24 in `GOCHARA_NATIVE_RULINGS_2026-09-24_v1_0.md` (read it in full; it is short).
Migrations 1075/1076 were renumbered to **1080/1081**; the next free number is by fresh scan.

### 12.1 Both authorization flags are now `true`

§7.B and §7.C are live. **Guards are not weakened** — steps 0 and 5 still build the
`(table, generation)` guard, the Phase 1.1 Clear `is_active` filter and `EXPLICIT_CLEAR_OPS`, and
step 0 consumes `origin/l3/kala-p1-1-b1-clear-guard` rather than duplicating it. Every evidence
precondition in §7.B/§7.C is unchanged and is checked by the scripts themselves. A failed gate stops
the tranche, writes its evidence and escalates. A failed **flip** gate yields a new candidate, never
a patch. `'3.0'` and `'v1'` remain protected and are never regenerated.

### 12.2 M-1 is ratified, with the value split — this changes §7.C

- **Shape:** linear in separation, no time box: `activity = 1 − |Δ| / orb_max_deg`. Ratified.
- **Candidate 1 of `'4.0'` uses `orb_max_deg = 5.0`**, so the factor-level delta report against
  `'3.0'` isolates the shape change and stays interpretable.
- **`orb_max_deg = 1.0` is candidate 2**, ratified only on candidate 1's delta report against the
  real canonical chart. `0.5` is rejected (plateau failure). `2.0` is the recorded runner-up.
- Record the value in the input generation vector of each candidate.

### 12.3 New task block §4.13 — the D-S1/D-S2 conformance fixes

One additive migration (fresh-scan number, disposable DB only) plus the code and tests:

| # | task | exit gate |
|---|---|---|
| 4.13a | `find_episodes` returns a `coverage` object on **every** branch, not only `moon=True` (`engine.py` ~:1756). `kala_gochara_coverage.partition_kind` admits only `body_target`/`event_class`/`moon_on_demand` — either emit per-body `body_target` rows or add a fourth kind in the same migration, and say which you chose and why | a zero-contact non-Moon search returns a coverage row; a test asserts no branch can return `coverage: None` |
| 4.13b | `inclusivity` column on `kala_gochara_contacts`, CHECK ∈ {`closed_closed`,`closed_open`}, value `closed_closed` on every row, because `t_in`/`t_out` are both in-orb threshold crossings | CHECK present; a row with a bad value is rejected |
| 4.13c | `completeness_state` CHECK-constrained to the six F06 states `{applied, inapplicable, unavailable, unqualified, contradictory_unresolved, unexplored}`; migrate live `qualified` → **`applied`** through `ledger.py`, `episodes.py`, `interval_solver.py`, `resolution_hierarchy.py` and every test. In `engine.py` ~:924 the λ-detail key becomes `completeness_state: 'inapplicable'` + `removed_by_ruling: 'N-14'` | CHECK present; suite green; no `qualified` literal survives |
| 4.13d | CHECK-constrain `time_basis`; add `tier_basis TEXT` CHECK ∈ {`relative_uncalibrated`,`calibrated:<gate_id>`}; pin both vocabularies in `WP1_CONTRACTS.md` §3.1 | columns constrained; §3.1 states the closed sets |
| 4.13e | **Rename `claim_grain` → `precision_regime`** in migration 1081, `ledger.py`, the kernel dataclasses and the tests — 1081 has never been applied outside a disposable DB, so edit it in place and re-verify; no alias generation is needed. Values `{instant_grain, date_grain}`, pinned at `WP1_CONTRACTS.md` §3.1, and `day_grade` is aliased to `date_grain` **until the successor condition of Saṅgam D-7 is met — every dependent claim has an authorized successor — not for a count of generations** (binding 2.2 §B1, verified at `8211c2dc6`). **Also fix the one caller writing the non-vocabulary value `"exact_instant"`** (`tests/l3/gochara/test_wp4_decomposed.py` ~:612) and make a production caller actually populate both columns | no `claim_grain` identifier remains; a test asserts a populated `precision_regime` on a written contact row |
| 4.13f | `services/gochara_grammar/primitives.py:193-194` — correct the comment: its BPHS Ch.26 citation is **refuted by F-29**, and the Rāhu/Ketu entry is retained **only** for the legacy arm of flag `nodal_drishti`, retiring when candidate `'4.0'` is accepted. Comment and docstring only; **do not remove the entry** | comment states the refutation and the retirement condition |
| 4.13g | **Per-call node-mode assertion** in this family's own readers: every node longitude read asserts `RAH_MEAN`/`KET_MEAN` and **raises** rather than degrading to `TRUE_NODE` | a test proves the assertion fires when a true-node value is injected |
| 4.13h | `window_ref = {asset_id:'ka_gochara', generation, id: contact_id}` documented in `WP1_CONTRACTS.md` §5 and in packet C-1's contract. **No new `target_type`** — plan R2 stands, this family imports nothing from Kṣetra or Saṅgam | one test resolves a `window_ref` against the PK `(chart_id, generation, contact_id)` |
| 4.13i | `comparable_with` stays at the four values pinned at WP1 §6. **`unstable_key` is declined** (D-S6). Record the decline in `WP1_CONTRACTS.md` §6 with its reason | §6 states the closed four and the declined value |

### 12.4 Adopt the layer binding — new §6.11

Adopt `KALA_SYNERGY_BINDING_v1_0.md` **§B1–B7 by reference** in §1 of this brief (currently **binding 2.2** at
`8211c2dc6` on `origin/l3/kala-elevation-readiness`, verified 2026-09-24; read the LIVE file and note its
own version — never trust a version quoted here or in a message). Prove each row this family OFFERS or DEMANDS in the packet proof matrix with
the binding's tests 5, 6, 7 and 9, **each with a negative fixture that makes the detector fire**. A
green run that could not go red does not count. B6 is adopted as written: this family is the sole
contact-episode producer.

### 12.5 A live test-isolation defect — fix before §7.B

`tests/l3/gochara/test_wp3a_kernel.py::test_case_02_mean_node_convention` **passes alone and fails in
the full suite**, deterministically. In the suite the module-global `swe` is left stubbed by an earlier
test, so `swe.julday(2026,1,1,0)` returns ≈ 0 and the call dies with "jd -0.001010 outside Moshier
planet range". This is finding F-31's process-global trap, and it means the one test that guards the
**mean-node convention three rulings pin** cannot actually run under the suite, while reporting as a
single ordinary failure. **CORRECTED 2026-09-24 13:50 — the earlier text of this section was wrong about the cause.** It said
the defect was "masked by the teardown, not fixed". That was inferred from a correlation (a disposable
database happened to be running when the failure was seen) and it is **falsified**: with the disposable
database up, the full suite passes (247 passed, 19 skipped); every pairwise ordering of the guarded test
after each other test file passes; nothing in `tests/` or `services/` rebinds the swisseph module or its
`julday`. **The failure has not reproduced, and its cause is unknown.** It is recorded as unknown, not as
masked.

What was done instead, because a recurrence must not be mysterious: `conftest.py` now carries
`assert_real_ephemeris()`, applied as an autouse guard to `test_wp3a_kernel.py`. It fails loudly, naming
finding F-31, if the swisseph object is not a real module or `swe.julday(2000,1,1,12.0)` is not
`2451545.0`. Two negative fixtures prove it can go red (a stubbed `julday`; a `MagicMock` module).
Separate weakness noted, not fixed: `EPHE_PATH` in `conftest.py` is an absolute path to this worktree.

**Do not re-open this item as a fix task.** If the original failure recurs, the guard will now say what
was stubbed, which is the missing evidence.

### 12.6 Owners are named — §9 is unchanged for you

O-1 is this run, already discharged for the nine packets. **O-2 is Kimi K3 at max effort, run by the
native's L3 session on the whole campaign once you report complete** — so keep writing
`REVIEW_REQUEST_*.md` per §9 and mark nothing `REVIEWED`. O-3 (the Kṣetra rulings 7/8/9 re-count) is
dispatched to an independent session and is **not yours**.

### 12.7 Still missing from §9's list

Write the five `REVIEW_REQUEST_*.md` files that do not exist yet: **§4 as a whole, §5, §7.A, §8.4,
§8.5** (the nine packet ones exist). Then §10's `REMAINDER_FINAL_REPORT_v1_0.md`.

### 12.8 Order of the remaining work

1. §8.5 G-10 — finish and commit what is already in the tree.
2. §12.5 the test-isolation fix (before anything touches a shared database).
3. §12.3 §4.13a–i and §12.4 §6.11.
4. §7.A the cutover kit + `WP10_REHEARSAL_v1_0.md` on the disposable DB.
5. §7.B tranche 1, then §7.C tranche 2, each step's evidence file before the next.
6. §12.7 the five review requests, then §10's final report.
7. **Tear down both disposable containers** — `gochara-wp6-disposable` and
   `gochara-remainder-disposable` are both still running; the brief requires them gone.
8. Push, and keep PR #2731 current.

Escalate to `ESCALATIONS.md`, never ask.

### 12.9 Upstream-fingerprint gap on the vedha/mūrti overlays — do this BEFORE the candidate build

Received from the Kṣetra stream (checklist C3) and verified at source on this branch.

`services/ka_vedha_gochara/writer.py` reads `bg_transit_rules` (`:106`) and copies each rule's
`classical_citation` **verbatim** (`:236`), but records **no fingerprint or digest of that upstream
input**. Consequence, measured by Kṣetra against production: the canonical chart's **132 `house_vedha`
rows are the 2026-09-07 build and still cite "BPHS Ch.29"** even though the L0 re-citation has moved
those rules to Phaladīpikā PG322/PG323, and the **24 sarvatobhadra rows cite Prasna Marga**. Nothing
detects the disagreement. This is the §N.8 earned-signal defect: the citation is asserted and no code
path could ever report it stale.

| # | task | exit gate |
|---|---|---|
| 12.9a | Add an upstream input fingerprint to the vedha and mūrti writers: a digest over the `bg_transit_rules` rows actually consumed (and the sarvatobhadra source for those rows), stored on the output row or its build record | a rebuild after any `bg_transit_rules` change produces a different fingerprint |
| 12.9b | Make staleness **detectable**: a check that fails when a served vedha/mūrti row's stored upstream fingerprint does not match the current `bg_transit_rules` state, naming the affected rows | the detector fires on the 132 stale rows as they stand today, and goes green only after a rebuild |
| 12.9c | **Gate the `'4.0'` candidate build on it** (§7.C step 6): the candidate must not be built on vedha rows whose fingerprint is stale, or a published generation carries refuted citations | step 6's evidence file records the fingerprint match before the build proceeds |
| 12.9d | Rename `platform/migrations/1086_nirmana_l0_gochara_g10_…` to an **`l1_`** basename. Its content is an L1 `ga_strength` change, the brief §8.5 calls G-10 L1, and the `l0_` prefix could route it to the wrong owner. It is unapplied, so this is a filename fix and engages no numbering rule — keep the number 1086 | basename says `l1_`; every reference updated; suite green |

**Do not** apply migration 1085 (the G-9 L0 data repair) to any shared database. It is file-only by
brief §8.4, and applying it belongs to an L0 owner the native has not named.


### 12.10 Migration 1085 must be rewritten as a delta, and a writer honesty bug blocks the rebuild

From the L0 repair session (PR #2727, `l0/vedha-and-frame-repair`), sent on the native's instruction.
Its production-state figures are **attributed, not verified here** (this session has no write access and
did not re-query); every claim about **files on this branch was verified at source** and all of them hold.

**A. `1085` as written would abort in production — verified in the file.** Its §5 G-8 sweep
(`1085:131-144`) does `RAISE EXCEPTION` if **any** `bg_transit_rules` row still cites `BPHS Ch.29`. The
L0 session reports **19 rows still cite it** (18 unfavourable + 1 favourable with no vedha pair),
deliberately left because they sit outside the spec's verified predicate. The whole migration, including
its `ADD COLUMN`, would roll back. The file's own §5 comment (`:133`) asserts "the spec's scope counts
exactly **39** in the live database"; production held **58** before the repair. That premise is wrong and
would have aborted on a freshly writer-seeded database too.

**B. Loosening the sweep is NOT the fix.** Verified in the file: the Mercury `ON CONFLICT ... DO UPDATE`
(`:102`) would overwrite the L0 session's Mercury row phala, citation and notes; the node-row `CASE`
(`:121`) would rewrite the six Rāhu/Ketu citations and notes. Both fields sit inside the **1078 content
hash** (frozen contracts 611/613, resealed by 1077/1078), so the integrity check would go red in
production. Anyone changing hashed content must ship a reseal computed against **production** state.

| # | task | exit gate |
|---|---|---|
| 12.10a | **Rewrite 1085 as a delta against the applied state.** Keep only: (1) `ADD COLUMN IF NOT EXISTS uncited_extension` and setting it TRUE on the six node rows, **guarded by their current `'UNSOURCED%'` citation**; (2) the śloka-17-sourced Mercury phala "Gain of wealth and birth of children", which the L0 session asked for by name over its own synthesized text after an independent reviewer flagged it. **Drop** the Venus section, the re-citation section, the Mercury INSERT and the BPHS sweep — all already applied upstream | the migration is idempotent against production as it stands, touches no hash-pinned content, and needs no reseal; if it must touch hashed content, it ships its own reseal computed against production |
| 12.10b | **Writer honesty bug — precondition of ANY L3 rebuild, including the `'4.0'` candidate.** `services/ka_vedha_gochara/writer.py:568` hardcodes `"uncited_extension": False` on every `house_vedha` row, and `_FETCH_VEDHA_RULES_SQL` (`:104-107`) selects `rule_type = 'favourable' AND vedha_house IS NOT NULL`, which **now includes the six node rows whose citation literally begins `UNSOURCED`**. A rebuild would therefore stamp uncited rows as machine-readably cited. That is §N.7 item 6 exactly: a favourable-sounding default standing in for a known negative. Make the field **read the row's actual citation state** (the new column, or derive it from an `'UNSOURCED%'` citation), never a literal | a test builds against a fixture containing an `UNSOURCED` rule row and asserts the output row carries `uncited_extension = true`; **§7.C step 6 does not run until this passes** |
| 12.10c | **Merge-order hygiene for PR #2731.** Both branches edit `ka_vedha_gochara/logic.py` in different hunks and `git merge-tree` shows a clean merge, per the L0 session. **Whoever merges second** must regenerate `nirmana-writer-digests.json`, re-admit the L3 pin (`nirmana_analysis_layer_pins.py --admit-successor`, baseline = `main` tip) and regenerate `capability_estate_census.json`, because those three fingerprint each other. New generations under decision `NATIVE-2026-09-24-L0-REPAIR-REPIN`: `l0:7d40f8c70640:64b8859fe692`, `l2:7d40f8c70640:dbbbb24c09cb`, `l3:7d40f8c70640:dfcf30d8b3d2`. Expect a re-admission after the L0 PR merges | CI green on the second merge without a manual pin fix |

**Unchanged and reinforced: do not apply 1085 to any shared database.** It is file-only by §8.4, and it
is now known to be wrong against the applied state rather than merely unverified.

### 12.11 COORDINATION — what the native's L3 session has already done in this worktree (read before starting §12.3 or §12.9)

The L3 session was asked to execute this delta directly and found, at 13:34, that this run is live in the same
worktree. To avoid collisions, ownership is split. **Do not redo, revert or re-derive the DONE items.**

| item | state | owner | commit / where |
|---|---|---|---|
| 12.10b writer honesty (UNSOURCED rows stamped cited) | **DONE** | L3 session | `4d8f83050` — also fixed `source_qualification` and the silent citation substitution; 18 tests |
| 12.5 test isolation | **DONE, two separate findings** | both | the L3 session added `assert_real_ephemeris()` (`eec8912e3`); this run independently found and fixed the cutover fixture dropping the WP6 ledger tables (`40ea32c7e`). The mean-node failure itself does **not reproduce**; its cause is recorded as unknown |
| 12.10a rewrite 1085 as a delta | **DONE — by RETIRING it, not rewriting** | L3 session | `7b86b8a08`, reasoning in `gochara_wp0_7/G9_DISPOSITION_v1_0.md`, escalation E-010. **1085 no longer exists. Do not restore it, and do not re-add 1085 or 1086 to step 4's `APPLY_SET`** — `assert_no_refused_migrations()` will exit 3 |
| 12.9d rename 1086 to an `l1_` basename | **DONE** | L3 session | `7b86b8a08` |
| **12.9a/b/c upstream fingerprint, detector, candidate-build gate** | **IN PROGRESS — CLAIMED by the L3 session** | L3 session | **Skip 12.9.** It lives in `services/ka_vedha_gochara/` and `scripts/kala_gochara_cutover/step06_candidate_build.py` |
| 12.3 tasks 4.13a–i | **OPEN — yours** | this run | the L3 session will not touch `engine.py`, `ledger.py`, `episodes.py`, `interval_solver.py`, `resolution_hierarchy.py`, `WP1_CONTRACTS.md` or migration 1081 |
| 12.4 binding B1–B7 adoption | **OPEN — yours** | this run | |
| 12.10c merge-order hygiene | **OPEN — yours**, at PR merge time | this run | |

**Migration numbers.** The L3 session's 12.9 needs **no migration** (the fingerprint rides the existing `detail`
jsonb). §12.3 needs one: take the lowest free number **after a fresh scan of every `origin/*` head across
both directories and a run of the MIG-1 guard** (`cd platform && npm run guard:migration-numbers`), not from
this file.

**Two facts the L3 session verified that change your plan:**
1. **Tranche 1 step 4 now applies 1080–1084 only.** Sheet A-2's literal step 4 names two migrations; 1082,
   1083 and 1084 exceed it and are flagged in E-010 as the native's to confirm. Treat step 4 as authorised
   for 1080/1081 until the native says otherwise, and apply the rest through the normal deploy pipeline.
2. **§12.10b is a hard precondition of step 6.** It is now satisfied by `4d8f83050`, but step 6 must also pass
   the 12.9 staleness gate, which the L3 session is adding.

Push order: fetch first; both writers commit by explicit path, never `git add -A`.

### 12.12 UPDATE 13:52 IST (originally mis-stamped 14:20; corrected) — §12.9 is DONE for both writers; 1084 changed; main is blocked by the L0 lane's pins

Supersedes the "IN PROGRESS" row for 12.9 in §12.11. **Skip §12.9 entirely.**

| item | state | commit / where |
|---|---|---|
| **12.9 upstream fingerprint, detector, candidate-build gate** | **DONE for vedha AND mūrti** | `bb7644ee4` (vedha), `b70115631` (mūrti + combined gate). Step 6 exits **7** if EITHER `kala_vedha_gochara` or `kala_moorti_nirnaya` is not fresh. Mūrti needed a nullable `upstream_fingerprint JSONB` column, **added to migration 1082 in place** (unapplied; no new number). Step 4's expected schema includes it |
| **migration 1084** | **CHANGED — the `ka_kshetra -> ka_gochara` edge is HELD OUT, do not re-add it** | `64bdc10da`. Reasons in the migration header and `REVIEW_REQUEST_K1.md`; `test_wp12_k1_edges.py` fails if it returns. The Kṣetra stream's executor applies or declines that edge, stating its consequence |
| **the merge of PR #2731** | **UNRESOLVED — do not assume it fails, and do not try to fix the pins yourself** | **Verified by the L3 session:** commit `7d40f8c70640`, referenced 12 times in main's `nirmana-analysis-layer-pins.json`, is on `origin/l0/vedha-and-frame-repair` only and is not an ancestor of main. The strategic session found that **54 of the 57** pinned commits are not ancestors of main, and that a bare local `--check` fails. **Contradicted by the strategic session's test:** `governance-gates` is SUCCESS on #2724, #2725 and #2726, all merged today, and on the open #2727, because the CI path derives its baseline from the PR or merge-group base SHA and validates a narrower set. The Kṣetra stream reported its own PR ejected twice from the queue on this test; that is **not reconciled** with those passes. An earlier version of this row said the merge WILL fail. That was this session relaying a stronger conclusion than it had verified, and is retracted. Treat the pins artifact as the L0 lane's and as hygiene unless the merge queue actually rejects PR #2731. |

**Test-database ports.** Three disposable databases may exist: WP6 on 55433, the run's WP10 on 55434, and a private
verification DB the L3 session starts and removes on 55435. The L3 session never uses 55434. Tear down whatever
remains at the end of your run, including the WP6 container the L3 session started.
