---
artifact: PURNA_ACCEPTANCE_PROBE_PLANNER_VERIFICATION_PROCEDURE
version: 1.1
status: PREPARED_OWNER_SURROGATE_SYSTEM_IDENTITY_PATH
date: 2026-09-29
campaign_id: madhav-purna-anvesana
authority: Native decision 2026-09-29 (Decision 1)
principal: probe-service-account
---

# Minimal proof that one probe-account planner call succeeds

Owner-Surrogate Ruling OSR-003 replaces the former human-operator wait. The campaign must first use
an already-approved system-owned connection or workload-identity provider path. If none exists, it
may implement a protected service-owned acceptance principal through the existing provider
abstraction without creating IAM or embedding a secret. Never copy or reuse another user's
credential. A genuinely absent third-party entitlement is recorded once as a terminal external
dependency and does not pause the remaining runnable queue.

## What "fixed" means

A planner-role invocation for `probe-service-account` reaches `succeeded` in
`ai_turn_role_invocations`, and a turn reaches `turn.close status=ok` with committed prose. No secret
is read, recorded or printed at any step.

## Steps

1. **Before** (read-only) — record the baseline: 0 successes of 7 planner calls for the account.
   ```sql
   select i.status, count(*) from ai_turn_role_invocations i
   join ai_turn_routing_snapshots s on s.id = i.snapshot_id
   where s.user_id = 'probe-service-account' and i.role = 'planner' and i.phase = 'terminal'
   group by 1;
   ```
2. **Connection state** (read-only, metadata only): `ai_provider_connections` row(s) for the account —
   `credential_validity`, `validation_state`, `last_validated_at`, `last_error_code`,
   `credential_version` must show the new/validated connection; the default in `ai_user_defaults`
   must point at it. Do not select any `credential_*` or `wrapped_*` column.
3. **One planner call** — a question that reaches the planner (not a clarification):
   ```bash
   cd platform && npx tsx scripts/probe/ask.ts \
     "What does my current Vimshottari dasha period mean for my career?" > /dev/null
   ```
   The script mints its own session in memory, writes one gitignored JSON under
   `scripts/probe/out/`, and never prints the cookie or key.
4. **Assert** on the output file (no prose printed):
   ```bash
   node -e 'const r=JSON.parse(require("fs").readFileSync(process.argv[1],"utf8"));
   const e=r.events.filter(x=>x.type==="error");
   console.log({terminal:r.terminal_status,errors:e.map(x=>x.raw.code),blocks:r.blocks.length,proseChars:(r.prose||"").length})' \
     platform/scripts/probe/out/<file>.json
   ```
   Pass = `terminal: "ok"`, `errors: []`, `blocks >= 1`, `proseChars > 0`.
5. **After** (read-only) — rerun the step-1 query: at least one `succeeded` planner row newer than the
   repair, and no `AI_EXECUTION_FAILED` for that turn's snapshot.
6. **Stop condition** — if the call fails again with `PLANNER_INVALID_PLAN`, do not repeat it. Report
   the new `error_code` from `ai_turn_role_invocations`; a specific code (e.g. `AI_CONNECTION_INVALID`,
   `AI_RATE_LIMITED`) now indicates the credential/quota cause. If it is again `AI_EXECUTION_FAILED`,
   the raw provider error is redacted by design and only the operator, who holds the provider console,
   can read it.

## Notes

- The synthetic chart `1c826d5a-…` is not a valid acceptance target (its latest build failed); use the
  canonical chart after the rebuild for the golden inquiry. This procedure only proves the provider
  lane and can use the default chart.
- Related unmerged source: PR #2755 adds a bounded selected-to-Default fallback per role. It is not
  part of this campaign and does not replace a working probe connection.
