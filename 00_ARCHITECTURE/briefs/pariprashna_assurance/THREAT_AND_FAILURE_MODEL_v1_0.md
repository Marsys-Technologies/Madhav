---
artifact: PARIPRASHNA_ASSURANCE_TRACKER_THREAT_AND_FAILURE_MODEL
version: 1.0
status: CURRENT
date: 2026-08-24
---

# Threat and failure model

| Failure or threat | Control | Demonstrated proof |
| --- | --- | --- |
| Duplicate delivery | Unique idempotency key returns the original accepted event | idempotency test |
| Lost concurrent update | `BEGIN IMMEDIATE` plus expected stream sequence | concurrent retry test |
| Cross-stream actor | Actor role and permitted-stream check before append | authorization rejection test |
| Forged swarm identity or role | Known-role roster entries resolve to a registered actor with exact role and stream eligibility; unregistered entries are `SPECIALIST` only | `test_participant_roster_is_registered_and_stream_eligible` |
| Self-verification | Finder/fixer identity is compared with verifier before closure credit | self-verification rejection test |
| History rewrite | SQLite triggers reject event update/delete; corrections are new events | append-only/correction test |
| Invalid lifecycle or authority | Versioned schema and transition/role validation retain rejected requests | invalid-transition test |
| Stale-green dashboard | Presence is separate; a RUNNING session ages to STALE; PAUSED does not | stale/paused tests |
| Projector crash or corruption | Full replay reconstructs stored hash; rebuild replaces projection | recovery/corruption tests |
| Unauthorized rebuild or presence impersonation | Only a programme integrator can invoke the rebuild API; a presence update must match an existing session owner and receives its timestamp server-side | `test_rebuild_and_presence_are_privilege_bound` |
| Demonstration data contaminates or impersonates campaign runtime | `--demo` only seeds a new empty runtime and refuses every existing/non-directory target; the projected runtime mode drives a persistent synthetic-data warning | `test_demo_seed_requires_an_empty_runtime`; browser smoke |
| External adapter outage | Adapter health becomes UNKNOWN without altering canonical event state | adapter-degradation test |
| Dashboard client disconnected | SSE reconnects and browser computes a visible stale/unknown banner | SSE and dashboard tests |

Residual risk: local SQLite is a single-host control plane. It is appropriate for the
locally proven CG-0 build, but high-availability deployment, key rotation, backup
retention, and production authorization remain A3 matters.
