---
artifact: L3_KALA_CLOSURE_AUDIT_v1_0.md
canonical_id: L3_KALA_CLOSURE_AUDIT
version: 1.0
status: AUDIT COMPLETE — closure gate report + cautious cleanup action list
audited_by: Cowork 2026-06-21 (4 parallel read-only investigation tracks + direct verification)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
scope: >
  Thorough layer-closure audit of L3 Kāla across four dimensions: (1) orchestrator wiring,
  (2) git/branch/merge/push hygiene, (3) prod data-plane + registry + migration correctness,
  (4) CI migration application + test/seal-doc/governance state + scratch cleanup. Read-only;
  no mutations performed. Produces a closure verdict + an ordered, cautious cleanup prompt.
---

# L3 KĀLA — LAYER CLOSURE AUDIT

## VERDICT

**L3 Kāla is functionally SEALED and prod-verified.** The instrument is correct on production
(12 assets, green, zero errors), all code is merged to `origin/main`, the orchestrator is
properly wired, and the DAG is clean and acyclic. **No defect blocks closure.**

Closure is **not yet 100% tidy** — there are **6 housekeeping items** (1 important, 5 routine)
that should be discharged to call the layer *cleanly* closed. The one important item
(**CI silent-skip**) is load-bearing for L4 and must be fixed before L4 migrations.

---

## SECTION 1 — Orchestrator wiring  ✅ PASS (closes CF.L3.8 on the code side)

All 12 ka_* assets are properly wired to the FROZEN orchestrator contract.

- **7 artifact writers** — each `@register('<id>')`, subclasses `WriterBase`, implements
  `run(ctx) -> WriterResult`. Files under `platform/python-sidecar/pipeline/orchestrator/writers/`:
  ka_kalasutra, ka_sangam, ka_vighnakara, ka_kala_darshana, ka_jivana_parva, ka_bhavishya_lekha, ka_yojaka.
- **5 services** — ka_graha_sancara + ka_dasha_kala + ka_muhurta_seva registered as service writers
  (WriterBase shims / adapters returning `rows_inserted=0`); ka_gochara + ka_tulana are pure
  `asset_kind='service'` registry entries.
- **Contract clean** — grep across all ka_* writers found **zero** `ctx.db_conn.commit()/.rollback()/.close()`
  and **zero** direct `asset_throughput` writes. Orchestrator owns the transaction.
- **DAG is acyclic and coherent** — clean topological order resolves (services → ka_yojaka →
  ka_sangam → ka_kalasutra/ka_vighnakara → ka_kala_darshana → ka_jivana_parva/ka_bhavishya_lekha →
  ka_tulana). `discover_all()` auto-imports all writers so the orchestrator finds them.
- **The orchestrator "click Build" path CAN drive all 12 in dependency order** — `resolveBuildPlan()`
  + `runner.py` + `asset_runner.py` are in place; scope='layer'/target='kala' filters to the 12.

> **CF.L3.8 nuance:** the L3 prod build-state was stamped by a ONE-SHOT `reconcile_l3_build_state.py`
> because the initial build used standalone `run_ka_*_prod.py` scripts that bypassed the orchestrator.
> The *code path* is now correct; what remains is (a) retire the bypass scripts (Section 5), and
> (b) ideally run one orchestrator-driven rebuild to prove the click-Build path end-to-end before L4.

---

## SECTION 2 — Git / branch / merge / push  ✅ MERGED & PUSHED (housekeeping remains)

- **`origin/main` HEAD = `e2ef4d72`** ("fix(cockpit): DRAFT·healthy StatusDot green not red (CF.L3.8)").
  This is the **canonical sealed tip.** All L3 work is on it: PRs #308–#321 (the 12 assets + ka_tulana),
  the prod-build remediation (#319), the cockpit StatusDot/aria/service-pill fixes, migrations 328+329,
  and the ka_transit_almanac hard-removal (13→12). **Seed on origin/main is clean: 0 almanac refs,
  0 `$$CHART_ID$$` literals.**
- **Local `main` = `4e0a21c4`** — 6 commits behind origin/main, **clean ancestor (fast-forward only,
  zero divergence)**. Just needs `git pull --ff-only`.
- **Checked-out branch = `fix/l3-cockpit-ui-service-pill-and-floor` (`a299eee3`)** — holds the
  pre-squash local versions of the SAME fixes now on origin/main (same commit messages). It looks
  "ahead" by commit count but its content is fully absorbed into `e2ef4d72` via squash-merge. **Pure
  squash residue — nothing unmerged.**
- **No uncommitted L3 work.** The only untracked files are L4 Phala planning docs (this thread's
  handoff) + the CONDUCTOR `l3-kala/smriti/` scaffolding — neither blocks L3.
- **~15 merged L3 branches** (local + remote) are all `[merged: yes | safe-to-delete: yes]`. Two
  (gochara, yojaka) are already deleted on GitHub.

> **No branch carries unmerged work. Nothing to rescue. The git state is safe to clean.**

---

## SECTION 3 — Prod data-plane + registry + migrations  ✅ PASS

- **Prod API (`/api/cockpit/stats`, cache-busted, this session):** Kāla = **12 assets**,
  `has_almanac: false`, `any_error: []`. 7 `lit` with real rows (no stale flags), 5 `service_ok`.
  Dots confirmed green (`rgba(83,200,100,0.95)`) on the live cockpit by the native.
- **Migrations confirmed present:** L3 build 242–250 (under `platform/supabase/migrations/`);
  removal/fix 323/328/329 (under `platform/migrations/` — the documented two-root split).
  Mig 328 expands the `asset_registry_catalog_status_check` CHECK to allow `RETIRED`; mig 329 is the
  FK-safe delete (asset_throughput row first, then asset_registry). Both idempotent.
- **count_sql:** all artifact rows use `$1` binding; services are `asset_kind='service'` with null
  count_sql and the stats-route service-health branch. No `$$CHART_ID$$` literals remain.

---

## SECTION 4 — CI / tests / seal-docs / governance  ⚠️ 1 IMPORTANT + routine items

### 4a. ⚠️ CI SILENT-SKIP — the one important finding (must fix before L4)
`.github/workflows/deploy.yml` lines 131–139: the "Run database migrations" step is
```
if [ -z "$DATABASE_URL" ]; then
  echo "SKIP: PROD_DATABASE_URL secret not set — migrations must be run manually..."
else
  cd platform && npx tsx scripts/migrate.ts
fi
```
If the `PROD_DATABASE_URL` secret is **unset, the step echoes SKIP and exits 0 (green build) while
applying zero migrations.** This is exactly why migrations 328/329 silently no-op'd and the DELETE
had to be hand-applied via psql. **L4 starts at migration 251+ — every L4 migration will silently
skip the same way until this is fixed.** Fix = set the `PROD_DATABASE_URL` secret in CI **or** make
the skip fail loudly (exit 1) so a missing secret can't masquerade as a successful migration.
This is flagged in `L4_PHALA_CONVERSATION_HANDOFF_v1_0.md §8` as the #1 L4 pre-build item.

### 4b. Tests — present, not run here
12 `test_ka_*.py` files (10 under `tests/l3/`, 2 service tests under `tests/`). None references the
removed almanac (the only "almanac" test is an unrelated L0 test). Recommend a `pytest tests/l3`
run on a clean origin/main checkout as a final green-gate (Section 5 prompt includes it).

### 4c. Seal-doc / state staleness — routine doc fixes
- **`L3_KALA_CLOSE_v1_0.md` (v1.1, CURRENT):** body + asset manifest are correct at **12 assets**.
  BUT the **frontmatter `role:` block still says "13 ka_* assets (5 service + 8 artifact)"** — stale.
  CF table: CF.L3.7 (cosmetic) + CF.L3.8 (process note) still marked OPEN; the StatusDot fix that
  addresses that family wasn't reflected back into the CF table.
- **`CURRENT_STATE_v1_0.md` (v5.89):** behind origin/main reality — it does **not** mention the
  13→12 almanac removal, CF.L3.7/CF.L3.8 dispositions, or the StatusDot fix. Needs a v5.90 bump to
  the true sealed tip `e2ef4d72`.

### 4d. Governance manifest — NOT a defect, but note
`CAPABILITY_MANIFEST.json` is a **file/artifact-path catalog**, not the asset_registry — by design
it carries **zero `ka_*` asset ids** (L3 assets live in the DB `asset_registry` table via migrations).
So it neither tracks nor needed updating for 13→12. One cleanup: a **stale duplicate manifest** exists
at `platform/00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (canonical is `00_ARCHITECTURE/...`) — consider
removing the duplicate to avoid drift.

---

## SECTION 5 — Scratch cleanup inventory (cautious; enumerate-then-act)

All verified **zero external callers** — dead scratch, safe to retire:

**9 bypass/one-shot scripts (`platform/python-sidecar/`)** — these ARE the CF.L3.8 footgun (re-running
them re-invokes the orchestrator-bypass path and leaves build-state unstamped):
`run_ka_yojaka_prod.py`, `run_ka_sangam_prod.py`, `run_ka_kalasutra_prod.py`, `run_ka_vighnakara_prod.py`,
`run_ka_kala_darshana_prod.py`, `run_ka_jivana_parva_prod.py`, `run_ka_bhavishya_lekha_prod.py`,
`run_l3_full_prod.py`, `reconcile_l3_build_state.py` (header self-declares one-time).

**~15 merged L3 branches** (local + remote) — all `safe-to-delete: yes`.

**~3 prunable L3 worktrees** — `.claude/worktrees/fix+l3-kala-prod-build-remediation`,
`/Users/Dev/Vibe-Coding/Apps/MadhavMuhurta` (→ feature/l3-ka-muhurta-seva), plus generic `agent-*`
scratch. `git worktree prune` clears prunable entries.

**Historical planning artifacts — RETAIN-IN-PLACE (audit trail, hygiene policy §A):** the 14 L3 briefs,
the CONDUCTOR `l3-kala/` scaffolding, and the L3 plan/template/closeout docs. The single canonical
sealed record is `L3_KALA_CLOSE_v1_0.md`. Do NOT delete these — they're the layer's provenance.

---

## SECTION 6 — Closure checklist (what to discharge)

| # | Item | Severity | Status |
|---|---|---|---|
| 1 | **Fix CI migration silent-skip** (deploy.yml — set secret OR fail-loud) | **IMPORTANT (L4 blocker)** | OPEN |
| 2 | FF local `main` to `e2ef4d72`; delete ~15 merged L3 branches (local+remote); prune worktrees | routine | OPEN |
| 3 | Retire the 9 dead bypass scripts (the CF.L3.8 footgun) | routine | OPEN |
| 4 | Fix `L3_KALA_CLOSE` frontmatter "13→12 / 8→7 artifact"; mark CF.L3.7/CF.L3.8 disposition | routine | OPEN |
| 5 | Bump `CURRENT_STATE` to v5.90 reflecting the true sealed tip `e2ef4d72` (almanac removal + fixes) | routine | OPEN |
| 6 | Remove the stale duplicate `platform/00_ARCHITECTURE/CAPABILITY_MANIFEST.json` | routine | OPEN |
| — | (Optional) one orchestrator-driven `click Build` rebuild of Kāla to prove the path end-to-end | nice-to-have | OPEN |

> Items 2–6 are pure housekeeping and carry zero risk (everything is merged; nothing unmerged to lose).
> Item 1 is the only one that matters beyond tidiness — it must be fixed before L4 builds migrations.

---

*End of L3_KALA_CLOSURE_AUDIT v1.0. Verdict: L3 is sealed and prod-correct; six housekeeping items
(one load-bearing: the CI silent-skip) remain to call it cleanly closed.*
