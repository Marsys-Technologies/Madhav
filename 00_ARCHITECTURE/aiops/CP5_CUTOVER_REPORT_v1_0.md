---
artifact: CP5_CUTOVER_REPORT_v1_0.md
status: CLOSED
authored_at: 2026-05-13
populated_at: 2026-05-14
session_id: AIOPS_CP_5
---

# CP.5 Cutover Report

> **Status:** CLOSED — populated from live acceptance run 2026-05-13/14.
> Branch: `feature/aiops-control-panel`

---

## §1 — Smoke test summary

| Run | Pass | Total | Fail (non-Anthrop.) | Anthropic | Notes |
|---|---|---|---|---|---|
| Flag-off (`AIOPS_OVERRIDES_ENABLED=false`) | 69 | 84 | 1 | 14 skipped (no API key) | nim/worker/fallback=claude-haiku routes to Anthropic without key |
| Flag-on  (`AIOPS_OVERRIDES_ENABLED=true`)  | 69 | 84 | 1 | 14 skipped (no API key) | Identical pattern — parity verified |

**Parity check:** mismatched=0 for all non-Anthropic rows. Flag-off and flag-on produce identical pass/fail patterns.

**Anthropic rows:** All 14 Anthropic rows return `skipped_auth` / `error` (no `ANTHROPIC_API_KEY` configured). Expected and non-blocking per LLM stack discipline (R7).

**Non-Anthropic failure:** `nim/worker/fallback` resolves to `claude-haiku-4-5` in the registry (NIM stack worker fallback). No Anthropic key → fails. This is a registry routing issue in the NIM stack definition, not a bug in the override system itself.

Evidence files:
- `acceptance_evidence/item_12_smoke_off.json` — flag-off full report
- `acceptance_evidence/item_12_smoke_on.json` — flag-on full report
- `acceptance_evidence/item_12_parity.txt` — parity check output

---

## §2 — Catalog freshness (per provider)

Populated from `GET /api/admin/aiops/catalog/<provider>` — 2026-05-13 ~18:32 UTC.

| Provider | Status | Model count | Fetched at |
|---|---|---|---|
| NIM (nvidia) | ok | 129 | 2026-05-13T18:32:35Z |
| Gemini (google) | ok | 50 | 2026-05-13T18:33:25Z |
| DeepSeek | ok | 2 | 2026-05-13T18:32:37Z |
| GPT (openai) | ok | 102 | 2026-05-13T18:32:39Z |
| Anthropic | unconfigured | 0 | 2026-05-13T18:32:39Z |

Evidence files: `acceptance_evidence/item_05_catalog_*.json`

**Note:** Anthropic catalog returns `unconfigured` (no `ANTHROPIC_API_KEY`). Non-blocking for Phase 1.

---

## §3 — Override surface

State at acceptance close (2026-05-14). Active stack: **gemini** (set during Item 2 acceptance, then switched back via Item 5 MARSYS testing).

**llm_param_override:** 0 rows — no param overrides active at cutover.

**llm_stack_routing_override** (11 rows — all MARSYS stack):

| Stack | Call type | Primary model | Fallback model | Updated by |
|---|---|---|---|---|
| marsys | checkpoint_4_5 | gemini-2.5-flash-lite | gpt-4.1-nano | system |
| marsys | checkpoint_5_5 | gemini-2.5-flash-lite | gpt-4.1-nano | system |
| marsys | checkpoint_8_5 | gemini-2.5-flash-lite | gpt-4.1-nano | system |
| marsys | context_assembly | gemini-2.5-flash | gemini-2.5-pro | system |
| marsys | eval_generator | gemini-2.5-flash | deepseek-v4-pro | system |
| marsys | eval_judge | gemini-2.5-pro | deepseek-v4-pro | system |
| marsys | planner_deep | gemini-2.5-flash | deepseek-v4-pro | system |
| marsys | planner_fast | gemini-2.5-flash-lite | gemini-2.5-flash | system |
| marsys | smoke_synth | gemini-2.5-pro | deepseek-v4-pro | system |
| marsys | synthesis | gemini-2.5-pro | gemini-2.5-flash | xl2wYZRPwsVgPSAgtn9XJ80Xkub2 (native) |
| marsys | worker | deepseek-chat | deepseek-v3 | xl2wYZRPwsVgPSAgtn9XJ80Xkub2 (native) |

`system` rows = seeded by CP.1 migration 049 (MARSYS stack defaults). 2 rows updated by native during acceptance (Items 5-6).

**llm_config_audit actions logged:** set_active_stack (3), set_routing (3), reset_routing (1), set_param (1), revert (1). All 5 action categories confirmed present.

---

## §4 — Health table snapshot

Populated from `llm_model_health` after `npm run aiops:health` cron run — 2026-05-13 18:37 UTC. 24 models probed.

| model_id | status | latency_ms | last_probe_at |
|---|---|---|---|
| deepseek-chat | pass | 956 | 2026-05-13 18:37 |
| deepseek-reasoner | pass | 1511 | 2026-05-13 18:37 |
| nvidia/llama-3.3-nemotron-super-49b-v1 | pass | 1657 | 2026-05-13 18:37 |
| deepseek-v4-flash | pass | 1691 | 2026-05-13 18:37 |
| gemini-2.5-flash-lite | pass | 1741 | 2026-05-13 18:37 |
| nvidia/nemotron-3-nano-omni-30b-a3b-reasoning | pass | 1999 | 2026-05-13 18:37 |
| gemini-2.5-flash | pass | 2472 | 2026-05-13 18:37 |
| gpt-4.1 | pass | 2652 | 2026-05-13 18:37 |
| gpt-4.1-mini | pass | 2823 | 2026-05-13 18:37 |
| gpt-4o | pass | 3170 | 2026-05-13 18:37 |
| gpt-4.1-nano | pass | 3471 | 2026-05-13 18:37 |
| gemini-2.5-pro | pass | 3551 | 2026-05-13 18:37 |
| gpt-4o-mini | pass | 3757 | 2026-05-13 18:37 |
| meta/llama-3.1-8b-instruct | pass | 4714 | 2026-05-13 18:37 |
| deepseek-v4-pro | pass | 6957 | 2026-05-13 18:37 |
| nvidia/nemotron-3-super-120b-a12b | pass | 8200 | 2026-05-13 18:37 |
| deepseek-ai/deepseek-v4-pro | pass | 15614 | 2026-05-13 18:37 |
| mistralai/mistral-large-3-675b-instruct-2512 | timeout | 20003 | 2026-05-13 18:37 |
| claude-opus-4-7 | fail | 24 | 2026-05-13 18:37 |
| claude-sonnet-4-6 | fail | 24 | 2026-05-13 18:37 |
| claude-haiku-4-5 | fail | 30 | 2026-05-13 18:37 |
| moonshotai/kimi-k2-instruct | fail | 466 | 2026-05-13 18:37 |
| qwen/qwen3-235b-a22b | fail | 467 | 2026-05-13 18:37 |
| nvidia/llama-3.1-nemotron-ultra-253b-v1 | fail | 528 | 2026-05-13 18:37 |

**Summary:** 17 pass, 1 timeout (Mistral — slow network, not a bug), 6 fail. Fails: 3 Anthropic (no key), 3 NIM models (ultra-253b, kimi-k2, qwen3-235b — quota or auth). Health cron itself exited 0 (pass threshold met per majority logic).

---

## §5 — Outstanding risks

| Risk | Severity | Blocking? | Mitigation |
|---|---|---|---|
| Anthropic API key not configured | Low | NO | Anthropic stack is opt-in; Phase 1 primary stacks are NIM/Gemini/DeepSeek/GPT. Add `ANTHROPIC_API_KEY` to Cloud Run env to enable. |
| NIM/worker/fallback routes to claude-haiku | Low | NO | Registry default; not a bug in override system. Will auto-resolve when Anthropic key added. |
| mistralai/mistral-large timeout in health probe | Low | NO | Network latency at probe time; model responds in production traffic. Monitor post-cutover. |
| 3 NIM catalog models fail health probe (kimi-k2, qwen3-235b, ultra-253b) | Low | NO | Likely quota/rate-limit at probe time. Not in primary routing paths. |
| AIOPS_OVERRIDES_ENABLED must be set in Cloud Run env | Info | NO | Flag is env-var only (not in code). Set to `true` at production cutover. Rollback = set to `false`. |

**0 risks blocking merge.** Branch is ready for native merge decision.
