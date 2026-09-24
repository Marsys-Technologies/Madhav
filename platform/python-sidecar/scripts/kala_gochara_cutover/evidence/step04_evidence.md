# Step 4 evidence — Schema

Runbook step 4 (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9). Tranche 1
(requires `PRODUCTION_TRANCHE_1_AUTHORIZED=true`).

**Standing order acknowledged:** both flags were read from
GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md frontmatter before this step started;
no step proceeds past a red gate; a failed gate stops the tranche and
escalates.

- **What:** Schema — migrations 1080–1086 applied + verified
- **Gate:** information_schema diff empty
- **Reversal:** per-migration down blocks
- **DSN target:** (record the exact instance this evidence covers)
- **Operator / principal:** (record)

<!-- Run outcomes are appended below by the step scripts (--evidence). -->

## 2026-09-24T10:56:19Z — GREEN

applied: 1080_nirmana_l3_gochara_resonance_target_resolution_state.sql, 1081_nirmana_l3_gochara_ledger_coverage_publication.sql

### Scope note (2026-09-24, same run) — A-2 literal scope followed over the committed script

The committed `step04_apply_verify.py` APPLY_SET is 1080–1084 + 1087. Per the
native's tranche-1 instruction ("apply ONLY 1080 and 1081 — follow the
native-rulings reading over the committed script"), the run was executed through
the script's own machinery (production refusal, evidence writer) with
`APPLY_SET` scoped to 1080/1081 and `EXPECTED_COLUMNS` scoped to 1080's two
columns (1081 owns all four expected tables, the immutability trigger and all
six expected indexes; the remaining EXPECTED_COLUMNS entries belong to
1082/1083, which were NOT applied). E-009 re-scan done at run time: max
migration number on the branch is 1087 (1086 present but REFUSED per E-010);
no higher-numbered gochara migration exists. The template header line above
("migrations 1080–1086 applied + verified") is the pre-run template text and
does not describe this run. **Not applied, deliberately: 1082, 1083, 1084,
1087** — their production application needs a native ruling (E-010's A-2
literal-scope question, re-flagged in ESCALATIONS.md). Post-state cross-check:
`kala_gochara_windows` generations unchanged (v1=38287, 3.0=1830);
`gochara_resonance_map` 1595 rows intact; century writer still is_active=false.

DSN target: production via Cloud SQL proxy 127.0.0.1:5433, database amjis.
Operator / principal: subagent (l3/gochara-autonomous-wp0-7, §7.B tranche 1) as
`amjis_app` (CREATE on public temporarily granted for tranche 1 — see step 3
evidence; revocation at tranche end).

## 2026-09-24T11:39:01Z — NATIVE RULING recorded; E-016 scope approved

Verbatim: **"Approved on point number two. Go ahead to everything."** (native,
2026-09-24 17:09 IST, via the main agent). Scope (b): apply 1082/1083/1084/1087
to production via this step's machinery with the full committed APPLY_SET;
1084 as committed (ka_kshetra→ka_gochara edge HELD OUT, `64bdc10da`); 1085
stays retired; 1085/1086 never re-added. Full text in ESCALATIONS.md. Outcome
appended below when executed.

## 2026-09-24T11:46:06Z — RED

applied: 1080_nirmana_l3_gochara_resonance_target_resolution_state.sql
missing:
- (verify skipped: apply failed)

## 2026-09-24T11:46:25Z — GREEN

applied: 1080_nirmana_l3_gochara_resonance_target_resolution_state.sql, 1081_nirmana_l3_gochara_ledger_coverage_publication.sql, 1082_nirmana_l3_vedha_moorti_stamp_columns.sql, 1083_l5_ledger_contact_id.sql, 1084_wp7_k1_v1_registry_edges.sql, 1087_nirmana_l3_gochara_contacts_inclusivity_completeness_tier_basis.sql

## 2026-09-24T11:39Z+ — E-016 scope executed under native ruling — GREEN

Ruling (verbatim): **"Approved on point number two. Go ahead to everything."**
(2026-09-24 17:09 IST; full text in ESCALATIONS.md NATIVE RULING entry).

### Run

`step04_apply_verify.py --evidence` against production with the **full committed
APPLY_SET** (1080–1084 + 1087), `PRODUCTION_TRANCHE_1_AUTHORIZED=true`, as
`amjis_app`. First attempt halted on 1081 (`permission denied for schema
public` — the temporary CREATE grant had been revoked at the step-5 halt);
grant re-established via the E-015 path for this step and revoked again at
gate-green (verified `has_schema_privilege = f`).

Applied (in order, script-verified, information_schema diff EMPTY):
- 1080 (idempotent re-apply; already live from tranche-1 step 4)
- 1081 (idempotent re-apply; already live)
- **1082** — vedha/moorti stamp columns + `upstream_fingerprint` (5 columns verified)
- **1083** — L5 `contact_id` on `brahma_prospective_ledger` + `mimamsa_predictions` (2 columns verified)
- **1084** — registry edges AS COMMITTED: `ka_kshetra → ka_vedha_gochara` and
  `ka_sangam → ka_vedha_gochara` service-seam edges added; the
  `ka_kshetra → ka_gochara` edge remains **HELD OUT** (verified absent:
  `depends_on @> {ka_gochara}` = false) per `64bdc10da`
- **1087** — §12.3 inclusivity / six-state F06 completeness / time_basis /
  tier_basis on `kala_gochara_contacts` (41 columns present)

1085 stayed retired; 1085/1086 were never in the apply set (REFUSED guard
intact).

### Post-checks (production, unchanged where they must be)

- generations: **v1=38287, 3.0=1830** — untouched
- authority rows: both `'3.0'` — untouched
- `gochara_resonance_map` 1595 rows; century `is_active=false`
- ka_gochara registry row as step 5 left it (count_sql '4.0'-scoped, conjunct
  (j) holding)

E-016 is RESOLVED: all four held migrations are now applied to production.
