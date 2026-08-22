---
version: 1.0
status: CURRENT (native-authorized 2026-08-14 — ruling N5, recorded SM-R-9)
author: native's desk (Fable 5, high effort)
purpose: TARGET-STATE plan — 27-class platform consistency, vectorization-first
  build, completeness + brilliance + minimal build time. Supersedes the W-wave
  numbering (SM-R-8) by ABSORBING it; nothing from the audit is dropped.
grounding: every architectural claim below was code-verified this session
  (writer.py shared contexts; hazard.py evaluate() signature + baseline_rate;
  dhara_null.py loop; live substep/row data in SAMPURTI_AUDIT_v1_0.md).
---

# PŪRṆA-KṢETRA — THE COMPLETE FIELD (target-state plan)

## N5 — THE NATIVE MANDATE (this plan's authority)
27-class consistency across the entire platform; vectorization implemented
BEFORE building; ideal target state for completeness of output, brilliance
of astrological insight, and minimal build time. Accuracy non-negotiable.

## 0. The three insights that make this achievable now

**I-1 (measured):** the expensive per-knot work is CHART-level, not class-
level. `_shared_envelopes/_clocks/_ladder` are already shared; the raw
curves (lord stacks, covariate x_j(t), obstruction u_m(t)) are identical
for all 27 classes. Class identity enters only as cheap coefficients
(lifetime_count, promise, weights). Today the writer recomputes the raw
curves 6× (would be 27×); computing them ONCE and combining per class is
a ~27× reduction on the dominant cost — and the data structure that holds
them is EXACTLY the term matrix the design already specifies (§4).

**I-2 (proved from C-1):** `baseline_rate = lifetime_count/DAYS_PER_CENTURY`
is a pure multiplicative constant on λ. The circular-shift null shares it,
so window detection (exceedance vs own-chart null quantile) is SCALE-
INVARIANT: timing windows, peaks, and salience are mathematically valid
WITHOUT a lifetime prior. Only absolute intensity and expected-count
integrals need the prior. Therefore prior-less classes can ship honest
`shape_only` timing output — LAW ZERO fully intact (no fabricated
baseline ever; absolute fields withheld, not invented).
  ADVERSARIAL GATE: this invariance claim gets a dedicated S2-style
  refutation review + a property test (scale λ by 10×, assert identical
  windows) BEFORE any shape_only row is written. If refuted → fallback:
  shape tier canceled, those classes stay skipped, priors lane remains
  the only expansion path. Blind-committed either way.

**I-3 (measured):** stage-4 at 23m39s/6 classes and nulls at 3–64min/class
show writes and per-replicate rebuilds — not mathematics — are the cost.
COPY-based bulk writes + matrix-combine + vectorized nulls put the full
27-class estate inside ~1 hour, and pin-matrix wiring makes every later
rebuild surgical (a weights refit = minutes, per the original design).

## 1. Target state (definition of done)

COMPLETENESS: all 27 ontology classes present on every kala_* surface
with an explicit per-class tier — `calibrated` (ratified prior: absolute
λ, expected counts, windows) · `shape_only` (windows/peaks/salience only;
absolutes honestly withheld) · `not_applicable` (e.g. birth_anchor if the
ontology says non-predictive — explicit status, never silence). Seamless
field (0 contiguity gaps, CI-enforced), sealed snapshot + content hash,
1024-replicate nulls (n3), era⊃month⊃day hierarchy consistent with the
gochara surface (Δ3 R2), and NO serving surface anywhere carrying a
hardcoded 6-class assumption (CI census).

BRILLIANCE: term-matrix EXPLAIN on every window (which daśā clock, which
covariate, which suppression drove it — the acharya-grade "why", served
via kala_explain_get); cross-class convergence detection in stage 6/8
(multiple classes peaking together = life-chapter structure) now over the
full 27-class estate; DVIPRAMĀṆA dual-reference comparison now 27-vs-27
against gochara; Brilliance Gate #1 (PRATINIDHI opus-max) unchanged as
the quality bar; M4′/M5 measurements per the elevated plan.

SPEED: full 27-class cold build ≤ ~60 min (targets §4); per-class or
weights-only rebuild surgical via pin matrix (minutes); no stage ever
again able to silently cost hours (FM-25 perf gates in CI).

## 2. Architecture (the P-wave — absorbs W1–W5)

**P1 TERM-MATRIX ENGINE (absorbs the audit's W1 + old W9):**
one sweep over K per chart computes the raw per-knot matrix (clock raw
r_s(t_k) per system, covariate x_j(t_k), suppression u_m(t_k)) — the §4
TermMatrixRow, now the ENGINE's working set, persisted as the .npz
artifact (n2 delivered: EXPLAIN + rho-refit for free). Per class: ln λ_e
= NumPy weighted combine over matrix columns → segments (α,γ) directly.
Decade edges (d·H/10, d=1..9) join K (seam fix; two exact half-segments,
zero accuracy cost). Row writes go COPY, not executemany. CONTIGUITY
property test (gaps==0 over full horizon) + matrix-vs-terms_at pointwise
equivalence test (sampled knots, 1e-12) in CI.

**P2 VECTORIZED NULL (the audit's W2, unchanged in substance):**
ln λ_r(t) = C(t) + E((t−δ_r) mod H); C,E precomputed on the 1-day grid
from the term matrix (C = baseline+promise+clock combine; E = envelope
combine); per replicate = periodic shift/interp + cumsum + vectorized
window-max. R=1024 restored (n3). Same statistical definition as today
(1-day grid, L1g-parity coarse clock knots for nulls). Equivalence test
vs sequential reference at R=8; FM-25 perf-gate test (fixture ceiling).

**P3 TIERED 27-CLASS MODEL:**
per-class basis spec BLIND-COMMITTED first (R13/R18): which of the 21
prior-less classes are countable (→ priors lane targets), which are
shape_only, which not_applicable — decided from brahma_event_ontology
semantics, PRATINIDHI-ratified, THEN computation. Writer: tier-aware
build replaces binary skip (calibrated path unchanged; shape path uses an
EXPLICIT shape constructor — the C-1 guard stays for calibrated rows so
a fabricated baseline remains structurally impossible). Serving: tier in
every row + facet; drill pointers to gochara for not_applicable.

**P4 PRIORS RESEARCH LANE (parallel, non-blocking):** citation-backed
lifetime-count sourcing for the countable classes (demographic/actuarial,
same protocol that ratified the 6), PRATINIDHI-ratified per class,
blind-committed before use. Each ratification upgrades a class
shape_only→calibrated via a SURGICAL per-class rebuild (pin matrix, P5).
No class is ever upgraded by estimation-without-source (B.10 absolute).

**P5 PIN MATRIX WIRED (old W8, now core):** (stage×class) fingerprints
replace the monolithic one — required so P4's per-class upgrades and any
stage-5-only change never re-cost stage-4. Own resume-semantics tests.

**P6 SERVING CONSISTENCY SWEEP (Δ3's new lane R5):** census every kala_*
tool + portal surface for class-universe and tier disclosure; add the CI
census check (universe == ontology's 27, tier facet present, no
hardcoded class lists). Independent of the field build — Δ3 can run it
inside its existing gate/sanity cadence.

Safety rails carried forward unchanged: bounded SET LOCAL 900000ms
(FM-24, old W3) · merge PR #1271 (FM-23, old W4) · `_RESUME_VERSION` 5→6
rides the first output-changing PR (FM-17, old W5) · GUC smoke-log at
T+3min · FM-21 hard trigger at T+35 · 90-min rate gate.

## 3. Phasing + order of operations (Δ1)

P-A DESIGN (blind, ~1 session): three spec docs — ENGINE (P1+P2 combined
    algorithm vs frozen DHARA §4/§6), TIERS (P3 per-class basis table +
    scale-invariance proof), PRIORS protocol (P4). Adversarial review
    (opus PARĪKṢAKA, FM-26 algorithm-vs-spec duty + the I-2 refutation
    gate). Freeze markers posted.
P-B BUILD (≤4 sonnet builders, parallel lanes): L-ENGINE (P1) ·
    L-NULL (P2) · L-TIER (P3 writer+serving) · L-PIN (P5). Each lane TDD,
    PR→main, FM-25 perf tests where speed is claimed. W3/W4 ride along.
P-C FIELD BUILD A7 ("PŪRṆA build"): all 27 classes under the tier spec.
    Rate-gated (§4 targets; >90min → stop + cProfile + substep-key-cited
    diagnosis). GUC verify, FM-21 hard watch.
P-D PROOF: Δ2 parity battery (fixtures regenerated for the new engine
    where the frozen EXPECTED-differences register says so) → G-P1 MCP
    gates → M4′ → DVIPRAMĀṆA (27-vs-27) → M5 + ablation → BRILLIANCE
    GATE #1 → ██ MARKER-POSTED: FIELD-INTEGRATED ██ → Δ3 R2-proof + R4.
P-E UPGRADE LOOP (ongoing): P4 priors ratifications → surgical per-class
    upgrades → M-measurement refresh. The platform stays live throughout.

## 4. Time budget (targets, anchored to measured data; rate gate enforces)

| Piece | Basis | Target |
|---|---|---|
| stage0–3 (chart-level) | measured ~4–5min | ≤6min |
| raw term-matrix sweep (once) | 1 class-sweep ≈ 4min measured | ≤8min |
| 27 × combine+COPY writes | I/O-bound; COPY ≫ executemany | ≤25min |
| 27 × vectorized nulls @1024 | matrix ops on 36525-grid | ≤12min |
| stages 6/6.5/8 + seal | prior runs | ≤8min |
| **FULL 27-class cold build** | | **≈45–60min** |
| per-class upgrade (P4 loop) | pin matrix surgical | minutes |
| weights/rho refit | term-matrix rho-refit (F-06/F-14) | seconds–minutes |

## 5. Governance
SM-R-9 records N5 (this mandate), the tier architecture, the I-2
adversarial gate, and Δ3's R5 lane. PARĪKṢAKA duties from SM-R-8 stand
(perf evidence, algorithm-vs-spec, native-ruled parameters untouchable,
substep-key-cited diagnoses). PARKED-FOR-NATIVE list unchanged — P3's
tier-basis table and every P4 prior ratification go through PRATINIDHI
with written rationale; anything reducing scope comes back to the native.
