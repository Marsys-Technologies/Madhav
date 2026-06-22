---
artifact: L4_PHALA_COCKPIT_SYNC_AUDIT_AND_FIX.md
canonical_id: L4_PHALA_COCKPIT_SYNC_AUDIT_AND_FIX
version: 1.0
status: READY — live Chrome-MCP audit of localhost:3000 cockpit + the Antigravity remediation
authored_by: Cowork 2026-06-22 (via Claude-in-Chrome against localhost:3000)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
runs_in: Antigravity (git merge + DB migrate + seed + build — needs the live dev DB + ephemeris)
---

# L4 Phala — Cockpit Out-of-Sync: Live Audit + Remediation

## §0 — Verdict (one line)
**The cockpit is NOT broken. localhost:3000 is serving `main`, which has ZERO L4 work** — so the
registry has the OLD 5 phala assets, the phala_ tables are empty, and nothing is built. The "9 not
showing / empty progress bars / out of sync" is a **deployment/data-state problem, not a UI bug.**

## §1 — What the live cockpit actually shows (Chrome-MCP evidence)
- Dashboard: Abhisek Mohanty = **"Partially built · 33%", "last updated 16d ago"** — stale, pre-L4.
- Nirmāṇa build panel: **Phala layer = "5 assets"** (not 9). All layers show "— rows". "This chart has
  not been built."
- `GET /api/cockpit/registry` → **200, clean, no console errors.** The cockpit renders correctly; the
  DATA is stale.
- Registry `data.assets` = **72 total**, byLayer: brahmagyan 22 · ganita 17 · bodha 10 · kala 12 ·
  **phala 5** · mimamsa 6.
- The 5 phala rows: `ph_nimitta, ph_muhurta, ph_sodhana, ph_pratikara, ph_suddha_sodhana` — all
  `catalog_status: DRAFT`. **MISSING: ph_sankrama, ph_pramana, ph_phaladesa, ph_rectification.**
- **These 5 carry the OLD rectification naming** (`ph_sodhana → phala_rectification`,
  `ph_suddha_sodhana → phala_rectification_best`) — a registry version PRE-DATING even PR #328.
- `GET /api/cockpit/stats?chartId=…` → 200. The 5 phala assets: `rows: 0, state: 'dormant', error: null`
  (tables exist + queryable but EMPTY). 20 assets lit (old L0/L1), 8 service_ok, 44 dormant.

## §2 — Root cause (code-confirmed against the mounts)
- **`main` has 0 of migrations 330–340** and its `asset_registry_seed.ts` has exactly the 5 stale ph_
  rows — **identical to what the live cockpit shows.** ⇒ localhost runs `main`.
- The L4 worktree (`MadhavL4Phala`, branch `feature/l4-phala-autonomous`, post-fix) has the correct
  **9 registry rows**, all pointing to tables with real migrations (verified):
  `ph_nimitta→phala_anchors, ph_muhurta→phala_muhurta, ph_pratikara→phala_mitigation,
  ph_sankrama→phala_sankrama, ph_pramana→phala_pramana, ph_phaladesa→phala_phaladesa,
  ph_sodhana→phala_sodhana, ph_suddha_sodhana→phala_suddha_sodhana, ph_rectification→phala_rectification.`
- **Nothing about the cockpit, layer panel, DAG, or stats route is broken.** They faithfully render a DB
  that was never given the L4 branch's migrations, seed, or build.

## §3 — The complete gap list (everything between "now" and "9 lit")
| # | Gap | Evidence | Severity |
|---|---|---|---|
| G1 | L4 branch not merged to main | main has 0 of migs 330–340 | BLOCKER |
| G2 | localhost DB never got migs 330–340 | phala_ tables exist but stats show rows:0 / the 4 new tables (sankrama/pramana/phaladesa/rectification) absent from registry | BLOCKER |
| G3 | Registry DB has 5 STALE rows (old rectification naming), not the 9 | live registry: 5 ph_ ids, ph_sodhana→phala_rectification | BLOCKER |
| G4 | asset_registry_seed never re-run against localhost DB | byLayer.phala = 5 | BLOCKER |
| G5 | No build ever run for 482012f1 on the L4 assets | all phala state='dormant', rows:0 | BLOCKER |
| G6 | Dashboard shows stale "33% / 16d ago" | will self-correct once G1–G5 done + rebuild | derived |
| G7 | (verify post-build) cockpit lit/dark + DAG render for 9 phala | can't confirm until data exists | verify-after |

> NOTE: G7 — I could NOT find a genuine cockpit/DAG rendering bug. The constellation DAG + layer panel
> read from the same registry+stats routes that work. If anything renders wrong AFTER the data lands,
> it's a real UI bug; right now there's nothing to render. Don't pre-fix a phantom (the clipping-hides-UI
> lesson). Re-audit visually after G1–G5.

## §4 — REMEDIATION (Antigravity Claude Code — paste this)

You are remediating the L4 Phala cockpit out-of-sync. ROOT CAUSE: the L4 branch
(`feature/l4-phala-autonomous`, post-fix head) is not merged and its migrations/seed/build never reached
the running dev database. The cockpit is fine. Bring the deployed code + DB to the L4 state, then build.

**Hard rules:** N4 boundary (no Prāṇa/level-5). Canonical chart `482012f1` never auto-mutated (B.10).
Anti-drift (writers touch only their layer). KEEP-BOTH naming: `ph_sodhana`=anomaly registry (phala_sodhana),
`ph_rectification`=birth-time rectification (phala_rectification) — distinct assets, both present.

### Step 1 — Merge the L4 branch into main with a MERGE COMMIT, run off main
**Merge situation (pre-verified by Cowork):** `git rev-list --left-right --count main...feature/l4-phala-autonomous`
= **`0  17`** and the merge-base IS main's HEAD (`8851b610`). The branch is a CLEAN LINEAR DESCENDANT of
main — **zero divergence, zero conflict risk.** Branch tip = `e4d6b5cb` (carries the JD-fix, the Aries
parity guard, the 9-asset seed, migrations 330–340, and the R6 stub cleanup — all verified present).
```
git checkout main && git pull --ff-only origin main
git merge --no-ff feature/l4-phala-autonomous -m "merge(l4-phala): L4 Phala build + remediation (9 assets, rectification JD-fix, U2 lifetime)"
git push origin main
```
Use **`--no-ff`** (explicit merge commit, as requested — not a fast-forward), so main carries one merge
commit recording the L4 integration. No conflicts are expected; if any appear, the branch is authoritative
for all L4 files (migrations 330–340, ph_* writers/services, seed, schools/*).
**Confirm on main after merge:**
- `git branch --contains HEAD | grep main` and `git log --oneline -1` shows the merge commit.
- `ls platform/supabase/migrations/33*.sql platform/supabase/migrations/340*.sql` → 330–340 present
  (and the dead stubs 333_phala_rectification/334_phala_rectification_best/337_phala_outlook/339 are GONE — R6).
- `grep -oE "asset_id: 'ph_[a-z_]+'" platform/scripts/seed/asset_registry_seed.ts | sort -u | wc -l` → **9**.
- Restart the dev server so localhost:3000 serves the merged main (`pnpm dev` / your run script).

### Step 2 — Apply migrations 330–340 to the dev DB (via the Cloud SQL proxy — data plane is prod)
```
cd platform && npx tsx scripts/migrate.ts            # applies 326–340 in order; 330 DROPs kala_timeline
npx tsx scripts/migrate.ts --dry-run                 # confirm 0 pending after
```
Confirm the 9 phala tables exist: `phala_anchors, phala_muhurta, phala_mitigation, phala_sankrama,
phala_pramana, phala_phaladesa, phala_sodhana, phala_suddha_sodhana, phala_rectification (+ _best)`.

### Step 3 — Re-seed the asset registry (the cockpit reads this)
```
npx tsx scripts/seed/asset_registry_seed.ts          # upserts all 9 ph_ rows + updates the 5 stale ones
```
Confirm via the API: `curl -s localhost:3000/api/cockpit/registry | jq '[.data.assets[]|select(.layer=="phala")]|length'`
→ must return **9**, and `ph_sodhana.count_sql` must reference `phala_sodhana` (NOT `phala_rectification`),
with a separate `ph_rectification → phala_rectification` row.

### Step 4 — Run the build for the native (the orchestrator click-Build path)
Either click **Build** on the Phala layer in the cockpit for `482012f1`, OR:
```
cd platform/python-sidecar && PYTHONPATH=. python -m pipeline.orchestrator.run \
   --chart-id 482012f1-710e-4a25-994a-93821f5871aa --layer phala
```
(Run the U2 L3 re-score + U3/U4 enablers first if not already in the DB — they feed ph_nimitta.)

### Step 5 — Verify in the cockpit (the visual seal gate)
- `curl -s "localhost:3000/api/cockpit/stats?chartId=482012f1-710e-4a25-994a-93821f5871aa" | jq '[.data.assets[]|select(.asset_id|startswith("ph_"))|{id:.asset_id,rows:.actual_rows,state:.state}]'`
  → all **9** ph_ with `rows > 0, state: 'lit'`, `error: null`.
- Open the cockpit Nirmāṇa panel: **Phala = "9 assets"**, progress bar full, DAG shows the 9 phala beads
  lit + wired to kala. Dashboard shows the native at the new % (not "33% / 16d ago").
- `phala_rectification` candidates show **Aries** lagna (the JD-fix); `phala_rectification_best` row has
  `auto_action='stage_for_review'`; canonical chart UNCHANGED.
- FORENSIC 7/7 spot-check in chart_facts.

### Step 6 — Only AFTER Step 5 visually passes: author the seal artifacts
Promote 9 ph_ DRAFT→CURRENT; target_floor = achieved counts; `L4_PHALA_CLOSE_v1_0.md` (record the
ascendant JD-fix as resolved); CURRENT_STATE → L4 CLOSED, L5 NEXT; SESSION_LOG entry.

## §5 — Why this happened (so it doesn't recur)
The whole L4 build lived on a branch + a worktree DB; localhost reads `main` + the shared dev DB. This is
the recurring **worktree-complete ≠ deployed** trap ([[feedback-ac-must-verify-target-environment]]). The
seal gate must ALWAYS be "the LIVE cockpit on the running instance shows it", never "the branch has it".
Add to the seal checklist: a registry-count assertion (`phala == 9`) that runs against the RUNNING API,
not the branch file.

---
*End. The cockpit is healthy; the data/deploy is the gap. Merge → migrate → re-seed → build → verify.
9 phala assets will light once the running DB has the L4 migrations + seed + a build run.*
