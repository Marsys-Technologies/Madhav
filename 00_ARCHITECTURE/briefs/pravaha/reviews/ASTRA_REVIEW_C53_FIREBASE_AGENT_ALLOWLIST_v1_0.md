---
artifact: ASTRA_REVIEW_C53_FIREBASE_AGENT_ALLOWLIST
version: "1.0"
reviewer: "Codex gpt-6-astra"
date: "2026-10-04"
verdict: ACCEPT_WITH_AMENDMENTS
reviewed_commit: 54b33e11fab460523234161909118e65cc119eb6
authority: "Review only; authorizes nothing."
---

**One required amendment: preserve the builder gate’s existing acceptance boundary.**

1. **Exactness: correct.** The entry requires exact role/member equality, the supplied numeric project number, and no condition. The caller restricts acceptance to this project’s ID or number representation. No wildcard, prefix, other `gcp-sa-*` identity, or alternative role is exempted. Google explicitly documents this Firebase identity and its project-level `roles/firebase.managementServiceAgent` grant. [Google service agents](https://docs.cloud.google.com/iam/docs/service-agents)

2. **Other gates: one latent change.** `assertSecretIsolation` and the direct service-account policy validator remain unchanged. However, `assertEffectiveIsolation` also calls the modified matcher at **preflight.ts:654**. Firebase currently lacks direct impersonation permissions, so its present grant passes that builder check both before and after C53. But an in-memory reproduction adding `iam.serviceAccounts.getAccessToken` to its resolved permissions produces **base: reject; HEAD: accept**. This is a synthetic permission-expansion case, not a claim about today’s role. The strict “other gates must not change” requirement therefore needs the Firebase exemption confined to `assertVerifierInheritedControl`, preserving the original ten builder exemptions. [Current Firebase permissions](https://docs.cloud.google.com/iam/docs/roles-permissions/firebase)

3. **Tests:** all **36 unit tests passed** under an isolated, cache-disabled Vitest configuration. Added tests cover exact acceptance, another member—including another project number—another control role, conditions, folders, and organizations. Missing committed cases include the exact member on a foreign **project resource**, mixed canonical/rogue members, and the cross-gate permission-expansion regression above.

4. **Trust and residual risk:** “same class” is fair for Google management, **not equivalent authority**. Eight existing agents have access-token minting; GKE and Instance Group Manager have `actAs`. None of those ten roles has `resourcemanager.projects.setIamPolicy`; Firebase does. Its project-IAM rewrite authority is materially broader: misuse could grant secret access or verifier impersonation to itself or others. Existing agents already present impersonation risk; this addition accepts another powerful trusted principal. [IAM permission comparison](https://docs.cloud.google.com/iam/docs/roles-permissions/iam), [project-IAM permission comparison](https://docs.cloud.google.com/iam/docs/roles-permissions/resourcemanager)

**MAY THIS BE MERGED and the declared-exception variable then removed — NO.** First confine Firebase’s exemption to verifier inherited-control validation and add the cross-gate regression proving builder rejection remains unchanged.