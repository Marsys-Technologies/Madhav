---
brief_id: RETRIEVAL_11C_a
status: PENDING
authored_by: Claude (Cowork) 2026-04-29
authored_for: Claude Code execution
session_type: implementation (Python sidecar ingest change; build pipeline run; deploy; verify)
related_plan: 00_ARCHITECTURE/RETRIEVAL_PRODUCTIVITY_PLAN_v0_1_DRAFT.md (§2.3 fix F3.2)
predecessor: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_RETRIEVAL_11C_PROBES.md (status: COMPLETE; probe data at 00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_2026-04-29.txt)
parallel_stream_note: |
  A separate UI/UX modernization stream is actively running via the default
  CLAUDECODE_BRIEF.md at the project root. That brief and ALL UI/UX paths
  (platform/src/components/**, platform/src/app/**, platform/src/hooks/**)
  are off limits this session. This brief is Python-sidecar-side only —
  it touches the data ingest layer, NOT the Next.js TypeScript app.
estimated_time: 1–2 days

scope_summary: |
  Resolve 105 orphan CGM edges by ingesting their missing target nodes into
  l25_cgm_nodes:
    • 101 orphans target UCN.SEC.* nodes that exist in UCN_v4_0.md but were
      never written to the cgm_nodes table.
    • 4 orphans target KARAKA.DUAL_SYSTEM_DIVERGENCE — a meta-concept node
      defined in the cgm_contradicts edge manifest but never registered as a
      CGM node.
  Implementation: extend the Python ingest pipeline (cgm_extractor) to emit
  UCN section nodes + the KARAKA aux node alongside the existing CGM_v9_0
  nodes. Run the build pipeline. Re-run probe 4 to verify.

may_touch:
  - platform/python-sidecar/pipeline/extractors/cgm_extractor.py        # extend with UCN+aux
  - platform/python-sidecar/pipeline/extractors/__init__.py             # add export if needed
  - platform/python-sidecar/pipeline/main.py                            # only if orchestrator wiring needed
  - platform/python-sidecar/tests/**                                    # update + add tests
  - platform/python-sidecar/pipeline/extractors/aux_cgm_nodes.py        # CREATE if separating aux nodes
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_RETRIEVAL_11C_a.md          # status update at session end
  - 00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_POST_11C_a.txt       # CREATE post-deploy verification
  # Read-only references (do NOT edit):
  - 025_HOLISTIC_SYNTHESIS/UCN_v4_0.md                                   # source of UCN sections
  - 035_DISCOVERY_LAYER/cgm_contradicts_edges_manifest_v1_0.json         # KARAKA references
  - 035_DISCOVERY_LAYER/cgm_supports_edges_manifest_v1_0.json
  - 035_DISCOVERY_LAYER/cgm_edges_manifest_v1_0.json
  - platform/scripts/retrieval_diagnostic_probes.sql                     # for re-running probe 4

must_not_touch:
  - CLAUDECODE_BRIEF.md                                                  # ROOT — UI/UX stream owns this
  - 00_ARCHITECTURE/RETRIEVAL_PRODUCTIVITY_PLAN_v0_1_DRAFT.md            # reference only
  - 00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_2026-04-29.txt        # historical artifact
  - platform/src/**                                                      # TypeScript / Next.js — DIFFERENT STREAM
  - platform/src/components/**                                           # UI/UX scope
  - platform/src/app/**                                                  # UI/UX scope
  - platform/src/hooks/**                                                # UI/UX scope
  - platform/src/lib/**                                                  # NOT changing query pipeline this session
  - platform/python-sidecar/pipeline/extractors/ucn_extractor.py         # do NOT modify; consume only
  - platform/python-sidecar/pipeline/writers/cgm_nodes_writer.py         # writer is correct as-is
  - platform/python-sidecar/pipeline/writers/cgm_edges_writer.py         # do NOT modify
  - platform/python-sidecar/pipeline/writers/ucn_sections_writer.py      # do NOT modify
  - platform/migrations/**                                               # NO schema changes — fits existing schema
  - 025_HOLISTIC_SYNTHESIS/CGM_v9_0.md                                   # source-of-truth; read-only
  - 025_HOLISTIC_SYNTHESIS/MSR_v3_0.md                                   # not in scope
  - 035_DISCOVERY_LAYER/REGISTERS/**                                     # not in scope
  - Any file under 03_DOMAIN_REPORTS/, 04_REMEDIAL_CODEX/, 05_TEMPORAL_ENGINES/ — out of scope
  - Any retrieval-tool TypeScript file (cgm_graph_walk.ts, msr_sql.ts, etc.) — code path is correct; data is the fix

acceptance_criteria:
  AC.1: cgm_extractor.py exports a new function (e.g., extract_ucn_section_nodes) that takes repo_root and returns ≥80 UCN section node dicts in l25_cgm_nodes shape, with node_id starting with "UCN.SEC.".
  AC.2: cgm_extractor.py exports an additional aux-node source containing exactly one node with node_id "KARAKA.DUAL_SYSTEM_DIVERGENCE", node_type "KARAKA_META", and a properties dict that includes the conflict_type "rahu_as_pk" plus a brief description.
  AC.3: Either extract_cgm_nodes is extended to merge UCN+aux nodes into its output, OR pipeline/main.py is extended to call the new functions and write the additional rows alongside the CGM_v9_0 nodes — pick whichever is cleanest. The merged set must NOT collide with existing CGM_v9_0 node_ids (collision check required).
  AC.4: The 17 specific UCN section node_ids the orphan edges target ARE present in the merged set: UCN.SEC.II.2, UCN.SEC.III.4, UCN.SEC.IV.1, UCN.SEC.IV.2, UCN.SEC.IV.3, UCN.SEC.IV.4, UCN.SEC.IV.5, UCN.SEC.V.4, UCN.SEC.V.5, UCN.SEC.V.7, UCN.SEC.VI.1, UCN.SEC.VI.3, UCN.SEC.VI.4, UCN.SEC.VII.4, UCN.SEC.VIII.2, UCN.SEC.VIII.4, UCN.SEC.IX.2. Verify by name before running the build pipeline.
  AC.5: Build pipeline runs successfully end-to-end (extract → staging → validate → swap_to_live). l25_cgm_nodes live count goes from 234 to ≥315 (234 base + ≥80 UCN sections + 1 KARAKA = ≥315).
  AC.6: cgm_extractor.extract_cgm_edges runs against the new node_ids set; valid edges go from 21 to ≥122 (gain of 101 from UCN-targeted edges) and ideally to 126 (gain of 4 more from KARAKA-targeted edges); orphan edges drop from 105 to ≤4 (and ideally to 0).
  AC.7: Python sidecar tests pass at the pre-existing baseline (no NEW failures introduced; pre-existing failures unchanged is acceptable).
  AC.8: Cloud Run revision amjis-web is rebuilt and serving 100% via bash platform/scripts/cloud_build_submit.sh (the script reads .env.local substitutions automatically). The TypeScript app code is unchanged but redeployed so cgm_graph_walk picks up the new graph topology at runtime.
  AC.9: PROBE 4 from platform/scripts/retrieval_diagnostic_probes.sql is re-executed against the live database. Output is captured to 00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_POST_11C_a.txt. Output shows valid_edges count and orphan_edges count consistent with AC.6 (no UCN.* targets remain in orphan_reason; KARAKA may or may not remain depending on whether AC.2 fully resolved).
  AC.10: This brief's frontmatter `status` is updated to COMPLETE.
  AC.11: No file under platform/src/** or under any UI/UX path is modified. `git status` should show ONLY: cgm_extractor.py changes, possibly main.py changes, possibly aux_cgm_nodes.py creation, test changes, and the two new files in 00_ARCHITECTURE/BRIEFS/ (this brief + the probe results capture).
---

# CLAUDECODE_BRIEF — RETRIEVAL_11C_a (F3.2 orphan resolution)

## §1 — Why this session

The diagnostic probes (predecessor brief; results in `00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_2026-04-29.txt`) confirmed that 101 of 105 orphan edges in `l25_cgm_edges` target `UCN.SEC.*` nodes that don't exist in `l25_cgm_nodes`. Another 4 target `KARAKA.DUAL_SYSTEM_DIVERGENCE`, also missing. The fix is structurally simple: ingest those nodes. Once ingested, the existing `cgm_extractor.extract_cgm_edges` orphan-classification pass (lines 220–238) will flip them to `status='valid'` automatically on the next pipeline run.

**Critical naming-convention fact.** `extract_ucn_sections` in `pipeline/extractors/ucn_extractor.py` emits section IDs as `UCN.{part}.{sub}` (e.g., `UCN.IV.1`). The edge manifests in `035_DISCOVERY_LAYER/cgm_*_manifest_v1_0.json` target `UCN.SEC.{part}.{sub}` (e.g., `UCN.SEC.IV.1`). They differ by the `SEC.` prefix. Your work this session must produce CGM nodes with the `UCN.SEC.` prefix — DO NOT modify `ucn_extractor.py` or `l25_ucn_sections.section_id` to match. The two tables are independent; `l25_ucn_sections` keeps its `UCN.{part}` IDs, and `l25_cgm_nodes` gets new `UCN.SEC.{part}` rows. This is intentional separation.

## §2 — Background facts you need

- The CGM ingest pipeline lives in `platform/python-sidecar/pipeline/`.
- `pipeline/extractors/cgm_extractor.py` exports `extract_cgm_nodes(repo_root)` (parses CGM_v9_0.md → 234 node dicts) and `extract_cgm_edges(repo_root, node_ids)` (parses CGM_v9_0.md inline edges + 3 manifest files → 127 edge dicts with status field).
- `pipeline/writers/cgm_nodes_writer.py` writes node dicts to `l25_cgm_nodes_staging` then swaps to `l25_cgm_nodes` (DELETE+INSERT atomic). Schema columns: `node_id`, `node_type`, `display_name`, `properties` (JSONB), `source_section`, `build_id`.
- `pipeline/extractors/ucn_extractor.py` exports `extract_ucn_sections(repo_root)` (parses UCN_v4_0.md → ≥50 section dicts with `section_id`, `parent_section_id`, `domain`, `title`, `content`, `derived_from_signals`, `source_lines`, `build_id`).
- `pipeline/main.py` (lines 236–238) is the orchestrator that calls each extractor → writer pair sequentially. UCN sections and CGM nodes are currently independent stages; they don't talk to each other.
- The 4 KARAKA.DUAL_SYSTEM_DIVERGENCE edges are defined in `035_DISCOVERY_LAYER/cgm_contradicts_edges_manifest_v1_0.json` (CGM_CONTRADICTS_001..004). Each has `conflict_type: "rahu_as_pk"`. They originate from MSR.226, MSR.320, MSR.321, MSR.432.
- The full list of 17 UCN section node_ids the orphan edges target is in AC.4 above. Total target node_ids you must add: 18 (17 UCN sections + 1 KARAKA).

## §3 — Implementation steps

### §3.1 — Add `extract_ucn_section_nodes(repo_root)` in cgm_extractor.py

Function signature:

```python
def extract_ucn_section_nodes(repo_root: str) -> list[dict[str, Any]]:
```

Implementation outline:

1. Import `extract_ucn_sections` from `pipeline.extractors.ucn_extractor`.
2. Call `sections = extract_ucn_sections(repo_root)`.
3. For each section, build a CGM-node dict:
   - `node_id`: `section["section_id"].replace("UCN.", "UCN.SEC.", 1)` — replaces ONLY the first occurrence.
   - `node_type`: `"UCN_SECTION"`
   - `display_name`: `section["title"]`
   - `properties`: a dict containing
     - `"domain"`: `section.get("domain")`
     - `"parent_section_id"`: `section.get("parent_section_id")`
     - `"derived_from_signals"`: `section.get("derived_from_signals", [])`
     - `"content_excerpt"`: `section["content"][:500]` (truncate to keep node row reasonable; full content remains in `l25_ucn_sections`)
     - `"source_layer"`: `"L2.5"`
   - `source_section`: `section.get("source_lines", "UCN_v4_0")`
4. Validate: assert that every node_id starts with `"UCN.SEC."`. Assert at least 80 rows produced. Raise ValueError with diagnostic message on failure.
5. Return the list.

After implementing, write a unit test (in `platform/python-sidecar/tests/`) that calls `extract_ucn_section_nodes` against the repo_root and asserts: (a) ≥80 rows, (b) all 17 specific node_ids from AC.4 are present, (c) every node_id starts with `UCN.SEC.`, (d) no node_id collision with the output of `extract_cgm_nodes(repo_root)`.

### §3.2 — Add aux KARAKA node source

Two valid implementations:

**Option A (preferred — tighter scope).** Add a constant in `cgm_extractor.py`:

```python
_AUX_CGM_NODES: list[dict[str, Any]] = [
    {
        "node_id": "KARAKA.DUAL_SYSTEM_DIVERGENCE",
        "node_type": "KARAKA_META",
        "display_name": "Karaka Dual-System Divergence",
        "properties": {
            "concept_class": "contradiction_target",
            "conflict_type": "rahu_as_pk",
            "axis": "7-karaka system vs 8-karaka system",
            "description": (
                "Meta-concept node representing the 7-karaka vs 8-karaka system "
                "divergence in the chart. CONTRADICTS edges from MSR signals point "
                "here when the signal's correctness depends on which karaka system "
                "is canonical. Resolution: chart-wide karaka system must be locked "
                "(see edge manifest steelman_reconciliation_excerpt fields)."
            ),
            "referenced_signals": ["SIG.MSR.226", "SIG.MSR.320", "SIG.MSR.321", "SIG.MSR.432"],
            "source_layer": "L2.5_meta",
        },
        "source_section": "035_DISCOVERY_LAYER/cgm_contradicts_edges_manifest_v1_0.json",
    },
]


def extract_aux_cgm_nodes(_repo_root: str) -> list[dict[str, Any]]:
    """Return small aux CGM nodes that don't have a natural source file."""
    return list(_AUX_CGM_NODES)
```

**Option B.** Create `platform/python-sidecar/pipeline/extractors/aux_cgm_nodes.py` with the same content if you prefer file separation. Either is acceptable.

### §3.3 — Wire UCN + aux nodes into the build

Choose one of two paths:

**Path I (preferred — no orchestrator change).** Modify `extract_cgm_nodes` in cgm_extractor.py to merge in UCN section nodes + aux nodes before returning:

```python
def extract_cgm_nodes(repo_root: str) -> list[dict[str, Any]]:
    # ... existing parsing of CGM_v9_0.md ...
    rows = [...]  # existing 234 nodes

    # NEW: merge UCN section nodes
    ucn_rows = extract_ucn_section_nodes(repo_root)
    aux_rows = extract_aux_cgm_nodes(repo_root)

    # Collision guard
    existing_ids = {r["node_id"] for r in rows}
    for new_row in ucn_rows + aux_rows:
        if new_row["node_id"] in existing_ids:
            raise ValueError(
                f"node_id collision detected: {new_row['node_id']} "
                f"already in CGM_v9_0 nodes — refusing to overwrite."
            )

    rows.extend(ucn_rows)
    rows.extend(aux_rows)

    # Re-validate count range (existing assertion at line 86–90)
    count = len(rows)
    if count < 10 or count > 5000:
        raise ValueError(...)
    return rows
```

**Path II.** Leave `extract_cgm_nodes` alone; modify `pipeline/main.py` to call the new functions and pass the merged list to `CGMNodesWriter.write_to_staging`. Slightly more invasive on the orchestrator side.

Path I is preferred because the writer's contract is "rows from extract_cgm_nodes" and the merge logic stays close to the extractor. Document the choice in a one-line code comment.

### §3.4 — Update / add tests

1. Locate existing `cgm_extractor` tests (likely `platform/python-sidecar/tests/extractors/test_cgm_extractor.py` or similar).
2. Add a test for `extract_ucn_section_nodes` per §3.1 step 5.
3. Add a test that `extract_cgm_nodes(repo_root)` (post-merge) returns ≥315 rows and contains all 18 named node_ids from AC.4 + KARAKA.
4. Add a test that node_id collision raises ValueError (mock or synthesise the collision case).
5. Run the python-sidecar test suite: `cd platform/python-sidecar && python -m pytest -x` (or whatever runner the project uses — check `pyproject.toml` / `pytest.ini`). Target: NO new failures vs the pre-existing baseline.

### §3.5 — Run the build pipeline locally

The build pipeline writes to Cloud SQL via the Auth Proxy. Before running the pipeline:

1. Confirm Auth Proxy is up on `127.0.0.1:5433` (reuse existing proxy if running; otherwise `bash platform/scripts/start_db_proxy.sh &`).
2. Set `DATABASE_URL` env var to a connection string that uses the proxy.
3. Identify the pipeline entry point — likely `python -m pipeline.main` or similar. Read `platform/python-sidecar/pipeline/main.py` to confirm CLI args (build_id, dry-run flag, stage selector).
4. Run the pipeline restricted to `cgm_nodes` + `cgm_edges` stages if the orchestrator supports stage selection. Otherwise run the full pipeline (other stages should be idempotent re-ingests with no harm).
5. Confirm via psql: `SELECT COUNT(*) FROM l25_cgm_nodes;` returns ≥315. `SELECT status, COUNT(*) FROM l25_cgm_edges GROUP BY status;` returns valid:≥122, orphan:≤4.

If the pipeline fails on a stage other than cgm_nodes/cgm_edges (e.g., a sade_sati or eclipses stage errors out), document the failure in the session output and proceed only if the cgm_nodes + cgm_edges stages completed successfully. Do NOT debug unrelated stage failures this session.

### §3.6 — Deploy

The TypeScript app code is unchanged this session, but `cgm_graph_walk` reads the live `l25_cgm_*` tables on every query, so a fresh deploy is **not required** for the new graph topology to take effect — the next query against amjis-web will see the new graph automatically. **However**, run a redeploy anyway to keep the build trail clean:

```
bash platform/scripts/cloud_build_submit.sh
```

Confirm via `gcloud run revisions list --service amjis-web --region asia-south1 --project madhav-astrology --limit 3` that a new revision is serving 100%.

### §3.7 — Verify

1. Re-run probe 4 against the live database. Use the same Auth Proxy connection. Capture output to `00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_POST_11C_a.txt`.

   Quickest way:

   ```
   psql "postgresql://amjis_app@127.0.0.1:5433/amjis" \
     -c "SELECT status, COUNT(*) FROM l25_cgm_edges GROUP BY status;" \
     -c "SELECT COUNT(*) FROM l25_cgm_nodes;" \
     -c "SELECT orphan_reason, COUNT(*) FROM l25_cgm_edges WHERE status='orphan' GROUP BY orphan_reason ORDER BY COUNT(*) DESC;" \
     > 00_ARCHITECTURE/BRIEFS/RETRIEVAL_PROBE_RESULTS_POST_11C_a.txt
   ```

2. The output should show:
   - `l25_cgm_nodes` count: ≥315
   - `l25_cgm_edges` valid count: ≥122
   - `l25_cgm_edges` orphan count: ≤4 (ideally 0)
   - `orphan_reason` breakdown: no rows starting with `target_not_in_cgm_nodes: UCN.SEC.*`. KARAKA.DUAL_SYSTEM_DIVERGENCE row should be absent if AC.2 was fully implemented.

### §3.8 — Close

1. Set this brief's `status: COMPLETE` in the frontmatter.
2. In the closing message, print:
   - Pre-fix counts (from RETRIEVAL_PROBE_RESULTS_2026-04-29.txt): nodes=234, valid=21, orphan=105.
   - Post-fix counts (from RETRIEVAL_PROBE_RESULTS_POST_11C_a.txt): nodes=N1, valid=N2, orphan=N3.
   - Cloud Run revision deployed.
   - Test result counts (failures: same as baseline / new failures introduced).

## §4 — Hard constraints

- **Python sidecar only.** This session does NOT modify any TypeScript file under `platform/src/**`. The query-pipeline TS code is correct as-is; the fix is purely in the data ingest layer.
- **Do not modify `ucn_extractor.py`.** The naming convention difference between `l25_ucn_sections.section_id` (`UCN.X`) and `l25_cgm_nodes.node_id` (`UCN.SEC.X`) is intentional and preserved. Your transformation lives in the new `extract_ucn_section_nodes` function in `cgm_extractor.py`.
- **Do not modify the writers.** `cgm_nodes_writer.py` and `cgm_edges_writer.py` are correct as-is. The only change needed is in the extractor that feeds them.
- **No schema changes, no migrations.** Everything fits the existing `l25_cgm_nodes` schema. If you find yourself wanting to alter the table, stop — the design constraint is to use the JSONB `properties` column for any per-node-type variation.
- **Do not touch the active root brief** `CLAUDECODE_BRIEF.md`. That belongs to the UI/UX stream.
- **Do not modify any retrieval-tool TypeScript file** (cgm_graph_walk.ts etc.). The TS code path is correct; the fix is data, not code.
- **Halt-and-report on blockers.** If the build pipeline fails on the cgm_nodes or cgm_edges stage, do not improvise a workaround — print the error, leave the system in its previous state if possible, and stop. The native will diagnose and decide.

## §5 — Closing checklist

Before claiming COMPLETE:

- [ ] AC.1 verified — new function present, returns ≥80 rows.
- [ ] AC.2 verified — KARAKA aux node defined.
- [ ] AC.3 verified — merge wired (Path I or II), collision guard in place.
- [ ] AC.4 verified — all 17 named UCN section node_ids present in the merged set (assert by name).
- [ ] AC.5 verified — `l25_cgm_nodes` count ≥315 in live DB.
- [ ] AC.6 verified — `l25_cgm_edges` valid ≥122, orphan ≤4 in live DB.
- [ ] AC.7 verified — pytest output matches baseline.
- [ ] AC.8 verified — Cloud Run revision listed.
- [ ] AC.9 verified — POST_11C_a.txt exists and shows expected numbers.
- [ ] AC.10 — this brief's status set to COMPLETE.
- [ ] AC.11 verified — `git status` shows only the expected files (no platform/src/** changes).

---

*End of CLAUDECODE_BRIEF_RETRIEVAL_11C_a. Status: PENDING.*
