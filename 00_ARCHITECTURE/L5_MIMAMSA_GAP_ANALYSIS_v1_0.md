---
artifact: L5_MIMAMSA_GAP_ANALYSIS_v1_0.md
canonical_id: L5_MIMAMSA_GAP_ANALYSIS
version: 1.0
status: DRAFT — step-back gap analysis: what's missing to make L5 a SUPREME product, grounded in the project
authored_by: Cowork 2026-06-22
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  The deliberate step-back. Grounds the entire L5 design corpus against the actual project (mission,
  Ethical Framework §3.5, architecture principles B.1–B.12, the System Integrity Substrate, the n=1 risk
  stance, the PPL pre-registration commitment) and identifies EVERY gap that would elevate L5 from
  "complete" to SUPREME — organized by the native's five target qualities: REALISTIC · CURRENT ·
  RELIABLE · HIGH-CONFIDENCE · DETERMINISTIC. Two kinds of gap are surfaced: (1) existing project rigor
  we have NOT yet wired into L5, and (2) genuinely new capabilities the supreme version needs.
grounded_in:
  - MACRO_PLAN_v2_0.md (mission §"Ultimate goal"; §Ethical Framework; §3.5.A/E/G; n=1 risk stance; §IS substrate; LL.1–LL.10)
  - PROJECT_ARCHITECTURE_v2_2.md (B.1–B.12, esp. B.6 calibration, B.7 honest-scope, B.10 no-fabrication, B.11 whole-chart, B.12 completeness-refusal)
  - the L5 corpus (VISION, CAMPAIGN_PLAN, CONTRIBUTION_CONTROL, LEARNING_PROPAGATION, ELEVATION, INDEX)
  - LIFE_EVENT_LOG_v1_2.md (the n=1 reality: 57 events)
---

# L5 Mīmāṃsā — Supreme-Product Gap Analysis

> The question: *what stands between the L5 we've designed and a SUPREME L5 whose outputs are
> realistic, current, reliable, high-confidence, and deterministic?* Answered against the real project,
> not generic best-practice. Each gap is tagged: **[UNWIRED]** = rigor the project already commits to
> that L5 hasn't absorbed; **[NEW]** = a capability the supreme version needs that doesn't exist yet.

---

## §0 — What is already strong (so we build on it, not over it)

Before gaps, the honest credit — the design is already unusually disciplined:
- Overlay model with strict base/effective segregation (determinism preserved).
- Single-origin attribution solving cross-layer double-counting on the `bodha_msr_signals` keystone.
- Bounded + evidence-scaled modulation; the two-key lock (gate + high-confidence) on real impact.
- The negative-control battery as a **blocking** seal gate (self-pointed lie-detector).
- The contribution-control matrix (per-family, tier-labeled, portal/MCP parity).
- Honest n=1 stance; structural-prior-only no-LEL mode; no fabricated numbers.

The gaps below are what turns this strong foundation into a *supreme* one. They cluster cleanly under
the five qualities the native named.

---

## §1 — REALISTIC (outputs reflect reality, not the instrument's wishes)

*Goal: the instrument's claims match how the world actually behaves for this native — no inflation, no
artifact, no calendar-noise dressed as insight.*

| id | gap | tag | why it matters for SUPREME |
|---|---|---|---|
| **R-1** | **Base-rate anchoring.** A "career change predicted" verdict means nothing without the base rate of career changes. L5 must score predictions against the **base rate** of each outcome (how often does this happen anyway?), not just hit/miss. | [NEW] | Without base rates, an instrument that predicts common events looks accurate while saying nothing. Realistic = skill ABOVE chance, measured. |
| **R-2** | **Seasonality/confound null models** (from the research). Every time-anchored signal (esp. the external science families) must be scored against a season/weekday/temperature null, or the layer rewards calendar artifacts. | [NEW] | The deep research showed seasonality is the universal confound; realistic outputs require subtracting it. |
| **R-3** | **LEL entry-bias / chronological-completeness audit.** The project already names this (MACRO_PLAN M4 risk-b: "native selectively logs memorable events"). L5 inherits a biased ground truth unless it audits completeness + flags the bias in every calibration. | [UNWIRED] | A calibration computed on a cherry-picked diary is not realistic. The project already mandates the audit; L5 must run it. |
| **R-4** | **Effect-size realism, not just direction.** Report how MUCH a signal moves an outcome (with CIs), not merely that it does. Most real correlations are small; honest magnitude is what keeps the reading realistic. | [UNWIRED→B.6] | B.6 demands calibrated confidence; the supreme version reports effect SIZE honestly, killing overstatement. |

---

## §2 — CURRENT (outputs reflect the present state of the native's life + the present moment)

*Goal: the reading is anchored to NOW — the live transit moment, the latest LEL, the freshest calibration.*

| id | gap | tag | why it matters |
|---|---|---|---|
| **C-1** | **Transit-current binding.** L5's strongest external science family (X-GEOMAG, lunar) and the prediction windows are time-of-event specific. The reading must compute against the **current date/transit** at serve time, not a stale build snapshot. | [NEW] | "Current" literally means the answer for *today* uses today's sky + today's geomagnetic state. The L3 services exist; L5 must invoke them at serve time. |
| **C-2** | **LEL freshness propagation (designed, must be guaranteed).** The lifecycle (ELEVATION A.2) recomputes L5 on LEL update — but the SERVE path must always read the freshest overlay + show a freshness marker ("calibrated through event N, date D"). | [PARTIAL] | A reading that silently uses stale calibration isn't current. The freshness marker makes currency visible + auditable. |
| **C-3** | **Prediction-due sweep.** A background pass that detects predictions whose evaluation window has passed and surfaces them for scoring/journaling — so the instrument is always current on what's now testable. | [NEW] | The ph_pramana PR3 staging exists; L5 must operationalize the "these are now due" sweep, or currency decays. |
| **C-4** | **Currency of the external corpus.** Sunspot/geomagnetic indices, ephemeris are time-series that must be refreshed; the catalog citations should carry a review date. | [NEW] | "Current" includes the science staying current; stale indices = wrong event-day scores. |

---

## §3 — RELIABLE (same question → same answer; the instrument doesn't contradict itself)

*Goal: reproducible, stable, internally consistent, and resilient to its own failure modes.*

| id | gap | tag | why it matters |
|---|---|---|---|
| **RL-1** | **Reproducibility harness.** A test that runs the full L5 computation twice and asserts byte-identical overlays + verdicts. Determinism claimed everywhere must be MECHANICALLY proven. | [UNWIRED→B.10] | "Reliable" = re-running yields the same result. This is the single most important reliability test and it must be a seal gate. |
| **RL-2** | **The OFF==baseline invariant test** (already specified in LEARNING_PROPAGATION §6) elevated to a hard CI gate. | [PARTIAL] | Reliability of the toggle: learning OFF must equal pure classical, provably, every build. |
| **RL-3** | **Contradiction surfacing within L5.** The project has a CDLM/contradiction apparatus (L2). L5 should flag when its calibration says one thing and a classical signal says the opposite, rather than silently averaging. | [UNWIRED→B.7] | B.7 mandates publishing contradiction, not softening it. A reliable instrument names its internal disagreements. |
| **RL-4** | **Kill-switches + drift alerts** (the project's LL mechanisms each specify a kill-switch). L5 must implement: suspend a family/weight if its calibration error worsens over a rolling window; alert on learned-vs-classical divergence beyond tolerance. | [UNWIRED] | Reliability over time: the instrument must catch its own degradation and halt the offending channel automatically. |
| **RL-5** | **Integrity-substrate binding.** The project runs a System Integrity Substrate (§IS) parallel to the Learning Layer. L5's overlays/registries must register with drift_detector + schema_validator so they can't silently drift. | [UNWIRED→§IS] | The project's whole anti-drift machinery should guard L5's new tables, not just the old ones. |
| **RL-6** | **Degenerate-distribution guard.** Halt + flag if any computed attribution column (planet, house, signal-family, manifestation channel) collapses to one value across all rows where diversity is expected. | [NEW] | Lesson from the 2026-06-23 all-Jupiter `kala_convergence` bug: a silent hardcoded fallback wrote `Jupiter` to all 660 rows and only surfaced via a manual distribution check. This guard catches that entire class of "plausible-but-wrong constant" bug at build time, deterministically. The most important reliability lesson the project has produced. |

---

## §4 — HIGH-CONFIDENCE (when the instrument is sure, it has earned it; uncertainty is labeled)

*Goal: confidence is calibrated, not rhetorical — and the two-key lock means high-confidence claims are rare and trustworthy.*

| id | gap | tag | why it matters |
|---|---|---|---|
| **HC-1** | **A formal confidence ladder + provenance for every L5 output.** Each effective value carries: its base, its overlay, the evidence (n, leakage-status, held-out result), the families that touched it, and a final calibrated confidence band. The two-key lock reads this. | [PARTIAL→B.6] | High-confidence requires a defined, auditable path from evidence to confidence — not a hand-set number. |
| **HC-2** | **Calibration-of-the-calibration (meta-calibration).** Report reliability curves: when L5 says 70%, is it right ~70%? ECE/Brier as the instrument's OWN trustworthiness score, shown to the user. | [NEW] | This is what lets the instrument honestly claim high confidence: it has measured its own calibration error. |
| **HC-3** | **The discriminative-validity headline** (V7): the negative-control battery scoring ~null is the instrument's trust certificate. Surface it as a first-class confidence signal. | [PARTIAL] | "I am high-confidence AND I've proven I don't fire on known-fake signals" is the strongest possible trust claim. |
| **HC-4** | **Insufficient-evidence honesty (B.12 binding).** Below the min-n gate, the instrument says "insufficient evidence," never a number. B.12 (completeness-refusal) already mandates this posture; L5 must enforce it at the calibration layer. | [UNWIRED→B.12] | High-confidence is meaningless without the discipline to say "I don't know yet." B.12 is exactly this principle. |
| **HC-5** | **Pre-registration enforcement (§3.5.E / the PPL).** A prediction only counts toward calibration if it was registered BEFORE its window with a frozen falsifier — structurally excluding post-hoc rationalization. | [UNWIRED→§3.5.E] | The project already commits to pre-registration (the PPL). It is THE mechanism that makes confidence honest. L5 must consume the PPL emission-timestamp as the calibration admissibility key. |

---

## §5 — DETERMINISTIC (the layer computes; it never guesses)

*Goal: every L5 number is reproducible Python over defined inputs; judgment lives only at LLM synthesis.*

| id | gap | tag | why it matters |
|---|---|---|---|
| **D-1** | **The deterministic/judgment boundary made explicit + tested.** Mark every L5 computation as deterministic and assert (in CI) that no `mi_*` writer calls a generative LLM. The boundary is a rule; make it mechanical. | [UNWIRED] | Determinism is only real if it's enforced, not promised. A test that greps for LLM calls in L5 writers. |
| **D-2** | **Versioned, frozen formulas.** Every scoring/overlay formula carries a version; changing it is a version bump with a changelog (B.8). The same inputs + same formula version = same output, forever. | [UNWIRED→B.8] | Determinism across TIME: a verdict computed today must be reproducible next year under the same formula version. |
| **D-3** | **Seeded, declared external inputs.** Geomagnetic/sunspot/ephemeris series are pinned to a dated snapshot per calibration session, so a re-run uses the same data. | [NEW] | Determinism requires the inputs to be frozen too — otherwise "deterministic math" on shifting data isn't reproducible. |
| **D-4** | **Retrieval determinism for the serve path.** The LLM does the judgment, but it pulls deterministic ingredients via retrieval; the retrieval result for a fixed query+state must be stable (ranking, overlay applied), so the LLM reasons over a fixed substrate. | [NEW] | The judgment is the LLM's, but the INGREDIENTS must be deterministic, or "deterministic layer" leaks non-determinism upward. |

---

## §6 — Cross-cutting SUPREME elevations (beyond the five qualities)

A few gaps don't fit one quality — they elevate the whole instrument.

| id | elevation | tag | the supreme value |
|---|---|---|---|
| **S-1** | **The Prediction Journal as a first-class loop** — the native answers "did this happen?" against staged predictions; those answers ARE the LEL growth path (native already named this). Make it a designed surface, not an afterthought. | [NEW] | This is the engine of currency + the cure for n=1: it grows the evidence base through use. The single highest-leverage product feature. |
| **S-2** | **A "why" / provenance endpoint** — any output can be expanded into its full derivation: base → overlay → families → evidence → L1 fact → classical citation. | [PARTIAL] | Auditability as a user-facing feature is a differentiator; it's the instrument showing its work. |
| **S-3** | **Inter-rater / two-pass verdict discipline** (the project's two-pass pattern). Calibration verdicts (confirmed/denied/partial) get a second deterministic pass or a rubric-bound check to avoid single-path error. | [UNWIRED] | Reliability of the verdicts themselves; the project already uses two-pass elsewhere. |
| **S-4** | **Disclosure-tier honesty in the OUTPUT** (§3.5.B/G). Every reading carries its calibration disclosure: n, confidence, what's empirical vs prior vs structural. | [UNWIRED→§3.5.G] | The Ethical Framework mandates calibration disclosure; the supreme product wears its honesty visibly. |
| **S-5** | **Graceful degradation ladder.** Define exactly how the instrument behaves as evidence thins: full calibration → prior-only → structural-only → "insufficient." One coherent ladder, not ad-hoc. | [NEW] | A supreme product is honest AND useful at every evidence level, including zero. |

---

## §7 — The honest meta-gap (the one that governs all others)

**The deepest gap is not technical — it is temporal: the instrument cannot be highly-confident-and-reliable
on calibration TODAY, because the evidence (n=1, 57 events) does not yet exist.** The supreme move is to
accept this and design for it:

- **Today, L5's reliable+deterministic+high-confidence outputs are the STRUCTURAL ones** (the classical
  reading, the priors, the falsifiability staging, the negative-control validity proof). These are
  genuinely supreme now.
- **The empirical calibration becomes reliable+high-confidence OVER TIME**, as the Prediction Journal
  (S-1) grows the LEL. The instrument's honesty about this trajectory IS its credibility.
- So the supreme architecture is one that is **maximally valuable at n=1 today** (structural + prior +
  self-validation) and **monotonically improving** (every logged outcome tightens calibration), with
  the two-key lock ensuring it never overclaims along the way.

> **The supreme product is not one that claims to be calibrated now. It is one that is honestly
> structural now, visibly improving, and architecturally guaranteed never to fool itself or the user.**
> That is realistic, current, reliable, high-confidence, and deterministic — at every stage, including
> the hardest one (the beginning).

---

## §8 — Prioritized gap-closure recommendation

Not all gaps are equal. Ordered by leverage toward the five qualities:

**Tier A — foundational (do in the L5 core build):**
- HC-5 pre-registration enforcement (PPL admissibility key) — *the* honesty mechanism.
- RL-1 reproducibility harness + RL-2 OFF==baseline gate — determinism, mechanically proven.
- HC-4 / B.12 insufficient-evidence honesty + S-5 degradation ladder — high-confidence discipline.
- R-1 base rates + R-2 null models — realism floor.
- D-1/D-2/D-3 determinism enforcement (no-LLM test, frozen formulas, pinned inputs).

**Tier B — reliability + currency (do alongside core):**
- RL-4 kill-switches + RL-5 integrity-substrate binding.
- C-1 transit-current serve binding + C-2 freshness marker + C-3 due-sweep.
- R-3 LEL entry-bias audit.

**Tier C — supreme differentiators (the product moat):**
- S-1 Prediction Journal loop (highest product leverage; grows the evidence base).
- HC-2 meta-calibration + HC-3 discriminative-validity headline (the trust certificate).
- S-2 provenance endpoint + S-4 disclosure-tier output (visible honesty).
- S-3 two-pass verdicts.

---

## §9 — What this adds to the build plan (folds into the campaign)

These gaps become explicit acceptance criteria + phases in `L5_MIMAMSA_CAMPAIGN_PLAN`:
- The seal gate gains: reproducibility (RL-1), OFF==baseline (RL-2), no-LLM-in-L5 (D-1), negative-controls-null (E3), pre-registration-enforced (HC-5).
- A new asset/surface: the **Prediction Journal** loop (S-1) — likely an extension of `mi_bhavisya` +
  a serve-time + ingestion path.
- The serve path gains: transit-current binding (C-1), provenance endpoint (S-2), disclosure-tier
  output (S-4), the confidence ladder (HC-1).
- The integrity substrate registration (RL-5) for all `mimamsa_*` tables.

---

*End of L5_MIMAMSA_GAP_ANALYSIS v1.0. The L5 design is strong; the gaps to SUPREME cluster under the
native's five qualities. The deepest is temporal — calibration can't be high-confidence at n=1 today — and
the supreme answer is an instrument that is maximally valuable structurally NOW, monotonically improving
through the Prediction Journal, pre-registration-honest, mechanically deterministic, and architecturally
incapable of fooling itself. Tier-A gaps (pre-registration enforcement, reproducibility, insufficient-
evidence honesty, base rates, determinism enforcement) are the floor; the Prediction Journal loop is the
highest-leverage differentiator.*
