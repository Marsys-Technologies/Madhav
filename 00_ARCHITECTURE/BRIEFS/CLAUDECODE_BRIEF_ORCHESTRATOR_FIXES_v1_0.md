---
artifact: CLAUDECODE_BRIEF_ORCHESTRATOR_FIXES_v1_0
canonical_id: L0_ORCHESTRATOR_FIXES_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
authored_by: Cowork (planning) 2026-06-08
authored_for: Claude Code in Antigravity IDE
native: Abhisek Mohanty
workstream: L0 Brahmagyan unified build — orchestrator fixes (writer discovery + global-asset throughput + layer-build semantics)
parent_design: 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1)
parent_plan: 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md
target_floor: N/A (infrastructure brief — gated by Vimarśaka-FIX checks in §7, not a row count)
dependencies: []  # this brief is Tier -1; it must merge/execute before any writer brief proves out end-to-end
llm_cost: $0
document_number: 2 of 15
---

# Orchestrator Fixes — Writer Discovery + Global-Asset Throughput + Layer-Build Semantics

> **Why this brief exists.** The 12 writer briefs each produce correct rows. None of that reaches the cockpit unless the orchestrator (a) discovers the registered writers at runtime, (b) transitions global-asset throughput state to `lit`, and (c) dispatches a layer-level "Build" across all 12 assets in dependency order. This brief fixes the orchestrator so that "press Build at the Brahmagyan layer → all 12 tiles light" is mechanically true. It is **Tier −1** in the campaign DAG: it must land before any writer brief can be proven end-to-end.

> **Scope discipline.** This brief touches ONLY the orchestrator + its DB plumbing: `pipeline/orchestrator/*.py`, one new migration (`181`), and (read-only verification) the cockpit API routes. It does NOT touch any writer, any classical content, or any cockpit React component. ZERO LLM.

## §0 — Summary of the four defects

These were confirmed by source inspection at main HEAD `db6cc7f3` + PR #227 (Phase β). File:line references are exact.

| # | Defect | Evidence | Severity |
|---|---|---|---|
| **D1** | `discover_all()` is **never called at runtime**. The writer modules (`bg_reference.py`, `bg_ontology.py`, …) only `@register` themselves *on import*, but no production code imports them. At runtime `_REGISTRY` is empty, so `get_writer(asset_id)` returns `None` for every asset → `run_asset` marks the asset `error` with `"no writer registered"`. | `writers/__init__.py:135` defines `discover_all`; **no call site** exists in `main.py`, `runner.py`, `asset_runner.py`. Only `tests/*` and the Phase β smoke script import writer modules / call `discover_all()`. | **BLOCKER** — pressing Build lights nothing. |
| **D2** | `global_runner.py` is a **stale parallel dispatch path**. Its `_build_writer_registry()` lazily imports *old* module names (`brahmagyan_sarani`, `brahmagyan_kalapancanga`, `brahmagyan_shastra`, …) that do not exist in the Phase β layout, so every asset returns `"deferred"`. It also writes **no** `asset_throughput` state, so even if a writer ran, the tile would never light. | `global_runner.py:137-193`; reached via `main.py:46` `--global-build`. | High — the chart-independent build path is dead. |
| **D3** | Global-asset `asset_throughput` rows cannot be upserted/transitioned when `chart_id IS NULL`. The only unique index is partial `WHERE chart_id IS NOT NULL` (migration `171:19-21`), and every state UPDATE uses `WHERE chart_id = %s`, which never matches `NULL`. | `asset_runner.py:128-134` (INSERT `ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL`), `:86-90`, `:188-198`, `:222-229`; `runner.py:68-75` (`is_asset_complete`). | Medium — latent; bites the moment a global (chart_id NULL) build is attempted. |
| **D4** | No explicit confirmation that a **layer-level Build** dispatches all 12 L0 assets in dependency order. (It does — `resolveBuildPlan` topo-sorts by `depends_on` — but this brief must lock it in with a test so the rebuild proof in Document 15 rests on something verified.) | `plan.ts:32-55` (`topoSort`), `:114-172` (`resolveBuildPlan`); `runs/route.ts:43-69`. | Low — works today; needs a regression guard. |

**The proven-good model (do not redesign it):** Phase β demonstrated that `bg_reference` and `bg_ontology` light up when built for the native chart (`chart_id` = the native's chart UUID, **non-null**) through the production path `runs/route.ts` → `invokeRunJob(runId)` → `main.py --run-id` → `runner.execute_run` → `asset_runner.run_asset`. L0 **content** tables are global (no `chart_id` column — confirmed by `clear/execute/route.ts:138-141` using unfiltered `DELETE FROM {table}` for `scope='global'`), but **throughput/tile state** is tracked per-`(chart_id, asset_id)` against the triggering chart. This brief preserves that model as the primary path and adds NULL-safety as defense-in-depth — it does **not** migrate L0 to a NULL-chart throughput model.

## §1 — Pre-read (mandatory before editing)

1. `00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md` — §3 (dependency DAG), §5 (Vimarśaka-Ω), §7 (locked principles)
2. `platform/python-sidecar/pipeline/orchestrator/` — read all 7 modules: `main.py`, `runner.py`, `asset_runner.py`, `global_runner.py`, `locks.py`, `events.py`, `db.py`
3. `platform/python-sidecar/pipeline/orchestrator/writers/__init__.py` — the registry substrate (KEEP AS-IS; do not modify the public surface)
4. `platform/src/lib/build/plan.ts` + `platform/src/app/api/cockpit/runs/route.ts` — the TS plan builder + Build trigger (read-only; D4 only adds a test)
5. Migrations `169`, `171`, `172` (asset_throughput + build_runs) and `179` (asset_registry: 4 new assets, all `scope='global'`, `depends_on` set)
6. Memory `[[l0-phase-beta-shipped]]` (the chart_id NULL residual) and `[[pr-quality-gate-is-not-a-merge]]`

## §2 — Setup

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git fetch --all --prune
git checkout main && git pull --ff-only origin main
git log --oneline -3   # expect db6cc7f3 + PR #227 writer-infra commits

# This campaign uses ONE worktree for the whole batch (master plan §4):
git worktree add -b feature/l0-unified-build /Users/Dev/Vibe-Coding/Apps/MadhavL0Unified main
cd /Users/Dev/Vibe-Coding/Apps/MadhavL0Unified

# FIRST STEP — make the holistic design available on the campaign branch.
# L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md (v1.1) is the authoritative design every
# writer brief cites, but it lives ONLY on branch track/l0-brahmagyan-build
# (commit cc61693c) — it is NOT on main. Cherry-pick the file onto the campaign branch:
git checkout track/l0-brahmagyan-build -- 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md
git add 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md
# (committed as part of the campaign PR; it is the design-of-record for every writer brief)
test -f 00_ARCHITECTURE/L0_BRAHMAGYAN_HOLISTIC_DESIGN_v1_0.md || \
  { echo "FATAL: holistic design not retrieved — check branch track/l0-brahmagyan-build"; exit 1; }

# DB proxy
bash platform/scripts/start_db_proxy.sh > /tmp/proxy_l0unified.log 2>&1 &
sleep 4
export PROD_DB_URL="postgresql://amjis_app@127.0.0.1:5433/amjis"
psql_prod() { psql "$PROD_DB_URL" -v ON_ERROR_STOP=1 "$@"; }

# Confirm the registry has the empty-at-runtime symptom (D1)
cd platform/python-sidecar
python -c "from pipeline.orchestrator.writers import list_writers; print('registry at import:', list_writers())"
# Expect: {} — proves D1 (nothing self-registered just by importing the package)
python -c "from pipeline.orchestrator.writers import discover_all, list_writers; discover_all(); print('after discover_all:', sorted(list_writers()))"
# Expect: ['bg_ontology', 'bg_reference'] — proves discover_all() is the missing call
cd ../..
```

**CHECKPOINT setup:** worktree on `feature/l0-unified-build`; both `python -c` probes behave as described (empty registry until `discover_all()` runs). This is the D1 reproduction.

## §3 — Fix D1: wire `discover_all()` at orchestrator startup (THE blocker)

The registry must be populated before the first `get_writer()` call, in **every** entrypoint that resolves writers.

### §3.1 — `runner.py` (per-chart / `--run-id` path)

In `execute_run()`, call `discover_all()` once, right after the imports inside the function, before the per-asset loop. Edit `platform/python-sidecar/pipeline/orchestrator/runner.py`:

```python
def execute_run(run_id: str) -> None:
    from .asset_runner import run_asset  # imported here to break circular deps
    from .writers import discover_all

    # Populate the writer registry exactly once per process. Idempotent: re-import
    # of already-imported modules is a no-op; @register raises only on a genuine
    # duplicate asset_id, which discover_all() never triggers on a clean module set.
    discover_all()

    conn = connect()
    conn.autocommit = False
    ...
```

### §3.2 — `global_runner.py` (the `--global-build` path) — see also D2 in §4

`execute_global_build()` must call `discover_all()` before dispatch. This is folded into the D2 rewrite (§4) since that function is being replaced wholesale.

### §3.3 — Defensive guard in `asset_runner.run_asset`

`run_asset` is the single chokepoint where a writer is resolved (`asset_runner.py:159`). Add a lazy self-heal so a missing-discovery never silently errors an asset:

```python
    # Resolve writer
    writer_cls = get_writer(asset_id)
    if writer_cls is None:
        # Self-heal: registry may be empty if discover_all() was not called by the
        # entrypoint (defense-in-depth against D1 regressions).
        from .writers import discover_all
        discover_all()
        writer_cls = get_writer(asset_id)
    if writer_cls is None:
        mark_asset_error(conn, cur, run_id, chart_id, asset_id,
                         f"no writer registered for {asset_id} (after discover_all)")
        return
```

**CHECKPOINT 3:** `grep -rn "discover_all" platform/python-sidecar/pipeline/orchestrator/*.py` shows call sites in `runner.py`, `global_runner.py`, and `asset_runner.py` (not just the definition + `__all__`).

## §4 — Fix D2: reconcile `global_runner.py` with the Phase β registry

The old `_build_writer_registry()` (lazy import of non-existent `brahmagyan_*` modules) is dead. Replace `global_runner.py`'s dispatch with the `discover_all()` + `get_writer()` + `WriterBase.run(ContextSpec)` substrate, AND make it write `asset_throughput` state so global builds light tiles.

**Decision (locked):** the production "Build" button never invokes `--global-build` (it always uses `--run-id`, see `jobInvoker.ts:116-127`). So `global_runner.py` is **not on the critical path** for the cockpit outcome. Two acceptable executor choices — pick **Option A** unless you find a live caller of `--global-build`:

- **Option A (preferred — reconcile):** rewrite `_run_asset_writer()` + delete `_build_writer_registry()` so the function resolves writers via `get_writer(asset_id)` and runs them with a `ContextSpec(asset_id=…, build_id=run_id, db_conn=conn, config={'chart_id': None})`, then transitions the global `asset_throughput` row (chart_id NULL — requires the D3 migration in §5) to `lit`. This keeps a working chart-independent path for future use.
- **Option B (retire):** if no live invoker of `--global-build` exists anywhere (`grep -rn "global-build\|execute_global_build" platform/ --include=*.ts --include=*.py --include=*.yaml --include=Dockerfile*`), mark `execute_global_build` deprecated with a `raise NotImplementedError("global-build retired; use --run-id per the unified-build campaign")` and keep `main.py`'s flag for a clear error. Document the decision in the commit body.

Whichever you pick, the rewrite MUST NOT reintroduce the stale module names. Author `platform/python-sidecar/pipeline/orchestrator/writers/tests/test_global_runner_registry.py` asserting that, after `discover_all()`, `get_writer('bg_reference')` and `get_writer('bg_ontology')` are non-None and that no symbol named `brahmagyan_sarani`/`brahmagyan_kalapancanga`/`brahmagyan_shastra` is referenced in `global_runner.py` (grep-style assertion on the source file).

**CHECKPOINT 4:** `grep -n "brahmagyan_sarani\|brahmagyan_kalapancanga\|brahmagyan_shastra\|_build_writer_registry" platform/python-sidecar/pipeline/orchestrator/global_runner.py` returns nothing (Option A) or only inside a deprecation comment (Option B).

## §5 — Fix D3: NULL-safe global-asset throughput

### §5.1 — Migration 181: global throughput unique index

> **Migration number:** `180` is already taken (`180_bg_reference_count_sql_fix.sql`, present at HEAD). Use **181**. Before authoring, re-confirm the ceiling: `ls platform/supabase/migrations/ | grep -E '^[0-9]' | sort -n | tail -1` and use the next integer if the campaign has added migrations ahead of this one.

Author `platform/supabase/migrations/181_asset_throughput_global_index.sql`:

```sql
-- Migration 181: global-asset throughput uniqueness.
-- L0 Brahmagyan assets are scope='global'. Their throughput state may be tracked
-- against a NULL chart_id (one shared global row per asset). The existing partial
-- unique index (migration 171) only covers chart_id IS NOT NULL, leaving global
-- rows without an ON CONFLICT arbiter. This adds the complementary partial index.
BEGIN;

CREATE UNIQUE INDEX IF NOT EXISTS asset_throughput_global_idx
  ON asset_throughput(asset_id)
  WHERE chart_id IS NULL;

COMMIT;
```

### §5.2 — NULL-safe matching in `asset_runner.py`

Replace `WHERE chart_id = %s` with `WHERE chart_id IS NOT DISTINCT FROM %s` in all four `asset_throughput` statements in `asset_runner.py`:

- `mark_asset_error` UPDATE (`:86-90`)
- the lit-transition UPDATE (`:188-198`)
- the downstream-stale UPDATE (`:224-229`)
- (the INSERT conflict target — see §5.3 below)

`IS NOT DISTINCT FROM` matches `NULL = NULL` as true and behaves identically to `=` for non-null values, so the proven per-chart path is unaffected.

### §5.3 — NULL-aware ON CONFLICT arbiter in the throughput upsert

The INSERT at `asset_runner.py:128-134` uses `ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL`, which only works for non-null chart_id. Branch on null-ness so both global and per-chart rows upsert correctly:

```python
    if chart_id is None:
        cur.execute(
            """INSERT INTO asset_throughput (asset_id, chart_id, state)
               VALUES (%s, NULL, 'building')
               ON CONFLICT (asset_id) WHERE chart_id IS NULL
               DO UPDATE SET state = 'building', last_error = NULL""",
            (asset_id,),
        )
    else:
        cur.execute(
            """INSERT INTO asset_throughput (asset_id, chart_id, state)
               VALUES (%s, %s, 'building')
               ON CONFLICT (chart_id, asset_id) WHERE chart_id IS NOT NULL
               DO UPDATE SET state = 'building', last_error = NULL""",
            (asset_id, chart_id),
        )
```

### §5.4 — `runner.py` skip-logic NULL-safety

`is_asset_complete` (`runner.py:68-75`) uses `WHERE chart_id = %s`. Change to `IS NOT DISTINCT FROM %s` so a global build correctly skips already-lit global assets on resume.

### §5.5 — Advisory lock with NULL chart_id

`locks.py:7-12` calls `hashtext(%s)` with `str(chart_id)`. For `chart_id=None`, `str(None) == 'None'` — a stable, valid lock key, so global builds serialize on a single `'None'` lock. This is acceptable (only one global build at a time). **No change required**, but add a one-line comment documenting it so a future reader doesn't "fix" it into a crash.

**CHECKPOINT 5:** migration 181 applies clean against prod; `grep -n "chart_id = %s" platform/python-sidecar/pipeline/orchestrator/asset_runner.py` returns nothing (all converted to `IS NOT DISTINCT FROM` or branched).

## §6 — Fix D4: lock the layer-level Build dispatch order with a test

`resolveBuildPlan` already topo-sorts the in-scope assets by `depends_on` (`plan.ts:157` calls `topoSort`). For `scope='layer', scope_target='brahmagyan', action='build'`, the candidate set is the 12 L0 assets filtered to `dormant` (`plan.ts:125-129`), then topo-sorted. Sequential execution by `runner.execute_run` (the plan is walked in order, `runner.py:115-130`) therefore honors the dependency DAG **without** needing parallel tiers. **Do not add parallelism** — it is out of scope (master plan §11 boundary; sequential is sufficient and simpler).

Add a regression test `platform/src/lib/build/__tests__/plan.l0-layer.test.ts` (vitest) asserting that for the 12-asset L0 registry (use a fixture mirroring migration 179 `depends_on`):

1. `resolveBuildPlan({scope:'layer', scope_target:'brahmagyan', action:'build', registry, throughput:emptyMap})` returns all 12 asset_ids.
2. In the returned `plan`, `bg_ontology` precedes `bg_yogas`, `bg_doshas`, and `bg_dasha_systems` (Tier 0 before Tier 1).
3. `bg_texts` precedes `bg_compendium_index` (the only registered cross-tier `depends_on` in migration 179: `bg_compendium_index depends_on ['bg_texts','reference_topic_tags']`).
4. No cycle is thrown.

> **Note for writer briefs:** migration 179 only encodes `depends_on` for the 4 *new* assets (`bg_yogas`/`bg_doshas`/`bg_dasha_systems` → `bg_ontology`; `bg_compendium_index` → `bg_texts`,`reference_topic_tags`). The fuller DAG in master plan §3 (e.g. `bg_rules` → `bg_texts`, `bg_text_index` → `bg_texts`) is **not yet** in `asset_registry.depends_on`. Each writer brief that introduces a cross-asset dependency MUST add an `asset_registry SET depends_on = …` UPDATE in its migration so the topo-sort dispatches it after its prerequisites. This brief does not back-fill those edges (it would pre-empt the writer briefs); it only guarantees the dispatch mechanism is correct and tested.

**CHECKPOINT 6:** `cd platform && npx vitest run src/lib/build/__tests__/plan.l0-layer.test.ts` → all green.

## §7 — Vimarśaka-FIX (programmatic gate for this brief)

Author `platform/scripts/vimarsaka/vimarsaka_fix.py`. Returns APPROVE / REJECT. Six checks:

```python
"""
Vimarśaka-FIX: orchestrator-fixes acceptance. APPROVE | REJECT.
Run: PROD_DB_URL=... python platform/scripts/vimarsaka/vimarsaka_fix.py
"""
import os, sys, subprocess, re

ROOT = 'platform/python-sidecar'

def check_discover_all_wired():
    """D1: discover_all() called in runner.py + asset_runner.py self-heal."""
    runner = open(f'{ROOT}/pipeline/orchestrator/runner.py').read()
    asset  = open(f'{ROOT}/pipeline/orchestrator/asset_runner.py').read()
    ok = 'discover_all()' in runner and 'discover_all()' in asset
    return ok, f'runner={"discover_all()" in runner} asset_runner={"discover_all()" in asset}'

def check_registry_populates():
    """D1: importing + discover_all() registers both Phase β writers."""
    out = subprocess.run([sys.executable, '-c',
        'import sys; sys.path.insert(0,".");'
        'from pipeline.orchestrator.writers import discover_all, list_writers;'
        'discover_all(); print(sorted(list_writers()))'],
        cwd=ROOT, capture_output=True, text=True)
    ok = 'bg_reference' in out.stdout and 'bg_ontology' in out.stdout
    return ok, out.stdout.strip() or out.stderr.strip()[:200]

def check_no_stale_global_registry():
    """D2: stale module names gone from global_runner.py."""
    src = open(f'{ROOT}/pipeline/orchestrator/global_runner.py').read()
    stale = [n for n in ('brahmagyan_sarani','brahmagyan_kalapancanga','brahmagyan_shastra',
                          'brahmagyan_samanvaya','brahmagyan_sutravali','brahmagyan_upaya_kosha',
                          'brahmagyan_text_index')
             if n in src and 'deprecat' not in src.lower().split(n)[0][-80:]]
    return len(stale) == 0, f'stale refs: {stale or "none"}'

def check_null_safe_throughput():
    """D3: no bare `chart_id = %s` left in asset_runner.py."""
    src = open(f'{ROOT}/pipeline/orchestrator/asset_runner.py').read()
    bare = re.findall(r'chart_id = %s', src)
    return len(bare) == 0, f'bare `chart_id = %s` occurrences: {len(bare)}'

def check_global_index_present():
    """D3: migration 181 global unique index exists in prod."""
    import psycopg
    conn = psycopg.connect(os.environ['PROD_DB_URL'])
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_indexes WHERE indexname = 'asset_throughput_global_idx'")
    ok = cur.fetchone() is not None
    conn.close()
    return ok, f'asset_throughput_global_idx present={ok}'

def check_plan_topo_test_exists():
    """D4: the layer-dispatch regression test file exists."""
    import os.path
    p = 'platform/src/lib/build/__tests__/plan.l0-layer.test.ts'
    return os.path.exists(p), f'{p} exists={os.path.exists(p)}'

CHECKS = [
    ('D1_discover_all_wired', check_discover_all_wired),
    ('D1_registry_populates', check_registry_populates),
    ('D2_no_stale_global_registry', check_no_stale_global_registry),
    ('D3_null_safe_throughput', check_null_safe_throughput),
    ('D3_global_index_present', check_global_index_present),
    ('D4_plan_topo_test_exists', check_plan_topo_test_exists),
]

def main():
    passed, failed = [], []
    for name, fn in CHECKS:
        try: ok, msg = fn()
        except Exception as e: ok, msg = False, f'{type(e).__name__}: {e}'
        print(f'{"✓ PASS" if ok else "✗ FAIL"}  {name}: {msg}')
        (passed if ok else failed).append(name)
    print(f'\nResult: {len(passed)}/{len(CHECKS)} PASS')
    if failed:
        print(f'FAIL: {failed}'); sys.exit(1)
    print('SEAL: orchestrator-fixes APPROVED')

if __name__ == '__main__':
    main()
```

**CHECKPOINT 7:** 6/6 PASS. Do not proceed to writer briefs' end-to-end proofs until this passes.

## §8 — End-to-end proof (the whole point)

After D1–D4 are in and Vimarśaka-FIX is green, prove the mechanism with the two writers that already exist (bg_reference + bg_ontology), against the native chart:

```bash
NATIVE_CHART="482012f1-710e-4a25-994a-93821f5871aa"   # confirm via SELECT id FROM charts WHERE subject_name ILIKE 'Abhisek%'

# 1. Reset the two assets to dormant for a clean Build
psql_prod -c "UPDATE asset_throughput SET state='dormant' WHERE chart_id='$NATIVE_CHART' AND asset_id IN ('bg_reference','bg_ontology')"

# 2. Trigger a layer-level Build via the API (or the cockpit button)
NATIVE_SESSION=$(cat /tmp/native_session)   # mint per Phase β brief §4.3 if absent
curl -s -X POST -b "__session=$NATIVE_SESSION" -H "Content-Type: application/json" \
  -d "{\"chart_id\":\"$NATIVE_CHART\",\"scope\":\"layer\",\"scope_target\":\"brahmagyan\",\"action\":\"build\"}" \
  https://madhav.marsys.in/api/cockpit/runs | jq .

# 3. The plan should include all DORMANT brahmagyan assets, topo-sorted.
#    With only the 2 Phase β writers implemented, the OTHER 10 assets will run, hit
#    "no writer registered (after discover_all)", and go to 'error' — EXPECTED at this
#    stage. bg_reference + bg_ontology MUST go to 'lit'.
sleep 30
psql_prod -c "SELECT asset_id, state, rows_written FROM asset_throughput WHERE chart_id='$NATIVE_CHART' AND asset_id LIKE 'bg_%' ORDER BY asset_id"
```

**Hard AC:** `bg_reference` and `bg_ontology` show `state='lit'` with `rows_written > 0` **via the orchestrator** (not a smoke script). This is the proof D1 is fixed. The other 10 assets in `error` is expected and acceptable until their writer briefs execute — they will all transition to `lit` once the full campaign runs.

## §9 — Hard stops

- §2 setup probe shows a NON-empty registry at bare import → a writer module is being imported somewhere unexpected; investigate before assuming D1 is moot.
- §4: a live invoker of `--global-build` is found (a cron, Cloud Run Job arg, or Dockerfile CMD) → do NOT pick Option B; reconcile (Option A) and re-verify that caller.
- §5: migration 181 fails because a duplicate global row already exists (`chart_id IS NULL` dupes) → dedupe first (`DELETE ... WHERE ctid NOT IN (SELECT min(ctid) ...)`), document it, then add the index.
- §8 end-to-end shows bg_reference/bg_ontology in `error` → read the `last_error`; if it is still "no writer registered", discover_all() wiring (§3) is incomplete — fix before declaring this brief done.

## §10 — Out of scope (explicit)

- Parallel tier execution (sequential topo-order is sufficient — master plan §11)
- Any writer implementation (each has its own brief)
- Migrating L0 to a NULL-chart throughput model (the per-chart-non-null model is proven; D3 is defense-in-depth only)
- Cockpit React components (registry-driven; auto-render — holistic design §5.4)
- The clear/rebuild proof (Document 15)
- `build_runs.chart_id` nullability (stays NOT NULL; the triggering native chart is always supplied)

## §11 — Commit (part of the single campaign PR)

This brief's changes are committed within the campaign branch `feature/l0-unified-build`. Do NOT open a separate PR — the master plan mandates ONE PR for the whole campaign (orchestrator fixes + 12 writers + integration). Suggested commit message:

```
fix(l0/orchestrator): wire writer discovery + global-asset throughput + layer-build guard

D1 (blocker): call discover_all() in runner.execute_run + asset_runner self-heal —
  registry was empty at runtime, so every Build hit "no writer registered".
D2: reconcile global_runner.py to the @register substrate (drop stale brahmagyan_* imports).
D3: migration 181 (asset_throughput_global_idx) + IS NOT DISTINCT FROM matching +
  null-aware ON CONFLICT arbiter — global (chart_id NULL) throughput can now transition.
D4: regression test locking layer-level topo-dispatch order (bg_ontology before
  yogas/doshas/dashas; bg_texts before compendium_index).

Vimarśaka-FIX: 6/6 PASS. End-to-end: bg_reference + bg_ontology light via orchestrator.

Parent: 00_ARCHITECTURE/L0_BRAHMAGYAN_BUILD_MASTER_v2_0.md
Brief:  00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_ORCHESTRATOR_FIXES_v1_0.md
```

---

*End of orchestrator-fixes brief (Document 2 of 15).*
