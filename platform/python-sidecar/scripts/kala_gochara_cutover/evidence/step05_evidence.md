# Step 5 evidence — Registry re-pin (plan §6.3)

Runbook step 5 (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9). Tranche 1
(requires `PRODUCTION_TRANCHE_1_AUTHORIZED=true`).

**Standing order acknowledged:** both flags were read from
GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md frontmatter before this step started;
no step proceeds past a red gate; a failed gate stops the tranche and
escalates.

- **What:** Registry re-pin (plan §6.3) — count_sql/clear_tables/conjuncts (a)-(k)/depends_on; century clear_tables (F-30)
- **Gate:** count_sql relation = target_table; cockpit reads new count; Clear-proof test green; cockpit-0-between-5-and-6 is EXPECTED
- **Reversal:** step05_reversal.sql (snapshot restore)
- **DSN target:** `127.0.0.1:5433/amjis` (production, via cloud-sql-proxy `madhav-astrology:asia-south1:amjis-postgres`)
- **Operator / principal:** `amjis_app` (production application role; held a temporary `CREATE ON SCHEMA public` grant for the tranche)

## 2026-09-24 — FAILED / tranche HALT (E-017)

**Verdict: FAILED. Tranche 1 halted per fail-closed doctrine. Steps 6–10 not
started. The fix is prepared (1091) but deliberately NOT re-run — the native's
"go ahead" covered the E-015 privilege path, not script surgery.**

### What was attempted

`platform/migrations/1091_wp10_ka_gochara_registry_repin.sql` — the numbered
form of the preparation artifact `step05_registry_repin.sql` (verbatim copy at
attempt time; numbering per E-009 re-scan, max across all origin/* heads =
1090 on origin/sangam/stage3 `platform/supabase/migrations`; MIG-1 guard
`npm run guard:migration-numbers` PASS after placement).

Applied as `amjis_app` against production with `PRODUCTION_TRANCHE_1_AUTHORIZED=true`.

### Failure

```
ERROR:  malformed array literal: "[kala_gochara_windows, kala_gochara_contacts, kala_gochara_coverage]"
LINE 94: ...clear_tables = '[kala_gochara_windows, ...
```

Production `asset_registry.clear_tables` is `text[]`; the script wrote
`'[...]'` (JSON-style) instead of Postgres `'{...}'`. The transaction aborted
at the first UPDATE; every statement in the migration is inside one
transaction, so nothing was applied.

### Why rehearsal did not catch it

The rehearsal harness `platform/python-sidecar/scripts/kala_gochara_cutover/test_wp10_cutover.py`
(line ~137) declares `asset_registry.clear_tables` as **TEXT**, not `text[]`.
Against a TEXT column the `'[...]'` literal is legal, so the full rehearsal
passed green. Rehearsal-fidelity gap recorded for E-017; the harness column
type must be corrected to `text[]` before any future rehearsal is treated as
authoritative for this script.

### Production verified unchanged after the abort

Checked immediately after the error:

- `asset_registry` ka_gochara `count_sql` still the pre-step-5 `'2.0'`
  generation value;
- step-5 snapshot table absent (script's first write never committed);
- generations unchanged: v1 = 38287 rows, 3.0 = 1830 rows (identical to the
  step-3/step-4 post-state);
- century row `is_active = false` unchanged.

### Type-hazard sweep of the remainder of the script

Every other production type touched by the script was verified compatible
before deciding the defect is limited to the two array literals:
`kala_gochara_authority` exists; `kala_gochara_publication.horizon` is
`tstzrange`; window date columns are `date`; `active_sentences` jsonb;
`era_slice_key` text. The only defect is the two `'[...]'` clear_tables
literals (1091 lines ~90 and ~99; same lines in `step05_registry_repin.sql`).

### Fix prepared, NOT run

1091 was corrected in place: both `'[...]'` literals → `'{...}'`, with a
header note documenting the type correction found at tranche run. Per the
halt decision this corrected migration was **not** re-applied. The
preparation copy `step05_registry_repin.sql` is intentionally left unchanged
as the record of what was attempted.

### §12.14 digest-pin sweep (old count_sql / depends_on copies elsewhere)

- `platform/scripts/seed/asset_registry_seed.ts`: ka_gochara row (~line 2143)
  and century row (~line 2222) carry the OLD count_sql/depends_on. The seed
  has **no** clear_tables or integrity_check_sql fields at all, and on
  conflict it owns only `target_table` — count_sql/depends_on are preserved
  from the DB. So no seed update is required for field survival after step 5.
  NOTE: seed ka_gochara `target_table='kala_gochara_windows_v2'` while
  production is `'kala_gochara_windows'` — exactly what step 5 conjunct (j)
  gates on. Cherry-picked-but-unapplied migration **1072** would set
  `target_table='kala_gochara_windows_v2'` WHERE it is currently
  `'kala_gochara_windows'`; if 1072 applies after step 5, conjunct (j)
  breaks. Flagged for native ruling at merge time (see E-016/E-017).
- Migrations 670/854/865/1018 carry historical copies — immutable, no action.

### Temporary privilege grant revoked

The tranche-1 temporary `GRANT CREATE ON SCHEMA public TO amjis_app` (granted
under the E-015 resolution path) was revoked at halt:

```
SET ROLE data_plane_schema_owner; REVOKE CREATE ON SCHEMA public FROM amjis_app;
-- verified: has_schema_privilege('amjis_app','public','CREATE') = f
```

Re-grant on resume is one command (recorded in ESCALATIONS.md E-015/E-017).
1081 needs CREATE, so resuming step 5 requires re-granting first.
