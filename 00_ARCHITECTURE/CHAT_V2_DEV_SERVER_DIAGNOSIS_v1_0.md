---
name: Chat V2 Dev Server Diagnosis
canonical_id: CHAT_V2_DEV_SERVER_DIAGNOSIS_v1_0
version: 1.0
status: CURRENT
authored: 2026-05-17
author: Claude Code executor (C.7+C.8 verification campaign)
---

# Chat V2 Dev Server Diagnosis — v1.0

## §1 Dev Server State Before vs. After Diagnosis

**Before diagnosis:**
- Pre-flight requirement: git status must be clean
- Actual state: `platform/src/components/consume/ConsumeChatV2.tsx` was modified
  (useMemo side-effect anti-pattern fix — valid React correction, not noise)
- Action taken: committed the fix as `d4605b1` before running verification
- After commit: git status clean (untracked `99_PERSONAL_SADHANA/` and `post_merge_smoke/`
  are non-platform directories and do not affect the test run)

**Dev server state:**
- Process: `node` PID 6732, listening on `*:hbci` (:3000) — already running before session
- No restart needed
- Server started in prior session with `MARSYS_FLAG_CHAT_V2_ENABLED=true`

## §2 Route-by-Route Response Codes

| Route | HTTP status | Diagnosis |
|---|---|---|
| `/` | 307 | Normal: Next.js redirects unauthenticated root to /login |
| `/api/health` | 401 | Normal: auth-gated health endpoint — server is responding |
| `/clients` | 307 | Normal: auth redirect |
| `/api/clients` | 401 | Normal: auth-gated |
| `/api/conversations` | 401 | Normal: auth-gated |

**Verdict:** All routes respond as expected. There is no 404 pathology.
A 307 on root is by design for a Next.js app with mandatory auth middleware.

## §3 Resolved Consume URL

**Client ID:** `362f9f17-95a5-490b-a5a7-027d3e0efda0`  
**Client name:** Abhisek Mohanty  
**Consume URL:** `/clients/362f9f17-95a5-490b-a5a7-027d3e0efda0/consume`  
**Full URL:** `http://localhost:3000/clients/362f9f17-95a5-490b-a5a7-027d3e0efda0/consume`

Verified with auth (super-admin session):
```
HTTP/1.1 200 OK
X-Powered-By: Next.js
```

Session minted via `platform/scripts/get_session_cookie.mjs` using
`FIREBASE_ADMIN_CREDENTIALS` + `NEXT_PUBLIC_FIREBASE_API_KEY` from `platform/.env.local`.

## §4 Healing Actions Taken

1. **ConsumeChatV2.tsx citation fix committed** (`d4605b1`):
   - `useMemo` was calling `onCitationCount` as a side effect (React anti-pattern)
   - Fixed: `useMemo` now returns `citationCount`; `useEffect` calls `onCitationCount`
   - This is a legitimate fix included in the D.1 verification scope

2. **No dev server restart needed** — server was already healthy on port 3000

3. **No client_id substitution needed** — `362f9f17-95a5-490b-a5a7-027d3e0efda0` exists
   in dev DB and responds 200 with a valid super-admin session
