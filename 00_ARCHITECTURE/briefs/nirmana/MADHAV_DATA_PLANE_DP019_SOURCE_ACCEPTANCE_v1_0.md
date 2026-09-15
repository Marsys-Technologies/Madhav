---
artifact: MADHAV_DATA_PLANE_DP019_SOURCE_ACCEPTANCE
version: "1.0"
status: SOURCE_PACKET_ACCEPTED
accepted_on: 2026-09-16
strategy_decision: DP-SD-019
execution_task: "Execution — Data Plane / 01a0998a-8240-7631-97ce-36c6d4734fde"
execution_branch: codex/madhav-data-plane-execution
---

# DP-SD-019 source acceptance

## Accepted source

The routine-delivery correction was independently accepted at exact branch tip
`1fa8f1f8f16afa30ae5142227149b5afbdb80214` and integrated as
`7c5885939` plus documentation child `d60bb0736`. It separates the read-only
semantic state probe, one-time protected bootstrap and ordinary migration
barrier. The ordinary marked path has no protected environment or bootstrap
credentials. Unknown, regressed, partial, failed and cancelled predecessor
states fail closed; bootstrap and routine writes share cross-ref serialization;
web, MCP and pipeline deployment remain behind successful routine migration.
The independent exact-tip verdict reports no CRITICAL/HIGH/MED/LOW finding.

The first Yojaka candidate `06c3d944dd33a68a783850d2d79bb49a41d9ff67`
was rejected with one MED finding: its compatibility scalar selected maximum
confirmation across domains even though `ph_nimitta` binds that scalar to the
primary domain. Correction `7697c43b31da3655c2add7cda128a57ca4afd44e`
aligns the scalar with the authoritative primary-domain contract while retaining
the complete per-domain map. The accepted integrated source is `cbae6cfa1` plus
correction `fbf7803dc`.

Yojaka now preserves the accepted L2 domain array, domain salience, signed
valence, contrary-signal evidence, all compatible promise identifiers, stable
ordering and de-duplication, and exact chart/ayanamsha/signal/fact context. It
uses legacy keyword inference only when the L2 domain column is genuinely
absent and does not fabricate a domain from an explicitly empty or invalid
current value. The receiving-consumer fixture traverses the real
`PhNimittaWriter` metadata loaders and proves a legitimate explicit-primary
distinction without cross-domain support inflation. Independent exact-tip
re-review reports no HIGH/MED/LOW finding.

## Verification

- routine-delivery focused Vitest: 23 passed;
- routine-delivery TypeScript, ESLint, `actionlint`, YAML parse and topology:
  PASS;
- Yojaka focused source contracts: 116 passed;
- complete post-correction L3 suite: 1,525 passed, 41 skipped and 2 expected
  failures;
- reviewer Yojaka recheck: 81 passed and 3 skipped;
- combined-tree Yojaka focused recheck: 102 passed;
- writer inventory regeneration changes exactly `ka_yojaka`, from
  `2c591d8c214b12c647f9bdcce370efd236a5700695c6f88251e36084d6afe04a`
  to `11576f295562d9a2e1b0be31da4baf47798f83bf0be470eb67bb6b3a2ff49f22`.

The representative complete-linkage benchmark for seven domains and 140
promises is 15.934 microseconds per signal for projection and 31.335
microseconds including JSON, versus 0.508 and 1.822 microseconds respectively
for the old lossy path. This is an accepted semantic-completeness cost, not a
speed improvement or empirical predictive-performance claim.

## Non-claims and next gate

This acceptance is source-local. It performs and proves no provider, IAM,
secret, role, shared-database, migration, build, deployment, physical generation
or consumer-value mutation. A fresh exclusive operation-specific lease and all
recorded protected-environment, identity, credential, backup/restore and canary
prerequisites remain mandatory before live cutover. Physical upstream and L3
generations, deployed consumer integration and measured value remain unreached;
terminal L3 acceptance is therefore still 0/22.
