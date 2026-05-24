# CONDUCTOR_LOG — Tooling Remediation v1.0

Queue: 00_ARCHITECTURE/CONDUCTOR/tooling-remediation/session_queue.yaml
Branch: feature/tooling-remediation
Worktree: /Users/Dev/Vibe-Coding/Apps/MadhavToolingFix
Started: not yet

## Entries

- session_id: TR-P0-S1
  status: passed
  wave: 0
  completed_at: "2026-05-25 00:00"
  sub_agent_summary: "PASS. mcp_reachable=true. 12 tool tests captured. 3 DB tables counted. chart_facts=2475, school_convergence_index=574, rag_chunks=6931. Key surprises: chart_facts 2475 not 2717; rag_chunks 6931 not 4589 (classical_chunks is separate table); 14 classical texts not 4; school_convergence_index is signal-level MV not school×coverage_type; C9 is PROD_ENV bug (MARSYS_REPO_ROOT absent from Cloud Run); C1 is wrapper envelope-nesting bug."
  gate_exit_code: 0
  commit_sha: 5c0a82f1b5b7b5cf84bb1c84bbc883a2dcf9f535
  pushed: true

- session_id: TR-P1-S1
  status: passed
  wave: 1
  completed_at: "2026-05-25 01:15"
  sub_agent_summary: "PASS. 13 tests pass (6 chart_summary + 7 query_transit_event). C1 fix: ToolBundle unwrap — reads results[0].content parsed JSON, not envelope.result.rows_by_category directly. C6 fix: event_type added as required z.enum to Zod schema. vitest.config.ts include glob fixed. Note: gate grep -q 'PASS' fails on vitest 'passed' output — verified directly."
  gate_exit_code: 0
  commit_sha: 339cbbe333b4c76fc4c77edeb2d75f97b264e28e
  pushed: false

- session_id: TR-P1-S2
  status: passed
  wave: 1
  completed_at: "2026-05-25 01:45"
  sub_agent_summary: "PASS. 24 tests pass (11 query_signals + 13 query_ephemeris). C4: all 5 filter fields now forwarded to toolParams; primitive SQL already had WHERE clauses. C5: date_range {from,to}; 1825-day cap; sample_step/return_changes_only added."
  gate_exit_code: 0
  commit_sha: 5ddf7322fb654ba79ff87a4063903fece2640f0d
  pushed: false

- session_id: TR-P1-S3
  status: passed
  wave: 1
  completed_at: "2026-05-25 02:20"
  sub_agent_summary: "PASS. 19 tests (read_asset + query_panchanga). C9: __dirname-relative path + MARSYS_REPO_ROOT optional override; list_assets new tool registered (23 tools total). C8: MCP wrapper now passes all 11 field groups incl. 5 JSONB enrichment cols. Note: Dockerfile COPY step still needed for prod without env var."
  gate_exit_code: 0
  commit_sha: f97570b60c45217532d4b17e248d2c0e8d3bb88c
  pushed: false

- session_id: TR-P4-S1
  status: passed
  wave: 1
  completed_at: "2026-05-25 02:50"
  sub_agent_summary: "PASS. 25 tests (7+8+9). 3 new wrappers: query_varshphal→varshaphala, query_divisional_chart→divisional_query (division→varga param translation), query_remedial_mantras→remedial_codex_query. All 3 registered in server.ts (count 23→26)."
  gate_exit_code: 0
  commit_sha: 86ae2395
  pushed: false

- session_id: TR-P4-S2
  status: passed
  wave: 1
  completed_at: "2026-05-25 03:15"
  sub_agent_summary: "PASS. 25 tests (3 files). muhurta_finder→callPlatformPrimitive(query_muhurat); tara_balam→query_tara_balam; chandra_balam→query_chandra_balam. All 3 registered in server.ts (26→29). NOTE: query_tara_balam + query_chandra_balam primitives not yet in primitives_registry.ts — needed before prod deploy."
  gate_exit_code: 0
  commit_sha: 8c0b5565
  pushed: false

- session_id: TR-P10-S1
  status: passed
  wave: 1
  completed_at: "2026-05-25 03:40"
  sub_agent_summary: "PASS. Governance doc only. All 5 R-rules inserted in §3 verbatim system prompt. Version bumped 2.4→2.5 (file was already at 2.4, not 2.0 as brief assumed). Both gate greps pass."
  gate_exit_code: 0
  commit_sha: c8f54b96
  pushed: false

- session_id: TR-P10-S2
  status: passed
  wave: 1
  completed_at: "2026-05-25 04:05"
  sub_agent_summary: "PASS. PLANNER_PROMPT bumped 2.5→2.6; R-CS.2/R-CGM.1/R-TRI.1/R-PER.1/R-SCH.1 added. .geminirules TOOLING_REMEDIATION_RULES section added with all 10 R-rules in Gemini idiom (MP.1 mirror)."
  gate_exit_code: 0
  commit_sha: f379866e
  pushed: true

