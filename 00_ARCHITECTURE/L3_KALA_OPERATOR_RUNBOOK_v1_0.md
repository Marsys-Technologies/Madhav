---
artifact: L3_KALA_OPERATOR_RUNBOOK_v1_0.md
canonical_id: L3_KALA_OPERATOR_RUNBOOK
version: 1.0
status: READY — the operator/data-plane gate sequence (OP1–OP4) to run before pasting the KICKOFF
authored_by: Cowork 2026-06-21 (grounded in the verified branch + tree state + a parallel branch-content audit)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
purpose: >
  The exact, paste-ready operator steps for the 4 data-plane gates that Cowork cannot execute (git
  push + branch ops + prod DB). Each step has its command + the verified rationale + the expected result.
  Run top-to-bottom; when §5 is all-green, paste the KICKOFF block. Commands assume repo root
  /Users/Dev/Vibe-Coding/Apps/Madhav and the Cloud SQL Auth Proxy on 127.0.0.1:5433.
audit_basis: >
  Verified 2026-06-21: current branch `fix/l2-bodha-writer-bugs-b6-gates` is 0/0 vs origin/main (level).
  Two parallel sub-agents audited the 4 temporal branches — ALL are stale (their work is already squashed
  into main); a merge would REVERT 50k–115k lines. K0's schema is ~60% on main (mig 202); ka_muhurta_seva's
  engine is ~90% on main (panchang_engine + muhurat/finder.py; Tara Bala FLOORED). K2's transit_search
  exists on NO branch — a genuine build.
---

# L3 Kāla — Operator Runbook v1.0 (OP1–OP4)

## §0 — TL;DR (what changed from the original plan)
The branch audit INVERTED OP1: **do NOT reconcile/merge the 4 temporal branches — DELETE them** (all stale;
work already on main; merging reverts tens of thousands of lines). And it found two briefs over-scope work
already on main — **already corrected in the briefs** (K0 = extend mig 202; ka_muhurta_seva = wrap + un-floor
Tara Bala). So OP1 is now "delete 4 stale branches + confirm the head-start is on main," which is far safer
than a merge.

---

## OP1 — Branch reconciliation → **DELETE the 4 stale branches (do NOT merge)**

**Rationale (verified):** each branch is 111–328 commits BEHIND main and only 2–15 ahead; the "ahead"
commits are earlier divergent copies of work since squashed into main (`c78c0d45` panchanga; the transit
Gate-1 files are byte-identical to main). `git merge-tree` shows add/add conflicts + a 49.7k-line reversion
on subsystem-transit. **There is nothing to merge.**

**Step OP1.1 — confirm (read-only) the head-start is already on main:**
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav && git fetch origin
# K0 schema (expect: file exists on main)
git cat-file -e origin/main:platform/supabase/migrations/202_asset_registry_service_support.sql && echo "OP1.1a K0 mig202 ON MAIN ✓"
# ka_muhurta_seva engine (expect: exists on main)
git cat-file -e origin/main:platform/python-sidecar/muhurat/finder.py && echo "OP1.1b muhurat engine ON MAIN ✓"
git cat-file -e origin/main:platform/python-sidecar/panchang_engine/tara_bala.py && echo "OP1.1c tara_bala (floored) ON MAIN ✓"
# K2 transit_search (expect: MISSING on main — confirms it's a real build)
git cat-file -e origin/main:platform/python-sidecar/pipeline/transit_search.py 2>/dev/null && echo "UNEXPECTED: exists" || echo "OP1.1d transit_search ABSENT on main ✓ (K2 builds it)"
```

**Step OP1.2 — delete the 4 stale branches (local + remote). DESTRUCTIVE — confirm OP1.1 first:**
```bash
for b in feature/subsystem-transit feature/panchanga-service-registry feature/panchanga-rich-output feature/l0fr-stream-e-panchanga-service; do
  git branch -D "$b" 2>/dev/null || true     # local (if present)
  git push origin --delete "$b"               # remote
done
```
> Keep-as-reference (do NOT delete the FILES, just the branches): the `l0fr-stream-e` `query_muhurta.ts` /
> `query_panchanga.ts` retrieval wrappers are a stale design reference for K1's retrieval surface — they are
> already captured in the ka_muhurta_seva brief note. No file action needed.

**OP1 expected result:** the 4 branches gone; the head-start (mig 202, panchang engine) confirmed on main;
transit_search confirmed absent (K2 builds it). **OP1 GREEN.**

---

## OP2 — Commit the swarm inputs onto a clean branch off `origin/main`

**Rationale:** the current branch is level with main (0/0). The 22 uncommitted items (13 briefs + the L3
governing docs + the CONDUCTOR dir) are the swarm's INPUT artifacts and must be in the repo.

**Step OP2.1 — fresh branch off main + stage the inputs:**
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav && git fetch origin && git checkout -b chore/l3-kala-planning-inputs origin/main
# stage ONLY the L3 planning artifacts (not unrelated working-tree changes)
git add 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_L3_*.md
git add 00_ARCHITECTURE/L3_KALA_CAMPAIGN_PLAN_v0_10.md \
        00_ARCHITECTURE/L3_KALA_PRE_IMPL_CLOSEOUT_v1_0.md \
        00_ARCHITECTURE/L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md \
        00_ARCHITECTURE/L3_KALA_AUTONOMOUS_EXECUTION_PLAN_v1_0.md \
        00_ARCHITECTURE/L3_KALA_OPERATOR_RUNBOOK_v1_0.md
git add 00_ARCHITECTURE/CONDUCTOR/l3-kala/
```

**Step OP2.2 — normalize the briefs dir case (BRIEFS → briefs).** The on-disk dir is `00_ARCHITECTURE/BRIEFS/`
(uppercase) but the plan/queue reference `briefs/` (lowercase). On a case-insensitive FS this works but is
fragile. Pick ONE (lowercase `briefs/` recommended, matching the L2 convention) and make git agree:
```bash
# only if the tracked path is uppercase; force git to the lowercase form:
git mv 00_ARCHITECTURE/BRIEFS 00_ARCHITECTURE/briefs_tmp && git mv 00_ARCHITECTURE/briefs_tmp 00_ARCHITECTURE/briefs
# (the two-step avoids the case-insensitive no-op; verify with: git ls-files 00_ARCHITECTURE/ | grep -i brief | head)
```

**Step OP2.3 — remove the stale superseded pointer + commit + push:**
```bash
git rm --cached 00_ARCHITECTURE/L3_KALA_CAMPAIGN_PLAN_v0_8.md 2>/dev/null || true   # the neutralized desync pointer
git commit -m "chore(l3-kala): L3 Kāla planning inputs — 13 briefs + campaign plan + closeout + ratified templates/weights + execution plan + Conductor queue/kickoff"
git push -u origin chore/l3-kala-planning-inputs
```
> Whether this merges to main before the swarm runs, or the swarm branches FROM it, is your call — but the
> inputs must be COMMITTED + pushed so the Conductor can read them. **OP2 GREEN when pushed.**

---

## OP3 — Prod == main verification (the seed→prod divergence guard; Brahma V1.3 lesson)

**Rationale:** the swarm's ACs verify against PROD. Prod must be a known-good baseline == main.

**Step OP3.1 — main HEAD == deployed prod revision:**
```bash
git rev-parse origin/main          # the SHA the swarm builds on
gcloud run services describe amjis-web --region asia-south1 \
  --format='value(status.traffic[0].revisionName)'   # the live revision — confirm it matches the merge SHA
```
**Step OP3.2 — L2 migrations applied on prod (not just on disk):**
```bash
bash platform/scripts/start_db_proxy.sh   # Cloud SQL Auth Proxy on 127.0.0.1:5433
# adjust connection string as per platform/scripts; then:
psql "host=127.0.0.1 port=5433 dbname=<prod_db> user=<user>" -c \
  "SELECT max(version) FROM schema_migrations;"   # confirm ≥ the L2 close migration (incl. 326 bo_* floors)
psql "host=127.0.0.1 port=5433 ..." -c \
  "SELECT asset_id, catalog_status FROM asset_registry WHERE layer_name='bodha' LIMIT 12;"  # L2 assets live
```
**Step OP3.3 — live asset state via the cockpit API:**
```bash
curl -s "https://<prod-host>/api/cockpit/stats?chart_id=482012f1-710e-4a25-994a-93821f5871aa" | head
```
**OP3 GREEN when:** prod revision == main SHA; schema_migrations ≥ L2 close; bodha assets CURRENT in prod.

---

## OP4 — Prod residual checks (two L2-carry-in items)

**Rationale:** on-disk, L2 is code-ready (the 4 NULL hooks exist; bo_samskara uses real Vertex embeddings).
Two things can only be confirmed in the prod data plane.

**Step OP4.1 — `bodha_signal_embeddings` holds REAL Vertex vectors (not a stale placeholder run):**
```bash
psql "host=127.0.0.1 port=5433 ..." -c \
  "SELECT count(*), (SELECT vector_dims(embedding) FROM bodha_signal_embeddings LIMIT 1) AS dims FROM bodha_signal_embeddings;"
# expect: count ≈ 66,738 ; dims = 768.  If dims≠768 or count is placeholder-shaped → re-run bo_samskara (operator).
```
> Per the closeout: NO L3 asset depends on embeddings, so a stale-placeholder here does NOT block the L3
> launch — but record it as a known gap if it fails.

**Step OP4.2 — the 4 L3-fill hooks are NULL in prod (the reserved surface ka_yojaka/ka_kalasutra fill):**
```bash
psql "host=127.0.0.1 port=5433 ..." -c \
  "SELECT count(*) FILTER (WHERE signature_class IS NOT NULL) AS sc,
          count(*) FILTER (WHERE active_dasha_periods_jsonb IS NOT NULL) AS adp,
          count(*) FILTER (WHERE activation_predicted_dates_jsonb IS NOT NULL) AS apd,
          count(*) FILTER (WHERE dasha_activation_proximity_score IS NOT NULL) AS daps
   FROM bodha_msr_signals;"
# expect: all four = 0 (the hooks are reserved-NULL; L3 fills them via ka_kalasutra's artifact + JOIN).
```
**OP4 GREEN when:** embeddings are real-or-recorded-gap; the 4 hooks are NULL as expected.

---

## §5 — THE LAUNCH GATE (all green → paste the KICKOFF)
| Gate | Result |
|---|---|
| OP1 — 4 stale branches deleted; head-start confirmed on main; transit_search absent | ☐ |
| OP2 — inputs committed + pushed on a clean branch off main; briefs dir normalized | ☐ |
| OP3 — prod revision == main SHA; L2 migrations applied; bodha assets CURRENT | ☐ |
| OP4 — embeddings real (or gap recorded); 4 L3-fill hooks NULL | ☐ |
| (pre-done) D7 templates/weights RATIFIED; CS3/CS4 brief fixes; DR1/DR2/DR3 corrections | ✅ |

When all four are checked → open `00_ARCHITECTURE/CONDUCTOR/l3-kala/KICKOFF_L3_KALA_AUTONOMOUS.md`, complete
its pre-flight (these same OP gates), and paste the §KICKOFF block to the Sūtradhāra. The autonomous run
begins.

---
*End of L3_KALA_OPERATOR_RUNBOOK v1.0. OP1 = delete 4 stale branches (NOT merge — verified). OP2 = commit
inputs to a clean branch. OP3 = prod==main. OP4 = 2 prod residual reads. Cowork already folded the two
scope-corrections (K0 extends mig 202; ka_muhurta_seva wraps+un-floors) into the briefs so the swarm doesn't
rebuild what exists.*
