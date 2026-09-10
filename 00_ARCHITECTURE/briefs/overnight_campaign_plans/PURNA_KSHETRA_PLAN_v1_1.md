---
version: 1.1
status: CURRENT (native-authorized 2026-08-14 — ruling N5 stands; this
  revision incorporates PURNA_GROUNDING_REPORT_v1_0.md, which found 7
  assumptions in v1.0 wrong. v1.0 is SUPERSEDED, not deleted.)
author: native's desk (Fable 5, high effort)
purpose: v1.0 corrected against code+data ground truth. Nothing in the
  MANDATE changed (27-class consistency, vectorization-first, minimal
  build time, accuracy non-negotiable); the ARCHITECTURE changed where
  grounding proved v1.0 wrong.
grounding: PURNA_GROUNDING_REPORT_v1_0.md (G1-G12, read-only, code+DB
  verified). Every change below cites the G-item that forced it.
---

# PŪRṆA-KṢETRA v1.1 — CORRECTED AGAINST GROUND TRUTH

## 0. What the grounding pass confirmed vs broke

**CONFIRMED (v1.0's core bet was right):** I-1 (chart-level shared raw
curves) is not just true, it's MORE separable than assumed — clocks
(G1), all 12 covariates (G2), and suppression (G3) are 100% chart-level
with zero class-dependence in their raw form; the actual waste is
`writer.py`'s `_class_context()` rebuilding chart-level structures once
per class. G6 confirms 27-class tiering has no algorithmic scaling risk
(no O(classes²) anywhere). G12 confirms the serving-consistency sweep
(P6) is small and targeted, not a rewrite.

**BROKEN and now fixed below:**
1. **I-2/P3's shape_only tier is architecturally unreachable as
   originally stated** (G5) — the single most important finding. Fixed
   in §2 P3.
2. **`DHARA_DESIGN_v1_0.md` is not merged to `origin/main`** — an
   unmerged, `AMENDED_BLIND` worktree artifact (G4). Fixed in new §2 P0.
3. **The frozen §4 term matrix is per-class WEIGHTED, not the chart-level
   raw layer P1 needs** — requires an explicit two-layer split (G4).
   Fixed in §2 P1.
4. **`bg_class_priors` does not exist**; the real table
   (`brahma_class_priors`) is signal-type-keyed and only 6/27 classes
   have usable citation-backed rows (G9). Fixed throughout, esp. §2 P4.
5. **Two live, disagreeing null engines with a silent-wrong-answer
   fallback** (G7/G10) — `stage5_null.NullResult` (R+1 denominator,
   confirmed DEAD CODE per this session's follow-up check:
   `ENGINE_VERSION` has no live `'sampled'` call site) vs
   `dhara_null.NullResult` (R denominator, live). Fixed in §2 P0+P2.
6. **Suppression's per-class-filter docstring is false against the live
   evaluator** (G3) — needs a native ruling, not a silent pick. Fixed in
   §2 P0.
7. Minor: the plan's own search hints for the 343,973 figure pointed at
   input tables, not the output table `kala_field` (G11) — corrected
   here for the record; no architecture change needed (memory headroom
   confirmed enormous, ~3-6% of 8Gi even generously sized).

## 1. Target state — UNCHANGED from v1.0 §1
Completeness (27 classes, explicit tier, seamless field, sealed
snapshot, 1024 nulls), brilliance (term-matrix EXPLAIN, cross-class
convergence, DVIPRAMĀṆA 27-vs-27, Brilliance Gate #1), speed (≤~60min
cold, surgical rebuilds). The mandate did not move; the path to it did.

## 2. Architecture (P-wave, revised)

**P0 CONSOLIDATION (NEW — must complete before P1/P2 design; this is
where v1.0 silently assumed settled ground that wasn't):**
  a. Adopt `DHARA_DESIGN_v1_0.md` properly: merge the doc from
     `sampurti/integration` to `main` AS-IS first (repo-of-record
     hygiene — a "frozen spec" every lane cites must actually be on
     main), THEN amend it in the same PR wave that lands P1/P2 to
     record the two-layer split and the null-engine pin below. Never
     amend an unmerged doc silently.
  b. NULL DEFINITION, pinned: `dhara_null.py`'s R-denominator
     (`resolution = 1/R`, the F-01 correction) is authoritative —
     confirmed the only live path (`stage5_null`'s block/finalize
     writer methods have zero live call sites now that `ENGINE_VERSION`
     is permanently `'analytic'` with no other value ever set). Move
     `NullResult` into `contracts.py` as ONE frozen dataclass with the
     R-denominator `resolution` property built in (not optional/getattr).
     DELETE the `getattr(null_result, 'resolution', None) or
     S5.null_resolution(...)` fallback in `writer.py` — it can only ever
     silently produce the WRONG formula now; make `.resolution` a
     required field, not a maybe-present property. `stage5_null.py`'s
     dead sampled-path methods get a deprecation-removal ticket (not in
     this wave — don't touch working dead code under time pressure, but
     name it so it isn't mistaken for live).
  c. NATIVE/PRATINIDHI RULING on G3: is chart-wide uniform vighna
     suppression (today's actual behavior) intentional, or should
     suppression be filtered per-class via `Route.suppressed_by` (what
     the docstring claims and what §4's per-class vighna columns
     assume)? This is a real astrological-model question, not an
     engineering one — PRATINIDHI rules with written rationale BEFORE
     P1 encodes either behavior as "the" architecture. Whichever way it
     rules, P1's Layer 0 raw suppression curves are identical either
     way (G3) — only the per-class PROJECTION (Layer 1) differs, so this
     ruling does not block starting P1's shared-sweep work.
  d. Naming/scope correction (applies everywhere downstream, no new
     work, just accuracy): every plan/kickoff/rails reference to
     "bg_class_priors" becomes "brahma_class_priors"; every reference to
     "the term matrix is the chart-level layer" becomes "Layer 0 is the
     new chart-level layer; the term matrix (§4) is Layer 1, a per-class
     projection of it."

**P1 TERM-MATRIX ENGINE (revised: explicit two layers, not one):**
  Layer 0 (NEW, chart-level, computed once per chart, per G1-G3's
  proof): lord stack per system/level at each clock knot; all 12 raw
  covariates x_j(t) at each knot; raw u_m(t) for every vighna instance
  in the chart. This is the actual P1 deliverable — it does not exist
  today in any form.
  Layer 1 (the EXISTING, UNCHANGED §4 `TermMatrixRow`/.npz schema,
  `dhara_term_matrix.py`): becomes a cheap per-class PROJECTION —
  select routes → relevance lookup (G1's cheap step) against Layer 0's
  shared lord stack; multiply Layer 0's shared x_j by β_j; project
  Layer 0's shared u_m per P0.c's ruling. Zero change to the .npz
  contract stage 9/EXPLAIN already consumes.
  Decade-seam fix rides here (was v1.0's W1): interior decade edges
  (d·H/10, d=1..9) join K in `assemble_knot_set` — exact, zero cost.
  CI: contiguity property test (gaps==0, full horizon) + Layer0→Layer1
  pointwise equivalence test against today's `terms_at()` (sampled
  knots, 1e-12) — this second test is the one that proves the refactor
  changed nothing observable for the 6 already-working classes.

**P2 VECTORIZED NULL (revised: pinned to ONE definition, contract fixed):**
  ln λ_r(t) = C(t) + E((t−δ_r) mod H), built from Layer 0 (P1) restricted
  to the coarse MD/AD/PD clock knots `dhara_null.py` already uses
  (`_NULL_COARSE_LEVELS` — unchanged, L1g parity preserved exactly).
  Per replicate: periodic shift/interp + cumsum + vectorized window-max.
  replicates=1024 (n3 restored — the OPT-N3 cut to 256 was an
  unauthorized scope reduction, voided per SM-R-8). Returns the NEW
  `contracts.NullResult` from P0.b — no ambiguity about which formula
  wins. Acceptance: equivalence vs the CURRENT `dhara_compute_null`
  (not stage5_null's — that path is dead, G7/follow-up) at R=8 on
  fixtures; FM-25 perf-gate test (hard time ceiling in CI).

**P3 TIERED 27-CLASS MODEL (the redesign G5 forced — was the biggest
  gap in v1.0):**
  The scale-invariance math is real (G5 confirms it end-to-end for
  window boundaries, null_p, adrishta_residual's ratio, and the
  stage6_salience ranking scalar) but is gated OUT OF REACH today by
  `hazard.baseline_rate()`/`stage4_field.require_baseline()`, which
  raise `ClassSkipped` unconditionally before any of that math runs.
  Revised P3 sequence (each step is now a NAMED, gated sub-task — not
  assumed done by "flip a flag"):
    P3-a SYNTHETIC-BASELINE PATH: a new, explicit, VERSIONED constant
       (e.g. `SHAPE_ONLY_SYNTHETIC_LIFETIME_COUNT = 1.0`, pinned in
       `contracts.py`, never silently chosen per-build — G5's forward
       caveat on cross-snapshot diffs) that lets `require_baseline`
       return a tagged synthetic value instead of raising, ONLY when
       the writer is explicitly running in shape_only mode for that
       class. `hazard.evaluate()`'s output (`HazardTerms`) gains a
       `baseline_is_synthetic: bool` field threaded through to every
       row it produces — a real, queryable tag, not an inferred one
       (§N.8 — this IS the earned-signal fix G5 demanded).
    P3-b ABSOLUTE-FIELD CENSUS (do this BEFORE writing any shape_only
       row, not after): grep+read every consumer of `kala_field_windows
       .expected_count`, `kala_field_null.max_stats`/`q_threshold`
       reaching a served surface (`kala_now_get`, `kala_ahead_get`,
       `kala_windows_get`, `kala_priority_get`, `stage65`'s
       `CONTRAST_MIN_DELTA_LN_LAMBDA` diff, and stage8_spec.py's
       already-confirmed `expected_count` leak) — for each, decide
       SUPPRESS (field becomes null when `baseline_is_synthetic`),
       RELABEL (field becomes a ratio/rank instead, per G5's proof
       these ARE invariant), or CONFIRMED-SAFE-AS-IS (rare — must show
       the invariance proof, not assert it). This census is itself a
       deliverable (a table in the PR description), reviewed by
       PARĪKṢAKA before P3-c.
    P3-c I-2 ADVERSARIAL GATE (unchanged from v1.0, now correctly
       sequenced AFTER P3-a/b exist to test): fresh opus refutation
       review + the scale-by-10x property test, run against the ACTUAL
       P3-a/b implementation, not the abstract claim. If refuted for
       any specific downstream consumer P3-b didn't already
       suppress/relabel: that consumer gets suppressed, not the whole
       tier canceled — G5 found the invariance holds broadly; the
       failure mode is a missed leak, which P3-b's census is built to
       catch, and P3-c is the adversarial double-check on that census.
    P3-d TIER-BASIS TABLE: per-class basis (calibrated | shape_only |
       not_applicable) — reads `brahma_event_ontology` per-row
       (`kill_switch_criteria`, `magnitude_floor`,
       `self_report_non_discriminating` — G8 confirmed no single flag
       column decides this; it's a judgment call per class, drafted by
       the conductor and RATIFIED by PRATINIDHI with written rationale,
       same as any classification affecting served claims).
    P3-e WRITER + SERVING: tier-aware build (calibrated path fully
       unchanged — the C-1 guard stays exactly as strict as today, so a
       fabricated absolute baseline remains structurally impossible);
       shape_only path uses P3-a's tagged synthetic constructor; every
       tier flows into `resolution_disclosure`-style facets already
       proven out by the gochara surface (Δ3's R2 work is the existing
       pattern to mirror, not invent).
  SCOPE HONESTY: if P3-b's census surfaces MORE leaks than P3-c's gate
  can close in this wave, shape_only ships for the consumers proven
  safe and stays deferred (not silently served unsafe) for the rest —
  logged as a named residual, never as done.

**P4 PRIORS RESEARCH LANE (scope corrected per G9 — parallel,
  non-blocking):** table is `brahma_class_priors`
  (`signal_type_class`/`fact_kind`/`class_prior`/`prior_basis`/
  `citation`/`source_ref`, `ratified_by`); the 6 `ne_v01` rows are the
  ONLY structurally-complete template (full citation + source_ref +
  `prior_basis='demographic_structural'`) — the other 171 rows are a
  DIFFERENT thing (signal-tradition weights, mostly wildcard/uncited)
  and must NOT be treated as partial coverage of the 21 remaining event
  classes. Each of the 21 needs genuinely new demographic sourcing (same
  protocol that ratified the 6: citation-backed, PRATINIDHI-ratified,
  blind-committed before use). Each ratification upgrades one class
  shape_only→calibrated via P5's surgical rebuild.

**P5 PIN MATRIX WIRED — unchanged from v1.0.** Now additionally the
  mechanism that makes P3's per-tier residual (some classes shape_only,
  some calibrated, evolving over time via P4) cheap to maintain: a P4
  ratification or P0.c's suppression ruling changing is a (stage×class)
  surgical rebuild, never a full 27-class re-run.

**P6 SERVING CONSISTENCY SWEEP — now concrete per G12 (was abstract in
  v1.0):** three real fixes, not a broad audit: (1)
  `platform-mcp/src/lib/ahead_autofile.ts`'s `KNOWN_EVENT_CLASSES`
  (static 27-entry mirror) → dynamic read or CI drift-guard against a
  live ontology query; (2) consolidate the two duplicated 5-item
  withhold lists (`ahead_autofile.ts` + `kala_upaya_diagnosis.ts`) to
  one shared source; (3) check whether `kala_upaya_diagnosis.ts`'s
  self-flagged missing primitive (a `query_event_ontology_class`-style
  MCP-side ontology query) was ever built — if not, build it, since it's
  the root cause both hardcoded lists exist to work around. Independent
  of the field build; Δ3's existing R5 lane, unchanged scope, runs this
  now rather than waiting.

Safety rails carried forward unchanged from the audit: bounded SET
LOCAL 900000ms (FM-24) · merge PR #1271 (FM-23) · `_RESUME_VERSION` 5→6
rides the first output-changing PR (FM-17) · GUC smoke-log T+3min ·
FM-21 hard trigger T+35 · 90-min rate gate.

## 3. Phasing (Δ1) — P0 now precedes everything

P-0 CONSOLIDATION: merge DHARA_DESIGN_v1_0.md to main; null-engine pin
    + contracts.py move + fallback deletion; PRATINIDHI ruling on G3;
    naming corrections across plan/rails/kickoffs. ~1 session, low risk
    (mechanical + one ruling), unblocks everything else.
P-A DESIGN (blind, per v1.0, now built on P-0's corrected ground):
    ENGINE spec (Layer 0/Layer 1 split), TIERS spec (P3-a..e sequence
    + the I-2 gate procedure), PRIORS protocol. Adversarial review
    (opus PARĪKṢAKA, FM-26 algorithm-vs-spec duty).
P-B BUILD (parallel sonnet lanes): L-ENGINE (P1) · L-NULL (P2) ·
    L-TIER (P3-a/b/d/e) · L-PIN (P5) · L-SERVE (P6, can start immediately,
    zero dependency on the others). Each lane TDD, PR→main, FM-25 perf
    tests where speed is claimed, FM-26 spec-citation duty.
P-C FIELD BUILD A7 ("PŪRṆA build"): all 27 classes, tiered. Rate-gated;
    GUC verify; FM-21 hard watch.
P-D PROOF: Δ2 parity battery (regenerated where P1's contiguity fix
    changes expected outputs — the EXPECTED-differences register
    documents exactly where) → G-P1 MCP gates → M4′ → DVIPRAMĀṆA
    (27-vs-27) → M5 + ablation → BRILLIANCE GATE #1 →
    ██ MARKER-POSTED: FIELD-INTEGRATED ██ → Δ3 R2-proof + R4.
P-E UPGRADE LOOP: P4 ratifications → P5 surgical upgrades → M-refresh.

## 4. Time budget — unchanged from v1.0 (grounding did not contradict
   the perf estimates; G11 confirmed memory headroom is enormous, G6
   confirmed no algorithmic scaling risk):
   Full 27-class cold build ≈45–60min · per-class upgrade: minutes ·
   weights/rho refit: seconds–minutes.

## 5. Governance
SM-R-10 records this revision (v1.0→v1.1, all 7 corrections), the P0
consolidation requirement, and refers P0.c (suppression semantics) to
PRATINIDHI explicitly. All SM-R-8/9 PARĪKṢAKA duties stand and gain one
more: **no PR may cite `DHARA_DESIGN_v1_0.md` as authority until P0.a's
merge lands** (citing an unmerged doc as settled doctrine is exactly
the kind of ground-truth gap this grounding pass was run to catch).
