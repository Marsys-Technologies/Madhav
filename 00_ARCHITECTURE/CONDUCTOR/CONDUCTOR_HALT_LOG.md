# CONDUCTOR Halt Log

Append-only record of every halt the orchestrator emitted. Read top-down for
the full halt history; most recent halt is at the bottom.

**Do NOT edit existing entries.** Update `resolution_status` in a `## RESOLUTION`
sub-entry appended immediately below the entry being resolved.

## Schema

Each entry contains:

| Field | Description |
|---|---|
| `session_id` | Queue entry session_id that triggered the halt |
| `failure_class` | `gate_failed`, `sub_agent_halt`, `human_approval_required`, or `requires_brief_authoring` |
| `timestamp` | ISO 8601 timestamp of the halt |
| `last_passed` | session_id of the last entry that reached `status: passed`, or `"none"` |
| `queue_position` | Position of the halted entry in the queue (e.g. `3 of 11`) |
| `resolution_status` | `open`, `resumed`, `skipped`, or `abandoned` |
| `failure_context` | Gate stderr (≤1000 chars) or sub-agent `human_decision_needed` text |
| `gate_output` | Gate stdout (≤500 chars), or `"(gate not run)"` |
| `resolution_paths` | RESUME / SKIP / ABANDON options |

---

<!-- Conductor appends entries below this line. Do not edit above. -->
