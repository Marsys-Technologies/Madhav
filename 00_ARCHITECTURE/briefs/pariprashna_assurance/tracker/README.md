# Paripraśna Assurance Control Plane (CG-0)

This is the new event-sourced control plane for the v3.0 assurance programme. It does not
reuse the retired tracker-v2 runtime or any historical assurance heartbeat. SQLite is the
append-only source of campaign state; the dashboard is always a derived projection.

## Components

- `control.py`: versioned schema, transactional event ingestion, role/stream authorization,
  deterministic projector, replay/hash reconciliation, presence overlay, and snapshots.
- `server.py`: loopback JSON/SSE service and responsive dashboard delivery.
- `cli.py`: bootstrap, event emission, projection, replay and immutable snapshots.
- `demo.py`: disposable seeded demonstration covering every lifecycle state.
- `EVENT_SCHEMA_v1_0.json`: API request contract.

## Local operation

### One-command disposable demonstration

From this directory, run:

```sh
python3 server.py --demo --runtime "$(mktemp -d /private/tmp/pariprashna-assurance-demo-XXXXXX)"
```

It refuses a non-empty runtime directory, so fixture data cannot be mixed with campaign state.
The served dashboard is labelled `SYNTHETIC DEMO` and warns that fixture data is not campaign
evidence. Open `http://127.0.0.1:8787`; never open `dashboard.html` directly.

### Controlled local runtime

```sh
TRACKER_RUNTIME=/private/tmp/pariprashna-assurance-demo
python3 00_ARCHITECTURE/briefs/pariprashna_assurance/tracker/demo.py --runtime "$TRACKER_RUNTIME"
python3 00_ARCHITECTURE/briefs/pariprashna_assurance/tracker/server.py --runtime "$TRACKER_RUNTIME"
```

Open `http://127.0.0.1:8787`. The demo is intentionally non-authoritative. Generated runtime
state belongs outside this repository and must not be manually edited.

For a non-demo local runtime, first run `cli.py --runtime "$TRACKER_RUNTIME"
provision-credentials`. It creates a random, mode-0600 credential file for that runtime.
`init` and `emit` require the matching actor token; there are no default bearer tokens.
The local-proof runtime includes separately scoped `lead-p0` through `lead-p7` identities and
one lead for each P3 stream; a production runtime must enroll corresponding approved identities
through its A3-governed issuer.

## Acceptance evidence

`tests/pariprashna_assurance_tracker/test_control.py` exercises replay, idempotency,
sequence conflict/retry, role and stream authorization, self-verification rejection,
surrogate/native separation, stale and paused behavior, stale-green prevention, projector
recovery/corruption detection, weighted evidence-only progress, scope-change reduction,
ledger-linked work-item verification, phase/gate prerequisites, append-only corrections,
snapshot reconciliation, external adapter degradation, lifecycle fixtures, end-to-end SSE
delivery and latency, and dashboard accessibility source contracts.

For a P3 stream, its first `work_started` event must include a positive
`planned_scenarios` integer. Scenario execution is separately recorded by unique
`scenario_id`; it earns no progress itself, but all chartered and scope-approved scenarios
must be present before regression credit can be accepted. Closure credit is earned only by
an accepted result packet, never a direct work-item event. The dashboard exposes the frozen
denominator, execution-session ownership/configuration, evidence timestamps, scope-change
reduction explanations, and retained rejection records.

After all discovered findings in a stream are triaged, the surrogate emits one
`remediation_approved` event containing its `remediation_plan` (an explicit empty list is
valid when no remediation is required). Each entry maps one triaged finding to one remediation.
Only those entries may be implemented, each must be independently verified, and the remediation
work item cannot earn credit until the complete frozen plan is verified.

An integrator records a defined phase prerequisite through evidence-bearing
`dependency_resolved` with `from` and `to`. The dependency panel preserves its resolved status
and evidence. An active downstream phase with a pending predecessor is an explicit campaign
attention condition, not a green dashboard state.

Run it with:

```sh
python3 -m unittest -v tests/pariprashna_assurance_tracker/test_control.py
tests/pariprashna_assurance_tracker/browser_smoke.sh
```

The browser/SSE integration test binds a loopback socket. In a sandboxed environment it may
require local socket permission; it never opens a non-loopback listener. The Chrome smoke
test requires a local Chrome binary (`CHROME_BIN` may override its macOS default), makes no
network request, and checks desktop landmarks plus a 390 px mobile render. Dynamic data
delivery and latency are separately asserted by the HTTP-to-SSE integration test.

The service rejects non-loopback binds and non-local peers. Authentication and authorization
for a networked or multi-user deployment are intentionally an A3 prerequisite; do not expose
this CG-0 local proof service beyond its host.
