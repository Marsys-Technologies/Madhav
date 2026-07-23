---
artifact: GOCHARA_SWEEP_2_0_DESIGN
type: DESIGN NOTE + WAVE-BRIEF SKELETON (candidate wave D-6 — first post-campaign initiative)
version: 1.0
status: RATIFICATION-READY DRAFT — native-originated architecture (2026-07-21 Cowork session:
  "use our understanding of how the planets move… jump to the likely points without scanning
  everything; mind the Moon's intra-day motion"), formalized by Fable. The D-4b conductor
  VALIDATES §6's assumptions with profiling data from the bulk-read work and fills §7's
  bind-slots as idle-time docs work — NO implementation before D-4b closes and the native
  ratifies this as BRIEF_D6.
governing_when_opened: CONDUCTOR_PROTOCOL.md + TEMPORAL_ENGINE_ARC_PLAN_v1_0.md + DR-10/13/14/
  15/16/17/18 + the D-4b campaign-close state
hard_precondition: D-4b CLOSED (campaign sealed). The v1 sweep's fully-materialized
  `kala_gochara_windows` table is this wave's VERIFICATION CORPUS — 2.0 may not open before v1's
  corpus is complete and the campaign that consumed it is sealed.
---

# GOCHARA-SWEEP-2.0 — Event-Driven Rearchitecture (candidate wave D-6)

## §1 — Why (three independent justifications)

1. **Scale:** v1 costs ~31 CPU-hours per chart per century (post-bulk-read: hours). The §A
   research mission requires many charts; per-chart hours do not scale. Target: **minutes per
   chart**.
2. **Correctness:** v1's daily-midnight grid UNDERSAMPLES fast bodies — the Moon (~13°/day)
   crosses a nakshatra daily and holds tight orbs for hours; contacts can enter and exit
   between samples. v1 windows are honest only at ≥1-day resolution (registered fidelity
   bound). 2.0 makes sub-day claims computable and honest.
3. **Fidelity of bounds:** DR-17's percentile/tie-band machinery and the RED-C defect class
   (chunk-artifact bounds) both improve when window edges are astronomical facts (transition
   timestamps) rather than grid artifacts. Under 2.0, an artifact-bounded window is
   structurally impossible.

## §2 — Core architecture: the transition calendar

Planetary motion is smooth and piecewise-monotonic; therefore every grammar primitive's state
changes only at COMPUTABLE moments. Invert the sweep: don't sample days and ask "what is
active?" — enumerate transitions and derive "active intervals" directly.

1. **Position substrate:** cubic splines fit over L0 `ephemeris_daily` rows (the bulk-read
   lane's tables, with the per-date ayanamsha polynomial). All position queries and
   root-finding run on splines — ZERO live Swiss-Ephemeris calls in the sweep path. Spline
   interpolation recovers any timestamp's position to arc-minute accuracy incl. the Moon
   (validate near stations, §6.V3).
2. **Chart-INDEPENDENT event calendar (global L0/L1 asset, computed ONCE for all charts):**
   sign ingresses, nakshatra ingresses, stations/retro-loop boundaries, eclipses, Sāde-Satī
   phase edges (per moon-sign, 12 variants), planetary returns, synodic double-transit
   geometry. This is "the sky's own diary" — every chart reads the same one.
3. **Chart-SPECIFIC contact events (per chart, cheap):** for each resonance-map target degree ×
   transiting body × contact type, root-solve orb entry/exit/peak crossings on the splines.
   Countable: an outer body crosses a given degree 1–3× per cycle (retro loops); total
   per-chart events ≈ tens of thousands of millisecond root-finds.
4. **Interval assembly + differential state:** primitives are active on INTERVALS between their
   transitions; composition operators (simultaneity, double-transit, kartari, vedha, daśā-
   coincidence) become interval-intersection algebra; a running active-sentence set updates
   only at events (subsumes the registered t±5 rescan CR). λ_e integrates analytically between
   events (cos² orb over smooth angular separation).
5. **Muhurta-hierarchy lazy refinement (classically shaped multi-rate):** slow layers
   (Jupiter…Ketu + daśā systems) computed full-span eagerly; Sun/Mercury/Venus at their own
   event density; **Moon/lagna-scale precision computed lazily** — materialized only inside
   windows the slow layers already elevate, or on demand for election queries ("which day this
   month → which hour"). Exactly how an acharya drills down; exactly where compute belongs.
6. **Serving contract unchanged:** same `kala_gochara_windows` schema + views (activation/
   forecast/election-avoidance), same DR-10 `peak_basis`, DR-13 shapes, DR-16 gating, §N.6
   budgets — plus `window_edge_basis: transition_timestamp` and sub-day fields where the
   event-class shape permits. Consumers notice precision, not upheaval.

## §3 — Verification discipline (the wave's spine)

1. **Equivalence corpus:** v1's fully-materialized century table is ground truth. 2.0 must
   reproduce v1's windows (same event-classes, overlapping bounds within 1 day — v1's own
   resolution) wherever v1 was RIGHT.
2. **Documented-divergence protocol:** where 2.0 differs, each divergence is classified with
   evidence: (a) v1 grid artifact (chunk-edge bounds, midnight snapping) — 2.0 correct;
   (b) v1 Moon-undersampling miss — 2.0 found a real sub-day window v1 couldn't see (expected
   headline finding); (c) genuine 2.0 bug — fix. NO divergence ships unclassified.
3. **Specimen continuity:** all D-5/D-4b named specimens reproduce (windfall plateau overlap;
   both 2013 marriage peaks incl. the double-transit at its exact timestamps).
4. **Determinism + adversarial probes:** per the campaign standard (byte-identical re-derivation,
   cache-poisoning class probes on the spline/event caches).
5. **Post-cutover:** ONE full re-run of the standing regression battery + the D-4b gate's
   scoring assertions on 2.0 data — calibration multipliers must be stable within tolerance or
   the divergences explain why (with native disposition before cutover).

## §4 — Lane skeleton (freeze at open)

E-1 spline substrate + ayanamsha polynomial + coverage (extends the D-4b bulk-read lane's
tables) → E-2 chart-independent event calendar (global asset + writer) → E-3 chart-specific
contact-event solver → E-4 interval assembly/differential composition + λ integration →
E-5 lazy Moon/refinement layer + election drill-down → E-6 equivalence battery + divergence
classification + cutover (v1 writer retired-in-place, table provenance-stamped per generation).
Merge order as listed; test-first law inherited (every lane measured against the v1 corpus +
A-3 harness as it lands).

## §5 — Exclusions

No new astrology (grammar/doctrine frozen as of D-4b close — 2.0 changes HOW, never WHAT);
no calibration changes (β/weights untouched; any multiplier drift at cutover is a finding,
not a tuning opportunity); no KP; FROZEN orchestrator (new writers conform to WriterBase);
sealed test split; §11 data governance.

## §6 — Bind-time validations (D-4b conductor fills from live data, idle-time)

V1: profile split from the bulk-read lane (confirms what fraction of residual cost 2.0
eliminates). V2: `ephemeris_daily` coverage/cadence actually present for 1984–2084 ×9 bodies.
V3: spline accuracy audit near stations + Moon perigee (max interpolation error vs one-off
swe spot-checks; sets the root-find tolerance). V4: transition-count estimate for this chart
(events per primitive family — validates the "tens of thousands" sizing). V5: v1 corpus
completeness state + provenance stamps ready for corpus role. V6: divergence-rate pilot on 1
materialized year (2.0 prototype math on paper/spike vs v1 rows — sizes §3.2's workload).

## §7 — Open items for the native at ratification

N1: wave naming (D-6 vs new-arc numbering). N2: multi-chart rollout order after cutover
(Abhinandan next?). N3: whether the global event calendar backfills deeper history
(pre-1984) for future research charts. N4: cutover posture — hard cutover after §3.5, or a
dual-serve shadow period with 2.0 shadow-writing and v1 authoritative until N days of
agreement. N5: **lock granularity** (from the D-4b concurrency assessment, 2026-07-21):
`acquire_chart_lock` is a single chart-level `pg_try_advisory_lock` — the orchestrator refuses
concurrent runs per chart BY DESIGN (`runner.py:729` → `sys.exit(3)`), which blocked safe
substep-shard parallelism even though the data writes were proven disjoint-safe (UNIQUE on
chart×event_class×window fields; FOR-UPDATE-scoped consolidation lookups). Changing granularity
is a FROZEN-contract PARK-class question — decide at D-6 ratification whether 2.0's writer gets
per-asset/per-shard locking (native + Adjudicator ruling required), since minutes-per-chart ×
many-charts throughput likely wants intra-chart parallelism the current lock forbids. The full
assessment text lives in the D-4b session record; it is this item's evidence base.
