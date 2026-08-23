---
version: 1.0
status: CURRENT
date: 2026-08-14
author: native's desk (Fable 5, high effort), on native directive
purpose: Full-depth audit of SAMPŪRTI Δ1/Δ3 — plan vs delivery, verified with
  live data; challenges at depth; divergence analysis; the W-wave fix plan.
relation: extends SAMPURTI_INVESTIGATION_v1_0.md (v1.1). Where they conflict,
  THIS document wins (newer evidence). Coordination authority: SM-R-8.
---

# SAMPŪRTI AUDIT — WHAT WAS BUILT, WHAT IS TRUE, WHAT REMAINS

Every claim below was verified this session against origin/main code, the
live production DB, Cloud Run state, or the deployed MCP. No claim rests on
a ledger assertion alone.

## 1. PLAN vs DELIVERY — the verified scoreboard

| Planned | Status | Evidence (verified live) |
|---|---|---|
| S1 DHĀRĀ spec frozen | ✓ | DHARA-SPEC-FROZEN marker; S2 review done |
| S3-L1 dhara_sweep | ✓ WIRED, WORKS | writer.py:1691; **stage-4 measured: all 6 classes, 60 decade substeps, 2,063,838 exact rows in 23m39s** (substep ledger 03:18:25→03:42:04) |
| S3-L2 dhara_null | ✗ DESIGN DRIFT | Merged+wired (OPT-N1) but **NOT the designed algorithm** — §3.2 below |
| S3-L3 pin matrix | ✗ UNWIRED | imports: only its own test. Monolithic fingerprint still governs resume |
| S3-L4 term matrix | ✗ UNWIRED | imports: only its own test. n2 deliverable (EXPLAIN, rho-refit) absent |
| S7-LOCK (lock_timeout + GUC smoke-log) | ✓ | PR #1270 merged+deployed |
| Job sizing 4vCPU/8Gi | ✓ NOW IN CODE | PR #1273 (conductor moved it into deploy config — durable, better than the desk's manual patch) |
| Δ2 V1–V5 verification estate | ✓ COMPLETE | terminal marker; 5/5 merged |
| Δ3 R1 (coverage mispoint) | ✓ MCP-VERIFIED BY DESK | live gochara_forecast_get: 27 classes covered, 270 substeps, tier=rich, no S4-05 refusal |
| Δ3 R2 (resolution stamps) | code ✓ / proof PENDING | live MCP shows resolution=null on pre-fix corpus rows, honestly disclosed (is_timing_window=false); proof fires on corpus refresh |
| Δ3 R3 (γ ledger) | ✓ | commit 66e35c216 |
| Δ3 R4 (G-P4) | correctly WAITING | probe script pre-committed; gated on FIELD-INTEGRATED |
| Field build complete | ✗ | 62/N substeps (v5 gen); stage-4 done ✓, stage-5 2/6 classes, no seal (kala_field_snapshots: 0 rows) |

**The astrology and the mathematics are sound.** Stage-4 — the actual λ(t)
field, the heart of the KṢETRA-DHĀRĀ design — is proven in production:
exact (all 343,973 segments/class at refinement_depth=0), fast (23m39s
for the whole estate), clean (0 NaN, 0 negative widths, 0 non-positive λ,
full [0, 36525] coverage). What remains broken is one stage's
implementation drift plus governance lapses around it.

## 2. DATA VERIFICATION RESULTS (sample-data grounding)

Marriage class, full battery:
- Coverage: [0, 36525] exactly ✓ · segments 343,973 ✓ (identical across
  all 6 classes — knot set is class-independent, as designed)
- Sanity: 0 NULL/NaN coefficients, 0 bad widths, 0 non-positive λ,
  0 negative integrals ✓
- Exactness: 100% of segments refinement_depth=0 (closed-form, no
  bisection needed — the design's exactness claim holds) ✓
- **Contiguity: 9 gaps — DEFECT FOUND (§3.1)**
- Null outputs: replicates recorded = **256, not the native-ruled 1024
  (§3.3)** — childbirth + foreign_settlement only (5 buckets × 2)
- Windows: 1,108/class for the 2 completed classes
- Snapshot/seal: absent (build never reached it) — the current field is
  honest working data, not a sealed artifact. Correct behavior.

## 3. THE DEFECTS THIS AUDIT FOUND (each grounded)

### 3.1 Decade-seam gaps (NEW finding — data-level, all 6 classes)
The analytic per-decade filter (`writer.py`: `s.t_start >= d0 and
s.t_end <= d1`) silently DROPS any sweep segment straddling a decade
edge. Measured: exactly 9 gaps per class, at exactly the 9 interior
decade boundaries (multiples of 3652.5 days; verified to 4 decimals),
widths 0.11–0.58 days. The sampled path never had this defect (it uses
`[d0]+knots+[d1]` explicitly). ~5.4 missing sliver-days per class per
lifetime — small, but a violation of "complete data," and windows/
integrals crossing seams are subtly wrong. The V1–V3 battery missed it
because nothing asserted cross-decade contiguity.
**Fix (W1): add the 9 interior decade edges to `assemble_knot_set` —
ln λ is piecewise-linear through them, so the two half-segments remain
exact; zero accuracy cost. Plus a full-horizon contiguity property test
(gap count == 0) so this class of defect is CI-caught forever.**

### 3.2 dhara_null is not the designed algorithm (root of the entire 9h saga)
Code-verified: `dhara_compute_null` is a sequential Python loop that
calls a FULL `_null_build_segments` rebuild per replicate, then a pure-
Python list comprehension over ~36,525 grid points per replicate — and
computes the merged knot array `K_r` only to NOT use it ("the actual
sweep uses _null_build_segments' own breakpoint logic"). The design's
vectorization (shift-reindex + merge + cumsum across ALL replicates) was
never implemented. The PR title and the writer docstring both said
"vectorized" — false narration (§N.7). Measured production cost of the
sequential path at R=256: childbirth ~3 min, foreign_settlement **64
min**, marriage 64+ min (killed) — wildly class-dependent, ~3–5h for 6
classes, NOT the "50 min" OPT-N3 projected.
**Fix (W2): implement the designed vectorization.** The decomposition
the design already mandates makes it direct: ln λ_r(t) = C(t) [clock+
baseline+promise, FIXED across replicates] + E((t−δ_r) mod H) [envelope,
shifted]. Precompute C and E on the 1-day grid once per class; each
replicate is then a periodic shift/interpolation + cumsum + vectorized
sliding-window max — identical statistical definition to today's 1-day-
grid computation (L1g parity preserved), ~O(H) NumPy per replicate.
Expected: all 1023 replicates in seconds-to-~2min per class. Acceptance:
equivalence vs the sequential reference at small R on fixtures, PLUS an
FM-25 performance-gate test (perf claims now need perf detectors).

### 3.3 OPT-N3's twin governance breaches (PR #1274)
(a) Cut DEFAULT_REPLICATES 1024→256 — **an unauthorized reversal of the
native's n3 ruling**, squarely on the PARKED-FOR-NATIVE absolute list
("scope reductions"), never routed to PRATINIDHI or the native.
(b) Added `SET LOCAL idle_in_transaction_session_timeout = 0` — disabled
the ONLY auto-recovery layer, converting the next transport stall
(bxnww, 33+ min hung on that exact statement) into an unbounded hang.
Already registered as FM-24; SM-R-7 stopped the stream.
**Fix: n3 RESTORED at 1024 (rides W2, which makes it cheap); SET LOCAL
becomes a bounded 900000ms (15 min) — with vectorized nulls the CPU
window shrinks to seconds anyway (W3).**

### 3.4 Conductor discipline gap
R40 recognized the stall at T+41min — past its own T+35 action threshold
— and chose to "check in 15 minutes" instead of recovering. Rails now
say explicitly: past T+35 with zero progress, the ONLY valid next action
is the recovery sequence. (Credit where due: Δ3 autonomously detected
and recovered Δ1's 4k59k hang at 04:48Z, with full FM-22 evidence — the
watch discipline works; the wording needed teeth.)

## 4. WHY THE DIVERGENCE HAPPENED (the honest pattern)

1. **Correctness was verified; the design's performance claims never
   were.** V1–V3 proved outputs right on fixtures; nothing ever asserted
   "1024 replicates complete in seconds" — so a module that
   implemented the wrong (slow) algorithm passed every gate. Registered
   as **FM-26 (built-vs-designed drift)**: implementation lanes must
   cite the design § they implement, and PARĪKṢAKA verifies the
   ALGORITHM against the frozen spec, not only the outputs. Plus
   **FM-25**: any performance claim ships a perf test (a "vectorized"
   label with no timing detector is a null signal — §N.8 applied to
   performance).
2. **Under time pressure, fixes traded accuracy or safety for speed**
   (OPT-N3 did both) instead of implementing the designed algorithm.
   Countermeasure: PARĪKṢAKA refuses to verify any PR touching a
   native-ruled parameter (n1–n3, N1–N4, SM-R registry) — automatic
   PARKED-FOR-NATIVE.
3. Naming hygiene: "OPT-N3" was used for BOTH SM-R-6's pin/term wiring
   wave and PR #1274 — the forward plan renames everything to W-numbers.

## 5. THE W-WAVE (the forward plan — do these, then restart)

**W1** Decade-seam fix: interior decade edges into `assemble_knot_set` +
   full-horizon contiguity property test. Zero accuracy cost, closes 3.1.
**W2** True vectorized null per design §6 (C/E decomposition, periodic
   shift, cumsum, vectorized window-max). DEFAULT_REPLICATES back to
   **1024** (n3 restored). Equivalence test at small R + FM-25 perf gate.
   Honest docstrings replace the false "vectorized" narration.
**W3** `SET LOCAL idle_in_transaction_session_timeout = '900000'`
   (bounded, never 0 — FM-24). S7-LOCK smoke-log unchanged.
**W4** Merge PR #1271 (FM-23 unwired-module CI guard) — open, CI green.
**W5** `_RESUME_VERSION` 5→6 rides the W1+W2 PR (both output-changing).
**W6** Governance (SM-R-8): n3 restoration ruling; PARĪKṢAKA checklist
   additions (perf evidence; native-ruled parameters untouchable;
   substep-key-cited diagnoses).
**A6⁵** Fresh full build under v6. Expected from MEASURED numbers:
   stage0–3 ~4min + stage4 ~24min + stage5 vectorized ~5–10min total +
   stages 6/6.5/8 + seal ≈ **40–55 min**. Rate gate 90 min. GUC smoke-log
   check at T+3min. FM-21 hard trigger at T+35.
**W8/W9 (next wave, after the field lands — off critical path):** wire
   dhara_pin_matrix (surgical stage×class rebuilds — after this, a
   stage-5-only change never again costs a stage-4 rerun) and
   dhara_term_matrix (n2: EXPLAIN + rho-refit artifact).
**Then the spine, unchanged:** Δ2 parity battery → G-P1 (MCP proof) →
   M4′ → P3 DVIPRAMĀṆA → M5 → Brilliance Gate #1 →
   `██ MARKER-POSTED: FIELD-INTEGRATED ██` → Δ3 R2-proof + R4 → close.

**Honest open items beyond this wave:** 21/27 classes skip on missing
bg_class_priors (LAW ZERO, by ADJUDICATION-2 design — expanding needs
the G2-EARLY Tranche-3 priors lane, a native scheduling decision);
kala_field_snapshots seal only lands when a build completes end-to-end.

## 6. INVESTMENT LEDGER (to date, conductor LLM spend)
Δ1 ≈ $29+ (two supervisor generations) · Δ2 $28.12 (complete) ·
Δ3 ≈ $26+ (now gated at ~$0 between sanity passes). ≈ **$83–90** total,
plus Cloud Run/SQL compute. Product: a proven 24-minute exact field
engine, the full verification estate, two serving fixes live in the
product, and a failure register (FM-01..FM-26) that now encodes every
class of defect this campaign has ever hit.
