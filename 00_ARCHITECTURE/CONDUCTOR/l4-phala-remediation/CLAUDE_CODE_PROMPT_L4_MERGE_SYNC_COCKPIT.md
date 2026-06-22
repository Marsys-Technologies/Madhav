---
artifact: CLAUDE_CODE_PROMPT_L4_MERGE_SYNC_COCKPIT.md
canonical_id: CLAUDE_CODE_PROMPT_L4_MERGE_SYNC_COCKPIT
version: 1.0
status: READY — single paste-prompt for Claude Code in Antigravity. Does EVERYTHING except the final seal.
authored_by: Cowork 2026-06-22
note: Paste the §PROMPT block to Claude Code in Antigravity. DO NOT SEAL — stop after prod is verified green; the native will make further changes, then seal separately.
---

# Claude Code Prompt — L4 Merge + Sync + Cockpit Fix (NO SEAL)

> Paste everything inside §PROMPT. It renumbers migrations, merges the L4 branch to main with a merge
> commit, syncs the DB, builds, fixes the Nirmāṇa tracker + DAG if (and only if) they're actually broken
> after data lands, pushes to GitHub, deploys + verifies prod. **It STOPS before the seal** — no
> DRAFT→CURRENT promotion, no L4_PHALA_CLOSE, no CURRENT_STATE flip.

---

## §PROMPT

You are Claude Code in Antigravity working on MARSYS-JIS (repo: Madhav). Execute the full L4 Phala
merge + sync + cockpit-fix below. **DO NOT perform the final seal** — stop after Phase 6 (prod verified).
The native will make further changes, then seal in a later session.

**Read first:** `00_ARCHITECTURE/L4_PHALA_MERGE_AND_PROD_SYNC_RUNBOOK.md` (the governing runbook),
`00_ARCHITECTURE/L4_PHALA_CODE_AUDIT_REMEDIATION_v1_0.md` (the gap list),
`00_ARCHITECTURE/L4_PHALA_COCKPIT_SYNC_AUDIT_AND_FIX.md` (the cockpit finding).

**Hard rails (non-negotiable):**
- N4 boundary: no Prāṇa / level-5 / chart_dashas_prana anywhere.
- Canonical chart `482012f1-710e-4a25-994a-93821f5871aa` is NEVER auto-mutated (B.10).
- Anti-drift: writers touch only their own layer's tables.
- KEEP-BOTH: `ph_sodhana`→`phala_sodhana` (anomaly registry) AND `ph_rectification`→`phala_rectification`
  (birth-time rectification) are DISTINCT assets — both stay.
- Data plane is ALWAYS prod via the Cloud SQL proxy; localhost serves code only. Applying migrations via
  the proxy IS a prod schema change — treat Phase 2 with prod care.
- Model policy: Gemini/DeepSeek; Anthropic banned for the instrument's own LLM calls.
- If anything fails the deep-fix attempts, STOP and report — do not work around with hacks.

---

### PHASE 1 — Renumber migrations to a clean unique sequence (on the branch, pre-merge)
On `feature/l4-phala-autonomous`, the L4 migrations have duplicate numbers (two 333s, two 334s). None are
applied to prod (prod max = 325), so renumber safely. Apply EXACTLY:
```
git checkout feature/l4-phala-autonomous && git pull
cd platform/supabase/migrations
git mv 333_phala_rectification.sql           335_phala_rectification.sql
git mv 334_phala_rectification_best.sql       336_phala_rectification_best.sql
git mv 335_phala_sankrama.sql                 337_phala_sankrama.sql
git mv 336_phala_pramana.sql                  338_phala_pramana.sql
git mv 337_phala_phaladesa.sql                339_phala_phaladesa.sql
git mv 338_kala_convergence_horizon_tier.sql  340_kala_convergence_horizon_tier.sql
git mv 340_school_consensus_tables.sql        341_school_consensus_tables.sql
cd -
```
Resulting clean set: 330 anchors(+DROP kala_timeline), 331 muhurta, 332 mitigation, 333 sodhana,
334 suddha_sodhana, 335 rectification, 336 rectification_best, 337 sankrama, 338 pramana, 339 phaladesa,
340 kala_convergence horizon_tier (ALTER), 341 school_consensus_tables.
**Update every place that references a migration NUMBER (grep-confirm, fix all):**
- `platform/python-sidecar/tests/test_ph_wave6.py` — `336_phala_pramana.sql`→`338_phala_pramana.sql`; "migration 336"→"338".
- `platform/python-sidecar/tests/test_ph_wave7.py` — `337_phala_phaladesa.sql`→`339_phala_phaladesa.sql`.
- `00_ARCHITECTURE/L3_KALA_CLOSE_v1_0.md` — "migration 338" (horizon_tier)→"340".
- `git grep -nE "33[0-9]_(phala|kala)|340_school|migration 33[0-9]|mig 33[0-9]"` → fix every non-`.sql` hit
  (CAPABILITY_MANIFEST.json, registry/wiring spec, any brief).
**Verify:** `ls platform/supabase/migrations | grep -oE '^[0-9]+_' | sort | uniq -d` → EMPTY (no dups).
Each 330–341 has a real `CREATE TABLE`/`ALTER TABLE` (no "[PLACEHOLDER]").
Commit: `git commit -am "chore(l4): renumber migrations to unique 330–341 (R6 completion)"` and push the branch.

### PHASE 2 — Merge to main (merge commit) + sync the DB + build
```
git checkout main && git pull --ff-only origin main
git merge --no-ff feature/l4-phala-autonomous -m "merge(l4-phala): L4 build + remediation — 9 assets, rectification JD-fix, U2 lifetime, clean migs 330–341"
# DO NOT PUSH YET.
./platform/scripts/start_db_proxy.sh           # Cloud SQL proxy, port 5433 (data plane = prod)
cd platform && npx tsx scripts/migrate.ts       # applies through 341; 330 DROPs kala_timeline (it has 0 rows — confirm first)
npx tsx scripts/migrate.ts --dry-run            # → 0 pending
npx tsx scripts/seed/asset_registry_seed.ts     # 5 stale ph_ rows → 9 correct
cd python-sidecar && PYTHONPATH=. python -m pipeline.orchestrator.run \
   --chart-id 482012f1-710e-4a25-994a-93821f5871aa --layer phala
cd ../..
```
(If U2/U3/U4 enabler data isn't in the DB yet, run those enablers first — they feed ph_nimitta.)

### PHASE 3 — VERIFY DATA on localhost (the cockpit's backing data is now correct)
Start the dev server off main (`pnpm dev` / your run script, `next dev --webpack` per the Turbopack note).
Assert against the RUNNING API:
```
curl -s localhost:3000/api/cockpit/registry | jq '[.data.assets[]|select(.layer=="phala")]|length'   # → 9
curl -s "localhost:3000/api/cockpit/stats?chartId=482012f1-710e-4a25-994a-93821f5871aa" \
  | jq '[.data.assets[]|select(.asset_id|startswith("ph_"))|{id:.asset_id,rows:.actual_rows,state:.state,err:.error}]'
  # → 9 ph_ assets, rows>0, state:"lit", err:null
```
If the registry returns 9 but any ph_ asset is rows:0/dormant, the build (Phase 2) didn't populate it —
fix the writer/build, not the cockpit.

### PHASE 4 — FIX the Nirmāṇa tracker + DAG (ONLY the real bugs that survive Phase 3)
**Important: in the pre-sync audit the cockpit rendered CORRECTLY — it showed stale data because the DB had
5 assets. Do NOT assume a UI bug. First load the Nirmāṇa panel now that 9 assets exist and the build is
populated, and SEE what's actually wrong.** Then fix only genuine defects. Likely-relevant files (trace
from the page DOWN, don't guess — the v2 tree is active per the cockpit-v1-v2-split note):
- `platform/src/app/clients/[id]/nirmana/page.tsx` (the Nirmāṇa build-tracker page)
- `platform/src/lib/components/cockpit/v2/LiveDependencyGraph.tsx` (v2 DAG — likely the active one)
- `platform/src/components/cockpit/LiveDependencyGraph.tsx` + `CockpitShell.tsx` + `OverallProgress.tsx` + `ProgressRing.tsx`
- `platform/src/components/build_orchestrator/ConstellationCanvas.tsx` (the radial constellation DAG)
- `platform/src/app/api/cockpit/registry/route.ts` + `stats/route.ts` + `sse/route.ts`

Check specifically, with 9 assets present:
1. **Layer panel** shows Phala = "9 assets" with the right rows + full progress bar (not "— rows").
2. **Per-asset count** uses each asset's `count_sql` with `$1` binding (the SQL-param-binding lesson —
   gate on `/\$1/.test(sql)`, not metadata). Confirm no `$$CHART_ID$$` leftovers.
3. **DAG / constellation** renders all 9 phala beads, on the correct orbital ring (L4 = Phala), wired to
   kala with the right edge taxonomy; deterministic layout; no overlap/clipping (cross-check
   `querySelectorAll` count vs rendered before declaring anything "missing" — the clipping-hides-UI lesson).
4. **SSE live updates** during a build transition assets dormant→building→lit without a manual refresh.
5. **dd-MMM-yyyy** dates via the central formatter; "9 assets" derived from the registry (no hardcoded count).
For any real bug: fix the component, add/extend a test, re-verify visually. If everything renders correctly
once data is present, RECORD "no cockpit/DAG code bug — was data-state only" and move on. Do NOT invent fixes.

### PHASE 5 — Push to GitHub → auto prod deploy
Only after Phases 3–4 are green:
```
git add -A && git commit -m "fix(cockpit): L4 Phala tracker/DAG render for 9 assets" --allow-empty   # if Phase 4 changed anything
git push origin main
```
This triggers CI → (green) → `deploy-web` runs `migrate.ts` against PROD (idempotent; schema already
applied via the shared prod DB in Phase 2, so a no-op re-run) → builds + deploys Cloud Run web + the
pipeline-job image. If CI is red on the 31 pre-existing failures only, confirm they're the known baseline
(identical on main pre-merge) and let the deploy proceed; any NET-NEW failure blocks — fix it.

### PHASE 6 — VERIFY PROD (the live cockpit is the only truth)
```
gcloud run services describe amjis-web --region=asia-south1 \
  --format='value(status.traffic[0].revisionName)'      # must correspond to the merge/push SHA; wait 30–60s for rollout + CDN
```
Open the PROD cockpit (madhav.marsys.in) → repeat the Phase 3 registry/stats assertions against prod →
Phala = 9 lit, real counts. Check Cloud Run logs: zero startup errors. Confirm `phala_rectification`
candidates show **Aries** lagna and `phala_rectification_best.auto_action='stage_for_review'` (canonical
chart UNCHANGED).

### PHASE 7 — Scoped cleanup (NON-destructive beyond this list; reverse-citation gate)
1. After confirming main contains the branch: `git push origin --delete feature/l4-phala-autonomous` + `git branch -d feature/l4-phala-autonomous`.
2. `git worktree remove .claude/worktrees/MadhavL4Phala && git worktree prune`.
3. Confirm: no duplicate migration numbers in main; no dead-stub migrations; `.gcloudignore` includes `.claude/`.
Before deleting anything NOT on this list, grep main for live references first (the rectification "stubs"
turned out to be real DDL — don't trust appearances).

### STOP HERE — DO NOT SEAL
Do NOT: promote ph_ DRAFT→CURRENT, set target_floors, author L4_PHALA_CLOSE, flip CURRENT_STATE to
L4 CLOSED, or append a layer-seal SESSION_LOG entry. **Report back** with: the merge SHA, the prod
revision, the Phase 3 + Phase 6 assertion outputs (registry=9, all ph_ lit), what (if anything) Phase 4
fixed in the cockpit, and any open issues. The native will make further changes, then seal separately.

**Report format:** a short status table — Phase | done? | evidence (SHA / curl output / file changed) —
plus a "still-open / needs-native" list.

---
*End of Claude Code prompt. Renumber → merge → sync → verify localhost → fix cockpit IF broken → push →
deploy → verify prod → scoped cleanup. NO SEAL — stop and report for the native's further changes.*
