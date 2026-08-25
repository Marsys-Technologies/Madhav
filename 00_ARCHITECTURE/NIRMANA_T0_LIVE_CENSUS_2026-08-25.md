---
artifact: NIRMANA_T0_LIVE_CENSUS_2026-08-25.md
canonical_id: NIRMANA_T0_LIVE_CENSUS
version: "1.0"
status: RECONCILED-CANDIDATE-PENDING-DEPLOY
campaign_id: nirmana-elevation
chart_id: 482012f1-710e-4a25-994a-93821f5871aa
observed_at_utc: 2026-08-25T05:51:18.674Z
---

# Nirmāṇa T0 live census — 2026-08-25

## Authority and status

This report reconciles the production PostgreSQL registry through a connection
that reports transaction_read_only=on. It is the evidence packet for the
candidate manifest at
00_ARCHITECTURE/control/NIRMANA_T0_MANIFEST_v1_0.json.

The candidate is **not yet a frozen campaign definition**. Its two forward
catalogue repairs, migrations 593 and 594, and the strengthened definition /
evidence API must merge and deploy before the manifest may be re-read, recorded,
and frozen in production.

At observation time, origin/main and Cloud Run revision amjis-web-01710-dv7
both identified 8d15808c25fedf90f919768ade436dfce3234c6f. Production
contained zero Nirmāṇa campaign-definition rows and zero evidence-event rows.

## Live denominator and graph

| Finding | Live result |
| --- | ---: |
| Registry assets | 128 |
| Dependency edges | 284 |
| Duplicate asset IDs | 0 |
| Dangling dependency edges | 0 |
| Self-dependencies | 0 |
| Backward-layer edges | 0 |
| Cycle paths | 0 |
| Maximum dependency path | 26 nodes |
| Active assets | 127 |
| Retired assets | 1 |

The manifest assigns every live registry row exactly once:

| Execution obligation | Assets |
| --- | ---: |
| build | 113 |
| probe | 8 |
| producer_covered | 3 |
| static_acceptance | 1 |
| empty_acceptance | 1 |
| source_acceptance | 1 |
| retired_with_disposition | 1 |
| unresolved | 0 |
| **Total** | **128** |

The three producer-covered identities come from the production writer AST, not
from a registry proxy:

- bg_medical_mappings covers bg_sign_medical and bg_nakshatra_medical.
- bg_transit_rules covers bg_transit_engine.

bg_gochara_citation_resolution is a migration-seeded static table;
bg_sarvatobhadra_grid is deliberately empty by adjudication; lel_events is
user-authored source data; and ka_gochara_sweep is the retained retired v1
corpus superseded by ka_gochara.

## Frozen wave candidate

Wave indices are the minimal same-layer topological depth derived from the live
dependency arrays. Cross-layer execution remains strictly L0 through L5.

| Layer | Candidate wave sizes | Assets |
| --- | --- | ---: |
| L0 | 31, 8, 1 | 40 |
| L1 | 1, 9, 3, 3, 2, 1 | 19 |
| L2 | 6, 2, 1, 4, 5, 1, 2, 1 | 22 |
| L3 | 10, 5, 1, 3, 1, 3 | 23 |
| L4 | 1, 5, 1, 1, 1 | 9 |
| L5 | 6, 1, 2, 2, 2, 2 | 15 |

Canonical candidate manifest SHA-256:

c0097895ab6b5318e8b9a2c34de34f7fe685eedfe9b8fb2293abe78593a5a3c4

Each asset also pins an individual SHA-256 fingerprint over its identity,
layer, dependencies, and live registry contract.

## Count, target, probe, and integrity contracts

- All 122 non-null registry count_sql contracts executed successfully against
  production. Canonical-chart parameters were bound to
  482012f1-710e-4a25-994a-93821f5871aa.
- The six assets without count_sql are service assets: bg_panchanga,
  bg_ephemeris_engine, ka_tulana, ka_graha_sancara, ka_dasha_kala, and
  ka_muhurta_seva.
- All eight service obligations have an executable probe path: the two L0
  services carry registry health_probe specifications; the other six have
  registered service writers whose run() is their readiness/self-test path.
- One live target contract is contradictory:
  bg_sky_calendar.target_table=bg_sky_events, although applied migration 561
  renamed the physical relation to bg_sky_calendar. Migration 594 and the
  accompanying writer/seed changes repair this forward. The candidate manifest
  records the post-594 canonical value and must be reverified after deploy.
- The registry currently carries zero non-null integrity_check_sql values.
  This remains an explicit F0/per-asset verification-contract gap; it earns no
  asset freeze credit merely because all count queries execute.

## Applied-migration source reconciliation

Production had four applied migration identities absent from current main.
Their exact Git-history bytes were restored without editing:

| Filename | Production SHA-256 |
| --- | --- |
| 588_remove_asset_build_protection.sql | a626570346237ed7b3cc609f986e333c615c83f89a7de082d3de46f88b39040c |
| 589_drop_orphaned_protection_functions.sql | 80ba7c0e5976411f188ca6b6469fb33e1ad15cf49dda063b6b309195b07f0e43 |
| 590_nirmana_m0_catalogue_contract_columns.sql | 813267f75e845c071a2025eb88e1d23aa4192263977267ad5a8b27da21ee2c4b |
| 591_nirmana_m0_partition_and_dead_flag_columns.sql | 666c0062f2c133ab09d52b2af1e2a87715aa62e5c16ea78ec793b21f7bf578bf |

Both distinct migration 588 filenames are already applied in production.
Their number collision is therefore disclosed, not renumbered or reported
resolved.

## Freeze gate

Before the candidate can become authoritative:

1. Merge and deploy the definition/evidence contract, recovered migration
   sources, writer repair, and forward migrations 593/594.
2. Verify production applied both forward migrations and that
   ka_gochara_sweep and bg_sky_calendar match their candidate contracts.
3. Re-run the 128-row registry fingerprint comparison, target-table existence,
   graph validation, and all 122 count contracts from fresh production reads.
4. Record one audited reconciling definition through the super-admin evidence
   API, then freeze that exact revision and digest.
5. Verify the tracker derives 128 total assets, the obligation totals above,
   and the exact layer/wave sizes from the frozen revision.

No T0 evidence in this report authorises an L0 rebuild before those gates pass.
