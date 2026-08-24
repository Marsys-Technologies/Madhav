---
artifact: PARIPRASHNA_ASSURANCE_CG0_ACCEPTANCE_EVIDENCE
version: 1.0
status: LOCAL_PROOF
date: 2026-08-24
scope: PARIPRASHNA-ASSURANCE-P0-TRACKER
---

# CG-0 acceptance evidence map

This map is intentionally implementation-specific. It does not certify a production
deployment, native acceptance, historical campaign progress, or any subsequent gate.

| # | Required proof | Local evidence |
| --- | --- | --- |
| 1 | Deterministic full replay | `test_replay_hash_is_identical`; `cli.py verify` |
| 2 | Idempotent duplicate | `test_duplicate_idempotency_returns_original` |
| 3 | Invalid/out-of-order rejection | `test_invalid_and_out_of_order_are_rejected_and_retained` |
| 4 | No loss with concurrent writers | `test_concurrent_stream_writers_retry_without_loss` |
| 5 | Cross-stream authorization | `test_stream_writer_cannot_write_another_stream` |
| 6 | No finder/fixer self-verification | `test_finder_or_fixer_cannot_self_verify` |
| 7 | Surrogate cannot native-close | `test_surrogate_cannot_close_native_gate` |
| 8 | Expired running presence is stale | `test_running_presence_stales_but_paused_does_not` |
| 9 | Paused is not falsely stale | `test_running_presence_stales_but_paused_does_not` |
| 10 | Bad integrity never presents green | `test_integrity_degraded_never_appears_green` |
| 11 | Projector restart recovery | `test_projector_recovery_and_corruption_detection` |
| 12 | Corruption detected by replay and visibly degraded | `test_projector_recovery_and_corruption_detection`; `test_periodic_replay_monitor_publishes_integrity_degradation` |
| 13 | Evidence-weighted credit | `test_evidence_progress_and_no_heartbeat_credit` |
| 14 | No credit for heartbeat/message/commit-like claim | `test_evidence_progress_and_no_heartbeat_credit` |
| 15 | Controlled scope denominator with visible reduction explanation | `test_scope_change_is_only_denominator_expansion_and_explains_drop` |
| 16 | Evidence/verifier-linked gates | `test_gate_closure_requires_evidence_and_integrator` |
| 17 | Retained, visible rejections | `test_invalid_and_out_of_order_are_rejected_and_retained`; `/api/rejected` |
| 18 | Real-time update | `test_sse_update_and_dashboard_accessibility_contract` performs authenticated POST to SSE receipt and checks sub-second local delivery |
| 19 | Desktop/mobile display | `tests/pariprashna_assurance_tracker/browser_smoke.sh` uses Chrome headless plus 390 px screenshot |
| 20 | Keyboard/focus/accessible names | semantic landmarks, focus CSS, aria labels, and source assertions in `test_sse_update_and_dashboard_accessibility_contract`; live Chrome accessibility review is required again for any dashboard change |
| 21 | All lifecycle and health surfaces | `demo.py`; `test_every_lifecycle_and_health_has_a_fixture_surface` |
| 22 | Immutable reconciled snapshot | `test_snapshot_export_reconciles` |
| 23 | External adapter fails safely | `test_external_adapter_failure_is_visible_not_canonical` |
| 24 | Honest P0 bootstrap | `setUp` bootstrap plus `test_gate_closure_requires_evidence_and_integrator` proves bootstrap alone cannot close CG-0 |
| 25 | Privileged recovery and owner-bound, server-timestamped presence | `test_rebuild_and_presence_are_privilege_bound` |
| 26 | One-command demo startup cannot contaminate a populated runtime or look like campaign evidence | `test_demo_seed_requires_an_empty_runtime`; `browser_smoke.sh` serves the fixture through `server.py --demo` and asserts the visible synthetic-warning label |
| 27 | Remediation denominator freezes only after triage and cannot earn credit outside its contract | `test_remediation_plan_is_frozen_after_triage` |

The same privilege test also proves that a session identifier cannot be reused across streams,
so a presence record has an unambiguous durable owner.

The stream-charter denominator is additionally proven by
`test_scenario_denominator_is_frozen`; `test_execution_session_projection_exposes_governance_fields`
proves the projection preserves the complete execution-session operational surface, including
recorded cost and a validated surrogate/specialist roster where supplied; the swarm view
otherwise says `Cost not reported` and `No participant roster reported`.
`test_failed_stream_cannot_receive_packet_closure_credit` proves terminal stream failure
cannot be overwritten by a result packet.
`test_remediation_plan_is_frozen_after_triage` proves that a remediation plan cannot be frozen
before every finding is triaged, cannot be altered after freezing, and cannot accept an
unplanned implementation or remediation-stage credit without a plan.

The seeded campaign definition in `control.py` includes P0–P7 with weights
5/8/17/45/10/7/5/3 and six equal P3 streams. It starts without historical credit. The
`demo.py` fixture is explicitly synthetic and must never be imported as campaign evidence.

## Local verification commands

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v tests/pariprashna_assurance_tracker/test_control.py
PYTHONDONTWRITEBYTECODE=1 tests/pariprashna_assurance_tracker/browser_smoke.sh
```
