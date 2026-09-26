# T2 hand-verification protocol — nikasha-test Phase 2

For each sampled asset, verify **every** verdict in the census JSON's `measurements` map by an
independent query or grep written from this protocol — never by re-running asset_census.py. Record
per check: census verdict, your verdict, AGREE/DISAGREE, and the evidence (SQL/grep + result).
A verdict of `NOT_GENERIC` or `NO_DETECTOR` is verified by confirming the claimed precondition
(e.g. no universe declared in registry fields the inspector reads).

Environment (production, read-only — verify `SHOW default_transaction_read_only;` = on first):
  source /Users/Dev/madhav-l3/dbenv.sh && export PGPORT=5433
  (exports PGHOST/PGUSER/PGPASSWORD/PGDATABASE; PGOPTIONS enforces read-only)

Independent checks:

- Build.registered: grep -rn "@register(['\"]<asset_id>" platform/ --include=*.py (both quote styles);
  compare with `SELECT asset_id FROM asset_registry WHERE asset_id='<id>'` and the census's
  writer_files. Census PASS requires both grep hit and registry row agreement.
- Build.contract: open the writer file; confirm class subclasses WriterBase; has run(ctx) XOR
  plan_substeps+run_substep; no ctx.db_conn.commit()/close() call; no INSERT into asset_throughput;
  chart_id/birth_params from ctx.config.
- Build.target: `SELECT target_table FROM asset_registry WHERE asset_id='<id>'` vs census value; then
  `SELECT to_regclass('public.<table>')`.
- Build.dag: `SELECT depends_on FROM asset_registry WHERE asset_id='<id>'`; verify each entry exists
  in asset_registry; eyeball cycle only if chain <4 deep, else note.
- Build.count_integrity: `SELECT count_sql, integrity_check_sql FROM asset_registry WHERE asset_id=…`
  non-null both; run count_sql (read-only) and compare to live count.
- Build.completion: latest build_run_assets row for the asset:
  `SELECT rows_written, state, finished_at FROM build_run_assets WHERE asset_id='<id>' ORDER BY finished_at DESC NULLS LAST LIMIT 1`
  vs `SELECT count(*) FROM <target_table>` (census compares rows_written to live).
- Build.exercised: `SELECT count(*), DISTINCT scope FROM build_run_assets JOIN build_runs USING (run_id) WHERE asset_id='<id>'`.
- Build.history: counts by state from build_run_assets; verdict rule: FAIL if latest errored/aborted,
  PARTIAL if errored before but latest complete, N/A if never ran.
- Build.dep_liveness: for each depends_on entry, does any writer exist that could light it
  (registry has_writer / build history state='lit' reachable). Judge: all deps lit => PASS.
- Earn.build_record: does the build record carry rows_per_second / duration (asset_throughput or
  build_run_assets fields)? Census FAILs on rows_per_second NULL.
- Cost.baseline: same build-cost fields; 'not instrumented' is legal — census FAILs when state=lit
  but no instrumentation; verify the underlying fields.
- Ldgr.source_presence (L0): does the target table carry a source/citation column and is it populated?
  `SELECT count(*) FROM <t> WHERE <source_col> IS NULL` — pick the column by inspecting \d <t>.
- Idem.pattern: grep the writer's own SQL for ON CONFLICT (L0) or DELETE…INSERT scoping (L1+);
  PARTIAL means delegation suspected — check whether a seeder module does the upsert.
- Vocab.alias: `SELECT count(*) FROM brahma_ontology WHERE …` alias set non-empty for the asset's
  entity class (inspect brahma_ontology schema first).
- Vocab.identity: declared key from registry (`SELECT key_columns…` or census "declared key" string);
  run `SELECT <keys>, count(*) FROM <t> GROUP BY 1,… HAVING count(*)>1` and count duplicates.
- Dens.served: grep platform/ capability modules (TypeScript) for references to the asset's table /
  query module; for each module found check for `density_contract` declaration.
- Complete.depth: column population census: `SELECT count(*) AS n, count(col) …` per column of the
  target table (or information_schema + generated SQL); compare NEVER-populated list.
- Count.floor: registry floor vs live count: `SELECT …floor… FROM asset_registry` and live count.
- Complete.width / Carr.detector / Reach.fields: verify the precondition absence (no declared
  universe / no per-asset D1-D3 detector exists in repo / exposure census is per-capability) by
  targeted grep; these are constant-verdict checks.

Sampling (per layer, ≥8 assets, every kind present): use the census JSON fields has_writer,
target_table (null → service/static), live_rows (0 → empty-by-design?), never_exercised list,
catalog_status. Cover: writer-backed data, service, multi-table, static/migration-seeded,
empty-by-design, has-writer-but-never-run — whichever exist in that layer; say which kinds were
absent.

Output per layer: `handverify/<L>_T2.md` — table of asset × check × AGREE/DISAGREE + evidence, a
per-check false-positive count, and a list of every DISAGREE with full reproduction.
