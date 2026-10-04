# Real-PostgreSQL environment for the L2 wrapper (production-mirrored privileges)

`test_l2_wrapper_real_pg.py` and the S-L2 rehearsal need a disposable PostgreSQL 15 whose schema, owners and ACLs mirror production and
whose session is the production pipeline login `data_plane_builder` (no superuser). Nothing here touches production except one
READ-ONLY `pg_dump -s` through the `suvarna_reader` proxy.

1. Start a throwaway PostgreSQL 15 with pgvector (e.g. `docker run -d --name omit_bo_N -e POSTGRES_PASSWORD=pw -e POSTGRES_DB=dp_role_test -p 127.0.0.1:54331:5432 pgvector/pgvector:pg15`).
2. As the container superuser: `00_bootstrap_roles.sql` (roles with the attributes read from production `pg_roles`; schema `public` owned by `amjis_app` for the dump load).
3. `01_stubs_pre_dump.sql` (stubs for the tables a reader cannot dump: charts, chart_grants and a few FK targets).
4. Schema-only dump from production through the reader, excluding every table the reader cannot SELECT (`pg_dump -s -n public -T ...`); load it as superuser.
   The dump carries the production owners (`data_plane_schema_owner` owns `public`, `data_plane_l1_owner` / `data_plane_l2_owner` own the protected tables), ACLs, functions and triggers.
5. `python3 extract_history_ddl.py <the excluded data-plane relation names>` writes `02_missing_history_tables.sql` and `04_grants_from_migrations.sql` from migrations 1035/1036 (verbatim statements); apply both as superuser.
6. Memberships and preflight grants (migrator in the three owner roles; SELECT on the stubbed tables to the owners), then copy the reference rows the lifecycle functions read
   (`asset_registry`, `l2_data_plane_asset_outputs`, `fact_category_ownership` or its migration-1219 equivalent) with a reader `\copy`.
7. `10_fixture_chart_and_l1.sql` inserts the synthetic chart; the test creates its L1 head through the REAL `open_l1_data_plane_generation` / `complete_l1_data_plane_partition`.

Run: `L2_WRAPPER_REALPG_ADMIN_URL=... L2_WRAPPER_REALPG_BUILDER_URL=... python -m pytest tests/l2/test_l2_wrapper_real_pg.py -m integration`.
Stop and delete the container by its exact name when done.
