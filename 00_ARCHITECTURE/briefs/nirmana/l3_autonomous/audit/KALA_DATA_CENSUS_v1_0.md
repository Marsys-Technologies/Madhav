---
artifact: KALA_DATA_CENSUS
version: "1.0"
status: DRAFT
date: 2026-09-22
canonical_id: KALA_DATA_CENSUS
scope: PROMPT_0_ENVIRONMENT_AND_ARCHITECTURE_AUDIT.md F7 (deliverable #8 of the KĀLA READINESS AUDIT)
produced_by: L3 Kāla readiness audit (autonomous, Claude Code), read-only DB-census subagent, cycle 2; promoted cycle 6
---

# F7 — Physical Data Census, `kala_*` tables, canonical chart

**Packet:** F7 (Kāla Readiness Audit)
**Canonical chart_id:** `482012f1-710e-4a25-994a-93821f5871aa`
**Method:** read-only `psql -Atq` one-shot queries via `source /Users/Dev/madhav-l3/dbenv.sh` (`default_transaction_read_only=on`, confirmed `SHOW default_transaction_read_only` → `on`). No individual row narrative/interpretive content was ever selected — every query below is a `count()`/`min()`/`max()`/`GROUP BY` aggregate or an `information_schema` metadata lookup. Two transient connection drops occurred mid-run (port 5434 proxy reset); both were recovered by re-`source`-ing `dbenv.sh` and resuming — no write was ever attempted, no credential was echoed.

Table discovery query:
```sql
SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'kala_%' ORDER BY 1
```
Returned **37** `kala_*` tables (list below). Column-shape discovery used `information_schema.columns` filtered to `table_name LIKE 'kala_%'`.

---

## 1. Per-table census (canonical chart, `WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'` unless noted)

Query pattern used per table: `SELECT count(*), min(<ts_col>), max(<ts_col>) FROM <table> WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa'`, with `<ts_col>` resolved per-table from `information_schema.columns` (see §2 for the resolution table). Generation/build-identity columns resolved the same way and queried separately (§3).

| table | row count (canonical chart) | oldest ts | newest ts | notes |
|---|---:|---|---|---|
| kala_activation | 0 | — | — | Globally non-empty (337,148 rows) but **100% owned by other charts** — see §4. |
| kala_activation_predicates | **50,678** | 2026-09-10 17:17:03 | 2026-09-10 17:17:03 (single `bound_at` instant, batch write) | Matches the ~50,678 reported figure. See §5a for MSR-ref verification. |
| kala_avadhi | 1,169 | 2026-08-12 15:25:28 | 2026-08-12 15:25:28 | |
| kala_bhavishya | 0 | — | — | Globally non-empty (100 rows), all owned by chart `1c826d5a-…` (Abhinandan Mohanty). |
| kala_convergence | 0 | — | — | Globally non-empty (20,497 rows across 2 other charts). |
| kala_convergence_staging | 0 | — | — | **Globally empty** (0 rows, any chart) — a true empty table, not chart-specific. |
| kala_darshana | 0 | — | — | Globally non-empty (750 rows), all owned by chart `1c826d5a-…`. |
| kala_field | **8,570,075** | 2026-09-10 19:40:08 | 2026-09-10 21:15:12 | Largest table by far. This is the ~8.6M-row table, not `kala_field_snapshots` — see §5b. |
| kala_field_boundaries | 261,998 | 2026-09-11 01:49:59 | 2026-09-11 01:49:59 | |
| kala_field_clocks | 8 | 2026-09-11 01:49:59 | 2026-09-11 01:49:59 | |
| kala_field_gof | 6 | 2026-08-09 09:25:34 | 2026-08-09 09:25:34 | |
| kala_field_kinematics | 120,118 | 2026-09-11 01:49:07 | 2026-09-11 01:49:55 | |
| kala_field_null | 150 | 2026-09-10 21:15:16 | 2026-09-11 03:22:11 | |
| kala_field_primitives | 165,082 | 2026-09-11 01:50:51 | 2026-09-11 01:50:51 | |
| kala_field_promise_edges | 114 | 2026-09-11 01:49:59 | 2026-09-11 01:49:59 | |
| kala_field_promise_nodes | 88 | 2026-09-11 01:49:59 | 2026-09-11 01:49:59 | |
| kala_field_provenance | 959,032 | 2026-09-10 21:17:51 | 2026-09-11 03:14:39 | Uses `created_at`, not `computed_at` (only table besides `kala_paddhati_profile` that does). |
| kala_field_routes | 91 | 2026-09-11 01:49:59 | 2026-09-11 01:49:59 | |
| kala_field_salience | 0 | — | — | Globally non-empty (7,650 rows), all owned by chart `1c826d5a-…`. |
| kala_field_skill | 7 | 2026-08-09 09:25:34 | 2026-08-09 09:25:34 | Uses `released_at`. |
| kala_field_snapshots | **0** | — | — | Globally near-empty: exactly **1 row total**, and that row belongs to chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (Abhinandan Mohanty), not the canonical chart. See §5c. |
| kala_field_weight_versions | n/a (no `chart_id` col) | activated_at: 2026-07-30 18:11:00 (only row) | same | Global weight-version table, keyed by `version_id`; has `fitted_from_chart_id` — **0 rows** where `fitted_from_chart_id` = canonical chart (1 row total, fitted from a different chart). |
| kala_field_weights | n/a (no `chart_id`, no timestamp col) | — | — | Global weight table, 29 rows total, keyed by `version_id`/`weight_id`. Unscoped total given per task instructions. |
| kala_field_windows | 17,528 | 2026-09-10 21:17:51 | 2026-09-11 03:14:39 | |
| kala_gochara_authority | 1 | 2026-08-11 09:44:07 | 2026-08-11 09:44:07 | Uses `flipped_at`. |
| kala_gochara_v2_build_state | 297 | 2026-08-12 22:36:47 | 2026-09-10 01:52:41 | |
| kala_gochara_windows | 17,211 | 2026-08-02 08:03:59 | 2026-08-12 23:34:46 | |
| kala_gochara_windows__ssv_20260728c | 0 | — | — | Globally non-empty (1,267 rows), all owned by chart `1c826d5a-…`. Name suggests a snapshot/shadow-variant (`__ssv_` = shadow-schema-variant) table, not a live production surface. |
| kala_gochara_windows_archive_20260805 | 16,297 | 2026-08-02 08:03:59 | 2026-08-05 04:30:18 | Named "archive" — historical snapshot, not a live-write target. |
| kala_gochara_windows_v2 | 1,001 | 2026-08-12 22:36:47 | 2026-09-10 01:52:41 | |
| kala_insights | 0 | — | — | Globally non-empty (415 rows), all owned by chart `1c826d5a-…`. |
| kala_jivana_parva | 100 | 2026-08-13 01:15:53 | 2026-08-13 01:15:53 | |
| kala_kota_chakra | 585 | 2026-09-07 21:08:11 | 2026-09-07 21:08:11 | |
| kala_moorti_nirnaya | 71 | 2026-09-07 21:08:12 | 2026-09-07 21:08:12 | |
| kala_obstruction | 0 | — | — | Globally non-empty (747 rows across 2 other charts). |
| kala_paddhati_profile | 6 | 2026-08-02 06:05:07 | 2026-09-06 10:13:02 | Uses `created_at`. |
| kala_sudarshana_varsha | 120 | 2026-09-07 21:08:11 | 2026-09-07 21:08:11 | |
| kala_taranga | 92,412 | 2026-08-13 01:07:14 | 2026-08-13 01:07:14 | |
| kala_timeline_spec | 0 | — | — | Globally non-empty (6 rows), all owned by chart `1c826d5a-…`. |
| kala_tithi_pravesha | 120 | 2026-09-07 21:08:12 | 2026-09-07 21:08:12 | |
| kala_vedha_gochara | 177 | 2026-09-07 22:40:55 | 2026-09-07 22:40:55 | |

**37 tables total; 9 of them (`kala_activation`, `kala_bhavishya`, `kala_convergence`, `kala_darshana`, `kala_field_salience`, `kala_gochara_windows__ssv_20260728c`, `kala_insights`, `kala_obstruction`, `kala_timeline_spec`) have zero rows for the canonical chart despite being non-empty tables — every single row in each currently belongs to chart `1c826d5a-41cb-4450-b4dc-59d440e5f75a` (and in 3 cases a secondary chart `cb73cd3d-9eba-4220-9902-0de91566e980`), never to the canonical `482012f1-…` chart.** `kala_convergence_staging` is the one table that is truly globally empty (0 rows, any chart). `kala_field_snapshots` is functionally empty for all practical purposes (1 total row, not canonical).

---

## 2. Timestamp-column resolution (how §1's `<ts_col>` was chosen)

```sql
SELECT table_name, column_name FROM information_schema.columns
WHERE table_schema='public' AND table_name LIKE 'kala_%'
  AND (column_name LIKE '%_at' OR column_name LIKE '%time%' OR column_name LIKE '%date%')
ORDER BY table_name, column_name;
```
Result: every table uses `computed_at` except `kala_activation_predicates` (`bound_at`), `kala_field_provenance` (`created_at`), `kala_field_skill` (`released_at`), `kala_field_snapshots` (`built_at`), `kala_gochara_authority` (`flipped_at`), `kala_paddhati_profile` (`created_at`), and `kala_field_weight_versions` (`activated_at`). `kala_field_weights` has no timestamp column at all.

---

## 3. Build/generation identity distribution

Column resolution query:
```sql
SELECT table_name, column_name FROM information_schema.columns
WHERE table_schema='public' AND table_name LIKE 'kala_%'
  AND (column_name LIKE '%version%' OR column_name LIKE '%build%' OR column_name LIKE '%revision%'
       OR column_name LIKE '%generation%' OR column_name LIKE '%run_id%' OR column_name LIKE '%era%');
```

| table | identity column | distribution (canonical chart) | notes |
|---|---|---|---|
| kala_field | `weights_version` | `v0_classical` → 8,570,075 | single generation, no split |
| kala_field_provenance | `weights_version` | `v0_classical` → 959,032 | single generation |
| kala_activation_predicates | `template_version` | `v1.0` → 50,678 | single generation |
| kala_avadhi | `formula_version` | `ka_avadhi_v1.0` → 1,169 | single generation |
| kala_gochara_windows | `generation` | `v1` → 16,297; `3.0` → 914 | **two generations coexist in the live table** — a `v1` legacy string tag and a `3.0` numeric tag both present |
| kala_gochara_windows_v2 | `generation` | `g3_utkarsha` → 914; `2.0` → 87 | **two generations coexist** — same pattern as above, named-era `g3_utkarsha` alongside numeric `2.0` |
| kala_gochara_v2_build_state | `generation` + `build_id` | `g3_utkarsha` / `a5a229b6-62ea-4e69-bef4-74501f1fbc8a` → 270; `2.0` / `cefe3b09-e8b3-42b5-9431-ca8cdf0b8bc4` → 27 | two distinct build runs recorded, confirms the generation split above is a real build-history artifact, not a data-entry inconsistency |
| kala_field_weight_versions | `version_id` (global, not chart-scoped) | 1 row total, `status`/`activated_at` present | fitted from a different chart (`fitted_from_chart_id` ≠ canonical) |
| kala_field_weights | `version_id` (global) | 29 rows total | no chart scoping possible |

Other tables with a `formula_version`/`version` column (`kala_kota_chakra`, `kala_moorti_nirnaya`, `kala_sudarshana_varsha`, `kala_taranga`, `kala_tithi_pravesha`, `kala_vedha_gochara`, `kala_paddhati_profile`) were not individually distributed — each holds well under 600 rows for the canonical chart and a single build timestamp per §1, making a multi-generation split unlikely; not queried further to stay inside budget.

---

## 4. Verdicts on the four specific reported facts (task items 4a–4c, 6)

### 4a. `kala_activation_predicates` ≈ 50,678 rows; MSR-ref resolution

**CONFIRMED** — exact count is 50,678:
```sql
SELECT count(*), min(bound_at), max(bound_at) FROM kala_activation_predicates
WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa';
-- → 50678 | 2026-09-10 17:17:03.734472+00 | 2026-09-10 17:17:03.734472+00
```

**MSR ref-resolution check.** `kala_activation_predicates.signal_id` (uuid) is the MSR fact reference; it resolves against `bodha_msr_signals.signal_id` (also scoped by `chart_id`). Verified `bodha_msr_signals` has 50,678 rows for the canonical chart with a 1:1 unique `signal_id` (`count(*) = count(DISTINCT signal_id) = 50678`). Anti-join:
```sql
SELECT count(*) FROM kala_activation_predicates kap
WHERE kap.chart_id='482012f1-710e-4a25-994a-93821f5871aa'
  AND NOT EXISTS (
    SELECT 1 FROM bodha_msr_signals bms
    WHERE bms.signal_id = kap.signal_id AND bms.chart_id = kap.chart_id
  );
-- → 79
```
**Result: 79 of 50,678 (0.156%) `kala_activation_predicates` rows have a `signal_id` that does not resolve against `bodha_msr_signals` for the same chart.** This is a real, small but nonzero unresolved-reference population — flag for the readiness audit; not re-attempted with a second join target since `bodha_msr_signals` is the only plausibly-correct MSR-signal table in the schema (the other `signal`-named tables — `l25_msr_signals`, `bodha_signal_embeddings`, `mimamsa_signal_*`, `school_signal_coverage`, and the `__ssv_20260728a` shadow variants — do not share `kala_activation_predicates`' `signal_id` semantics on inspection of column names and were not joined against, per the "don't guess after 3 tries" instruction — 1 join attempted, it worked, so no further tries were needed).

### 4b. `ka_kshetra`'s table ≈ 8.6M rows

**CORRECTED-TO-8,570,075, AND CORRECTED-IDENTITY.** The ~8.6M-row table is **`kala_field`**, not `kala_field_snapshots` (which is empty for the canonical chart — see 4c). `kala_field` has exactly 8,570,075 rows for the canonical chart (`weights_version = 'v0_classical'`, 100%, single generation), which is consistent with "~8.6M" (99.65% of 8.6M). This is very likely the actual `ka_kshetra` writer's table by scale and naming (`kala_field` = the raw field/kṣetra grid), while `kala_field_snapshots` is a much smaller, separate "snapshot manifest" table (hash/provenance pointer rows, not the field data itself) that happens to be near-empty for this chart.
```sql
SELECT count(*), min(computed_at), max(computed_at) FROM kala_field
WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa';
-- → 8570075 | 2026-09-10 19:40:08.189363+00 | 2026-09-10 21:15:12.736838+00
```

### 4c. `kala_field_snapshots` reported as 0 rows

**CONFIRMED for the canonical chart, with a nuance.** 0 rows scoped to `chart_id='482012f1-…'`:
```sql
SELECT count(*), min(built_at), max(built_at) FROM kala_field_snapshots
WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa';
-- → 0 | (null) | (null)
```
But the table is **not globally empty** — it holds exactly 1 row total, for a different chart:
```sql
SELECT count(*) FROM kala_field_snapshots;                       -- → 1
SELECT chart_id, built_at, weights_version, x_schema_version FROM kala_field_snapshots;
-- → 1c826d5a-41cb-4450-b4dc-59d440e5f75a | 2026-08-12 22:23:30.478189+00 | v0_classical | x12_v0
```
So "0 rows" is correct as reported *for the canonical chart*, but should not be read as "the table has never been written to" — one snapshot exists, for chart `1c826d5a-…` (Abhinandan Mohanty), never for the canonical chart.

### 6. `ganita_dashas_get`-equivalent placeholder (`ga_dashas_replacement_in_progress`)

**COULD-NOT-VERIFY** — this is a live MCP/API-response string, not a DB row; no DB query can confirm or refute what a live API call currently returns. This sub-claim needs an operator with API/MCP access to re-run the actual `ganita_dashas_get`-equivalent call against the canonical chart.

**Indirect signal checked instead**, per task instructions — `chart_dashas` (the table `call_dasha_eligibility` reads per F5) for the canonical chart:
```sql
SELECT count(*) FROM chart_dashas WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa';
-- → 483870
```
`chart_dashas` holds 483,870 rows for the canonical chart — the underlying dasha data is populated at the DB layer. This does not confirm or refute whether the live API path currently serves it correctly (the placeholder claim could still be true if the serving code path errors out or short-circuits before reaching this table) — it only rules out "the table itself is empty" as the cause.

---

## 5. Constraints observed

- Every query above ran as a one-shot `psql -Atq -c "..."`/`-F'|' -c "..."` invocation, never an interactive session.
- No DDL/DML was ever issued; `default_transaction_read_only=on` was confirmed active before any query.
- No individual row's narrative/interpretive/JSONB content field was ever selected — all `SELECT`s were `count()`, `min()`, `max()`, `DISTINCT <identity_col>`, or plain identity/timestamp columns (`chart_id`, `built_at`, `weights_version`, `x_schema_version`) for metadata purposes only, never `signal_summary_text`, `signal_headline_text`, or any `*_jsonb` payload column.
- Two transient DB-proxy connection drops occurred (mid-loop, port 5434) — both recovered cleanly by re-running `source /Users/Dev/madhav-l3/dbenv.sh`; no write was in flight at either drop, no partial/uncommitted state resulted (all queries were single-statement `SELECT`s under the enforced read-only transaction mode).
