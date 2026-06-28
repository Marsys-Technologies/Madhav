---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_MCP_TOOL_HYGIENE
version: 1.0
status: READY-FOR-EXECUTION
created: 2026-06-28
author: Cowork (planning) — for execution by Claude Code in Antigravity
classification: CLAUDECODE_BRIEF — scrub/retire unwired legacy MCP tool files (ISSUE-7)
session_type: implementation — latent native-contamination hygiene (no live exposure)
priority: not urgent (no live serving exposure) — but DO before any future MCP-tool wiring
parent: RETRIEVAL_AUTONOMOUS_RUN_OUTCOME_v1_2 (ISSUE-7)
hard_constraints:
  - reverse-citation gate before ANY retirement (feedback_destructive_brief_reverse_citation_gate)
  - chart-agnostic (#14): no native UUIDs/identifiers anywhere in platform-mcp/src/tools/ after this
acceptance_criteria: see §3
---

# CLAUDE CODE BRIEF — MCP-TOOL HYGIENE (ISSUE-7)

> 19 files in `platform-mcp/src/tools/` still contain native identifiers (`482012f1` / `NATIVE_CHART_ID` /
> "Abhisek"). These are **unwired legacy tool files** — D6/D7 remediated the WIRED tools that form the sealed
> MCP surface; these were left because they're not in the live serving path. **Latent risk:** if any get wired
> later, the contamination re-enters. This brief cleans them and closes the gap permanently.

## §0 — The 19 files (code-verified 2026-06-28)
l0_ephemeris, bo_2-5, bo_2-6, muhurta_finder, phala_event_anchors, get_cgm_subgraph, bodha_bo22, bodha_bo24,
phala_rectification, kala_period_snapshot, mimamsa_lel_intake, mimamsa_outcome, phala_outlook,
phala_mitigation_map, kala_convergence, retrieval/kala_temporal, kala_temporal, retrieval/ganita_forensic_render,
kala_timeline. (Re-grep at session open to confirm the list hasn't changed.)

## §1 — Per-file decision (the swarm/human-proxy decides each)
For each file, classify and act:
- **SUPERSEDED** by the consolidated sealed MCP surface (D6/D7's 12 tools) — **retire** under the
  reverse-citation gate (grep for any live import/registration first; most are unwired so expect zero, but
  verify — never delete on faith). Citation report in the PR.
- **STILL USEFUL** (a capability not covered by the consolidated surface) — **scrub to chart-agnostic**: remove
  native UUID defaults, make chart_id required + error-if-missing, fix `lel_query`-style no-selector cases,
  scrub native identifiers from descriptions to `<chart_uuid>` placeholder, fix any `'default'` cache buckets.
  Then it conforms to the contract and could be safely wired later.
- When unsure, prefer retire-if-superseded over keeping dead contaminated code.

## §2 — Close the gap permanently
Extend the **chart-agnostic CI gate** (the one built in D1, beside `parity_check.ts`) to ALSO scan
`platform-mcp/src/tools/` — so native UUIDs / native-default patterns in any MCP tool file (wired or not) fail
CI. This makes re-contamination impossible going forward, which is the real fix (the 19 files are the symptom;
the missing gate coverage is the cause).

## §3 — Acceptance criteria
- Each of the 19 files retired (citation report) or scrubbed to chart-agnostic; zero native identifiers remain
  in `platform-mcp/src/tools/`.
- The chart-agnostic CI gate covers `platform-mcp/src/tools/`; a test proves it catches a native UUID there.
- No live serving behavior changed (these were unwired); the sealed MCP surface untouched.
- Tests green; reverse-citation reports filed for any retirement.

## §4 — Close
Set `status: COMPLETE` when all 19 are clean and the gate covers the directory. This closes the last
contamination-hygiene item from the retrieval campaign.

*End of CLAUDECODE_BRIEF_RETRIEVAL_MCP_TOOL_HYGIENE v1.0.*
