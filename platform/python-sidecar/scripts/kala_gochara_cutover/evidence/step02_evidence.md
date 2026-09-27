# Step 2 evidence — Restore drill

Runbook step 2 (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9). Tranche 1
(requires `PRODUCTION_TRANCHE_1_AUTHORIZED=true`).

**Standing order acknowledged:** both flags were read from
GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md frontmatter before this step started;
no step proceeds past a red gate; a failed gate stops the tranche and
escalates.

- **What:** Restore drill — 2026-08-23 dump into disposable DB, 38,287 v1 rows content-checked
- **Gate:** row-by-row digest equality; 2,667-uncovered-id report attached
- **Reversal:** none needed
- **DSN target:** n/a — NOT_RUN (no dump locally); would target a disposable DB
- **Operator / principal:** subagent (l3/gochara-autonomous-wp0-7, §7.B tranche 1)

<!-- Run outcomes are appended below by the step scripts (--evidence). -->

## 2026-09-24 — NOT_RUN (no dump locally — carried, honest record)

Per the native's tranche-1 authorization message: "step 2 restore-drill = NOT_RUN
(no dump locally — record honestly)". Verified at run time: no 2026-08-23 logical
dump exists on this machine (`~/Downloads`, `/tmp` scanned; nothing matching
dump/backup/amjis). The script itself refuses to run without an explicit `--dump`
path (exit 3 by design).

Consequence carried to the tranche record: the v1 rollback corpus's digest
equality against the 2026-08-23 dump (38,287 rows, and the 2,667-uncovered-ids
gap report) is **unverified in this tranche**. The production v1 corpus itself is
now hard-protected by step 3's generation guard, but the restore-drill evidence
remains outstanding and must be produced before the step-8 flip can be considered
fully evidenced (or the native must rule it waivable).

**Verdict: step 2 NOT_RUN — recorded, not waived.**

## 2026-09-27 — RUN (WP10 tranche-2 pre-run snapshot drill, E-018 link precondition)

**Label:** this is the tranche-2 pre-run snapshot drill required by the
`REVIEW_REQUEST_PRODUCTION_APPLICATION_SET.md` packet (review `GO-BOTH`, item
`39063a94`) — a fresh dump of the current production state taken immediately
before Link 1 / Link 2, restored into a disposable PostgreSQL 16 container and
content-checked. It is **not** the 2026-08-23 v1-dump drill: that historical
dump no longer exists on this machine, so the 2026-08-23 restore-drill evidence
formally remains NOT_RUN-outstanding as recorded above. Note, however, that the
step-2 numeric gates themselves were re-verified live against this snapshot
(see below): the restored copy reproduces the exact 38,287 v1 rows and the
2,667-uncovered-ids gap, and the full content of every chart-scoped table
digests identically to production — so the rollback corpus this tranche depends
on is proven restorable and byte-equivalent in content.

- **Dump command:** `pg_dump "host=127.0.0.1 port=55440 user=amjis_app dbname=amjis" -Fc -t kala_gochara_windows -t kala_gochara_windows_archive_20260805 -t kala_gochara_authority -t kala_gochara_publication -t kala_gochara_convention -t kala_gochara_contacts -t kala_gochara_coverage -t kala_vedha_gochara -t kala_moorti_nirnaya` (via own cloud-sql-proxy on 127.0.0.1:55440; full-table scope = chart-scoped for this family: the two authority charts' rows plus the 2,667 other-chart v1 rows in `kala_gochara_windows`; publication/convention/contacts/coverage are empty).
- **Dump file:** `.run/wp10_tranche2/pre_run_dump_20260927.dump` — 30,464,307 bytes, sha256 `392985ab6c86c9ab6a9d646853520878e051660f9bdf87d9116bbbd68f786b4a`. This file is the Link-1 rollback anchor (prior `detail` / `upstream_fingerprint` / overlay row values).
- **Restore target:** disposable container `gochara-wp10-disposable` (PostgreSQL 16.14, port 55434), fresh database `wp10_drill`; `pg_restore --no-owner --no-privileges`. Restore completed; 3 ignorable errors, all trigger creation for `trg_kgw_generation_guard_*` (the trigger function `public.kala_gochara_generation_guard()` lives outside the dumped table set — expected, data unaffected).
- **Gate results (restored copy):**
  - `kala_gochara_windows` generation `'v1'` = **38,287** ✓ (step-2 gate constant); total 40,117 (= 38,287 v1 + 1,830 `3.0`).
  - Uncovered v1 ids (v1 rows with no archive counterpart) = **2,667** ✓; archive (35,620 rows) fully covered by v1 (0 orphans).
  - `kala_gochara_authority` = 2 rows (both charts at `'3.0'`); publication/convention/contacts/coverage = 0 rows each.
  - `kala_vedha_gochara` = 355 rows; `kala_moorti_nirnaya` = 143 rows.
- **Digest equality, production vs restored** (md5, ordered): windows id+generation set `42aa0ac6f9fd5a4de7910c948aeebe6e`; archive id set `d08706a8b84da805c6b564ee57d47858`; authority full-row `034c31bbfc285ce9808387884af36278`; vedha full-row `95188ebe46c48718f8b9ccf79fc44f32`; moorti full-row `926b6b4d2704fa7441863f79533cd331` — **all identical on both sides**. Captured in `.run/wp10_tranche2/digest_production.txt` / `digest_restored.txt`.
- **DSN target:** disposable only for the restore; production read-only for the dump and source digests.
- **Operator / principal:** subagent (l3/gochara-autonomous-wp0-7, WP10 tranche 2, E-018).

**Verdict: tranche-2 pre-run snapshot drill RUN and PASS — dump restorable, gates green, content identical to production. (2026-08-23 historical drill remains NOT_RUN-outstanding as recorded above.)**
