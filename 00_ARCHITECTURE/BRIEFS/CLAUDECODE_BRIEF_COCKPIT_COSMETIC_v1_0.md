# Cockpit cosmetic polish — 4 changes (paste into Claude Code / Antigravity)

**Scope:** purely cosmetic, two files, no logic/data change. The v2 cockpit asset list
(`/clients/[id]/nirmana` → CockpitShell → DataAssetsView → LayerPanel → AssetRow). Branch-agnostic — fine on a
small `fix/cockpit-cosmetic` branch OR folded into the open `fix/l0-closure-integrity`. No migration, no seed.

Files:
- `platform/src/lib/components/cockpit/v2/LayerPanel.tsx`
- `platform/src/lib/components/cockpit/v2/AssetRow.tsx`

Grid is shared between the header row (LayerPanel) and each data row (AssetRow):
`gridTemplateColumns: 'minmax(0,42%) minmax(0,28%) minmax(0,14%) minmax(0,16%)'` = Asset · Progress · Last built · Actions.

---

## CHANGE 1 — Order services BEFORE data assets within each layer

**File:** `LayerPanel.tsx`. The body renders `assets.map(...)` (~line 229) in array order. Sort so
`asset_type === 'service'` rows come first, data assets after, each group preserving its existing relative order.

Just before the `.map`, derive a sorted list (stable sort — services first):
```tsx
const orderedAssets = [...assets].sort((a, b) => {
  const aSvc = a.asset_type === 'service' ? 0 : 1
  const bSvc = b.asset_type === 'service' ? 0 : 1
  return aSvc - bSvc   // stable: equal keys keep original order
})
```
Then map over `orderedAssets` instead of `assets`. (Do NOT change the `assets.length`/`totalRows` calcs — only
the render order.)

---

## CHANGE 2 — Service "green" pill same dimension as the data-asset progress bar

**File:** `AssetRow.tsx`, `ServiceHealthPill` (~lines 52–77). Service rows render a small inline pill in the
Progress column where data rows render the full-width `AssetProgressBar` — that's the size mismatch (the green
looks smaller than the other progress fills). Make the service health indicator occupy the **same block
dimension** as `AssetProgressBar` so the green sits in a bar of equal height and full column width.

Match the AssetProgressBar's outer dimensions. Inspect `AssetProgressBar.tsx` for its track height (e.g. the
bar wrapper height/border-radius/full-width) and give the service indicator the same. Concretely: make the pill
wrapper a full-width block of the same height as the progress track, with the green as its fill — e.g. wrap the
existing pill in a container `style={{ width: '100%' }}` and set the pill (or a new fill element) to the same
height as the AssetProgressBar track (read the exact px from that component, don't guess — match it), full
width, same border-radius. The GREEN/amber/red color logic stays exactly as-is (isGreen/isRunning/isError);
only the geometry changes so it's the same size as the other progress bars. The error sub-text line below stays.

Acceptance: a service row's green bar and a data row's lit progress bar are visually the same height and width
in the Progress column.

---

## CHANGE 3 — Center all 4 column headers

**File:** `LayerPanel.tsx`, the column-header grid (~lines 224–227). Currently: Asset/Progress/Last built have
no `textAlign` (default left); Actions is `textAlign:'right'`. Center ALL FOUR:
```tsx
<div style={{ textAlign: 'center' }}>Asset</div>
<div style={{ textAlign: 'center' }}>Progress</div>
<div style={{ textAlign: 'center' }}>Last built</div>
<div style={{ textAlign: 'center' }}>Actions</div>
```
(Native confirmed: center the HEADERS only — the CELL contents stay as-is, EXCEPT the Last built column whose
whole column centers per CHANGE 4. Note for awareness: the Asset header will now sit centered above its
left-aligned two-line name cells — this is the intended result.)

---

## CHANGE 4 — Last built: center the ENTIRE column (header + every cell)

Header already handled in CHANGE 3 (Last built → center). Now the **cell**:

**File:** `AssetRow.tsx`, the "Last built" cell (~lines 214–220). Add `textAlign: 'center'` to its style:
```tsx
<div
  style={{ fontSize: '11px', color: 'var(--on-dark-faint)', fontFamily: 'var(--mono-stack)', textAlign: 'center' }}
  title={stat?.last_built_at ? formatDateTime(stat.last_built_at) : 'never built'}
>
  {stat?.last_built_at ? (formatRelative(stat.last_built_at) ?? '—') : '—'}
</div>
```
Acceptance: the Last built header AND every Last built value (relative time or '—') are center-aligned in the
column.

---

## DO NOT TOUCH (native: "rest all the way it is")

- Asset name cell content (status dot + Sanskrit/English two-line) stays LEFT-aligned.
- Progress column cell content stays as-is except CHANGE 2's service-pill geometry.
- Actions cell stays right-aligned (`justify-end`).
- No change to colors, logic, data, state derivation, the layer header row, or the grid column widths.

---

## VERIFY

Run the cockpit on localhost (`--webpack`, per the Turbopack CPU-thrash defensive default), open
`/clients/482012f1/nirmana`, expand Brahma Jñāna:
1. Services (bg_ephemeris_engine, bg_panchanga) appear ABOVE the data assets.
2. A service's green bar is the same height + width as a data asset's progress bar.
3. All 4 column headers are centered.
4. Last built header + all its cells are centered.
5. Everything else unchanged.
Take a screenshot to confirm. Existing AssetRow/LayerPanel tests stay green (update snapshot assertions only if
a test pins the old left-alignment / order — adjust the test to the new intended state, don't weaken it).
