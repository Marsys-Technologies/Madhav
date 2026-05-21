# MCP — Claude Code ACTIVATION Operator Prompt v1.0

Paste this into a **fresh Claude Code session in Antigravity IDE**, pointed at `/Users/Dev/Vibe-Coding/Apps/Madhav`, AFTER `MCP_POST_MERGE_PROMPT_v1_0.md` has been run (governance close-out done, `amjis-mcp` deployed at Cloud Run, smoke check passed).

This prompt finishes the remaining 4 activation steps:

1. **Apply migrations 070 + 071 to prod Supabase** (automated — needs `MARSYS_PROD_DB_URL`)
2. **Mint an MCP API key via direct DB insert** (automated — bypasses the admin UI; same bcrypt the auth lib uses)
3. **Print Claude Chat custom-integration registration instructions** (browser-only, but with all values filled in)
4. **Print Cowork remote-MCP registration instructions** (browser-only)

Launch Claude Code with:

```
cd /Users/Dev/Vibe-Coding/Apps/Madhav
claude --dangerously-skip-permissions
```

Set required env vars before launching (or in the same shell):

```bash
export MARSYS_PROD_DB_URL='postgresql://...'        # Supabase connection string
export AMJIS_MCP_URL='https://amjis-mcp-938361928218.asia-south1.run.app'
export KEY_LABEL='claude-chat-personal'             # any human label you want
# Optional — if you don't set this, the prompt looks up profiles.id WHERE role='astrologer'
# export NATIVE_UID='xl2wYZRPwsVgPSAgtn9XJ80Xkub2'  # native's Firebase UID
```

> **Note on prior version (v0):** an earlier draft of this prompt had three bugs that would have caused immediate failure: wrong hash algorithm (bcryptjs, but `auth.ts` uses PBKDF2-SHA256 100k iterations), wrong key format (used `_` separator + base64url, but `splitKey()` regex requires `mcp_<env>_<40 alphanumeric>` with no separator), and a non-existent `profiles.email` column (profiles has only `id, role, name, created_at`; email is in Firebase Auth). This version (v1.0) fixes all three by reading the algorithm + key format directly from the deployed `platform/src/lib/mcp/auth.ts` and using `role='astrologer'` for the UID lookup.

---

## What to paste

```
You are the post-deploy activation operator for the MARSYS-JIS MCP server.
The Cloud Run service amjis-mcp is deployed and /health responds OK. Your
job is to apply migrations to prod, mint the native's first API key
directly via DB insert (bypassing the admin UI), and print the two
browser-only registration steps with all values pre-filled.

Worktree: /Users/Dev/Vibe-Coding/Apps/Madhav (the main worktree)
Mode: --dangerously-skip-permissions
Halt policy: STOP on any non-recoverable error; report what worked.

Echo each step header. Echo a clear PASS / FAIL line per step.

────────────────────────────────────────────────────────────────────────
STEP 0 — Verify preconditions
────────────────────────────────────────────────────────────────────────

Verify these env vars are set:
  - MARSYS_PROD_DB_URL  (Supabase connection string)
  - AMJIS_MCP_URL       (e.g. https://amjis-mcp-938361928218.asia-south1.run.app)
  - KEY_LABEL           (human label for the key)
  - NATIVE_UID          (OPTIONAL — Firebase UID; if absent, looked up from profiles)

If MARSYS_PROD_DB_URL or AMJIS_MCP_URL or KEY_LABEL is missing: HALT and
print which env vars must be exported.

Verify `psql` and `node` are on PATH.

cd /Users/Dev/Vibe-Coding/Apps/Madhav
git pull origin main --ff-only

Verify migration files exist:
  test -f platform/supabase/migrations/070_mcp_api_keys.sql
  test -f platform/supabase/migrations/071_mcp_predictions_disagreements.sql

(Note: the actual 071 file is 071_mcp_predictions_disagreements.sql, a
combined file — not 071_mcp_predictions.sql as the brief originally
specified. Use the on-disk filename.)

CRITICAL — re-read these two files FIRST before generating any key.
They are the source of truth for the key format and hashing algorithm:
  - platform/src/lib/mcp/auth.ts          (PBKDF2 hashing, splitKey regex, generateMcpKey)
  - platform/supabase/migrations/070_mcp_api_keys.sql  (table schema)

If the hashing algorithm or key format in auth.ts has diverged from what
the Node helper below uses, STOP and report — the helper must mirror
auth.ts exactly. The deployed validateMcpKey() will reject keys that
don't conform.

────────────────────────────────────────────────────────────────────────
STEP 1 — Apply migrations 070 + 071 to prod Supabase
────────────────────────────────────────────────────────────────────────

psql "$MARSYS_PROD_DB_URL" \
  -v ON_ERROR_STOP=1 \
  -f platform/supabase/migrations/070_mcp_api_keys.sql

psql "$MARSYS_PROD_DB_URL" \
  -v ON_ERROR_STOP=1 \
  -f platform/supabase/migrations/071_mcp_predictions_disagreements.sql

Verify the tables exist:
  psql "$MARSYS_PROD_DB_URL" -c "\d mcp_api_keys"
  psql "$MARSYS_PROD_DB_URL" -c "\d mcp_predictions"
  psql "$MARSYS_PROD_DB_URL" -c "\d mcp_disagreements"

If any verification fails: HALT and print the psql error.

────────────────────────────────────────────────────────────────────────
STEP 2 — Resolve the native's user_uid
────────────────────────────────────────────────────────────────────────

The profiles table has no email column (it has only id, role, name,
created_at; email lives in Firebase Auth, not Postgres). The native's
Firebase UID is either provided as $NATIVE_UID or looked up by role.

If $NATIVE_UID is set, use it directly:
  USER_UID="$NATIVE_UID"

Otherwise look up the astrologer profile (seeded in migration 006):
  USER_UID=$(psql "$MARSYS_PROD_DB_URL" -At -c \
    "SELECT id FROM profiles WHERE role = 'astrologer' LIMIT 1;")

If the result is empty: HALT and report
"no astrologer profile found; set NATIVE_UID manually or seed the
astrologer profile per migration 006".

Echo USER_UID (it's a Firebase UID, public-safe).

────────────────────────────────────────────────────────────────────────
STEP 3 — Mint the API key via direct DB insert
────────────────────────────────────────────────────────────────────────

Generate, hash, and insert the key using a small Node helper. The
algorithm and key format MUST match platform/src/lib/mcp/auth.ts
exactly, otherwise validateMcpKey() will reject every request.

Algorithm (from auth.ts):
  - Hashing: PBKDF2-SHA256, 100,000 iterations, 16-byte salt,
    32-byte output. Stored as "<salt_hex>:<hash_hex>".
  - Key format: mcp_<env>_<40 ALPHANUMERIC chars> (no separator
    between env and tail, alphanumeric only — A-Za-z0-9).
  - key_id = "mcp_<env>_<first 8 chars of random40>" (stored in DB).
  - tail   = remaining 32 chars of random40 (hashed, never stored raw).

Re-read platform/src/lib/mcp/auth.ts BEFORE proceeding. If the algorithm
or format below has drifted from auth.ts, STOP and report.

Use ONLY Node built-ins (no bcrypt, no bcryptjs, no external crypto
deps — `pg` is the only npm install needed).

Create /tmp/mcp_mint/mint.mjs with EXACTLY this content:

  import { pbkdf2Sync, randomBytes } from 'crypto';
  import pg from 'pg';

  // Mirror of platform/src/lib/mcp/auth.ts constants
  const PBKDF2_ITERATIONS = 100_000;
  const PBKDF2_KEYLEN     = 32;
  const PBKDF2_DIGEST     = 'sha256';
  const SALT_BYTES        = 16;
  const ALPHANUMERIC = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';

  function hashKeyTail(tail) {
    const salt = randomBytes(SALT_BYTES);
    const hash = pbkdf2Sync(tail, salt, PBKDF2_ITERATIONS, PBKDF2_KEYLEN, PBKDF2_DIGEST);
    return `${salt.toString('hex')}:${hash.toString('hex')}`;
  }

  function generateMcpKey(env) {
    // 40 cryptographically random alphanumeric chars
    const randomPart = Array.from(
      randomBytes(40),
      (byte) => ALPHANUMERIC[byte % ALPHANUMERIC.length]
    ).join('');
    const prefix = randomPart.slice(0, 8);
    const tail   = randomPart.slice(8);                 // 32 chars
    const key_id = `mcp_${env}_${prefix}`;              // matches splitKey() regex
    const full_key = `mcp_${env}_${randomPart}`;        // mcp_<env>_<40 alphanum>
    const key_hash = hashKeyTail(tail);
    return { key_id, full_key, key_hash };
  }

  const USER_UID  = process.env.USER_UID;
  const DB_URL    = process.env.MARSYS_PROD_DB_URL;
  const KEY_LABEL = process.env.KEY_LABEL || 'claude-chat-personal';
  const ENV       = process.env.MCP_KEY_ENV || 'prod';

  if (!USER_UID || !DB_URL) {
    console.error('HALT: USER_UID and MARSYS_PROD_DB_URL must be set');
    process.exit(1);
  }

  const { key_id, full_key, key_hash } = generateMcpKey(ENV);

  // Sanity-check the generated key matches the auth.ts splitKey regex
  const re = /^(mcp_[a-z]+_[A-Za-z0-9]{8})([A-Za-z0-9]{32})$/;
  if (!re.test(full_key)) {
    console.error(`HALT: generated key "${full_key}" does not match auth.ts regex`);
    process.exit(3);
  }

  const client = new pg.Client({ connectionString: DB_URL });
  await client.connect();

  // Duplicate-label guard for the same user+label that is not revoked.
  const dup = await client.query(
    `SELECT key_id FROM mcp_api_keys
      WHERE user_uid = $1 AND label = $2 AND revoked_at IS NULL`,
    [USER_UID, KEY_LABEL]
  );
  if (dup.rows.length) {
    console.error(`HALT: active key with label "${KEY_LABEL}" already exists for this user (key_id=${dup.rows[0].key_id}). Use a different KEY_LABEL or revoke the existing key first.`);
    await client.end();
    process.exit(2);
  }

  await client.query(
    `INSERT INTO mcp_api_keys (key_id, key_hash, user_uid, audience_tier, label)
     VALUES ($1, $2, $3, 'super_admin', $4)`,
    [key_id, key_hash, USER_UID, KEY_LABEL]
  );
  await client.end();

  console.log('═══════════════════════════════════════════════════════════');
  console.log(' MCP API KEY — COPY THIS NOW. IT WILL NEVER BE SHOWN AGAIN.');
  console.log('═══════════════════════════════════════════════════════════');
  console.log(`  ${full_key}`);
  console.log('═══════════════════════════════════════════════════════════');
  console.log(`  key_id:        ${key_id}`);
  console.log(`  user_uid:      ${USER_UID}`);
  console.log(`  audience_tier: super_admin`);
  console.log(`  label:         ${KEY_LABEL}`);
  console.log('═══════════════════════════════════════════════════════════');

Install ONLY pg (no bcryptjs needed):

  mkdir -p /tmp/mcp_mint && cd /tmp/mcp_mint
  npm init -y >/dev/null
  npm pkg set type=module >/dev/null
  npm install pg >/dev/null 2>&1

Then create mint.mjs from the content above. Run with all required env
vars on a single command line:

  USER_UID="$USER_UID" \
  MARSYS_PROD_DB_URL="$MARSYS_PROD_DB_URL" \
  KEY_LABEL="$KEY_LABEL" \
  MCP_KEY_ENV=prod \
  node mint.mjs

Capture the full key from stdout. Store it in shell variable MCP_API_KEY
for Step 4. Do NOT log the key to any file.

Exit codes:
  0 = success, key minted, full_key printed to stdout
  1 = missing required env (USER_UID or MARSYS_PROD_DB_URL)
  2 = duplicate label for this user — pick a different KEY_LABEL
  3 = generated key failed format self-check (algorithm drift) — bug

If exit code is 2 or 3: STOP. Do not proceed to Step 4.

cd /Users/Dev/Vibe-Coding/Apps/Madhav

────────────────────────────────────────────────────────────────────────
STEP 4 — Live smoke test against amjis-mcp via curl
────────────────────────────────────────────────────────────────────────

Confirm the key works end-to-end before instructing the native to paste
it into Claude Chat. The MCP server's tool-call endpoint depends on the
@modelcontextprotocol/sdk shape; for a quick liveness probe use the
health endpoint (no auth) AND a Bearer-authenticated list-tools call.

# Health (no auth — already verified post-deploy, but quick re-check)
curl -fsS "$AMJIS_MCP_URL/health"

# Liveness with auth — depends on MCP server's endpoint shape. Try
# common probes; report the first one that responds with HTTP 200.
# The MCP server may expose /mcp or /sse or /. Adjust based on what
# platform-mcp/src/server.ts actually serves.
for path in /mcp /sse /; do
  status=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $MCP_API_KEY" \
    "$AMJIS_MCP_URL$path")
  echo "GET $AMJIS_MCP_URL$path → $status"
done

If none returns 200 OR 400 (400 is acceptable — means the route exists
but the body shape is wrong, which is fine for a probe): proceed
anyway with a WARNING that smoke could not confirm auth-path liveness;
the next step (browser registration) is the canonical smoke.

────────────────────────────────────────────────────────────────────────
STEP 5 — Print pre-filled browser instructions
────────────────────────────────────────────────────────────────────────

Echo:

═══════════════════════════════════════════════════════════════════════
 MCP ACTIVATION — AUTOMATED STEPS DONE
═══════════════════════════════════════════════════════════════════════

 Migrations 070 + 071: APPLIED to prod Supabase
   Tables verified: mcp_api_keys, mcp_predictions, mcp_disagreements

 API key minted:
   Label:         <KEY_LABEL>
   Audience tier: super_admin
   user_uid:      <USER_UID>
   key_id:        <prefix>
   Full key:      <printed once in Step 3 stdout above — already copied?>

═══════════════════════════════════════════════════════════════════════
 NEXT — TWO BROWSER STEPS (each ~30 seconds)
═══════════════════════════════════════════════════════════════════════

 STEP A — Register in Claude Chat

   1. Open: https://claude.ai/settings/connectors
   2. Click "Add custom integration"
   3. Fill in:
        Name:           MARSYS-JIS
        URL:            <AMJIS_MCP_URL>
        Authorization:  Bearer <paste the full key from Step 3>
   4. Save.
   5. Open any Claude chat. Tools picker should show ask_madhav,
      plan_query, execute_plan, query_chart_facts, query_signals,
      query_dasha_periods, query_panchanga, query_ephemeris,
      query_transit_event, lel_query, vector_search, get_cgm_subgraph,
      cross_school_lookup, read_asset, get_trace, list_recent_queries,
      log_prediction, record_outcome, flag_disagreement.
      Plus two resources: marsys://chart-overview, marsys://house-rules.
   6. Smoke: ask Claude "Use ask_madhav to summarize my Atmakaraka."
      Expected: answer with inline citations, a trace_id field, and a
      synthesis_audit block showing holistic_read_passed: true.

 STEP B — (Optional) Register in Cowork

   1. Open Cowork → Settings → Connectors → Add remote MCP
   2. Fill in:
        URL:            <AMJIS_MCP_URL>
        Authorization:  Bearer <same key>
   3. Save.
   4. Open any Cowork chat. Same tool list should appear.

═══════════════════════════════════════════════════════════════════════
 IF SOMETHING GOES WRONG
═══════════════════════════════════════════════════════════════════════

 - Tool list doesn't appear in Claude Chat:
     Check Cloud Run logs:
       gcloud run services logs read amjis-mcp --region asia-south1 --limit 50

 - "401 Unauthorized" on first ask_madhav call:
     Confirm the key in claude.ai matches what was printed in Step 3.
     Re-mint if uncertain (delete the existing integration first):
       Re-run this prompt with a different KEY_LABEL.

 - synthesis_audit.holistic_read_passed is false:
     B.11 floor was bypassed. Check /admin/observatory for the trace.
     Possible cause: planner selected "factual" mode for what should be
     a holistic query. Open a Cowork session to investigate.

 - Migration error in Step 1:
     Likely cause: profile schema drift OR migration ordering conflict
     with a parallel workstream. Read the psql error carefully; resolve
     by hand. Migrations 070 and 071 are idempotent (CREATE TABLE IF NOT
     EXISTS), so re-running this prompt after fixing is safe.

═══════════════════════════════════════════════════════════════════════
 Workstream activation status: LIVE pending Steps A + B.
═══════════════════════════════════════════════════════════════════════

Then terminate. Do not start any other work.
```

---

## What this prompt deliberately does NOT do

- **Does not log the API key to any file.** The key appears once on stdout. You copy it from your terminal scrollback and paste into Claude Chat. If you lose it, re-run with a different `KEY_LABEL` to mint a fresh one (the prior key remains valid until you revoke it via `/admin/mcp/keys` later).

- **Does not store credentials.** `MARSYS_PROD_DB_URL` stays in your shell env; no persistence.

- **Does not register in claude.ai automatically.** No public API for that. The two browser steps are unavoidable.

- **Does not delete the temp Node helper.** It lives at `/tmp/mcp_mint/` until your OS cleans `/tmp`. Safe to `rm -rf` after run if you want.

## Recovery scenarios

- **Key was lost / never copied:** re-run with `KEY_LABEL='claude-chat-personal-2'` (or any new label). The duplicate-label guard prevents silent collisions; pick a new label and you'll get a fresh key.

- **Migration partially applied:** both migrations use `CREATE TABLE IF NOT EXISTS` semantics; re-running is safe and skips already-applied DDL.

- **gcloud not authenticated for log inspection:** `gcloud auth login`; project should auto-resolve from `~/.config/gcloud/active_config`.
