# WP9 5.3 — Moorti Ingress Error Rate Report v1.0

**Status:** MEASURED on declared synthetic fixtures; the real-ephemeris rate
stays **[U] NOT_RUN** until this is executed on the production build's
`ephemeris_daily`. Implements GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0 §5.3
("the day-grade misclassification rate measured and reported").

## What is measured

For every non-truncated moorti sign run, the writer now solves the **true
ingress instant** on the kernel's `sign_ingress` machinery
(`gochara_kernel.arcs.build_arc_index` + `contacts.find_boundary_roots`;
Swiss-refined where the ephemeris backend is present, spline roots over the
same daily knots otherwise) and grades the Moon's nakshatra **at that
instant** (`precision_regime='instant_grain'`). The **day-grade
misclassification rate** is the fraction of instant-graded runs where the
civil-ingress-DATE daily Moon (the pre-5.3 grade) falls in a *different*
nakshatra than the Moon at the true instant — i.e. the runs the old day-grade
path stamped with the wrong moorti. The writer emits
`kernel_instant_graded` / `day_grade_misclassified` /
`day_grade_misclassification_rate` in its `WriterResult.notes` on every run.

## Numbers (every figure printed by a test)

| Fixture | Layout | instant_graded | misclassified | rate |
|---|---|---|---|---|
| `test_wp9_stamp_columns` shared seed (WP9 5.1) | Sun sign-run days 100–130; Saturn two sign-runs; Moon 13.0°/day | 4 | 0 | 0.0000 |
| `test_wp9_overlays_kernel` engineered layout | Sun ingress ≈ day 69.667 with the Moon (20°/day) crossing a nakshatra boundary between the instant and the civil day; Saturn ingress day ~149.8 | 2 | 2 | 1.0000 |

Source of the numbers:
`tests/l3/gochara/test_wp9_overlays_kernel.py::TestMoortiKernelIngress::test_instant_grading_and_misclassification_rate`
(prints the second row) and the writer-notes assertion in
`tests/l3/gochara/test_wp9_stamp_columns.py` (first row).

The engineered row demonstrates the failure mode end-to-end: the Sun's run
grades the Moon in nak 23 → offset 24 → `loha` at the true instant, where the
day-grade path produced nak 24 → offset 25 → `swarna` — a different moorti
name, tier, and phala on the same run.

## Honest bounds

- Both fixtures are synthetic layouts with invented longitudes; they measure
  the mechanism, not the sky. A rate of 0.0 on the 13°/day fixture and 1.0 on
  the boundary-straddling fixture brackets what the mechanism can do — the
  production rate over a real century of ingresses is **[U] NOT_RUN** and is
  readable off `WriterResult.notes` of the first production build that runs
  with `KERNEL_INSTANT_GRADING` (default on).
- Instant solving uses the kernel spline over daily knots where no Swiss
  backend is available (this checkout); the production sidecar refines against
  Swiss ephemeris (`refine=True` attempted first, honest fallback per body).
- Rows the kernel cannot solve (arc-build failure, no matching root) grade
  day-grain exactly as before and keep `precision_regime='date_grain'` — never
  an instant claim on day-grade evidence.
- Truncated horizon-edge runs (`moorti_computed=false`) are untouched and stay
  `date_grain`.

## Related 5.3 landings (same commit series)

- Requested horizon: both overlay writers accept
  `ctx.config['horizon_start']/['horizon_end']`; the ±60/+400 d window is only
  the default (F-11).
- `services/gochara_kernel/overlays.py`: the interval-set overlay projection —
  `quality_gates_at` returns `unavailable` (factor `None`) outside the
  searched horizon, never a default 1.0; A08/H-6 dedup so one obstruction root
  attenuates once; `coverage_gaps` for the manifest's `unavailable` spans.
- `independence_group` (gochara_kernel/ids.py — the family's single identity
  scheme) on every vedha row's `detail` (house_vedha with active obstruction,
  sarvatobhadra, latta).

## 5.4 record — Kota (record only, nothing touched)

Kota-chakra stays `PRESERVE` per plan §5.4: `services/ka_kota_chakra/` was not
modified in WP9. The `w25` mechanism exists in `gochara_v3/mechanisms/` but is
not wired into the scoring product, and per ruling M-4 an operand audit (which
mechanisms enter scoring and in what order) must precede any use of Kota as a
scoring input. This note is the record; there is no code change to review.
