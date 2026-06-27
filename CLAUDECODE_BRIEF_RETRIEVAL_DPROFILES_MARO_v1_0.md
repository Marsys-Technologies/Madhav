---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_DPROFILES_MARO
version: 1.0
status: PARAMETERIZED — structurally complete; values resolved when inputs land (see §0)
created: 2026-06-27
author: Cowork (planning) — for execution by Claude Code in Antigravity
classification: CLAUDECODE_BRIEF — D-PROFILES + MARO (model-heterogeneity wave)
session_type: implementation — the shared Model-Aware Retrieval Orchestrator + 4 behavioral profiles
parent_design: RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_4 (§A MARO; principles 8,11; wave D-PROFILES)
depends_on: D1,D2,D3,D4 ; profile VALUES depend on D8 eval-harness measurement
detail_pass_required_when: D8 eval harness exists (to harden profile values from hypothesis → measured)
prereq_reading:
  - RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_0.md (§A whole model-heterogeneity spine; principles 8,11)
  - RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC_v1_0.md (the per-provider conflict matrix + obligations = the v1 profile hypotheses)
hard_constraints:
  - per-model intelligence lives in ONE shared core (MARO), not per-channel
  - channel asymmetry honesty: full loop control on chat; surface-shaping only on BYO-MCP
  - validate-and-repair all model JSON (#9); chart-agnostic (#14)
acceptance_criteria: see §4
---

# CLAUDE CODE BRIEF — D-PROFILES + MARO (parameterized)

> Model-heterogeneity is the central requirement on BOTH channels. This wave builds the shared MARO core and
> the four behavioral profiles. **PARAMETERIZED:** the profile STRUCTURE + initial hypotheses are specified
> now (from the provider spec); the MEASURED values get a detail-pass once the D8 eval harness can measure
> each model on our corpus.

## §0 — Parameterized inputs (resolve at detail-pass)
- `[resolved from D8]` — the measured per-model values: context-degradation curve, bundle-size sweet spot,
  structured-output drift rate, optimal tool granularity on OUR corpus. Until then, use the provider-spec
  hypotheses (e.g. DeepSeek ~128k floor + 5–12% JSON drift; Gemini fat-bundle; Opus fine-grained loop; GPT
  reason-then-act) as v1 defaults, clearly tagged as unmeasured.
- `[resolved from D7]` — the final MCP declaration mechanism (config/OAuth-scope/per-key/client-hint).

## §1 — MARO core
Shared model-aware orchestrator behind BOTH channels: reads the active family's profile and shapes tool
surface, bundle size, context budget, output validation, grounding, routing. Both the chat engine and the MCP
adapter consume it (single source — no per-channel duplication). Implement the per-family normalization the
provider spec mandates: tool-arg decoding (string for OpenAI/DeepSeek, object for Anthropic/Gemini), per-family
caching strategy, structured-output validate-and-repair (DeepSeek the weak link), context budgeting to the
smallest-supported floor, `[stable prefix]→[variable tail]` prompt structure.

## §2 — The four behavioral profiles (living artifact)
Emit `RETRIEVAL_MODEL_PROFILES` — one dossier per family (Anthropic/Gemini/OpenAI/DeepSeek) of concrete
orchestrator parameters. v1 from the provider spec hypotheses; each parameter tagged for D8 measurement. This
is a LIVING artifact — re-measured + bumped as models evolve. Pin model identifiers; track deprecations
(DeepSeek legacy retires 2026-07-24).

## §3 — Channel asymmetry
Chat: MARO owns the loop → full per-model optimization. BYO-MCP: MARO shapes surface/returns/grounding/budget/
validation but cannot control the client's loop → declared→profiled / undeclared→universal-best (DG: mechanism
from D7). Capability statement honest: no claim of controlling a stranger's loop.

## §4 — Acceptance criteria
- MARO core implemented + consumed by both channels (one source of model logic).
- Per-family normalization (arg-decode, caching, validate-and-repair, budgeting, prompt structure) working.
- `RETRIEVAL_MODEL_PROFILES` v1 emitted with hypotheses tagged for measurement; living-artifact versioning set.
- Declared→profiled / undeclared→universal MCP behavior wired (mechanism per D7).
- Detail-pass scheduled against D8 to harden values. chart-agnostic throughout.

*End of CLAUDECODE_BRIEF_RETRIEVAL_DPROFILES_MARO v1.0 (parameterized).*
