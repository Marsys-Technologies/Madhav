---
artifact: ASTRA_REVIEW_ENV_BRANCH_POLICY_FIX
version: "1.0"
reviewer: "Codex gpt-6-astra"
date: 2026-10-04
verdict: ACCEPT_WITH_AMENDMENTS
reviewed_commit: 49acfb65b329e57bd0e77b030634703b9cb871ce
authority: "Review only; authorizes nothing."
---

The final `main` branch restriction is correct. Amend the transition, rollback, and trust claims before use. This review used the checkout and supplied evidence; no production access or changes occurred.

1. **Explanation: supported, with a documentation qualification.**

GitHub states: “If no branch protection rules are defined for any branch in the repository, then all branches can deploy.” [Deployment restrictions](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments#deployment-branches-and-tags).

The documentation does **not explicitly state that rulesets are excluded** from this calculation. Therefore replace “GitHub documents that only classic rules count” with: “The documented fallback and this repository’s observed behavior are consistent with classic rules being counted and its ruleset not being counted.” The supplied off-branch run independently proves the restriction failed here.

2. **API and matching: correct final configuration; transition not fully established.**

The proposed full PUT preserves the reviewer settings and correctly switches the mutually exclusive policy flags. POST must follow PUT: the branch-policy endpoint requires `custom_branch_policies:true`. Explicit `{"name":"main","type":"branch"}` selects the literal branch name; there is no wildcard, and a tag named `main` is excluded. [Environment API](https://docs.github.com/en/rest/deployments/environments#create-or-update-an-environment), [Branch-policy API](https://docs.github.com/en/rest/deployments/branch-policies#create-a-deployment-branch-policy).

Two qualifications:

- The public environment REST parameter list omits `can_admins_bypass`. The supplied readback supports its use here; require a fresh readback of `false`, rather than treating PUT success as sufficient.
- An empty custom-policy list **should deny everything under the documented matching semantics**, but GitHub does not explicitly document the empty-list transition or atomicity. Do not certify `(a)→(b)` as proven fail-closed. Drain existing environment jobs, keep secrets absent, inspect the intermediate policy list, and complete both calls before resuming consumers.

The final GET assertion is `total_count == 1` and the `{name,type}` projection of `branch_policies` equals `[{"name":"main","type":"branch"}]`; also verify every reviewer/bypass/self-review setting and zero secrets.

GitHub evaluates the workflow run’s event ref. Consequences:

| Invocation | Result under branch policy `main` |
|---|---|
| Dispatch another branch, even checking out `main` | Refused |
| Dispatch `main`, then checkout/execute another ref | Admitted; checkout provenance is not checked by this policy |
| Ordinary unmerged `pull_request` | Refused: ref is `refs/pull/N/merge` |
| Merged-PR event, or `pull_request_target`, whose evaluated ref is `main` | Can qualify |
| Off-branch caller invoking reusable workflow `@main` | Refused; caller context governs |
| Main caller invoking reusable workflow at another ref | Can qualify |
| Tag dispatch, including tag `main` | Refused |

These follow from [event-ref semantics](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows), [ref context](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts#github-context), and [reusable-workflow context](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations#github-context).

3. **The gate remains an account approval checkpoint, not independent review.**

With bypass disabled, administrators cannot force waiting jobs through the configured protection rules. They can still approve as the designated reviewer, and administrators retain authority to change/delete the environment configuration. [Deployment review](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/review-deployments), [Environment administration](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments).

The trust table must distinguish:

- GitHub enforces eligible event refs and recorded approval before releasing this environment’s secrets.
- It does not establish an independent human decision, honest code, a specific permitted workflow, or the provenance of downloaded/checked-out code.
- PR/check/merge-queue requirements do not themselves enforce **Codex review** unless a required check implements that requirement.
- Act 2b’s staging copy in `data-plane-production-cutover` is outside the seal gate’s protection.

4. **Cutover compatibility: expected for main flows, but the finding overstates its evidence.**

For `workflow_run`, GitHub documents `GITHUB_REF` as the **default branch**. Consequently, with default branch `main`, the environment policy matches `main`, independently of `workflow_run.head_sha` or the checkout ref. This is a documented inference, not a live compatibility test. Preserve the separate upstream `branches: [main]` filter. [Workflow-run documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_run).

Apply only the corresponding branch-policy change there, preserving that environment’s own settings—not the seal environment’s reviewer body. Replace “cannot break existing flows” with “expected compatible with the documented main-ref flows; requires controlled readback and workflow-run verification.”

**Checkout correction:** both `privileged-bootstrap` and `jataka-protected-migrations` are explicitly `workflow_dispatch`-only here; routine `migrate` has no environment. Thus adding a reviewer would pause those protected jobs and credential preflight, **not this revision’s ordinary automatic deploy path**. Any automatic job that actually references the environment would wait, subject to its retained bypass setting. The one-shot and proof workflows are absent from this checkout, so their current source cannot be certified.

5. **Required wording changes.**

In **Act 5**, replace the creation-only precondition for this repair with:

> The existing environment must match the recorded act-5 configuration, contain no secrets, and have no outstanding jobs using it. Any discrepancy is STOP.

Replace “ONE API call” with:

> TWO sequential API calls: PUT the complete existing body with `protected_branches:false, custom_branch_policies:true`; then POST `{"name":"main","type":"branch"}` to its deployment-branch-policies endpoint. Verify the complete configuration and exactly one branch policy before proof. No secret may be provisioned until both proofs pass.

Replace **checklist row 6’s action/evidence/failure wording** with:

> Prove the unchanged no-secret workflow from a non-main branch: GitHub must reject the environment job for its branch policy before runner execution, with no pending approval. A dispatch error, skipped job, or workflow-local ref guard is not passing evidence. Then dispatch from main: observe WAIT, capture owner-account approval with the ruling comment, and observe successful execution. Retain configuration, policy-list, run/ref, rejection, and approval evidence. Any mismatch is STOP; cancel probes and keep secrets absent.

Replace the trust-table branch claim with:

> Only workflow runs whose evaluated event ref matches branch `main` qualify; this does not constrain code subsequently fetched or executed.

Replace the admin claim with:

> Runtime bypass is disabled while this configuration remains intact; administrative reconfiguration remains possible.

Finally, replace **“STOP and revert”** with an explicit failed-proof hold. Restoring the old policy restores the demonstrated weakness; deleting the environment is not a durable lock because a later workflow can recreate it without protection rules. Update the corresponding “protected branches” wording in the live-gate proof, act 2b verification, and §5.3. [Environment creation/deletion behavior](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments).

