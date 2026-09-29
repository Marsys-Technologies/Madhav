---
artifact: D6_SUVARNA_READER_RUNBOOK
canonical_id: D6_SUVARNA_READER_RUNBOOK
version: "1.0"
status: DRAFT — for native review; nothing has been run against any database
produced_on: 2026-09-29
produced_in: session "Strategic Suvarṇa" (D6 implementation draft)
implements: native decision D6 (2026-09-29) — Suvarṇa reads production through a dedicated, genuinely read-only login
tooling:
  - platform/scripts/suvarna-reader-bootstrap.ts (one-shot administrator bootstrap; --dry-run / --apply / --rollback)
  - platform/scripts/governance/suvarna_tracker/monitor.py (check credential_readonly)
supersedes: platform/scripts/governance/suvarna_tracker/setup_reader.sh (deleted — it assumed the app login could set passwords; it cannot)
changelog:
  - "1.0 (2026-09-29): first runbook. Blocking prerequisite found while drafting: the deployed data-plane gate (data-plane-ownership-status.ts) rejects any new grantee on schema public and on the protected L1/L2 tables, so it must be amended and deployed before --apply. Rollback is a script mode because a hand-typed REVOKE by postgres cannot remove owner-made grants."
---

# D6 — the `suvarna_reader` login: runbook

**What this does.** It creates the login `suvarna_reader`, which can read the tables Suvarṇa needs and
has no way to write. It replaces `amjis_app`, the app login Suvarṇa uses today. `amjis_app` holds
about 1,370 write grants and is "read-only" only through a session setting.

**How it does it.** The native runs one script as `postgres`. It does not use a migration: the
migration runner (`amjis_app`) lost CREATEROLE and table-grant rights in the data-plane and Nirmāṇa
ownership handoffs. The script follows `data-plane-ownership-preflight.ts`:

- every grant is made as the object's owner;
- any owner membership that `postgres` lacks is added for the transaction only and removed before
  commit;
- nothing commits unless every check passes.

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

Once the amendment is **merged and deployed**, pass `--data-plane-gate-amended`. The script then
accepts only the reader's own `SELECT`/`USAGE` entries in D3–D5, and still fails on anything else.

If the native decides not to amend the gate, D6 cannot proceed as designed. Without `USAGE` on
`public`, the reader can read nothing there.

Keep in mind: if the data-plane ownership preflight is ever re-run (it only runs when the gate says
the boundary is unmarked or needs repair), it revokes every non-listed grantee on `public` and on the
protected tables. The reader would silently lose read access. It would still have no write path, so
the Monitor stays OK, but its queries would fail. The fix is to re-run this bootstrap.

## 1 · Prerequisites

- **A checkout of `main`** that contains the script, with the platform dependencies installed. The
  script needs `pg` and `tsx`, the same pair `deploy.yml` installs.
- **The Cloud SQL proxy on 127.0.0.1:5433:**
  `cloud-sql-proxy --address 127.0.0.1 --port 5433 madhav-astrology:asia-south1:amjis-postgres`
- **The admin URL, set by the native in their own shell.** It must authenticate directly as
  `postgres`. The script rejects any other user, any host other than 127.0.0.1, and any
  `host`/`user`/`options` query override. It never prints the URL. One way to keep the password out
  of shell history:
  ```bash
  read -rs -p 'postgres password: ' PGADMINPW; echo; export PGADMINPW
  export SUVARNA_READER_ADMIN_DATABASE_URL="postgres://postgres:$(python3 -c 'import os,urllib.parse;print(urllib.parse.quote(os.environ["PGADMINPW"],safe=""))')@127.0.0.1:5433/amjis"
  unset PGADMINPW
  ```
- **For `--apply` only: `gcloud` authenticated** (`gcloud auth list` shows an active account), with
  rights to create and add versions of Secret Manager secrets in project `madhav-astrology`.
- **The gate amendment from §0 deployed.** The dry run works without it, but will show the conflict.

## 2 · Dry run (the default; always rolls back)

```bash
cd platform
npx tsx scripts/suvarna-reader-bootstrap.ts                              # before the gate amendment
npx tsx scripts/suvarna-reader-bootstrap.ts --data-plane-gate-amended    # after it is deployed
```

**What the output must show before you apply:**

1. **Actor and role.** `actor: postgres (CREATEROLE), server_version_num=15…`. Then the role is
   either created, or found to exist and pass the normalisation checks: not elevated, no
   memberships, owns nothing, and holds only SELECT/USAGE/CONNECT grants.
2. **The plan.**
   - The read set, counted by source: census, asset_registry, fixed, nirmana_evidence.
   - The owner of each group, and every relation in it.
   - An **EXCLUDED** list: deny-list matches, plus any view that reads `auth` or a denied table.
   - Any `asset_registry.target_table` value that has no table.
3. **The grants.**
   - CONNECT.
   - USAGE on `public` (made as `data_plane_schema_owner`) and on `nirmana_evidence` (made as
     `nirmana_evidence_owner`).
   - One SELECT line per owner.
   - "Sequences: none".
   - The temporary memberships that were used and removed. Expect some of `amjis_app`, the
     `data_plane_*_owner` roles, `nirmana_evidence_owner` and `purna_inquiry_owner`.
4. **V0–V13 all PASS:**
   - LOGIN NOINHERIT and the read-only role default;
   - CONNECT, USAGE, and SELECT on every target;
   - no memberships, owns nothing;
   - no database or schema CREATE;
   - no INSERT/UPDATE/DELETE/TRUNCATE/REFERENCES/TRIGGER on any relation, at table or column level;
   - no sequence USAGE/UPDATE;
   - no reachable SECURITY DEFINER function outside `pg_catalog`;
   - schema `auth` and any view over it unreachable;
   - deny-listed tables unreadable;
   - no default-privilege grants to the reader.

   INFO lines are allowed. **V6b TEMPORARY** is normally allowed through PUBLIC (session-local temp
   tables only). **V14** lists anything readable beyond the plan through PUBLIC grants; read it.
5. **The handoff invariants, all PASS** (baseline and after):
   - N1–N9: the Nirmāṇa evidence handoff and migration 633's attestation.
   - D1–D7: the data-plane gate, and it must pass under the amended gate.
   - P1–P3: the Pūrṇa owner/serving topology, which must not change.
6. **The snapshots.** `S memberships`, `S roles` and `S acl` each show **+0 −0**. That means every
   role, membership and ACL other than the reader's own is exactly as found.
7. **The RLS and PII sections.** Read them (§5).
8. **The last line:** `RESULT: PASS (dry run) — … nothing persisted.`

**If V10 lists a SECURITY DEFINER function** that PUBLIC can execute, it is a real write path: it runs
as its owner. The native can either revoke PUBLIC EXECUTE on it, as the owner, in a reviewed change,
or accept it by name. Accepting uses the exact text the dry run prints:
`--accept-secdef='public.fn(integer)'`, which can be repeated. The Monitor must accept the same list
through `SUVARNA_READER_SECDEF_ALLOW` (`;`-separated).

**If `CREATE ROLE … PASSWORD` is rejected:** the script sends a SCRAM verifier it computed itself.
If the instance enforces Cloud SQL password validation, the server may refuse a pre-hashed
password. Stop and decide. The script has deliberately no plaintext fallback, because a plaintext
password in the statement could reach server logs.

## 3 · Apply

```bash
npx tsx scripts/suvarna-reader-bootstrap.ts --apply --data-plane-gate-amended [--accept-secdef=…]
```

The steps, in order:

1. The gcloud and secret checks run before the database is touched. The secret
   `suvarna-reader-password` is created if it is missing.
2. The whole dry-run sequence runs in one transaction.
3. Only if every check passes, the password is added as a new secret version, fed through stdin.
4. COMMIT.
5. The script connects **as `suvarna_reader`** and repeats the self-checks.
6. Only then is `~/.config/suvarna/pgenv.sh` replaced: atomically, mode 600, holding PGHOST,
   PGPORT=5433, PGDATABASE, PGUSER=suvarna_reader, PGPASSWORD and
   `PGOPTIONS='-c default_transaction_read_only=on'`.

The previous file is kept as `pgenv.app-login.bak` (mode 600). An existing `.bak` is never
overwritten; a differing current file is kept under a timestamped name instead.

The password is never printed. It exists only in Secret Manager and in the credential file.

Possible final results:

- `RESULT: APPLIED` — done.
- `APPLIED BUT UNPROVEN` — the role and secret are committed, but the login test failed, so the
  credential file was **not** changed. Investigate, then re-run `--apply`; it resets the password.

## 4 · Post-checks

1. **The Monitor.** From `platform/scripts/governance`, run `python3 -m suvarna_tracker.monitor --once`.
   `credential_readonly` must read:
   `OK … suvarna_reader: no write path (…); default_transaction_read_only=on; …`.
   The check now evaluates, as the login itself:
   - table and column write privileges on every relation;
   - sequences;
   - database and schema CREATE;
   - memberships in both directions;
   - ownership;
   - elevated attributes;
   - reachable SECURITY DEFINER functions;
   - access to `auth`.

   It reports BLOCK on any write path, WARN if the login is anything other than `suvarna_reader`,
   and OK only when every check passes.
2. **The tracker.** Run `curl -s http://127.0.0.1:8765/api/health`. Both `detector_errors` and
   `metrics_errors` must be `[]`. The database detectors read `asset_registry` and
   `information_schema.columns`. The second only shows columns of tables the reader can access, so
   a detector aimed at a table outside the read set will report it as missing.
3. **The next deploy.** Its step "Inspect protected data-plane ownership state" must print `marked`.

## 5 · What the native must knowingly accept

**The dry run's lists are authoritative.** The items below come from the repository's migrations and
are an early warning only.

**Row-level security.** No policy is added: that is the native's decision.

- **`charts` — reader sees zero rows unless it sets a session value.** Its policies
  (`chart_owner_policy`, `chart_grant_policy`) match `current_setting('app.principal_id', true)`
  against `owner_id` and `chart_grants`. That is why `chart_grants` is in the read set. Two
  consequences:
  - To read a chart, a Suvarṇa session must `SET app.principal_id = '<principal>'`, as the app
    does.
  - Any login with SELECT on `charts` can do the same for any principal. This is how the app scopes
    access today; it is not something this bootstrap introduces.
- **`charts` — queries may error.** If the legacy policy `"charts: astrologer all"` (built on
  `auth.uid()` and `profiles`) still exists in production, every `charts` query by the reader will
  **fail**: the reader has no access to `auth`, and `profiles` is deny-listed. The dry-run section
  "applicable policies that reference objects suvarna_reader cannot use" shows whether this applies.
- **`chart_divisionals` — zero rows.** Its only policy is `"service role full access"`, for the role
  `service_role`, so the reader silently sees nothing. It is also a protected L1 table: adding a
  policy would change the data-plane gate's policy attestation too.
- **Other tables with RLS, if they are in the read set:** `predictions` (its policy reads
  `query_trace_steps`), the `planner_inquiry_*` / `planner_managed_prashna_jobs` tables (principal
  policies), and the legacy Supabase tables `chat_attachments`, `documents`, `message_feedback`,
  `messages`, `pyramid_layers` and `reports` (policies on `auth.uid()`).

**PII and sensitive content.**

- **`charts` holds birth data** (date, time, place). It is included because Suvarṇa needs chart ids.
- The dry run prints a name-based review list: tables in the read set with columns such as
  email, phone, birth, uid, token or address. They are not excluded automatically.
- **Flagged for a deny-list decision:** the legacy tables `messages`, `documents`, `reports`,
  `chat_attachments` and `message_feedback`, if the census role can read them. They hold user
  content and are not on the review's deny-list.

**The deny-list** (never granted; widening it means editing `DENY_PATTERNS` in the script):

- `profiles`, `access_requests`, `conversation_%`, `mcp_oauth_%`, `ai_provider_connections`,
  `mv_session_summary`, `query_baseline_stats`, and everything in schema `auth`;
- **also `mcp_api_keys`** — API-key material, the same class as `mcp_oauth_%`;
- automatically, any view that reads `auth` or a denied table.

These are SQL `LIKE` patterns, so `conversation_%` also matches `conversations`.

## 6 · Rollback

```bash
npx tsx scripts/suvarna-reader-bootstrap.ts --rollback            # dry run: proves it would work
npx tsx scripts/suvarna-reader-bootstrap.ts --rollback --apply
```

The rollback uses the same admin route. In one transaction, it:

- revokes every grant `suvarna_reader` holds, **each as its grantor** (a plain `REVOKE` by
  `postgres` cannot remove a grant an owner made);
- runs `DROP ROLE suvarna_reader`;
- proves the same handoff invariants and snapshots;
- on `--apply`, restores `~/.config/suvarna/pgenv.sh` from `pgenv.app-login.bak`.

The Secret Manager secret is left in place; disable its versions yourself if you want. After a
rollback the Monitor returns to BLOCK, which is correct: the app login has write grants.

The manual equivalent, shown only so the mechanism is clear:

```sql
BEGIN;
GRANT <each grantor postgres is not already a member of> TO postgres;
SET LOCAL ROLE <grantor>; REVOKE ALL ON TABLE <its tables> FROM suvarna_reader; RESET ROLE;   -- per grantor
SET LOCAL ROLE data_plane_schema_owner; REVOKE ALL ON SCHEMA public FROM suvarna_reader; RESET ROLE;
SET LOCAL ROLE nirmana_evidence_owner;  REVOKE ALL ON SCHEMA nirmana_evidence FROM suvarna_reader; RESET ROLE;
REVOKE ALL ON DATABASE amjis FROM suvarna_reader;
REVOKE <every grantor granted above> FROM postgres;   -- mandatory: the handoff checks forbid these edges
DROP ROLE suvarna_reader;
COMMIT;
```

Then restore the file: `cp -p ~/.config/suvarna/pgenv.app-login.bak ~/.config/suvarna/pgenv.sh`.
The gate amendment from §0 can stay: it admits `suvarna_reader` only when that role exists.
