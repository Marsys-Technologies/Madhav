---
artifact: CLAUDECODE_BRIEF_B6_EVAL_HARNESS_v1_0.md
canonical_id: B6_EVAL_HARNESS_BRIEF
version: 1.0
status: FOR_NATIVE_REVIEW (the SEAL GATE — L2 Bodha does NOT close until this passes)
authored_by: Cowork (grounded in the existing coverage gate + answer-quality eval + the held-out LEL) 2026-06-19
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
scope: B6 ONLY — the SEMANTIC-COMPLETENESS + JUDGMENT-QUALITY eval harness that GATES the L2 Bodha seal. NOT an asset; a standing, re-runnable test suite. Depends on ALL 9 bo_* assets + the retrieval layer being built.
data_plane: ALWAYS prod via Cloud SQL Auth Proxy (127.0.0.1:5433)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
governing:
  - L2_BODHA_JUDGMENT_SUBSTRATE_STRATEGY_v1_0.md (v1.1 FROZEN — B6 tests JUDGMENT quality, not just coverage)
  - L2_BODHA_DISCOVERY_MISSION_v1_0.md (B6 must test DISCOVERY — the absolute goal)
  - L2_BODHA_STRATEGIC_FINDINGS_TRACKER_v1_0.md (F1 — B6 tests retrieval DE-DUP) + L2_BODHA_OVERALL_APPROACH (two pillars)
  - the held-out LEL (01_FACTS_LAYER/LEL_HELD_OUT_PARTITION_v1_0.md) — the lived-reality ground truth for falsifier checks
seeds_from:
  - platform/tests/retrieval/coverage_gate.test.ts (the SYNTACTIC coverage sibling — B6 is the SEMANTIC layer above it)
  - platform/python-sidecar/tests/test_mimamsa_answer_quality.py (the answer-quality eval pattern to follow)
target_files:
  - platform/tests/eval/l2_bodha_eval_harness.test.ts (or .py) — the committed, re-runnable suite
  - platform/tests/eval/fixtures/ — the curated questions + known-complete answer sets
  - CI wiring so the harness runs as the seal gate
must_not_touch: FROZEN orchestrator contract; the bo_* writers (it READS their output via retrieval); the held-out LEL partition (sacrosanct — never train/tune against it).
---

# B6 — The Semantic-Completeness + Judgment-Quality Eval Harness (the seal gate)

## §0 — Why B6 exists + what it tests (the distinction that matters)
The retrieval **coverage gate** (already built) proves SYNTACTIC coverage — every bodha_* table has ≥1 tool. That
is necessary but NOT sufficient. B6 proves SEMANTIC completeness + JUDGMENT quality: when the LLM answers a real
question, does it RETRIEVE everything relevant, WEIGH the evidence, STATE confidence, LEAD with what matters,
SURFACE the outlier, and DISCOVER the buried insight? **A green coverage gate can sit atop a layer that double-
counts, loses outliers, can't reach half the chart, and never discovers anything — B6 catches all of that.**
**L2 Bodha does NOT seal until B6 passes the native's thresholds.** It is a committed, RE-RUNNABLE suite (the
standing regression gate for synthesis quality), not a one-off.

## §1 — Non-negotiables
Deterministic test HARNESS where possible (the SCORING is deterministic against known-complete answer sets; the
LLM-under-test is the only non-deterministic part, run at a pinned model/temperature for reproducibility); the
**held-out LEL partition is SACROSANCT** (never tune against it — the falsifier checks read it ONCE, at eval, never
in training); no audience tier; the harness READS via the retrieval tools (it tests the real path the LLM uses,
not the DB directly — except for building the ground-truth answer sets, which ARE built deterministically from the data).

## §2 — Preconditions
1. All 9 bo_* assets built + verified (each brief's acceptance passed); the L2_bodha retrieval layer + coverage gate green.
2. The held-out LEL partition exists + is sealed (the lived-reality ground truth for §6).
3. A pinned LLM for the under-test runs (model + temperature fixed for reproducibility).

## §3 — THE TEST CORPUS (curated questions × known-complete answer sets)
Author a curated set of native-chart questions spanning every capability the layer must deliver. For EACH, build
the **known-complete answer set** DETERMINISTICALLY from the data (the ground truth — what a thorough acharya-grade
answer MUST include). Question classes (the layer's full surface):
- **domain questions** ("tell me about career/wealth/marriage/health…") → the domain's evidence ledger + the relevant signals + citations.
- **weight-of-evidence questions** ("what supports vs undercuts wealth?") → the ledger's support/oppose/verdict/confidence/dissents.
- **contradiction/contested questions** ("where is the chart conflicted?") → the contradictions + contested domains.
- **the-defining-chart question** ("what defines this chart?") → the signature_tier threads + the gestalt + central dynamics.
- **pivot/root questions** ("what one factor explains the most?") → the CDLM pivot + cross-subsystem root.
- **graph/mechanism questions** ("trace why X relates to Y") → the dispositor/significator path, narratable.
- **remedy questions** ("what helps career / should I remedy this?") → grounded remedies + the do-not-remedy cases + acharya-review flags.
- **discovery questions** ("tell me something I don't know / what would an acharya miss?") → the ranked bodha_discoveries.
- **cross-subsystem questions** ("does anything connect my health and career?") → the cross-subsystem edges/discoveries.
- **provenance/confidence questions** ("how sure are you about X?") → the epistemic state + citations.
- **outlier-recall questions** (a question whose true answer INCLUDES a far-from-template signal) → tests the lens wildcard.

## §4 — THE SCORED CHECKS (what B6 measures — the seal thresholds)
For each question, run it through the LIVE retrieval+planner+LLM and SCORE:
- **RECALL** — did the answer retrieve ALL items in the known-complete set? (the completeness pillar at the point of use). `recall_pct`.
- **PROVENANCE** — does every claim carry its tier + citation + fact_id? (a claim without provenance = a fail). `provenance_pct`.
- **JUDGMENT** — did it WEIGH evidence (support vs oppose, not a flat list), STATE confidence, and LEAD with what matters (the signature_tier / gestalt first, not buried)? `judgment_score`.
- **OUTLIER SURFACING** — for outlier-recall questions, did the significant non-template signal APPEAR (the anti-tunnel-vision guard works end-to-end)? `outlier_recall_pct`.
- **DISCOVERY** — for discovery questions, did it surface the genuinely buried, non-obvious, meaningful insight (not just re-state the obvious gestalt)? `discovery_quality_score`.
- **NO-FABRICATION** — did it invent anything NOT traceable to the substrate? (the gravest fail — must be 0). `fabrication_count`.
- **F1 DE-DUP** — does answering return each fact ONCE with its perspectives, or N times across assets? (token-bloat + weighting-distortion check). `dedup_pass` — the same fact_id appearing N× in one answer FAILS.
- **HONEST LIMITS** — when data is thin/contested/ayanamsha-fragile, does it SAY SO (the self-assessment)? `calibrated_humility_score`.

## §5 — THE NEGATIVE / ADVERSARIAL TESTS (prove the harness measures real retrieval)
- **Deliberately remove a tool** → the dependent recall DROPS (proves the harness measures real retrieval, not a fixed pass).
- **Deliberately strip provenance from a return** → provenance check FAILS.
- **Inject a fabricated claim** → no-fabrication catches it.
- **A template-only lens (no wildcard)** → outlier-recall FAILS.
These prove B6 isn't a rubber stamp.

## §6 — THE FALSIFIABLE-DISCOVERY CHECK (the research-instrument loop — against the HELD-OUT LEL)
bo_anveshana frames discoveries as falsifiable hypotheses (D5). B6 reads the **held-out LEL partition** (lived
events the build never saw) and checks: do the chart's discoveries/verdicts CORRESPOND to the native's actual life
events where the LEL has them? This is NOT a pass/fail seal gate (the instrument isn't calibrated yet — too few
outcomes) — it is the CALIBRATION-READINESS measurement: record hit/miss per discovery so L4/L5 can later build the
calibration curve. **The held-out partition is read ONCE, at eval, never tuned against (sacrosanct).**

## §6B — LEL DUAL-MODE (per LEL_TOGGLE_GOVERNING_PRINCIPLE — run BOTH modes, measure the delta)
LEL is semi-subjective, so its influence on responses is a USER TOGGLE over an always-LEL-free deterministic core
(the internal research always runs + produces a calibration overlay; the toggle gates only whether it reaches the
response). B6 therefore runs in BOTH modes:
- **LEL-OFF (the seal-gate baseline):** pure deterministic. ALL §4 thresholds (recall/provenance/judgment/discovery/
  no-fabrication/dedup/honest-limits) must pass HERE — the deterministic instrument is what seals. **The response
  must be provably free of ALL LEL-DNA — content AND anything derived from LEL (calibration/ranking/boosts) —
  asserted as ZERO `lel_origin`-tagged elements in the entire return (§3.1 of the LEL governing principle). A single
  LEL-tagged element surviving in a toggle-off response is a FAIL.**
- **LEL-ON:** the calibration overlay (from the §6 held-out validation) IS applied. Re-score; record the DELTA
  (does LEL-calibration improve recall/judgment/confidence-accuracy?). The delta is a calibration MEASUREMENT, not a
  seal threshold (the instrument isn't calibrated yet).
**The seal is gated on LEL-OFF (deterministic).** LEL-ON is measured, not gated. The held-out partition is read
once, sacrosanct, in both modes.

## §7 — THE SEAL GATE
L2_BODHA_CLOSE seals ONLY when: recall ≥ threshold, provenance = 100% (every claim cited), fabrication = 0,
dedup_pass = true, outlier-recall ≥ threshold, judgment + discovery scores ≥ thresholds (native sets the bars).
A sub-threshold run is a retrieval/planner/asset FIX, not a seal. The harness is COMMITTED + CI-wired so it stays
a standing regression gate (a future change that regresses synthesis quality fails CI).

## §8 — Acceptance
- [ ] Curated question corpus across all 11 classes (§3) + deterministically-built known-complete answer sets.
- [ ] Scored checks (§4): recall / provenance / judgment / outlier / discovery / no-fabrication / F1-dedup / honest-limits.
- [ ] Negative/adversarial tests (§5) prove the harness measures real retrieval (removing a tool drops recall, etc.).
- [ ] Falsifiable-discovery check vs the HELD-OUT LEL (§6) — calibration-readiness measurement; held-out never tuned against.
- [ ] **LEL DUAL-MODE (§6B):** seal gated on LEL-OFF (deterministic, provably LEL-free); LEL-ON re-scored + delta measured (not gated). Held-out sacrosanct both modes.
- [ ] Committed + CI-wired as the standing seal/regression gate; pinned LLM for reproducibility.
- [ ] Seeds from the existing coverage_gate + answer-quality eval; builds the SEMANTIC layer above the syntactic gate.

---

# §ELEVATION (toward supreme)
- **B6-E1 [research] Cross-chart eval scaffold** — the harness structured so the SAME question corpus runs on
  future charts (the L5 research path: does the instrument's judgment quality hold across natives?).
- **B6-E2 [honesty] The "acharya disagreement" set** — questions where acharyas genuinely DIFFER; score whether
  the instrument PRESENTS the disagreement (not forces a false consensus) — tests the L0-reasoning bridge.
- **B6-E3 [discovery] Discovery novelty audit** — track which discovery CLASSES the harness finds across runs (feeds the L2→L5 novelty register).
- **B6-E4 [calibration] Confidence-calibration slots** — per-confidence-band hit-rate frame (when the instrument says 0.8, how often right — awaiting L5 outcomes).

---
*End of B6_EVAL_HARNESS v1.0. The SEAL GATE: proves SEMANTIC completeness + JUDGMENT quality, not just syntactic
coverage. A curated question corpus × deterministically-built known-complete answer sets, scored on recall /
provenance / judgment / outlier-surfacing / discovery / no-fabrication / F1-dedup / honest-limits, with
adversarial tests proving it measures real retrieval, and a falsifiable-discovery check against the SACROSANCT
held-out LEL (calibration-readiness, not yet a gate). L2 Bodha seals ONLY when B6 passes the native's thresholds;
the suite is committed + CI-wired as the standing synthesis-quality regression gate. This is what proves the layer
delivers the acharya's JUDGMENT + the discovery mission — not just a complete, retrievable library.*
