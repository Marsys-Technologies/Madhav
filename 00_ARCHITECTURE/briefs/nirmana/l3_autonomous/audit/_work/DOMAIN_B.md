# Kāla Readiness Audit — Domain B: Acceptance Machinery

Scope: the executor/verifier split that gates NIRMĀṆA campaign evidence acceptance — HTTP route
`requiredPrincipalFor`, DB trigger `nirmana_elevation_guard_server_reconstructed_insert`, and the
`nrec` CLI wrapper. Read-only audit; no DML/DDL executed, no credentials printed.

## 1. `nrec` CLI (`platform/scripts/nirmana/nrec`)

Read directly (`Read` tool, full 160-line file). Summary:

- **Purpose**: single sanctioned path for submitting a NIRMĀṆA evidence/definition command to the
  executor HTTP route, under the *correct* service-account identity, refusing to send it under the
  wrong one.
- **Invocation modes**: `nrec --as executor|verifier --file cmd.json`, stdin piping, and
  `--dry-run` (decide only, mint/send nothing).
- **Identity derivation** (lines 84–89): required identity is derived from the submitted body's
  `command` + `source_kind` — `record_evidence` + `source_kind == 'server_reconstructed'` →
  `verifier`; everything else → `executor`. This intentionally mirrors `requiredPrincipalFor()` in
  `route.ts` rather than hardcoding an `event_type` list (explicit design decision, documented in
  the header comment and again in the README).
- **`--as` is mandatory and checked, not inferred** (lines 63–66, 91–109): a mismatch between
  `--as` and the derived requirement causes the script to **refuse and exit 2** before minting any
  token or sending anything (`if [ "$AS" != "$REQUIRED" ]`). This is the load-bearing
  implementer≠certifier guard at the tool layer.
- **Token minting** (lines 121–141): `gcloud auth print-identity-token --impersonate-service-account=... --audiences=... --include-email`. `--include-email` is **hardcoded inside the script**, not exposed as a caller-supplied flag — the caller cannot omit it. One retry with a 5s sleep on first mint failure (propagation-delay workaround), then a hard `die` with a diagnostic hint.
- **HTTP call**: POST to the fixed `ROUTE` with `Authorization: Bearer $TOKEN`, non-2xx status
  branches into specific diagnostics for 403 (identity/`--include-email` hint) and 409 (idempotency
  — "usually correct, not an error").

**Verdict for this sub-check**: nrec itself does not have a silent-403 hole — `--include-email` is
unconditionally passed by the tool, so a caller using `nrec` cannot trigger the failure mode by
omission. See §2 for whether the *route* itself fails closed if a caller bypasses `nrec` and mints
a token without `--include-email`.

## 2. HTTP route — `requiredPrincipalFor` and the auth path

File: `platform/src/app/api/admin/internal/nirmana-elevation-executor/route.ts` (Read tool, lines
1–113, full file).

- `requiredPrincipalFor()` — lines 43–54: pure function, same source_kind-derived split as `nrec`
  (`record_evidence` + `source_kind === 'server_reconstructed'` → `VERIFIER_PRINCIPAL`, else
  `EXECUTOR_PRINCIPAL`).
- Auth flow — lines 58–107:
  1. Line 60: missing/malformed `Authorization: Bearer` header → `401`.
  2. Lines 72–89: `verifyOidcToken(token, { expectedAudience: EXECUTOR_OIDC_AUDIENCE })`. If the
     returned `identity` is falsy **or** `identity.email` is not one of the two allowlisted
     principals → `403 forbidden`. Any thrown error (bad/expired token) is also caught → `403`.
  3. Lines 91–100: body JSON-parsed and Zod-validated (`nirmanaEvidenceCommand.safeParse`) → `400`
     on failure.
  4. Line 102: `actorEmail !== requiredPrincipalFor(parsed.data)` → `403 principal not authorized`.

**Silent-403 check (explicit ask in the brief)**: this is **not** a silent-success/wrong-identity
bug — it fails **closed**, correctly, in every branch. The specific `--include-email` hazard is
that if a caller mints a token *without* `nrec` and omits `--include-email`, the minted JWT carries
no `email` claim; `verifyOidcToken()` (not read in full here, but per the route's own comment at
lines 31–39 and the `nrec` script comment lines 121–124 / README §"`--include-email` is not
optional") returns a payload with `email` absent, so `identity.email` fails the allowlist check and
the route answers a **generic 403** — indistinguishable at the HTTP layer from "wrong SA" or
"expired token" **without already knowing to check this specific cause**. This is a genuine
diagnosability footgun, explicitly documented in three places (route.ts header comment, nrec
header comment, README.md lines 93–99, dated to a real incident "2026-09-01" in `CAMPAIGN_STATE.md`
per the README), but it is **not** a security defect — the failure mode is "reject a legitimate
caller with a confusing error," never "accept an illegitimate one."

- **More consequential finding — the separation-of-duties residual** (route.ts lines 31–39, "HONEST
  RESIDUAL" comment, verbatim in the file): *"the native currently holds `serviceAccountTokenCreator`
  on both identities, so this allowlist enforces separation of what a given authenticated call may
  submit, not separation between disjoint human principals."* In other words: the HTTP-layer +
  DB-trigger split enforces that **a single call** cannot claim both hats, but does **not** prevent
  the **same human** (the native) from minting a verifier token and an executor token for the same
  asset in two separate calls, since both SAs' impersonation rights resolve to the one identity. The
  file states plainly that the actual implementer≠certifier guarantee today rests on the campaign's
  *procedural* fresh-context-verification protocol (a terminal capsule only minted after independent
  reconstruction), not on access control disjointness. This is accurately self-disclosed in the code
  comment, not hidden — but it is a real gap between "acceptance machinery enforces implementer ≠
  certifier" (as claimed in nrec's own header, line 16) and what is cryptographically/IAM-enforced.

## 3. DB trigger — `nirmana_elevation_guard_server_reconstructed_insert`

Queried live (one-shot, capped):
```
source /Users/Dev/madhav-l3/dbenv.sh && psql -Atq -c "SELECT current_user"
psql -Atq -c "SELECT pg_get_functiondef(oid) FROM pg_proc WHERE proname = 'nirmana_elevation_guard_server_reconstructed_insert'"
```
`current_user` = `amjis_app`. Function definition (verbatim, `nirmana_evidence` schema):

```sql
CREATE OR REPLACE FUNCTION nirmana_evidence.nirmana_elevation_guard_server_reconstructed_insert()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$ BEGIN
        IF session_user <> current_user THEN RAISE EXCEPTION 'Nirmana evidence writers may not cross roles'; END IF;
        IF NEW.source_kind = 'server_reconstructed' THEN IF session_user <> 'nirmana_evidence_ingress_writer' THEN RAISE EXCEPTION 'server evidence requires ingress writer'; END IF;
        ELSIF session_user <> 'nirmana_campaign_control_writer' THEN RAISE EXCEPTION 'non-server evidence requires control writer'; END IF;
        NEW.writer_identity := session_user; RETURN NEW;
      END $function$
```

Attachment (one-shot query on `pg_trigger`):
```sql
SELECT tgname, tgrelid::regclass, tgtype, pg_get_triggerdef(oid)
FROM pg_trigger WHERE tgfoid = 'nirmana_evidence.nirmana_elevation_guard_server_reconstructed_insert'::regproc
```
→ `nirmana_elevation_events_server_writer` — **BEFORE INSERT** on
`nirmana_evidence.nirmana_elevation_campaign_events`, `FOR EACH ROW`.

Enforcement summary:
- Refuses any session that has switched roles mid-session (`session_user <> current_user` — guards
  against `SET ROLE` tricks within one DB session).
- `source_kind = 'server_reconstructed'` rows require DB session role
  `nirmana_evidence_ingress_writer`; all other rows require `nirmana_campaign_control_writer`. Both
  are hard `RAISE EXCEPTION`s — insert fails outright, not a soft flag.
- `NEW.writer_identity` is **stamped by the trigger from `session_user`**, not trusted from the
  inserted row — so the identity attribution is DB-role-authoritative, not application-claimed. This
  is the correct pattern (matches §N.8 Earned-Signal doctrine: the claim and the detector are the
  same mechanism, not a self-reported field).
- Matches the HTTP-layer split exactly (`server_reconstructed` → verifier-equivalent DB role;
  else → executor-equivalent DB role), confirming the "two layers, same rule" claim in the code
  comments and README is accurate as implemented, not just asserted.

This DB-role split is a **stronger** control than the HTTP-layer allowlist: DB role membership
(`nirmana_evidence_ingress_writer` / `nirmana_campaign_control_writer`) is presumably granted
independently of who holds `serviceAccountTokenCreator` on the two GCP SAs — but this audit did not
verify DB role grants (out of scope for the capped commands run; would need
`SELECT rolname FROM pg_roles WHERE ...` / `pg_auth_members` to confirm whether the same backend
application role ultimately exercises both DB roles). **Flagged as unverified, not as a defect.**

## 4. README / credential-holder runbook

File: `platform/scripts/nirmana/README.md` (read in full, 142 lines).

- Confirms nrec requires `jq`, `curl`, and "a `gcloud` session holding `serviceAccountTokenCreator`
  on the two campaign service accounts" (line 63–64) — i.e. the README itself documents that one
  operator session is expected to hold impersonation rights to **both** `amjis-nirmana-executor` and
  `amjis-nirmana-verifier`, consistent with the route.ts "HONEST RESIDUAL" comment in §2 above.
- Per `route.ts` lines 15–19 and 31–34 (comment, not independently re-verified against live IAM by
  this audit — no `gcloud iam` command was run, per the brief's instruction to skip unless a single
  fast command): `serviceAccountTokenCreator` on both SAs is granted **only to the native's own
  Google identity**, for on-demand impersonation; no standing trigger, no key file, no invoker grant.
  This audit did **not** run a live `gcloud iam service-accounts get-iam-policy` check to confirm
  current grant state — reported here as the runbook's documented design, not independently
  re-verified against live IAM. **This is the one item in this domain that would need a live IAM
  read to fully close** (a single fast, read-only `gcloud iam service-accounts get-iam-policy
  <sa>@madhav-astrology.iam.gserviceaccount.com` per SA would settle it, but was skipped per the
  brief's caution against commands the auditor is "unsure" will be fast/safe in this non-interactive
  context).
- `capsule_audit.sql` (documented in the same README) is a continuously-run, SQL-only audit
  instrument with a §2 section specifically checking "was the implementer ≠ certifier identity split
  ever crossed?" with pass condition "every row `ok`, none `*** CROSSED ***`" — i.e. there is already
  a live, re-runnable detector for a crossing, which is exactly the kind of real-detector-behind-the-
  claim discipline CLAUDE.md §N.8 asks for. This audit did not execute `capsule_audit.sql` (would
  require judgement calls about DB write scope / long-running query risk out of scope for this
  capped pass) but notes its existence as a positive structural finding.

## Classification: READY (with one open verification item, not a blocking defect)

**Acceptance machinery is structurally sound and fails closed everywhere checked:**
- HTTP route: fails closed on missing/invalid auth, unparseable body, and identity/command mismatch
  (all branches return 401/403/400, never a silent pass-through).
- DB trigger: fails closed via hard exceptions on role mismatch; identity is DB-role-stamped, not
  self-reported.
- CLI (`nrec`): hardcodes the one previously-costly footgun (`--include-email`) so operators cannot
  omit it; refuses identity mismatches before any network call.
- A continuously-run SQL detector (`capsule_audit.sql`) already exists specifically to catch a real
  crossing of the implementer≠certifier line, not just assert it never happens.

**What could have made this NOT READY / NEEDS DECISION, and why it doesn't quite tip there:**
1. *Silent-403 from missing `--include-email`* — this was the brief's named suspicion. Confirmed
   real as a **diagnosability** hazard (a confusing generic 403), but confirmed **not** a security
   hole — the route never grants access on a malformed/incomplete token, and the one sanctioned
   tool (`nrec`) cannot trigger it since the flag is hardcoded, not caller-supplied. Downgraded from
   "possible silent 403 defect" to "documented, mitigated footgun."
2. *Separation of duties* — the executor and verifier GCP identities are both impersonable by the
   same human principal (the native), self-disclosed in `route.ts`'s own "HONEST RESIDUAL" comment.
   This means the HTTP+DB technical controls enforce "no single call wears both hats" but not "no
   single human can act as both over two calls" — that residual guarantee is procedural (fresh-
   context verification protocol), not access-control-enforced. This is an accepted, documented
   design tradeoff rather than an undiscovered gap, so it does not by itself block readiness — but a
   reviewer should be aware "implementer ≠ certifier" in this campaign is **partially** procedural,
   not fully cryptographic.
3. *Live IAM grant state* — not independently re-verified in this pass (no `gcloud iam` command run,
   per the brief's caution). Everything reported about "who currently holds valid tokens" traces to
   in-repo comments/README, not a live policy read. If a fully closed audit is required, this is the
   one follow-up: a single `gcloud iam service-accounts get-iam-policy` call per SA.

None of the three items above is a defect discovered by this audit that the campaign doesn't already
know about — all three are already named, in the native's own words, in the code/README. Domain B
is assessed **READY** for the acceptance-machinery claim, with the live-IAM-grant confirmation
flagged as an easy, low-risk follow-up rather than a blocker.
