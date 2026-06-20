# Pre-L2 foundation + Prashna activation + L0 build-permission + executor hardening

Branch: `feature/prashna-embed-across-layers` → `main`

## TL;DR
Closes the pre-L2 work: activates Prashna (L1 horary), implements + verifies the L0 build-permission
model, hardens the build executor (D1/D2), completes the foundation close-out, fixes the auth-session role
bug, and ships cockpit cosmetic fixes. **One deliberate caveat: `ga_structural` lands at its KNOWN-INTERIM
state (77,821 rows) — L2 Bodha is GATED until the ga_structural v2.0 completeness rebuild replaces it (logic
gate already approved, build in flight).** Everything below was verified by LIVE evidence (real HTTP / DB
inspection / cast rows), not test-count alone.

---

## What's in this PR

### 1. Prashna activation (L1 horary) — VERIFIED
`ga_prashna` was dormant (0 rows for every cast). Now activated end-to-end.
- Fixed `ga_prashna_writer` to read positions from `chart_facts` (the `ga_positions`-table bug).
- F1: `_ABBREV_TO_FULL` graha-name normalization (`MOON`→`Moon`, `RAH_MEAN`→`Rahu`…) + Decimal cast.
- F2: removed the spurious `charts` INSERT that 500'd on NOT NULL columns.
- F3: validation gate rejects contraction-form lookups (`what's my Moon sign?`).
- New routes: Next.js `/api/prashna` + FastAPI sidecar `/api/compute/prashna/cast`.
- **Cast evidence:** chart `b35046d8` → `ga_prashna_judgment` = 5 rows (one per ayanamsha), querent=Moon,
  quesited=Saturn, gap 56.42° → UNCERTAIN; Lagna Capricorn 28.39° (not the 0°Aries fallback). Namespace
  isolated — native `482012f1` has 0 prashna rows. 26/26 tests.
- Scope: single-querent (native) live; full "any querent" horary is DESIGNED + GATED on the multi-chart
  platform (see L2-L5 contribution design doc). L5 outcome-tracking deferred.

### 2. L0 build-permission model — VERIFIED (security boundary)
The `runs` build endpoint previously locked ALL builds to super_admin. Now mirrors the `clear` model.
- Two user roles only: `super_admin` (native) + `guest` (everyone else). "client" is a chart SUBJECT,
  not a user role.
- L0 (Brahmagyan) is a GLOBAL SINGLETON: no chart_id ever triggers an L0 build — not guest, not
  super_admin, not the native chart. L0 builds only at `scope=global`.
- guest builds L1-L5 only; L0/global assets are SILENTLY filtered from any guest plan
  (`allowedScopes=['per_chart']`).
- Backend 403 `FORBIDDEN_L0` + UI hides L0 Build/Rebuild/Clear for non-super_admin.
- **Live security matrix (real minted cookies, live HTTP):** super_admin global build → 201 (L0 in plan);
  super_admin per-chart L0 asset → 403 (singleton); guest brahmagyan → 403; guest ganita → plan has 16
  per_chart assets, ZERO global; guest "build global" → zero global assets in plan. L0 never leaks into a
  guest plan.

### 3. Auth-session role fix — VERIFIED
New non-admin signups 500'd: the route INSERTed `role='client'` but the `profiles` CHECK allows only
`['guest','super_admin']`.
- Aligned `/api/auth/session` + `db/types.ts` + ~25 straggler sites to the canonical `guest`.
- **Domain-safe:** `git diff | grep client_id` → no output; 63 `client_id` (chart-subject) references
  intact. Only the user-role sense changed.
- **Live signup:** POST `/api/auth/session` → HTTP 200, new `profiles` row `role=guest`, no Admin-SDK
  bypass. No migration needed (constraint was already correct).

### 4. Build-executor hardening (D1/D2) — VERIFIED
Cockpit-triggered builds could silently stall: `invokeRunJob` failure was swallowed, leaving runs stuck
`planned`, and the watchdog couldn't reap `planned` orphans.
- D1: dispatch failure now marks the run `failed` + returns 503 (no silent `planned` phantom).
- D2: watchdog reaps `planned`-orphans (`started_at IS NULL` > 10 min); existing 30/15-min thresholds
  untouched.
- **Live:** an asset rebuild executed `planned→running→completed`, zero phantoms; watchdog tests green.

### 5. Foundation close-out — VERIFIED
- Migrations 311–321 applied + ledger-reconciled.
- 4 autonomy writers confirmed regenerable; bg_rules at corpus ceiling (2,912, deterministic); catalogs
  accepted at measured floors (bg_yogas 175, bg_doshas 79, bg_medical grid).
- All L0+L1 assets lit/service_ok on the endpoint; FORENSIC 7/7.

### 6. Cockpit cosmetics — VERIFIED (migration 322)
- ga_yoga red-dot fixed (catalog_status DRAFT→CURRENT; ga_prashna same); the legitimate L2-L5 DRAFTs left
  untouched.
- Stripped the `(asset_id)` suffix from `english_name` for ga_yoga + ga_transit_anchors. Pure registry
  metadata; no component change.

---

## ⚠️ KNOWN-INTERIM: ga_structural (do not gate L2 on this)
`ga_structural` is included at **77,821 rows — its interim state, NOT final.** A completeness audit found it
is simultaneously under-built (threshold-drops; ~half the depth layer D1-only; the full sensitive-point
entity set un-ingested; inline strength proxies instead of fact_id references) AND partly inflated (spurious
`contradiction_pair` rows). The v2.0 rebuild (cited-aspect logic gate APPROVED 2026-06-19; all-30-varga
expansion + GAP 1-4 closure + Phase-3 additions + contradiction de-inflation) replaces it on a follow-up
branch. **L2 Bodha must NOT open until ga_structural v2.0 lands.** Merging this PR is safe because nothing
auto-triggers L2 (it isn't built yet) — the gate is enforced procedurally.

## Verification
Every workstream above verified by live evidence (HTTP status + DB rows + cast counts), not test-count
alone. Reports: `PRASHNA_VERIFY_v2_0`, `ORCHESTRATOR_L0_PERMISSION_VERIFY_v1_0`,
`AUTH_SESSION_ROLE_FIX_VERIFY_v1_0`, `FOUNDATION_SESSION_1_CLOSE`. FROZEN orchestrator contract untouched
(only `@register` writer additions). CI green.

## Follow-ups (not blocking this PR)
- ga_structural v2.0 completeness rebuild (the L2 gate).
- `is_asset_complete()` skips already-lit L1 assets on rebuild (observed, non-security).
- PR #179 (old hygiene pass) disposition; the yoga_label/aspect_tajik canonical-source forks.
