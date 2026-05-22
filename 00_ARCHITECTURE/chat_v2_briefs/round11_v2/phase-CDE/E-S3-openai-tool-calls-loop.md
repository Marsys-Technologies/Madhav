---
canonical_id: R11E_E_S3
session_id: E-S3
title: OpenAI agentic loop — while (finish_reason === 'tool_calls'); use Responses API where available
phase: R11.E
depends_on: [E-S2]
flag: MARSYS_FLAG_R11E_OPENAI_LOOP (server-side, default false — HIGH risk)
client_side: no
authored: 2026-05-22
---

# E-S3 — OpenAI tool_calls Loop

## Context

OpenAI's Responses API has native loop support. For Chat Completions endpoint, use the while-loop pattern keyed on `finish_reason === 'tool_calls'`.

## Files in Scope

- `platform/src/lib/providers/openai/adapter.ts` — `tools()` returns OpenAI loop config; prefer Responses API where available.
- `platform/src/lib/synthesis/agentic_loop.ts` — extend.
- `platform/src/app/api/chat/consume/route.ts`.
- `platform/src/lib/config/feature_flags.ts`.

## Files MUST NOT Touch

- Anthropic/Gemini loop paths
- Stream-1 UI files

## Acceptance Criteria

1. With flag=true + OpenAI active: loop iterates correctly.
2. Responses API used when available; falls back to Chat Completions otherwise.
3. Integration test.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11CDE/platform
grep -n "finish_reason.*tool_calls\|Responses" src/lib/providers/openai/adapter.ts && echo "PASS"
npx jest --testPathPattern="E-S3|openai.*loop" --passWithNoTests
```

## Commit Template

```
feat(synthesis): OpenAI tool_calls agentic loop (E-S3, HIGH RISK)
```

## Decision Log

*(Executor: document Responses API availability; paste sample trace.)*
