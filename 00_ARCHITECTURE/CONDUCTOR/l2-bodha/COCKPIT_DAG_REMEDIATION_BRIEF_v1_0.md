# Nirmāṇa Cockpit + DAG — Remediation (red dots · stale badges · open DAG rings)

**Paste as the prompt in Claude Code (Antigravity). Closes the cockpit/DAG visual gaps the native observed on the
Nirmāṇa build tracker. Diagnosed live (Chrome MCP on the cockpit + the stats route + ArmillaryGraph code). Data
plane = prod via Cloud SQL proxy (5433). Verify the Cloud Run revision matches the merge SHA before any prod
cockpit probe (the phantom-bug trap).**

---

## THE DIAGNOSIS (all three symptoms → ONE root cause)
**Root cause: `asset_throughput` build-state ledger is STALE for several built assets** — count_sql confirms rows
ARE present, but the throughput row was never marked `lit`/fresh when the autonomous swarm wrote the data. The
stats route flags this as `build_state_stale = true` (rows present BUT asset_throughput says stale/dormant/absent
— stats/route.ts ~line 52). This single flag surfaces three ways:
1. **RED DOTS on every Bodha asset** — the dot is semantically `CURRENT · healthy` (confirmed in the DOM), but its
   COLOUR is driven by build_state_stale → renders amber/red as a "ledger behind" warning despite the asset being fully built.
2. **STALE BADGES on bo_drishti + bo_anveshana** — the same flag shown as an explicit badge on the two assets whose
   throughput row is most clearly stale. (bo_anveshana shows 7,215/5,770 — over-floor, fine — but throughput-stale.)
3. **OPEN DAG OUTER RINGS** — ArmillaryGraph `aggregate()`: `builtFrac = built/total` where `built` counts only
   `state==='lit'`; and `state = stale ? 'stale' : 'lit'` means ANY stale asset makes the layer aggregate 'stale' +
   excludes stale assets from `built`. So Brahmagyan 20/22, Gaṇita 16/17, AND Bodha "10/10 built but ring open"
   (all 10 have rows, but several carry build_state_stale → built<10 → ring < 100%).
**NOT a glitch, NOT by design — a real throughput-ledger sync gap** (the known L1 "count_sql shows rows but
asset_throughput says stale" failure mode; related to the orchestrator throughput-write not landing cleanly when
the autonomous writers committed early — see the Vimarśaka conn.commit finding).

## VERIFIED STATE (live, 2026-06-20)
Bodha layer, chart 482012f1 — all 10 assets LIVE with full/over-floor bars, all dots `CURRENT · healthy`:
laksana 66,738/66,738 · karanajala 360/300 · bimba 140/140 · samskara 66,738/66,738 · sangati 100/84 ·
upaya 180/180 · samvada 5/5 · pramana_mapa 1/1 · **drishti 60/60 (STALE badge)** · **anveshana 7,215/5,770 (STALE badge)**.
DAG: Bodha shows "10/10 built" in header but the outer ring is not closed.

## PART A — THE DATA FIX (the real cause — re-sync asset_throughput) → fixes dots + badges + rings
For every bo_* asset (and any Brahmagyan/Gaṇita asset showing the same stale-despite-built state), where count_sql
confirms rows > 0, mark the throughput ledger LIT/fresh so build_state_stale clears.
1. **Diagnose which rows are stale:** for chart 482012f1, list `asset_id, state, last_built_at` from
   `asset_throughput` for the bodha assets; identify those whose `state != 'lit'` (or last_built_at stale) despite
   count_sql > 0. Expect: at least bo_drishti + bo_anveshana (the badged two); confirm whether the red-dot assets
   (all of them) are also throughput-stale or only colour-flagged.
2. **Re-sync:** UPDATE asset_throughput SET state='lit', last_built_at=now() (or re-run the orchestrator's
   throughput-write path) for the confirmed-built-but-stale assets. Use the orchestrator's own throughput-write if
   one exists (preferred — it's the canonical writer); otherwise a surgical UPDATE scoped to (chart_id, asset_id).
   Do NOT fabricate — only mark lit where count_sql actually returns rows > 0.
3. **Extend to Brahmagyan (20/22) + Gaṇita (16/17):** apply the SAME diagnosis — which specific assets are
   stale-despite-built (or genuinely 0-rows-correct like ga_prashna). For genuinely-built ones, re-sync; for
   legitimately-empty ones (e.g. ga_prashna on a natal chart = correct 0), confirm they're handled as 'lit'
   (writer ran, 0 rows by design) NOT stale — that's the §N.4 rule (stats line ~29-31).
4. **VERIFY (prod + cockpit):** after re-sync — every bo_ dot green (`CURRENT · healthy`, no amber); zero stale
   badges; the Bodha DAG ring CLOSED (builtFrac=1.0); Brahmagyan/Gaṇita rings reflect their true built/total.

## PART B — DAG built-fraction ROBUSTNESS (so "X/X built" and the ring AGREE) → prevents recurrence
The header "10/10 built" (rows-present) and the ring (lit-only) use DIFFERENT counts — internally inconsistent.
Fix `ArmillaryGraph.aggregate()` (platform/src/lib/components/cockpit/v2/ArmillaryGraph.tsx ~line 60-67):
- **Count `build_state_stale` (rows present, ledger behind) as BUILT for `builtFrac`** — so the ring closes when the
  DATA is genuinely there. Keep the amber tint / soft badge as the "ledger-stale" signal, but do NOT treat
  rows-present-but-ledger-stale as un-built in the ring arc.
- Concretely: `built = assets.filter(a => a.state === 'lit' || a.build_state_stale).length` (or treat
  build_state_stale assets as lit-equivalent in the aggregate), and the layer `state` shows 'stale' as a soft
  warning, not as a reason to open the ring. Then "10/10 built" ⇒ ring closed, always consistent.
- This makes the DAG TRUTHFUL: ring completeness = data presence (the §N.4 "count_sql is authoritative" principle,
  applied to the visualization). Add/extend the ArmillaryGraph test to assert: a layer with all assets rows-present
  (even if throughput-stale) renders a CLOSED ring.

## SEQUENCE + LANDING
Part A (data re-sync — fixes the live cockpit immediately) → Part B (UI robustness — prevents recurrence on the
next build) → commit on a branch off main → CI green → verify the cockpit visually (localhost:3000 against prod
data, or the deployed URL with the revision confirmed). Update the relevant close-doc / OPEN_ITEMS with the fix.

## HARD STOPS
- A bo_ count_sql returns 0 despite rows in the table → the count_sql/$1-binding is wrong → fix the count_sql, do
  NOT mark it lit to mask it.
- Marking an asset 'lit' that genuinely has 0 rows AND no writer ran → STOP (that would be fabricating build state).
- prod ≠ merged SHA when probing the cockpit → wait for the deploy.

**Begin: Part A — diagnose asset_throughput staleness for 482012f1, re-sync the built-but-stale assets, verify dots
green + rings closed. Then Part B. Go.**
