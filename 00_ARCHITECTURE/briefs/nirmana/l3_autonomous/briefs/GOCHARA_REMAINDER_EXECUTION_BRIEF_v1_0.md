---
artifact: GOCHARA_REMAINDER_EXECUTION_BRIEF
version: "1.0"
status: READY_TO_RUN
date: 2026-09-23
executes: "Everything left after WP0–WP7 (FINAL_REPORT_v1_0.md) under the native-ratified GOCHARA_RULING_SHEET_v2_0.md: point-1 residuals (rulings that still need code or evidence), point 2 (the eight receiving-contract packets), point 3 (WP9 overlays), point 4 (WP10 — prepared and rehearsed here; executed only when the flags in §0 are set), point 5 (loose ends)."
branch: "l3/gochara-autonomous-wp0-7 @ /Users/Dev/madhav-l3/gochara-wp0-7 — the same branch and worktree WP0–WP7 ran in; HEAD at brief time 367087bb7 (+ this brief's commit)"
authorization_flags:
  PRODUCTION_TRANCHE_1_AUTHORIZED: false   # WP10 runbook steps 0–5 (guards, drill, schema, registry). Native flips to true, in this file, before the run may touch any shared database.
  PRODUCTION_TRANCHE_2_AUTHORIZED: false   # WP10 steps 6–10 (candidate build, flip gates, flip, soak, second chart, N-11). Requires tranche 1's evidence file to exist and be green.
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
(H-1a/H-2/H-3/H-4/H-6), WP6 (ledger on a disposable DB; migrations **1075/1076** — renumbered, see §3),
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
  number after 1076 at brief time — re-scan at run time; four branches already collided on 1071–1074).
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
its reversal; step 4 apply/verify **1075/1076** (+ any migration this run adds) with an
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
| 8.1 | **N-18 push + PR.** Push `l3/gochara-autonomous-wp0-7`; open the PR to `main` (title `feat(l3-gochara): …`; body states: merge lands code only, no build runs under the 2026-08-21 standing order, R-1..R-6 take effect only at a resonance rebuild sequenced at WP10 step 6, migrations 1075/1076 unapplied to any shared DB, the four-branch number collision and its resolution). End the body with the attribution line the repo's PR convention uses | PR URL recorded in the final report |
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
