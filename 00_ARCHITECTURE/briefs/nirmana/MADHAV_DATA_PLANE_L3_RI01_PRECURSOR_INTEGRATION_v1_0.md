---
artifact: MADHAV_DATA_PLANE_L3_RI01_PRECURSOR_INTEGRATION
version: "1.0"
status: HELD_ON_RATIFICATION_AND_ROLE_CUTOVER
observed_at: 2026-09-15T06:07:00+05:30
strategy_decision: DP-SD-017
accepted_w0_source_tip: 00a161195
hardening_commit: 8bda677aa67747e027a2fc2c5609addc2fee63c9
reviewed_tip: 6a7ecc17117163debcc4b742aa183f17588ef621
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

This packet integrates the accepted L1 and L2 generation migrations. It
relocates them from the legacy migration directory to the binding active
directory, renumbers them around the open planner/Purna stack, and hardens the
generation-admission and replay boundaries exposed by independent review. It
updates filename-dependent tests/evidence and proves the combined migration
surface in disposable PostgreSQL.

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

## 3. Relocation and reviewed hardening

| Accepted candidate | Active release file | Accepted SQL identity | Hardened raw SHA-256 | Hardened SQL identity |
|---|---|---|---|---|
| platform/migrations/1033_data_plane_l1_producer_history.sql | platform/supabase/migrations/1035_data_plane_l1_producer_history.sql | 73619035b97f4da12485c890c76b14860232f912da2e089fd3cd8f3c54333b33 | c1718fb5662c3c47a45112fcc2a840d915b6f9ec14b1ed2cfd7ab845c1b2e46c | 9de44b8285da2d85a1a335f2698e41491f1bedc149114abe1531b2b3d37b572f |
| platform/migrations/1034_data_plane_l2_producer_generations.sql | platform/supabase/migrations/1036_data_plane_l2_producer_generations.sql | 9a21a222823a69eb6e8063a3a5caf0bb18f39700d2a106606bdb2ec0e33f0e57 | 2e9b1af7a1f7e08b671fb29032bfe54d5924dbe38ac5e05bfe5e9e3d2b262621 | eef1dc67912fcde2e58544410e2e91d7676997c1c15d03c8965b5450fc12a982 |

The initial relocation preserved normalized SQL identity. Independent security
review then found three HIGH release defects. L1 and L2 generations could be
forged or reset after completion, undeclared or excess partitions could earn
completion, and an arbitrary L2 build could manufacture an empty replay receipt.
The candidate now changes executable SQL intentionally to close those findings:
declared partition contexts, immutable build intents, foreign-key closure,
state/progress guards, declaration cardinality checks and mutation-free exact
completion replay. The changed identities above supersede the relocation-only
identities; neither migration has been applied to the shared target.

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
| L1/L2 focused contracts | PASS, 75; zero skips with `L2_CONTRACT_DATABASE_URL` bound to the disposable cluster |
| disposable PostgreSQL 15 direct apply/reapply, 1035 then 1036 | PASS; current hardened files applied twice exactly |
| generation/admission database negatives | PASS; L1/L2 exact replay is generation-row mutation-free; undeclared partitions, undeclared L2 builds, N+1 declarations, completed reset, forged completion and orphan partition receipts all reject |
| migration-runner and number-guard unit tests | PASS, 67 |
| L3 writer inventory and layer pin | PASS; only `ka_bhavishya_lekha` and `ka_kshetra` writer digests changed, L3 aggregate `139bde3133923b4513aa2eb8cb0046a0a03291a7adfb2cedfbee8fa14fbaa16d` pinned to reviewed W0 tip `00a161195392a6fd5be7db2c964e0c621e05530b` |
| whole-file analysis-layer pin check | HELD outside L3: committed L0, L1, L2 and L4 aggregates are stale against the branch inventory; L3 is current and no other layer was repinned |
| ESLint | PASS with 0 errors and 590 warnings after eight deterministic lint-fix commits |
| TypeScript | PASS, 0 errors |
| repository full unit run | HELD; 1,083 files passed, 71 skipped; 11,575 tests passed, 662 skipped and 2 todo, but 8 receipt tests reject current L0 aggregate `3dda261170ee0dc879071d43d8e266e5cbf5c715775f94d2a27edaeee1c9e146` against frozen `5125cccb119713391964576a7442171e353f0e5be8c2c8554b1b009a6c922839` |
| git diff --check | PASS |

The first disposable attempt used incomplete stub row types and failed before
commit on missing chart_dashas.dasha_row_id and asset_registry.depends_on.
Both migration transactions rolled back. The disposable database was recreated
with the required pre-data shapes and rerun under set -e; both initial
applications and both exact reapplications then passed. This setup correction
is not counted as migration evidence.

## 5. Review findings and release gates

Independent exact-tip re-challenge PASS at `6a7ecc17117163debcc4b742aa183f17588ef621`
confirmed all three code-owned HIGH findings closed with no additional
CRITICAL/HIGH/MED/LOW finding. One HIGH security finding remains deliberately
open: production
migrations and the current build path authenticate as `amjis_app`, which owns
objects it creates. `role_orchestrator` is NOLOGIN, `amjis_app` is not its member,
and grants or revokes cannot constrain an object owner. The migration closes
default PUBLIC access and documents intended privileges, but it does not claim
owner isolation. A protected-owner/SECURITY-DEFINER design needs an administrator
to create the non-owner build login, protected L1/L2 owner roles and exact
membership/ownership cutover; that external action is not an ordinary migration
running as `amjis_app`.

The full test run also exposes a reserved-governance blocker rather than an L3
test defect. Seven intentional L0 writer changes moved the generated L0 aggregate
from the frozen receipt above. The full pin checker additionally reports stale
L1, L2 and L4 aggregates inherited on this branch. RI-01 reconciled its own two
changed L3 writers and exact reviewed L3 pin only; it did not restate any other
layer. Prior rulings reserve those pins to their adjudicating/owning authorities,
so RI-01 must not silently regenerate or repin them.

Accordingly this packet is held before PR, protected merge or shared apply on two
authorities: (1) explicit reconciliation of the protected non-L3 provenance pins,
including the frozen L0 receipt, and (2) the database-administrator
role/credential/ownership cutover. After both, the exact
committed tip needs fresh independent migration/security review and governed full
checks. Immediately before protected merge it must also refresh origin/main, the
open-PR migration sweep, production applied identities and the coordination
lease/claims. Protected CI is not deployment proof: RI-01 closes only after the
exact served source revision and both `_migrations_applied` rows are independently
observed.
