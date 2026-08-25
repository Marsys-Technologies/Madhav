# P1 remediation plan and verification v1.0

Status: **frozen for the P1 identity/control-plane remediation only.** It does
not authorize inherited product fixes.

| P1 finding | Classification | Remediation | Verification |
| --- | --- | --- | --- |
| P1-F-001: P0B-only release lacked P1 identities | VERIFIED_CARRY_FORWARD | Phase-scoped identity tables/tokens; P1-only role/stream guard; attested guarded upgrade and rollback path. | Failing capability test, 54 tracker tests, independent review, PR #1524 protected CI and merge-queue CI, deployed read-only verifier PASS. |
| P1-F-002: newly started P1 cell initially lacked current presence | VERIFIED_CARRY_FORWARD | Record only current `lead-p1` presence after accepted work start. | At remediation time the loopback projection reported the P1 cell ACTIVE/HEALTHY; no percentage changed. The closed cell is now COMPLETED/STALE. |
| P1-F-003: historical evidence summaries drift | OPEN_BLOCKER_FOR_P2 | No P1 product remediation; freeze latest-record derivation and contradiction register. | P2 must reproduce any product claim against fresh primary evidence. |
| P1-F-004: work-start lacked operational duration ceiling | VERIFIED_CARRY_FORWARD | The single append-only correction targets the accepted receipt and projects a positive `259200`-second ceiling. | Failing regression, protected PR #1549/CI/merge, attested `ca4fd54…-retry1` deployment, replay/recovery, verifier acceptance, and integrator closure are recorded in `P1_CLOSURE_PACKET_v1_0.md`. |

The plan is deliberately empty for inherited P-PORTAL, EDIR, and product
defects: they are P2 blockers, not P1 fixes. No historical campaign credential,
event, heartbeat, or timer was reused.

The F-004 result closes only P1's control-plane receipt defect. It does not
discharge an inherited obligation, close an EDIR finding, or change P2 intake.
