---
artifact: BIND_D-3_CYCLE2.md
wave: D-3 — Kāla Taraṅga + Three-Lock
cycle: 2
type: BINDER FINDINGS RECORD (CONDUCTOR_PROTOCOL §2 step 1 OPEN, cycle-2 re-open)
status: BOUND
bound_at: 2026-07-18T03:00+05:30 IST
binder_model: Fable
conductor_model: Sonnet
native_directive: D-3 KERNEL CYCLE — cycle-2. Proceed under CONDUCTOR_PROTOCOL.md §2 (2026-07-18)
---

# BIND_D-3_CYCLE2 — Binder findings (cycle-2 open)

Cycle-1 (T-0 harness, T-1 aṣṭakavarga/kakṣyā, kala_temporal.ts hotfix) is CLOSED and deployed —
see `STATE_D-3.md` for the full record. This cycle builds the transit kernel (T-2/T-3), runs the
kernel-admission loop (T-4/T-5), wires serving (T-6), and submits to the §G retrodiction gate —
the empirical crux of D-3. All findings below are fresh live re-verification (Fable, MCP probes
against the deployed connector + `gcloud`, 2026-07-18 ~03:00 IST), not cache. Binder pass was
read-only per protocol §1.1 — no files written by the Binder agent; this record is the
conductor's transcription.

## Gate-zero (re-asserted by conductor before Binder dispatch)
`kala_temporal_bundle(482012f1)` → `sidecar_available: true`. `ref_planet_transit_get(Saturn,
2026-07-18..25)` → `ok:true`, 8 real ephemeris rows, no 401. GREEN.

## §B slot verdicts (cycle-2 re-verification)

**B-1 — Mechanism-object interface — HOLDS.** `ganita_vichara_get` live: 1,595 rows unchanged,
`formula_version: valence_pass_v2_doctrine`, build `b84c3797`. T-3 PROMISE-lock inputs intact.

**B-2 — Sidecar status — HOLDS.** Corroborated independently by the Binder's own probe
(`sidecar_available: true`) in addition to the conductor's gate-zero check above.

**B-3 — LEL train/test split integrity — HOLDS. 57 total / 36 train / 21 test, boundary
2020-01-01.** Verified by count only, per the cycle-2 no-leakage constraint — test-split event
*contents* were not read or summarized. Both T-0 anchor events re-confirmed present by ID/date
only (`bd7f5711` 2010-07-01 train, `d81fae4e` 2025-05-15 test). **One correction to the cycle-1
bind record:** the test span's observed start is 2021-01-15, not 2020-01-15 as BIND_D-3.md
recorded — a one-character transcription slip in cycle-1 (counts are byte-identical, 21/21, so
this is not a corpus change). Structural note: zero test events fall in calendar-year 2020 — no
scoring opportunity that year, does not affect the 36/21 boundary. Carry-forwards from cycle-1
still apply: 50-row page cap (page to exhaustion), ~40 scorable derived via the published
exclusion rule, not asserted.

**B-4 — Kernel admission order — UNCHANGED, strengthened by cycle-1 delivery.** Order stands:
dasha-capability steps → slow-transit pulses → SAV potency → kakṣyā → relational algebra →
Guru-Śani double-transit → gochara vedha → signed suppressive currents → saham → concordance
multiplier → stub predicates. Cycle-1 shipped SAV/kakṣyā as a live capability (T-1) and proved the
dasha spine's serving face (the hotfix) — both slots are now wiring steps into the kernel, not
builds, without changing their rank (admission order tracks expected retrodiction lift, not
implementation readiness). **Two T-0 flag-forwards the kernel/admission-loop must account for**
before scoring deltas: (1) the `top_decile_fraction=1.0` sparse-curve artifact, (2) the `localMax`
grid tie-break making `peak_lag_days` uninformative — both would contaminate "keep only on
blind-battery improvement" measurements if left in the scorer unaddressed. Kakṣyā live-serving via
the sidecar transit endpoint remains Phase-2-unproven (T-1 receipt note) — gate runner exercises
it post-deploy before kakṣyā's kernel-admission is measured.

**B-5 — Cycle-2 rollback pin (distinct from cycle-1's).**
- `amjis-web` → `11377530892799afd8015d3ee9b6ec68efeb0c0d` (PR #602, cycle-1 deploy)
- `amjis-mcp` → `11377530892799afd8015d3ee9b6ec68efeb0c0d`
- `amjis-sidecar` → `b536e13b63168839187692b50f94a3d334f5ee1b`
- `brahma-build-pipeline-job` → `b536e13b63168839187692b50f94a3d334f5ee1b`
- Abhisek build_id → `b84c3797-b64a-4956-a431-5f4ccdf9ee55` (unchanged — cycle-1 correctly ruled no
  rebuild needed). Current MD/AD: Mercury MD / Saturn AD, confirmed live via `judgment_query`.

## Estate drift spot-checks — NO DRIFT (3 live checks)
1. **kala_temporal_bundle non-hollow** — `timeline_count:7`, active_dasha resolved, readiness
   score 0.7. Hotfix holding.
2. **Wealth guard at re-baseline** — `convergent_moderate` / composite `2.38` / `d1_score 1.15` /
   `yoga_term 1.23` (3/12 domain-bearing), Dhana Yoga present, affliction layer live,
   `kala_activations` populated (`dasha_activation_proximity: 0.28025`). Exact match to the
   DISAGREEMENT_REGISTER re-baseline FINDING.
3. **D-2 mechanism serving** — confirmed via B-1 (valence_pass rows + grounded
   `affliction_mechanisms`, 472 resolved facts).

## Verdict

**HOLDS — cycle-2 is safe to open.** All five §B slots resolve on fresh live evidence; no prior
battery has gone red (§8.8(i) not triggered); the LEL split is structurally intact and its content
was never inspected. One correction transcribed above (test-span start date). Cycle-2 rollback pin
recorded distinct from cycle-1's.

---
*BIND_D-3_CYCLE2.md — cycle-2 stamped BOUND 2026-07-18. Conductor holds at this milestone per the
native's explicit instruction — pausing before SPAWN of the T-2/T-3 kernel lane pending go.*
