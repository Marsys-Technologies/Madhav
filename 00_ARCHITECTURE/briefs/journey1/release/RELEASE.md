---
artifact: JOURNEY1_RELEASE
version: 1.0
status: PREPARING
---

# Journey 1 release

Direct owner authorization: “Go ahead and deploy it.” Scope is the reviewed Journey1 payload and required release corrections, existing protected PR/merge queue/CI, zero-traffic web candidate, guarded promotion and live verification. Journey2 stays deferred. No new migration, chart rebuild, paid provider execution, credential/account approval/reset or foreign-worktree change.

Release authority narrowly supersedes GIP §P.4 for this delivery only; CCD-021 records it. Existing quality and exact-revision/traffic controls remain.

Baseline: main `944ccf22c250b6ebd0507c18d0f23438efceade4`; 100% live `amjis-web-probe-944ccf22c250-37310776256-1`. This is the rollback reference, not a deployment claim for the new UI.

Steps: typed test lint fixes, current-main reconciliation, full lint/types/unit, production build via protected PR, merge queue, established no-traffic smoke/promotion, authenticated read-only UI verification and traffic/revision proof. Real account creation/reset remains a separate manual acceptance task; no production records will be created to demonstrate it.
