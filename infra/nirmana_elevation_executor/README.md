# Nirmana elevation executor/verifier Terraform root

This root owns only the two Nirmana campaign identities below and uses the
dedicated GCS state prefix `nirmana-elevation-executor`. It is intentionally
separate from `infra/nirmana_elevation_monitor` (a different, already-live
identity) and from `infra/scheduler`, whose remote state owns unrelated
Scheduler jobs. State ownership is an operational release gate: do not infer
it from this repository layout or from an earlier claim.

## Why two identities

`platform/src/app/api/admin/internal/nirmana-elevation-executor/route.ts`
authenticates its OIDC caller against a per-command principal allowlist:
non-terminal commands (record_definition, freeze_definition,
supersede_definition, record_label_catalogue, accept_baseline_candidate, and
every record_evidence event_type except the terminal-capsule ones) accept
only `amjis-nirmana-executor@...`; terminal-capsule commands
(`asset_frozen`, and `stage_transition_accepted` when it represents a layer
freeze) accept only `amjis-nirmana-verifier@...`. This makes the campaign's
implementer-never-certifies-terminal rule identity-enforced at the route,
not only enforced by the pre-existing DB-role trigger that separates
`server_reconstructed` writes (ingress writer) from other writes (control
writer) -- see CAMPAIGN_STATE.md for the residual this does *not* close (the
native currently holds impersonation rights to both identities).

## Resources

- `google_service_account.nirmana_elevation_executor` — the dedicated
  `amjis-nirmana-executor` OIDC identity.
- `google_service_account.nirmana_elevation_verifier` — the dedicated
  `amjis-nirmana-verifier` OIDC identity.
- `google_service_account_iam_member.native_impersonates_executor` /
  `..._verifier` — `roles/iam.serviceAccountTokenCreator` on each SA, for the
  native's own Google identity only. This is the sole permission granted:
  it lets the native mint short-lived ID tokens for either identity via
  `gcloud auth print-identity-token --impersonate-service-account=<sa-email>
  --audiences=<audience>` on demand, per action. There is no standing
  trigger, no Cloud Scheduler job, no key file, and no CI workflow that
  assumes either identity.

**No `roles/run.invoker` grant.** `amjis-web`'s Cloud Run IAM policy already
grants `roles/run.invoker` to `allUsers` (verified live, 2026-09-01, via
`gcloud run services get-iam-policy amjis-web`) — the service is publicly
reachable at the network level, and every route under
`platform/src/app/api/admin/internal/` performs its own authorization at the
application layer via `verifyOidcToken()`. An invoker grant here would be
redundant, not load-bearing. (The monitor root's own invoker grant predates
this observation and is likewise redundant, not incorrect — it is simply
unnecessary defense-in-depth, not something this root needed to repeat.)

## Apply discipline and bootstrap permissions

Identical discipline to `infra/nirmana_elevation_monitor` — see that root's
README for the full rationale. Summary: the GCP-native release path does not
depend on GitHub. A named, approved GCP release operator creates
`executor.tfplan` with Terraform and then applies that exact saved plan from
a trusted GCP environment. The wrapper accepts an apply only when
`IAC_APPLY_ENVIRONMENT=production` and `GOOGLE_CLOUD_RELEASE_APPROVAL`
contains the recorded change/approval reference. Those values are
traceability guards; GCP IAM and Cloud Audit Logs are the actual
authorization and evidence boundary.

Use short-lived Application Default Credentials or service-account
impersonation for the approved GCP release identity. The wrapper refuses
`GOOGLE_APPLICATION_CREDENTIALS`, so static service-account key files cannot
become an alternate release path.

The execution sequence is deliberately two-person and saved-plan based:

1. The approved GCP release operator creates a saved plan:
   `bash apply.sh plan executor.tfplan`.
2. An independent reviewer records that the plan has exactly the approved
   resource changes (two service accounts, two IAM member bindings, nothing
   else) and cites the approval reference.
3. The same approved GCP release identity applies that unchanged file with
   `IAC_APPLY_ENVIRONMENT=production` and the recorded
   `GOOGLE_CLOUD_RELEASE_APPROVAL`.
4. Retain the Terraform output and corresponding Cloud Audit Logs entries as
   the release evidence. Do not use `-auto-approve`, ad-hoc console edits, or
   a new plan in place of the reviewed saved plan.

GitHub Actions has no apply path for this root; it is not a runtime or
provisioning dependency.

Before the first apply, name the GCP operator group or dedicated release
service account in the approval record. Grant the first-apply permissions
only to that identity for the approved release window. The Terraform
executor needs only the following first-apply permission families, scoped
to this project, the two dedicated service accounts, and this state prefix
where the platform permits it:

| Scope                                  | Required permissions                                                                                                                                                                         |
| --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Project and the two dedicated SAs       | `resourcemanager.projects.get`, `iam.serviceAccounts.create`, `iam.serviceAccounts.get`, `iam.serviceAccounts.getIamPolicy`, `iam.serviceAccounts.setIamPolicy`                             |
| `nirmana-elevation-executor` state objects | the existing Terraform-state read/write/lock object permissions (`get`, `list`, `create`, `update`, and lock release)                                                                    |

No project-wide role, `roles/run.invoker` grant, or permission touching any
other service account is required. No permission is granted by this
repository change beyond the two `serviceAccountTokenCreator` bindings above.

## After apply: swap the route's hardcoded principals

`nirmana-elevation-executor/route.ts` currently has `EXECUTOR_PRINCIPAL =
'mail.abhisek.mohanty@gmail.com'` as a documented placeholder (see the
route's own comment) — a human identity that cannot mint an audience-bound
OIDC token, so nothing can currently authenticate through it. Once this root
is applied, a follow-up PR swaps that constant to the two SA emails from
this root's outputs, per the per-command allowlist described above. Verify
the swap against the applied `nirmana_elevation_executor_email` /
`nirmana_elevation_verifier_email` Terraform outputs, not against this
document's account-id strings, in case either changes before apply.
