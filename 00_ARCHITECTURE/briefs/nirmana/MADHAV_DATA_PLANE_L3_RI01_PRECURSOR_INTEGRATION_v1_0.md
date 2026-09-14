---
artifact: MADHAV_DATA_PLANE_L3_RI01_PRECURSOR_INTEGRATION
version: "1.0"
status: CANDIDATE_AWAITING_INDEPENDENT_REVIEW
observed_at: 2026-09-15T05:14:00+05:30
strategy_decision: DP-SD-017
accepted_w0_source_tip: 00a161195
protected_main_observed: 731e311f0b8f5f84db2f152b93951e1d3d50d89a
planner_head_observed: fccfbb5ab11eadb33259ff987738068753d12ebc
coordination_commit: ef132c87dbf483aae0b2c805a61deeb9bee0ba1e
lease: MADHAV-DATA-PLANE-L3-RI01-20260915
reserved_migrations:
  - 1035_data_plane_l1_producer_history.sql
  - 1036_data_plane_l2_producer_generations.sql
---

# L3 RI-01 precursor generation integration

## 1. Scope and non-claims

This packet integrates the already accepted L1 and L2 generation migrations
without reopening their semantics. It relocates them from the legacy migration
directory to the binding active directory, renumbers them around the open
planner/Purna stack, updates their filename-dependent tests and evidence, and
proves the combined migration surface in disposable PostgreSQL.

No shared migration has yet been applied by this candidate. No protected merge,
deployment, generation selection, corpus build/rebuild, L3 data materialization,
L4/L5 work, consumer-value result or empirical-performance result is claimed.
Physical W1 remains held.

## 2. Fresh namespace and shared-target reconciliation

At authoring time:

- origin/main was 731e311f0b8f5f84db2f152b93951e1d3d50d89a and stopped
  at migration 1032 across both migration directories.
- PR 2597 was open/clean and owned 1033_planner_inquiry_lifecycle.sql; the
  stacked Purna Wave 1 PR 2599 owned
  1034_nirmana_purna_anvesana_wave1_output_digest_specs.sql.
- Purna Wave 5 changed planner migration 1033 before any shared application.
  The complete open-PR sweep found no migration number above 1034.
- A read-only production transaction authenticated as retrieval_census_ro.
  _migrations_applied returned zero rows for both data-plane filenames and
  both planner/Purna filenames. The L1, L2 and planner head/lifecycle relations
  were absent, and zero of the six exact Purna digest specifications existed.
  This checks both the tracker and semantic side effects rather than inferring
  non-application from either alone.
- The only shared target authorized by this packet was that production
  instance. The local cluster below is disposable validation state.

The exclusive RI-01 release lease and migration 1035/1036 claims were committed,
pushed and read back at
origin/campaign-coordination@ef132c87dbf483aae0b2c805a61deeb9bee0ba1e.

## 3. Content-identity-preserving transformation

| Accepted candidate | Active release file | Original SHA-256 | Candidate SHA-256 | SQL identity before/after |
|---|---|---|---|---|
| platform/migrations/1033_data_plane_l1_producer_history.sql | platform/supabase/migrations/1035_data_plane_l1_producer_history.sql | b174f6423d9e9ca12b2c5816f4cdedba799e8067013438842713a194e7808300 | ec1c4e2cce8e068df3e5e0a29bebe53e6d43b77baea6f3aa2be811d4bd9dedec | 73619035b97f4da12485c890c76b14860232f912da2e089fd3cd8f3c54333b33 |
| platform/migrations/1034_data_plane_l2_producer_generations.sql | platform/supabase/migrations/1036_data_plane_l2_producer_generations.sql | 4e611d4b97cb56766b4561660a36ce1f064cfeadb7fba8e115b30d393aeb2a48 | c35f3a424939f46608d07a825a30a12409d54d7b5ff3556fc76c80bf932e2619 | 9a21a222823a69eb6e8063a3a5caf0bb18f39700d2a106606bdb2ec0e33f0e57 |

Raw hashes differ only because the first-line filename/header declaration was
renumbered. The repository migration runner's comment/whitespace-normalized SQL
identity is byte-for-byte identical before and after for each file. No
executable statement changed.

Filename-dependent validators, tests and current evidence now resolve the
active-directory paths. One combined-schema negative-test fixture was corrected
to supply the accepted L1 generation table's required pins and completion
fields; it previously passed only when L1's real schema was absent.

## 4. Candidate validation

| Check | Result |
|---|---|
| migration number guard | PASS; highest 1036, next 1037, no new collision |
| L1 contract validator | PASS; 19/19 writers, zero findings |
| L2 contract validator | PASS; 23/23 adopted writers, zero violations |
| L1 focused contracts from sidecar and repo-root working directories | PASS, 52 each |
| L2 focused source tests without disposable DB | PASS, 31; 3 DB-gated skips |
| disposable PostgreSQL 15 direct apply/reapply, 1035 then 1036 | PASS; both head relations present, 36 L2 output-manifest rows, 11 intended L1 capture triggers |
| combined-schema L2 database negatives | PASS, 34; zero skips |
| git diff --check | PASS |

The first disposable attempt used incomplete stub row types and failed before
commit on missing chart_dashas.dasha_row_id and asset_registry.depends_on.
Both migration transactions rolled back. The disposable database was recreated
with the required pre-data shapes and rerun under set -e; both initial
applications and both exact reapplications then passed. This setup correction
is not counted as migration evidence.

## 5. Review and release gate

The candidate still requires independent migration and security review of an
exact committed tip, then the governed full checks. Immediately before any
protected merge it must refresh origin/main, the full open-PR migration sweep,
the production applied-identity query and the coordination lease/claims.
Protected CI is not deployment proof: RI-01 closes only after the exact served
source revision and both _migrations_applied rows are independently observed.
