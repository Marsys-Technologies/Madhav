---
artifact: CLAUDECODE_BRIEF_COCKPIT_POLISH_R2_v1_0.md
canonical_id: COCKPIT_POLISH_R2_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-10 — diagnosed live against prod via Chrome MCP + source
authored_for: Claude Code in Antigravity IDE
delivery_model: 1 branch, single PR, plan-then-execute
scope: Cockpit Nirmāṇa visual + service-rendering fixes (8 native-reported issues)
---

# Cockpit Polish R2 — Service Rendering + Visual Fixes — Execution Brief v1.0

## §0 — How this was diagnosed (don't re-investigate from scratch)

Observed live on `https://madhav.marsys.in/clients/482012f1-…/build` via Chrome MCP, cross-read
against source. The registry API **already returns correct data** — `bg_panchanga`,
`bg_ephemeris_engine`, `ga_pyjhora_engine` all have `asset_type:'service'`, `storage_type:'service'`,
`count_sql:null`, `target_table:null`, and a populated `health_probe`. **Every issue below is
frontend/data presentation — none is a registry-data problem.** Files are already located; line
numbers cited. Verify them, then fix.

## §1 — Root cause of the "missing_table / × degraded" service errors (issues 1 + 2)

**File: `platform/src/app/api/cockpit/stats/route.ts`.** `fetchAssetStats` lines 56–67:
```ts
if (!asset.count_sql) {
  return { ... error: 'missing_table', state: 'error' as const, ... }
}
```
Service assets have `count_sql: null` **by design** → they always hit this → `deriveState` (line 16
`if (error) return 'error'`) → `AssetRow`'s `ServiceHealthPill` renders `× degraded` + `missing_table`.
The stats route's `RegistryAsset` SELECT (line 190) doesn't even fetch `asset_type`, so it can't tell
a service from a table-less data asset.

**Fix:**
1. Add `asset_type` (and `health_probe`) to the `RegistryAsset` interface + the SELECT at line 190–195.
2. In `fetchAssetStats`, BEFORE the `!count_sql` guard: if `asset.asset_type === 'service'`, return a
   **service-health stat** instead of an error — `actual_rows: null`, `error: null`, and a new
   `state: 'service_ok'` (or reuse `'lit'` to mean "healthy"). Do NOT run any SQL for services.
3. **Health probe (optional but correct):** the registry carries a `health_probe` (e.g. panchanga's
   FORENSIC expected angas at 1984-02-05). If wiring the probe is in scope, run it server-side and
   return `service_ok` on pass / `error` on fail. If NOT in this pass, default services to
   `service_ok` (they're registered + CURRENT) and leave probe execution as a follow-up — do NOT
   show them as errored. **Minimum bar for this brief: services never show `× degraded`/`missing_table`
   when they are correctly registered.**
4. `deriveState` (line 9): add a branch so `asset_type==='service'` short-circuits to the service
   state and never falls through to the `if (error)`/`dormant` data-asset logic.

**File: `platform/src/lib/components/cockpit/v2/AssetRow.tsx`.** The `ServiceHealthPill` (lines 32–76)
already exists and the branch at line 142 already routes services to it. Once the stats route stops
returning `error:'missing_table'`, the pill's `isError` goes false and it shows `● GREEN`. Confirm the
pill's state mapping (lines 41–48) reads the new `service_ok`/`lit` as green. Adjust the `derivedState`
computation (lines 84–87) so a service with no rows but healthy resolves to green, not `dormant`.

**AC:** the 3 service rows (Panchanga Engine, Ephemeris Engine, PyJHora Engine) show a green health
pill, no `missing_table`, no `× degraded`. `[verify-against: prod]`

## §2 — Devanagari → roman transliteration on the two service names (issue 7)

The two L0 service rows store `sanskrit_name` in **Devanagari** while every other asset uses roman
IAST: `bg_panchanga.sanskrit_name = 'पञ्चाङ्ग गणना'`, `bg_ephemeris_engine.sanskrit_name = 'दृक्
एफिमेरिस'`. (Confirmed via registry API.) Every sibling uses roman: Graha-sphuṭa, Sāraṇi, Śāstrapāṭha,
Anukrama, etc.

**Fix (data, migration):** author `platform/supabase/migrations/<NEXT>_service_asset_name_iast.sql`
updating the two rows to roman IAST consistent with the house style:
- `bg_panchanga` → `Pañcāṅga Gaṇanā` (Panchanga Engine)
- `bg_ephemeris_engine` → `Dṛk Ephemeris` (or `Dṛk Sāraṇi` if the house prefers a fully-Sanskrit
  second word — match the convention used by `bg_ephemeris`/`Graha-sphuṭa`; pick one and note it).
- Also check `ga_pyjhora_engine.sanskrit_name` — if it's non-roman or a raw id, give it a roman name
  too (e.g. `Janma-yantra` / keep "PyJHora Engine" as english_name).
Reversible down-block restoring the prior values. Idempotent. `[verify-against: prod]`

## §3 — Progress bar: deeper gold + readable centered text (issue 4)

**File: `platform/src/lib/components/cockpit/v2/AssetProgressBar.tsx`.** The `lit` fill is
`rgba(236,197,106,0.85)` — bright gold, near-white at the band, washing out the centered text
(`text-white/85`, line 66) and the whole bar reads as blinding.

**Fix:**
- `STATE_COLORS.lit.fill` → a **deeper/darker gold** (e.g. `rgba(176,137,58,0.9)` or
  `var(--gold-deep)` if one exists in globals.css — check first). `building`/`stale` similarly toned
  down one notch so the palette is cohesive, not neon.
- Numeric overlay (line 66): on the darker fill, make the centered text **higher-contrast** —
  e.g. `text-white` with a subtle dark text-shadow (`textShadow:'0 1px 2px rgba(0,0,0,0.6)'`) so it's
  legible over both the filled and unfilled portions. The native explicitly noted the centered text
  is "too white / not visible" against the bright/white background — the deeper gold + stronger text
  contrast fixes both at once.
- Keep the existing `--brand-*` token system ([[reference-design-system-canonical]]); prefer a token
  over a raw hex if globals.css already defines a deep-gold.

**AC:** bar reads as deep/dark gold, not blinding; centered `N / N` text is clearly legible. `[verify: prod screenshot]`

## §4 — "LIVE" pill crowding the right edge + empty Last Built (issue 3)

**Files: `AssetProgressBar.tsx` + `AssetRow.tsx`.**
- The state pill ("LIVE"/"NOT BUILT") is `absolute right-[2px]` **inside** the bar (lines 70–80),
  so the centered numeric text collides with it. Give the numeric overlay right-padding clear of the
  pill (e.g. the centering container reserves `pr-[64px]` so text centers in the *remaining* space),
  OR move the pill OUT of the bar into its own small column. Simplest: increase the numeric overlay's
  right padding so it never sits under the pill.
- **Last Built empty:** `AssetRow.tsx` lines 160–166 render `formatRelative(stat.last_built_at)`,
  falling back to `—`. It's empty because `asset_throughput.last_built_at` is null for never-built
  assets — that's correct (they haven't built). But the native flagged the text "almost sticking to
  the right edge of the progress bar": that's the **Progress column / Last-built column gap**. The grid
  is `42% / 28% / 14% / 16%` (line 95). The 28% Progress column has no right gutter before the 14%
  Last-built column. Add horizontal breathing room: bump the inter-column `gap` (line 97, currently
  `8px`) to ~`16px`, or widen the Last-built column and left-pad it. Ensure the bar's right edge and
  the Last-built text don't visually touch.

**AC:** "LIVE" pill no longer overlaps the numeric text; clear gutter between the progress bar and the
Last Built column. `[verify: prod screenshot]`

## §5 — Replace per-asset "CURRENT" text badge with a status circle (issue 5)

**File: `AssetRow.tsx` lines 113–132.** Currently renders the literal `catalog_status` ("CURRENT") as
a text chip next to every asset name — visually noisy, repeated on every row.

**Fix:** replace the text chip with a small **status dot** (a colored circle, ~8px) before or after the
name:
- **green** = `catalog_status==='CURRENT'` AND state lit/healthy
- **orange/amber** = building / stale / dormant-but-current
- **red** = error / not_migrated / catalog DRAFT
Keep `title={...}` tooltip carrying the words ("CURRENT · lit") for hover detail. This collapses the
repeated "CURRENT CURRENT CURRENT" column into a clean status-dot rail. Use the same color tokens as
the progress-bar states for consistency.

**AC:** no "CURRENT" text per row; a green/amber/red dot conveys status; tooltip preserves detail. `[verify: prod]`

## §6 — Layer header: asset-count + rows formatting (issue 6)

**File: `LayerPanel.tsx` lines 145–150.** Two adjacent `<span>`s — `{n} assets` (width 66px) and
`{rows} rows` (width 82px) — sit flush with only the flex `gap:6px`, so "14 assets 851,910 rows" reads
as one crowded run.

**Fix:** give them a proper structure — e.g. a small two-cell metric group with a separator (a thin
`·` or a vertical divider) and aligned label/value, OR stack them as `14 assets` / `851,910 rows` with
consistent right-alignment and a clear gap (~`16px`). Match the mono-stack styling but make the two
metrics visually distinct and consistently spaced across all six layer headers. `[verify: prod]`

## §7 — Sanskrit asset names: bigger + bolder (issue 8)

**File: `AssetRow.tsx` line 110.** Asset Sanskrit name is `text-[16px] ... font-serif text-[#C4942A]`
with default weight. The native finds it too small/faint.

**Fix:** bump to ~`text-[18px]`–`text-[19px]` and add weight (`font-medium` / `fontWeight:500`), keep
the serif + gold. The **layer-level** name (`LayerPanel.tsx` line 121, 22px) is fine as the hierarchy
anchor — keep asset names a clear step below it but more legible than now. Verify the two-line
(Sanskrit over English) row still aligns vertically after the size bump. `[verify: prod]`

## §8 — Branch, verification, rails

- Branch `fix/cockpit-polish-r2` off `main`. Single PR.
- **Localhost-first** ([[feedback-localhost-codeplane-prod-dataplane]]): iterate on `localhost:3000`
  (`next dev --webpack` per [[feedback-turbopack-1624-cpu-thrash]]); the data-plane (the name
  migration) writes to PROD via the Cloud SQL proxy — be deliberate about applying it.
- **NEXT_PUBLIC not involved** — these are server-component/API + CSS changes, no build-arg baking.
- After deploy, re-verify all 8 issues on prod with Chrome MCP at the canonical chart
  `482012f1-710e-4a25-994a-93821f5871aa`; confirm the running Cloud Run revision matches the merge SHA
  before drawing conclusions ([[feedback-verify-cloud-run-revision-before-chrome-probe]]).
- Mount-verification + parent-context tests for AssetRow/AssetProgressBar/LayerPanel changes.
- Merge-verify (`gh pr view N --json mergeCommit,state`) before "done" ([[feedback-pr-quality-gate-is-not-a-merge]]).

## §9 — Acceptance checklist (all `[verify-against: prod]`)

1. 3 service rows (Panchanga/Ephemeris/PyJHora engines) show green health pill — no missing_table, no × degraded.
2. The two (or three) service names render in roman IAST, consistent with sibling assets — no Devanagari.
3. Progress bar deep/dark gold, not blinding; centered N/N text clearly legible.
4. "LIVE" pill no longer overlaps numeric text; clear gutter before Last Built column.
5. Per-asset "CURRENT" text replaced by a green/amber/red status dot (tooltip retains words).
6. Layer header asset-count + rows properly structured/spaced across all 6 layers.
7. Asset Sanskrit names bigger + bolder, still aligned, hierarchy below layer name preserved.
8. No regression to the constellation DAG, build/refresh/clear actions, or the role-gated controls.
9. CI green; merge-verified.

---

*End of Cockpit Polish R2 brief v1.0. All 8 issues diagnosed live; root cause of the service errors is
stats/route.ts treating count_sql:null as missing_table — services need an asset_type-aware path.*
