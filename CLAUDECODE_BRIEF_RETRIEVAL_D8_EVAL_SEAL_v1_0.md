---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_D8_EVAL_SEAL
version: 1.0
status: PARAMETERIZED — structurally complete; specifics resolved when inputs land (see §0)
created: 2026-06-27
author: Cowork (planning) — for execution by Claude Code in Antigravity
classification: CLAUDECODE_BRIEF — D8 eval harness + governance + seal (closes the master artifact)
session_type: implementation — the gate that seals the retrieval system
parent_design: RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_4 (wave D8; principle 10)
depends_on: D1–D7 + D-PROFILES
detail_pass_required_when: the system is built enough to evaluate end-to-end
prereq_reading:
  - RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_0.md (wave D8; principle 10 eval-gates-seal)
  - RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC_v1_0.md (eval section — retrieval vs generation, faithfulness, judge calibration)
hard_constraints:
  - the eval harness GATES the seal — no retrieval seal without it (principle #10)
  - evaluate trajectories, not just outputs; calibrate the LLM judge against a human gold set
  - chart-agnostic eval (multiple charts, never native-only)
acceptance_criteria: see §4
---

# CLAUDE CODE BRIEF — D8: EVAL HARNESS + GOVERNANCE + SEAL (parameterized)

> The eval harness both grades retrieval quality AND hardens the D-PROFILES values from hypothesis to measured
> fact. It gates the seal. PARAMETERIZED: structure set now; golden set + thresholds resolved when the system
> is evaluable end-to-end.

## §0 — Parameterized inputs (resolve at detail-pass)
- `[resolved from D1–D7]` — the built system to evaluate.
- `[resolved in-wave]` — the golden set (synthetic + human-verified subset), the judge calibration thresholds
  (never copy blog numbers — calibrate against 50–200 human-rated items), the seal criteria.

## §1 — Eval harness
- **Decompose** retrieval vs generation. Retrieval: recall@k (the ceiling), nDCG/MRR where labels exist;
  label-free fallback = context precision/recall. Generation: **faithfulness/groundedness** as the headline
  (decompose answer into atomic claims, verify each against retrieved context — catches true-but-ungrounded).
- **Trajectory eval** (agentic routes): score tool choices, reasoning, loop termination, per-step latency
  (the D2 trajectory logs feed this).
- **LLM-as-judge calibrated** against a human gold set; report judge–human correlation; re-baseline on model change.
- **Per-model**: run the harness across Anthropic/Gemini/OpenAI/DeepSeek to HARDEN the D-PROFILES values
  (context-degradation curve, output-drift, bundle sweet spot on OUR corpus) — the detail-pass for D-PROFILES.

## §2 — Governance + debt closure
- Reconcile the `gemini`-vs-`nim` model-default discrepancy (deferred from DG4).
- Register the retrieval primitives + the new artifacts in the (regenerated) CAPABILITY_MANIFEST; wire
  drift_detector/schema_validator coverage; version/status/changelog on every primitive.
- CI hard gate on the golden set; rolling-window faithfulness alerts on sampled prod.

## §3 — Seal
- Red-team pass (macro-phase-close cadence requires it before seal).
- Confirm all 14 principles satisfied end-to-end (esp. #3 cited-numbers, #14 chart-agnostic, F1 dedup).
- Emit the seal artifact; update CURRENT_STATE + the campaign tracker; mark the master design built.

## §4 — Acceptance criteria
- Eval harness: retrieval/generation split, recall@k + faithfulness, trajectory + span scoring, calibrated judge
  (correlation reported), golden set, CI gate. Runs across all 4 model families.
- D-PROFILES values hardened from measurement; living artifact updated.
- Governance debt closed (model-default, manifest registration, drift/schema coverage).
- Red-team done; 14 principles verified; seal emitted; CURRENT_STATE + tracker updated.
- Eval is chart-agnostic (multiple charts); no native-only evaluation.

*End of CLAUDECODE_BRIEF_RETRIEVAL_D8_EVAL_SEAL v1.0 (parameterized).*
