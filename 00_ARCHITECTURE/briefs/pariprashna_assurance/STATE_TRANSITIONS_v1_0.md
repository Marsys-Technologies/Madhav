---
artifact: PARIPRASHNA_ASSURANCE_STATE_TRANSITIONS
version: 1.0
status: CURRENT
date: 2026-08-24
---

# State-transition specification

Durable events use schema `pariprashna-assurance-event@1`. Every stream event carries an
idempotency key and the caller’s expected stream sequence. The server assigns the next
monotonic sequence only inside its append transaction.

`NOT_STARTED → READY → RUNNING → IN_VERIFICATION → COMPLETE` is the normal path.
`RUNNING` may move to `BLOCKED` or `PAUSED`; `PAUSED` may resume to `RUNNING`.
`FAILED` is terminal until an explicit corrective work item is accepted. No event accepts a
percentage. Completion credit is issued only by `work_item_accepted`, with evidence, after
independent verification. A stream-close recommendation is not closure; an integrator must
accept the result packet. CG-6 accepts only a native-acceptance event, never a surrogate
decision.

Corrections never mutate a prior event. `correction_recorded` and
`scope_change_approved` reference the prior event/work item and explain the correction.
Only an approved scope-change may add denominator work items; the projector displays the
resulting reduction and its evidence reference.

Every `work_started` event carries a globally unique non-empty `session_id`. Its optional
`participants` roster has unique actor identifiers and a declared role/state. A known role
(`STREAM_LEAD`, native, surrogate, verifier, or integrator) must resolve to the registered
actor with that exact role and eligibility for the event stream. An unregistered participant is
allowed only when explicitly declared as a `SPECIALIST`; it cannot assert a known role.

`dependency_resolved` is an evidence-bearing integrator event for one defined phase edge. Each
edge is resolved once, is replayed into the canonical dependency projection, and is shown with
its evidence. If a downstream phase is active while its predecessor edge remains unresolved,
the tracker elevates the target phase and overall campaign to `ATTENTION_REQUIRED` and shows a
non-green warning; it cannot be a silent ordering exception.

Every control event is written to the target it governs: a work-item acceptance and its verifier
event share the work item's declared stream or phase; a gate and its verifier event share the
corresponding phase; a result packet shares its stream; a dependency resolution shares its
downstream phase; and native acceptance is written to P6. A mismatched target is rejected before
it can earn credit or close a gate.

After all discovered findings for a P3 stream have a surrogate triage, the surrogate may
freeze exactly one `remediation_plan`. The plan names each triaged finding once, including an
explicit empty plan when there is no remediation work. Implementations outside that plan are
rejected, every planned remediation needs independent verification, and remediation-stage
credit is rejected until that durable contract is complete. The plan is never expanded by a
later ordinary event; a material expansion requires its own governed scope path.

For every P3 stream, its initial `work_started` event freezes a positive
`planned_scenarios` denominator. A scope-change may add explicitly named scenarios only
through `added_scenarios`; those increase the approved denominator and must each be
executed. Each `scenario_executed` event names one unique scenario and is rejected if it
duplicates a prior scenario or exceeds that denominator. Regression credit is rejected
until every chartered and scope-approved scenario is executed. The closure work item is
never directly accepted: only `result_packet_accepted` earns it, after every other stream
work item, every approved scenario, and an independent closure recommendation are present.
`result_packet_accepted` is rejected for a `FAILED` stream; terminal failure remains visible
until a separately governed recovery path is authorized.

Each `work_item_accepted` must name a durable `verification_accepted` or
`regression_accepted` event from an independent verifier. That verifier event must name the
same work item plus distinct finder/fixer identities. A gate closure must name a separate,
durable verifier event for that exact gate; it is also rejected until every work item in the
corresponding phase is accepted, the predecessor gate is closed, and (for CG-3) all six
stream result packets are accepted. These predicates are evaluated in the append
transaction, not trusted from a dashboard field.

A result packet is valid only after every non-closure work item in its stream is accepted and an
independent verifier has recommended stream closure. Native acceptance is valid only after
complete P6 evidence and CG-5. Scope additions must be new, positive work items no greater
than the full campaign denominator; a failed stream cannot receive further completion credit.
