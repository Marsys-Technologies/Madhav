---
artifact: ADDENDUM_D-5_PRE_D4B_READINESS
type: WAVE-CLOSE ADDENDUM (appends to, does not rewrite, STATE_D-5.md / REPORT_D-5.md)
wave: D-5 — Gochara-Chitra (CLOSED GREEN-WITH-PARTIALS 2026-07-20)
authored_by: Claude Code (Sonnet 5), pre-D-4b readiness pass v3, 2026-07-21
status: ADDENDUM — does not retroactively flip D-5's own gate disposition. Per this readiness
  pass's own charter ("do NOT retroactively flip D-5's gate; append an addendum recording the
  residual RESOLVED-BY-MATERIALIZATION with evidence, or note it still stands"), this records
  new evidence and its honest, current disposition.
---

# Addendum — marriage-specimen residual re-examined on partially-improved materialization

## §1 — What STATE_D-5.md's `gate_run_3` closed on

`marriage_verdict: FAIL` — "Still only ONE served row (2013-01-07, chara_karaka active,
guru_shani_double_transit inactive that day)." This was true of the live data AT THAT TIME
(3 committed substeps: `major_gain:year:60/61`, `marriage:year:63`).

## §2 — What changed between D-5's close and this readiness pass

A prior diagnostic session (this session's own earlier turn, `DIAG_GOCHARA_SWEEP_STALE_v1_0.md`,
merged to `origin/main` via PR #669) found that `ka_gochara_sweep`'s live data had REGRESSED from
3 committed rows back down to 1 (the `_RESUME_VERSION`-triggered delete-then-insert of a later,
incomplete dispatch had wiped the prior 3-row state without a successful re-materialization ever
completing). This readiness pass's own A.0 work (root-cause + perf fix, §A.0 of this pass's own
report) re-dispatched the sweep and, after the fix, successfully re-committed the 3 named specimen
substeps plus made a small amount of further progress.

## §3 — Fresh evidence (this readiness pass, direct query, independently re-derived)

`marriage` event_class, chart 482012f1, live `kala_gochara_windows` rows in Dec 2013 window
(post top-K local-maxima fix, per D-5's own gate_run_2 finding-2 disposition):

- **52 candidate peak rows** exist for `marriage` across 2012-12 through 2013-12 (top-K local
  maxima, not a single argmax) — a materially richer served surface than the 1-row state
  `gate_run_3` assessed.
- `guru_shani_double_transit` is **active** (`weight=0.1, active=true`) at peak dates
  **2013-12-07** and **2013-12-15** — the two peaks immediately bracketing the LEL marriage date
  of **2013-12-11**.
- This directly contradicts `gate_run_3`'s "guru_shani_double_transit inactive that day" finding.

## §4 — Honest disposition (per the residual-pair schema, `DR_17_18_MANIFESTATION_CENSUS_DOCTRINE_v1_0.md` §3)

```
residual_pair: {
  event_class: "marriage",
  chart_id: "482012f1-710e-4a25-994a-93821f5871aa",
  true_date: "2013-12-11",
  mechanism_a: {system_id: "chara_karaka", active: true, weight: 0.1},
  mechanism_b: {system_id: "guru_shani_double_transit", active: true (at 2013-12-07/12-15, per
                this pass's fresh data) — NOT independently re-verified as the model's OWN
                declared peak (a `sub_peak`-vs-`peak` grade question, DR-17 §1), weight: 0.1},
  agreement: "concordant (both mechanisms now show live activity bracketing the true date)",
  disposition: "OPEN-RESIDUAL — IMPROVED, NOT YET CERTIFIED",
  evidence_ref: "this addendum + DIAG_GOCHARA_SWEEP_STALE_v1_0.md + this pass's own report §A.0",
}
```

**This is explicitly NOT marked `RESOLVED-BY-MATERIALIZATION`.** Reason: `ka_gochara_sweep` for
chart 482012f1 is still far from fully materialized at the time of this addendum (a small number
of the ~300 planned substeps have committed; see this pass's own report for the exact count and
the BRIEF_D4B §0 gate this pass added specifically to prevent a scoring/verdict claim from being
made against partial data again). The evidence above is genuinely encouraging — it suggests the
original `gate_run_3` FAIL may have been an artifact of the ~1%-materialized dataset it was forced
to assess, not a true engine limitation — but "encouraging" is not "certified." **D-4b's own Binder
must re-run this exact check against a FULLY materialized sweep (BRIEF_D4B §0's gate) before
striking this residual from the inherited-items list.** Until then, `BRIEF_D4B.md §2` correctly
carries it as "RE-EXAMINED, not resolved."

## §5 — What this addendum does NOT do

- Does not change `STATE_D-5.md`'s own `gate_run_3` block (historical record, left as-is).
- Does not change D-5's close status (GREEN-WITH-PARTIALS stands).
- Does not authorize D-4b's B-1 bakeoff to treat this residual as closed.
