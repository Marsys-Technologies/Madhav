---
artifact: AI_CLI_UNREACHABLE_DIAGNOSIS_v1_0.md
canonical_id: AI_CLI_UNREACHABLE_DIAGNOSIS
version: 1.0
status: ACTIVE — diagnosis only, no fix proposed
date: 2026-10-03
authored_by: Stream C (Kimi) — steward task C45
scope: >
  Repository-only diagnosis of the pariprashna-post-deploy-smoke.yml 'behaviour-smoke' job
  failing with HTTP 400 code AI_CLI_UNREACHABLE ('The selected CLI could not be reached') on
  synthetic chart 1c826d5a, 0 successes in the last 100 runs. No network calls to production,
  no secrets, no gcloud, no database were used; every claim below cites repo file:line.
---

# AI_CLI_UNREACHABLE on the post-deploy behaviour smoke — diagnosis

## 0. TL;DR

The smoke deliberately resolves the probe principal's **configured default AI choice**, which —
by design (owner-surrogate ruling OSR-007) — is the **local CLI `claude_code`**, executed through
the **CLI bridge at `http://10.160.0.2:8787`** (a VM-side service), not through a provider API.
The most likely cause of a *deterministic* HTTP 400 on every run is a **latched database state**:
`ai_cli_installations.validation_state` for `claude_code` is no longer `'reachable'`, so the
turn-prepare check throws `AI_CLI_UNREACHABLE` **before any executor or bridge call exists** — and
nothing in the serving path ever revalidates, so the failure cannot self-heal. The unprovisioned
`ANTHROPIC_API_KEY` (CLAUDE.md v7.2) is **not** on this code path at all and is excluded below.

## 1. Where the error is raised, and why it is an HTTP 400

The smoke's failing job runs `platform/scripts/probe/post_deploy_behavior_smoke.ts`, which drives
`platform/scripts/probe/ask.ts`. ask.ts POSTs `/api/pariprashna` with
(`platform/scripts/probe/ask.ts:303-312`):

```json
{ "chartId": "1c826d5a-…", "ai_selection": { "kind": "default" }, "reading_depth": "auto",
  "length_tier": "standard", "messages": [ … ] }
```

The comment at ask.ts:306-308 states this is deliberate: "the standing probe always asks
Pariprashna to resolve this account's configured default."

In the route (`platform/src/app/api/pariprashna/route.ts`):

- `:90` — `byokEnabled = configService.getFlag('AI_CONSOLE_BYOK')`. Production sets
  `MARSYS_FLAG_AI_CONSOLE_BYOK=true` (`.github/workflows/deploy.yml:1436`), so every web turn
  takes the BYOK branch at `:131`.
- `:141-150` — `prepareByokTurn(...)` runs synchronously **before** the stream starts.
- `:152-155` — any `AiConsoleError` thrown inside prepare is returned as
  `Response.json(safe.toJSON(), { status: 400 })` (429 only for `AI_RATE_LIMITED`).

So the observed **HTTP 400 + coded body can only come from the synchronous prepare phase**
(`prepareByokTurn` → `prepareTurnRouting` → `loadRoutingTarget`, or executor construction).
Anything that fails later — including a genuinely dead bridge at execution time — surfaces as an
error event *inside* the stream (HTTP 200), not a 400. The public message text
('The selected CLI could not be reached') is `platform/src/lib/ai-console/errors.ts:21`.

## 2. What "the selected CLI" means here

Resolution chain for `ai_selection: { kind: 'default' }`:

1. `platform/src/lib/ai-console/repository.ts:340-342` — reads the account's
   `ai_user_defaults` row (`AI_DEFAULT_REQUIRED` if absent — a *different* code, so the row exists).
2. The probe principal's default is, by design, `{ kind: 'local_cli', cliId: 'claude_code',
   modelId: null }` — `platform/scripts/probe/set_default.ts:33-34` exists solely to set exactly
   that, per OSR-007; `platform/migrations/1119_purna_acceptance_probe_cli_grants.sql:57-58`
   grants the probe principal exactly one CLI, `claude_code`. `modelId: null` means the CLI's
   built-in default model (set_default.ts:32-33 comment; repository.ts:313-314
   `m.is_builtin_default=true`).
3. For a `local_cli` target, `loadRoutingTarget`
   (`platform/src/lib/ai-console/repository.ts:302-326`) checks, in order:
   - `:302` registry has an execution definition → `AI_CLI_UNREACHABLE` (not the case for
     `claude_code`: `platform/src/lib/ai-console/cli/registry.ts:65-81` defines it);
   - `:305` grant non-revoked → `AI_CLI_NOT_GRANTED` (a different code);
   - `:308` installation `validation_state='not_installed'` → `AI_CLI_NOT_INSTALLED` (different code);
   - `:309` `validation_state='auth_unavailable'` → `AI_CLI_AUTH_UNAVAILABLE` (different code);
   - **`:310` `validation_state` is anything other than `'reachable'` → `AI_CLI_UNREACHABLE`**;
   - `:316` model row missing/unavailable → `AI_MODEL_UNAVAILABLE` (different code).

   **Of all prepare-time throw sites, only :310 produces the observed code.** The probe's grant
   is migration-pinned and the model is the built-in default seeded by validation, so the
   deterministic candidate is: the `claude_code` installation row's `validation_state` is
   latched at `unreachable` / `needs_attention` / `untested` (anything ≠ `'reachable'`).

4. How the CLI would be executed if the check passed: production runs the **remote bridge
   runner**, not a local spawn — `createConfiguredCliRunner`
   (`platform/src/lib/ai-console/cli/runner.ts:1161-1169`) picks `RemoteCliRunner` when
   `MARSYS_AI_CLI_BRIDGE_URL`/`MARSYS_AI_CLI_BRIDGE_TOKEN` are set, and deploy.yml sets both:
   `MARSYS_AI_CLI_BRIDGE_URL=http://10.160.0.2:8787` (deploy.yml:1439, plain env),
   `MARSYS_AI_CLI_BRIDGE_TOKEN=marsys-ai-cli-bridge-token:1` (deploy.yml:1459, Secret Manager
   reference). Local execution is explicitly off: `MARSYS_AI_LOCAL_CLI_EXECUTION_ENABLED=false`
   (deploy.yml:1438). The bridge itself is `platform/scripts/ai-cli-bridge/server.mjs`, which
   runs the actual `claude` binary on that VM.

## 3. Why the failure is deterministic (0/100) and cannot self-heal

`validation_state` is written by exactly one function: `validateCli`
(`platform/src/lib/ai-console/cli/validation.ts:25-200`), which persists
`unreachable` / `auth_unavailable` / `needs_attention` / `not_installed` via
`storeCliValidation` (e.g. validation.ts:93-94 on a failed `inspectInstallation`, :124-125 on
auth failure, :145-148 on a changed binary). Its only callers are:

- the AI Console UI endpoints `…/clis/[cliId]/validate` and `…/clis/[cliId]/refresh`
  (manual, human-driven);
- execution-time revalidation `revalidateCliForExecution`
  (`platform/src/lib/ai-console/cli/runner.ts:1111-1116`), reached from
  `ensureConfirmed` **during a turn's execution phase**.

The self-latching structure: once the row is not `'reachable'`, the *prepare-time* check
(repository.ts:310) throws before any executor is constructed (route.ts:141-155 → 400), so the
execution-time revalidation that could flip the row back **never runs**. The only ways back to
`'reachable'` are the two manual UI endpoints. One bad night (bridge VM down, token rotation,
binary upgrade on the VM) latches the row, and every later run fails identically at prepare —
exactly the observed 0-successes-in-100-runs signature. No cron revalidates CLI installations
(the only writers are the three call sites above).

## 4. Candidate causes, ranked

### C1 (most likely) — latched `validation_state ≠ 'reachable'` on the `claude_code` installation row
Evidence: repository.ts:310 is the only prepare-time site producing this code; the latch
mechanics in §3 make it permanent and deterministic. The original cause of the flip is recorded
in the row itself (`last_error_code`, `last_checked_at`).
Cheap confirm: one read-only production query —
`SELECT cli_id, validation_state, last_error_code, last_checked_at, detected_version FROM ai_cli_installations WHERE cli_id='claude_code';`
(plus `SELECT kind, cli_id, model_id FROM ai_user_defaults WHERE user_id='probe-service-account';`
to confirm the selection is still the by-design `local_cli/claude_code/null`).
User impact if confirmed: **only selections that route to the `claude_code` CLI are broken** —
the probe principal (by design) and any real user who chose a local-CLI default in AI Console.
Users on `provider_model` defaults (e.g. a Gemini connection) prepare and run normally.

### C2 — the bridge host genuinely failed first (the cause *behind* the C1 latch)
The bridge is a VM-side service at `10.160.0.2:8787` (deploy.yml:1439; contract-pinned in
`platform/src/lib/ai-console/__tests__/deployment_contract.test.ts:35-36` and
`cli_bridge_contract.test.ts:52`). Any of: VM stopped/preempted, internal IP changed, bridge
process dead, token drift between `marsys-ai-cli-bridge-token:1` and the VM's token file, or the
VM's own `claude` binary upgraded (its entrypoint sha256 is pinned per installation —
runner.ts:1122-1128 treats a changed identity as unreachable) or de-authenticated
(validation.ts:124-125 → `auth_unavailable`, which would instead 400 as
`AI_CLI_AUTH_UNAVAILABLE` — *not* observed, so auth-on-VM is less likely than reachability).
Cheap confirm: the same C1 row's `last_error_code` + `last_checked_at` names and dates the first
failure; then a steward-side `gcloud compute instances describe` of the bridge VM and a
Secret Manager version check. (Both are owner-side checks; nothing in the repo can settle them.)
User impact if confirmed: same blast radius as C1 — CLI selections only. Note that *with a dead
bridge but a `'reachable'` row*, the first failing turn would show a **streamed** error
(runner.ts:321/333 → retry once → `AI_CLI_UNREACHABLE` event), and the revalidation inside that
turn would flip the row — after which every turn looks like C1. The observed 100% 400s mean the
row is already latched.

### C3 — bridge URL/token miswired at deploy
`createConfiguredCliRunner` throws `AI_CLI_UNREACHABLE` if only one of URL/token is set
(runner.ts:1165) or the URL fails the private-endpoint rules (runner.ts:1147-1158). deploy.yml
sets both (1439/1459) and the URL passes the 10.x rule, so this would require a *live* drift
from the repo config (e.g. a secret deleted, an env removed by another deploy path).
Cheap confirm: steward-side `gcloud run services describe amjis-web …` env/secrets diff against
deploy.yml:1438-1459. Low likelihood (config is static and contract-tested), but one command
excludes it. User impact if confirmed: all CLI selections broken from that deploy onward;
provider selections unaffected.

### Excluded candidates (the evidence rules them out)
- **Unprovisioned `ANTHROPIC_API_KEY`** (CLAUDE.md v7.2 known fact): confirmed absent from the
  production secret list (deploy.yml:1441-1459 — OpenAI/Google/DeepSeek/NIM keys present, no
  Anthropic). But the smoke never touches the Anthropic *provider* path: its selection resolves
  to the `local_cli` target (§2), and the legacy stack path (where `DEFAULT_STACK_ID='gemini'`
  lives, `platform/src/lib/models/registry.ts:872`) runs only in the flag-**off** `else` branch
  (route.ts:157-161). With BYOK on, no turn consults `DEFAULT_STACK_ID`. A user whose default
  were an Anthropic *connection* would fail with `AI_CONNECTION_INVALID`-class codes
  (errors.ts:101-102), not `AI_CLI_UNREACHABLE`. Not the cause; also not what a real user on the
  default stack would hit.
- **Smoke misconfiguration**: the request body is the by-design contract (ask.ts:306-308),
  secrets are shape-preflighted before the turn (workflow lines 161-189), and a missing default
  row would read `AI_DEFAULT_REQUIRED`, a revoked grant `AI_CLI_NOT_GRANTED`, an expired VM auth
  `AI_CLI_AUTH_UNAVAILABLE` — none of which is the observed code. The smoke is measuring a real
  production state, not misconfigured.
- **Executor-construction throws** (`cli-executor.ts:31-32`): `AI_CLI_NOT_INSTALLED` /
  `AI_CLI_UNREACHABLE` only if the registry entry lacked an execution definition — it does not
  (registry.ts:74-81). Ruled out for `claude_code`.

## 5. What a real user experiences, per candidate

| Candidate | Probe smoke | Real users |
|---|---|---|
| C1 latched state | 400 `AI_CLI_UNREACHABLE` every run | Broken **only** for users whose AI Console default/custom config routes to `claude_code` (same 400). Everyone else normal. |
| C2 bridge down (pre-latch) | first failures = streamed error, then C1 | Same shape: one streamed failure, then 400s for CLI selections; provider selections never affected. |
| C3 deploy miswire | 400 from that deploy on | All CLI selections broken; provider selections fine. |
| (Excluded) Anthropic key gap | never observed here | Would break only users who explicitly picked an Anthropic provider connection, with a *different* code. |

In no candidate is the whole user base broken, and in no candidate is the default
(gemini-stack, provider-key) path implicated — BYOK turns never consult it (route.ts:131 vs 157).

## 6. Deliberately not done

No fix proposed (per task). No workflow change. No production calls, no credential use, no
database access — all evidence above is from the repository at the branch base.
