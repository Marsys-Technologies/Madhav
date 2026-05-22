---
artifact: ROLLOUT_DE_PREFLIGHT.md
version: "1.0"
status: PASS
captured: 2026-05-23
purpose: Pre-flight state capture for R11.D + R11.E flag rollout per R11V2_PHASE_DE_FLIP_PROMPT.md
---

# R11.D + R11.E Rollout — Pre-flight State

## Cloud Run service state

| Field | Value |
|---|---|
| Service URL | https://amjis-web-qm256lasva-el.a.run.app |
| Latest ready revision | amjis-web-00341-667 |
| Region | asia-south1 |
| Captured at | 2026-05-23 session open |

## R11 env-var state at pre-flight

Only `MARSYS_FLAG_R11V2_USE_ADAPTERS=true` is set. All other R11 flags are unset (using code-default `false`).

```
MARSYS_FLAG_R11V2_USE_ADAPTERS=true
```

## Pre-flight checks

| Check | Result | Detail |
|---|---|---|
| Service responding | PASS | amjis-web-00341-667 ready |
| MARSYS_FLAG_R11V2_USE_ADAPTERS=true | PASS | Prerequisite satisfied — dispatch wiring live (commit 77205869) |
| MARSYS_FLAG_R11D_PROMPT_LAYOUT=false | PASS | Unset (defaulting false) |
| MARSYS_FLAG_R11D_ANTHROPIC_CACHE=false | PASS | Unset (defaulting false) |
| MARSYS_FLAG_R11D_GEMINI_CACHE=false | PASS | Unset (defaulting false) |
| MARSYS_FLAG_R11E_ANTHROPIC_LOOP=false | PASS | Unset (defaulting false) |
| MARSYS_FLAG_R11E_GEMINI_LOOP=false | PASS | Unset (defaulting false) |
| MARSYS_FLAG_R11E_DEEPSEEK_LOOP=false | PASS | Unset (defaulting false) |
| MARSYS_FLAG_R11E_NVIDIA_LOOP=false | PASS | Unset (defaulting false) |

**Pre-flight verdict: ALL PASS. Proceeding to Stage D.**

## Rollout plan

| Stage | Flag | Watch | Operator action |
|---|---|---|---|
| D.1 | MARSYS_FLAG_R11D_PROMPT_LAYOUT | 15 min | Log watch only |
| D.2 | MARSYS_FLAG_R11D_ANTHROPIC_CACHE | 20 min | Send long-context anthropic query twice |
| D.3 | MARSYS_FLAG_R11D_GEMINI_CACHE | 20 min | Send long-context google query twice |
| E.1 | MARSYS_FLAG_R11E_ANTHROPIC_LOOP | 20 min | Send 2-tool fixture query (anthropic) |
| E.2 | MARSYS_FLAG_R11E_GEMINI_LOOP | 20 min | Send 2-tool fixture query (google) |
| E.3 | MARSYS_FLAG_R11E_DEEPSEEK_LOOP | 20 min | Send 2-tool fixture query (deepseek) |
| E.4 | MARSYS_FLAG_R11E_NVIDIA_LOOP | 20 min | Send 2-tool fixture query (nvidia) |

*ROLLOUT_DE_PREFLIGHT.md — captured 2026-05-23*
