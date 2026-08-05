# Claude Code task — verify `DATABASE_URL` is ready for the overnight run (Madhav)

Small pre-flight task. **Credential rule, absolute:** never print, echo, log, or write the value of
`DATABASE_URL` (or any credential) anywhere — not in output, not in a file, not in a ledger. You may
test its *presence* and *behaviour* only. If a command would display it, don't run that command.

## Step 1 — Presence, without exposure
- `[ -n "$DATABASE_URL" ] && echo SET || echo UNSET` — report only SET/UNSET.
- If SET, report shape only, never content: does it parse as a postgres URL
  (`python3 -c "from urllib.parse import urlparse; import os; u=urlparse(os.environ['DATABASE_URL']); print(u.scheme, 'host_present' if u.hostname else 'no_host')"`)
  — prints scheme and a boolean, nothing else.

## Step 2 — Connectivity + right database (read-only)
If SET, verify it reaches the **correct** estate, not just *a* database:
1. `SELECT 1` succeeds.
2. `chart_facts`, `chart_dashas`, `chart_divisionals` exist and `SELECT count(*) FROM chart_facts`
   returns a plausible number (~1.5M+ rows total estate; report the count — counts are fine, they
   are not credentials).
3. Sanity-match against known ground truth: `verification_pass_status` values present should match
   the last census (e.g. `PASS` ≈ 5,428 in chart_facts if the drain hasn't run). If counts are wildly
   different, say so — it may be pointing at a dev/wrong database, which is a HALT-quality finding:
   the overnight run must not backfill the wrong estate.
4. Confirm the connection is to the production instance the repo expects (the deploy pipeline
   proxies to `madhav-astrology:asia-south1:amjis-postgres` — check server identity via
   `SELECT current_database(), inet_server_addr()` or the proxy socket path; report what you can
   without exposing credentials).

## Step 3 — If UNSET: locate the sanctioned pattern, hand over the setup
Do NOT construct or guess a value. Instead:
1. Find how this repo already connects locally/CI: read `platform/scripts/audit/tap/README.md`
   (documents the Cloud SQL Auth Proxy invocation) and `deploy.yml`'s proxy step
   (`cloud-sql-proxy` → `madhav-astrology:asia-south1:amjis-postgres`).
2. Check whether the value exists somewhere Abhisek can pull it from without typing it: gcloud
   Secret Manager (`gcloud secrets list` — names only), or an existing local proxy setup.
3. Hand Abhisek the exact commands with a `<PLACEHOLDER>` where the value goes — e.g. start the
   proxy, then `export DATABASE_URL=<value-from-secret-manager>` — and state clearly that he runs
   the export in the same shell/environment that will launch the overnight run, since env vars
   don't cross shells.

## Step 4 — Hygiene check
- Confirm the value is not committed anywhere: `git grep -I "postgresql://" origin/main -- '*.py' '*.ts' '*.yml' '*.md' '*.env*' '*.json'`
  (matches are findings; report file:line only, never the matched content beyond the scheme).
- Confirm no `.env` file in the worktree would be swept into a commit (check `.gitignore` covers it).

## Deliverable
Five lines, no more: SET/UNSET · connects yes/no · right database yes/no (with the count evidence) ·
any hygiene findings · **GO / NO-GO for tonight's run**, and if NO-GO, the exact placeholder command
Abhisek must run in the launch shell.
