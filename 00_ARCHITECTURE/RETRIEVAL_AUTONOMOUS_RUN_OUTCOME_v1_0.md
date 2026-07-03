---
artifact: RETRIEVAL_AUTONOMOUS_RUN_OUTCOME
canonical_id: RETRIEVAL_AUTONOMOUS_RUN_OUTCOME
version: 1.1
status: CURRENT — retrieval SEALED (both channels); 2 non-retrieval items routed
created: 2026-06-28
author: Cowork (planning) — recording the autonomous swarm run result, for native Abhisek Mohanty
classification: run outcome + remediation triage
parent: CLAUDECODE_BRIEF_RETRIEVAL_AUTONOMOUS_SWARM_CHARTER_v1_0 (the run this records)
changelog:
  - v1.0 (2026-06-28): Records the overnight autonomous run. Verdict SUBSTANTIALLY COMPLETE — MCP channel sealed, chat channel pending. Triages 3 open items (chat migration BLOCKING, faithfulness eval MODERATE, deepseek retirement TIME-SENSITIVE).
  - v1.1 (2026-06-28): **ISSUE-1 CLOSED — chat migration complete** (commit fab501b1, CURRENT_STATE v6.04, DG1 complete; 20/20 drift parity, 5082 tests pass, legacy retired with citation report). **Retrieval system SEALED on BOTH channels.** ISSUE-4 reframed: it is an L2 Bodha MSR rebuild (the retrieval layer correctly surfaced pre-existing computed-value drift — 6.88% fact resolution = the documented MSR-vs-L1-epoch problem, NOT a retrieval defect). ISSUE-6 target VERIFIED from DeepSeek live docs (deepseek-v4-flash IS the valid ID; code comments were stale).
  - v1.2 (2026-06-28): **ISSUE-6 CLOSED — DeepSeek migration complete** (commit afae7e1b, PR #359; FAMILY_WORKER + 11 CALL_TYPE_ROUTING slots → deepseek-v4-flash; stale comments corrected; live API call confirmed; regression tests enforce deepseek-chat NOT as primary; 5085 tests pass). **ISSUE-7 captured** (new): 19 UNWIRED legacy MCP tool files in platform-mcp/src/tools still carry native UUIDs — latent (not in the live sealed serving path; D6/D7 remediated the wired files), but must be scrubbed/retired before any future wiring. Scoped brief authored. Retrieval campaign CLOSED; ISSUE-4 (L2 Bodha) + ISSUE-7 (MCP-tool hygiene) are correctly-routed follow-ons.
  - v1.3 (2026-06-28): **ISSUE-7 CLOSED — MCP-tool hygiene complete** (commit d9a22a5d, PR #360; CURRENT_STATE v6.05). 10 superseded files retired (+ test) under reverse-citation gate; 9 still-useful files scrubbed to chart-agnostic; **chart_agnostic_gate.ts extended to scan platform-mcp/src/tools/ — re-contamination now structurally impossible (CI catches it)**. platform-mcp/src/tools/ verified clean (zero native-id hits). **The retrieval campaign is now FULLY CLOSED except ISSUE-4 (L2 Bodha MSR rebuild — not retrieval debt).**
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

## §2 — Item status

### ISSUE-1 — Chat channel migration. ✅ **CLOSED (commit fab501b1).**
Chat now consumes the registry; 20/20 drift parity (MCP == chat); `lib/retrieve` + `primitives_registry`
retired with citation report; 5082 tests pass; zero runtime legacy imports. **Retrieval SEALED both channels;
CURRENT_STATE v6.04; DG1 complete.** The two-systems split is gone.

### ISSUE-4 — 6.88% fact resolution. **NOT A RETRIEVAL ITEM — routes to L2 Bodha.**
The structural grounding check found `constituent_facts_array` resolves to real L1 facts at only 6.88%. **This
is the retrieval layer working correctly** — it surfaced the pre-existing MSR computed-value drift documented in
`MSR_COMPUTED_VALUE_DRIFT_HANDOFF_v1_0.md`. Root cause: L2 Bodha's MSR signals were built against a PRIOR L1
epoch; the §N.5 detector is faithfully reporting that the cited fact_ids no longer resolve. **The fix is an L2
Bodha MSR rebuild against the current L1, not a retrieval change.** → Route to the L2 Bodha workstream as an
MSR rebuild; the retrieval layer needs no change (and its detector is the proof the rebuild worked, after).
The faithfulness/groundedness eval (judge-model run) is best run AFTER the MSR rebuild, since scoring against
drifted data would measure the data problem, not retrieval quality.

### ISSUE-6 — DeepSeek alias retirement. ✅ **CLOSED (commit afae7e1b, PR #359).**
FAMILY_WORKER.deepseek + all 11 CALL_TYPE_ROUTING slots → `deepseek-v4-flash`; stale "not a valid ID" comments
corrected; live `api.deepseek.com` call with `deepseek-v4-flash` + tool_choice confirmed working; regression
tests now enforce `deepseek-chat` must NOT appear as a primary (anti-regression); 5085 tests pass. Done with
26 days of margin before the 2026-07-24 retirement.

### ISSUE-7 — Unwired legacy MCP tool files carry native UUIDs. ✅ **CLOSED (commit d9a22a5d, PR #360, v6.05).**
The 19 contaminated unwired files are resolved: **10 retired** (superseded by the consolidated surface; under
the reverse-citation gate, with the test) + **9 scrubbed** to chart-agnostic. The durable fix:
**`chart_agnostic_gate.ts` now scans `platform-mcp/src/tools/`** — a native UUID in any MCP tool file (wired or
not) fails CI, so re-contamination is structurally impossible. Directory verified clean (zero native-id hits).
The symptom (19 files) AND the cause (missing gate coverage) are both closed.

## §3 — Other run notes
- D0.5 closed via REMEDIATION_PHASE0 (drift_detector exit 3, 0 HIGH/0 CRITICAL; 52 schema violations all
  MEDIUM/LOW pre-existing baseline, booked as known_residuals per ONGOING_HYGIENE_POLICIES §B). A
  SESSION_LOG append + frontmatter hygiene pass is scheduled for the next governance session.
- Snapshots/restore points were taken per the charter recovery rails.

## §4 — Final state + remaining follow-ons

**The retrieval campaign is COMPLETE.** Both channels sealed (v6.04, DG1 done); ISSUE-1 + ISSUE-6 closed.
Everything that remains is downstream/adjacent, none of it retrieval debt, none of it blocking the seal:

1. **ISSUE-4 → L2 Bodha MSR rebuild** (separate workstream): rebuild MSR signals against the current L1 epoch
   so `constituent_facts_array` resolves above 6.88%; then run the faithfulness eval on clean data. The
   retrieval §N.5 detector is the proof-of-fix instrument once the rebuild runs. **No urgency from retrieval's
   side; owned by the L2 Bodha campaign. This is the ONLY remaining open item.**
2. ~~ISSUE-7 → MCP-tool hygiene~~ ✅ CLOSED (commit d9a22a5d, v6.05) — 10 retired + 9 scrubbed + CI gate
   extended to platform-mcp/src/tools/.
3. Governance hygiene (SESSION_LOG append + frontmatter pass) at the next governance session (booked as
   known_residuals in the D0.5 close record).

Nothing above gates the retrieval system, which is done and serving both channels. The retrieval campaign is
COMPLETE; only the (non-retrieval) L2 Bodha MSR rebuild remains, owned by its own workstream.

*End of RETRIEVAL_AUTONOMOUS_RUN_OUTCOME v1.0.*
