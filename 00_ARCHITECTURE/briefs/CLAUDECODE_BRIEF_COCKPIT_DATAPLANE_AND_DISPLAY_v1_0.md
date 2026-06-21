---
artifact: CLAUDECODE_BRIEF_COCKPIT_DATAPLANE_AND_DISPLAY_v1_0.md
canonical_id: COCKPIT_DATAPLANE_AND_DISPLAY_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (Chrome-MCP live diagnosis on localhost:3000 build cockpit) 2026-06-16
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
execution_mode: CONTINUOUS / AUTONOMOUS — phase-by-phase, no human gate between phases. Dependency gates + Tier-3 rails only.
data_plane: ALWAYS prod via Cloud SQL proxy (port 5433)
diagnosis_surface: /clients/482012f1-710e-4a25-994a-93821f5871aa/build (native build cockpit, Nirmāṇa entry) — CockpitShell → DataAssetsView → AssetRow
key_finding: >
  Five reported symptoms, THREE distinct causes. (1) Most red dots / FAILED / conn_timeout are the
  DATA PLANE being down/flapping — SIDECAR observed flipping OK→DOWN, network log shows 503s + hung
  requests on /api/cockpit/runs/active + /sse. The stats route is working CORRECTLY: it times out
  per-asset at 3.5s and returns error:'conn_timeout' when the DB connection hangs (half-open TCP
  after a proxy restart — documented in the route itself). (2) "build-state stale" on every lit
  asset + short bars at 100% count are the TWO OWED MIGRATIONS never applied to prod (229 throughput
  reconcile, 231 floor reset). (3) The two service engines looking "reverted to Sanskrit" is a SEED
  SCRIPT inconsistency — their sanskrit_name is Devanagari while every other asset is romanized IAST.
inherited_non_negotiables: >
  count_sql is data-truth (§N.4); floors aspirational (target_floor = achieved, NEVER a gate); no
  silent drops; surgical migrations only with FRESH unused numbers (check ledger — 223/227 collided);
  no audience tier.
---

# Cockpit Data-Plane + Display — Fix Brief v1.0

## §0 — The reported symptoms → four root causes
(The native flagged the all-Gaṇita red dot specifically — note it splits from the data-plane red
dots: the FAILED/conn_timeout ones are the down plane, but the LIVE-with-data ga_ assets are red
because of DRAFT catalog_status. Two different causes behind one "red dot" symptom.)
Native reported, on the build cockpit (`/clients/[native]/build`):
1. Progress bars not filling up.
2. "build-state stale" under every asset.
3. The last two Brahmagyan service engines reverted to Sanskrit (were English).
4. All Gaṇita assets show red dots.
5. Gaṇita assets show FAILED / stale.

**Live Chrome-MCP diagnosis maps these to THREE causes:**

| Symptom | Root cause | Fix owner |
|---|---|---|
| Red dots, FAILED, `conn_timeout` (most L1 + Yoga Catalog) | **DATA PLANE down/flapping** — SIDECAR OK→DOWN observed; 503s + hung requests in network log; stats route times out per-asset at 3.5s → `error:'conn_timeout'` (correct behaviour, half-open TCP after proxy restart) | OPERATOR (proxy/sidecar) + P1 resilience |
| "build-state stale" on every lit asset | **Migration 229 (throughput reconcile) never applied to prod** — count_sql has rows so state='lit', but asset_throughput.state is stale/absent → the informational badge fires (working as designed, lines 266-270) | P2 (apply 229) |
| Bars short even at 100% count (e.g. 825,084/825,084 ~15% fill) | **Migration 231 (floor reset) never applied** — target_floor still set ABOVE achieved; AssetProgressBar fills actual/target_floor | P2 (apply 231) |
| Two service engines "reverted to Sanskrit" | **Seed script inconsistency** — bg_panchanga.sanskrit_name='पञ्चाङ्ग गणना' + bg_ephemeris_engine.sanskrit_name='दृक् एफिमेरिस' are Devanagari; every other asset's sanskrit_name is romanized IAST | P3 (seed romanize) |
| RED DOT on EVERY Gaṇita asset — incl. LIVE-with-data ones (Graha-sthāna 50/50, Daśākrama 536,471, Pañcāṅga 221) | **All ga_ assets are `catalog_status='DRAFT'`** — no ga_ seed row sets catalog_status, so the seed default (line 1302: non-brahmagyan → 'DRAFT') applies. StatusDot line 93: `isRed = state==='error' \|\| not_migrated \|\| isDraft` → DRAFT forces red REGARDLESS of data/lit state. L1 is SEALED, so DRAFT is now stale. | P5 (promote L1 → CURRENT) |

## §1 — IMPORTANT: the cockpit code is largely CORRECT
Do NOT "fix" the stats route's timeout/error logic — it is behaving exactly as designed. The red
dots are the cockpit HONESTLY reporting a down data plane. The real fixes are: bring the data plane
up + make it resilient (P1), apply the two owed migrations (P2), and romanize two seed rows (P3).
This brief is mostly DATA-PLANE + DATA, not display-logic.

---

## PHASE P1 — Data-plane health + cockpit resilience to a flapping proxy
### P1.0 — Operator precondition (verify first)
Confirm on the native's machine: `platform/scripts/start_db_proxy.sh` is running (Cloud SQL Auth
Proxy listening on 5433) AND the python sidecar is up. The header showed `SIDECAR DOWN` and the
network log had 503s on `/api/cockpit/runs/active` + `/api/cockpit/sse`. If the proxy/sidecar is
down, START it and re-check the cockpit — most red dots should clear on the next stats poll. This is
the same ECONNREFUSED-5433 / half-open-TCP class seen before.

### P1.1 — Make the cockpit degrade gracefully when the data plane flaps (resilience)
Even with the proxy up, a transient proxy restart currently paints assets red for a full poll cycle.
Harden the surface so a transient data-plane blip is visibly TRANSIENT, not a scary "FAILED":
- In the stats route, distinguish **`conn_timeout` / connection-level errors** (data-plane down) from
  **per-asset SQL errors** (a real count_sql problem). Return a distinct marker (e.g.
  `error_class: 'dataplane' | 'query'`) so the UI can render data-plane blips as an amber
  "data plane reconnecting…" state rather than a red per-asset FAILED.
- In `AssetRow`/`AssetProgressBar`, when `error_class==='dataplane'`, show an amber "reconnecting"
  state (NOT a red FAILED bar) — the asset has data, the plane is just momentarily unreachable.
- Confirm the `/api/cockpit/sse` 503 path retries/backs off rather than wedging the overlay (ties to
  the sticky-overlay fix in CLAUDECODE_BRIEF_L0_L1_CLOSURE P1 — ensure that landed).
- Acceptance: with the proxy up, all assets with data render lit; kill the proxy briefly → assets
  show amber "reconnecting", NOT red FAILED; restore proxy → they return to lit within one poll.

## PHASE P2 — Apply the two owed migrations to prod (the real "stale" + "short bar" fixes)
These were authored in the L0/L1 closure but the prod apply is owed. Apply them surgically (verify
fresh numbers against the ledger; if 229/231 already consumed, use the next free numbers and note it):
- **Migration 229** — reap orphaned `asset_throughput` records (building/stale → lit where count_sql
  confirms data). Clears the "build-state stale" badge from every L0/L1 asset that has real data.
- **Migration 231** — reset `target_floor` = achieved count for every asset whose floor is currently
  ABOVE its actual rows (bg_yogas, the corpus assets, and audit ALL bg_/ga_ for the same). Fixes the
  short-bar-at-100%-count rendering (floors are aspirational, NOT gates — §N.4).
- Also confirm **230** (bodha_registry_reconcile) and **232** (drop ganita_positions, from the
  closure pass) are applied or queued; run `scripts/audit/p6_cockpit_consistency_check.sql` after.
- Acceptance [verify-against: prod, proxy up]: zero assets with rows>0 show "build-state stale";
  bars fill proportionally to achieved (a 100%-of-achieved asset shows a full or near-full bar);
  p6 consistency SQL returns zero divergences.

## PHASE P3 — Romanize the two service-engine seed names (native decision: romanize to match)
Per native decision 2026-06-16 (romanize to match the other 37 assets, keep the bilingual layout):
- `platform/scripts/seed/asset_registry_seed.ts`:
  - `bg_panchanga.sanskrit_name`: `'पञ्चाङ्ग गणना'` → `'Pañcāṅga Gaṇanā'`
  - `bg_ephemeris_engine.sanskrit_name`: `'दृक् एफिमेरिस'` → `'Druk Ephemeris'`
  - Leave `english_name` ('Panchanga Engine' / 'Ephemeris Engine') and everything else unchanged.
- Re-apply the seed to prod (the seed-apply hardening / post-apply readback must confirm the two
  rows now carry the romanized sanskrit_name). NO migration needed if the seed is the source of
  truth for these columns — but if asset_registry was hand-patched in prod, a tiny UPDATE migration
  (fresh number) is the safe path; verify which is authoritative before choosing.
- Acceptance [verify-against: prod]: the two Brahmagyan service engines render `Pañcāṅga Gaṇanā` /
  `Druk Ephemeris` as the big line + 'Panchanga Engine' / 'Ephemeris Engine' as the small line,
  matching the romanized style of every other asset. No other asset's name changes.

## PHASE P4 — Re-verify the whole Brahmagyan + Gaṇita cockpit (proxy up)
After P1–P3, with the data plane up:
- Acceptance: Brahmagyan = all 14 assets correct (12 data lit, 2 service GREEN — not dormant/red —
  once the sidecar health probe passes; the 2 service engines romanized). Gaṇita = all 10 ga_ assets
  lit + **GREEN dot** (after P5 promotes them to CURRENT), no red dots, no FAILED, no conn_timeout,
  bars filled, no "build-state stale". Yoga Catalog no longer FAILED (it was conn_timeout from the
  down plane, not a data problem — confirm it has its rows once the plane is up). NOTE: the Gaṇita
  green dots require BOTH the data plane up (P1) AND the DRAFT→CURRENT promotion (P5) — a lit-but-DRAFT
  asset still renders red.

## PHASE P5 — Promote L1 Gaṇita from DRAFT → CURRENT (the LIVE-but-red dot fix)
### P5.0 — Root cause (distinct from the data-plane red dots)
The Gaṇita assets that render LIVE with full data (Graha-sthāna 50/50, Daśākrama 536,471, Pañcāṅga
221/221) STILL show a red dot. Cause is NOT the data plane — it is `catalog_status`:
- `StatusDot` (AssetRow.tsx ~line 93): `isRed = state==='error' || state==='not_migrated' || isDraft`,
  where `isDraft = catalogStatus === 'DRAFT'`. So **DRAFT forces a red dot regardless of lit state.**
- Seed (asset_registry_seed.ts ~line 1302): `catalogStatus = asset.catalog_status ?? (asset.layer === 'brahmagyan' ? 'CURRENT' : 'DRAFT')`.
  **No ga_ row sets catalog_status**, so every Gaṇita asset defaults to `'DRAFT'` → red dot.
- This convention ("L0=CURRENT; L1–L5=DRAFT", seed line ~49) predates the L1 seal. **L1 Gaṇita is
  now SEALED** (L1_GANITA_CLOSURE_v1_0) and fully built — so DRAFT is stale and the red dots are wrong.

### P5.1 — FIX: promote the L1 Gaṇita assets to CURRENT
This is the same DRAFT→CURRENT flip the L2 seal performs at B5 — appropriate now that L1 is sealed.
- Set `catalog_status: 'CURRENT'` on all 9 (or 10, incl ga_chart_service) `ga_*` rows in
  `asset_registry_seed.ts` (explicit per-row, do NOT rely on the layer default — make it intentional
  and visible). Re-apply the seed to prod with the post-apply readback asserting the ga_ rows now
  read CURRENT.
- Leave L2–L5 (`bo_/ka_/ph_/mi_`) as DRAFT — those layers are NOT sealed; their red dots are correct
  (they genuinely are draft/unbuilt). Only L1 promotes here.
- If asset_registry was hand-patched in prod rather than seed-authoritative, use a tiny UPDATE
  migration (fresh number) instead — verify which is authoritative first (same caveat as P3).
- Acceptance [verify-against: prod]: every ga_ asset reads `catalog_status='CURRENT'`; with the data
  plane up, all Gaṇita assets show a GREEN dot (lit + CURRENT), no red; L2–L5 assets remain DRAFT
  (correctly amber/red as draft). The StatusDot title reads "CURRENT · healthy" for ga_ assets.

### P5.2 — Governance note
Promoting L1 → CURRENT is a governance statement (L1 is production-sealed). It is consistent with
L1_GANITA_CLOSURE. Record the promotion in CURRENT_STATE at the next session close. Do NOT promote
any layer that is not sealed.

---

## §5 — Out of scope
- No change to the stats-route timeout/error LOGIC (it is correct — it honestly reports a down plane).
- No L2 Bodha / B5 (deferred until L0/L1 cockpit reads clean).
- No re-flip of the bilingual layout for non-service assets (Sanskrit-primary is the intended design;
  only the two Devanagari service rows are romanized to match).
- The `/cockpit` governance landing page (stale GCS) remains separately deferred.

## §6 — Note for the record (why this looked alarming)
Four of the five symptoms are NOT new bugs: two are owed-migration debt (229/231) that the prior
closure brief flagged as operator-apply-pending, one is a down data plane (operator), and one is a
cosmetic seed-script inconsistency. The cockpit logic itself (count_sql truth, floor-not-gate,
service pill, per-asset timeout) is sound. The lesson: a flapping Cloud SQL proxy makes a CORRECT
cockpit look broken — P1.1 adds the resilience so a transient blip reads as "reconnecting", not
"FAILED", removing the false alarm.

---
*End of COCKPIT_DATAPLANE_AND_DISPLAY v1.0. Six symptoms, FOUR causes: (1) data plane down/flapping
→ conn_timeout red dots on the timed-out assets (operator: start proxy+sidecar; P1.1: amber
"reconnecting" not red FAILED); (2) migrations 229 (throughput) + 231 (floor reset) never applied →
"build-state stale" + short bars (P2: apply); (3) two service engines seeded in Devanagari → romanize
to Pañcāṅga Gaṇanā / Druk Ephemeris (P3); (4) EVERY Gaṇita asset is catalog_status=DRAFT (seed
default for non-L0) → StatusDot forces red even on LIVE-with-data assets; L1 is sealed so promote
ga_* DRAFT→CURRENT (P5). The cockpit logic is correct; this is data-plane + two owed migrations +
one seed-romanize + one DRAFT→CURRENT promotion.*
