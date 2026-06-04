# WS-0C Sub-A-EXEC — Chat-Layer Fix-Forward — CC Prompt

> **Paste this entire block into your Claude Code chat inside Google Antigravity IDE.**
> Brief: `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_WS0C_RESIDUAL_PURGE_v1_0.md`
> Branch: `feature/ws0c-residual-purge` (same branch Sub-A ran on; cut from `legacy-code-cluster-purge-complete`)
> Repo: `/Users/Dev/Vibe-Coding/Apps/Madhav`
> Predecessor: Sub-A findings doc `/tmp/ws0c_sub_a_findings.md` (verdict: state c, silently broken)

---

You are Claude Code in Google Antigravity IDE. Sub-A's investigation confirmed `conversations.ts` has 2 dead exports (`loadConversationMessages`, `replaceConversationMessages`) querying the dropped `messages` table, with 6 consumer files still on the V1 surface — a Chat V2 cutover residual. **Native dispositions resolved:**

1. **Build chat = ephemeral.** Don't persist build-chat messages. `api/chat/build/route.ts` → surgical remove the `replaceConversationMessages` call only; do not re-point to V2.
2. **V1 fallback in `[id]/messages` route = delete.** Zero rows in both tables; the fallback is dead defensive code from a migration window that never accumulated data.
3. **Continue route = conditional.** Grep for UI callers first. Has callers → fix-forward to V2. Zero callers → delete the route file.

This paste produces **one commit** on the WS-0C branch: surgical removal of the 2 dead exports from `conversations.ts`, plus 5 fix-forward consumer re-points (or 4 if Step 2's grep is empty), plus 1 surgical removal (build route), plus 1 V1-fallback deletion.

## Step 0 — Branch + proxy

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git checkout feature/ws0c-residual-purge
git status
git log --oneline -3

# Start proxy for the AC curl smoke + DB write probe later
bash platform/scripts/start_db_proxy.sh &
PROXY_PID=$!
sleep 3
export PROD_DB_URL="postgresql://amjis_app@127.0.0.1:5433/amjis"
psql_prod() { psql "$PROD_DB_URL" -v ON_ERROR_STOP=1 "$@"; }
psql_prod -c "SELECT 1" >/dev/null && echo "Proxy up" || { echo "Proxy fail"; exit 1; }
```

## Step 1 — V2 API discovery (READ first; understand before editing)

```bash
# Find the V2 writer module the fix-forwards target
find platform/src -name 'conversation_writer.ts' -not -path '*/node_modules/*'

# Find the V2 loader (might be in the same file or a sibling)
grep -rEln "loadConversationMessagesV2|writeConversationMessages|conversation_messages" platform/src/lib \
  --include='*.ts' 2>/dev/null | head -20
```

Read the V2 writer module(s) fully. Capture the signatures CC needs to swap V1 calls for V2 calls — write them to `/tmp/ws0c_sub_a_exec_v2_api.md`:

```
loadConversationMessagesV2(conversationId, opts?) → Promise<Message[]>
writeConversationMessages(conversationId, messages, opts?) → Promise<void>
[any other V2 functions the 6 consumers may need]
```

Note any differences in argument shapes, return types, or pagination behavior vs V1 — the fix-forward edits must respect those.

## Step 2 — Continue-route disposition (grep decides)

```bash
# Does any UI file call /api/chat/consult/continue?
grep -rEn "/api/chat/consult/continue|chat/consult/continue|api/chat/consult/continue" platform/src \
  --include='*.ts' --include='*.tsx' 2>/dev/null \
  | grep -v "^platform/src/app/api/chat/consult/continue/" \
  | tee /tmp/ws0c_sub_a_exec_continue_callers.txt

CONTINUE_CALLERS=$(wc -l < /tmp/ws0c_sub_a_exec_continue_callers.txt)
echo "Continue-route UI callers: $CONTINUE_CALLERS"

# Also check the R7 truncation-Continue button (per CLAUDE.md §E R7 brief)
grep -rEn "Continue|continueConversation|truncation" platform/src/lib/components platform/src/app \
  --include='*.tsx' --include='*.ts' 2>/dev/null \
  | grep -iE "continue|truncat" \
  | head -20
```

**If `CONTINUE_CALLERS > 0`:** Step 4 = fix-forward (re-point to V2).
**If `CONTINUE_CALLERS == 0`:** Step 4 = `git rm` the continue route + its directory. Note the deletion in the commit message.

Record the decision in `/tmp/ws0c_sub_a_exec_disposition.md`.

## Step 3 — Edit `api/chat/build/route.ts` (surgical remove `replaceConversationMessages`)

Native call: ephemeral build chat. The build route still streams responses to the user; it just doesn't persist messages.

```bash
ROUTE=platform/src/app/api/chat/build/route.ts
grep -n "replaceConversationMessages\|loadConversationMessages\|from.*conversations" "$ROUTE"
```

Use the Edit tool. Remove:
- The import line for `replaceConversationMessages` (and `loadConversationMessages` if also imported but unused).
- The `replaceConversationMessages(...)` call (likely in a try/catch or post-stream handler).
- Any now-unused variables that only fed the call.

**Do NOT** remove anything else from the build route — only the persistence side-effect.

After the edit, search the file again to confirm zero residual references:
```bash
grep -nE "replaceConversationMessages|loadConversationMessages" "$ROUTE"
# Expected: empty
```

## Step 4 — `api/chat/consult/continue/route.ts` (conditional)

**Path A — `CONTINUE_CALLERS > 0` (fix-forward):**

Edit `platform/src/app/api/chat/consult/continue/route.ts`:
- Swap `loadConversationMessages(conversationId)` → `loadConversationMessagesV2(conversationId)` per the V2 API doc from Step 1.
- Update the import line accordingly.
- Adjust the return-shape handling if V2's signature differs.

**Path B — `CONTINUE_CALLERS == 0` (delete):**

```bash
git rm platform/src/app/api/chat/consult/continue/route.ts
# If the directory is now empty
if [ -d platform/src/app/api/chat/consult/continue ] \
   && [ -z "$(find platform/src/app/api/chat/consult/continue -type f)" ]; then
  rmdir platform/src/app/api/chat/consult/continue
fi
```

## Step 5 — `api/conversations/[id]/messages/route.ts` (fix-forward + delete V1 fallback)

Edit the route:
- Swap V1 `loadConversationMessages` call → V2 `loadConversationMessagesV2`.
- **Delete the V1 fallback block entirely.** The pattern probably looks like a try/catch where V1 is tried first, then V2 on failure — remove the V1 attempt and the catch wrapper; call V2 directly.
- Verify no lingering reference to the dropped `messages` table or V1 loader after the edit.

## Step 6 — `api/conversations/[id]/export/route.ts` (fix-forward)

Edit:
- Swap V1 → V2 for the message load.
- Adjust any shape differences in the export payload.

## Step 7 — `app/share/[slug]/page.tsx` (fix-forward)

Edit:
- Swap V1 → V2.
- Ensure the share page server component still renders properly with V2's return shape.

## Step 8 — `app/clients/[id]/consult/[conversationId]/page.tsx` (fix-forward — primary chat restore page)

This is the highest user-impact edit. The page restores a consult conversation when the user navigates back to it.

Edit:
- Swap V1 → V2.
- The page likely passes the loaded messages into `ConsumeChatV2` as initial messages — verify the prop shape lines up.
- If V2 returns paginated results vs V1's full list, handle pagination explicitly (or load all pages on first render).

## Step 9 — Remove the 2 dead exports from `conversations.ts`

Now that all 6 consumers (5 if continue deleted) no longer import V1, delete the dead functions.

```bash
CONV=$(find platform/src -name 'conversations.ts' -not -path '*/node_modules/*' | head -1)
echo "conversations.ts: $CONV"
```

Use the Edit tool. Delete:
- The entire `loadConversationMessages` function.
- The entire `replaceConversationMessages` function.
- Any private helpers ONLY used by those two (grep for each helper to confirm no other consumer).
- The export declarations.

Keep the 6 safe exports + their helpers untouched.

```bash
# Verify the dead exports are gone
grep -nE "function (loadConversationMessages|replaceConversationMessages)|export.*loadConversationMessages|export.*replaceConversationMessages" "$CONV"
# Expected: empty

# Verify no helper imports were broken
cd platform && npm run typecheck 2>&1 | grep -E "error TS|Found [0-9]+ error" | head -20 && cd ..
```

## Step 10 — Final reverse-citation gate

After all edits, confirm zero residual importers of the now-gone V1 functions:

```bash
# No file should import loadConversationMessages or replaceConversationMessages
grep -rEn "loadConversationMessages\b|replaceConversationMessages\b" platform/src \
  --include='*.ts' --include='*.tsx' 2>/dev/null \
  | grep -v "/lib/.*conversations\.ts:" 2>/dev/null
# Expected: empty. If any hit appears, it's a consumer we missed — edit it before commit.

# Also check the SQL-context grep for the messages table is now empty
grep -rEn "\b(FROM|INTO|UPDATE|DELETE\s+FROM|JOIN)\s+messages\b" platform/src \
  --include='*.ts' --include='*.tsx' 2>/dev/null
# Expected: empty
```

## Step 11 — Typecheck + build

```bash
cd platform
npm run typecheck 2>&1 | grep -E "error TS|Found [0-9]+ error" | head -20
# Expected: zero new errors vs pre-Sub-A baseline.

npm run build 2>&1 | tail -20 | tee /tmp/ws0c_sub_a_exec_build.txt
grep -E "(Compiled successfully|Failed to compile)" /tmp/ws0c_sub_a_exec_build.txt
# If build succeeds, AC-3 unblocks for the first time since WS-0B.
# If it still fails with the Turbopack symlink issue, that's pre-existing — note in commit message.
cd ..
```

## Step 12 — Curl smoke + DB write probe

```bash
cd platform
npm run start &
SERVER_PID=$!
sleep 8

# Smoke each edited / surviving route. The dropped-`messages` 500 has a recognizable signature:
# "relation \"messages\" does not exist" — any route hitting that error fails the AC.

declare -a SMOKE_ROUTES=(
  "/api/chat/build"                                  # POST — surgical remove site
  "/api/conversations/test-stub-id/messages"         # GET — fix-forward + fallback delete
  "/api/conversations/test-stub-id/export"           # GET — fix-forward
  "/share/test-stub-slug"                            # page — fix-forward
  "/clients/test-stub-id/consult/test-stub-conv"     # page — fix-forward (primary chat restore)
)
# Add /api/chat/consult/continue ONLY IF Step 4 chose fix-forward (not delete)

FAIL=0
for r in "${SMOKE_ROUTES[@]}"; do
  CODE=$(curl -s -o /tmp/ws0c_resp.txt -w '%{http_code}' -m 10 "http://localhost:3000${r}")
  BODY=$(head -c 300 /tmp/ws0c_resp.txt)
  echo "[$CODE] $r"
  # Hard failure conditions:
  #  - 500 with "relation \"messages\" does not exist" → the dropped-table runtime-bomb survived
  #  - 500 with any other SQL error tied to the V2 migration → fix-forward bug
  if [ "$CODE" = "500" ]; then
    if echo "$BODY" | grep -qE 'relation .*messages.* does not exist|loadConversationMessages|replaceConversationMessages'; then
      echo "  FAIL: dropped-table or V1 residual: $BODY"
      FAIL=$((FAIL+1))
    elif echo "$BODY" | grep -qE 'relation .* does not exist|column .* does not exist'; then
      echo "  FAIL: V2-migration SQL bug: $BODY"
      FAIL=$((FAIL+1))
    fi
    # Other 500s (auth, generic crashes) are noted but not WS-0C failures
  fi
  # 200, 401, 403, 404 are all acceptable (404 = stub conversation_id doesn't exist; expected)
done | tee /tmp/ws0c_sub_a_exec_smoke.txt

kill $SERVER_PID
cd ..

test "$FAIL" -eq 0 && echo "Smoke PASS" || echo "Smoke FAIL — $FAIL routes errored on the dropped-messages signature"
```

**Optional DB write probe** (only if a fresh conversation can be created via the consult flow):
```bash
# Verify writeConversationMessages actually persists by checking conversation_messages row count
psql_prod -c "SELECT count(*) FROM conversation_messages;"
# Note the count. After running a manual chat-create flow, re-run and confirm it increased.
# This isn't part of the AC — it's an optional sanity probe for native review.
```

## Step 13 — Commit + push

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git add -A
git status

# Commit message reflects the actual disposition (build = surgical remove, continue = fix-forward or delete)
git commit -m "fix(ws0c): chat-layer fix-forward (Sub-A-EXEC)

Sub-A investigation found conversations.ts had 2 dead exports
(loadConversationMessages, replaceConversationMessages) querying the
dropped 'messages' table, with 6 consumer files unmigrated from the
Chat V2 cutover (commit 6c431f9, May 18).

Native dispositions:
- Build chat = ephemeral: surgically removed replaceConversationMessages
  call from api/chat/build/route.ts; build streams continue, persistence
  removed.
- V1 fallback in [id]/messages = deleted (zero pre-cutover data exists).
- Continue route = [fix-forward to V2 / deleted (zero UI callers)].

Edits:
- api/chat/build/route.ts: removed replaceConversationMessages call
- api/chat/consult/continue/route.ts: [fix-forward / deleted]
- api/conversations/[id]/messages/route.ts: V2 + fallback removed
- api/conversations/[id]/export/route.ts: V2
- app/share/[slug]/page.tsx: V2
- app/clients/[id]/consult/[conversationId]/page.tsx: V2 (primary chat
  restore — biggest user-impact fix; was silently 500-ing for any saved
  conversation)
- lib/.../conversations.ts: removed loadConversationMessages +
  replaceConversationMessages dead exports

Smoke: dropped-messages signature absent on all 5 (or 6) live routes.
Typecheck: 0 new errors vs baseline.
Build: [Compiled successfully / pre-existing Turbopack symlink unchanged].

Refs WS-0C, predecessor PR #206 + tag legacy-code-cluster-purge-complete.
Sub-A findings: /tmp/ws0c_sub_a_findings.md."

git push origin feature/ws0c-residual-purge

# Closeout
kill $PROXY_PID 2>/dev/null
```

**STOP — do NOT open a PR yet.** WS-0C is one PR for all five sub-streams (per the brief §7). Sub-A-EXEC is just commit 1 of N. Report back with:
- Step 2's continue-route decision (fix-forward or deleted).
- Step 11/12 results (typecheck delta, build outcome, smoke FAIL count).
- The final commit SHA.

Cowork authors Sub-B paste next, on the same branch.

---

## Hard stops (halt and report — do not attempt unauthorized fix)

- Step 1 V2 API discovery reveals the V2 writer doesn't exist OR has fundamentally different semantics that don't map cleanly to V1's use sites — report; Cowork + native may revisit the disposition.
- Step 2 grep reveals more than just `/api/chat/consult/continue` — e.g., the URL is referenced from a config file or a different route — surface every caller; the disposition needs more nuance than fix-forward/delete.
- Step 9 typecheck cascades into errors outside the 6 consumer files (e.g., a barrel index.ts re-exports the dead functions for elsewhere) — report each cascade; fix in same commit if scoped, halt if it surfaces a whole new cluster.
- Step 10 reverse-citation gate finds a residual importer of the 2 dead functions outside `conversations.ts` — that's a 7th consumer Sub-A missed; fold into this commit.
- Step 12 smoke fails on the dropped-messages signature for any route — the fix-forward edit has a bug; debug; do not commit.
- More than 3 attempts on any single fix.

Begin with Step 0. Report at the final commit.
