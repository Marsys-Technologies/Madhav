# MCP — Claude Code DEPLOY + VERIFY Prompt v1.0

Paste this into a **fresh Claude Code session in Antigravity IDE**, pointed at the **main** Madhav worktree (`/Users/Dev/Vibe-Coding/Apps/Madhav`).

This prompt:
1. Commits the `cloudbuild.yaml` `_TAG` fix (if uncommitted)
2. Pushes to main
3. Builds + deploys `amjis-mcp` to Cloud Run with the correct image tag
4. Waits for the new revision to become ready
5. Runs four smoke tests to verify auth paths work end-to-end
6. Prints a final PASS/FAIL report

It does NOT register the connector in claude.ai (that's a browser UI step you do after smoke passes).

---

## Before pasting, in your terminal

Export your MCP API key as `MCP_API_KEY` (single quotes to survive the `$` in the password):

```bash
export MCP_API_KEY='<your-mcp-prod-api-key>'  # fetch: gcloud secrets versions access latest --secret=mcp-canary-key
```

Then launch Claude Code in this directory:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
claude --dangerously-skip-permissions
```

---

## What to paste

```
You are the deploy-and-verify operator for the MARSYS-JIS MCP URL-token
auth fix. The platform-mcp source has been patched (commit 3bf5342a)
to accept ?api_key=<key> as a Bearer fallback. cloudbuild.yaml has been
locally edited to use ${_TAG} instead of $COMMIT_SHA (so local builds
work without source-trigger context).

Your job: commit any uncommitted governance changes, deploy the new
amjis-mcp revision, wait for it to serve traffic, and run smoke tests
that prove auth works on both the Authorization-header and URL-query
paths.

Worktree: /Users/Dev/Vibe-Coding/Apps/Madhav
Mode: --dangerously-skip-permissions
Halt policy: STOP on any non-recoverable error; report what worked.

Echo each step header. Echo PASS/FAIL after each step. Use clear visual
separators so I can scan the output quickly.

────────────────────────────────────────────────────────────────────────
STEP 0 — Preconditions
────────────────────────────────────────────────────────────────────────

  Verify env var:
    if [ -z "$MCP_API_KEY" ]; then
      echo "HALT: MCP_API_KEY env var not set. Export it before launching Claude Code."
      exit 1
    fi
    echo "MCP_API_KEY length: ${#MCP_API_KEY} (expect 49)"

  Verify gcloud auth + active project:
    gcloud config get-value account
    gcloud config get-value project
    # Expect: your @gmail account, project madhav-astrology (or equivalent)

  Verify we are on main, clean (apart from possibly cloudbuild.yaml + .mcp.json):
    cd /Users/Dev/Vibe-Coding/Apps/Madhav
    git status

  Verify cloudbuild.yaml has the _TAG fix:
    grep -q '\${_TAG}' platform-mcp/cloudbuild.yaml || {
      echo "HALT: cloudbuild.yaml is missing the _TAG substitution. Cowork was supposed to have edited it."
      exit 1
    }
    grep -q '\$COMMIT_SHA' platform-mcp/cloudbuild.yaml && {
      echo "WARN: cloudbuild.yaml still references \$COMMIT_SHA. The _TAG fix may not have replaced all occurrences."
    }
    echo "PASS: cloudbuild.yaml uses _TAG substitution"

────────────────────────────────────────────────────────────────────────
STEP 1 — Commit + push the cloudbuild.yaml fix (if uncommitted)
────────────────────────────────────────────────────────────────────────

  If cloudbuild.yaml shows as modified in `git status`:
    git add platform-mcp/cloudbuild.yaml
    git commit -m "fix(mcp-build): use _TAG substitution instead of \$COMMIT_SHA

\$COMMIT_SHA is only populated when Cloud Build is triggered by a
source-control event. Local 'gcloud builds submit' leaves it empty,
producing an invalid image tag 'amjis-mcp:' (trailing colon).

Switch to a user-defined _TAG substitution that defaults to 'latest'.
Local builds can override with --substitutions=_TAG=\$(git rev-parse --short HEAD)
to keep the per-commit image history."
    git push origin main
    echo "PASS: cloudbuild.yaml fix committed and pushed"
  else
    echo "SKIP: cloudbuild.yaml already committed (no uncommitted changes)"
  fi

────────────────────────────────────────────────────────────────────────
STEP 2 — Build + deploy amjis-mcp
────────────────────────────────────────────────────────────────────────

  Capture commit SHA for image tagging:
    SHA=$(git rev-parse --short HEAD)
    echo "Image tag will be: amjis-mcp:$SHA"

  Note the current latest-ready revision so we can detect when the new
  one takes over:
    OLD_REV=$(gcloud run services describe amjis-mcp \
      --region asia-south1 \
      --format='value(status.latestReadyRevisionName)')
    echo "Current revision (will be replaced): $OLD_REV"

  Submit the build:
    cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform-mcp
    gcloud builds submit \
      --config=cloudbuild.yaml \
      --substitutions=_TAG="$SHA"
    cd /Users/Dev/Vibe-Coding/Apps/Madhav

  If build fails: HALT. Capture the build ID from the error and run:
    gcloud builds log <build_id>
  Surface the relevant error block.

────────────────────────────────────────────────────────────────────────
STEP 3 — Wait for new revision to serve traffic
────────────────────────────────────────────────────────────────────────

  Poll latestReadyRevisionName until it changes from OLD_REV:

    for i in $(seq 1 30); do
      NEW_REV=$(gcloud run services describe amjis-mcp \
        --region asia-south1 \
        --format='value(status.latestReadyRevisionName)')
      if [ "$NEW_REV" != "$OLD_REV" ]; then
        echo "PASS: new revision $NEW_REV ready (was $OLD_REV)"
        break
      fi
      echo "  waiting... ($i/30) still on $OLD_REV"
      sleep 10
    done

    if [ "$NEW_REV" = "$OLD_REV" ]; then
      echo "HALT: revision did not change after 5 minutes. Check build status:"
      gcloud builds list --limit=3
      exit 1
    fi

  Capture the service URL for the smoke tests:
    AMJIS_MCP_URL=$(gcloud run services describe amjis-mcp \
      --region asia-south1 \
      --format='value(status.url)')
    echo "amjis-mcp serving at: $AMJIS_MCP_URL"

────────────────────────────────────────────────────────────────────────
STEP 4 — Smoke test (4 probes)
────────────────────────────────────────────────────────────────────────

  Probe 1 — Health endpoint (no auth, public):
    H1=$(curl -fsS -o /dev/null -w "%{http_code}" "$AMJIS_MCP_URL/health")
    echo "Probe 1 — GET /health → $H1 (expect 200)"
    [ "$H1" = "200" ] && P1=PASS || P1=FAIL

  Probe 2 — POST /mcp without any auth (should reject):
    H2=$(curl -s -o /dev/null -w "%{http_code}" \
      -X POST "$AMJIS_MCP_URL/mcp" \
      -H "Content-Type: application/json" \
      -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"1.0"}}}')
    echo "Probe 2 — POST /mcp no auth → $H2 (expect 401)"
    [ "$H2" = "401" ] && P2=PASS || P2=FAIL

  Probe 3 — POST /mcp WITH Authorization Bearer header (canonical path):
    H3=$(curl -s -o /dev/null -w "%{http_code}" \
      -X POST "$AMJIS_MCP_URL/mcp" \
      -H "Content-Type: application/json" \
      -H "Accept: application/json, text/event-stream" \
      -H "Authorization: Bearer $MCP_API_KEY" \
      -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"1.0"}}}')
    echo "Probe 3 — POST /mcp + Bearer header → $H3 (expect 200)"
    [ "$H3" = "200" ] && P3=PASS || P3=FAIL

  Probe 4 — POST /mcp?api_key=... URL-token fallback (the new code path):
    H4=$(curl -s -o /dev/null -w "%{http_code}" \
      -X POST "$AMJIS_MCP_URL/mcp?api_key=$MCP_API_KEY" \
      -H "Content-Type: application/json" \
      -H "Accept: application/json, text/event-stream" \
      -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"smoke","version":"1.0"}}}')
    echo "Probe 4 — POST /mcp?api_key=... → $H4 (expect 200 — this is the URL-token fix)"
    [ "$H4" = "200" ] && P4=PASS || P4=FAIL

  If Probe 4 returns 401: the new revision is serving but the URL-token
  fallback didn't make it into the image. Check Cloud Run logs:
    gcloud run services logs read amjis-mcp --region asia-south1 --limit 30

────────────────────────────────────────────────────────────────────────
STEP 5 — Final report
────────────────────────────────────────────────────────────────────────

  Echo:

═══════════════════════════════════════════════════════════════════════
 MCP URL-TOKEN AUTH DEPLOY — FINAL REPORT
═══════════════════════════════════════════════════════════════════════

 Image tag deployed:       amjis-mcp:$SHA
 Cloud Run revision:       $NEW_REV   (was $OLD_REV)
 Service URL:              $AMJIS_MCP_URL

 Smoke tests:
   Probe 1  GET /health                       → $H1   ($P1)
   Probe 2  POST /mcp (no auth)               → $H2   ($P2)
   Probe 3  POST /mcp + Bearer header         → $H3   ($P3)
   Probe 4  POST /mcp?api_key=... URL fallback → $H4   ($P4)

═══════════════════════════════════════════════════════════════════════
 NEXT — REGISTER IN CLAUDE.AI (browser, ~30 seconds)
═══════════════════════════════════════════════════════════════════════

 1. Open: https://claude.ai/customize/connectors
 2. If a previous "MARSYS-JIS" entry exists, REMOVE it first.
 3. Click "+" → "Add custom connector"
 4. Name:  MARSYS-JIS
    URL:   $AMJIS_MCP_URL/mcp?api_key=<your-key>
           (substitute the actual key; do NOT paste it from chat history)
 5. Skip Advanced settings.
 6. Click "Add".
 7. In any new chat: "+" → Connectors → toggle MARSYS-JIS on
 8. Smoke prompt:  Use MARSYS-JIS ask_madhav to summarize my Atmakaraka.

═══════════════════════════════════════════════════════════════════════
 STATUS: $(if [ "$P1" = "PASS" ] && [ "$P2" = "PASS" ] && [ "$P3" = "PASS" ] && [ "$P4" = "PASS" ]; then echo "ALL PROBES PASS — ready for claude.ai registration"; else echo "FAILURES PRESENT — see probe table above"; fi)
═══════════════════════════════════════════════════════════════════════

Then terminate. Do not start any other work.
```

---

## What this prompt deliberately does NOT do

- **Doesn't register in claude.ai.** No API for that; UI step.
- **Doesn't write the API key to any file.** The key lives only in your shell `MCP_API_KEY` env var for the duration of the session.
- **Doesn't modify the application code or briefs.** Pure deploy + verify.

## If any probe fails

- **Probe 1 FAIL (no 200 from /health):** The service isn't serving at all. Check `gcloud run revisions list --service amjis-mcp --region asia-south1` to see if any revision is in ready state; check Cloud Build for build failures.
- **Probe 2 FAIL (expected 401, got something else):** Auth middleware is broken. The server may be allowing unauthenticated requests, which is a security regression. Read the new code in `platform-mcp/src/server.ts` lines 71-90.
- **Probe 3 FAIL (Bearer header rejected):** The PBKDF2 validation path is broken, OR `MCP_INTERNAL_TOKEN` is misconfigured between amjis-web and amjis-mcp, OR your key has been revoked. Check Cloud Run logs.
- **Probe 4 FAIL (URL fallback rejected):** The new revision didn't pick up the URL-token patch. Check that the deployed image tag matches what you just built: `gcloud run services describe amjis-mcp --region asia-south1 --format='value(spec.template.spec.containers[0].image)'`.

## Idempotency

Safe to re-paste this prompt anytime. Each step is conditional or self-recovering — git commits skip if nothing to commit; build runs unconditionally (new builds are cheap); revision polling has a 5-min timeout; smoke probes are stateless.
