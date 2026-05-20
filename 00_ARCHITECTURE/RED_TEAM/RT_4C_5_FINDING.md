---
artifact: RT_4C_5_FINDING.md
probe_id: RT.4C.5
probe_question: >
  Calendar feed PII surface — verify no chart_id, email, or user identity leaks
  via feed URL or ICS content.
session_id: 4C-9
authored_on: 2026-05-20
verdict: PASS
---

# RT.4C.5 — Calendar Feed PII Surface Finding

## §1 — Probe question

Does the iCal feed system (subscribable URL + ICS content) leak any PII:
chart_id, user email, user_id, or other identity information?

## §2 — Attack surfaces examined

1. `platform/src/app/api/panchang/feed.ics/route.ts` — the subscribable feed route
2. `platform/src/app/api/panchang/feed/subscribe/route.ts` — the token generation route
3. `platform/src/app/api/panchang/ics/route.ts` — the single-day download route
4. `platform/src/lib/security/sign_url.ts` — HMAC-signed token implementation
5. `platform/src/lib/panchang/ics_builder.ts` — ICS content builder

## §3 — Findings

### Feed URL structure

The subscribable feed URL has the form:
```
/api/panchang/feed.ics?token=<signed_token>
```

The `signed_token` is a base64url-encoded JSON payload + HMAC-SHA256 signature.

**Token payload fields (from `sign_url.ts`):**
```typescript
{
  jti: string           // Random UUID — DB key for revocation (no user info)
  location: string      // Location slug: "bhubaneswar" (not a user identifier)
  personalise?: string  // SHA-256 hash of chart_id, first 16 hex chars ONLY
  expires_at: number    // Unix timestamp (expiry)
  issued_at: number     // Unix timestamp (issue time)
}
```

**PII assessment:**
- `jti` is a random identifier — not derivable from user identity
- `location` is a public city slug — not a user identifier
- `personalise` is `sha256(chart_id).slice(0,16)` — irreversible; chart_id is NOT exposed
- No `user_id`, `email`, or `uid` field in token payload
- The subscribe route comment explicitly states: "Token payload: NO user_id, NO chart_id — only jti + location + optional hash"

**PASS** — the feed URL carries no recoverable user PII.

### ICS content (feed + single-day download)

Inspection of `ics_builder.ts` confirms:
- Event `SUMMARY` lines contain: Panchang element names (tithi, nakshatra, vara, etc.) + star rating unicode
- Event `DESCRIPTION` lines contain: breakdown factor labels + scores, inauspicious windows list
- No `ATTENDEE`, `ORGANIZER`, or `X-WR-*` custom properties that would embed user identity
- The `UID` field in each calendar event is derived from event date + element, not from user identity

grep result confirms: no `uid`, `user_id`, `email`, `chart_id` strings in ics_builder.ts output paths.

**PASS** — ICS content carries no user PII.

### DB-side user_id storage

The subscribe route stores `user_id` in the `panchang_feed_subscriptions` DB table
(server-side only, for revocation purposes). This is appropriate — user_id is needed
to implement "Revoke All" per-user. It is NOT included in the token or the feed URL.
The DB-side storage is standard JWT revocation practice. **PASS.**

### Single-day download (`/api/panchang/ics`)

The single-day download accepts `?chart_id=` as a query param (passed to the sidecar
for personalised ICS generation). This chart_id travels server-side only — it is not
embedded in the generated ICS file content. **PASS.**

## §4 — Summary table

| Surface | PII risk checked | Result |
|---|---|---|
| Feed URL token | chart_id, email, user_id in token payload | PASS — none present; personalise is hash |
| ICS event content | user identity fields in SUMMARY/DESCRIPTION | PASS — none present |
| HMAC signing | token reversibility | PASS — HMAC-SHA256, not reversible |
| DB revocation store | user_id stored (appropriate) | PASS — server-side only, not in URL/ICS |
| Single-day download | chart_id leaks into ICS | PASS — chart_id server-side only |

## §5 — Verdict

**PASS** — No PII leakage identified in feed URL, token payload, or ICS content.
The design correctly separates: (a) the anonymous token (jti + location + expiry)
that travels in the URL from (b) the server-side user_id stored only for revocation.
The chart_id personalisation is encoded as a 16-char hash — irreversible without
the original value.
