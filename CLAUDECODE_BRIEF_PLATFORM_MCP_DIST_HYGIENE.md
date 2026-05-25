---
artifact: CLAUDECODE_BRIEF_PLATFORM_MCP_DIST_HYGIENE.md
session: PLATFORM-MCP-DIST-HYGIENE
workstream: platform-mcp repo hygiene (independent of any active arc)
status: PROPOSED
author: Claude Opus 4.7 (Cowork planning)
created: 2026-05-23
worktree: main (/Users/Dev/Vibe-Coding/Apps/Madhav)
estimated_duration: 10-15 minutes
cost: free
---

# Claude Code Brief — platform-mcp/dist/ Hygiene

## The problem

`platform-mcp/dist/` is committed to the repo but contains **stale v1 MCP tool compiled JS files** (`ask_madhav.js`, `execute_plan.js`, etc.) while the source under `platform-mcp/src/` has the current v3.2 tools (`chart_summary.ts`, `holistic_bundle_tool.ts`, etc.). The deployed Cloud Run revision (`amjis-mcp-00011-9zv`) is provably running v3.2 because R3 routing eval confirmed `chart_summary` works in prod — meaning Cloud Build rebuilds from source at deploy time and ignores the committed `dist/`.

This makes the committed `dist/` dead weight:
- ~100KB+ of stale compiled JS shadowing real source
- Misleads anyone reading the repo who assumes `dist/` reflects source
- Footgun: if someone runs `npm start` locally without `npm run build` first, they'll get v1 behavior
- Future-confusing: a new contributor may "fix" a v3.2 source file but never regenerate dist, then wonder why local testing shows v1 behavior

## Scope

**In scope:**
- `platform-mcp/.gitignore` (likely modifies this)
- `platform-mcp/dist/` directory (remove from tracking OR rebuild and commit, depending on decision)
- `platform-mcp/Dockerfile` (read-only investigation; touch only if it depends on committed dist)
- `platform-mcp/package.json` (read-only investigation)

**Out of scope:**
- Any `platform/src/` or other `platform/` files
- Any MCPT v3.2 work (already closed)
- Anything under `01_FACTS_LAYER/`, `025_HOLISTIC_SYNTHESIS/`, `04_REMEDIAL_CODEX/`, `06_LEARNING_LAYER/`
- `CLAUDE.md`, `.geminirules`
- Other worktrees

## Preconditions

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git rev-parse --abbrev-ref HEAD                # main
git pull --ff-only origin main
git status --porcelain                          # may have known untracked items; those stay
```

If main is dirty with anything other than the known PROBE test + the new HAIKU_TIER and R3_VERIFICATION briefs (which should already be committed per e31196ce), STOP and report.

## Step 1 — Investigate (read-only)

Confirm the decision rule before doing anything destructive.

### 1.1 — Inspect the Dockerfile

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform-mcp
cat Dockerfile
```

Look for one of these patterns:

**Pattern A (rebuilds from source — safe to gitignore dist):**
```
COPY package*.json ./
RUN npm ci
COPY src ./src
COPY tsconfig.json ./
RUN npm run build      # <-- regenerates dist/ inside the image
```

**Pattern B (copies committed dist — DO NOT gitignore):**
```
COPY package*.json ./
RUN npm ci --omit=dev
COPY dist ./dist       # <-- uses committed dist as-is
CMD ["node", "dist/server.js"]
```

Record which pattern is present.

### 1.2 — Inspect package.json scripts

```bash
cat package.json | head -40
```

Check the `scripts` block. `"start": "node dist/server.js"` means `dist/` is needed at runtime, but that's true in both patterns — the question is whether `dist/` is generated inside the image or copied from the repo.

### 1.3 — Check if anything outside platform-mcp/ depends on the committed dist

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
grep -rn "platform-mcp/dist" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.json" --include="*.yaml" --include="*.yml" --include="*.toml" --include="Dockerfile" --include="*.md" 2>/dev/null | head -20
```

If anything outside `platform-mcp/dist/` itself references the path (e.g. `import` statements pointing at the dist tree, CI workflows that read from it, deploy scripts that upload it directly), record those references — they may need to be updated.

### 1.4 — Confirm the staleness

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform-mcp
ls dist/tools/ 2>/dev/null | sort > /tmp/dist-tools.txt
ls src/tools/  2>/dev/null | sort > /tmp/src-tools.txt
diff /tmp/dist-tools.txt /tmp/src-tools.txt
```

Expected: dist has files like `ask_madhav.js`, `execute_plan.js`, `plan_query.js` that no longer exist in src; src has `chart_summary.ts`, `holistic_bundle_tool.ts` etc. that don't have corresponding .js in dist. That confirms the staleness.

## Step 2 — Decide

**If Pattern A (Dockerfile rebuilds from source) and nothing external depends on committed dist:**
→ Execute **Option 1 — Gitignore + remove**.

**If Pattern B (Dockerfile copies committed dist) OR external dependencies on committed dist exist:**
→ Execute **Option 2 — Rebuild + commit + add CI check**, and SURFACE to the native that this is the heavier path you chose, with a one-line reason.

**If unclear:** STOP and surface findings. Do not guess.

## Option 1 — Gitignore + Remove (recommended path)

### O1.1 — Add to .gitignore

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform-mcp

# Check if dist/ is already in this directory's .gitignore (it might not have one)
ls -la .gitignore 2>/dev/null
cat .gitignore 2>/dev/null | grep -E "^dist/?$"

# If absent, append (use printf to avoid trailing-newline issues)
if [ ! -f .gitignore ]; then
  printf 'dist/\nnode_modules/\n*.log\n' > .gitignore
elif ! grep -qE "^dist/?$" .gitignore; then
  printf '\n# Compiled output\ndist/\n' >> .gitignore
fi

cat .gitignore
```

### O1.2 — Remove from tracking (keep on disk for local runs)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git rm -r --cached platform-mcp/dist/
# This unstages dist/ from the index but leaves the files on disk.
# `git status` should now show dist/ as untracked (and gitignore will hide it).

git status --porcelain | head -10
# Expect: many "D platform-mcp/dist/..." entries (deletions from index),
# plus the modified .gitignore.
```

### O1.3 — Verify build still works locally

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform-mcp
npm run build 2>&1 | tail -20
# Expect: tsc completes, dist/ is regenerated on disk
ls dist/server.js && echo "dist regenerated OK"
```

If `npm run build` fails, STOP. Either the source is broken (escalate) or the build script is misconfigured (investigate before proceeding).

### O1.4 — Run tests as a smoke

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform-mcp
npm test 2>&1 | tail -30
# Expect: 257/257 pass (same baseline as MCPT v3.2 close).
```

### O1.5 — Commit + push

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

# Verify staging — should be exactly the .gitignore + all the dist/ deletions
git diff --cached --name-only | head -20

git commit -m "chore(platform-mcp): gitignore compiled dist/ + remove stale v1 artifacts

The committed platform-mcp/dist/ contained stale v1 MCP tool files
(ask_madhav.js, execute_plan.js, plan_query.js) while source has v3.2
(chart_summary.ts, holistic_bundle_tool.ts, etc.). The deployed Cloud Run
revision rebuilds from source at deploy time (confirmed via R3 routing
eval against amjis-mcp-00011-9zv), so the committed dist/ was dead weight
that misled anyone reading the repo and risked v1 behavior on local
npm start without npm run build first.

This commit:
- Adds dist/ to platform-mcp/.gitignore
- Removes the stale compiled output from git tracking (files stay on disk
  for local dev convenience)

No behavior change. Cloud Build still rebuilds from source. Local
contributors should run 'npm run build' before 'npm start' as usual.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

git push origin main
```

### O1.6 — Verify deploy if it triggers

```bash
gh run list --workflow=deploy.yml --limit=3
```

If a deploy triggered: watch it complete (`gh run watch`), then verify the new revision still serves v3.2 correctly:

```bash
gcloud run services describe amjis-mcp --region asia-south1 \
  --format='value(status.latestReadyRevisionName,status.url)'

# Sanity probe — call list_tools and confirm chart_summary is there
curl -sS -X POST "$(gcloud run services describe amjis-mcp --region asia-south1 --format='value(status.url)')/mcp" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $MARSYS_MCP_KEY" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}' \
  2>/dev/null | grep -o '"name":"chart_summary"' | head -1
# Expect: "name":"chart_summary" in the response — confirms v3.2 still live.
```

If the deploy didn't trigger (because docs-only path filters), no action needed — the next code change to platform-mcp/ will pick up the gitignore correctly.

## Option 2 — Rebuild + Commit + Add CI Check (only if Pattern B)

Only execute if Step 1 found that the Dockerfile copies committed dist or something external depends on it.

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform-mcp

# Rebuild
rm -rf dist/
npm run build 2>&1 | tail -10

cd /Users/Dev/Vibe-Coding/Apps/Madhav
git add platform-mcp/dist/
git diff --cached --stat platform-mcp/dist/ | tail -3
# Expect: many additions (new v3.2 tool .js files) and deletions (old v1 .js files)

git commit -m "chore(platform-mcp): rebuild dist/ to match current v3.2 source

The committed dist/ was stale v1 (ask_madhav, execute_plan) while source
is v3.2 (chart_summary, holistic_bundle). Rebuilt to bring dist/ into
parity with source. Dockerfile copies committed dist/ at image build,
so this commit is functionally required for next deploy to ship v3.2 if
that path is exercised.

Follow-up: add a CI step that fails if 'npm run build' produces dist/
output different from what's committed. Without the CI gate, dist/
will drift again. Tracked as: 'CI gate: dist/ matches build output'.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"

git push origin main
```

Then surface to native: "Chose Option 2 because <reason>. A follow-up brief is needed to add the CI gate."

## Acceptance — done when

- [ ] Decision (Option 1 or 2) made and rationale recorded.
- [ ] `platform-mcp/dist/` either gitignored + untracked, OR rebuilt to match source.
- [ ] `npm run build` succeeds locally.
- [ ] `npm test` still passes (257/257).
- [ ] Commit pushed to main.
- [ ] If deploy triggered: new revision is healthy and still serves v3.2 tools.
- [ ] Native notified with the report below.

## Final report to Cowork (the native)

1. **Dockerfile pattern detected**: A (rebuild) or B (copy committed).
2. **Decision**: Option 1 or Option 2, with one-line rationale.
3. **Commit SHA**.
4. **Tests still passing**: yes/no.
5. **Deploy state**: if a deploy triggered, the new revision name + confirmation chart_summary is still in tools/list.
6. **Anomalies**: anything unexpected in the Dockerfile, package.json, or build process.

## Failure modes

| Failure | Action |
|---|---|
| Dockerfile is neither clearly A nor B (custom script, multi-stage with conditional copy) | STOP. Read the full Dockerfile carefully. Surface to native if unclear |
| `npm run build` fails | STOP. The source may have a real build error masked by the stale dist; this becomes a separate triage |
| `npm test` fails after change | STOP. The change should be purely about packaging, not behavior. Investigate |
| External reference to platform-mcp/dist/ found in Step 1.3 | Switch to Option 2 OR update the reference; surface to native |
| Push rejected (branch protection) | Open a small PR instead, request review, do not auto-merge |
| Deploy fails on the new revision | Surface logs; previous revision still serves traffic; rollback only if symptomatic |

## Out of scope

- Any change to `platform-mcp/src/` (source files stay as-is).
- Touching any other workstream's files.
- Adding the CI gate (Option 2 follow-up) — that's a separate brief.
- Modifying `CLAUDE.md`, `.geminirules`, or anything under the must-not-touch globs.
