---
artifact: G12_ROUTE1_SNAPSHOT_DESIGN
version: "1.0"
status: "DESIGN NOTE (one page) for steward and Stream A/Codex review; authorises NOTHING. Route 1 of gap G12 adopted by steward G12-ROUTE1 (2026-10-05). The migration and code follow as a DRAFT PR."
date: 2026-10-05
author: Stream B (Śāstra)
changelog:
  - "1.0 (2026-10-05): first version."
---

# G12 Route 1 — the input snapshot owns a COPY of the L1 rows it consumed

**Goal.** A sealed (or candidate) generation stays self-contained and verifiable after any later `ga_positions` / `ga_dashas` rebuild: no row id, build id, engine bump or new L1 column can make it unverifiable. Values that actually changed show as HARD drift; everything else as SOFT drift.

**What is stored (additive columns on `ka_gochara_search_input_snapshot`, immutable like the rest of the row).**
`consumed_fact_rows jsonb` and `consumed_dasha_rows jsonb`: arrays of `{key, content, metadata}`; `l1_facts_metadata_digest`, `dasha_metadata_digest` text. The old `consumed_fact_ids` / `consumed_dasha_row_ids` stay as informational provenance (ids at build time) and no longer decide anything. A `CHECK ... NOT VALID` makes the copies mandatory for every NEW row (0 snapshots exist on production; no backfill).

**Content (identity) vs metadata.**
- *Fact row* (10 today, `graha_position`, tier single, build 15862437). key = `fact_id` (deterministic). content = `ayanamsha_id, fact_category, fact_subject, fact_key, fact_value_text, fact_value_num, fact_value_jsonb, unit`. metadata = `build_id, verification_pass_status, engine_version, salience_formula_ver, tolerance_arcsec, citation_*, source_calculation, formula_*, near_*_flag, vargottama_flag_at_point, cross_ayanamsha_divergence_arcsec`. `computed_at` is in neither (audit).
- *Daśā row* (levels 1 to 3 of the pinned Vimśottarī / lahiri / two_pass_verified build). key = `ayanamsha_id, system_id, level_n, start_iso, coalesce(kp_sublevel,'')`. content = `lord_graha, end_iso, parent_level_n, parent_start_iso` (the parent pointer is a natural pointer, never `parent_row_id`) plus an ordinal `lord_path` (MD/AD/PD lords from the root, so a moved boundary can be named "the 3rd AD of Venus moved by N s" instead of "row missing"). metadata = `dasha_row_id, build_id, parent_row_id, verification_pass_status, engine_version`.

**Digest recipes (both recomputable from the copy alone, same helpers as today: `ka_gochara_canonical_json`, `ka_gochara_sha256_hex`).** IDENTITY digest = sha256 over the byte-sorted lines `key|sha256(canonical_json(content))` (stored in the EXISTING columns `l1_facts_digest` / `dasha_digest`, so `input_digest` and every inventory / ledger digest keep their recipe, only their input values change). METADATA digest = the same over `key|sha256(canonical_json(metadata))` (informational; never enters `input_digest`). New insert guard (a separate additive trigger, not a rewrite of the 1206 guard): the stored digests must equal the digests recomputed from the stored copies.

**What the functions compare after the change.**
- *Live view*: new `ka_gochara_search_live_copy(p_chart, copy)` returns the live rows for the copy's KEYS in the copy's shape (a missing key contributes MISSING).
- *Completeness* (`ka_gochara_search_completeness_violations`, a full replace carrying the existing body): live IDENTITY digest ≠ stored → `input_snapshot_drift` "values changed" (HARD: blocks seal, as today). A metadata-only difference is NOT a violation row (it is reported, not blocking).
- *Moon-resolved domain* (`ka_gochara_search_moon_resolved_domain`): reads the snapshot's copy (`jsonb_to_recordset`), not live `chart_dashas`.
- *Staleness* (`staleness.py`): components `l1_facts`, `dasha` (identity: hard), `l1_metadata`, `dasha_metadata` (soft), `input`; `drifted` = any hard; `drift_kind` per component; for daśā, the ordinal path names a moved boundary.
- *Verification job and seal brief*: read the copy only. `validate_consumed_dasha_population`, `rederive_ledger_digest`, `inventory_store.consumed_dasha_rows` and the P1 anchor SQL (`record_verifier`) take their rows from the copy; the §4.0 population contract is checked ON THE COPY (levels 1 to 3, one build recorded, no conflicting pins); the comparison with live L1 ("omitted pinned row", "build not pinned") moves to the drift REPORT. The frozen-build constant `_C_BUILD` stays only as the writer's BUILD-time acceptance (`assert_single_pinned_build`); a sealed generation is never rejected for a later re-pin.

**Horizon implication (Ruling 7), read from production (read-only).** Consumed daśā rows (levels 1 to 3, the pinned build): scored horizon 1998-01-01..2026-04-17 = **151**; owner formula with start 1998-02-16 = **636** (8 + 64 + 564); start = birth 1984-02-05 = **712** (9 + 71 + 632); start = build date 2026-10-05 = **486**; the whole table for the chart (levels 1 to 3, 1950 to 2100) = **1,040**. At about 140 bytes of compact jsonb per row the copy is about 90 KB (636 rows) and at most about 150 KB (all 1,040); facts add 10 rows (about 3 KB). Negligible against the 5,962+ contacts a full build writes.

**Migration.** One additive PROTECTED migration (proposed number 1305, so it applies BEFORE G8's 1306, which re-syncs onto it: both replace `ka_gochara_search_completeness_violations` in full): preflight (objects exist, not already applied, as 1232 does); `ADD COLUMN`s; the content/metadata/digest/live-copy functions (new names, nothing dropped); the additive copy-check trigger; the two replaced functions; grants (EXECUTE for the builder and verifier roles as 1206/1232 do); a read-only readback SQL; never edited after applied; verified applied, not assumed.

**Tests (real migration chain, disposable DB).** (1) Build a candidate-shaped snapshot, then REBUILD the L1 rows with NEW row ids and a NEW build id and the same values: completeness returns no violation, the verifier and ledger re-derivation pass on the copy, staleness reports metadata-only drift. (2) Change ONE VALUE (a fact value, a daśā `end_iso`): completeness `input_snapshot_drift` and staleness identity drift = HARD. (3) A moved boundary: the ordinal path names it. (4) The copy-check trigger refuses a copy whose digest does not recompute. (5) Moon-domain function unchanged result when L1 is rebuilt.

**Owner decision needed?** No: no policy is open. Two choices recorded for the reviewers, both reversible in code: tier (`verification_pass_status`) is METADATA (a later second derivation of the natal positions is a verification, not a value, per Suvarṇa and Ruling S7); `computed_at` is audit and in neither digest. **Not in scope:** deterministic L1 ids (Suvarṇa's deferred item): v5 does not need them.
