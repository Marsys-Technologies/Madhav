# A5.1 — migration window post-checks (runbook §2.1–2.6)

- Window run: 36785877387 on `main@5d800f9ea` (= #2765 merge sha), dispatched 2026-09-30 ~22:32Z,
  SUCCEEDED; 1153–1157 applied 22:35:37–42Z; full deploy green after.
- Post-checks run by stream-A 2026-10-01 (session after restart), read-only, against production.

## §2.1 — all five recorded, in order, hash-tracked ✓

`_migrations_applied` (filename, applied_at UTC):

| filename | applied_at |
|---|---|
| 1153_gochara_sky_event_substrate.sql | 2026-09-30T22:35:37.292Z |
| 1154_gochara_rule_path_registry.sql | 2026-09-30T22:35:39.019Z |
| 1155_gochara_relationship_record.sql | 2026-09-30T22:35:40.174Z |
| 1156_gochara_eval_window.sql | 2026-09-30T22:35:41.350Z |
| 1157_gochara_av_polarity_declaration.sql | 2026-09-30T22:35:42.488Z |

Exactly 1153..1157, applied_at ascending in filename order.

## §2.2 — tables present ✓

All 18 expected tables present in `public`: ka_gochara_sky_convention, ka_gochara_physical_object,
ka_gochara_sky_event, ka_gochara_contact_identity, ka_gochara_generation_seal, ka_gochara_convention_bridge,
ka_gochara_contact (1153); ka_gochara_predicate, ka_gochara_factor, ka_gochara_rule_path,
ka_gochara_rule_path_prerequisite, ka_gochara_rule_path_soft_factor, ka_gochara_rule_path_seal (1154);
ka_gochara_relationship_record, ka_gochara_record_prerequisite (1155); ka_gochara_eval_window,
ka_gochara_eval_window_record (1156); ka_gochara_av_polarity_declaration (1157).

## §2.3 — constraints convalidated ✓

`pg_constraint` `NOT convalidated` on ka_gochara_% relations: **0 rows**.

## §2.4 — triggers present ✓

59 triggers on ka_gochara_% tables. Reconciliation against the five files on `origin/main`:
57 `CREATE TRIGGER` + 2 `CREATE CONSTRAINT TRIGGER` (`ka_gochara_rr_finalize`,
`ka_gochara_rpr_finalize` in 1155) = 59. Full set matches; nothing missing, nothing extra.

## §2.5 — read-only smoke ✓

- `ka_gochara_generation_is_sealed('482012f1-710e-4a25-994a-93821f5871aa', '3.0')` → **f** (expected f)
- `count(ka_gochara_sky_event)` = 0; `count(ka_gochara_rule_path)` = 0 (expected 0)

## §2.6 — existing data untouched ✓

- 11-conjunct `integrity_check_sql` for asset `ka_gochara` (post-1150 UTC date-compare form) evaluated
  verbatim → **integrity_passed = t**.
- `kala_gochara_windows` post-window state: generation `v1` = 38,287 rows
  (md5 checksum `7efb08c0b5e2c97446617c80376b2fe9`), generation `3.0` = 1,830 rows
  (md5 checksum `5de67c6032ffe7f931495ed1cdec95cb`). The window ran DDL-only migrations 1153–1157,
  which contain no writes to `kala_gochara_windows`; these values are recorded as the post-window baseline.
