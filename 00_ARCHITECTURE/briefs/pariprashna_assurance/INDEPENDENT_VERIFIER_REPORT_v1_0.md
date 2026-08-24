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
- 27/27 `tests/pariprashna_assurance_tracker/test_control.py` tests.
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

## Residual limits

The proof is intentionally loopback-only and uses a disposable local SQLite runtime. Production
hosting, multi-user/network authentication, credential issuance/rotation, backup retention, and
release authority remain reserved A3 decisions.
