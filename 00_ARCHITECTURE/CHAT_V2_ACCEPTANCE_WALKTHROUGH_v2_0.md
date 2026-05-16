---
name: Chat V2 Acceptance Walkthrough v2.0
canonical_id: CHAT_V2_ACCEPTANCE_WALKTHROUGH_v2_0
version: 2.0
status: PENDING OPERATOR — awaiting native walkthrough
authored: 2026-05-17
author: Claude Code executor (remediation session)
predecessor: CHAT_V2_ACCEPTANCE_WALKTHROUGH_v1_0.md (2026-05-16, 11 areas PASS)
remediation_item: C.8
---

# Chat V2 Acceptance Walkthrough — v2.0

## §1 Purpose

Re-verify Chat V2 against the specific audit findings in `CHAT_V2_VERIFICATION_AUDIT_v1_0.md §5`
after the Phase B remediations. v1.0 was conducted against the original 28 master-gate criteria;
v2.0 adds the 10 audit-finding verification matrix.

## §2 Prerequisites

- MARSYS_FLAG_CHAT_V2_ENABLED=true deployed (Phase D.1 merged)
- Super-admin session active
- All Phase B PRs merged to main (confirmed: #23–#33)

## §3 Verification Matrix — Operator Fill

For each finding: observe the described behavior, mark PASS/FAIL, add notes.

| Finding | What to verify | Expected behavior | Verdict | Notes |
|---|---|---|---|---|
| O1 (cost data part) | Complete a query; open details drawer immediately (before reload) | Input tokens, output tokens, cost (USD) all show non-dash values | | |
| O2 (panel mode toggle) | Click panel mode toggle; submit a panel-eligible query | Toggle state persists in sessionStorage; dissent tabs visible in answer | | |
| O3 (stage progress) | Watch stage stepper during a live query | Classify → Compose bundle → Tool fetch → Synthesis stages visible with checkmarks | | |
| O3 (tool cards) | Same query | At least one ToolCallCard renders during retrieval phase | | |
| O4 (user_id PPL) | Submit a time-indexed prediction answer; open PPL log modal | Modal submits cleanly; no "user_id missing" error in logs | | |
| O5 (citation format) | Ask a question that references MSR signals | Answer contains `→ SIG.MSR.NNN` inline citations that render as `[N]` chips | | |
| O6 (streamdown) | Submit a query expecting markdown | Bold, italic, code blocks, KaTeX, GFM tables render correctly during streaming | | |
| O7 (PDF upload) | Upload a PDF; query about its content | If Vertex DU wired: real extracted text; if not: fixture/deferred marker | | |
| O8 (GCS upload) | Upload an image | If GCS wired: real signed URL; if not: fixture/deferred marker | | |
| O9 (metadata reload) | Complete a query; reload page; open details drawer | Model, query class, latency, disclosure tier still populated (from persisted metadata_json) | | |
| O10 (regenerate) | Click regenerate on an existing assistant message | Old assistant turn removed; new streaming response begins | | |

## §4 Overall Verdict

**Status**: PENDING OPERATOR ACTION  
**Walkthrough by**: _______________  
**Date**: _______________  
**Verdict**: _______________

Sign off here when complete:

```
closed_by: <name>
closed_at: <ISO timestamp>
verdict: PASS / FAIL
notes: <any deferred items acceptable>
```
