# WS-0C Sub-A — Chat-Layer Triage (`messages` in `conversations.ts`) — CC Prompt

> **Paste this entire block into your Claude Code chat inside Google Antigravity IDE.**
> Brief: `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_WS0C_RESIDUAL_PURGE_v1_0.md`
> Branch: `feature/ws0c-residual-purge` (cut from tag `legacy-code-cluster-purge-complete`)
> Repo: `/Users/Dev/Vibe-Coding/Apps/Madhav`

---

You are Claude Code in Google Antigravity IDE. PR #206 (WS-0B) is merged + tagged. WS-0C residual-purge begins with Sub-A. **Sub-A is INVESTIGATION ONLY.** Do not delete, edit, or rename any file. The deliverable is one findings document at `/tmp/ws0c_sub_a_findings.md` that the native + Cowork use to decide Sub-A's disposition (delete / repoint / surgical fix) before authorizing Sub-B.

**The question Sub-A answers:** Of the 433 `messages` citations in `conversations.ts` (and any sibling files), which state are we in?
- (a) **DEAD** — `conversations.ts` is fully orphaned; live chat uses different files.
- (b) **ALIVE + FALLBACK** — `conversations.ts` is reached by live routes but has try/catch / empty-array / sentinel fallbacks that mask the missing table.
- (c) **SILENTLY BROKEN** — `conversations.ts` is reached by live routes and the `messages` queries throw at runtime, but the broken path isn't surfaced (maybe a side-effect logging path, maybe a feature nobody exercises).

The answer determines whether Sub-A's disposition is `git rm` (state a), `git rm with consumer cleanup` (state b), or `surgical edit to fix-forward / delete-the-feature` (state c).

## Step 0 — Branch + baseline

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch origin --tags
git checkout -b feature/ws0c-residual-purge legacy-code-cluster-purge-complete 2>/dev/null || git checkout feature/ws0c-residual-purge
git status

# Start Cloud SQL proxy (needed for live-path DB existence checks)
bash platform/scripts/start_db_proxy.sh &
PROXY_PID=$!
sleep 3
export PROD_DB_URL="postgresql://amjis_app@127.0.0.1:5433/amjis"
psql_prod() { psql "$PROD_DB_URL" -v ON_ERROR_STOP=1 "$@"; }
psql_prod -c "SELECT 1;" >/dev/null && echo "Proxy up" || { echo "Proxy fail"; exit 1; }
```

## Step 1 — Locate every file citing `messages` as a table

```bash
# Word-boundary SQL-context grep (strips substring false positives)
grep -rEn "\b(FROM|INTO|UPDATE|DELETE\s+FROM|JOIN)\s+messages\b" \
  --include='*.ts' --include='*.tsx' \
  --exclude-dir=node_modules --exclude-dir=.next \
  platform/src 2>/dev/null \
  | tee /tmp/ws0c_sub_a_sql_hits.txt

# Group by file
awk -F: '{print $1}' /tmp/ws0c_sub_a_sql_hits.txt | sort | uniq -c | sort -rn \
  | tee /tmp/ws0c_sub_a_files.txt
cat /tmp/ws0c_sub_a_files.txt
```

`conversations.ts` should dominate; surface any sibling file that also has SQL-context hits.

## Step 2 — Read `conversations.ts` end to end

Use the Read tool. Capture:
- **Exports** — every public function/class/const the file exposes. List each with its signature.
- **`messages`-touching exports** — the subset of exports that themselves run a `messages` SQL query (directly or via a private helper that runs one).
- **Existing error handling** — is there a try/catch, a `if (!table) return []` pattern, a feature flag short-circuit, a runtime config check? If yes, that's evidence for state (b).
- **Comments / dead-code markers** — `@deprecated`, `// TODO remove`, `// LEGACY` — evidence for state (a) or intent.

Output the export list as a markdown table to `/tmp/ws0c_sub_a_exports.md`.

## Step 3 — Reverse-import graph from `conversations.ts`

```bash
# Every file that imports anything from conversations.ts
CONV_PATH=$(find platform/src -name 'conversations.ts' -not -path '*/node_modules/*' | head -1)
echo "conversations.ts path: $CONV_PATH"

# Find importers via the actual import path (could be relative or aliased like @/lib/conversations)
grep -rEn "from ['\"][^'\"]*conversations['\"]" platform/src \
  --include='*.ts' --include='*.tsx' 2>/dev/null \
  | grep -v "$CONV_PATH" \
  | tee /tmp/ws0c_sub_a_importers.txt

# Group by importer file
awk -F: '{print $1}' /tmp/ws0c_sub_a_importers.txt | sort -u | tee /tmp/ws0c_sub_a_importer_files.txt
echo "Importers: $(wc -l < /tmp/ws0c_sub_a_importer_files.txt)"
```

For each importer file in `/tmp/ws0c_sub_a_importer_files.txt`:
- Is it under `app/api/*/route.ts` or `app/*/page.tsx`? → **LIVE-ROUTE / LIVE-PAGE** consumer.
- Is it itself in a dead cluster (e.g., still inside the now-orphaned `lib/build/` or `lib/aiops/` paths WS-0B did NOT delete)? → **DEAD-CONSUMER** — extends the delete blast radius.
- Is it in a barrel/index file? → trace one level up (its importers).

Build a tree: which routes/pages transitively reach `conversations.ts`. Capture to `/tmp/ws0c_sub_a_reach_tree.md`.

## Step 4 — Map which `messages`-touching export each LIVE-ROUTE consumer uses

For each LIVE-ROUTE consumer:
- Open the route file.
- Identify which exported function it calls from `conversations.ts`.
- Cross-reference Step 2: is that function one of the `messages`-touching exports?
  - **Yes** → this route's HTTP path DEPENDS on the dropped `messages` table.
  - **No** → this route only uses non-`messages` exports; `conversations.ts` could potentially be split (live + dead).

Append to `/tmp/ws0c_sub_a_reach_tree.md`.

## Step 5 — Live-path runtime check (curl each LIVE-ROUTE)

```bash
# Build + start the production server locally
cd platform
npm run build 2>&1 | tail -10 | tee /tmp/ws0c_sub_a_build.txt
# If the build fails on the known Turbopack symlink issue, fall back to dev:
# npm run dev &
npm run start &
SERVER_PID=$!
sleep 8

# Curl each LIVE-ROUTE that touches messages-dependent exports.
# Build the route list from Step 4's tree — only the routes where Step 4 said "depends on messages".
# Test with a minimal valid request (GET for read routes; POST with a stub body for write routes).
# Capture status codes + first 200 chars of response body.

# Example pattern — fill in real routes from Step 4:
declare -a ROUTES=(
  "/api/conversations"
  "/api/conversations/[id]/messages"
  # ... fill in from Step 4 ...
)

for r in "${ROUTES[@]}"; do
  REAL=$(echo "$r" | sed 's|\[id\]|test|')  # substitute a stub value for dynamic segments
  echo "--- $REAL ---"
  curl -s -o /tmp/ws0c_resp.txt -w "HTTP:%{http_code}\n" -m 10 "http://localhost:3000${REAL}"
  head -c 200 /tmp/ws0c_resp.txt
  echo
done | tee /tmp/ws0c_sub_a_curl.txt

kill $SERVER_PID
cd ..
```

**Interpretation:**
- HTTP 200 with valid data → the route works → state (b) "alive with fallback" is most likely. The fallback is masking the dropped table.
- HTTP 500 with `relation "messages" does not exist` → state (c) "silently broken" — route is live but errors.
- HTTP 401/403/404 → can't conclude; the route exists but auth/routing blocks the SQL path; needs deeper trace (read the route handler code directly).
- The build never reaches `npm run start` (Turbopack symlink blocker) → fall back to: read the route handler code and reason about reachability without execution.

## Step 6 — DB-level fallback check (does anything currently write to `messages`?)

`messages` is dropped; nothing can write to it. But check if any SURVIVING table in the DB has data with timestamps that suggest the chat layer is functioning via an alternate table:

```bash
psql_prod <<'EOF'
-- Is conversation_messages (the Brahma chat table) accumulating data?
SELECT 'conversation_messages' AS tbl,
       count(*) AS rows,
       max(created_at) AS last_write
FROM conversation_messages;

-- Compare to other shell tables
SELECT 'conversations' AS tbl,
       count(*) AS rows,
       max(created_at) AS last_write
FROM conversations;
EOF
```

If `conversation_messages` has recent writes → the live chat IS writing somewhere; `conversations.ts`'s `messages` queries are either dead paths or read-only-with-fallback. Evidence for state (a) or (b).
If `conversation_messages` is empty / stale → the live chat may itself be broken; deeper concern.

## Step 7 — Write the findings document

Compose `/tmp/ws0c_sub_a_findings.md` with this structure (CC writes via Write tool):

```markdown
# WS-0C Sub-A — Chat-Layer Triage Findings

## Verdict

State: **(a) DEAD / (b) ALIVE+FALLBACK / (c) SILENTLY BROKEN** — pick one based on Steps 5+6 evidence.

## Evidence

### conversations.ts surface
- Path: `<actual path>`
- Exports: `<list>`
- `messages`-touching exports: `<list>`
- Existing fallback handling: `<yes/no — describe>`

### Importer reachability
- Total importer files: `<N>`
- LIVE-ROUTE consumers: `<list with route paths>`
- DEAD-CONSUMER importers: `<list>`

### Live-path curl results
| Route | HTTP | Body excerpt | Interpretation |
|---|---|---|---|
| ... | ... | ... | ... |

### DB-level signals
- `conversation_messages` rows / last_write: ...
- `conversations` rows / last_write: ...

## Recommended disposition

Based on the verdict:
- (a) DEAD → `git rm conversations.ts + tests + DEAD-CONSUMER importers` in Sub-A-EXEC commit.
- (b) ALIVE+FALLBACK → keep the fallback path, remove only the dead `messages`-touching helpers; reduces hits but preserves the live surface. Alternatively, if the fallback always returns empty, the whole `messages`-touching code is effectively no-op — delete + remove the fallback wrappers from consumers.
- (c) SILENTLY BROKEN → choose: (i) fix forward by re-pointing `messages` → `conversation_messages`, OR (ii) delete the broken feature entirely and append to `BRAHMA_DEFERRED_FEATURES.md`. Decision needed from native.

## Open questions for native (if any)

- ...
```

## Step 8 — Report back

Output the findings doc to the native by:
1. Echoing the verdict + recommended-disposition section into the chat.
2. Path: `/tmp/ws0c_sub_a_findings.md` (also `cat` the full doc to chat for easy native review).

**STOP.** Do not commit, do not git rm, do not edit any file under `platform/src`. Sub-A is investigation-only.

```bash
kill $PROXY_PID 2>/dev/null
```

---

## Hard stops (halt and report — do not attempt fix)

- Step 1 SQL-context grep finds `messages` citations OUTSIDE `conversations.ts` and clear siblings — fold them into the findings; do not investigate beyond the chat layer in Sub-A.
- Step 3 reverse-import graph reveals `conversations.ts` is imported by `00_ARCHITECTURE/**` or any governance/test tooling — report; that's a deeper coupling than Sub-A's chat-layer focus.
- Step 5 build fails AND `npm run dev` also fails — report; reason about reachability from code alone in Step 4's tree and note the limitation in the findings.
- Step 6 reveals `conversation_messages` is empty / has zero recent writes — that's a separate "is chat actually working in prod" concern; surface in the findings as an open question for native.

Begin with Step 0. The deliverable is one markdown findings doc.
