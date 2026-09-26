# W-L0-7 Readings — Verdict Matrix v1.0

**Date**: 2026-09-26
**Runner**: `scripts/l0harness/run_readings.py` (+ `read_serve.ts`)
**Evidence**: `run_readings_20260926.log` (full stdout), `reading_verdicts.json` (machine state)
**Fixture**: `madhav_l0w7_fixture` on 127.0.0.1:55433 (rebuilt in step 0, BUILD GREEN, state-B gate green: sutravali 3002/7, sunapha present, exact post-1123 link set, seeded firing present, 11 L1 heads)
**Design law**: `00_ARCHITECTURE/briefs/nirmana/L0_W_L0_7_PACKET_REPORT_v1_0.md` v1.5, "Predicted movement" frozen matrix

Execution was the real decorated path (`dry_run=False`) as direct
`session_user=data_plane_builder` (1035:578-580 / 1036:805-807 / 1036:941-943
check `session_user`; SET ROLE insufficient). PERTURB DELETE ran as superuser
per the brief. No consumer/writer/data-plane SQL was edited; every failure is
recorded as a finding with verbatim error text.

## Frozen matrix vs measured

| Verdict | Frozen prediction | Measured | Verdict |
|---|---|---|---|
| **V-C0-S3** | sunapha absent from `query_yoga_catalog` output | `total_matching=0`, sunapha rows=0 | **PASS** |
| **V-R2-S4** | sunapha firing row STILL PRESENT (stale window); `catalog_classical_citations` → NULL | row id=1 present (`ayanamsha=surya_siddhanta_classical`), `catalog_classical_citations=NULL` | **PASS** |
| **V-R1-S5** | firings lose exactly `(chart, surya_siddhanta_classical, sunapha)`; every other row byte-identical | could not measure: R1 rerun did not complete — `InsufficientPrivilege: permission denied for table build_runs` inside `open_l1_data_plane_generation` (F-W-L0-7-9); disclosed grant-workaround probe also failed — `RaiseException: L1 partition ayanamsha_lahiri_chitrapaksha has undeclared empty output` (F-W-L0-7-5) | **UNMEASURED** |
| **V-R2-S6** | sunapha firing row absent entirely | could not measure: premise broken (R1 rerun failed); actual served state: row PRESENT | **UNMEASURED** |
| **V-R3-S7** | `catalog_ids ['sunapha']→[]`; `rule_ids {a5d58ce9…, cf36fd63…}→[]`; citations `['bphs:30','saravali:38']` unchanged; `classical_sources_jsonb` NOT NULL; corroboration stays 2 | could not measure: R3 rebuild did not complete — `ContractError: missing completed selected L1 dependencies: ['ga_yoga']` (F-W-L0-7-8) | **UNMEASURED** |

**Step 9 (RESEED + REPLAY): green.** sunapha catalog row re-inserted
(`jsonb_populate_record`, rowcount=1), post-1123 link set exact, replay C0
`total_matching=1`, R2 `catalog_classical_citations` restored.

## Findings measured by this run

| ID | Where | Verbatim error | Substance |
|---|---|---|---|
| **F-W-L0-7-9** (new) | R1 baseline + step-5 rerun, first substep | `InsufficientPrivilege: permission denied for table build_runs` — PL/pgSQL `open_l1_data_plane_generation` line 18 at IF | SECURITY DEFINER owner `data_plane_l1_owner` holds no SELECT on build_runs/build_run_assets (grant probe: only amjis_app has any); the decorated R1 dies inside open_l1 (1035:599-611) before the writer body. Same defect shape in `open_l2_data_plane_generation` (1036:951-963, owner `data_plane_l2_owner`) — unmeasurable here, R3 fails earlier. Masks every downstream R1/R2-verdict measurement. |
| **F-W-L0-7-5** | R1, first substep (`ayanamsha_lahiri_chitrapaksha`), measured via disclosed grant workaround | `RaiseException: L1 partition ayanamsha_lahiri_chitrapaksha has undeclared empty output` — `complete_l1_data_plane_partition` line 75 at RAISE | ga_yoga plans 5 ayanamsha substeps (`ga_yoga.py:45-52`); the fixture seeds chart_facts for surya_siddhanta_classical only, so the first substep finds 0 facts → returns 0 rows (`ga_yoga_writer.py:147-156`, `:2822-2828`) → complete_l1 rejects the undeclared empty partition (1035:1385-1389; `asset_registry.target_floor=63 ≠ 0`). Identical pre- and post-perturbation. No ga_yoga generation/head is ever created. |
| **F-W-L0-7-8** | R3 baseline + step-7 rebuild, pre-flight | `ContractError: missing completed selected L1 dependencies: ['ga_yoga']` | `_resolve_upstream_context` (`bodha_writers/data_plane_contracts.py:262-266`) raises before bind/open because ga_yoga (in bo_laksana's transitive L1 closure) has no completed generation head — consequence of F-W-L0-7-9/-5. |
| **F-W-L0-7-7** | auxiliary probe (non-verdict) | `InsufficientPrivilege: permission denied for table chart_facts` | 1036 pg_temp bind shadows owned by `data_plane_l2_owner` (SECURITY DEFINER `bind_l2_exact_inputs`) carry relacl NULL; pg_temp precedes public in name resolution, so the writer role's unqualified `chart_facts` reads land on a shadow it cannot SELECT. Re-measured through the real bind path with the 11-head vector (bind validates elements vs heads only, 1036:813-828 — succeeds even with ga_yoga headless). |

## Open mechanics — answered by code reading + this run

- **(a) open semantics for a fresh run_id**: `open_l1_data_plane_generation`
  with a fresh uuid creates a brand-new generation (`ON CONFLICT DO NOTHING`,
  1035:687-692; compat checks only on reopen); `correction_of` is optional
  (1035:645-651). The harness generates a fresh `uuid4()` per run.
- **(b) bind vector element shape**:
  `{layer, asset_id, generation_id, semantic_output_digest}`
  (`bodha_writers/data_plane_contracts.py:360-375`); bind validates each
  element against the heads table only (1036:813-828).
- **(c) bo_laksana is HEAVY**: `plan_substeps` emits one `aya_<ayanamsha>`
  substep per the 5 ayanamshas (`bo_laksana.py:3378-3382`) through the
  decorated `run_substep`; ctx needs a mutable config carrying `chart_id`
  (`begin_observation`, `bo_laksana.py:395-439`).
- **(d) session role**: the decorated path requires a direct connection as
  `data_plane_builder` — 1035:578-580, 1036:805-807 and 1036:941-943 check
  `session_user`, which `SET ROLE` does not change. The runner connects via
  the orchestrator's own factory (`pipeline/orchestrator/db.py:39-43`).

## Could-not-measure register

- **V-R1-S5 / V-R2-S6**: blocked by F-W-L0-7-9 (grant defect) and, under the
  disclosed workaround, F-W-L0-7-5 (fixture fact coverage). Additional
  premise risk even with both fixed: the sunapha formation rule is
  unevaluable from seeded facts (no MOON position row), so a successful R1
  rerun would DELETE the seeded firing and not recreate it — the frozen
  "lose exactly the sunapha row" requires writer re-derivation the fixture
  does not support.
- **V-R3-S7**: blocked by F-W-L0-7-8 (no ga_yoga head); downstream L2-stage
  defects (F-W-L0-7-1 open-before-bind, F-W-L0-7-7 shadow ACL, F-W-L0-7-9's
  L2 twin) are staged behind it and individually re-measured only by probe.
- **Whether production grants SELECT on build_runs to the data-plane owner
  roles**: unverifiable from the rehearsal cluster (production proxy password
  unavailable); the fixture replays the production-probed grant set, where
  the grant is absent.
