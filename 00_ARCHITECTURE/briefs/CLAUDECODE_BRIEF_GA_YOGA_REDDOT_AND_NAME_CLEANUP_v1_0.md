# ga_yoga red-dot + asset-name (id-suffix) cleanup (paste into Claude Code / Antigravity)

**Read CLAUDE.md §C first.** Two cockpit fixes for L1 Gaṇita, both **DATA drift (prod `asset_registry` diverged
from the clean seed), NOT a component bug** — code-verified via the live `/api/cockpit/registry` endpoint. The
`AssetRow` component renders `english_name` verbatim and colors the StatusDot from `catalog_status` — both are
behaving correctly; the stored DB values are wrong for two L1 rows.

## STANDING RAILS
surgical migration (≥ next free above the current max — CONFIRM next-free), ledger-reconciled; seed-consistency
(the seed must MATCH the post-fix DB so a reseed doesn't reintroduce drift); endpoint-verify via
`/api/cockpit/registry` (the route that feeds the cockpit name + dot), not DB-only; FROZEN contract untouched
(this is registry metadata, no writer/orchestrator change); only metadata columns touched.

---

## FINDING (code + endpoint verified 2026-06-18)

`/api/cockpit/registry` live values:
- `ga_yoga`: `english_name="Yoga Firings (ga_yoga)"`, `catalog_status="DRAFT"` → renders red dot + bracketed id.
- `ga_transit_anchors`: `english_name="Transit Natal Anchors (ga_transit_anchors)"`, `catalog_status="CURRENT"`
  → bracketed id (no red dot, since CURRENT).

`AssetRow.tsx`: StatusDot is red when `catalog_status==='DRAFT'` (or not_migrated/error). `english_name` is
rendered as-is (no component-side id suffix). Seed (`asset_registry_seed.ts`) is CLEAN: ga_yoga
`english_name:'Yoga Firings'`, `catalog_status:'CURRENT'`; ga_transit_anchors `english_name:'Transit Natal
Anchors'`. **So prod DB drifted from seed** — a migration or manual write injected the `(id)` suffix and left
ga_yoga at DRAFT.

Full-registry sweep (62 assets):
- **Bracketed english_name: exactly 2** — `ga_yoga`, `ga_transit_anchors`. (No others.)
- **DRAFT rows: 25** — but 23 are CORRECT (all `bo_*`/`ka_*`/`ph_*`/`mi_*` L2-L5 assets are legitimately DRAFT;
  their red dot is honest — not-yet-built). The only WRONG DRAFTs are two BUILT L1 assets:
  `ga_yoga` (lit, 5 rows) and `ga_prashna` (lit, 0-valid-natal, activated this session). Both should be CURRENT.

---

## FIX 1 — red dot: flip the two mis-DRAFT'd built L1 assets to CURRENT

Surgical migration: `UPDATE asset_registry SET catalog_status='CURRENT' WHERE asset_id IN ('ga_yoga',
'ga_prashna');`
- **ga_yoga:** seed already says CURRENT — pure drift fix.
- **ga_prashna:** activated this session (PR #301), lit/0-valid-for-natal — it is a real working asset, so CURRENT
  is correct (0 natal rows is by-design, not draft-ness). CONFIRM the seed says CURRENT for ga_prashna; if it
  says DRAFT, fix the seed too (it should be CURRENT).
- **DO NOT touch the L2-L5 DRAFTs** (`bo_*`/`ka_*`/`ph_*`/`mi_*`) — those are correctly DRAFT (unbuilt layers);
  their red dot is honest and will clear when each layer is built.

## FIX 2 — strip the `(id)` suffix from the two english_names

Same migration: set `english_name='Yoga Firings'` for ga_yoga and `english_name='Transit Natal Anchors'` for
ga_transit_anchors. CONFIRM the seed already has the clean values (it does per the read) so seed+DB agree;
no seed change needed beyond verification. (If any seed row DOES carry a bracketed name, clean it.)

**Guard:** grep the migrations history for whatever wrote the bracketed `english_name` / DRAFT status, so we
know the drift source and it isn't re-applied by a later replay. If a prior migration sets these bracketed
values, supersede it (don't just patch over it silently).

---

## VERIFY (endpoint, paste evidence)
- Migration applied to prod, ledger-reconciled (SHA), next-free number confirmed.
- `/api/cockpit/registry` now shows: ga_yoga `english_name="Yoga Firings"`, `catalog_status="CURRENT"`;
  ga_transit_anchors `english_name="Transit Natal Anchors"`, `catalog_status="CURRENT"`; ga_prashna
  `catalog_status="CURRENT"`.
- Cockpit visual: ga_yoga dot GREEN (no longer red); both rows show clean names with NO `(id)` suffix.
- Confirm the 23 L2-L5 DRAFT rows are UNCHANGED (still DRAFT — correct).
- Seed ↔ DB parity confirmed for all touched rows.
- FROZEN contract untouched; no component change (AssetRow was correct).

**Both issues are prod data-drift from the clean seed — a metadata migration fixes them with zero code/component
change. Low-risk; do not over-reach into the legitimate L2-L5 DRAFT rows.**
