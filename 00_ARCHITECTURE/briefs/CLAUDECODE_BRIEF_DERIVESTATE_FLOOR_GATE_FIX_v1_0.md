---
artifact: CLAUDECODE_BRIEF_DERIVESTATE_FLOOR_GATE_FIX_v1_0.md
canonical_id: DERIVESTATE_FLOOR_GATE_FIX_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (Chrome-MCP live diagnosis, proxy up) 2026-06-12
authored_for: Claude Code in Antigravity IDE
diagnosis_method: Chrome MCP against localhost:3000/cockpit/atlas (proxy live) — read rendered L0 states + the deriveState source
data_plane: prod via Cloud SQL proxy
key_finding: The 4 L0 assets still showing `building` is NOT missing data and NOT stale throughput — it's deriveState GATING `lit` on `actualRows >= target_floor`, while those 4 assets have target_floor set ABOVE their achieved count. This violates the project's own "floors are aspirational, NOT gates" rule.
---

# deriveState Floor-Gate Fix (L0 stuck-`building`) — Fix Brief v1.0

## §0 — The live finding (proxy up, Atlas rendering)
L0 · Brahmagyan shows **8/14 lit**. The 4 not-lit (excluding the 2 service assets which are correctly
service_ok) are all `(building)` WITH full data:
- bg_concordance — 720 rows (building)
- bg_remedies — 266 rows (building)
- bg_text_index — 361 rows (building)
- bg_yogas — 175 rows (building)
Every other L0 asset is lit. Data is present; these render `building`.

## §1 — ROOT CAUSE (in the code, not a deployment gap)
`platform/src/app/api/cockpit/stats/route.ts` `deriveState()` (L25-28):
```js
if (actualRows != null && actualRows > 0) {
  if (!asset.target_floor || actualRows >= asset.target_floor) return 'lit'
  return 'building'   // ← rows present but BELOW target_floor → "building"
}
```
The reconcile DOES override throughput (good) — but it then GATES `lit` on `actualRows >=
target_floor`. The 4 stuck assets have **target_floor set ABOVE their achieved count** (e.g. bg_yogas:
175 achieved but floor was the old aspiration ~250; the corpus-derived assets similarly have
aspirational floors > achieved). So `actualRows < target_floor` → renders `building` forever.

**This directly violates CLAUDE.md §N.4 / the floors policy: "floors are aspirational, NOT gates;
target_floor = achieved count after build; never gate on a floor."** ([[feedback-floors-are-aspirational-not-gates]])
deriveState is using target_floor as a GATE — the exact anti-pattern the policy forbids. (Migration
229 flipped the throughput record, but deriveState now ignores throughput and uses the floor
comparison, so 229 was necessary-but-insufficient.)

## §2 — FIX (two parts — both, per the floors policy)

### Fix A — deriveState: floors NEVER gate `lit` (the principled fix)
Change the lit determination so **any asset with actualRows > 0 that is not ACTIVELY building is
`lit`**, regardless of target_floor:
```js
if (actualRows != null && actualRows > 0) {
  // floors are aspirational, NOT gates (§N.4) — data present = lit.
  // Only an ACTIVE in-progress build (throughput building AND rows climbing) is 'building'.
  return 'lit'
}
```
Keep the genuine `building` case for assets that are *actually mid-build with zero rows yet*
(actualRows == 0 AND throughputState === 'building'). The "rows present but under an aspirational
floor" case must be `lit`, optionally with a "below target_floor" informational badge (NOT a
building/incomplete state). Do NOT treat under-floor as incomplete — that's the gate the policy bans.

### Fix B — correct the 4 target_floors to achieved counts (data hygiene per the policy)
Per the floors policy, target_floor should EQUAL the achieved count after build. Reset the 4 assets'
target_floor to their actual current counts (bg_concordance 720, bg_remedies 266, bg_text_index 361,
bg_yogas 175) — and audit ALL bg_ assets for any other target_floor > actual_rows (same latent bug).
Surgical migration, fresh number (NOT a duplicate — check the ledger; we've had 223/227 collisions).

## §3 — Acceptance [verify on localhost:3000 + prod]
- [ ] All 4 L0 assets (bg_concordance/remedies/text_index/yogas) render `lit` in the Atlas + cockpit.
- [ ] deriveState: actualRows>0 + not-actively-building → lit, INDEPENDENT of target_floor; under-floor shows an informational badge, not `building`.
- [ ] No bg_/ga_ asset with rows>0 shows `building`/incomplete due to an aspirational floor.
- [ ] target_floors reset to achieved counts for the 4 (+ any others found above actual); migration has a fresh unused number.
- [ ] Genuine cases still correct: 0-rows-mid-build → building; 0-rows-no-build → dormant; service assets → service_ok; count error → error.
- [ ] No data rebuild (data is present — this is a display-logic + floor-value fix only).

## §4 — Why this kept recurring (note for the record)
The cockpit-truth fixes have each closed one source-of-untruth: dormant (PROGRESSBAR_RECONCILE),
then building/stale via throughput (COCKPIT_INCOMPLETE_BARS_FIX). But deriveState still had ONE
remaining gate — the target_floor comparison — which this brief removes. After this, `lit` depends
ONLY on "has data, not actively building," never on a floor. That should be the FINAL source of the
"incomplete over complete data" class.

## §5 — Out of scope
No data rebuild; no count_sql change; no re-run of the assets (data present). Display-logic +
target_floor values only.

---
*End of DERIVESTATE_FLOOR_GATE_FIX v1.0. The 4 L0 `building` assets have data but a target_floor set
ABOVE achieved, and deriveState gates `lit` on rows>=floor — violating "floors aren't gates." Fix:
floors never gate lit (rows>0 + not-actively-building = lit) + reset the 4 floors to achieved. Closes
the last remaining cockpit-truth gate. No data rebuild.*
