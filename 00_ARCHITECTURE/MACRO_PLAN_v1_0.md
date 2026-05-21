---
artifact: MACRO_PLAN_v1_0
document: MARSYS-JIS MACRO PLAN — STRATEGIC ARC
project_name: Abhisek Mohanty — Jyotish Intelligence System (MARSYS-JIS)
subject: Abhisek Mohanty (b. 1984-02-05, 10:43 IST, Bhubaneswar)
version: 1.0
status: SUPERSEDED by MACRO_PLAN_v2_0.md (closed 2026-04-23 at Step 5 of the Step 0→15 governance rebuild)
superseded_by: 00_ARCHITECTURE/MACRO_PLAN_v2_0.md
superseded_on: 2026-04-23
author: Abhisek Mohanty (native, project owner)
date: 2026-04-23
purpose: >
  Strategic orientation layer for the MARSYS-JIS project. Frames the ten macro-phase
  arc (M1–M10) and the cross-cutting Learning Layer substrate. Read once per
  session for orientation only; execute only the currently-scoped phase. This
  document was introduced to prevent session-level scope drift in M2 work by
  giving every session a stable view of where the current phase sits in the
  full arc.
audience:
  primary: Any LLM session working on MARSYS-JIS, current and future
  secondary: Abhisek Mohanty (native, project owner)
  tertiary: Independent classical-Jyotish acharyas reviewing the corpus
operational_rule: >
  Read this once per session for orientation. Execute only the currently-scoped
  phase. Do not pre-build infrastructure for later macro-phases.
changelog:
  - v1.0 (2026-04-23): Initial macro plan establishing ten macro-phase arc and
    cross-cutting Learning Layer substrate. Introduced to prevent session-level
    scope drift in M2 work.
  - SUPERSEDED 2026-04-23 at Step 5 of the Step 0→15 governance rebuild.
    Successor: MACRO_PLAN_v2_0.md (architectural revision per
    MACRO_PLAN_REVISION_SPEC_v1_0.md; red-team verdict PASS_WITH_FIXES per
    MACRO_PLAN_REDTEAM_v1_0.md). Content below retained for historical
    reference only — do not cite as current.
---

> **⚠ SUPERSEDED** — This file is historical. The current Macro Plan is **`MACRO_PLAN_v2_0.md`** (published 2026-04-23 at Step 5 of the Step 0→15 governance rebuild). v2.0 is an architectural revision: per-phase schema (entry/exit/dependencies/risks/quality gate), System Integrity Substrate (IS.1–IS.9) parallel to the Learning Layer, Mirror Discipline per native directive ND.1, plus Ethical Framework / External Dependency Graph / Meta-Governance / Multi-Agent Collaboration / Post-M10 Framing. Read v2.0 for any current work. v1.0 content below is retained for lineage tracing only — it is **not authoritative**.

# MARSYS-JIS Macro Plan — Strategic Arc v1.0

**Status:** Orientation document. Defines the full project arc across macro-phases.
**Audience:** Any LLM session working on MARSYS-JIS, current and future.
**Operational rule:** Read this once per session for orientation. Execute only the currently-scoped phase. Do not pre-build infrastructure for later macro-phases.
**Date:** 2026-04-23
**Owner:** Abhisek Mohanty

---

## Why this exists

The detailed phase plans in `00_ARCHITECTURE/` describe the current work in depth. They do not describe where the current work sits in the full arc. Without that frame, any session risks over-engineering the present phase or under-engineering it by missing forward dependencies. This document fixes the frame.

## Ultimate goal

Build an LLM-operated Jyotish instrument that, for this native, (1) reads the chart with acharya-grade depth, (2) surfaces patterns and contradictions across layers and systems that no individual astrologer could hold in working memory, (3) makes time-indexed, probabilistic, calibrated predictions testable against lived reality and correctable from outcomes. Then extend the method beyond this native so the instrument becomes a research tool for astrology as a discipline.

## The ten macro-phases

**M1 Corpus Completeness** *(mostly done)*. L1 facts v8.0, L2 signals (MSR 437→499), L2.5 synthesis. Known gaps: CGM not rebuilt on v8.0, four L3 reports stale, GAP.13 open.

**M2 Corpus Activation** *(current work)*. Graph-RAG + Discovery Engine. Turns static corpus into LLM-navigable graph+vector. Batch discovery surfaces patterns, resonances, contradictions, clusters. This is the B.0–B.10 plan.

**M3 Temporal Animation.** Add time. Vimshottari and cross-check dashas, transits, Varshaphala (Tajika), KP sublord timing, shadbala over time. Produces a time-indexed event surface: for any date, which signals are lit, dormant, ripening.

**M4 Empirical Calibration.** The Life Event Log becomes the ground-truth spine. Every significant life event maps to which signals should have fired and whether they did. Produces per-signal, per-domain calibration tables. First macro-phase where learning algorithms fire on real data.

**M5 Probabilistic Model.** Dynamic Bayesian Network over (signals × time) → (life-domain outcomes). Signal embeddings become learned vectors. Outputs become probabilities with confidence intervals.

**M6 Prospective Testing.** Forward predictions with falsifiable windows. Automated scoring at window close. Counterfactual learning from misses. The only real accuracy measurement in the system.

**M7 Population Extension.** Cohort beyond this native — family, public figures with reliable birth data, a research corpus. Desha-kala-patra (place-time-person) modulators learned. Fine-tuning of LLM components becomes feasible for the first time.

**M8 Classical Text Cross-Reference.** Indexed corpus of BPHS, Phaladeepika, Saravali, Uttara Kalamrita, Jaimini Sutra, Prashna Marga, Hora Sara, KP texts. Every discovered pattern cross-referenced to classical attribution. Where classical claims systematically hold or fail becomes a finding in itself.

**M9 Multi-School Triangulation.** Parashari + Jaimini + Tajika + KP + Nadi + BNN + Yogini. Convergence across lenses as a precision signal. Humans cannot do this live; the instrument can.

**M10 LLM-Acharya Interface and External Validation.** Full wiring. Blind-test against independent acharyas reading the same chart. Publish the methodology.

## The Learning Layer — a cross-cutting substrate

Progressive calibration is woven through M2–M10, not treated as a single phase. It sits in `06_LEARNING_LAYER/` as a sibling to the Discovery Layer.

Ten mechanisms, roughly in order of feasibility: signal weight calibration, graph edge weight learning, embedding space adaptation, prompt optimization, retrieval ranking learning, plan selection learning, discovery prior shaping, Bayesian model updating, counterfactual learning from misses, LLM fine-tuning. The first four become available during M2. The rest activate at M4, M5, M6, M7 respectively.

**Learning discipline — non-negotiable across all macro-phases:**
1. Classical priors are locked; learning modulates, never overwrites.
2. Bayesian posterior framing with tight priors. Frequentist overfit is rejected.
3. Every parameter update requires ≥3 independent observations and passes the two-pass Gemini/Claude protocol.
4. Held-out prospective data is sacrosanct; the model never sees outcome before prediction.
5. Every learned parameter is auditable, reversible, versioned, and logged to the ledger.
6. The prior is the classical corpus. Evidence earns the right to modulate the prior; it never automatically does.

**n=1 risk:** with a single native, overfit is the dominant statistical risk, not underfit. Every mechanism above is designed to resist retrofit. New parameters live in shadow mode for N observations before influencing downstream components.

## What is concurrent with code work

Two non-code workstreams run in parallel with any code macro-phase:

**Life Event Log.** Populated continuously on the native's cadence. Prerequisite for M4. Start immediately; do not defer.

**Prospective prediction logging.** Every falsifiable claim the system surfaces is logged with a verification window the moment it appears. The first six months of this data cannot be manufactured later. Start the day the discovery engine produces its first forward-looking output.

## Scope boundary for any single session

A session executes within the currently-active macro-phase and the currently-active phase-plan expansion. It does not:
- Pre-build infrastructure for later macro-phases
- Anticipate schemas for later data that has not arrived
- Optimize for future use cases at the cost of current clarity

It does:
- Carry forward Learning Layer scaffolding hooks as specified in the current phase plan
- Preserve extensibility where the Macro Plan names a downstream dependency
- Flag any current decision that would compromise a later macro-phase
- Update `SESSION_LOG.md` at close with current position in the macro arc

## Change control

The Macro Plan is versioned. Changes require explicit native approval and a version bump. Phase-plan details below M2 are not part of the Macro Plan; they live in their own documents and update independently.
