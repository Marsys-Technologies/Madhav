---
artifact: L1_PYJHORA_REVALIDATION_REBUILD_BRIEF_v1_0.md
canonical_id: L1_PYJHORA_REVALIDATION_REBUILD_BRIEF
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-24
purpose: >
  Prep + execution plan to regenerate ALL of Layer 1 (Gaṇita) on the PyJHora engine via the
  cockpit/orchestrator (delete-then-insert per asset, NOT a pre-wipe), validating both the engine
  (FORENSIC 7/7 + value-diff) and the orchestrator (full-layer build from the webpage). Runs on
  TWO charts: native 482012f1 (anchor validation) + non-native 1c826d5a (safe empty→full test).
  L0 IS UNTOUCHED — hard constraint. This is the template for the later L2/L3/L4 re-runs.
audience: Claude Code executor + operator
---

# L1 PyJHora Re-validation Rebuild — Prep + Execution

## §0 — Decisions locked (native, 2026-06-24)
- **Delete strategy:** orchestrator's per-asset delete-then-insert. NO upfront mass-wipe of L1 on
  the native chart (avoids the window where L1 is empty while L2+ still cite its fact_ids).
- **Charts:** BOTH. Native `482012f1-710e-4a25-994a-93821f5871aa` (FORENSIC anchors) +
  non-native `1c826d5a` (no downstream citations → safe place to test true empty→full orchestration).
- **L0 is UNTOUCHED.** No bg_ asset, no L0 table, no L0-scope clear. The cockpit clear route already
  requires typed confirmation for `scope='layer' && scope_target='brahmagyan'` — never trigger it.

## §0.1 — Verified prep state (Cowork, against main cf90bf96)
- ✅ Engine swap clean: NO dangling `natal_engine` import in live code (only a stale pytest-cache nodeid).
- ✅ Layer-scope build path EXISTS + registry-driven: `cockpit/refresh` does
  `SELECT asset_id FROM asset_registry WHERE layer=$1 AND is_active=true` for `scope='layer'`.
- ✅ Engine-fed set (8 writers, import pyjhora_adapter — the value-validation focus):
  ga_positions, ga_strength, ga_condition, ga_dashas, ga_sensitive, ga_structural, ga_tajaka, ga_vargas.
- ✅ Engine-independent set (5 writers, compute downstream of chart_facts): ga_medical, ga_prashna,
  ga_sade_sati, ga_vastu, ga_yoga. (If the 8 engine-fed reproduce, these follow.)
- ✅ Idempotency = scoped delete-then-insert already (`replace_prior_chart_facts/_dashas/_divisionals`
  delete WHERE chart_id AND natural-key = ANY(...)). The orchestrator gives clean per-asset replace.

## §GATE P0 — THE one open prep item (operator, prod DB via proxy :5433). BLOCKS everything.
The webpage layer-build trusts `asset_registry.layer` + `is_active`. Verify it enumerates EXACTLY
the intended L1 data assets — no missing, no stray service asset.
```sql
SELECT asset_id, layer, is_active, storage_type, count_sql IS NOT NULL AS has_count
FROM asset_registry
WHERE asset_id LIKE 'ga_%'
ORDER BY is_active DESC, asset_id;
```
Confirm:
- Every L1 DATA asset intended for bulk rebuild is `layer='L1'` (or whatever the L1 value is — confirm
  it) AND `is_active=true`.
- **`ga_transit_anchors` is NOT in the bulk set** unless it's genuinely a stored L1 asset — transit is
  "service-not-storage" per native ruling. If it's `is_active=true, layer='L1'`, decide: exclude from
  the rebuild plan, or confirm it's legitimately a stored anchor asset. STOP and report the table.
- Note any asset with `storage_type='service'` — those are health-probe, not data; the build will
  mark them lit via probe, not rows. Expected, but confirm none are mis-flagged as data.
RESULT of this query is the AUTHORITATIVE L1 MANIFEST. Everything downstream builds from it.

## §PREP — before any build
1. **(P0 above) registry manifest confirmed.**
2. **Image SHA gate:** confirm deployed `amjis-web` revision is built from current main (cf90bf96 or
   later) so the webpage drives the PyJHora code, not a stale image:
   `gcloud run services describe amjis-web --region asia-south1 --format='value(status.traffic[0].revisionName)'`
3. **SNAPSHOT current L1 for BOTH charts** (the value-diff reference — delete-then-insert overwrites,
   so capture first). Suggested: copy to throwaway tables, e.g.
   `CREATE TABLE _snap_chart_facts_pre_pyjhora AS SELECT * FROM chart_facts WHERE chart_id IN ('482012f1-...','1c826d5a-...');`
   and the same for chart_dashas, chart_divisionals. Keep until validation closes; drop after.
4. **Capture the PRE values of the gate metrics** from the snapshot (so post-build diff is mechanical):
   - native FORENSIC 7/7 (Sun=Capricorn, Moon=Purva Bhadrapada, Lagna=Aries ×5 ayanamsha,
     Tithi=Shukla Tritiya, Vara=Ravivara, Yoga=Shiva, Karana=Garaja);
   - sealed row counts per asset (chart_facts ~27,554; chart_dashas ~536,471; chart_divisionals ~21,635);
   - Mercury's sign in all 5 ayanamshas (the known sign-edge planet);
   - a sample of planetary longitudes for the value-diff.

## §EXEC-A — Non-native 1c826d5a FIRST (safe empty→full orchestration test)
Run this chart first BECAUSE it has no downstream L2-L5 citations — the safe place to prove the
orchestrator drives a full layer. Here the empty→full path is risk-free, so it doubles as the
orchestrator stress test.
1. From the cockpit Build webpage, drive a **layer-scope build, scope_target=L1**, for chart 1c826d5a.
   (This is the real orchestrator test — one action, full DAG in dependency order.)
2. Watch the Nirmāṇa tracker: every L1 asset transitions building→lit, correct DAG order
   (ga_positions before its dependents; ga_structural after ga_condition+ga_nakshatra), real row
   counts appear, NO asset stalls/errors/reconnects.
3. Confirm: asset_throughput correct (no chart-scoped row for any global asset — migration-331 guard
   holds), per-asset row counts plausible, the build_run plan covered exactly the P0 manifest.
4. GATE A: orchestrator drove the full L1 layer end-to-end from the webpage, all assets lit, no
   errors. If any asset fails → capture the error, STOP, diagnose (this is the orchestrator test
   doing its job — a failure here is a finding, not a setback).

## §EXEC-B — Native 482012f1 (engine validation against the anchors)
Only after EXEC-A proves the orchestrator path.
1. From the webpage, drive the layer-scope L1 build for 482012f1 (delete-then-insert per asset; no
   pre-wipe).
2. **FORENSIC 7/7 GATE (inviolable):** post-build, the 7 anchors must reproduce EXACTLY. Any miss =
   the engine swap moved a foundation anchor = HALT. Do not proceed; surface immediately.
3. **Value-diff vs snapshot (the engine-fed 8):** compare post-build vs `_snap_*` for planetary
   longitudes (arc-sec tolerance), divisional signs, dasha heads. Mercury sign-edge across 5
   ayanamshas is the known acceptable variance point — anything ELSE moving sign is a finding.
4. **Row-count + consistency gates:** per-asset counts match sealed (±expected); dasha↔chart_facts
   JOIN resolves 5/5 ayanamshas; run the L1_SEAL internal-consistency gates (`gates.py` / run_all_gates).
5. **Citation-resolution GATE:** a full L1 rebuild regenerates fact_ids. Confirm L2+ citations still
   resolve: `constituent_facts_array → chart_facts.fact_id`. If fact_ids are content-hashed → stable
   (expected pass). If they changed → every downstream citation dangles → this is a real finding to
   surface NOW, before L2 work builds on it.

## §CLOSE
- If all gates green on both charts: PyJHora is validated; re-seal L1 on the new engine (update
  L1_SEAL_v1_0.md + L0_SEAL note that L0 untouched + CURRENT_STATE: engine=PyJHora, L1 re-validated).
  Update the memory note [[project-pyjhora-engine-validation-deferred]] → resolved.
- Drop the `_snap_*` throwaway tables.
- This run is the TEMPLATE for the later L2/L3/L4 re-runs (same shape: snapshot → layer-build from
  webpage → anchor/value/count/citation gates → re-seal). Note any orchestrator rough edges found,
  for the L2 run.

## §HARD CONSTRAINTS (every step)
- **L0 UNTOUCHED** — no bg_ asset, no L0 table, never trigger L0-scope clear (typed-confirm guard).
- **No upfront mass-delete on the native** — orchestrator per-asset delete-then-insert only.
- **FORENSIC 7/7 exact on native** — any anchor move is an immediate HALT.
- **Every build from the webpage drives prod** — confirm image SHA first; data plane is prod.
- **A failed asset in EXEC-A is a FINDING (the orchestrator test working), not a quiet retry** —
  capture + diagnose.
- Snapshot BEFORE rebuild — the value-diff reference cannot be recovered after delete-then-insert.
