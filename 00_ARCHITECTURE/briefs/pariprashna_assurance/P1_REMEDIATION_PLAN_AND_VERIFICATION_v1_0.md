# P1 remediation plan and verification v1.0

Status: **frozen for the P1 identity/control-plane remediation only.** It does
not authorize inherited product fixes.

| P1 finding | Classification | Remediation | Verification |
| --- | --- | --- | --- |
| P1-F-001: P0B-only release lacked P1 identities | VERIFIED_CARRY_FORWARD | Phase-scoped identity tables/tokens; P1-only role/stream guard; attested guarded upgrade and rollback path. | Failing capability test, 54 tracker tests, independent review, PR #1524 protected CI and merge-queue CI, deployed read-only verifier PASS. |
| P1-F-002: newly started P1 cell initially lacked current presence | VERIFIED_CARRY_FORWARD | Record only current `lead-p1` presence after accepted work start. | Loopback projection reports the P1 cell ACTIVE/HEALTHY; no percentage changed. |
| P1-F-003: historical evidence summaries drift | OPEN_BLOCKER_FOR_P2 | No P1 product remediation; freeze latest-record derivation and contradiction register. | P2 must reproduce any product claim against fresh primary evidence. |
| P1-F-004: work-start lacked operational duration ceiling | OPEN_BLOCKER_FOR_P2 | Append-only correction that targets the accepted receipt; projector must expose only a positive corrected ceiling. | New failing regression, protected PR/CI/merge, attested deployment, replay, and independent runtime verification are required. |

The plan is deliberately empty for inherited P-PORTAL, EDIR, and product
defects: they are P2 blockers, not P1 fixes. No historical campaign credential,
event, heartbeat, or timer was reused.
