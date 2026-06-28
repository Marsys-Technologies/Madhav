---
canonical_id: RETRIEVAL_AUTONOMOUS_RUN_OUTCOME
version: 1.0
status: CURRENT — post-run state record + open-item triage
created: 2026-06-28
author: Cowork (planning) — recording the autonomous swarm run result, for native Abhisek Mohanty
classification: run outcome + remediation triage
parent: CLAUDECODE_BRIEF_RETRIEVAL_AUTONOMOUS_SWARM_CHARTER_v1_0 (the run this records)
changelog:
  - v1.0 (2026-06-28): Records the overnight autonomous run. Verdict SUBSTANTIALLY COMPLETE — MCP channel sealed, chat channel pending. Triages 3 open items (chat migration BLOCKING, faithfulness eval MODERATE, deepseek retirement TIME-SENSITIVE).
---

# RETRIEVAL AUTONOMOUS RUN — OUTCOME + TRIAGE (v1.0)

> The overnight swarm run executed the D0→D8 build per the charter. **Verdict: SUBSTANTIALLY COMPLETE — MCP
> channel sealed, chat channel pending.** All hard gates PASS; 14/14 principles PASS; `retrieval-d8-sealed`
> tag set. The final audit logged FAIL(7/10) only because two items were intentionally not closed before the
> audit fired (the chat migration — deferred by design as too risky mid-run; and the morning report — now
> written). This record captures what's sealed and triages what's open.

## §1 — What's sealed and working

| Component | Status |
|---|---|
| D1 contract (types.ts, chart_agnostic_gate.ts, 33 capabilities retrofitted) | ✅ SEALED |
| D2 router (5-class classifier, mandatory chart_id gate) | ✅ |
| D3 grounding spine (§N.5 detector — found 3 REAL violations in live lahiri_chitrapaksha data) | ✅ |
| D4 graph (traverse_chart_graph, mig-325 schema) | ✅ |
| D5 fan-out (28 new L2–L5 capabilities) | ✅ |
| D-PROFILES / MARO (Anthropic/Gemini/OpenAI/DeepSeek) | ✅ MEASURED v1.1.0 |
| D6/D7 MCP channel (12 consolidated tools; native contamination remediated in 5 files) | ✅ |
| D8 seal (14/14 principles, eval harness, red-team, `retrieval-d8-sealed` tag) | ✅ |

**Notable wins:** the chart-agnostic gate held and remediated 5 contaminated files; the §N.5 detector found
3 genuine computed-value-drift violations in live data (a real correctness catch, not a false positive); the
swarm correctly REFUSED to migrate the chat channel without a scoped brief (recovery discipline working —
queued the risk instead of compounding it).

## §2 — Open items (triaged)

### ISSUE-1 — Chat channel still on lib/retrieve legacy path. **BLOCKING.**
`/api/chat/consult` and a broad surface (code-verified: 40+ files reference `lib/retrieve`/`msr_sql` across
the chat route, pipelines, gateway, contract, MCP primitives, and tests) still use the old system. The chat UI
bypasses all D1–D8 work until migrated. The swarm correctly declined to do this unscoped mid-run.
→ **Remediation:** `CLAUDECODE_BRIEF_RETRIEVAL_D7_CHAT_MIGRATION` (authored alongside this record). Scoped,
per-caller repoint, parity-tested, under the reverse-citation gate. This is the one item that gates "fully done."

### ISSUE-4 — Faithfulness eval deferred. **MODERATE.**
Routing correctness is confirmed (all 15 golden queries route correctly across all 4 families), but answer-
quality (faithfulness/groundedness) scoring needs a live judge-model run against the populated prod DB. The
harness EXISTS; it just hasn't been run with a judge model.
→ **Remediation:** run the existing harness against prod with a judge model (Gemini Pro primary per model
policy; never native-only — multiple charts). Fold into the chat-migration session or a short follow-up. Not
blocking the MCP seal; needed before claiming end-to-end answer quality.

### ISSUE-6 — `deepseek-chat` alias retires 2026-07-24. **TIME-SENSITIVE (26 days).**
**Code-verified nuance (important):** this is NOT a simple find-replace. `registry.ts` actively uses
`deepseek-chat` as the VALID API ID across many call-type routes, with explicit comments that
`deepseek-v4-flash` is *not* a valid API model ID (the API rejects it). So swapping `deepseek-chat` →
`deepseek-v4-flash` would BREAK DeepSeek calls. The correct fix must confirm DeepSeek's actual post-retirement
model ID from current docs and update the routes + the FAMILY_WORKER map + CALL_TYPE_ROUTING accordingly.
→ **Remediation:** a small, well-scoped registry update — verify the correct ID from DeepSeek docs first, then
update. Must land before 2026-07-24. Low effort, but do it deliberately, not by naive replace.

## §3 — Other run notes
- D0.5 closed via REMEDIATION_PHASE0 (drift_detector exit 3, 0 HIGH/0 CRITICAL; 52 schema violations all
  MEDIUM/LOW pre-existing baseline, booked as known_residuals per ONGOING_HYGIENE_POLICIES §B). A
  SESSION_LOG append + frontmatter hygiene pass is scheduled for the next governance session.
- Snapshots/restore points were taken per the charter recovery rails.

## §4 — Recommended next actions (in order)
1. **ISSUE-6 first** (smallest, time-boxed): scoped registry fix, verify the correct DeepSeek ID, land before 2026-07-24.
2. **ISSUE-1 chat migration** (blocking the full seal): run the new chat-migration brief.
3. **ISSUE-4 faithfulness eval** (fold in with or after the chat migration; needs the chat path live for end-to-end).
4. Governance hygiene (SESSION_LOG append + frontmatter pass) at the next governance session.

After ISSUE-1 + ISSUE-4 close, the chat channel joins the MCP channel as sealed → the retrieval system is
fully complete end-to-end.

*End of RETRIEVAL_AUTONOMOUS_RUN_OUTCOME v1.0.*
