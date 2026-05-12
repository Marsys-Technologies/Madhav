---
gate: II
session: post-close-fixup-2026-05-13
status: DOCUMENTED
---

# Gate II — Post-close Fixup Blockers

## B.1 — T5 visual smoke: Playwright spec not authored; auth credentials absent

**Phase:** C (Visual smoke for T5)

**Blocker type:** Missing spec + missing credentials

**Details:**
The previous fixup session documented that a dedicated Gate II trace drawer spec
"can be added" but never authored one. `find . -name "*gate_ii*smoke*"` finds
fixture JSON files only — no `.spec.ts` file exists. Additionally, the auth
credentials required to run any portal E2E test are not set in the environment.

**What's missing:**

| Item | Status |
|---|---|
| `SMOKE_SESSION_COOKIE` (super_admin Firebase session) | Not set in env |
| `SMOKE_CHART_ID` (client ID with recent queries) | Not set in env |
| Gate II trace drawer spec (`tests/e2e/portal/gate_ii_trace_drawer.spec.ts`) | Not yet authored |

**To unblock (native action required):**

1. Obtain a valid super_admin session cookie (Firebase session token):
   ```bash
   # Start the dev server, log in as super_admin at localhost:3000,
   # then extract the 'session' cookie from browser DevTools → Application → Cookies
   export SMOKE_SESSION_COOKIE="<paste-cookie-value-here>"
   ```

2. Set a client ID with recent queries:
   ```bash
   export SMOKE_CHART_ID="<paste-a-chart-uuid-here>"
   # Example: psql $DATABASE_URL -c "SELECT chart_id FROM audit_events LIMIT 1;"
   ```

3. Author the spec (one-time setup, ~30 min):
   ```bash
   # Create tests/e2e/portal/gate_ii_trace_drawer.spec.ts
   # Follow the auth pattern from tests/e2e/portal/consume-polish.spec.ts:
   #   - test.skip if !SMOKE_SESSION_COOKIE || !SMOKE_CHART_ID
   #   - beforeEach: context.addCookies([{ name: 'session', value: SESSION_COOKIE, ... }])
   #   - Navigate to /clients/<CHART_ID>/consume
   #   - Click the Trace button (data-testid="trace-toggle" or similar)
   #   - Verify drawer opens; screenshot drawer_full.png
   #   - Verify QueryPlan banner sticky; screenshot banner.png
   #   - Expand Retrieval group; screenshot retrieval_expanded.png
   #   - Expand Checkpoints group; screenshot checkpoints_expanded.png
   ```

4. Run once credentials and spec are ready:
   ```bash
   SMOKE_SESSION_COOKIE="..." SMOKE_CHART_ID="..." \
   npx playwright test gate_ii_trace_drawer --reporter=list --workers=1
   ```

**Impact on merge eligibility:** None. Gate II is merge-ready per all 20 ACs.
T5 visual smoke is supplementary verification — it does not gate the merge.

---

## B.2 — J.2 audit_events schema mismatch: follow-up gate needed

**Phase:** B (live DB verification — completed, but with a critical finding)

**Blocker type:** Code defect requiring a follow-up gate (not a merge blocker)

**Details:**
Live DB verification (2026-05-13) found that `loadAuditRow()` in
`src/lib/admin/trace_assembler.ts:489-499` queries columns that do not exist in
the production `audit_events` table. The assembler's `.catch()` silently returns
null for all production queries. The Audit lifecycle node always renders
`placeholder_note` even for queries that have `audit_events` rows.

**Columns queried vs. columns available:**

| Assembler queries | Live production column | Action needed |
|---|---|---|
| `audit_event_id` | `id` | rename in SELECT |
| `validator_verdict` | `audit_status` | rename in SELECT + map values |
| `audit_event_version` | (not present) | omit or add migration |
| `disclosure_tier` | (not present) | omit or add migration |
| `b10_compliant` | (not present) | omit or derive |
| `b11_compliant` | (not present) | omit or derive |

**Full detail:** `platform/tests/fixtures/gate_ii_j2_live_verification.json`

**To fix (follow-up gate scope):**
Update `loadAuditRow()` to use the actual production column names:
```sql
SELECT id AS audit_event_id,
       NULL::int AS audit_event_version,
       NULL::text AS disclosure_tier,
       audit_status AS validator_verdict,
       (audit_status = 'ok') AS b10_compliant,
       (audit_warnings IS NULL) AS b11_compliant
FROM audit_events
WHERE query_id = $1::uuid
LIMIT 1
```
Then update `AuditStepMetadata` to use `audit_status` vocabulary
(`'ok'` | `'warn'` | `'block'`) instead of `'PASS'` | `'FAIL'`.

**Impact on merge eligibility:** None. The Audit node degrades gracefully to
`placeholder_note`; the renderer does not crash.

---

*End of BLOCKERS.md — Gate II post-close fixup 2026-05-13.*
