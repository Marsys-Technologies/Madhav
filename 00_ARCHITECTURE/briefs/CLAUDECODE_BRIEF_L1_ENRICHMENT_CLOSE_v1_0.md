# L1 Enrichment v2.0 — Close (cherry-pick + prod gate + PR) — paste into Claude Code / Antigravity

**Context:** L1 Enrichment v2.0 on `feature/l1-phase3-enrichment` @ `7ce339d4` passed the 4-question pre-PR
review (Q1 PASS · Q2 PASS no-rebuild · Q3 READY · Q4 PASS pre-existing). Native ruled CLOSE via
**cherry-pick-now, parallel with L0**. Execute the steps in order. Standards: surgical migrations only;
seed-consistency; computed-and-cited / canonical-or-floor; only `482012f1`; merge-verify.

⚠️ **PARALLEL-BRANCH COLLISION GUARD (this runs alongside `fix/l0-closure-integrity`, which also touches prod
`asset_registry` + throughput):** before creating ANY migration on this branch, check the highest migration
number ALREADY taken on both `main` AND `fix/l0-closure-integrity` (L0 used through 305) — pick the next free
number above both; do NOT reuse 305. Both branches write `asset_throughput` only for their OWN assets
(L0 = bg_*, L1 = ga_*), so throughput rows don't collide by key — but confirm no shared registry row is edited
by both. If a true collision appears → HALT and report.

---

## STEP 1 — Cherry-pick the registry-test fix (Q4 action item)

The 2 failing registry tests (`birth_params` MagicMock in `test_writer_registry.py`) are pre-existing and were
fixed on `fix/l0-closure-integrity` @ `0ba8c108`.
```bash
git checkout feature/l1-phase3-enrichment
git cherry-pick 0ba8c108
```
If the cherry-pick conflicts (the fix touches `asset_runner.py`/`test_writer_registry.py` which this branch
didn't): resolve taking the L0 version of those test/runner lines (this branch made no changes there). Then:
```bash
# run the python test suite
pytest platform/python-sidecar -q
```
Expect **380 passed, 0 failed** (was 378 passed / 2 failed). Confirm the 2 registry tests now pass.

---

## STEP 2 — Prod gate: run the 3 reopened writers for the native, verify on PROD

Connect to PROD (Cloud SQL Auth Proxy, port 5433, secret `amjis-db-password/3`). Run via the orchestrator
(POST /api/cockpit/runs or the build path) for chart `482012f1-710e-4a25-994a-93821f5871aa`, the 3 reopened
assets: `ga_strength`, `ga_condition`, `ga_sensitive`. Then verify on prod (NOT the branch DB):

1. **New categories landed** (`SELECT fact_category, count(*) FROM chart_facts WHERE chart_id=:c AND fact_category IN (...) GROUP BY 1`):
   - Per-varga Ashtakavarga: expect ~675 rows (15 vargas × 9 grahas × 5 ayanamshas) under the new category.
   - Per-varga avastha: `avastha_baladi_per_varga` + `avastha_deeptadi_per_varga` populated for all 9 grahas × vargas.
   - The 5 Amendment-3 sensitive categories: Gulika/Mandi, Sun-upagrahas (Kala/Mrityu/Artha-Prahara/Yamaghantaka),
     special lagnas (Hora/Ghati/Bhava), Beeja+Kshetra sphuta, Yogi Graha + Dagdha Rashi.
2. **FLOORED items show the reason, NOT a fabricated value** (the integrity gate — verify explicitly):
   - Kala-bala, Cheshta-bala per varga → `fact_value_text = 'floored: no_canonical_per_varga_method'`, numeric value NULL.
   - Jagradadi / Sayanadi / Lajjitadi per varga → floored with reason.
   - Vighati lagna → floored with reason.
   - Confirm NO floored row carries a plausible numeric substitute (canonical-or-floor).
3. **L1-authority check:** per-varga Deeptadi rows reference / are consistent with the existing
   `graha_dignity_per_varga` dignity (not a re-derived dignity). Spot-check one graha.
4. **ga_condition first-run sanity:** ga_condition has never run for 482012f1 before (graha_condition absent
   from prod). Confirm it now populates without the old `dignity_status` bug (per-varga dignity spread loads
   non-zero rows — the bug-fix working in prod).
5. **Floors:** `UPDATE asset_registry SET target_floor = <achieved count>` for ga_strength/ga_condition/
   ga_sensitive to their post-run counts (floors-aspirational). Patch `asset_registry_seed.ts` to match.
6. **catalog_status:** confirm all 3 are CURRENT (the recurring DRAFT-hides-asset rail).

Produce a prod-verify table (category × expected × actual × PASS/FAIL). If any new category is empty on prod
or any floored item shows a number, HALT and report — that's a real failure, not a pass.

---

## STEP 3 — PR + merge-verify

Open PR `feature/l1-phase3-enrichment` → `main`. PR body = the 4-question review verdict + the STEP-2 prod-verify
table + the floored-items attestation. After merge: `gh pr view <N> --json mergeCommit,state`; re-confirm the
new categories + floors on prod; confirm cockpit `/clients/482012f1/nirmana` Gaṇita panel shows
ga_strength/ga_condition/ga_sensitive green with updated counts, no red/stale.

**Parallel note:** if `fix/l0-closure-integrity` merges first, rebase this branch on the new main before the PR
(the cherry-picked 0ba8c108 will then already be on main — git will skip it cleanly). Re-run pytest after rebase.

Report back: the 380-green confirmation, the prod-verify table, and the merge SHA. That closes L1 Enrichment
Phase 3 — the per-varga strength/avastha + sensitive-point completeness the native ratified, prod-validated.
