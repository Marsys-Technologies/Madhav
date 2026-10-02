---
artifact: AI_CONSOLE_CATALOG_REFRESH_PLAN
version: 1.0
status: PRODUCTION_CATALOGUE_SCOPE_VERIFIED
produced_on: 2026-10-02
authority: Continuing native AI Console feature request
---

# AI Console catalogue refresh

Add a refresh icon on each API provider and authorized CLI card. On page entry,
refresh stale metadata in the background, with a fifteen-minute success cache,
one-minute failure/manual cooldown, and a database lease shared across instances.
Display the last successful refresh, installed CLI version, and a safe failure
message. A refresh never changes a saved default, role assignment or effort.

API refresh calls only authenticated model-list endpoints. Existing exact-key
generation evidence and model selections survive for models still in the catalogue.
New API models remain discovery candidates until the user explicitly tests them.
Where APIs do not advertise effort metadata, retain conservative provider capability
rules; do not claim those rules came from the catalogue.

CLI refresh uses the configured execution host. Production uses the dedicated
private VM bridge; this Mac is a different installation. Codex app-server model/list
and Claude control initialization may advertise subscription models and effort
levels. Keep only safe capability metadata, never account material. Retain generation
readiness only for the same verified executable/version; a changed installation
requires the explicit local CLI test. New catalogue models are labeled discovered,
not individually generation-tested. Arbitrary effort strings are accepted only when
the exact model advertises them and runtime authorization checks them again.
Historical reachable installations without an executable fingerprint retain their
existing readiness when the detected version is unchanged; metadata refresh cannot
create a verified fingerprint or warm an execution cache. The existing cold-start
execution revalidation or an explicit CLI test establishes that baseline. Unlisted
manual models retain exact-binary test evidence but use Model default only when
there is no current effort capability metadata.

Preserve provider-locked role setups and explicit mixed custom configurations.
Unavailable saved choices stay visible with a repair message. No silent substitution.
Refresh does not install or upgrade CLI binaries.

Verification: protocol pagination, process bounds/cancellation, subscription-only
authentication, grant isolation, credential/epoch fencing, TTL/cooldown, preservation
on failed refresh, model removal, dynamically advertised effort, scoped UI refresh,
and full repository quality gates. Independent code/security/migration review follows.
Production release remains a separate exact-revision milestone after these pass.

## Corrected production milestone — 3 October 2026

PR #2985 and automatic deployment `37071001730` released exact runtime main
`55a666f8943bcda313f1e9bc52f3ea3d47916c96`, with the paired private bridge and
unchanged applied migration 1301. Authenticated catalogue refresh, provider-locked
and mixed unsaved CLI model/effort controls, explicit AGY installation validation
and the independent 15-minute watch passed. The first PR #2977 rollout failed
live acceptance and was rolled back; it is not retroactively called successful.

`PRODUCTION_ACCEPTANCE.md` is the scoped live receipt and records the unrelated
successor-main deployment in progress, existing account/setup issues, transient
UI-hint residual and separate failing full Pariprasna behaviour smoke. No paid API
test, saved role/default change, universal model access or whole-pipeline health
is inferred from this catalogue milestone.

Integration-only accommodation: current main's migration-1255 static test lacked
TypeScript guards for two array lookups. Added explicit undefined guards after
existing single-element assertions; no migration SQL or Gochara behavior changed.
