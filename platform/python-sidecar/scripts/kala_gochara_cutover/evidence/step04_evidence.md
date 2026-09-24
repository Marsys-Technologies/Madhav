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
