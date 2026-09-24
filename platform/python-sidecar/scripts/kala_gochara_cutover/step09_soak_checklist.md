# Step 9 — Soak checklist + second-chart birth-epoch fixture (#2534 class)

Runbook: GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9 step 9.
Sheet: A-3 (tranche 2, `PRODUCTION_TRANCHE_2_AUTHORIZED`).

## Soak checklist (production, after step 8)

- [ ] Soak window declared in the evidence header (start/end timestamps) before
      it begins; no minimum duration is asserted at preparation time — the
      tranche records the actual window.
- [ ] Walkthroughs §3 F-02 re-run: ordinary quarter and marriage 2013 show
      episodes with contacts and coverage (step 8's gate, re-run under soak
      traffic).
- [ ] Integrity contract green throughout the soak (`ka_gochara`
      `integrity_check_sql` — conjuncts (a)–(k) — evaluated at soak start,
      midpoint, end; all three results recorded).
- [ ] Cockpit count equals `count_sql` throughout (no drift between display
      and relation).
- [ ] No guard-trigger refusals in the logs other than expected
      protection rejections.
- [ ] Kṣetra's next build reads '4.0' rows (K-1 pins edges by
      `(generation, id)`); Saṅgam consumes `find_episodes` (V-1/S-2).

## Second-chart fixture — birth-epoch defect class (#2534)

The century writer's known-RED defect (#2534): a hardcoded native birth epoch
used for ALL charts. The second chart (`1c826d5a`, Abhinandan) is built with
birth from `ctx.config['birth_params']` — never a shared constant.

Fixture assertion (synthetic rehearsal form, exercised in
`tests/l3/gochara/test_wp10_cutover.py`): a synthetic chart born 1985-03-02
produces **no window before its own birth** — the detector the proof matrix
(§10 Revision row) names for this defect class.

Production form: build `1c826d5a` per step 6 with the same flags; gate =
integrity green on both charts AND zero `'4.0'` windows with
`window_start < birth date` for either chart.

## Reversal

As step 8 (re-point authority to '3.0'; manifest `rolled_back`).

## Evidence

`evidence/step09_evidence.md` — soak window, the three integrity evaluations,
walkthrough outcomes, second-chart build report, and the birth-epoch assertion
result.
