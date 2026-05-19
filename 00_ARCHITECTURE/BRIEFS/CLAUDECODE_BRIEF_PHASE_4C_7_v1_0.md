---
artifact: CLAUDECODE_BRIEF_PHASE_4C_7_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: COMPLETE
authored_by: Cowork 2026-05-19
session_id: 4C-7
session_name: 4C-7 — iCal export + signed time-boxed feed URLs
executor: Claude Code sub-agent (Conductor)
worktree:
  branch: feature/phase-4c-panchang
  path_absolute: /Users/Dev/Vibe-Coding/Apps/Panchang
predecessor: 4C-6-S4
governing_plan: 00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §4.4.2 + §5.6 (feed.ics route)
---

# CLAUDECODE_BRIEF — Phase 4C-7
## iCal export — page export, finder results, subscribable feed (HMAC-signed)

Three calendar export surfaces per master plan §4.4.2: (1) day's significant windows from /panchang, (2) selected Muhurat Finder results, (3) subscribable iCal feed URL. All feed URLs HMAC-signed with 90-day expiry per D3 settled 2026-05-19.

---

## §0 — Pre-flight
```bash
cd /Users/Dev/Vibe-Coding/Apps/Panchang
test -f 00_ARCHITECTURE/PHASE_4C_6_CLOSE_v1_0.md
test -f platform/src/app/panchang/components/ActionBar.tsx
test -f platform/src/app/panchang/components/MuhuratResultsList.tsx
# Verify SESSION_SECRET or similar HMAC secret exists in env
grep -l "SESSION_SECRET\|HMAC_SECRET" platform/.env.* 2>/dev/null || true
```

## §2 — Mandatory reads
1. `CLAUDE.md` §C
2. Master plan §4.4.2 (Calendar Export full spec) + §5.6 (route layout)
3. Existing iCal usage in project if any (`grep -l "ical" platform/src/` or check package.json for `ical-generator`)
4. Existing HMAC patterns in project (`grep -l "hmac\|sign_url" platform/src/lib/`)

## §3 — Scope (11 items)

### Item 1 — Install `ical-generator` dependency
Add to `platform/package.json`: `"ical-generator": "^6.0.0"`. Run `npm install` in `platform/`. Or use Node's built-in if a heavier dep is undesirable.

**AC.4C7.1:** Dep installed; import works.

### Item 2 — `panchangToIcs` builder
Add `platform/src/lib/panchang/ics_builder.ts`. Function: `buildDayIcs(panchang: Panchang, location: string) → string` returning a valid iCal blob with events:
- Auspicious yogas as events with categories `MARSYS-Panchang/auspicious`
- Inauspicious windows (Rahu/Yama/Gulika/Bhadra) as events with `MARSYS-Panchang/avoid`
- Each event: SUMMARY (e.g., "Sarvartha Siddhi Yoga ★★★★"), DESCRIPTION (full breakdown + back-link to /panchang?d=YYYY-MM-DD), LOCATION (human readable, e.g., "Bhubaneswar, IN"), CATEGORIES

Also: `buildMuhuratIcs(windows: MuhuratWindow[], location: string) → string` for Muhurat Finder result exports.

**AC.4C7.2:** Builders return RFC 5545-compliant ICS strings; sample output validates against `ics-deep-parser`.

### Item 3 — HMAC URL signing utility
Add `platform/src/lib/security/sign_url.ts`:

```typescript
import { createHmac } from 'crypto';

const SECRET = process.env.SESSION_SECRET ?? process.env.HMAC_SECRET;
if (!SECRET) throw new Error('SESSION_SECRET or HMAC_SECRET must be set');

export function signFeedUrl(params: {
  user_id: string;
  location: string;
  personalise?: string;  // hash of chart_id if personalise enabled; NEVER raw chart_id
  expires_at: number;    // unix ts, 90 days from now
}): string {
  const payload = JSON.stringify(params);
  const sig = createHmac('sha256', SECRET).update(payload).digest('hex');
  return `${Buffer.from(payload).toString('base64url')}.${sig}`;
}

export function verifyFeedUrl(token: string): typeof params | null {
  const [encoded, sig] = token.split('.');
  if (!encoded || !sig) return null;
  const payload = Buffer.from(encoded, 'base64url').toString('utf8');
  const expected = createHmac('sha256', SECRET).update(payload).digest('hex');
  if (sig !== expected) return null;
  const params = JSON.parse(payload);
  if (params.expires_at < Date.now() / 1000) return null;  // expired
  return params;
}
```

**AC.4C7.3:** Sign+verify round-trip works; expired tokens rejected; tampered signatures rejected.

### Item 4 — `/api/panchang/ics` route (one-off export)
Create `platform/src/app/api/panchang/ics/route.ts`. Handles GET with query params `?d=YYYY-MM-DD&loc=...&chart_id=...`. Returns ICS file (Content-Type: `text/calendar`, Content-Disposition: `attachment; filename=panchang-<date>.ics`). Auth-gated (uses same auth pattern as existing API routes).

**AC.4C7.4:** Endpoint returns valid ICS; downloads to file in browser.

### Item 5 — `/api/panchang/feed.ics` route (subscribable feed)
Create `platform/src/app/api/panchang/feed.ics/route.ts`. Handles GET with query param `?token=<signed_token>`. Verifies token; if valid, returns a rolling 90-day iCal feed (today through today+90) with all significant Panchang events. Content-Type: `text/calendar; charset=utf-8`. NO auth — token IS the auth.

Refreshes daily. Calendar apps cache for 12-24 hours; that's fine.

**AC.4C7.5:** Subscribed in Google Calendar via URL; events appear with correct windows.

### Item 6 — `/api/panchang/feed/subscribe` route (token generation)
POST endpoint that generates a signed token for the current user. Body: `{ location: "bhubaneswar", personalise: bool }`. Returns: `{ feed_url: "https://amjis-web.../api/panchang/feed.ics?token=..." }`. Auth-gated.

**AC.4C7.6:** Subscribe endpoint returns signed URL; URL works as feed source.

### Item 7 — `/api/panchang/feed/revoke` route
POST endpoint that rotates the HMAC secret per-user (or maintains a per-user revocation list — pick whichever is simpler). After revoke, all previously-signed URLs for that user fail verification.

**AC.4C7.7:** Revoke endpoint works; pre-revoke URL returns 401 after revoke.

### Item 8 — UI wiring: ActionBar export button
Update `ActionBar.tsx`: "📅 Export to Calendar" button now enabled. Click opens a dropdown menu with three options:
- "Download today's Panchang as .ics" → triggers `/api/panchang/ics?d=...&loc=...`
- "Get subscribable feed URL" → calls `/api/panchang/feed/subscribe`, copies URL to clipboard, shows toast "URL copied! Paste into Google/Apple Calendar to subscribe."
- "Manage feed subscriptions" → modal listing current user's active tokens (with creation/expiry dates) + revoke button per token

**AC.4C7.8:** All three actions work end-to-end.

### Item 9 — Muhurat Finder results export
Update `MuhuratResultsList.tsx` from 4C-6-S3: the "📅 Export to Calendar" inline action on each window row now enabled. Builds a single-event ICS for that window via `buildMuhuratIcs` and downloads.

**AC.4C7.9:** Click export on a muhurat result → ICS download.

### Item 10 — Tests + cross-app verification
- Unit tests for `ics_builder`, `sign_url` (sign/verify/expire/tamper)
- Manual test: subscribe to feed.ics URL in Google Calendar → events appear with correct times and categories
- Manual test: subscribe in Apple Calendar → events appear
- Acceptance: feed URL doesn't contain `chart_id` or any PII — only `location` and optional `personalise=<hash>`

**AC.4C7.10:** All tests PASS; cross-app subscribe verified in Google + Apple; PII check passes.

### Item 11 — Close
CURRENT_STATE: 4C.7 CLOSED; SESSION_LOG; brief flip; FINAL_SUMMARY; queue advance to 4C-8.

**AC.4C7.11:** Done.

---

## §5 — Constraints
**may_touch:** `platform/package.json` (Item 1 dep); `platform/src/lib/panchang/ics_builder.ts` (new); `platform/src/lib/security/sign_url.ts` (new); `platform/src/app/api/panchang/{ics,feed.ics,feed/subscribe,feed/revoke}/route.ts` (new); `platform/src/app/panchang/components/{ActionBar,MuhuratResultsList}.tsx` (wiring only); tests; governance state files; this brief.
**must_not_touch:** sidecar; engine internals; retrieve/; muhurat backend (sealed); UI component internals from prior sessions (only the named files for wiring); corpus.

## §6 — Close checklist
- [ ] 11 ACs PASS
- [ ] Cross-app subscribe verified (Google + Apple)
- [ ] PII audit: feed URL contains no chart_id or user identity beyond signed token
- [ ] HMAC secret has 90-day expiry honored
- [ ] FINAL_SUMMARY emitted

## §7 — LLM stack
Gemini primary; Anthropic BANNED.

## §8 — Context carried
- D3 settled: signed time-boxed URLs (HMAC, 90-day expiry, no chart_id in URL)
- ICS format must be RFC 5545 compliant
- ical-generator npm package preferred over hand-rolling

## §9 — Canary
Subscribe the generated feed URL in Google Calendar. If events don't appear within 30 minutes (Google's poll interval), the feed format is broken — halt and report.

*End — 4C-7.*
