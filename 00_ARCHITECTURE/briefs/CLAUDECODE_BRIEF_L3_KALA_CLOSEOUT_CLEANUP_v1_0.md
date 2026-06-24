---
artifact: CLAUDECODE_BRIEF_L3_KALA_CLOSEOUT_CLEANUP_v1_0.md
canonical_id: CLAUDECODE_BRIEF_L3_KALA_CLOSEOUT_CLEANUP
version: 1.0
status: AUTHORED — cautious, ordered L3 closeout cleanup for Claude Code
executor: Claude Code in Antigravity — all commands embedded
authored_by: Cowork 2026-06-21
source_audit: 00_ARCHITECTURE/L3_KALA_CLOSURE_AUDIT_v1_0.md
principle: >
  Cautious, reversible-first ordering. Verify before destroy. Every branch/script removal is
  pre-verified as merged/absorbed (see audit §2 + §5). Nothing here touches prod data or the
  asset_registry — L3 is already prod-sealed; this is code/git/doc hygiene + one CI fix.
---

# L3 KĀLA CLOSEOUT CLEANUP — cautious, ordered

> Do the steps IN ORDER. Steps 0–1 are verification + sync (no deletion). Steps 2–6 are the
> housekeeping. Each step has a verify gate. STOP and report if any gate fails.

## STEP 0 — Verify the canonical tip + clean working tree (no mutation)
```bash
cd <repo>
git fetch --prune origin
git rev-parse origin/main          # expect e2ef4d72 (or later if new work landed)
git status --porcelain             # expect only untracked L4 docs / smriti — NO modified L3 files
# Confirm seed is clean on origin/main:
git show origin/main:platform/scripts/seed/asset_registry_seed.ts | grep -c "ka_transit_almanac"  # expect 0
git show origin/main:platform/scripts/seed/asset_registry_seed.ts | grep -c "CHART_ID"             # expect 0
```
GATE: origin/main is the sealed tip; seed has 0 almanac + 0 CHART_ID literals. If not, STOP.

## STEP 1 — Fast-forward local main (sync, no deletion)
```bash
git checkout main
git pull --ff-only origin main     # local main was a clean ancestor — FF only, no merge commit
git rev-parse main                 # now == origin/main
```
GATE: `git branch --merged origin/main` now lists all the L3 branches as merged.

## STEP 2 — IMPORTANT: fix the CI migration silent-skip (the only load-bearing item)
`.github/workflows/deploy.yml` "Run database migrations" step currently SKIPS silently (exit 0)
when `PROD_DATABASE_URL` is unset — so migrations never apply but CI stays green. L4 migrations
(251+) will silently no-op the same way. Do ONE of:
- **(Preferred)** Set the `PROD_DATABASE_URL` GitHub Actions secret so line 138 (`migrate.ts`) runs.
  (Operator action — set the secret in repo settings; cannot be done from code.)
- **(Code-side fail-loud, do this regardless)** change the skip branch to FAIL instead of pass:
  ```yaml
  if [ -z "$DATABASE_URL" ]; then
    echo "::error::PROD_DATABASE_URL secret not set — migrations NOT applied. Failing build."
    exit 1
  else
    cd platform && npx tsx scripts/migrate.ts
  fi
  ```
  This makes a missing secret a red build instead of a silent green no-op.
Commit on a small branch `chore/ci-migration-failloud`, PR to main.
GATE: a deploy run with the secret present actually applies migrations; with it absent, the build FAILS (not skips).

## STEP 3 — Retire the 9 dead bypass scripts (CF.L3.8 footgun; zero callers — audit §5)
```bash
git checkout -b chore/l3-retire-bypass-scripts
cd platform/python-sidecar
# RE-VERIFY zero callers before deleting (cautious):
for f in run_ka_yojaka_prod run_ka_sangam_prod run_ka_kalasutra_prod run_ka_vighnakara_prod \
         run_ka_kala_darshana_prod run_ka_jivana_parva_prod run_ka_bhavishya_lekha_prod \
         run_l3_full_prod reconcile_l3_build_state; do
  echo "== $f =="; grep -rln "$f" .. --include=*.py --include=*.ts --include=*.yml | grep -v "/$f.py"
done
# Expect NO output per script (only the file itself). If any external ref appears, KEEP that one + report.
git rm run_ka_*_prod.py run_l3_full_prod.py reconcile_l3_build_state.py
git commit -m "chore(l3): retire orchestrator-bypass run scripts + one-shot reconcile (CF.L3.8 footgun; zero callers)"
```
GATE: re-grep shows zero external callers; tests still pass (Step 5). PR to main.

## STEP 4 — Doc closeout (frontmatter + CF table + CURRENT_STATE + dup manifest)
```bash
git checkout -b chore/l3-closeout-docs
```
- `00_ARCHITECTURE/L3_KALA_CLOSE_v1_0.md`: fix frontmatter `role:` "13 ka_* assets (5 service +
  8 artifact)" → "**12 ka_* assets (5 service + 7 artifact)**". In the CF table, update CF.L3.7 +
  CF.L3.8 to note the StatusDot fix (commit on origin/main) addressed the render family, and mark
  CF.L3.8 RESOLVED on the code side (orchestrator wired) with the residual = "retire bypass scripts"
  (now done in Step 3). Bump close doc to v1.2.
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md`: bump to **v5.90**, changelog entry reflecting the true
  sealed tip `e2ef4d72`: almanac hard-removal (13→12), migs 328/329, StatusDot CF.L3.8 green fix,
  L3 closure audit complete. Point §2 state block at "L3 SEALED + closed-out; NEXT = L4 Phala".
- Remove the stale DUPLICATE manifest: `git rm platform/00_ARCHITECTURE/CAPABILITY_MANIFEST.json`
  (canonical stays at `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`). RE-VERIFY first that no tooling
  reads the platform/ path: `grep -rln "platform/00_ARCHITECTURE/CAPABILITY_MANIFEST" .` → expect 0.
```bash
git commit -am "docs(l3): closeout — 12-asset frontmatter fix, CF.L3.7/8 disposition, CURRENT_STATE v5.90, drop dup manifest"
```
GATE: drift_detector.py + schema_validator.py pass; PR to main.

## STEP 5 — Final green-gate: tests + (recommended) one orchestrator-driven rebuild
```bash
cd platform/python-sidecar && python -m pytest tests/l3 tests/test_ka_graha_sancara.py tests/test_ka_muhurta_seva.py -q
```
GATE: L3 suite green. 
RECOMMENDED (proves CF.L3.8 click-Build end-to-end, not just code-correct): from the cockpit,
trigger a **Rebuild** on the Kāla layer for chart 482012f1 via the orchestrator (NOT the retired
scripts), and confirm asset_throughput.last_built_at updates through the normal path + cockpit
stays green. This is the true CF.L3.8 closure.

## STEP 6 — Branch + worktree sweep (LAST; everything verified merged in Steps 0–1)
```bash
# DELETE merged local L3 branches (safe -d variant refuses if not merged):
for b in feature/l3-k0-service-asset-type feature/l3-ka-graha-sancara feature/l3-ka-dasha-kala \
         feature/l3-ka-muhurta-seva feature/l3-ka-gochara feature/l3-ka-yojaka feature/l3-ka-sangam \
         feature/l3-ka-kalasutra feature/l3-ka-vighnakara feature/l3-ka-kala-darshana \
         feature/l3-ka-jivana-parva feature/l3-ka-bhavishya-lekha chore/l3-kala-planning-inputs \
         fix/l3-cockpit-ui-service-pill-and-floor fix/l3-kala-prod-build-remediation; do
  git branch -d "$b" 2>/dev/null && echo "deleted $b" || echo "KEPT (not merged or absent): $b"
done
# DELETE the corresponding remote branches still on GitHub:
for b in feature/l3-k0-service-asset-type feature/l3-ka-graha-sancara feature/l3-ka-dasha-kala \
         feature/l3-ka-muhurta-seva feature/l3-ka-sangam feature/l3-ka-kalasutra \
         feature/l3-ka-vighnakara feature/l3-ka-kala-darshana feature/l3-ka-jivana-parva \
         feature/l3-ka-bhavishya-lekha chore/l3-kala-planning-inputs \
         fix/l3-cockpit-ui-service-pill-and-floor fix/l3-kala-prod-build-remediation; do
  git push origin --delete "$b" 2>/dev/null && echo "remote-deleted $b" || echo "remote absent: $b"
done
# Prune worktrees:
git worktree prune
git worktree list   # confirm the l3 + MadhavMuhurta + agent-* prunables are gone
```
GATE: `git branch -d` (safe variant) refused to delete anything unmerged. If it KEPT a branch as
"not merged", STOP and report — do NOT force-delete. Everything in the list above was pre-verified
merged, so all should delete cleanly.

---
## Definition of done
- [ ] Step 1: local main == origin/main (FF, no merge commit).
- [ ] Step 2: CI migration step fails loud on missing secret (and/or secret set) — no more silent skip.
- [ ] Step 3: 9 bypass scripts removed (zero-caller re-verified); tests green.
- [ ] Step 4: close-doc frontmatter 12/7, CF.L3.7/8 dispositioned, CURRENT_STATE v5.90, dup manifest dropped.
- [ ] Step 5: L3 test suite green; (recommended) one orchestrator-driven Kāla rebuild proves click-Build.
- [ ] Step 6: ~15 merged L3 branches deleted (local+remote), worktrees pruned; nothing unmerged force-deleted.

*All destructive ops are gated on a merged/zero-caller re-check. If any gate trips, STOP and report —
do not override. L3 prod data is already sealed and is NOT touched by this cleanup.*
