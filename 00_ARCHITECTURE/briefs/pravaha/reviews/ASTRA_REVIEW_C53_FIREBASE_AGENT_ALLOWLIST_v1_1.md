---
artifact: ASTRA_REVIEW_C53_FIREBASE_AGENT_ALLOWLIST
version: "1.1"
reviewer: "Codex gpt-6-astra"
date: "2026-10-04"
verdict: ACCEPT
reviewed_commit: ab96a9fa8ddb3fcc2465c24267752ac2a426c24d
authority: "Review only; authorizes nothing."
---

- Firebase exemption is reachable only through `assertVerifierInheritedControl`. The builder’s default matcher path and original ten exemptions are provably identical to `origin/main`; no additional gate weakening found.
- In-memory replay with an adapted test runner: **40/40 pass** at this head; **39/40 pass** against `54b33e11f`, failing precisely the synthetic `iam.serviceAccounts.getAccessToken` cross-gate regression.
- Foreign-project and mixed canonical/rogue-member tests exist and pass on both revisions; they cover restrictions already enforced before this amendment.

**MAY THIS BE MERGED and `DATA_PLANE_VERIFIER_CONTROL_EXCEPTIONS` then removed — YES**, for the Firebase-only declared exception.

Residual risk: the owner accepts that the Firebase agent’s project-IAM rewrite authority can be used to grant control over the verifier.

No files written, Git state changed, or cloud accessed.