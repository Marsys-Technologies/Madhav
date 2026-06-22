---
artifact: L4_PHALA_MERGE_AND_PROD_SYNC_RUNBOOK.md
canonical_id: L4_PHALA_MERGE_AND_PROD_SYNC_RUNBOOK
version: 1.0
status: READY — the end-to-end Antigravity runbook: renumber → merge to main → localhost verify → push → prod deploy → prod verify → seal
authored_by: Cowork 2026-06-22
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
runs_in: Antigravity Claude Code (needs git push creds, Cloud SQL proxy, gcloud deploy — ALL execution is operator/swarm-side)
governing_decisions:
  - "Merge with --no-ff merge commit; run localhost off MAIN (not the branch)."
  - "RENUMBER duplicate migration numbers to clean sequence BEFORE merge (none applied to prod yet; prod max=325)."
  - "VERIFY on localhost/main FIRST, then push to prod (push auto-triggers prod migrate + deploy)."
  - "N4 boundary; canonical chart 482012f1 never auto-mutated (B.10)."
---

# L4 Phala — Merge + Prod-Sync Runbook

## §0 — Critical facts (read before running)
- **Pushing the merge to `main` AUTO-DEPLOYS PROD.** `.github/workflows/deploy.yml` on push→main: CI
  passes → `deploy-web` runs `npx tsx scripts/migrate.ts` against **`PROD_DATABASE_URL`** → then deploys
  Cloud Run. **The push IS the prod-migration trigger.** Migration 330 **DROPs `kala_timeline`**
  (irreversible). ⇒ We verify on localhost/main BEFORE pushing (Phase B gate).
- **Merge is conflict-free:** `main...branch = 0  17`, merge-base = main HEAD `8851b610`. Linear descendant.
- **Branch tip `e4d6b5cb`** has: 9 registry rows, JD-fix, Aries parity guard, R6 partial cleanup
  (337_outlook + 339 deleted), but **duplicate migration numbers remain (two 333s, two 334s)** → Phase A renumbers them.
- **Data plane is ALWAYS prod** ([[feedback-localhost-codeplane-prod-dataplane]]): localhost code on :3000,
  but DB writes go to prod via the Cloud SQL proxy. So "apply migrations to dev DB" = applying to PROD via
  proxy. Treat Phase B migrate as a prod write already — there is no separate local Postgres.
  **⇒ This means there is effectively ONE database. Phase B already migrates prod; the push (Phase D)
  re-runs migrate idempotently + deploys the code.** Plan accordingly: Phase B is the real prod-data gate.

> Because the data plane is prod, the safe order is: renumber → merge to main locally → apply migrations
> (hits prod DB via proxy, idempotent) → re-seed → build → verify in the localhost cockpit (which reads
> the same prod DB) → THEN push (deploys the code + re-runs idempotent migrate, no new schema change) →
> verify prod URL. The cockpit verification on localhost IS the pre-deploy gate because the data is shared.

---

## PHASE A — Renumber migrations to a clean sequence  `[swarm; on the branch, pre-merge]`
None of 330–341 are applied to prod (prod max = 325), so renumbering is safe. Apply this exact map:

| Current file | New file |
|---|---|
| 330_phala_anchors_and_drop_kala_timeline.sql | 330 (unchanged) |
| 331_phala_muhurta.sql | 331 (unchanged) |
| 332_phala_mitigation.sql | 332 (unchanged) |
| 333_phala_sodhana.sql | 333 (unchanged) |
| 334_phala_suddha_sodhana.sql | 334 (unchanged) |
| **333_phala_rectification.sql** | **335_phala_rectification.sql** |
| **334_phala_rectification_best.sql** | **336_phala_rectification_best.sql** |
| **335_phala_sankrama.sql** | **337_phala_sankrama.sql** |
| **336_phala_pramana.sql** | **338_phala_pramana.sql** |
| **337_phala_phaladesa.sql** | **339_phala_phaladesa.sql** |
| **338_kala_convergence_horizon_tier.sql** | **340_kala_convergence_horizon_tier.sql** |
| **340_school_consensus_tables.sql** | **341_school_consensus_tables.sql** |

```
cd platform/supabase/migrations
git mv 333_phala_rectification.sql       335_phala_rectification.sql
git mv 334_phala_rectification_best.sql  336_phala_rectification_best.sql
git mv 335_phala_sankrama.sql            337_phala_sankrama.sql
git mv 336_phala_pramana.sql             338_phala_pramana.sql
git mv 337_phala_phaladesa.sql           339_phala_phaladesa.sql
git mv 338_kala_convergence_horizon_tier.sql 340_kala_convergence_horizon_tier.sql
git mv 340_school_consensus_tables.sql   341_school_consensus_tables.sql
```
**Update the 3 number-references (or tests/docs break):**
- `platform/python-sidecar/tests/test_ph_wave6.py` — `336_phala_pramana.sql` → `338_phala_pramana.sql`; "migration 336" → "338".
- `platform/python-sidecar/tests/test_ph_wave7.py` — `337_phala_phaladesa.sql` → `339_phala_phaladesa.sql`.
- `00_ARCHITECTURE/L3_KALA_CLOSE_v1_0.md` — "migration 338" (horizon_tier) → "340".
- Also grep CAPABILITY_MANIFEST.json + the registry/wiring spec for any 33x/340 number and update.
**Verify:** `ls platform/supabase/migrations/33*.sql platform/supabase/migrations/34*.sql` → unique
330–341, NO duplicate numbers: `ls | grep -oE '^3[0-9]+_' | sort | uniq -d` returns EMPTY.
Commit: `git commit -am "chore(l4): renumber migrations to unique 330–341 sequence (R6 completion)"`.

---

## PHASE B — Merge to main + apply migrations + seed + build  `[operator/swarm]`
```
git checkout main && git pull --ff-only origin main
git merge --no-ff feature/l4-phala-autonomous -m "merge(l4-phala): L4 build + remediation — 9 assets, rectification JD-fix, U2 lifetime, clean migs 330–341"
# DO NOT PUSH YET — verify first (push auto-deploys prod).
```
Apply migrations (hits prod DB via the Cloud SQL proxy — this is the real schema change):
```
./platform/scripts/start_db_proxy.sh    # port 5433
cd platform && npx tsx scripts/migrate.ts        # applies 326–341 in order; 330 DROPs kala_timeline
npx tsx scripts/migrate.ts --dry-run             # → 0 pending
```
Re-seed the registry (5 stale → 9 correct):
```
npx tsx scripts/seed/asset_registry_seed.ts
```
Build the native's L4 (+ the U2/U3/U4 enablers if not yet in the DB):
```
cd platform/python-sidecar && PYTHONPATH=. python -m pipeline.orchestrator.run \
   --chart-id 482012f1-710e-4a25-994a-93821f5871aa --layer phala
```

---

## PHASE C — VERIFY on localhost (the pre-push gate)  `[operator + Cowork via Chrome MCP]`
Start the dev server off **main** (`pnpm dev`). Then assert against the RUNNING API:
```
curl -s localhost:3000/api/cockpit/registry | jq '[.data.assets[]|select(.layer=="phala")]|length'   # → 9
curl -s "localhost:3000/api/cockpit/stats?chartId=482012f1-710e-4a25-994a-93821f5871aa" \
  | jq '[.data.assets[]|select(.asset_id|startswith("ph_"))|{id:.asset_id,rows:.actual_rows,state:.state,err:.error}]'
  # → all 9 ph_ with rows>0, state:"lit", err:null
```
Visual (Chrome MCP / browser): cockpit Nirmāṇa panel **Phala = "9 assets"**, full progress bar, DAG shows
9 phala beads lit + wired to kala; dashboard native no longer "33% / 16d ago"; `phala_rectification`
candidates = **Aries**; `phala_rectification_best.auto_action='stage_for_review'`; canonical chart UNCHANGED.
FORENSIC 7/7 in chart_facts. **GATE: do not proceed to Phase D until all green.**

---

## PHASE D — Push to GitHub → prod deploy  `[operator]`
Only after Phase C passes:
```
git push origin main
```
This triggers: CI → (green) → `deploy-web` runs `migrate.ts` against PROD (idempotent — schema already
applied in Phase B via the shared prod DB, so this is a no-op re-run) → builds + deploys Cloud Run web +
the pipeline job image.
**Verify prod (the #1 L3 lesson — the LIVE prod cockpit is the only seal signal):**
```
gcloud run services describe amjis-web --region=asia-south1 --format='value(status.traffic[0].revisionName)'
# confirm the revision corresponds to the merge SHA; wait for rollout + CDN (30–60s)
```
Open the PROD cockpit URL (madhav.marsys.in) → repeat the Phase C registry/stats assertions against prod
→ Phala = 9 lit. Zero startup errors in Cloud Run logs.

---

## PHASE E — Complete cleanup  `[swarm — SCOPED; reverse-citation gate per the destructive-brief lesson]`
**Scope (do ONLY these; do not invent a kill-list):**
1. Delete the merged branch: `git push origin --delete feature/l4-phala-autonomous` + `git branch -d feature/l4-phala-autonomous` (after confirming main contains it).
2. Prune the L4 worktree: `git worktree remove .claude/worktrees/MadhavL4Phala && git worktree prune`.
3. Confirm NO duplicate migration numbers in main: `ls platform/supabase/migrations | grep -oE '^[0-9]+_' | sort | uniq -d` → empty.
4. Confirm zero dead-stub migrations remain: every 330–341 file has a real `CREATE TABLE`/`ALTER TABLE` (no "[PLACEHOLDER]").
5. `.claude/worktrees` disk reclaim if other agent-* dirs are stale ([[reference-claude-worktrees-disk-growth]]) — `rm -rf` only when no Antigravity session is active, then `git worktree prune`.
**Reverse-citation gate:** before deleting ANYTHING beyond the above, grep main for live references to the
target. Do NOT delete files merely because they look like stubs — the rectification "stubs" turned out to
be real DDL. (Destructive-brief lesson [[feedback-destructive-brief-reverse-citation-gate]].)

---

## PHASE F — Author seal artifacts  `[swarm — only after Phase D prod-verify passes]`
- Promote 9 ph_ DRAFT→CURRENT in CAPABILITY_MANIFEST.json; target_floor = achieved counts.
- `L4_PHALA_CLOSE_v1_0.md` — seal notes incl. the ascendant JD-fix as RESOLVED + the clean-renumber.
- `CURRENT_STATE_v1_0.md` → L4 CLOSED, L5 Mīmāṃsā NEXT. Append `SESSION_LOG.md`. Final Vimarśaka audit.
- Add the **live-registry guard** to the seal checklist (see SESSION_CLOSE_TEMPLATE update): the seal MUST
  assert `phala == 9` against the RUNNING prod API, never the branch file. This prevents the
  worktree-complete-≠-deployed recurrence at L5.

---

## Risk register
| Risk | Mitigation |
|---|---|
| Prod migrate auto-runs on push (incl. kala_timeline DROP) | Phase C localhost/prod-DB verify BEFORE push; migrate is idempotent so the Phase-D re-run is a no-op |
| Data plane is shared prod | Phase B IS the prod schema change — treat it with prod care; back up kala_timeline row count first (it's 0, per recon — confirm) |
| Renumber breaks number-refs | Phase A updates the 3 known refs + greps manifest/specs |
| CI red baseline blocks deploy | confirm the 31 known failures are quarantined; deploy gates on CI green |
| Duplicate-number debt to prod | Phase A renumber (chosen) |

---
*End. Renumber → merge (--no-ff) → migrate+seed+build → VERIFY localhost (gate) → push (auto prod deploy)
→ verify prod → scoped cleanup → seal with the live-registry guard. The cockpit is healthy; this syncs
code+data across main + prod and closes L4.*
