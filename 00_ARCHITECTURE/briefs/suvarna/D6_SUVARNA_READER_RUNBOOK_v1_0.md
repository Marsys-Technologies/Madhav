---
artifact: D6_SUVARNA_READER_RUNBOOK
canonical_id: D6_SUVARNA_READER_RUNBOOK
version: "1.1"
status: DRAFT — for native review; nothing has been run against any database
produced_on: 2026-09-29
produced_in: session "Strategic Suvarṇa" (D6 implementation draft)
implements: native decision D6 (2026-09-29) — Suvarṇa reads production through a dedicated, genuinely read-only login
tooling:
  - platform/scripts/suvarna-reader-bootstrap.ts (one-shot administrator bootstrap; --dry-run / --apply / --rollback)
  - platform/scripts/governance/suvarna_tracker/monitor.py (checks credential and credential_readonly)
supersedes: platform/scripts/governance/suvarna_tracker/setup_reader.sh (deleted — it assumed the app login could set passwords; it cannot)
changelog:
  - "1.1 (2026-09-29): security review 2 applied. (1) The write-capable app-login backup moves to ~/.config/madhav-admin/ (dir 700, files 600, never overwritten); rollback restores from there; the Monitor WARNs on any pgenv*.bak* / pgenv.previous* beside the credential. (2) SET LOCAL search_path = pg_catalog, pg_temp is the first statement of every transaction; every relation is schema-qualified; the roles snapshot also compares rolvaliduntil, rolconfig and per-database role settings. (3) The COMMIT runs in its own try: on failure the new Secret Manager version is disabled and the run reports 'COMMIT outcome unknown'; after a proven apply older versions are disabled. (4) --apply needs --expect-plan=<sha256>; the dry run prints the plan, EXCLUDED and PII lists in full with that hash (targets + column spec + exclusion decisions). (5) Role defaults: statement_timeout 120s, idle_in_transaction_session_timeout 60s, lock_timeout 5s, temp_file_limit 1GB, read-only on; the Monitor WARNs if they differ and BLOCKs on owned large objects. (6) public.charts is granted column-level SELECT on 7 non-personal columns only; definer views/matviews reaching an RLS table are excluded unless --accept-view. (7) Deny list widened by 15 patterns; any readable PII-looking column fails the dry run unless --accept-pii. (8) SECURITY DEFINER checks drop the schema-USAGE condition (bootstrap and Monitor). (9) pg_shdepend catch-all for ACL dependencies (bootstrap V15, existing-reader refusal, Monitor). (10) Monitor requires session_user = current_user = suvarna_reader and reports the session read-only value (with its source) separately from the role default. (11) Monitor shlex-quotes path and SQL and pins search_path. (12) gcloud runs with a minimal environment; its stderr is redacted. (13) SCRAM verifier exposure documented; pg_stat_statements entries reset after apply (best effort). (14) Atomic writes unlink the temp file if the rename fails. (15) Rollback restores only over a file with PGUSER=suvarna_reader and keeps the replaced file. (16) --data-plane-gate-amended is refused unless the checked-out gate names suvarna_reader; runbook adds subshell / unset, npx --no-install, the post-apply gate run, and 'never during a deploy or migration'. Also corrected: §5's charts RLS description (chart_service_policy exposes all rows when app.principal_id is unset)."
  - "1.0 (2026-09-29): first runbook. Blocking prerequisite found while drafting: the deployed data-plane gate (data-plane-ownership-status.ts) rejects any new grantee on schema public and on the protected L1/L2 tables, so it must be amended and deployed before --apply. Rollback is a script mode because a hand-typed REVOKE by postgres cannot remove owner-made grants."
---

# D6 — the `suvarna_reader` login: runbook

**What this does.** It creates the login `suvarna_reader`, which can read the tables Suvarṇa needs and
has no write to application data. It replaces `amjis_app`, the app login Suvarṇa uses today.
`amjis_app` holds about 1,370 write grants and is "read-only" only through a session setting.

**What "no write" means exactly.** The reader has no write to application data: no table, column or
sequence write, no CREATE, no ownership, no role membership, no reachable SECURITY DEFINER function
(unless accepted by name). Residual surfaces remain and are limited and monitored:

- its own role settings (it can `SET` the user-settable ones in its own session, e.g. raise
  `statement_timeout`; it cannot change `temp_file_limit`, which is superuser-only);
- session-local temporary objects (through the database's PUBLIC `TEMPORARY`), capped by
  `temp_file_limit = 1GB`;
- large objects, if it turns off `default_transaction_read_only` in its own session (the Monitor
  BLOCKs if it owns any);
- advisory locks (session-scoped, released on disconnect).

**How it does it.** The native runs one script as `postgres`. It does not use a migration: the
migration runner (`amjis_app`) lost CREATEROLE and table-grant rights in the data-plane and Nirmāṇa
ownership handoffs. The script follows `data-plane-ownership-preflight.ts`:

- every grant is made as the object's owner;
- any owner membership that `postgres` lacks is added for the transaction only and removed before
  commit;
- every transaction starts with `SET LOCAL search_path = pg_catalog, pg_temp`, and every relation is
  schema-qualified;
- nothing commits unless every check passes and the plan matches the reviewed dry run.

## 0 · Blocking: the data-plane deploy gate must be amended first

Every deploy runs `platform/scripts/data-plane-ownership-status.ts`. Two of its checks would fail as
soon as `suvarna_reader` exists:

- **Schema `public`:** the gate compares the schema's access list against an exact list (FULL JOIN).
  A new `USAGE` grantee therefore fails the gate with *"Public schema ACL allowlist drift"*.
- **Protected L1/L2 tables and their history tables:** the gate keeps an allowlist of grantees. A
  `SELECT` for a grantee outside the list fails the gate with *"Protected table ACL allowlist drift"*.

The reader needs both, because Suvarṇa reads `chart_facts`, `bodha_*` and the rest. Applying the
bootstrap without amending the gate would **block the next deploy**. By default the script detects
this: the checks D3, D4 and D5 print **DATA-PLANE GATE CONFLICT**, and the run fails.

**The amendment** (a separate, reviewed PR on `main`; this session has not written it). It admits
`suvarna_reader` and nothing else:

1. `schemaAcl`: add a conditional expected row, the same pattern already used for
   `purna_inquiry_owner`:
   `UNION ALL SELECT 'suvarna_reader','USAGE' WHERE to_regrole('suvarna_reader') IS NOT NULL`.
2. `aclSurface`: in the first `EXISTS`, add
   `AND NOT (a.grantee='suvarna_reader' AND a.privilege_type='SELECT')`.
3. `historyAcl`: the same exception in its first `EXISTS`.
4. Sequence and function allowlists: no change, because the reader gets no sequence or function
   grants.
5. Update any contract test that pins these queries (see `platform/tests/unit/data_plane_security_contract.test.ts`).

Once the amendment is **merged and deployed**, pass `--data-plane-gate-amended`. The script refuses
that flag unless the `data-plane-ownership-status.ts` next to it (the checked-out branch, resolved
from the script's own directory) mentions `suvarna_reader`, so run it from a checkout that contains
the amendment. It then accepts only the reader's own `SELECT`/`USAGE` entries in D3–D5, and still
fails on anything else.

If the native decides not to amend the gate, D6 cannot proceed as designed. Without `USAGE` on
`public`, the reader can read nothing there.

Keep in mind: if the data-plane ownership preflight is ever re-run (it only runs when the gate says
the boundary is unmarked or needs repair), it revokes every non-listed grantee on `public` and on the
protected tables. The reader would silently lose read access. It would still have no write path, so
the Monitor stays OK, but its queries would fail. The fix is to re-run this bootstrap.

## 1 · Prerequisites and ground rules

- **Never run any mode during a deploy or a migration.** Check that no deploy workflow is running
  and no migration is in progress first. The script takes catalog snapshots and handoff invariants
  before and after; a concurrent deploy would make them diverge, and its grants race the deploy's.
- **A checkout of `main`** that contains the script and the gate amendment, with the platform
  dependencies installed. The script needs `pg` and `tsx`, the same pair `deploy.yml` installs.
  Always call it with `npx --no-install tsx`, so npx can never fetch a package at run time.
- **The Cloud SQL proxy on 127.0.0.1:5433:**
  `cloud-sql-proxy --address 127.0.0.1 --port 5433 madhav-astrology:asia-south1:amjis-postgres`
- **The admin URL, set by the native in a subshell.** It must authenticate directly as `postgres`.
  The script rejects any other user, any host other than 127.0.0.1, and any `host`/`user`/`options`
  query override. It never prints the URL, and never passes it (or anything else from your shell)
  to `gcloud`, which runs with only `PATH`, `HOME` and `CLOUDSDK_CONFIG`. Keep the URL out of shell
  history and out of your long-lived shell: run everything inside `( … )`, or `unset
  SUVARNA_READER_ADMIN_DATABASE_URL` as soon as you finish.
  ```bash
  (
    read -rs -p 'postgres password: ' PGADMINPW; echo; export PGADMINPW
    export SUVARNA_READER_ADMIN_DATABASE_URL="postgres://postgres:$(python3 -c 'import os,urllib.parse;print(urllib.parse.quote(os.environ["PGADMINPW"],safe=""))')@127.0.0.1:5433/amjis"
    unset PGADMINPW
    cd platform
    npx --no-install tsx scripts/suvarna-reader-bootstrap.ts --data-plane-gate-amended
  )
  ```
- **For `--apply` only: `gcloud` authenticated** (`gcloud auth list` shows an active account), with
  rights to create, add, list and disable versions of Secret Manager secrets in project
  `madhav-astrology`.
- **The gate amendment from §0 deployed.** The dry run works without it, but will show the conflict.

## 2 · Dry run (the default; always rolls back)

```bash
# inside the subshell from §1, in platform/
npx --no-install tsx scripts/suvarna-reader-bootstrap.ts                              # before the gate amendment
npx --no-install tsx scripts/suvarna-reader-bootstrap.ts --data-plane-gate-amended    # after it is deployed
```

**What the output must show before you apply:**

1. **Actor and role.** `actor: postgres (CREATEROLE), server_version_num=15…`. Then the role is
   either created, or found to exist and pass the normalisation checks: not elevated, no
   memberships, owns nothing, no ACL dependency outside this database's relations/schemas/CONNECT,
   and holds only table SELECT, column SELECT on `public.charts`, schema USAGE and CONNECT.
   Then the role defaults, one line each (see §5). If `temp_file_limit` is refused (it is a
   superuser-only setting and Cloud SQL's `postgres` may lack `SET` on it), the run shows
   `R role default temp_file_limit` FAIL and rolls back: stop and decide.
2. **The plan, printed in full** (nothing is truncated):
   - The read set, counted by source: census, asset_registry, fixed, nirmana_evidence.
   - The owner of each group, and every relation in it. `public.charts` is marked `COLUMN-LEVEL`.
   - `public.charts columns GRANTED` and `public.charts columns WITHHELD` (§5).
   - An **EXCLUDED** list: deny-list matches; any view that reads `auth` or a denied table; and any
     view or materialized view that reaches a row-level-security table without
     `security_invoker=true` (on the view itself and on every view on the way; a materialized view
     never qualifies). Keep one only with `--accept-view=<schema.rel>`, repeatable.
   - Any `asset_registry.target_table` value that has no table.
   - **`PLAN SHA256: <64 hex>`** — sha256 over the sorted `schema.name` targets, the column-level
     grant spec (granted and withheld columns) and every exclusion decision (and any accepted PII
     relation). Write it down: `--apply` needs it.
3. **The grants.**
   - CONNECT.
   - USAGE on `public` (made as `data_plane_schema_owner`) and on `nirmana_evidence` (made as
     `nirmana_evidence_owner`).
   - Column SELECT on `public.charts`, with the withheld list.
   - One SELECT line per owner.
   - "Sequences: none".
   - The temporary memberships that were used and removed. Expect some of `amjis_app`, the
     `data_plane_*_owner` roles, `nirmana_evidence_owner` and `purna_inquiry_owner`.
4. **V0–V15 all PASS:**
   - V0: LOGIN NOINHERIT, connection limit 10, and the role defaults exactly as listed in §5 (every
     database);
   - V1–V3: CONNECT, USAGE, SELECT on every table-level target; **V3b**: on `public.charts` every
     granted column selectable, no withheld column selectable, no table-level SELECT;
   - V4–V9: no memberships, owns nothing, no database or schema CREATE, no
     INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER on any relation (table or column level), no
     sequence USAGE/UPDATE;
   - V10: no executable SECURITY DEFINER function outside `pg_catalog` **in any schema** — schema
     USAGE is not required, because an operator, cast or aggregate can call a function in a schema
     the reader cannot use;
   - V11–V13: schema `auth` and any view over it unreachable; deny-listed tables unreadable; no
     default-privilege grants to the reader;
   - V15: zero `pg_shdepend` ACL entries for the reader other than this database's relations and
     schemas and database CONNECT (a catch-all for function/type/large-object/default-ACL grants and
     for grants in any other database).

   INFO lines are allowed. **V6b TEMPORARY** is normally allowed through PUBLIC (session-local temp
   tables only). **V14** lists anything readable beyond the plan through PUBLIC grants; read it.
5. **The handoff invariants, all PASS** (baseline and after):
   - N1–N9: the Nirmāṇa evidence handoff and migration 633's attestation.
   - D1–D7: the data-plane gate, and it must pass under the amended gate.
   - P1–P3: the Pūrṇa owner/serving topology, which must not change.
6. **The snapshots.** `S memberships`, `S roles` and `S acl` each show **+0 −0**. The roles
   snapshot now includes each role's `rolvaliduntil`, `rolconfig` and per-database settings, so a
   changed expiry or role default on any other role is caught. Every role, membership and ACL other
   than the reader's own is exactly as found.
7. **The RLS and PII sections.** Read them (§5). `PII columns` must PASS: every readable relation
   with a column matching the PII/credential name pattern (for `public.charts`, only its granted
   columns count) fails the run unless accepted with `--accept-pii=<schema.rel>` (repeatable). The
   whole list is printed.
8. **The last line:** `RESULT: PASS (dry run) — … nothing persisted. PLAN SHA256: …`.

**If V10 lists a SECURITY DEFINER function** that PUBLIC can execute, it is a real write path: it runs
as its owner. The native can either revoke PUBLIC EXECUTE on it, as the owner, in a reviewed change,
or accept it by name. Accepting uses the exact text the dry run prints:
`--accept-secdef='public.fn(integer)'`, which can be repeated. The Monitor must accept the same list
through `SUVARNA_READER_SECDEF_ALLOW` (`;`-separated). Both sides print signatures under
`search_path = pg_catalog`, so they are always schema-qualified and match.

**If `CREATE ROLE … PASSWORD` is rejected:** the script sends a SCRAM verifier it computed itself.
If the instance enforces Cloud SQL password validation, the server may refuse a pre-hashed
password. Stop and decide. The script has deliberately no plaintext fallback, because a plaintext
password in the statement could reach server logs.

**The SCRAM verifier is not the password, but treat it as sensitive.** The `CREATE/ALTER ROLE …
PASSWORD '<verifier>'` statement text can reach `pg_stat_statements` (utility statements are tracked
by default) and the server log (if `log_statement` is `ddl` or `all`). A verifier cannot be used to
log in directly, but it allows an offline guessing attack on the password (48 random alphanumerics
make that impractical) and, with the server key, impersonating the server to a client. After
`--apply` commits, the script resets the matching `pg_stat_statements` entries if the extension
exists and `pg_stat_statements_reset(oid, oid, bigint)` is callable by `postgres`; it reports
whether it could. It cannot remove server-log lines: check the Cloud SQL `log_statement` flag, and
if it logs DDL, note the log window. Dry runs also send a verifier, but of a password that is
discarded and a role that is rolled back.

## 3 · Apply

```bash
# inside the subshell from §1, in platform/, NOT during a deploy or migration
npx --no-install tsx scripts/suvarna-reader-bootstrap.ts --apply --data-plane-gate-amended \
  --expect-plan=<the PLAN SHA256 from the reviewed dry run> [--accept-secdef=…] [--accept-pii=…] [--accept-view=…]
```

Pass the same `--accept-*` values as the reviewed dry run; they are part of the plan.

The steps, in order:

1. The gcloud and secret checks run before the database is touched. The secret
   `suvarna-reader-password` is created if it is missing.
2. The whole dry-run sequence runs in one transaction. The plan hash is recomputed and **must equal
   `--expect-plan`**; any change to the targets, the `charts` column split or an exclusion since the
   reviewed dry run fails the run and rolls back.
3. Only if every check passes, the password is added as a new secret version, fed through stdin. The
   version id is recorded.
4. COMMIT, in its own error handler. If the COMMIT fails or its outcome is unknown (for example the
   connection drops), the new secret version is **disabled** and the run ends with
   `RESULT: COMMIT outcome unknown: check pg_roles for suvarna_reader; re-run --apply (it resets the password).`
5. `pg_stat_statements` entries for the reader's PASSWORD statements are reset (best effort,
   reported).
6. The script connects **as `suvarna_reader`** and repeats the self-checks.
7. Only then is `~/.config/suvarna/pgenv.sh` replaced: atomically (temp file removed if the rename
   fails), mode 600, holding PGHOST, PGPORT=5433, PGDATABASE, PGUSER=suvarna_reader, PGPASSWORD and
   `PGOPTIONS='-c default_transaction_read_only=on'`.
8. Every older ENABLED version of the secret is disabled (reported per version).

**The previous credential file is the write-capable app login.** It is backed up to
`~/.config/madhav-admin/pgenv.app-login.bak` (directory mode 700, file mode 600), **never** beside
the reader credential. An existing backup is never overwritten: a differing current file is kept as
`~/.config/madhav-admin/pgenv.previous.<timestamp>.bak`, and a superseded reader file as
`pgenv.suvarna-reader.<timestamp>.bak`. The Monitor warns if any `pgenv*.bak*` or `pgenv.previous*`
file appears in `~/.config/suvarna/`.

The password is never printed. It exists only in Secret Manager and in the credential file.

Possible final results:

- `RESULT: APPLIED` — done.
- `APPLIED BUT UNPROVEN` — the role and secret are committed, but the login test failed, so the
  credential file was **not** changed and older secret versions were **not** disabled. Investigate,
  then re-run `--apply`; it resets the password.
- `COMMIT outcome unknown` — see step 4.

**Right after `RESULT: APPLIED`, run the deploy gate** (read-only) and confirm it prints `marked`:

```bash
# still in platform/; the gate needs DATABASE_URL, e.g. the reader credential just written:
( source ~/.config/suvarna/pgenv.sh && DATABASE_URL="postgres://$PGUSER@$PGHOST:$PGPORT/$PGDATABASE" \
    npx --no-install tsx scripts/data-plane-ownership-status.ts )
```

It reads only catalogs and `public._migrations_applied`, both readable by the reader (node-pg takes
the password from `PGPASSWORD`). Any drift error here means the next deploy would fail: roll back
(§6) or fix before the next deploy. Then leave the subshell (or `unset
SUVARNA_READER_ADMIN_DATABASE_URL`).

## 4 · Post-checks

1. **The Monitor.** From `platform/scripts/governance`, run `python3 -m suvarna_tracker.monitor --once`.
   - `credential` must be OK. It WARNs if a `pgenv*.bak*` / `pgenv.previous*` file sits beside the
     credential (names only; it never opens any file).
   - `credential_readonly` must read:
     `OK … suvarna_reader: no write path (…); session default_transaction_read_only=on (source client); role default read-only=on, role defaults as expected; …`.

   The check runs one query through `bash -c` with the path and SQL `shlex`-quoted and
   `set search_path = pg_catalog;` first. It evaluates, as the login itself:
   - table and column write privileges on every relation;
   - sequences;
   - database and schema CREATE;
   - memberships in both directions;
   - ownership, including large objects;
   - ACL dependencies outside this database's relations/schemas/CONNECT (`pg_shdepend`);
   - elevated attributes;
   - executable SECURITY DEFINER functions in any schema;
   - access to `auth`;
   - `session_user`, `current_user`, the session's read-only value and its source, and the role's
     own defaults from `pg_db_role_setting`.

   It reports BLOCK on any write path (including owned large objects); WARN if `session_user` and
   `current_user` are not both `suvarna_reader`, if the session is not read-only, or if the role
   defaults differ from §5's set; and OK only when every check passes.
2. **The tracker.** Run `curl -s http://127.0.0.1:8765/api/health`. Both `detector_errors` and
   `metrics_errors` must be `[]`. The database detectors read `asset_registry` and
   `information_schema.columns`. The second only shows columns of tables the reader can access, so
   a detector aimed at a table outside the read set will report it as missing. A detector that
   selects a withheld `charts` column (e.g. `SELECT *` on `charts`) now fails with a permission
   error: name the granted columns.
3. **The next deploy.** Its step "Inspect protected data-plane ownership state" must print `marked`.

## 5 · What the native must knowingly accept

**The dry run's lists are authoritative.** The items below come from the repository's migrations
(`platform/migrations/001_baseline.sql`, `platform/supabase/migrations/0001_brahma_baseline.sql`)
and are an early warning only.

**Role defaults** (`ALTER ROLE suvarna_reader SET …`; checked by V0 and by the Monitor):

| setting | value |
|---|---|
| `default_transaction_read_only` | `on` |
| `statement_timeout` | `120s` |
| `idle_in_transaction_session_timeout` | `60s` |
| `lock_timeout` | `5s` |
| `temp_file_limit` | `1GB` |
| connection limit | 10 |

These are defaults. The reader can lower or raise the first four in its own session; it cannot
change `temp_file_limit`. The Monitor checks the role's stored defaults, not each session.

**`public.charts` — column-level SELECT only.**

| granted (7) | withheld (12) |
|---|---|
| `id`, `chart_id`, `role`, `ayanamsa`, `house_system`, `created_at`, `created_at_iso` | `client_id`, `name`, `birth_date`, `birth_time`, `birth_place`, `birth_lat`, `birth_lng`, `native_id`, `owner_id`, `subject_name`, `preferred_name`, `timezone_id` |

- Withheld because they carry birth data (date, time, place, coordinates, timezone) or identify a
  person or account (names, the Firebase-UID `client_id`, the principal `owner_id`, the `native_id`
  slug). Any column in production that is not on the granted list is withheld too, and printed.
- Suvarṇa gets chart ids and non-personal configuration, which is what it joins on.

**Row-level security.** No policy is added: that is the native's decision.

- **`charts` — the reader sees ALL rows unless it sets a session value.** The migrations define
  three policies: `chart_service_policy` (FOR ALL, to PUBLIC, passes when `app.principal_id` is unset
  or empty), `chart_owner_policy` (`owner_id` = `app.principal_id`) and `chart_grant_policy` (via
  `chart_grants`, which is why that table is in the read set). A reader session that never sets
  `app.principal_id` therefore matches every row. That is why the column-level grant matters: every
  row is visible, but only the 7 non-personal columns.
  - Any login with SELECT on `charts` can also `SET app.principal_id` to any principal. This is how
    the app scopes access today; it is not something this bootstrap introduces.
- **`charts` — queries may error.** If the legacy policy `"charts: astrologer all"` (built on
  `auth.uid()` and `profiles`) still exists in production, every `charts` query by the reader will
  **fail**: the reader has no access to `auth`, and `profiles` is deny-listed. The dry-run section
  "applicable policies that reference objects suvarna_reader cannot use" shows whether this applies.
- **`chart_divisionals` — zero rows.** Its only policy is `"service role full access"`, for the role
  `service_role`, so the reader silently sees nothing. It is also a protected L1 table: adding a
  policy would change the data-plane gate's policy attestation too.
- **Views over RLS tables.** A view without `security_invoker=true`, or any materialized view, runs
  with its owner's rights and returns rows the table's policies would hide. Such relations in the
  read set are EXCLUDED unless `--accept-view=<schema.rel>`.
- **Other tables with RLS, if they are in the read set:** `predictions` (its policy reads
  `query_trace_steps`) and the `planner_inquiry_*` tables (principal policies). The legacy
  user-content tables and `planner_managed_prashna_jobs` are now deny-listed.

**PII and sensitive content.**

- Any readable relation with a PII/credential-looking column name (email, phone, mobile, birth, dob,
  first/last/full/display/subject/preferred `_name`, address, ip, uid, password, token, secret,
  api_key, latitude/longitude) fails the dry run unless accepted with
  `--accept-pii=<schema.rel>`. The full list is printed. Ephemeris-style `latitude`/`longitude`
  columns will appear here and need an explicit decision.

**The deny-list** (never granted; widening it means editing `DENY_PATTERNS` in the script):

- `profiles`, `access_requests`, `conversation_%`, `mcp_oauth_%`, `ai_provider_connections`,
  `mv_session_summary`, `query_baseline_stats`, and everything in schema `auth`;
- `mcp_api_keys` — API-key material, the same class as `mcp_oauth_%`;
- added in 1.1: `message_parts`, `mcp_sessions`, `planner_managed_prashna_jobs`, `admin_audit_log`,
  `audit_log`, `audit_events`, `ai_custom_configurations`, `ai_user_defaults`, `ai_cli_grants`,
  `chart_subject_consent%`, and the user-content tables `messages`, `documents`, `reports`,
  `chat_attachments`, `message_feedback`;
- automatically, any view that reads `auth` or a denied table.

These are SQL `LIKE` patterns, so `conversation_%` also matches `conversations`, and `_` matches any
single character (so a pattern can only over-deny).

## 6 · Rollback

```bash
# inside the subshell from §1, in platform/, NOT during a deploy or migration
npx --no-install tsx scripts/suvarna-reader-bootstrap.ts --rollback            # dry run: proves it would work
npx --no-install tsx scripts/suvarna-reader-bootstrap.ts --rollback --apply
```

The rollback uses the same admin route. In one transaction (also starting with
`SET LOCAL search_path = pg_catalog, pg_temp`), it:

- revokes every grant `suvarna_reader` holds, **each as its grantor** (a plain `REVOKE` by
  `postgres` cannot remove a grant an owner made), including the column grants on `charts`;
- runs `DROP ROLE suvarna_reader` (its role defaults go with it);
- proves the same handoff invariants and snapshots;
- on `--apply`, restores `~/.config/suvarna/pgenv.sh` from `~/.config/madhav-admin/pgenv.app-login.bak`
  — **only if** the current `pgenv.sh` has the line `PGUSER=suvarna_reader` (only that line is
  checked). The replaced reader file is kept as
  `~/.config/madhav-admin/pgenv.suvarna-reader.<timestamp>.bak`; the app-login backup is kept too.
  Otherwise the file is left untouched and the run says why.

The Secret Manager secret is left in place; disable its versions yourself if you want. After a
rollback the Monitor returns to BLOCK, which is correct: the app login has write grants. Run
`data-plane-ownership-status.ts` again afterwards (§3).

The manual equivalent, shown only so the mechanism is clear:

```sql
BEGIN;
SET LOCAL search_path = pg_catalog, pg_temp;
GRANT <each grantor postgres is not already a member of> TO postgres;
SET LOCAL ROLE <grantor>; REVOKE ALL ON TABLE <its tables, including public.charts> FROM suvarna_reader; RESET ROLE;   -- per grantor
SET LOCAL ROLE data_plane_schema_owner; REVOKE ALL ON SCHEMA public FROM suvarna_reader; RESET ROLE;
SET LOCAL ROLE nirmana_evidence_owner;  REVOKE ALL ON SCHEMA nirmana_evidence FROM suvarna_reader; RESET ROLE;
REVOKE ALL ON DATABASE amjis FROM suvarna_reader;
REVOKE <every grantor granted above> FROM postgres;   -- mandatory: the handoff checks forbid these edges
DROP ROLE suvarna_reader;
COMMIT;
```

Then restore the file: `cp -p ~/.config/madhav-admin/pgenv.app-login.bak ~/.config/suvarna/pgenv.sh`
(after moving the reader file into `~/.config/madhav-admin/`). The gate amendment from §0 can stay:
it admits `suvarna_reader` only when that role exists.
