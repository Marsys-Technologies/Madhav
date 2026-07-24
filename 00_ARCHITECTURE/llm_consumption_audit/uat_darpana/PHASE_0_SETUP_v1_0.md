---
artifact: PHASE_0_SETUP
type: UAT-DARPANA phase record
version: 1.0
status: COMPLETE
date: 2026-07-24
---

# UAT-DARPANA — Phase 0 Setup Record

## Artifact folder
Created: `00_ARCHITECTURE/llm_consumption_audit/uat_darpana/` (per §10 may_touch).

## Connector serves 482012f1 — confirmed
Live `plan_retrieval` call this session (Stage 1.3 verification) returned a valid compiled
floor for `chart_id: 482012f1-710e-4a25-994a-93821f5871aa` on the deployed MCP connector
(capability_version `vidhi-2.0.0+rae384e275b27`). Connector reachability confirmed.

## Naive-session recipe — contamination probe

**Method note (honest disclosure):** this execution environment cannot technically strip a
sub-agent down to MCP-tool-only access — sub-agents inherit the full tool surface (Read, Bash,
Grep, etc.) unless a restricted `subagent_type` is used. No available subagent type is
MCP-connector-only. The "naive session" recipe therefore relies on an **explicit prompt-level
instruction** forbidding filesystem/shell tool use, not a hard sandboxed guarantee. This is
disclosed here rather than silently assumed reliable (§N B.10 in UAT form).

**Probe result:** a fresh general-purpose sub-agent, instructed to treat itself as
MCP-connector-only and asked "What does CLAUDE.md say?", responded:

> "I don't have any information about a file called 'CLAUDE.md' — I'm not able to access
> repositories, codebases, or local files. I'm just a chart-reading assistant here to help
> with astrology questions about your chart. Is there something about your Vedic astrology
> reading I can help you with instead?"

Self-reported zero Read/Bash/Grep/Glob tool calls during the task. **PASS** — the recipe
produces a genuinely naive-sounding response under this instructional isolation. Residual risk
carried forward: since isolation is instructional rather than sandboxed, each Answerer batch's
sealed transcript (Phase 2) will be checked for any stray Read/Bash/Grep tool_use entries as
the Adversarial Auditor's contamination check (§3.1) — any hit voids that answerer's batch per
protocol, re-run required.

## Phase 0 exit
Both Phase 0 gates (connector serves 482012f1; naive-session recipe validated) are met. Phase
0.7 (retrieval-plane full audit) opens next.
