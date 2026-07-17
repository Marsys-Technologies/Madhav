---
artifact: BIND_D-3.md
wave: D-3 — Kāla Taraṅga + Three-Lock
type: BINDER FINDINGS RECORD (CONDUCTOR_PROTOCOL §2 step 1 OPEN)
status: BOUND
bound_at: 2026-07-17T22:20+05:30 IST
binder_model: Fable (per CONDUCTOR_PROTOCOL §1 role table)
conductor_model: Sonnet
native_directive: D-3 OPEN — GO (2026-07-17), merge #599 on green then open under standing protocol
---

# BIND_D-3 — Binder findings

All findings below are the Binder's fresh live re-verification (Fable, MCP probes against the
deployed `marsys-jis-direct` connector + `gcloud`/git + direct code reads, 2026-07-17 ~22:20 IST) —
NOT a rubber-stamp of `PRE_D3_READINESS.md`'s pre-work pass (which explicitly stated it is "the
gate, not the open"). Agreement with the readiness pass is noted where it holds; nothing here is
trusted from cache. Binder pass was read-only per protocol §1.1 — no files written by the Binder
agent itself; this record and the brief's status stamp are the conductor's transcription.

## §B slot verdicts (BRIEF_D3 §B, re-verified fresh)

**B-1 — Mechanism-object interface (D-2 as-shipped) — HOLDS.**
`ganita_vichara_get(482012f1, family=valence_pass)`: 1,595 rows live, `formula_version:
valence_pass_v2_doctrine`, build `b84c3797-b64a-4956-a431-5f4ccdf9ee55`. Each row carries a full
`value_jsonb` mechanism object (`link_kind`, `link_type`, `matrix_key`, `target_house`,
`actor_classes`, `actor_primary_class`, `stored_functional_class_bphs`) + `constituent_fact_ids` +
BPHS Ch.3/Ch.34 citation. `judgment_query(wealth, v3)` serves `affliction_mechanisms` as named
valenced objects with resolvable grounding (472 facts, `resolvable:true`). PROMISE-lock inputs
(T-3) are fully consumable.

**B-2 — Sidecar status — HOLDS, GREEN.** T-1-only fallback NOT needed.
`kala_temporal_bundle(482012f1)` → `sidecar_available: true`. `ref_planet_transit_get(Jupiter,
2026-07)` → `ok:true`, 31 real ephemeris rows, no 401. `ref_aspects_at_time_get(2026-07-17)` →
`ok:true`, real aspect row (Ketu-Rahu opposition, orb 0). T-2/T-5 unblocked. Independently
confirmed twice this session (conductor gate-zero check + Binder re-check).

**B-3 — Scorable-LEL list + train/test split — HOLDS; counts reconciled.**
`lel_query(482012f1)`: `total_count = 57`, LEL v1.7. **Server caps a page at 50 regardless of
`limit`** — T-0's harness must page to exhaustion (a second 2025-07-01 event was hidden behind the
page-1 cut). Both T-0 anchors present and dated: `2010-07-01 finance/family_windfall`
(`bd7f5711`), `2025-05-15 loss/financial_deception` (`d81fae4e`).
- **Split:** TRAIN = 36 events with `event_date < 2020-01-01` (matches brief exactly). TEST = 21
  events 2020-01-15 → 2026-04-17. **Scorable ≈ 40** = 57 minus birth anchor minus ~16 non-discrete
  rows (multi-year arcs / ongoing-status events with defaulted mid-year dates that can't support a
  ±45d proximity test).
- **T-0 action item:** finalize the exact scorable list under one stated rule — proposed: *scorable
  = discrete-onset events with month-or-better date precision* — and publish the exclusion list in
  the harness so ~40 is derived, not asserted.

**B-4 — Kernel admission order (Adjudicator-engineering proposal, ranked).**
v1 kernel (fixed by §F1): (1) dasha-capability steps → (2) slow-transit pulses → (3) SAV potency.
Staged admissions thereafter, one at a time, kept only on blind-battery improvement: (4) kakṣyā
sub-windows (T-1) · (5) period-lord relational algebra + tāra-from-MD-lord (T-4) · (6) Guru-Śani
double-transit (T-5) · (7) gochara vedha filter (T-5, CR-102) · (8) signed suppressive currents /
papa-kartari (T-5, CR-89) · (9) saham currents (T-5) · (10) multi-system concordance multiplier
(T-4) · (11) repair-or-retire school_consensus + stub predicates, last.
Rationale: rank by expected retrodiction lift × input-readiness × classical load-bearing weight.
Dasha spine first — it's the only current with direct LEL alignment already served (B8's
`ganita_dasha_lord_capability_get` live, 9 lords, deterministic tiers) and the LEL corpus is
dasha-annotated. Slow transits second — periodicity matches the ±45d event scale, sidecar green.
SAV third — facts shipped in D-1.5b, near-zero compute. Amplifiers/refiners admitted before
*subtractive* currents (vedha, suppression) so each filter's hit-rate effect is measured against a
stable base superposition, not confounded with it. Concordance multiplier calibrated once the
spine's score is stable. Stubs last — unknown expected lift by construction.

**B-5 — Rollback pin + prior batteries — recorded, GREEN, no drift.**
Pin (live `gcloud describe`, this pass):
- `amjis-web` → `e8b1047f56a06591352dbb748373a59b6dea5715` (origin/main HEAD, PR #599 merge)
- `amjis-mcp` → `8c3b21a9afa88934e621a9d525f460a72ed5ca52` (D-2 close merge #598)
- `amjis-sidecar` → `6487694fe70635e12c84746443ee2359c51b447d` (PR #597 merge)
- `brahma-pipeline` job → `6487694fe70635e12c84746443ee2359c51b447d`
All four SHAs verified contained in `origin/main`. Skew is docs-only trailing commits — expected.
**Abhisek build_id = `b84c3797-b64a-4956-a431-5f4ccdf9ee55`** (from `ganita_vichara_get`
provenance; `judgment_query` chart_header confirms Mercury MD / Saturn AD current).

Prior-battery spot check (D-2 §G, live this pass) — **zero new reds**: G0-1 dhana_yoga_2_5_9_11
fired 1.0218 ✓ · G0-2(half) wealth verdict varga_term=0 ✓ · G0-3 NBRY bhanga_active:true, both
Venus+Saturn @D9 rules fired, BPHS Ch.39 cited ✓ · G0-4 affliction_mechanisms Rahu-on-2nd net
−0.50 ✓ · G0-6 Ketu watch/shadbala 0.625 ✓ · completeness receipt timing_anchored:true ✓ ·
DEFECT-001 orphan 0% (0/17) ✓. Not re-run this pass (no contradicting evidence found anywhere):
G0-5 leverage_index, full census sweep, FORENSIC 7/7. **Gate Ś #8 residual unchanged, not worse**
(`yoga_activation_by_dasha` = 15 rows, `undated_activation_count: 15` — same dispositioned residual
REPORT_D-2 recorded, folded into T-6 per BRIEF_D3 §F0/§F1). **Protocol §8.8(i) trigger: NOT hit —
no prior battery has gone red at open.**

## DR ratifications (native-ratified 2026-07-17, D-3 open directive)

Recorded in `DISAGREEMENT_REGISTER_v1_0.md` as DIS.023/024/025 (campaign refs DR-10/11/12):

- **DR-10 (DIS.023)** — within-period peak model: pratyantar-lord decomposition is the classical
  default; midpoint-triangle DEPRECATED (never served bare); every served peak carries
  `peak_basis` provenance (`pratyantar_lord | midpoint_triangle | transit_kernel`); transit-kernel
  supersedes both where computed. Binding for T-2/T-3/T-6.
- **DR-11 (DIS.024)** — T-0 thresholds v1: ±45d window / top-decile salience / ≥50% blind-battery
  hit-rate vs shuffled-birth control. DR-revisable only, never silently retuned. Anti-gaming rule
  binding: no statistical gate greens on the primary runner alone — independent fresh-context
  (Opus) reproduction required.
- **DR-12 (DIS.025)** — D-4 peak-model adjudication hook: D-4's battery MUST score all three peak
  models against the LEL corpus; the data retires the loser. Forward-binding, no D-3 action —
  D-4's Binder inherits this at its own bind.

## Carried-item dispositions

**1. Orchestrator run-rollup race — diagnosis CONFIRMED current; §N.2 STOP NOT triggered.**
Fresh code read (`platform/src/app/api/cockpit/watchdog/route.ts` lines 57-69,
`pipeline/orchestrator/runner.py` ~675-733, `asset_runner.py` ~174/241/640) confirms the gap is
unchanged: the `build_runs.state='completed'` rollup commit is separate and later than per-asset
`state='lit'` commits; process death in that window strands the rollup at `running` while every
asset carries real rows; the watchdog blind-marks such runs `failed` with no child-state
reconciliation; run-start orphan cleanup resets stuck assets but never a stuck prior rollup.
`b13640d1` (on main) is confirmed to be the *per-asset* fix only — it does not cover the rollup
gap. **§N.2 ruling: does NOT trigger the STOP** — `build_runs.state` is run-machinery-owned, no
`WriterBase` contract element changes (precedent: `b13640d1` itself patched run machinery pre-D-2
without a PARK). **First-agenda D-3 lane, platform-owned:** (A) run-start rollup reconciliation
from `build_run_assets` children under the chart advisory lock; (B) watchdog reconcile-to-truth
(a `running` run >30min with no child still building/queued → recompute completed/failed from
children) instead of blind-fail. Both idempotent; verifiable via 2-asset fault-injection repro +
DB-only unit tests, no whole-chart rebuild needed.

**2. kala_avadhi hollow timeline — CONFIRMED live; disposition: scoped rebuild first, T-6 decides
retire-vs-populate with the kernel in hand if the rebuild doesn't resolve it.**
Fresh probe: `kala_temporal_bundle(482012f1, 2026-07..12)` → `timeline_count:0,
convergence_count:0, active_dasha:null, kala_readiness.score:null` — while `chart_dashas` serves
Mercury MD 2010-08-18→2027-08-18 (two_pass_verified) and `kala_activation` IS populated
(`kala_windows_get`: activation_count 10, though `forward_window_count:0` — stale forward-
classification, separately flagged). Hollow is asset-specific to
kala_avadhi/kala_convergence/kala_darshana.
**Disposition (Binder recommendation, adopted):** (a) scoped rebuild at open —
`scope=asset_set` targeting `ka_avadhi` + its DAG dependents (`kala_convergence`, `kala_darshana`
per `asset_registry.depends_on`), Cloud Run job path, minimal-cascade-compliant, minutes. Rationale:
`kala_temporal_bundle` is a served surface today (§F2 protects prior-gate surface semantics) —
retiring it pre-emptively is a scope decision made before the kernel exists. The rebuild doubles as
diagnostic: if a clean `lit` build still yields 0 rows, that's a writer defect with evidence, and
*then* option (b) — T-6 serves `timing_hooks` directly from the Taraṅga service (T-2) and
kala_avadhi retires-with-evidence — becomes the earned disposition inside T-6, not assumed now.
**Promise-ledger row (T-6):** "kala_temporal_bundle timeline non-hollow on 482012f1 OR kala_avadhi
retired-with-evidence."
**Status at bind: NOT yet executed** — the scoped rebuild is a pre-spawn action for the conductor
to dispatch before T-1/T-2 lanes need `kala_temporal_bundle` populated, flagged here rather than
run silently inside the Binder pass (Binder is read-only; rebuild dispatch is a conductor action).

## Promise ledger carry-forward (Definition-of-DONE, BRIEF_D3 §F3)

Every ledger row below must resolve GREEN+evidence or PARKED+evidence+owner at D-3 close
(`REPORT_D-3.md`); no ledger row → bind failure would have applied (none found — all rows land):
1. T-0: three retrodiction checks green + anti-gaming pass (DR-11).
2. T-1: SAV/BAV transit damp/amplify type specimens (SAV-10th=27 damps career, SAV-7th=34 amplifies
   partnership) + kakṣyā ~3.4-day windows served.
3. T-2: `activation()`/`curve()` stateless service live; evidence write-through on citation/L5
   consumption only.
4. T-3: shared kernel extracted; PROMISE lock (salience × functional valence × varga-ratification ×
   NBRY-deferral × mechanism graph-weight) computable — kills CR-88.
5. T-4: PERMISSION lock — 7-system concordance as real gate multiplier + period-lord relational
   algebra + full dasha-lord capability consumed.
6. T-5: TRIGGER lock — 12 currents + signed suppressive currents (kills CR-89 additive-only) +
   Guru-Śani double-transit + saham currents + gochara vedha filter (CR-102) + school_consensus
   repair-or-retire.
7. T-6: `timing_hooks` kernel-fed in the TRIMMED shape (`kala_activations_trimmed` preserved,
   verified live this pass); `kala_windows_get`/`get_temporal_windows`/`kala_priority_ranking_get`
   re-pointed; pact TRIGGER stage wired; phala wealth anchors fed (CR-19/66); Gate Ś #8 closes via
   `dasha_eligibility_rule` (yoga_activation_by_dasha dated for eligible signals); kala_avadhi
   row (above).
8. Peak-basis provenance (DR-10) present on every served peak.
9. §G final proof: 2027-2034 Ketu-MD lean stretch + 2034 Venus-MD activation served, dated,
   mechanism-attributed — not hand-derived.

## Verdict

**HOLDS — D-3 stamped BOUND.** All five §B slots resolve on fresh live evidence. Two conditions
carried forward: (1) scoped `ka_avadhi`-cascade rebuild to be dispatched by the conductor before
T-1/T-2 need it (or T-6 decides retire-with-evidence if the rebuild doesn't resolve the hollow);
(2) T-0 harness must page `lel_query` to exhaustion (50-row server cap) and publish its scorable-
list exclusion rule. No §8.8(i) regression trigger. No FROZEN-contract STOP triggered by the B.3
disposition.

---
*BIND_D-3.md — wave stamped BOUND 2026-07-17. Conductor proceeds to SPAWN (CONDUCTOR_PROTOCOL §2
step 2) only after native review of this record, per this session's pause-at-first-milestone
instruction.*
