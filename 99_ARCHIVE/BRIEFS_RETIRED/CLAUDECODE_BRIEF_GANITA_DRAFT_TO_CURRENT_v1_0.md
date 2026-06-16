---
artifact: CLAUDECODE_BRIEF_GANITA_DRAFT_TO_CURRENT_v1_0.md
canonical_id: GANITA_DRAFT_TO_CURRENT_BRIEF
version: 1.0
status: COMPLETE
authored_by: Cowork (Chrome-MCP live re-verify post-migrations-229–235) 2026-06-16
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
data_plane: ALWAYS prod via Cloud SQL proxy (port 5433)
diagnosis_surface: /clients/482012f1-710e-4a25-994a-93821f5871aa/build (verified live, zoomed)
key_finding: >
  COCKPIT_DATAPLANE_AND_DISPLAY P1–P4 are confirmed live (data plane up, bars full, services green +
  romanized, no build-state-stale). But **P5 was NOT executed** — every Gaṇita asset still shows a
  RED dot despite being LIVE with full data (verified at zoom: Graha-sthāna/Varga/Daśākrama/Balatva
  all red-orange, not amber). Cause: ga_ assets are still catalog_status='DRAFT', and StatusDot
  (AssetRow.tsx ~L93) forces red on DRAFT regardless of lit state. Migrations 229–235 fixed DATA
  state; none touched catalog_status. This brief is the standalone P5.
inherited_non_negotiables: surgical migration, FRESH unused number (236+ — 229–235 now consumed); seed is co-source; no audience tier.
---

# Gaṇita DRAFT → CURRENT promotion — Fix Brief v1.0 (the outstanding P5)

## §0 — Confirmed live state (post 229–235)
On the native build cockpit, with the data plane UP:
- L0 Brahmagyan: 12 data assets lit, 2 service engines GREEN + romanized (Pañcāṅga Gaṇanā / Druk Ephemeris). ✓
- L1 Gaṇita: all bars full + LIVE (Varga 21,635/21,635, Daśākrama 536,471/536,471, Balatva 2,184/2,184, Sūkṣmabindu 8,055/8,055, Graha-sthāna 530/50, …). ✓ data
- **BUT every Gaṇita asset still shows a RED dot** (zoom-confirmed red-orange, not amber). ✗

## §1 — Root cause (catalog_status, NOT data state)
- `StatusDot` (AssetRow.tsx ~L93): `isRed = state==='error' || state==='not_migrated' || isDraft`,
  `isDraft = catalog_status === 'DRAFT'`. **DRAFT ⇒ red dot, even when the asset is lit.**
- Seed (asset_registry_seed.ts ~L1302): `catalogStatus = asset.catalog_status ?? (asset.layer === 'brahmagyan' ? 'CURRENT' : 'DRAFT')`.
  No ga_ row sets catalog_status ⇒ all default to DRAFT. The L0 service engines are CURRENT (explicit), which is why they went green; the ga_ assets cannot until promoted.
- L1 Gaṇita is SEALED (L1_GANITA_CLOSURE_v1_0) + fully built ⇒ DRAFT is stale; the red dots are wrong.

## §2 — FIX: promote the Gaṇita assets DRAFT → CURRENT
This is the same DRAFT→CURRENT flip the L2 seal does at B5 — correct now that L1 is sealed.

### Fix A — seed (source for catalog_status)
Set `catalog_status: 'CURRENT'` EXPLICITLY (per-row, not via the layer default) on all 9 ga_ rows in
`asset_registry_seed.ts`:
`ga_positions, ga_vargas, ga_dashas, ga_strength, ga_sensitive, ga_panchanga, ga_sade_sati,
ga_tajaka, ga_structural`.
ALSO promote the Gaṇita **service** asset (the cockpit shows "10 assets" for Gaṇita; the 10th is the
chart service — `ga_chart_service` or equivalent). Locate it (it may be seeded outside
asset_registry_seed.ts) and set catalog_status='CURRENT' so the whole layer is consistent.

### Fix B — migration (prod truth — the UPSERT in the seed reads EXCLUDED.catalog_status, so a re-seed
should propagate; but since prod was hand-patched via 229–235, apply a surgical migration to be safe)
`236_ganita_catalog_current.sql` (FRESH number — verify 236 free; 229–235 are consumed):
```sql
UPDATE asset_registry
SET catalog_status = 'CURRENT'
WHERE layer = 'ganita';   -- or: asset_id LIKE 'ga\_%' ESCAPE '\'
```
(Use whichever column the registry actually keys layer on — confirm `layer='ganita'` is the live
value before running; if the column is `layer_index='L1'`, key on that.)

### Fix C — DO NOT promote unsealed layers
Leave L2 Bodha / L3 Kāla / L4 Phala / L5 Mīmāṃsā (`bo_/ka_/ph_/mi_`) as DRAFT — they are NOT sealed;
their red/amber dots are CORRECT. Only L1 promotes here.

## §3 — Acceptance [verify-against: prod, proxy up]
- [ ] All 9 ga_ data assets + the Gaṇita service asset read `catalog_status='CURRENT'` in asset_registry.
- [ ] On the build cockpit, every Gaṇita asset shows a **GREEN** dot (lit + CURRENT) — zero red dots in the Gaṇita panel.
- [ ] StatusDot title for a ga_ asset reads "CURRENT · healthy".
- [ ] L2–L5 assets remain DRAFT (their dots stay draft-colored — NOT promoted).
- [ ] Brahmagyan unchanged (still 12 lit + 2 green services).

## §4 — Governance
Record the L1 DRAFT→CURRENT promotion in CURRENT_STATE at next session close (it is a production-seal
governance statement, consistent with L1_GANITA_CLOSURE). See [[cockpit-draft-status-forces-red-dot]].

---
*End of GANITA_DRAFT_TO_CURRENT v1.0. The one outstanding item from COCKPIT_DATAPLANE_AND_DISPLAY:
P1–P4 landed, but P5 (catalog_status promotion) did not — so all Gaṇita assets are LIVE-with-data yet
still red because they are DRAFT. Fix: set ga_* (+ the Gaṇita service) catalog_status='CURRENT' in
seed + a fresh migration (236). L2–L5 stay DRAFT. Then the Gaṇita dots go green.*
