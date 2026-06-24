---
brief_id: POST_ARC_CLEANUP_v1_0
status: ACTIVE
authored_by: Cowork (planning)
executor: Claude Code in Google Antigravity IDE
authored_at: 2026-05-31
model_directive: Use Gemini Pro or DeepSeek. Anthropic banned.
worktree: /Users/Dev/Vibe-Coding/Apps/Madhav (main checkout)
work_branch: fix/post-arc-cleanup
upstream_finding: build_e2e_arc + CI recovery arc — eight post-arc residuals
                  accumulated across May 31 sessions.
---

# CLAUDECODE_BRIEF — Post-arc eight-item cleanup

## Why

Eight hygiene items accumulated across the build_e2e_arc and its CI
recovery. None individually warrants its own session; bundled into a
single cleanup pass. Three are pure operator shell commands (no code
touch); five are code changes. All are non-blocking to production
today — form works, chart builds, CI is green — but each item has a
known downstream cost if left unaddressed.

| # | Item | Type | Risk |
|---|---|---|---|
| 1 | Turbopack python-sidecar venv symlink breaks `npm run build` | git/code | Low — build already broken in same way on main |
| 2 | PROD_DATABASE_URL secret not set → migrations skip in deploy | operator | Low — graceful skip already in place |
| 3 | schema_migrations row 161 missing in prod | operator | Low — migration was renamed, not re-run |
| 4 | proxy.ts not wired as Next.js middleware (orphaned) | code | Low — currently a no-op |
| 5 | github-actions SA lacks storage.objectAdmin on tf-state bucket | operator | Low — terraform init warns, continues |
| 6 | Places API hook exists but not wired in NewClientForm | code | Medium — form works but lat/lon are manual-only |
| 7 | dashas_writer A66/A67/A68 xfail: early `return 0` makes dry-run unreachable | code | Low — tests marked xfail, not failing CI |
| 8 | CascadePreviewModal is a C-S7 scaffold (shell only) | code | Low — modal opens but shows placeholder |

## Scope

`may_touch`:
- `platform/python-sidecar/venv/` (git untrack only — do NOT delete files)
- `.gitignore` (root)
- `platform/src/middleware.ts` (NEW)
- `platform/src/proxy.ts` (read-only; do NOT modify)
- `platform/src/components/clients/NewClientForm.tsx`
- `platform/src/components/clients/usePlacesAutocomplete.ts` (read-only)
- `platform/python-sidecar/pipeline/writers/dashas_writer.py`
- `platform/python-sidecar/pipeline/__tests__/test_dashas_writer.py`
- `platform/src/components/cockpit/CascadePreviewModal.tsx`
- `platform/src/app/api/build/cascade/route.ts` (NEW)
- `platform/src/app/api/build/cascade/__tests__/route.test.ts` (NEW)
- `.github/workflows/deploy.yml` (build-arg addition for Places key only)

`must_not_touch`:
- `platform/src/proxy.ts` content (wire it, do not rewrite it)
- `platform/src/app/api/clients/create/route.ts`
- Any other API route
- Any cockpit component other than CascadePreviewModal
- `00_ARCHITECTURE/` except this brief
- `platform/python-sidecar/venv/` files (git-untrack only, not rm -rf)

## Hard gates

- DO NOT deploy. DO NOT push to main directly. Terminal state is one
  commit on `fix/post-arc-cleanup` + PR opened.
- DO NOT use Anthropic models.
- Operator-action items (2, 3, 5) get printed as shell commands only —
  executor does NOT run them. Print them at the end under
  "=== OPERATOR ACTIONS ===".
- git rm --cached on the venv must use `--cached` (index only).
  Do NOT `rm -rf` the venv directory.
- middleware.ts must re-export from `./proxy` exactly — do not copy
  proxy.ts contents into middleware.ts.

═══════════════════════════════════════════════════════════════════════════
§0 — Pre-flight
═══════════════════════════════════════════════════════════════════════════

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch origin
git checkout main && git pull origin main
git checkout -b fix/post-arc-cleanup

# Confirm proxy.ts is a named export (not default) — middleware.ts needed
grep "^export async function proxy\|^export function proxy" \
  platform/src/proxy.ts | head -3

# Confirm middleware.ts does NOT exist
ls platform/src/middleware.ts 2>/dev/null || echo "CONFIRMED ABSENT"

# Check if venv is tracked in git
git ls-files platform/python-sidecar/venv/ | head -5

# Confirm the early-return bug in dashas_writer
sed -n '1028,1035p' platform/python-sidecar/pipeline/writers/dashas_writer.py
```

═══════════════════════════════════════════════════════════════════════════
§1 — Item 1: Remove venv from git index + fix gitignore
═══════════════════════════════════════════════════════════════════════════

The Turbopack error is:
  `Symlink [project]/python-sidecar/venv/bin/python is invalid`
Cause: `python3.13` is valid on the host but Turbopack's virtual FS
can't resolve a relative symlink inside a tracked venv directory.
Fix: untrack from git (leaves files on disk; gitignore prevents re-add).

```bash
# Untrack from git index — files stay on disk
git rm -r --cached platform/python-sidecar/venv/ 2>/dev/null \
  || echo "INFO: venv not tracked — skipping git rm"

# Add explicit gitignore entry if not already covered
# Root .gitignore already has `venv/` (matches any depth) but an explicit
# entry at the platform level is belt-and-suspenders
grep -q "python-sidecar/venv" .gitignore \
  || echo "python-sidecar/venv/" >> .gitignore

grep -q "python-sidecar/venv" platform/.gitignore 2>/dev/null \
  || echo "venv/" >> platform/.gitignore
```

After removing from index, verify Turbopack no longer errors on the
symlink:
```bash
cd platform && timeout 30 npx next build 2>&1 \
  | grep -c "python-sidecar/venv/bin/python" && echo "STILL ERRORING" \
  || echo "SYMLINK ERROR GONE"
cd ..
```

═══════════════════════════════════════════════════════════════════════════
§2 — Item 4: Wire proxy.ts as Next.js middleware
═══════════════════════════════════════════════════════════════════════════

`platform/src/proxy.ts` exports `proxy` (named, not default) and a
`config` matcher object. Next.js requires a file named `middleware.ts`
at `src/` that exports a default function named `middleware` and a
`config` export. Create the wiring shim:

Create `platform/src/middleware.ts`:
```ts
export { proxy as middleware, config } from './proxy'
```

That is the ENTIRE file. Do not copy proxy.ts contents. Do not add
logic. The health endpoint `/api/health` is already in proxy.ts's
`isPublic` list (line 39) — no further exemption needed.

Verify the shim builds cleanly:
```bash
cd platform && npx tsc --noEmit 2>&1 | grep middleware | head -5
cd ..
```

═══════════════════════════════════════════════════════════════════════════
§3 — Item 7: Fix A66/A67/A68 — remove early `return 0` in dashas_writer
═══════════════════════════════════════════════════════════════════════════

Root cause: lines 1030–1031 of `dashas_writer.py` return 0 immediately
when `conn is None`, before any row-collection happens. Lines 1113–1115
already have the correct dry-run return (`return total`) but are
unreachable because of the early guard.

Fix: delete lines 1030–1031:
```python
# DELETE THESE TWO LINES (around line 1030):
    if conn is None:
        return 0
```

After deletion the function reads:
```python
def write(build_id, chart_id, ayanamsha_id, chart_output, conn, extra=None):
    """..."""
    logger.info(...)   # <-- execution now continues here when conn=None

    all_rows: list[tuple] = []
    # ... all collection code runs ...

    if conn is None:               # line ~1113 — still present, correct
        logger.info(...)
        return total               # returns actual count
    # ... DB write for real conn ...
```

Then remove the `xfail` markers from A66, A67, A68 in
`test_dashas_writer.py` — they should now pass:

```python
# DELETE these decorator + reason blocks (keep the test functions):
@pytest.mark.xfail(
    reason="dry-run row counting not yet implemented ...",
    strict=False,
)
```

Remove the three `@pytest.mark.xfail` blocks (A66, A67, A68). Keep
the test functions and their assertions unchanged.

Verify:
```bash
cd platform/python-sidecar
python -m pytest pipeline/__tests__/test_dashas_writer.py \
  -k "test_write_returns_positive_count_conn_none \
      or test_write_returns_large_count_for_full_chart \
      or test_write_with_empty_maha_seq" \
  -v 2>&1 | tail -20
cd ../..
```

All three must be PASSED (not xfail, not xpass — actual PASSED).

═══════════════════════════════════════════════════════════════════════════
§4 — Item 6: Wire usePlacesAutocomplete into NewClientForm
═══════════════════════════════════════════════════════════════════════════

`platform/src/components/clients/usePlacesAutocomplete.ts` already
exists. Read it first to understand the interface, then wire it.

The hook contract (from reading the file):
- `isPlacesEnabled()` → bool (checks NEXT_PUBLIC_GOOGLE_MAPS_API_KEY)
- `buildPlacesHandler(onResult)` → callback for the Places onPlaceChanged
- `PlacesResult` shape: `{ lat, lng, timezone_id, tz_offset, formatted_address }`

Changes to `NewClientForm.tsx`:

1. Import at top:
```ts
import {
  isPlacesEnabled,
  buildPlacesHandler,
  type PlacesResult,
} from './usePlacesAutocomplete'
```

2. Add to `handleBirthPlaceBlur` (or a new `handlePlacesResult` callback):
```ts
function handlePlacesResult(result: PlacesResult) {
  setForm((prev) => ({
    ...prev,
    birth_place: result.formatted_address,
    latitude: String(result.lat),
    longitude: String(result.lng),
    timezone_id: result.timezone_id ?? prev.timezone_id,
    tz_offset: result.tz_offset !== undefined
      ? String(result.tz_offset)
      : offsetFromTimezoneId(result.timezone_id ?? prev.timezone_id),
    places_resolved: true,
  }))
  setManualOpen(false)
  setErrors((prev) => ({
    ...prev,
    birth_place: undefined,
    latitude: undefined,
    longitude: undefined,
    tz_offset: undefined,
  }))
}
```

3. In the birth_place input row, if `isPlacesEnabled()` is true, render
   the Google Places `<Autocomplete>` wrapper around the input. If false,
   render the plain Input unchanged (current behaviour — no regression).

   Use the existing `@react-google-maps/api` package if it's a dep;
   otherwise check `package.json` for the available Google Maps package
   and use that. If no Google Maps package exists at all, add a comment
   `// TODO: npm install @react-google-maps/api when key is ready` and
   use a `useEffect` that simulates the callback via a ref — i.e. keep
   the Places wire ready but guard the entire import behind
   `isPlacesEnabled()` so it doesn't blow up when the key is absent.

4. In `deploy.yml`, add the build-arg:
```yaml
# In the Web service build step, alongside other NEXT_PUBLIC_* args:
--build-arg NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=${{ secrets.GOOGLE_MAPS_API_KEY }}
```

   Add it to BOTH the Cloud Build step and any local-build notes. Do NOT
   add the actual key value anywhere in code.

Verify:
```bash
cd platform
npx tsc --noEmit 2>&1 | grep NewClientForm | head -5
npm test -- NewClientForm.test.tsx 2>&1 | tail -10
cd ..
```

All 10 existing NewClientForm tests must still pass (Places path is
gated on `isPlacesEnabled()` which returns false in test env because
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY is absent).

═══════════════════════════════════════════════════════════════════════════
§5 — Item 8: CascadePreviewModal full implementation
═══════════════════════════════════════════════════════════════════════════

Current state: `platform/src/components/cockpit/CascadePreviewModal.tsx`
is a C-S7 scaffold — modal opens, shows "Rebuild {assetId}?" and a
placeholder sentence, has Cancel + Confirm buttons. Full implementation
adds the downstream dependency list.

### §5.1 — API endpoint

Create `platform/src/app/api/build/cascade/route.ts`:

```ts
/**
 * GET /api/build/cascade?chart_id=X&asset_id=Y
 *
 * Returns the ordered list of downstream asset_names that would be
 * invalidated and requeued if asset_id is rebuilt for chart_id.
 *
 * Uses the build_steps table's `depends_on` JSONB column (array of
 * asset_name strings). If depends_on is absent, falls back to a
 * static dependency map derived from the asset registry.
 */
import { NextResponse } from 'next/server'
import { getServerUser } from '@/lib/firebase/server'
import { query } from '@/lib/db/client'

export const dynamic = 'force-dynamic'

export async function GET(request: Request): Promise<Response> {
  const user = await getServerUser()
  if (!user) return NextResponse.json({ error: 'unauthenticated' }, { status: 401 })

  const { searchParams } = new URL(request.url)
  const chart_id = searchParams.get('chart_id')
  const asset_id = searchParams.get('asset_id')

  if (!chart_id || !asset_id) {
    return NextResponse.json(
      { error: 'chart_id and asset_id are required' },
      { status: 400 },
    )
  }

  // Find the most recent build for this chart
  const buildResult = await query<{ build_id: string }>(
    `SELECT build_id FROM builds
      WHERE chart_id = $1
      ORDER BY created_at DESC LIMIT 1`,
    [chart_id],
  )
  const build_id = buildResult.rows[0]?.build_id

  if (!build_id) {
    return NextResponse.json({ asset_id, downstream: [], build_id: null })
  }

  // Fetch all steps and their depends_on arrays for this build
  const stepsResult = await query<{
    asset_name: string
    depends_on: string[] | null
    status: string
  }>(
    `SELECT asset_name, depends_on, status
       FROM build_steps
      WHERE build_id = $1
      ORDER BY step_index ASC`,
    [build_id],
  )

  // Walk forward through steps: a step is downstream if any of its
  // depends_on includes asset_id OR a step already in the downstream set
  const downstream: string[] = []
  const downstreamSet = new Set<string>([asset_id])

  for (const step of stepsResult.rows) {
    if (step.asset_name === asset_id) continue
    const deps: string[] = Array.isArray(step.depends_on) ? step.depends_on : []
    if (deps.some((d) => downstreamSet.has(d))) {
      downstream.push(step.asset_name)
      downstreamSet.add(step.asset_name)
    }
  }

  return NextResponse.json({
    asset_id,
    build_id,
    downstream,
    total_affected: downstream.length,
  })
}
```

**Schema note:** If `build_steps` has no `depends_on` column, return
`{ downstream: [], total_affected: 0, note: 'depends_on column absent' }`
rather than erroring. The modal will display a fallback message.
Detect absence by catching the query error and checking for
`column "depends_on" does not exist` in the message.

### §5.2 — Modal implementation

Replace `CascadePreviewModal.tsx` with a fetching implementation.
Keep the Props interface exactly as-is (no prop changes).

The modal should:
1. On open (`open === true`), fetch `/api/build/cascade?chart_id=X&asset_id=Y`
2. While loading: show a spinner (simple pulsing dot, no external lib)
3. On success with `downstream.length > 0`:
   - Heading: `Rebuild {assetId}?`
   - Body: list of downstream asset names, each on its own row with
     a gold `→` prefix and a dimmed status badge (status from steps if
     available; else just the name)
   - Footer counter: `{n} downstream asset(s) will be requeued`
4. On success with `downstream.length === 0`:
   - Body: `No downstream dependencies — safe to rebuild in isolation.`
5. On fetch error: `Could not load dependency graph. Rebuilding anyway?`
6. Cancel + Confirm rebuild buttons (unchanged behaviour)

Visual treatment: obsidian panel (`#0f0d12`), gold headings, 12px body
text, JetBrains Mono for asset names and counter.

Max height of the downstream list: `max-height: 240px; overflow-y: auto`
to avoid a gigantic modal for deep dependency chains.

### §5.3 — Tests

Create `platform/src/app/api/build/cascade/__tests__/route.test.ts`:

1. `test: returns 401 without auth`
2. `test: returns 400 without chart_id`
3. `test: returns {downstream:[]} when no build exists for chart_id`
4. `test: returns correct downstream list by walking depends_on`
   — mock build_steps with a 3-step chain where step C depends on B,
   B depends on A; rebuilding A should return [B, C]
5. `test: excludes the rebuilt asset_id itself from downstream`

Verify:
```bash
cd platform
npm test -- cascade/route.test.ts 2>&1 | tail -15
npx tsc --noEmit 2>&1 | grep -E "cascade|CascadePreviewModal" | head -5
cd ..
```

═══════════════════════════════════════════════════════════════════════════
§6 — Local verification gates
═══════════════════════════════════════════════════════════════════════════

```bash
cd platform

# TypeScript — form + middleware + cascade (pre-existing errors are noise)
npx tsc --noEmit 2>&1 \
  | grep -E "(NewClientForm|middleware|cascade|CascadePreviewModal)" \
  | head -20

# Form tests — all 10 must pass
npm test -- NewClientForm.test.tsx 2>&1 | tail -5

# Cascade tests — all 5 must pass
npm test -- cascade 2>&1 | tail -5

# Python xfail resolution — A66/A67/A68 must be PASSED
cd python-sidecar
python -m pytest pipeline/__tests__/test_dashas_writer.py \
  -k "conn_none or large_count or empty_maha" -v 2>&1 | tail -10
cd ../..
```

═══════════════════════════════════════════════════════════════════════════
§7 — Commit + push + PR
═══════════════════════════════════════════════════════════════════════════

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav

git add .gitignore platform/.gitignore
git add platform/src/middleware.ts
git add platform/python-sidecar/pipeline/writers/dashas_writer.py
git add platform/python-sidecar/pipeline/__tests__/test_dashas_writer.py
git add platform/src/components/clients/NewClientForm.tsx
git add platform/src/app/api/build/cascade/
git add platform/src/components/cockpit/CascadePreviewModal.tsx
git add .github/workflows/deploy.yml

git status

git commit -m "$(cat <<'EOF'
fix(cleanup): post-arc eight-item hygiene pass

Item 1 — Turbopack symlink: git-untrack platform/python-sidecar/venv/
  from index (files stay on disk); add explicit gitignore entries.
  Resolves TurbopackInternalError that blocked npm run build.

Item 4 — Next.js middleware: create platform/src/middleware.ts shim
  that re-exports {proxy as middleware, config} from ./proxy.
  Activates session-based auth middleware (health + /api/mcp/* already
  exempted in proxy.ts isPublic list).

Item 7 — A66/A67/A68 xfail: remove early `return 0` guard at
  dashas_writer.py:1030-1031. Dry-run row collection now runs fully;
  correct `return total` at line ~1113 is now reachable. Remove xfail
  markers from three test functions.

Item 6 — Places API wiring: wire usePlacesAutocomplete hook into
  NewClientForm; handlePlacesResult populates lat/lon/tz fields and
  sets places_resolved=true; gated on isPlacesEnabled() so form works
  unchanged when NEXT_PUBLIC_GOOGLE_MAPS_API_KEY is absent.
  Add --build-arg NEXT_PUBLIC_GOOGLE_MAPS_API_KEY to deploy.yml.

Item 8 — CascadePreviewModal: replace scaffold with fetching impl;
  GET /api/build/cascade walks build_steps.depends_on forward-transitively
  from asset_id; modal shows downstream list, spinner, fallback on error.
  5 new route tests.

Items 2/3/5 are operator-only actions — see §8 OPERATOR ACTIONS block
printed to console.

Pre-existing: npm run build TurbopackInternalError on mcp/asset/route.ts
python symlink is resolved by Item 1 of this commit.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"

git push -u origin fix/post-arc-cleanup

gh pr create \
  --base main \
  --head fix/post-arc-cleanup \
  --title "fix(cleanup): post-arc eight-item hygiene pass" \
  --body "$(cat <<'EOF'
## Summary

- **Item 1** Turbopack symlink: git-untrack `python-sidecar/venv/` — resolves `npm run build` TurbopackInternalError
- **Item 4** Middleware wiring: `src/middleware.ts` shim activates session auth (`proxy.ts` was orphaned named export)
- **Item 7** A66/A67/A68: remove early `return 0` in `dashas_writer.write(conn=None)` — dry-run count now reachable; xfail markers removed
- **Item 6** Places API: `usePlacesAutocomplete` hook wired in `NewClientForm`; populates lat/lon/tz on resolve; no regression when key absent
- **Item 8** CascadePreviewModal: replaces C-S7 scaffold with fetching impl; `GET /api/build/cascade` walks `build_steps.depends_on` transitively; 5 new tests

Items 2/3/5 are operator-shell-only (no code) — see §8 in brief.

## Test plan
- [x] 10/10 NewClientForm tests pass
- [x] 5/5 cascade route tests pass
- [x] A66/A67/A68 PASSED (not xfail)
- [x] tsc clean for touched files

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

═══════════════════════════════════════════════════════════════════════════
§8 — OPERATOR ACTIONS (executor prints these; does NOT run them)
═══════════════════════════════════════════════════════════════════════════

After merging PR and auto-deploy completes, operator runs:

**Item 2 — PROD_DATABASE_URL secret:**
```
GitHub → repo → Settings → Secrets and variables → Actions
→ New repository secret
  Name:  PROD_DATABASE_URL
  Value: <get from GCP Secret Manager: prod-db-url>

After adding: re-run the last deploy workflow job to apply pending
migrations, OR run manually:
  cd platform && DATABASE_URL=<value> npx tsx scripts/migrate.ts
```

**Item 3 — Migration 161 backfill:**
```sql
-- Run via start_db_proxy.sh + psql, or in Supabase SQL editor:
INSERT INTO schema_migrations (version)
VALUES ('161')
ON CONFLICT DO NOTHING;

-- Verify:
SELECT version FROM schema_migrations WHERE version = '161';
-- Expected: one row
```

**Item 5 — storage.objectAdmin for Terraform state bucket:**
```bash
gcloud storage buckets add-iam-policy-binding \
  gs://madhav-astrology-tf-state \
  --member="serviceAccount:github-actions@madhav-astrology.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# Verify: re-run deploy.yml — the "terraform init" step should no longer
# print the WARN about storage.objects.list.
```

**Item 6 — Places API key (after PR merge):**
```bash
# Add secret to GitHub:
# GitHub → Settings → Secrets → GOOGLE_MAPS_API_KEY → <key from GCP>

# Add to Cloud Run env (for SSR path if needed):
gcloud run services update amjis-web \
  --region=asia-south1 \
  --update-env-vars="NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=<key>"
# Note: NEXT_PUBLIC_* baked at build time via --build-arg in deploy.yml;
# the Cloud Run env-var is a belt-and-suspenders for runtime fallback only.
```

═══════════════════════════════════════════════════════════════════════════
§9 — Final report (print this after PR is opened)
═══════════════════════════════════════════════════════════════════════════

```
=== POST-ARC CLEANUP REPORT ===

PR:                     #<N> — fix/post-arc-cleanup
Branch:                 fix/post-arc-cleanup

Code items completed:
  Item 1 (symlink)      DONE — venv git-untracked; gitignore updated
  Item 4 (middleware)   DONE — src/middleware.ts shim created
  Item 7 (A66-A68)      DONE — early return 0 removed; xfails removed
  Item 6 (Places)       DONE — usePlacesAutocomplete wired; deploy.yml updated
  Item 8 (Cascade)      DONE — full modal + /api/build/cascade + 5 tests

Operator-action items (DO NOT auto-execute):
  Item 2 (DB secret)    PENDING — see §8
  Item 3 (migration 161) PENDING — see §8
  Item 5 (IAM)          PENDING — see §8

Tests:
  NewClientForm:        10/10 passing
  cascade route:         5/5 passing
  dashas A66/A67/A68:   3/3 PASSED (was xfail)
  tsc:                  clean for touched files

Next step:   Review + merge PR #<N>. Run §8 operator actions.
             Auto-deploy will activate middleware and cascade modal.

=== END REPORT ===
```

---

End of CLAUDECODE_BRIEF_POST_ARC_CLEANUP_v1_0.
