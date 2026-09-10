---
canonical_id: SF004_OAUTH_BINDING_CONTRACT
version: 1.0
status: CURRENT
campaign: PARIŚEṢA-V4
finding: SF-004 (OAuth RFC 6749 §4.1.3 — redirect_uri allowlist + code binding)
lane: security (sequenced immediately behind SF-003; both touch token.ts)
authored: 2026-08-22
authority: implementing session, self-reviewed (no live second reviewer available —
  see §6 for the adversarial self-review conducted in place of one)
changelog:
  - v1.0 (2026-08-22) — original contract, written before any implementation per the
    ruled contract-first process.
---

# SF-004 — OAuth Authorization-Code Binding Contract

## §1 — The finding, restated precisely

Two independent holes in the authorization_code grant, CWE-601 (open redirect) class:

1. **`platform-mcp/src/oauth/authorize.ts`'s `handleAuthorize`** validates `redirect_uri`
   only for presence (truthy), never against the requesting client's registered allowlist.
   `client_id` is not secret (it travels in authorize URLs), so a registered `client_id`
   paired with an attacker-chosen `redirect_uri` is currently accepted, stored on the auth
   code, and used as the final 302 target in `handleCallback` — **after** a real Firebase
   session verification succeeds. This hands an attacker who can lure a legitimate,
   already-authenticated user through the flow a real authorization code delivered to a
   URI of the attacker's choosing.
2. **`platform-mcp/src/oauth/token.ts`'s `authorization_code` branch** never compares the
   redeeming request's `client_id`/`redirect_uri` against the values stamped on the auth
   code at issuance (`ConsumedAuthCode.client_id` / `.redirect_uri`). No client
   authentication of any kind gates code redemption.

Both columns already exist and are already plumbed to the token endpoint (migration 383;
`ConsumedAuthCode` in `oauth_platform_client.ts`) — they are simply never compared. **No
migration is needed.**

## §2 — The exact-match rule (binds both hunks 1 and 2)

`redirect_uri` comparison, at both `/authorize` (against the registered allowlist) and
`/token` (against the auth code's stamped value), is **exact string equality on the raw,
un-decoded parameter** — `params.redirect_uri === registeredUri` / `params.redirect_uri
=== authCode.redirect_uri`. Specifically:

- **No prefix matching, no `startsWith`, no wildcard matching, ever.** Prefix matching is
  itself a well-documented open-redirect primitive (a registered
  `https://example.com/cb` would otherwise authorize
  `https://example.com/cb.evil.com` or `https://example.com/cb/../../attacker`).
- **No normalization beyond what the two strings already are.** No percent-decoding, no
  case-folding of path/query, no trailing-slash trimming, no default-port stripping. The
  registered form and the presented form must be byte-identical. (Scheme/host
  case-insensitivity per RFC 3986 §6.2.2.1 is deliberately NOT implemented — it would
  require a normalization step, and a normalization step is exactly the kind of "helpful"
  transform that has historically hidden open-redirect bypasses. A client that registers
  `https://Example.com/cb` and later sends `https://example.com/cb` gets rejected; this is
  a stricter-than-RFC-minimum posture, chosen deliberately.)
- This applies identically whether the allowlist has one entry or many — the presented URI
  must match *some* member of `redirect_uris` exactly; membership in a set is still exact
  match per element, never a fuzzy/partial test against the set.

## §3 — Error responses, per RFC section

| Site | Failure | Response | RFC basis |
|---|---|---|---|
| `/authorize` | `client_id` unknown (no client record found) | `400 { error: 'invalid_request', error_description: 'unknown client_id' }` — **NOT a redirect** | §4.1.2.1: "If the request fails due to a missing, invalid, or mismatching redirection URI, the authorization server SHOULD inform the resource owner of the error and MUST NOT automatically redirect the user-agent to the invalid redirection URI." |
| `/authorize` | `redirect_uri` present but not an exact member of the client's registered `redirect_uris` | `400 { error: 'invalid_request', error_description: 'redirect_uri not registered for this client' }` — **NOT a redirect** | same, §4.1.2.1 |
| `/token` (`authorization_code` grant) | `params.client_id !== authCode.client_id` | `400 { error: 'invalid_grant' }` | §4.1.3: the token endpoint MUST ensure the authorization code was issued to the authenticated (or, here, asserting) confidential/public client identified by `client_id` |
| `/token` | `params.redirect_uri` absent | `400 { error: 'invalid_grant', error_description: 'redirect_uri required' }` | §4.1.3: "required if the redirect_uri parameter was included in the authorization request" — since `mcp_oauth_auth_codes.redirect_uri` is `NOT NULL`, it was always included, so it is unconditionally required at redemption |
| `/token` | `params.redirect_uri !== authCode.redirect_uri` | `400 { error: 'invalid_grant' }` | §4.1.3: "and if included ensure that they match" |

The `/authorize` failures never redirect — not to the client's `redirect_uri` (that's the
attack), and not to Firebase either (the request is rejected before the Firebase
round-trip begins). This is a stronger reading of §4.1.2.1 than the RFC's own "SHOULD" — a
"MUST NOT" is safer with no compatibility cost, since no compliant client relies on being
redirected to an unregistered URI.

## §4 — The `metadata_only` lookup mode

**Problem:** `/authorize` runs before any client secret is available (the flow is a
browser redirect, not a service-to-service call with a client secret in hand), so it
cannot call `validateOAuthClient` → `validateClient`, which (correctly, per SF-002)
rejects `clientSecret === undefined`. `/authorize` needs the client's `redirect_uris` to
validate against, without authenticating the client.

**Shape.** `POST /api/mcp/oauth/clients/validate` gains a second mode, selected by
`metadata_only: true` in the body, fully separate from the existing secret-required
branch:

- **Request:** `{ client_id: string, metadata_only: true }`. Any `client_secret` present
  alongside `metadata_only: true` is ignored — this mode never touches secret
  verification.
- **Response (found):** `{ found: true, redirect_uris: string[], scopes: string[] }`.
- **Response (not found):** `{ found: false }`.
- **MUST NEVER return, in this mode:** `owner_uid`, `client_secret_hash`, `created_at`, or
  any field derived from the secret. The lookup function backing this mode (`store.ts`)
  does not `SELECT` `owner_uid` or `client_secret_hash` at all — the omission is enforced
  by the SQL projection itself, not only by response shaping, so a later careless edit to
  the response object cannot leak them.
- **Auth gate:** this route still requires `validateServiceToken(request)` (the
  `X-MCP-Internal-Token` service-to-service check) exactly as the existing route does. It
  is not a public/unauthenticated endpoint — it is reachable only by the MCP sidecar (or
  another holder of the internal token), the same trust boundary every other
  `/api/mcp/*` route already sits behind. "Unauthenticated-ish" in the plan's own risk
  note refers to the absence of *OAuth client* authentication (no secret), not the
  absence of *service* authentication (the internal token gate stays fully intact).
- **The existing secret-required branch (`metadata_only` falsy/absent) is completely
  untouched** — same code path, same `validateClient` call, same SF-002 guard
  (`clientSecret === undefined` → reject). The two modes are `if`/`else`-separated in the
  route handler with no shared mutable state, so a change to one cannot silently weaken
  the other.

## §5 — Registration URI policy

Applied at both registration entry points — `platform/src/app/api/mcp/oauth/clients/route.ts`
(the platform API, the actual DB write path) and `platform-mcp/src/server.ts`'s
`POST /mcp/oauth/register` (the public-facing RFC 7591 dynamic-registration endpoint,
which calls the former) — as defense in depth at both HTTP boundaries. Each `redirect_uri`
in `redirect_uris` must satisfy ALL of:

1. **Parses as an absolute URI.** A string that throws out of `new URL(uri)` is rejected.
2. **No fragment.** Per RFC 6749 §3.1.2.2, the redirection endpoint MUST NOT include a
   fragment component; reject any URI containing `#` (checked on the raw string, not only
   the parsed `.hash`, so a fragment-in-a-weird-place cannot slip past a lenient parse).
3. **No literal `*`.** Rejects wildcard host/path patterns outright (`https://*.evil.com/cb`,
   `https://example.com/*`) — RFC 3986 permits `*` as a valid character in several URI
   components, so this is a policy restriction, not a parse-level one, and must be
   checked explicitly.
4. **Scheme is `https:`**, OR **scheme is `http:` and the host is a loopback address**
   (`localhost`, `127.0.0.1`, or `::1`) — the RFC 8252 §7.3 dev-loopback carve-out. Every
   other scheme (`http:` on a non-loopback host, `javascript:`, `data:`, `file:`, a custom
   app-private URI scheme, or anything else) is rejected.
5. **Non-empty host** for the `https:`/loopback-`http:` schemes (rejects the
   truly-authority-less forms `https://` and `https:///`, which throw out of the `URL`
   parser and are caught by rule 1, not this rule specifically — verified empirically:
   `new URL('https:///cb')` does NOT produce an empty host; the WHATWG parser resolves the
   segment after the empty authority to hostname `'cb'`. That is a parser quirk, not a
   bypass — the raw string is what is stored and later exact-matched at `/authorize`,
   never re-parsed or re-normalized, so it cannot be used to register one string and have
   a different one match later.

**Deliberate scope limit, stated not hidden:** native-app custom URI schemes (RFC 8252
§7.1, e.g. `com.example.app:/callback`) are rejected by this policy along with everything
else non-http(s). This deployment does not currently register or serve any native-app
client, so there is no regression; adding that carve-out is out of scope for SF-004 and is
left as a follow-up if a native-app client is ever onboarded — it should not be
backed into this security fix as a speculative allowance.

**Failure response:** `400 { error: 'invalid_redirect_uri', error_description: '<which
rule failed, without echoing attacker-controlled scheme/host verbatim into a log at
error level beyond what already happens for other 400s>' }` (RFC 7591 §3.2.2 error
vocabulary; `invalid_redirect_uri` is not one of RFC 7591's four defined values but is
the closest, most literal name — case names in the test suite label the intent instead of
relying on the exact string).

## §6 — Adversarial self-review (no live second reviewer available)

Conducted in place of the GA-5 + `security-reviewer` sign-off the plan calls for; recorded
honestly here rather than claimed as obtained (§N.8 — a signal needs a real check behind
it). Bypasses considered and how this contract closes each:

1. **Trailing slash / case mismatch smuggled as "close enough."** Closed by §2's
   byte-identical exact match — no normalization step exists to exploit.
2. **Attacker registers their OWN client with a wide-open or attacker-controlled
   `redirect_uri`, then uses that legitimately-registered `client_id`.** This is NOT a
   bypass of SF-004 — SF-004's threat model is a registered `client_id` (not secret) being
   paired with an *unregistered* `redirect_uri` to redirect a *different, unsuspecting*
   user's code to the attacker. If the attacker registers their own client with their own
   `redirect_uri`, the code that gets redirected there was requested by, and consumed for,
   whatever `uid` completes that specific `/authorize`→Firebase→`/callback` round trip —
   the attacker only ever obtains a code bound to a Firebase session *they* drove through
   the flow. Registration-time abuse (e.g., trying to register `javascript:`/`data:`/an
   open third-party redirector) is what §5 closes.
3. **Empty `redirect_uris` array on a client record (e.g., a pre-SF-004 row, or a race
   with registration).** `redirect_uris.includes(params.redirect_uri)` on an empty array
   is always `false` → fails closed (400), never open. No special-case "allow if empty"
   path is implemented anywhere — confirmed by reading the exact-match check: it is a
   single `.includes()` call, not a conditional that treats an empty allowlist as
   "unrestricted."
4. **`metadata_only: true` used to fish for the existence of arbitrary `client_id`s
   (enumeration).** The response leaks only `found: boolean` plus non-secret
   `redirect_uris`/`scopes` to a caller that already holds the internal service token —
   i.e., already trusted infrastructure (the sidecar), not an arbitrary internet caller.
   This is a narrower disclosure surface than `validateOAuthClient`'s existing
   `{valid: true, owner_uid, scopes}` response already grants to the same trust tier, so
   `metadata_only` strictly reduces, not increases, what a holder of the internal token
   can learn in one path (no `owner_uid`) while adding nothing a holder of the internal
   token could not already get by attempting the client_credentials grant with a guessed
   secret and reading the 401 vs the different 400 shapes.
5. **`metadata_only` flag itself gets forwarded into the secret-required branch by
   accident (parameter-pollution-style confusion).** Closed by construction: the route
   handler branches on `body.metadata_only === true` (strict equality against the literal
   `true`, not truthy-check on a string/number) as its very first decision after the
   service-token + `client_id` checks, before `validateClient` is ever referenced in that
   request's control flow. The two branches do not share a call to `validateClient`.
6. **Token endpoint: omit `redirect_uri` entirely to dodge the comparison.** Closed by
   §3's row 4 — absence is now an explicit `400 invalid_grant`, not a skipped check.
7. **Token endpoint: send `redirect_uri` matching the code's stored value but a
   DIFFERENT, wrong `client_id`.** Closed by §3 row 3 — `client_id` is compared
   independently of `redirect_uri`; both must match, not either.
8. **Race: two concurrent `/token` requests for the same code, one with correct binding,
   one without, hoping the check reads state before the other request consumes it.**
   `consumeAuthCode` already atomically claims the code (`UPDATE ... WHERE consumed_at IS
   NULL ... RETURNING`) before SF-004's comparison ever runs — only one caller can ever
   receive a non-null record for a given code, and SF-004's binding check runs against
   *that* caller's own request params vs. the row *that same caller* just claimed. There
   is no window where a second caller's mismatched params are checked against a code
   already consumed by someone else's successful request.
9. **IPv6 loopback written as `[::1]` vs `::1` in the URI vs the parsed hostname.**
   Verified empirically against this runtime's WHATWG `URL` implementation:
   `new URL('http://[::1]:PORT/cb').hostname` returns `'[::1]'` — **brackets retained**,
   not stripped (an initial draft of this contract assumed the opposite and was corrected
   after actually running it — recorded honestly rather than silently fixed). §5's
   loopback check compares the parsed `.hostname` against both `'::1'` and `'[::1]'` so a
   real bracketed IPv6 loopback URI is accepted, not falsely rejected.
10. **Scheme-only tricks: `HTTPS://example.com` (uppercase), or `https:example.com`
    (no `//`).** `new URL()` lower-cases `.protocol` for any input it accepts, so
    uppercase-scheme registration still evaluates against `'https:'` correctly. A
    schema without `//` for `https`/`http` is not a valid absolute URI those schemes
    define and `new URL()` will either throw or parse it in a way that produces an
    empty/wrong host, which rule 5 (`non-empty host`) then catches.

**Residual, disclosed, not closed by this contract:** SF-004 does not address the
pre-existing, separately-disclosed `client_credentials` secretless-request defect
documented inline in `token.ts`'s own comment (a secretless `client_credentials` request
is still honoured, per SF-002/RATE-07's own disclosure) — that is a distinct grant type
and a distinct, already-triaged finding, not this one. SF-004 also does not add native-app
custom-scheme support (§5's stated scope limit).

## §7 — Summary of file-level changes this contract authorizes

1. `platform/src/lib/mcp/oauth/store.ts` — new exported `getClientMetadata(clientId)`,
   SQL-level restricted to `redirect_uris, scopes` only.
2. `platform/src/app/api/mcp/oauth/clients/validate/route.ts` — new `metadata_only`
   branch per §4; existing branch untouched.
3. `platform/src/lib/mcp/oauth/redirect_uri_policy.ts` (new, small, testable) —
   `isRegistrableRedirectUri(uri)` per §5.
4. `platform/src/app/api/mcp/oauth/clients/route.ts` — calls the above validator over
   every entry in `redirect_uris`.
5. `platform-mcp/src/oauth/oauth_platform_client.ts` — new
   `fetchOAuthClientMetadata(clientId)` calling the `metadata_only` mode.
6. `platform-mcp/src/oauth/authorize.ts` — `handleAuthorize` calls
   `fetchOAuthClientMetadata` and enforces §2's exact-match rule per §3's error table,
   before any other processing of `redirect_uri`.
7. `platform-mcp/src/oauth/token.ts` — `authorization_code` branch enforces §3 rows 3–5
   immediately after `consumeAuthCode` succeeds, before PKCE verification.
8. `platform-mcp/src/oauth/redirect_uri_policy.ts` (new, small, testable — a deliberate,
   disclosed duplicate of #3; the two packages do not share a module boundary, the same
   reason `platform-mcp/src/oauth/types.ts` already duplicates
   `platform/src/lib/mcp/oauth/types.ts` per its own header) — same policy, applied by:
9. `platform-mcp/src/server.ts` — the `/mcp/oauth/register` handler calls the above
   validator over every entry in `body.redirect_uris`.

No migration. No change to SF-002's `validateClient` or SF-003's PKCE enforcement.

---

*SF004_OAUTH_BINDING_CONTRACT v1.0 — PARIŚEṢA-V4, 2026-08-22. Written before
implementation per the ruled contract-first process; self-reviewed adversarially in §6 in
the declared absence of a live second reviewer.*
