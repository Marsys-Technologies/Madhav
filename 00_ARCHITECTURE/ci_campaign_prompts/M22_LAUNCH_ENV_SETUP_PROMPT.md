# Claude Code — set up `DATABASE_URL` for the M-22 overnight run (Madhav)

Small setup task, run in the **same Claude Code session** that will then launch the overnight swarm
run — the env var you set here lives only in this session's shell and must not be re-set in a
different one. Do the steps in order; **STOP at the first failure** with a plain diagnosis rather
than working around it.

**Credential rule, absolute:** never print, echo, log, `cat`, or interpolate-into-output the value
of `DATABASE_URL` or the secret. Pull it directly from Secret Manager into the environment variable
in one step; every check below reports only booleans, counts, scheme, or database name — never the
value. If a command would display the secret, don't run it.

## Step 1 — Context
- `gcloud config get-value project` → expect `madhav-astrology` (or report what it is; if wrong,
  `gcloud config set project madhav-astrology`). Confirm `gcloud auth list` shows an active account.
- Confirm the secret exists: `gcloud secrets describe amjis-pipeline-db-url` succeeds (names/metadata
  only — do NOT `versions access` yet in a way that prints).

## Step 2 — Start the Cloud SQL Auth Proxy (background, must stay alive for the whole run)
- Start it: `cloud-sql-proxy madhav-astrology:asia-south1:amjis-postgres &` (or the repo's documented
  invocation from `platform/scripts/audit/tap/README.md` if it differs — read it, prefer it).
- Wait until it is actually listening (poll for the local port, e.g. `127.0.0.1:5432`, up to ~15s).
  If it never comes up, STOP: report that the proxy failed to start and hand back the manual path.

## Step 3 — Export the value without exposing it
Pull the full URL straight from Secret Manager into the env var in a single expansion, no echo:
```
export DATABASE_URL="$(gcloud secrets versions access latest --secret=amjis-pipeline-db-url)"
```
Then confirm presence only: `[ -n "$DATABASE_URL" ] && echo SET || echo UNSET`.

## Step 4 — Verify it reaches the RIGHT database (read-only, value never shown)
Run, reporting only the printed fields:
```
python3 -c "import os,psycopg2; c=psycopg2.connect(os.environ['DATABASE_URL']); cur=c.cursor(); \
cur.execute('select current_database(), inet_server_addr()'); print(cur.fetchone()); \
cur.execute(\"select verification_pass_status, count(*) from chart_facts where verification_pass_status in ('PASS','single_pass') group by 1\"); print(cur.fetchall())"
```
Expected: `current_database()` = `amjis`; `inet_server_addr()` = `None` (proxy socket / loopback);
and `PASS`/`single_pass` counts present (order ~5,428 / ~32,614 — they confirm the real, undrained
estate; exact numbers may have drifted, report them). **If `current_database()` is not `amjis`, or
the counts are wildly off, STOP** — the URL may point at a dev/wrong database and the overnight run
must not touch it.

If the Secret Manager URL does **not** connect (e.g. it encodes a host not reachable locally rather
than the proxy socket), do NOT rewrite the password-bearing URL yourself — STOP and hand back the
manual method:
```
export DATABASE_URL="postgresql://<user>:<password>@127.0.0.1:5432/amjis"   # value from Secret Manager, set by Abhisek
```

## Step 5 — Report
Five lines: project OK · proxy listening · DATABASE_URL SET · connects to `amjis` via proxy (with the
count evidence) · **GO / NO-GO**. If GO, end with exactly:
> Environment ready in THIS session. Paste the swarm prompt (`M22_SWARM_OVERNIGHT_PROMPT.md`) into
> this same Claude Code session now; `DATABASE_URL` will not carry into any other shell. Keep the
> proxy process alive until the run's morning report is produced.
