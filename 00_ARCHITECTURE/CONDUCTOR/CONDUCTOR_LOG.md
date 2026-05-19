# CONDUCTOR Run Log

Append-only record of every Conductor-driven session execution. Read top-down
for the full run history; most recent run is at the bottom.

**Do NOT edit existing entries.** Corrections go in a `## CORRECTION` sub-entry
appended immediately below the entry being corrected.

## Schema

Each entry contains:

| Field | Description |
|---|---|
| `session_id` | Queue entry session_id that was executed |
| `result` | `PASS`, `HALT`, or `SKIPPED` |
| `timestamp` | ISO 8601 timestamp when the Conductor decided |
| `commits` | Comma-separated git SHAs from the sub-agent (or `"(none)"` if skipped) |
| `gate_exit_code` | Exit code from `gate_command` (or `n/a` if gate was empty/skipped) |
| `context_sessions_used` | Sub-agents spawned so far this orchestrator chat |
| `gate_output` | stdout from gate command, truncated to 500 chars |
| `sub_agent_summary` | `notes_for_orchestrator` from the sub-agent's FINAL_SUMMARY |
| `scope_items_completed` | AC IDs the sub-agent reported complete |

---

<!-- Conductor appends entries below this line. Do not edit above. -->
