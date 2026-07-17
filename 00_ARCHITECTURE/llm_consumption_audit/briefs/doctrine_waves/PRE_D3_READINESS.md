---
artifact: PRE_D3_READINESS.md
wave_gate: D-2 → D-3
status: READINESS-PASS (gate to D-3 open; NOT the open)
produced: 2026-07-17
authority: native pre-D-3 readiness directive (2026-07-17)
---

# Pre-D-3 Readiness Pass — the gate to D-3 (not the open)

Executed per the native's pre-D-3 readiness directive. Constraints honored: no D-3 lane code, no
schema migrations, no rebuilds. Verification, documentation, doctrine-drafting, staging only.

## A — Prerequisite verification (hard gates — evidence)

| # | Gate | Result | Evidence (live, 2026-07-17) |
|---|---|---|---|
| A.1 | Track-2 sidecar re-check on deployed connector | ✅ **PASS** | `ref_planet_transit_get(Jupiter, 2026-07)` → `ok:true`, 31 rows, **no 401**. `kala_temporal_bundle(482012f1)` → `provenance_envelope.sidecar_available: true`. Track-2 UP — no restore needed. |
| A.1-obs | Kāla timeline population | ⚠ observe | `kala_temporal_bundle(482012f1, 2026-07..12)` returns `timeline_count:0, active_dasha:null` — the L3 `kala_avadhi` windows appear **unpopulated for this chart** post-D-2 (sidecar healthy, but the L3 temporal rows aren't there). Flagged for E.1 (does a D-3 T-lane depend on kala_avadhi being populated?). |
| A.2 | B-2 ashtakavarga handoff (T-1's first input) | ✅ **PASS** | On `482012f1`: `ashtakavarga_bindu_sign` 96 (`01bf359bf27a02a0`), `ashtakavarga_trikona_shodhana` 84 (`0366cd14b6203915`), `ashtakavarga_ekadhipathya_shodhana` 84 (`02fa93325ef1f703`), `ashtakavarga_kakshya_boundary` 24 (`063686f735896de8`), `ashtakavarga_pinda_{sarva,bhinna,raasi,sodhita}` 8 each (`09f908c78150d84a`…). SAV/BAV-by-sign + śodhana + piṇḍas + kakṣyā all serve. **T-1 input note:** the connector's `category='ashtakavarga'` (bare) returns 0 — the specific category names must be used; T-1's input contract should name them. |
| A.3 | D-2 §G gate regression snapshot (D-3 entry baseline) | ✅ archived | See §A.3 below — the "zero new reds vs baseline" reference for D-3. |

### §A.3 — D-2 §G gate regression snapshot (D-3 entry baseline)

Frozen state at D-2 close (build `b84c3797`, deployed `8c3b21a9`, health tools=120). This is the
reference D-3 must show **zero new reds against**:

- **§G.1 master-acceptance: 6/6** single-pass, Opus-verified live (G0-1 dhana firings 1.02 · G0-2 varga_ratification_divergence SAT + D2 varga_term=0 · G0-3 NBRY bhanga_active grounds both Ven+Sat · G0-4 affliction_mechanism Rahu-on-2nd −0.50 · G0-5 leverage_index VEN 3.94 · G0-6 dasha_lord_capability Ketu watch/0.625).
- **§G.3 career probe: PASS** (adverse-layer generalization).
- **G0-4 amended + anti-overcorrection C1/C2/C3: PASS** (Rahu-H2 mixed −0.50; Ven/Jup-H9 strong_benefic; valence_pass distribution 580/551/406/58, no collapse).
- **Census 135 = baseline.** DEFECT-001 orphan 0%; signature_tier 84.6/12.4/2.4/0.7 (non-degenerate).
- **Gate-B live; Gate-Ś honesty live; Gate Ś #8** the sole dispositioned residual (`yoga_activation_by_dasha` 15/15 undated).
- **Ledger:** 52 KEPT / 1 BROKEN-w-evidence / 3 DEFERRED-w-pointer / 0 unmarked.

## B — Carried-items intake (D-3 opening agenda)

### B.3 — Orchestrator state-commit race (D-1.6 carry; D-2 first-agenda item)

**Diagnosed (Opus, read-only). Verdict: fix does NOT require a frozen-contract change — the native's
§N.2 STOP condition is NOT triggered.** Root cause: a run-**rollup** finalization gap — the
`build_runs.state='completed'` commit (`runner.py:733`, main connection) is a *separate, later* commit
than the per-asset `state='lit'` commits (`asset_runner.py:646`, worker connections). Process death in
that window (Cloud Run SIGTERM/OOM/eviction, most exposed on long whole-chart 61-asset builds) strands
the rollup at `running` while every asset carries real rows. Compounded by: (a) run-start orphan
cleanup (`runner.py:675-699`) never reconciles a stuck prior rollup; (b) the watchdog backstop
(`platform/src/app/api/cockpit/watchdog/route.ts:57-69`) blind-marks such runs `failed` instead of
reconciling from child asset states. The `bo_samvada`/digest count-vs-status confusion is the SAME
defect on one asset (§N.4 cockpit-truth split surfaced by the race).

`build_runs.state` is orchestrator/run-machinery-owned — NOT part of the WriterBase contract (no writer
reads/writes it). **Proposed fix (D-3 first-agenda, platform-owned, no §N.2 escalation):** (A) add
run-start rollup reconciliation (recompute prior stuck `running` rollups from `build_run_assets`
children under the chart advisory lock); (B) the load-bearing fix — make the watchdog **reconcile to
truth**: a `running` run >30min with no child still `building/queued` → recompute `completed`/`failed`
from children (mirroring `execute_run`), instead of blind-failing. Both idempotent. Verifiable via a
2-asset fault-injection repro + DB-only unit tests — no whole-chart rebuild needed.

### B.1 / B.2 — carried findings + Gate Ś #8 subsume-check

**B.1 — the 4 D-2 gate findings, each a named D-3 opening-agenda entry (register pointers):**

| # | Finding | D-3 agenda entry | maps to |
|---|---|---|---|
| 1 | `leverage_index subject=venus` false-empty (code is `VEN`) + ambiguous `empty_reason` | Alias natural-language planet names in `subject`, OR sharpen `empty_reason` to "unrecognized subject code, expected {SUN,MOO,...}". B.10-adjacent: an ambiguous empty must never read as a negative finding. | REPORT_D-2 §6.1 (open new CR at D-3 or file under consumability bucket) |
| 2 | C1 nodal-exaltation offset (Rahu-H2 −0.50) judgment-surface-only | Serve the tenancy-valence adjustment on the granular `ganita_vichara_get` surface so raw + synthesized surfaces agree. Residual Part-A-granular gap now that Part B synthesis is fixed. | REPORT_D-2 §6.2 (VAL-ROOT Part-A granular) |
| 3 | `canonical_faces.json` missing 3 cycle-2 tools | Add `plan_retrieval` / `scan_fetch_signals` / `reading_notes_get` with alias bookkeeping so census (138 vs 135) + alias-check stay accurate. Low-effort "down" dial. | REPORT_D-2 §5 row 22, §6.3 |
| 4 | `judgment_query` v3 oversize (73KB→23KB, still >12KB self-flag) | Continue §N.6 `response_budget.ts` trim (S-5 class); **re-scope after T-6 lands** since kernel-fed `timing_hooks` reshapes the payload. | REPORT_D-2 §6.4 |

**B.2 — Gate Ś #8 subsume-check → FOLD-INTO-T-6 (do NOT carry separately).** BRIEF_D3 §F0/§F1
**already names this exact residual in T-6's scope**: *"yoga-activation dating (CR-12/48) via kernel
— INCLUDING the Gate Ś #8 parked yoga-signal-class `dasha_eligibility_rule` residual"*, framed
*"squarely inside T-6's scope: D-3 should absorb it, not rediscover it."* Root cause: the 74/`482012f1`
`yoga_activation_by_dasha` rows are birth-moment catalog facts lacking a real natal constituent_lord
for dasha matching — a T-6 serving/joining concern once the kernel + lord-relational algebra exist.
**Recommendation:** the D-3 Binder's promise ledger carries an explicit T-6 row — "Gate Ś #8 closes:
`yoga_activation_by_dasha` rows carry non-null `activation_predicted_dates` for eligible signals,
remainder honestly null via `dasha_eligibility_rule` gate" — so it doesn't silently fall through
T-6's broader scope. (Sequencing caveat: T-6 is the LAST admission-loop lane, so this closes on
D-3's final serving pass — acceptable.)

## C — Doctrine pre-rulings (DR-CANDIDATES — draft for native ratification at bind; NOT auto-adjudicated)

> These are drafted candidates only. They are **not** adjudicated DISAGREEMENT_REGISTER rows and do
> not bind until the native ratifies them at D-3 bind.

### DR-CANDIDATE C.1 — Within-period peak model (pratyantar-lord default; midpoint-triangle deprecated)

**Proposed ruling.** The classical default basis for a within-period *peak* becomes **pratyantar-lord
(sub-sub-period) decomposition** — the peak is the strongest pratyantar window within the antardaśā,
by classical lord-strength, not an arithmetic construct. The legacy **midpoint-triangle**
(`period_peak = arithmetic midpoint of the AD`, with a `0.6 / 1.0 / 0.4` rise/peak/taper envelope) is
**DEPRECATED**: it must **never serve as a bare peak date**. Any served peak **must carry
`peak_basis` provenance** (`pratyantar_lord` | `midpoint_triangle` | `transit_kernel`). Where the D-3
**transit-kernel** computes a peak, it **supersedes** both.

**482012f1 evidence (why the midpoint is wrong here).** The current Saturn-AD (2024-12-08 → 2027-08-18)
midpoint-triangle puts `period_peak ≈ 2026-04-13`. But the classically strongest sub-window is the
**Saturn–Jupiter pratyantar (≈2027-04-09 → 2027-08-18)** — which lands in the midpoint-triangle's
**0.4 taper** (i.e. the arithmetic model scores the true peak as a *fading tail*). The midpoint model
inverts the classical peak on a live chart — the concrete falsifier motivating the deprecation.

### DR-CANDIDATE C.2 — T-0 threshold gates (v1)

**Proposed ruling.** The T-0 harness v1 statistical gates are: **±45 days** window tolerance ·
**top-decile** salience placement · **≥50% blind-battery hit-rate**. These are v1 gates, **revisable
only by a recorded DR** (never silently retuned). The **anti-gaming rule is restated as binding:** a
statistical gate **never greens on the primary runner alone** — an independent fresh-context runner
must reproduce the hit-rate against live payloads (the D-2 §G.1 Opus-verifier discipline, generalized
to T-0's statistical battery).

### DR-CANDIDATE C.3 — Peak-model adjudication hook for D-4

**Proposed ruling (register now, fires at D-4).** The D-4 retrodiction battery **must score
midpoint-triangle vs pratyantar-lord vs transit-kernel as competing peak models** against the LEL
outcome corpus — the **data retires the loser**. Neither doctrine nor engineering decides the peak
model by opinion; the empirical retrodiction score does. This hook is registered at D-3 so D-4's
binder inherits it as a mandatory battery dimension.

## D — Hygiene before bind

| # | Check | Result |
|---|---|---|
| D.3 | Worktrees clean | ✅ 8 → **1** (main only); 7 D-2 lane worktrees pruned. Merged D-2 branches deletion in progress (background). |
| D.3 | Deployed SHA == main | ✅ main `8c3b21a9` (REPORT_D-2 merged); doc-string fix deploying serving-only. |
| D.3 | Live tools == REGISTERED_TOOL_COUNT | ✅ health `tools:120` == `REGISTERED_TOOL_COUNT = 120`. |
| D.1 | 4-surface consistency (STATE/REPORT/CURRENT_STATE/CLAUDECODE_BRIEF) | ⚠→✅ **1 contradiction, FIXED.** STATE_D-2 (`wave_status:CLOSED`, `gate_battery.status:PASS`), REPORT_D-2 (`status:CLOSED, gate:PASS`), CURRENT_STATE §2 (`current_wave=D-3`, D-2 CLOSED) all agree. **`CLAUDECODE_BRIEF.md:17` was STALE** (`current_wave: D-2`) → corrected to D-3 this pass. |
| D.2 | Register sync + CR-59 correction | ✅ **3 rows corrected this pass:** MARSYS_DEFECT_GAP VAL-ROOT `OPEN (Step-2 in flight)` → CLOSED (DR-9/DIS.022, REPORT_D-2 §3/§7); POST_REMEDIATION CR-54 `OPEN-ELEVATED` → CLOSED (DR-9, REPORT_D-2 §3/§4); CR-59 text corrected — detection is LIVE (PR #596/D-1.6), residual = ranking/routing surfacing, not detector blindness. |
| D.4 | Baseline continuity (post-D-2 diff sibling + comparison protocol staged) | ✅ `REPORT_D-2.md §4` IS the post-D-2 diff sibling to `BASELINE_WEALTH_READING_PRE_D2_v1_0.md §4`. D-3 close re-runs the verbatim question *"Full financial analysis of 482012f1: when does the wealth promise activate, and what intervention secures or advances it?"* — deltas to capture: (1) served forward Venus-MD window with NBRY-deferral sub-timing, (2) transit-derived (non-midpoint) peaks — see DR-candidate C.1, (3) suppression-adjusted windows. |

## E — Binder pre-work (allowed; NOT the wave open)

**E.1 — BIND_D-3 §B re-verified fresh against the live estate (Opus, probe-not-trust per the D-2 lesson).**
BRIEF_D3 (v1.3 FROZEN) §B declares 5 bind-slots:

| §B | binding | verdict | live evidence |
|---|---|---|---|
| B-1 | Mechanism-object interface → PROMISE-lock inputs | **HOLDS** | `ganita_vichara_get(valence_pass)` 1595 rows, `valence_pass_v2_doctrine`, mechanism `value_jsonb` + fact_ids; `affliction_mechanisms` objects live |
| B-2 | Sidecar status (expect GREEN since D-1.6 S-6) | **HOLDS — GREEN** | `ref_aspects_at_time_get`/`ref_planet_transit_get` real ephemeris (retro flip 2026-07-27); `sidecar_available:true`. T-1-only fallback NOT needed |
| B-3 | Scorable-LEL list + train/test split | **HOLDS** | `lel_query` `total_count:57`, v1.7; both T-0 anchors present + dated (2010-07 windfall, 2025-05 deception). Split counts = Binder finalizes at open |
| B-4 | Current-inventory admission order | defer (by design) | Adjudicator bind-time judgment; ranking inputs exist |
| B-5 | Rollback pin + prior batteries green | out-of-band | Binder sets pin + re-runs prior Gate A/B/Ś/D-2 batteries at open |

**Two D-2-induced items for the Binder:**
1. **T-6 must honor the trimmed `timing_hooks` shape.** `judgment_query.timing_hooks.kala_activations` is now **deduped-to-distinct-windows with per-row JSONB blobs dropped** (`kala_activations_trimmed` flag). T-6 (Serving) re-feeds `timing_hooks` from the kernel — it MUST emit that trimmed shape, not raw fat `kala_activation` rows, or it regresses the D-2 budget contract (`response_still_over_12kb_budget_after_full_trim`). Ledger row for T-6.
2. **`kala_avadhi` prerequisite gap.** `kala_temporal_bundle(482012f1)` serves a **hollow timeline** (`timeline_count:0, active_dasha:null`) though `chart_dashas` has Mercury MD active — `kala_avadhi`/`kala_convergence`/`kala_darshana` are stale/unbuilt for this chart post-D-2. **Non-blocking for §G** (which reads the *populated* `kala_activation` surface — `kala_windows_get` → 10 activations + `kala_activation_predicates` rows), **load-bearing for T-6 servability.** Binder must probe rows, not assume; put "L3 kala_avadhi rebuild-or-re-point" on the T-6 ledger. (Related: `kala_windows_get` `forward_window_count:0` for a 2027 window — forward-classification keyed to a stale last-build date; rebuild-freshness check at open.)

**Note — reconcile B.3 vs §F3:** BRIEF_D3 §F3 references a state-commit-race fix at `b13640d1` (the D-1.6 *per-asset* patch — `_data_rows_present`/`_guard_state_write`). The B.3 diagnosis above shows the *per-asset* write was patched there, but the **run-rollup** finalization gap is a separate residual still open — the Binder should confirm which the §F3 pin actually covers.

**E.2 — Lane-order sanity: COHERENT, no D-2 inversion.** T-0 harness first (retrodiction gate; inputs = LEL 57 + valence curves). T-1 (sidecar-independent, AV facts 96 live) before T-2 (sidecar-dependent, unblocked since B-2 GREEN). D-2 mechanism-object shape is consumed by T-3/T-5 (after T-1/T-2) and the trimmed `timing_hooks` by T-6 (last) — no earlier lane depends on a later lane's D-2 output.

---

*Readiness pass — pauses for native go on the D-3 open. This is the gate, not the open.*
