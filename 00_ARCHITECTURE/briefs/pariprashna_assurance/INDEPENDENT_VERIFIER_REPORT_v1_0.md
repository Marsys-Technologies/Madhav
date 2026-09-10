---
artifact: PARIPRASHNA_ASSURANCE_P0_INDEPENDENT_VERIFIER_REPORT
version: 1.0
status: PASS_LOCAL_CG0_PROOF
date: 2026-08-24
scope: PARIPRASHNA-ASSURANCE-P0-TRACKER
verifier: Independent verifier operating from fresh context and primary source inspection
---

# Independent verifier report — P0 tracker

## Verdict

**PASS for the local CG-0 proof.** This is not native acceptance, a production
deployment approval, or authorization to close CG-0 in a production runtime.

## Primary evidence inspected

- `control.py`, `server.py`, `dashboard.html`, the event schema, operations artifacts, and
  browser smoke script.
- 33/33 `tests/pariprashna_assurance_tracker/test_control.py` tests.
- Desktop plus 390 px rendered browser smoke; live Chrome review found no console errors and
  reported 100 for accessibility, best practices, SEO, and agentic browsing.

## Adversarial findings and disposition

| Finding | Disposition | Final proof |
| --- | --- | --- |
| Dashboard retained a green-looking projection after SSE/API failure | Fixed: failure removes projection/navigation and presents an explicit unavailable state | Live disconnect inspection |
| Evidence URI could be unsafe | Fixed: protocol allowlist plus attribute-safe escaping | Source inspection and browser checks |
| Closure work-item credit could precede the result packet | Fixed: only `result_packet_accepted` credits closure | `test_regression_requires_scenarios_and_completed_session_is_not_stale` |
| Scope-added scenario did not expand/enforce the scenario contract | Fixed: validated `added_scenarios` expand the denominator and are required before regression/packet | Same adversarial test |
| Failed stream could receive a result packet and be projected complete | Fixed: packet rejected with `FAILED_STREAM`; fold preserves terminal failure | `test_failed_stream_cannot_receive_packet_closure_credit` |
| A stream lead could invoke recovery or claim another session's freshness | Fixed: rebuild is integrator-only; a durable, globally unique session must belong to the caller; the server assigns the observation time | `test_rebuild_and_presence_are_privilege_bound` |
| Operator could mistake a static dashboard for the live service or seed fixtures into campaign state | Fixed: `--demo` serves a full loopback dashboard from a new empty runtime only; direct files explain this path | `test_demo_seed_requires_an_empty_runtime`; rendered browser smoke |
| Synthetic fixture state could look like campaign evidence | Fixed: immutable bootstrap provenance derives the runtime mode; the dashboard visibly labels demos without hiding stale/integrity warnings | demo/campaign runtime-mode tests; rendered browser smoke |
| Swarm cost could be silently omitted or misrepresented | Fixed: dashboard displays the persisted value verbatim or says that it is not reported; cost has no progress or health effect | execution-session projection test; rendered browser smoke |
| A leader could display an unverified actor as a native, verifier, integrator, or stream lead | Fixed: known roles must resolve to a registered actor with the exact role and stream eligibility; unregistered participants are explicitly limited to `SPECIALIST` | `test_participant_roster_is_registered_and_stream_eligible` |
| Remediation credit had no frozen post-triage contract | Fixed: the surrogate freezes one plan only after every finding is triaged; unplanned work and incomplete plan verification cannot earn remediation credit | `test_remediation_plan_is_frozen_after_triage` |
| P1–P7 work could not be assigned to a phase-scoped local execution lead | Fixed: each phase has its own scoped local lead identity, while stream-lead boundaries remain isolated | `test_each_phase_has_a_scoped_execution_lead` |
| An active dependent phase could remain green without an evidenced prerequisite resolution | Fixed: resolution must name a defined edge and primary evidence; malformed/repeated submissions are retained rejections, while an unresolved active edge forces non-green campaign and target-phase attention | `test_each_phase_has_a_scoped_execution_lead` |
| Phase-only sessions and event envelopes could hide stale/incorrectly routed state | Fixed: non-P3 phase sessions contribute to phase/campaign health; work-item, gate, packet, dependency, and native events must use their declared target | `test_each_phase_has_a_scoped_execution_lead`; `test_control_events_are_bound_to_their_declared_target` |
| Concurrent credential issuers could overwrite a valid local token set | Fixed: exclusive file reservation admits one issuer and preserves its token set; other callers receive `CREDENTIALS_EXIST` | `test_concurrent_credential_provisioning_has_one_winner` |

## Residual limits

The proof is intentionally loopback-only and uses a disposable local SQLite runtime. Production
hosting, multi-user/network authentication, credential issuance/rotation, backup retention, and
release authority remain reserved A3 decisions.
