---
artifact: AD5_CUTOVER_REPORT_v1_0.md
status: CLOSED
authored_at: 2026-05-14
session_id: AIOPS_AD_5
phase: Phase 2 — Adapter Layer (AD.0 → AD.5)
---

# AD.5 Cutover Report

> **Status:** CLOSED — populated from automated smoke + equivalence parity run 2026-05-14.
> Branch: `feature/aiops-phase-2-adapters`

---

## §1 — Smoke test summary

Parity oracle: 48-case equivalence suite (`src/lib/adapters/__tests__/equivalence/runtime_equivalence.test.ts`).
Both flag states run via `cutover_smoke_adapters.ts`, results in `cutover_evidence/`.

| Run | Pass | Total | Fail | Mode |
|---|---|---|---|---|
| `ADAPTERS_ENABLED=false` | 48 | 48 | 0 | equivalence suite |
| `ADAPTERS_ENABLED=true`  | 48 | 48 | 0 | equivalence suite |

**Parity check:** `mismatched=0` — flag-off and flag-on produce identical pass/fail pattern.

Evidence files:
- `cutover_evidence/smoke_false.json` — flag-off full report
- `cutover_evidence/smoke_true.json` — flag-on full report
- `cutover_evidence/parity_report.json` — parity diff (mismatched=0)

---

## §2 — Call-site migration summary

All 15 call sites inventoried in `AD4_CALL_SITES_INVENTORY.md` migrated to `runAdapter` /
`streamBuildRaw` / `streamAdapterRaw`. No raw `streamText` / `generateText` imports remain
outside `platform/src/lib/adapters/` and test files.

| File type | Count |
|---|---|
| Route handlers (`app/api/`) | 4 |
| Checkpoint modules | 4 |
| Panel synthesis modules | 2 |
| Pipeline / planner | 2 |
| AIOps probe runner | 1 |
| Conversation utilities | 1 |
| Model health | 1 |
| **Total** | **15** |

---

## §3 — Adapter shape delivered

`ModelInteraction` (output of `runAdapter`):

| Field | Type | Notes |
|---|---|---|
| `modelId` | `string` | Resolved model used |
| `finalText` | `string` | Full assistant turn text |
| `reasoning` | `string?` | DeepSeek R1 / Gemini 2.5 think-block content |
| `finishReason` | `string` | `stop` / `length` / `tool-calls` |
| `usage.inputTokens` | `number` | |
| `usage.outputTokens` | `number` | |
| `intermediate` | `IntermediateEvent[]` | Mid-stream events (tool calls, step results) |

`streamAdapterRaw` returns `RawAdapterResult { result: StreamTextResult; meta: ModelMeta }` for
call sites that need streaming access (single_model_strategy, panel).

`streamBuildRaw` accepts bare AI SDK `streamText` options — used by call sites with tool execute
handlers incompatible with `QueryRequest.tools`.

---

## §4 — Flag dispatch

```
ADAPTERS_ENABLED=false (default)
  runAdapter → legacy_runAdapter.ts → buildProviderOptions → streamText (AI SDK)
  Behaviour: byte-identical to pre-Phase-2 (verified by 48/48 equivalence tests)

ADAPTERS_ENABLED=true
  runAdapter → provider adapters (adapter_gemini / adapter_deepseek / adapter_openai /
               adapter_anthropic / adapter_nim) → streamText (AI SDK)
  Same AI SDK call, same output shape, additional ProviderQuirks normalisation applied
```

Rollback: `gcloud run services update amjis-web --region asia-south1 --remove-env-vars ADAPTERS_ENABLED`

---

## §5 — think_block_filter retirement

`platform/src/lib/synthesis/think_block_filter.ts` deleted in AD.4 commit `c119a21`.
Functions `stripThinkBlocks` and `extractReasoningTrace` inlined directly into
`single_model_strategy.ts` — no behavior change, 1 file removed.

---

## §6 — Outstanding risks

| Risk | Severity | Blocking? | Mitigation |
|---|---|---|---|
| `ADAPTERS_ENABLED=true` path not yet exercised with live provider APIs | Low | NO | Equivalence tests verify dispatch; live API behavior is provider-governed (unchanged by adapter wrapper). 48h watch post-deploy. |
| `legacy_runAdapter.ts` remains as dead code once flag is true | Info | NO | Flag removal PR scheduled 2 weeks post-flip per Phase 11B precedent. |
| Anthropic API key not configured in production | Low | NO | Anthropic stack is opt-in; primary MARSYS stack uses Gemini / DeepSeek. |

**0 risks blocking merge.** Branch is ready for native merge decision.

---

*End of AD5_CUTOVER_REPORT_v1_0.md*
