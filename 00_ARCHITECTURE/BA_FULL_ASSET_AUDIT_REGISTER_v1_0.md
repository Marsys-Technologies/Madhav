---
artifact: BA_FULL_ASSET_AUDIT_REGISTER
type: audit_register
version: 1.0
status: CURRENT
authored_by: Claude (BA_FULL_ASSET_AUDIT session)
date: 2026-07-05
---

# BA Full Asset Audit — Register (v1.0)

Exhaustive per-asset, per-finding register for the BA_FULL_ASSET_AUDIT covering all 91 has_writer=true assets across the six sealed/closed layers (Brahmagyan, Ganita, Bodha, Kala, Phala, Mimamsa). Every asset gets at least one entry: assets with no findings get a one-line **clean** entry (exhaustiveness gate). Findings are grouped by layer then asset, in registry order.

**Verification status key:** `CONFIRMED` = independently re-verified against live code/DB during the verify pass. `REFUTED` = the original finding did not reproduce against current HEAD (rationale given) — retained here for audit-trail completeness, not as an open issue. `UNVERIFIED` = not run through the dedicated verify pass in this session (still worth triage, treat with normal scrutiny).

**Fix status key:** `FIXED (commit <sha>)` = remediated in code this session's fix phase, on branch `fix/ba-rebuild-live-abhinandan` (see BA_AUDIT_FIX_PLAN for the consolidated list), **and the fix requires no separate DB migration to take effect** (pure writer/service Python or TS logic changes). `PARTIALLY FIXED` = the corrective code/SQL migration file is committed, but a subsequent migration-apply step against the live database has **not** been run — re-verified by direct live-DB query during this artifact-writing pass (5 such cases: `bg_remedies` target_floor via migration 405, `ka_yojaka`/`ka_avadhi`/`ka_taranga` depends_on via migration 406, `ph_sodhana`'s new CHECK-constraint value via migration 407 — all confirmed still showing pre-fix state live). `OPEN` = confirmed but not yet fixed. `SKIPPED (native_judgment queued)` = requires a scope/formula/data decision from the native before a fix can be written.

**Coverage:** 91/91 assets addressed. 68 findings recorded across 45 assets with findings; 46 assets clean. Of the 13 findings with a fix applied this session, 8 are fully live (pure code, no migration required) and 5 are PARTIALLY FIXED pending a migration-apply step (see fix-status key above and `BA_AUDIT_FIX_PLAN_v1_0.md`).

**Severity distribution:** BLOCKER=24 · MAJOR=22 · MINOR=17 · ENHANCEMENT=5

---

## L0 — Brahmagyan

### `bg_ephemeris`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bg_reference`

**[MINOR] L2-Data** — verification: `UNVERIFIED`

- **Finding:** bg_reference's own count_sql total is 1,242 (sum of 11 reference_* tables) against asset_registry.target_floor=1485 — 84% of floor, a real shortfall rather than a rounding gap.
- **Evidence:** Computed sum of reference_planets(11)+signs(12)+aspects(19)+vargas(19)+houses(12)+strength_systems(33)+karakas(77)+upagrahas(11)+constants(203)+topic_tags(481)+glossary(364) = 1242 vs target_floor 1485.
- **Fix:** Identify which sub-table(s) are thin relative to the classical scope this asset claims (glossary and topic_tags are the largest, most likely under-seeded categories) and either backfill or adjust the floor to the honestly-achieved count.
- **fix_type:** `seed`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `bg_texts`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bg_ontology`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bg_text_index`

**[BLOCKER] L3-Code** — verification: `REFUTED`

- **Finding:** TextIndexWriter (pipeline/orchestrator/writers/bg_text_index.py) reads DB rows with positional integer indexing (`cur.fetchone()[0]` at lines 460, 484, 488, 511, 587) even though `ctx.db_conn` is created in `pipeline/orchestrator/db.py::connect()` with `row_factory=psycopg.rows.dict_row` — every row is a plain dict (e.g. `{"count": N}`), not a tuple, so `row[0]` raises `KeyError: 0`. Separately, at line 548 the writer does `for i, (chunk_id, content_en) in enumerate(chunk_rows)` where `chunk_rows` are 2-key dicts from `SELECT chunk_id, content_en FROM ...` — unpacking a dict without indexing iterates its KEYS, so `chunk_id` and `content_en` silently become the literal strings 'chunk_id'/'content_en' instead of the row's actual values (this branch is unreachable in practice because the KeyError above fires first, but it is a second live bug in the same code path).
- **Evidence:** psycopg.connect(..., row_factory=psycopg.rows.dict_row) confirmed in platform/python-sidecar/pipeline/orchestrator/db.py:24-32. bg_text_index.py's own `conn.cursor()` calls (lines 456,468,482,506,522,541,582) take no cursor_factory/row_factory override, so they inherit dict_row. DB state confirms the writer cannot be progressing: classical_text_chunks has 3,716/10,651 (35%) embedded chunks still with topic_tag IS NULL, and count_sql result (SELECT count(DISTINCT topic_tag)...) = 361 vs asset_registry.target_floor = 400 for bg_text_index — stuck below floor with no path to close the gap because the writer errors before it can classify anything.
- **Fix:** Switch all fetchone()[0]/positional accesses in this writer to the dict key returned by the query (e.g. `cur.fetchone()["count"]`, or add `AS count` aliases consistently and use that key), and fix the row unpack at line 548 to `chunk_id, content_en = row["chunk_id"], row["content_en"]` (or iterate `row.values()` only if a real tuple_row cursor is deliberately requested per-call). Add a regression test that runs the writer against a live psycopg dict_row connection (not a mock tuple cursor) so this class of bug cannot land again silently.
- **fix_type:** `code`
- **Status:** N/A (finding refuted — no fix needed)
- **Refutation rationale:** Read the live file at platform/python-sidecar/pipeline/orchestrator/writers/bg_text_index.py in full. Every cited line (460, 484, 488, 511, 587) already uses dict-key access (`cur.fetchone()["count"]`), not positional tuple indexing (`[0]`) as the finding claims. The line-548 dict-unpack bug is also absent: current code at line 549 does `chunk_id, content_en = row["chunk_id"], row["content_en"]`, correct key-based extraction. `db.py::connect()` does confirm `row_factory=psycopg.rows.dict_row` as claimed, so the premise is accurate, but the writer's code no longer has the described defect. `git log -- .../bg_text_index.py` shows a commit `41225988 fix(bg_text_index): use dict-row keys instead of positional tuple indexing` that already remediated exactly this class of bug, with no later regression. The audit finding appears to describe a real historical bug that has since been fixed — it does not reproduce against the current HEAD, so it should not be confirmed as an open BLOCKER.

### `bg_rules`

**[BLOCKER] L2-Data** — verification: `CONFIRMED`

- **Finding:** sutravali_rules.yoga_canonical_id is 0% populated across all 2,912 rows in production (Abhinandan-scope global table). The column is declared in the writer's dataclass default (l0_rules.py:116), threaded through FK validation (lines 1304-1306, 1368-1371) and the INSERT statement (line 1385/1407), but NO extraction pattern in the P1–P21+ dispatch table (l0_rules.py:1098-1119, and all _pN_extract functions) ever sets a real yoga_canonical_id value on the returned rule_row dict — there is no yoga-detection pattern at all. It is also referenced nowhere downstream (`grep yoga_canonical_id` across the repo hits only l0_rules.py itself) — a column that exists and joins/is-joined-by nothing, exactly the documented sutravali_rules scar pattern.
- **Evidence:** SQL: `SELECT count(*) filter (where yoga_canonical_id is not null) FROM sutravali_rules` = 0 of 2912. `grep -rn yoga_canonical_id` across platform/python-sidecar returns only brahmagyan/l0_rules.py (writer-internal); no consumer joins it.
- **Fix:** Either (a) implement a real yoga-name-match extraction pattern (regex over brahma_yoga_catalog.canonical_id / name aliases against chunk text) so rules can genuinely cite the yoga they derive from, or (b) if yoga-linkage was descoped, drop the column and its FK-validation dead code rather than leave a phantom citation field that silently starves any future consumer expecting it to be populated.
- **fix_type:** `code`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

**[MAJOR] L6-Coverage** — verification: `CONFIRMED`

- **Finding:** sutravali_rules.dasha_system_id is also 0% populated (0/2912), despite pattern P7 ('dasha_rule', l0_rules.py:401-424) explicitly setting `dasha_system_id: 'vimshottari'` on every match it produces, and 'vimshottari' being a valid FK target in brahma_dasha_systems (would not be nulled by the FK-validation guard). The rule ptype distribution in the live table has zero rows with predicate_jsonb->>'type' = 'dasha_rule' — the P7 regex is registered but never actually fires against the current 13-text, 10,651-chunk corpus, or every match it does produce falls below QUALITY_THRESHOLD_LIVE and is silently discarded (rows_below_threshold counter, not surfaced per-pattern).
- **Evidence:** `select predicate_jsonb->>'type', count(*) from sutravali_rules group by 1` shows 19 distinct ptypes, none named 'dasha_rule' (transit_rule=25, dignity_placement=94, etc. all present, dasha_rule absent). dasha_system_id notnull count = 0/2912.
- **Fix:** Instrument extract_rules_from_chunk to log per-pattern match counts (not just aggregate rows_below_threshold) so it's visible whether P7 is matching-but-filtered vs never-matching; if never matching, the regex needs broadening for the corpus's actual English-translation phrasing of dasha-timing rules (classical dasha citations are a core Jyotish technique — this is a real coverage gap, not cosmetic).
- **fix_type:** `code`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `bg_remedies`

**[MAJOR] L1-Registry** — verification: `CONFIRMED`

- **Finding:** asset_registry.target_floor for bg_remedies is 800, but the writer's own docstring (bg_remedies.py:5-8) documents a fixed, by-design corpus of 108 + 102 + 54 = 264 rows (planet matrix + dosha remedies + legacy remedies) — actual brahma_remedy_corpus count is 266, essentially at 100% of the writer's designed capacity, yet the registry floor makes it look like a 33%-populated, badly-thin asset.
- **Evidence:** SELECT count(*) FROM brahma_remedy_corpus = 266; asset_registry.target_floor for bg_remedies = 800 (query result). Writer docstring explicitly enumerates 108+102+54=264 as the complete deterministic bucket design; ZERO LLM / ZERO fabrication is stated as a hard constraint, so the floor cannot be hit without either expanding the deterministic corpus design or being native-judgment-approved to lower the floor.
- **Fix:** Per CLAUDE.md §N.4 (floors are aspirational == achieved count after build, never a fabrication target), either correct target_floor to reflect the current design's true ceiling (~266) or queue a native_judgment decision to expand remedy corpus coverage (e.g. additional dosha remedies, nakshatra-specific remedies) to genuinely justify a higher floor — do not leave a floor the writer can structurally never reach.
- **fix_type:** `registry`
- **Status:** PARTIALLY FIXED — migration `405_bg_remedies_floor_recorrection.sql` + `asset_registry_seed.ts` correction committed (`29ce08d0`), but **NOT YET APPLIED to the live database**: re-verified via direct query this session, `asset_registry.target_floor` for `bg_remedies` is still `800` live. The migration file exists and is correct; someone must run it against the live DB before this asset's floor reads honestly.

### `bg_concordance`

**[BLOCKER] L3-Code** — verification: `REFUTED`

- **Finding:** ConcordanceWriter (pipeline/orchestrator/writers/bg_concordance.py) has the identical bug pattern: `topic_meta: dict[str, tuple[str, str]] = {row[0]: (row[1], row[2]) for row in topic_rows}` at line 98 and `tagged_chunks = cur.fetchone()[0]` at line 107, both against a dict_row cursor from `SELECT canonical_id, name, category FROM reference_topic_tags` / `SELECT COUNT(*) ...` — these raise KeyError on any real (non-mocked) run.
- **Evidence:** Same shared connect() with row_factory=dict_row applies (no cursor_factory override in bg_concordance.py's conn.cursor() calls). classical_attributions currently sits at 720 rows vs asset_registry.target_floor=800 for bg_concordance and has clearly been static/stale — consistent with the writer erroring out on every rebuild attempt before it can insert new rows (delete-then-insert would never progress past Step 1).
- **Fix:** Same class of fix as bg_text_index: replace `row[0]/row[1]/row[2]` with `row["canonical_id"], row["name"], row["category"]` and `cur.fetchone()[0]` with `cur.fetchone()["count"]`.
- **fix_type:** `code`
- **Status:** N/A (finding refuted — no fix needed)
- **Refutation rationale:** Read platform/python-sidecar/pipeline/orchestrator/writers/bg_concordance.py in full. Line 98 is `topic_meta = {row["canonical_id"]: (row["name"], row["category"]) for row in topic_rows}` and line 107 is `tagged_chunks = cur.fetchone()["count"]` — both already use dict-key access appropriate for a dict_row cursor, not the `row[0]/row[1]/row[2]` / `fetchone()[0]` positional-tuple pattern the finding claims exists at those lines. git log for this file shows commit b9a495bf 'fix(bg_concordance): use dict-row keys instead of positional tuple indexing' already applied and present at HEAD, with no subsequent regression. The finding describes a pre-fix version of the code; the bug does not exist in the current working tree. (Did not independently verify the classical_attributions=720-vs-target_floor=800 row-count claim since Postgres MCP access wasn't available in this session, but the load-bearing code-level claim — the KeyError-causing bug pattern at lines 98/107 — is directly falsified by reading the file.)

### `bg_yogas`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bg_dasha_systems`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bg_doshas`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bg_compendium_index`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bg_panchanga`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bg_ephemeris_engine`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bg_nakshatra`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bg_class_priors`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bg_ghatana`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bg_formula_constants`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bg_prashna_rules`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bg_vastu_directions`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bg_transit_engine`

**[ENHANCEMENT] L1-Registry** — verification: `UNVERIFIED`

- **Finding:** Both assets are postgres_table-scoped with real target tables/floors in asset_registry but has_writer=false; this is by design and already documented (bg_transit_rules.py and bg_medical_mappings.py each carry a second @register() decorator that routes both asset_ids through one writer, and runner.py has an explicit KNOWN_SUBTABLE allowlist for exactly these two + explains the has_writer=true plan-resolver gate). Verified clean — no action needed, but flagging so it isn't re-flagged as a false positive by a future audit.
- **Evidence:** pipeline/orchestrator/runner.py lines ~107-145 documents the sub-table allowlist by name ("bg_nakshatra_medical", "bg_transit_engine"); bg_transit_rules.py and bg_medical_mappings.py docstrings explicitly explain the dual-@register pattern. Table row counts (bg_transit_engine=9=target_floor, bg_nakshatra_medical=27=target_floor) confirm the sub-table writer is in fact populating them correctly.
- **Fix:** No fix needed; consider adding a `catalog_status`/comment column note directly in asset_registry (not just in writer docstrings + runner.py) so this documented exception is visible from the registry itself without needing to read three separate files.
- **fix_type:** `registry`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `bg_transit_rules`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bg_medical_mappings`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bg_nakshatra_medical`

**[ENHANCEMENT] L1-Registry** — verification: `UNVERIFIED`

- **Finding:** Both assets are postgres_table-scoped with real target tables/floors in asset_registry but has_writer=false; this is by design and already documented (bg_transit_rules.py and bg_medical_mappings.py each carry a second @register() decorator that routes both asset_ids through one writer, and runner.py has an explicit KNOWN_SUBTABLE allowlist for exactly these two + explains the has_writer=true plan-resolver gate). Verified clean — no action needed, but flagging so it isn't re-flagged as a false positive by a future audit.
- **Evidence:** pipeline/orchestrator/runner.py lines ~107-145 documents the sub-table allowlist by name ("bg_nakshatra_medical", "bg_transit_engine"); bg_transit_rules.py and bg_medical_mappings.py docstrings explicitly explain the dual-@register pattern. Table row counts (bg_transit_engine=9=target_floor, bg_nakshatra_medical=27=target_floor) confirm the sub-table writer is in fact populating them correctly.
- **Fix:** No fix needed; consider adding a `catalog_status`/comment column note directly in asset_registry (not just in writer docstrings + runner.py) so this documented exception is visible from the registry itself without needing to read three separate files.
- **fix_type:** `registry`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `bg_dignity_reference`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)


## L1 — Ganita

### `ga_positions`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `ga_vargas`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `ga_dashas`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `ga_strength`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `ga_sensitive`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `ga_panchanga`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `ga_prashna`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `ga_sade_sati`

**[BLOCKER] L3-Code correctness / L2-Data completeness** — verification: `CONFIRMED`

- **Finding:** The `natal_facts` cross-reference dict passed into row emission is a hardcoded scaffold of constant defaults (mars_aspect_during_period=False, jupiter_aspect_during_period=False, saturn_rahu_axis_flag=False, eclipse_during_period=False, concurrent_saturn_return=False, d10_karya_bhava_activation_flag=False, argala_during_period=[], saturn_moon_parivartana=False, moon_sign_lord_strong=False, jupiter_aspects_saturn_during_cycle=False, saturn_yoga_karaka=False, tara_bala_at_janma_peak='PENDING_GA4_LOOKUP') built inline in build_ga_sade_sati() (lines ~1469-1485) and NEVER enriched from the GA4/GA6/GA7/GA8 tables the writer explicitly gates on in _verify_upstream_rows(). The docstring/comments claim these are read from GA7/GA4/GA6/GA8 at build time ('enriched from GA7 at build time'), but no such enrichment code exists anywhere in the file.
- **Evidence:** Verified on Abhinandan (chart_id 1c826d5a...): sade_sati_modifier_overlay flags are FALSE for 100% of 105 rows (mars/jupiter/saturn-rahu/eclipse/saturn-return all constant-false, 5 categories x 105 rows each); sade_sati_cancellation_check.cancellation_active_flag is FALSE for all 35 rows (i.e. cancellation is dynamically never detected beyond a static sign match, because 6 of 8 rule inputs are hardcoded False); sade_sati_concurrent_dasha_overlay stores the literal string 'PENDING_GA7_LOOKUP' in fact_value_text for all 7 dasha-lord keys x 35 rows = 245 rows; sade_sati_downstream_cross_reference.tara_bala_baseline_ref and sade_sati_phase.tara_bala_during_peak store the literal string 'PENDING_GA4_LOOKUP'. These placeholder/degenerate values are written straight to chart_facts as final, citable, engine_version-stamped rows (verification_pass_status='two_pass_verified'), not marked as pending.
- **Fix:** Implement the GA4 (tara_bala_natal_baseline lookup by nakshatra-at-peak), GA6 (D10 Karya bhava activation via chart_divisionals), GA7 (per-dasha-system lord-at-date lookup from chart_dashas for each of the 7 systems), and GA8 (argala_natal_matrix subset-in-window) joins that _verify_upstream_rows() already gates the build on, and replace the hardcoded natal_facts scaffold with the real computed values before calling _emit_cycle_rows(). Until then this asset materially overstates its own verification_pass_status.
- **fix_type:** `code`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

**[MINOR] L2-Data completeness** — verification: `UNVERIFIED`

- **Finding:** Row count for Abhinandan (9,790) is below its own asset_registry.target_floor (11,019), a ~11% shortfall, consistent with/compounding the natal_facts stub finding above (several categories emit fewer atomic rows than the spec envisions once real per-phase enrichment is added).
- **Evidence:** asset_registry.ga_sade_sati.target_floor=11019; live count_sql result for chart 1c826d5a...=9790.
- **Fix:** Re-baseline target_floor after the natal_facts enrichment fix lands, or investigate why cycle/dhaiya emission undershoots the floor independent of the enrichment gap.
- **fix_type:** `registry`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `ga_tajaka`

**[MINOR] L2-Data completeness** — verification: `UNVERIFIED`

- **Finding:** Row count for Abhinandan (235) is slightly below target_floor (240); 5 of 235 rows have an empty applicable_tajik_yogas_array.
- **Evidence:** count_sql result 235 vs target_floor 240; 5/235 rows with NULL/empty applicable_tajik_yogas_array.
- **Fix:** Confirm whether the 5-row shortfall is an expected edge-year boundary effect (first/last varsha year partially outside window) or a genuine gap; re-baseline floor if by design.
- **fix_type:** `seed`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `ga_structural`

**[ENHANCEMENT] L1-Registry & DAG** — verification: `UNVERIFIED`

- **Finding:** count_sql is a very large, hand-maintained category allow-list with an explicit exclusion sub-list to avoid double-counting categories owned by ga_strength; this is fragile (any new fact_category added by the writer must be manually reconciled into both the inclusion and exclusion branches, as already happened twice per migrations 364/368 noted in the SQL comments) but is currently internally consistent and reconciles correctly against ga_strength's disjoint category set.
- **Evidence:** count_sql text contains inline comments 'Added in migration 364' / 'Added in migration 368 ... 9 categories confirmed emitted by ga_structural_writer.py but absent from the IN() list' — evidence this has already silently drifted out of sync with the writer at least twice before being caught.
- **Fix:** Consider deriving the count_sql category list from a single source of truth (e.g. a registered category-ownership table) instead of a hand-maintained SQL string, to prevent a third silent-drift incident.
- **fix_type:** `native_judgment`
- **Status:** SKIPPED (native_judgment queued — see BA_AUDIT_FIX_PLAN §NATIVE_JUDGMENT_QUEUE)

### `ga_nakshatra`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `ga_condition`

**[MAJOR] L3-Code correctness / L2-Data completeness** — verification: `CONFIRMED`

- **Finding:** _load_dasha_periods() in ga_condition_writer.py explicitly returns `weak_periods=None` unconditionally (comment: 'weak periods require cross-reference with condition score' — never implemented), while `peak_periods` IS computed from chart_dashas. Result: ga_condition_composite.weak_dasha_periods is 0% populated for every graha/chart, while peak_dasha_periods is 100% populated — an asymmetric, silently-stubbed column.
- **Evidence:** ga_condition_writer.py line ~822: `return periods, None   # weak periods require cross-reference with condition score`. Postgres on Abhinandan: 45/45 rows have weak_dasha_periods NULL/empty, 0/45 have peak_dasha_periods empty.
- **Fix:** Implement the weak-period cross-reference (graha's own mahadasha where condition_score for that graha is below a weak threshold, or antardasha windows where the dasha lord is in poor natal condition) or explicitly document/flag the column as not-yet-implemented rather than emitting it as if computed.
- **fix_type:** `code`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `ga_yoga`

**[MAJOR] L2-Data completeness / L5-Data-engineering** — verification: `CONFIRMED`

- **Finding:** `activation_dasha_periods` (jsonb) is a real column on ga_yoga_firings but is never included in the writer's INSERT statement at all — it is not read, computed, or passed as a parameter anywhere in ga_yoga_writer.py — so it is permanently NULL for every yoga firing on every chart. Separately, `family_ids` is sourced from the `yoga_family_members` reference table via _load_yoga_families(), but that table has zero rows in prod, so family_ids is also 0% populated across all charts (an empty '[]' for every row).
- **Evidence:** Postgres: ga_yoga_firings INSERT column list (lines 1027-1033 of ga_yoga_writer.py) omits activation_dasha_periods entirely. For Abhinandan chart_id 1c826d5a...: all 30 fired yoga rows have activation_dasha_periods NULL and family_ids='[]'; SELECT count(*) FROM yoga_family_members returns 0 rows platform-wide.
- **Fix:** Either wire activation_dasha_periods to a real per-yoga dasha-window computation and seed yoga_family_members with the intended family taxonomy, or drop/deprecate both as not-yet-implemented columns so the schema doesn't silently promise data that never arrives (matches the sutravali_rules.yoga_canonical_id scar pattern: a column that exists and joins/serves nothing).
- **fix_type:** `code`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

**[MINOR] L4-Astrological soundness / L6-Coverage** — verification: `UNVERIFIED`

- **Finding:** compute_yoga_strength_v1() (the only place `strength` is ever set) is wired to a narrow subset of yoga rule shapes; for Abhinandan none of the 30 fired yogas (amala x5, anapha, budha_aditya x4, pasha x5, ubhayachari x5, vasi x5, vesi x5) receive a strength score — strength is NULL for 100% of firings, and is_partial/bhanga_active are constant-false for all 30 rows too. This may be legitimate design (B.10 no-fabricated-computation: 'strength NULL unless classical formula applies') if these yoga types are genuinely outside the formula's classical scope, but it means the richest analytical column on this asset currently delivers zero signal for this chart.
- **Evidence:** SELECT count(strength) FROM ga_yoga_firings WHERE chart_id=Abhinandan → 0 of 30; count(is_partial=true)=0; count(bhanga_active=true)=0.
- **Fix:** Native/astrological judgment call: decide whether the strength formula's scope should be widened to solar/positional yogas (vasi, vesi, anapha, budha_aditya, pasha, ubhayachari) per a cited classical weighting rule, or whether NULL-for-these-types is the correct scoped behavior.
- **fix_type:** `native_judgment`
- **Status:** SKIPPED (native_judgment queued — see BA_AUDIT_FIX_PLAN §NATIVE_JUDGMENT_QUEUE)

### `ga_vastu`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `ga_medical`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `ga_transit_anchors`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)


## L2 — Bodha

### `bo_laksana`

**[MINOR] L5-DataEng / L2-Data** — verification: `UNVERIFIED`

- **Finding:** bodha_msr_signals.verification_pass_status carries 8 distinct raw values inherited pass-through from upstream L1 fact rows, with inconsistent casing/vocabulary (two_pass_verified, computed_extension, PASS [uppercase — stylistic outlier], single, floored, classical_match, documented_approximation, not_defined_for_nodes). bo_pramana_mapa's scorecard only buckets two of these (two_pass_verified_pct=94.26%, documented_approximation_pct=0.07%) — leaving ~5,791 signals (≈8.7%) in unclassified/unreported buckets, so the two published quality percentages don't account for the full population and understate how much of the chart is not two-pass-verified.
- **Evidence:** SELECT verification_pass_status, count(*) FROM bodha_msr_signals WHERE chart_id=... GROUP BY 1 → two_pass_verified 62980, computed_extension 1632, PASS 1095, single 649, floored 335, classical_match 60, documented_approximation 45, not_defined_for_nodes 20 (total 66816, only 63025/66816=94.33% covered by the two reported percentages' numerators).
- **Fix:** Normalize verification_pass_status vocabulary at the L1→L2 boundary (map to a canonical enum), and have bo_pramana_mapa report a full histogram (or at minimum a 'other/unclassified_pct') rather than only two named buckets, so the scorecard percentages sum to 100%.
- **fix_type:** `code`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `bo_bimba`

**[MINOR] L3-Code** — verification: `UNVERIFIED`

- **Finding:** Two bare `except Exception: pass` blocks (lines 220, 273) swallow errors with no logging, inside a pgvector node-writer — any transient failure building a subset of nodes (e.g. embedding/vector construction for a given node) disappears silently rather than surfacing in build logs, making the kind of partial-build data loss seen in bo_samskara/bo_pramana_mapa (finding above) harder to diagnose after the fact.
- **Evidence:** bo_bimba.py:220-221 and :273-274 — `except Exception: pass` with no logger call.
- **Fix:** Replace bare `except Exception: pass` with at least a `logger.warning(...)` including the node/signal id and exception, consistent with the pattern used elsewhere in bo_samskara's per-row fallback.
- **fix_type:** `code`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `bo_karanajala`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bo_cgm_motifs`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bo_cgm_paths`

**[MAJOR] L4-Astro / L3-Code** — verification: `CONFIRMED`

- **Finding:** path_strength is a module-level constant PATH_STRENGTH_PLACEHOLDER = 0.5, explicitly commented 'calibrated in L4 Phala; placeholder for now', and is written identically for all 45 bodha_cgm_paths rows for Abhinandan. L4 Phala is now sealed/CLOSED per CLAUDE.md §E, but nothing calibrates this column — the flat placeholder is still live in production.
- **Evidence:** bo_cgm_paths.py:40 `PATH_STRENGTH_PLACEHOLDER = 0.5`; line 291 assigns it directly to path_strength. `select path_strength, count(*) from bodha_cgm_paths where chart_id=... group by 1` → single row: 0.5, 45.
- **Fix:** Either (a) compute path_strength per-path from the constituent edges' computed_strength (already present on bodha_cgm_edges) now that L4 is closed, or (b) if genuinely deferred to a later calibration phase, this is a native scope call — but it should not silently ship as a real-looking numeric column with zero variance; at minimum mark it clearly non-authoritative in the API response.
- **fix_type:** `native_judgment`
- **Status:** SKIPPED (native_judgment queued — see BA_AUDIT_FIX_PLAN §NATIVE_JUDGMENT_QUEUE)

### `bo_samskara`

**[BLOCKER] L2-Data / L5-DataEng** — verification: `CONFIRMED`

- **Finding:** bodha_signal_embeddings has only 13,383 rows for Abhinandan against a target_floor of 60,000 and against bodha_msr_signals=66,816 (should be 1:1, one embedding per signal per the writer's own docstring). Worse: the terminal synthesis_quality_scorecard row (scored_at 2026-07-04) still reports embedding_count=66816 and contradiction_count=5, i.e. the scorecard is stale/wrong relative to live data — 4 of 5 ayanamsha substeps' embeddings (and most contradiction rows) were lost after the scorecard was last computed, and bo_pramana_mapa was never rerun to reflect it.
- **Evidence:** SELECT count(*) FROM bodha_signal_embeddings WHERE chart_id='1c826d5a-...' → 13383 (live, re-checked twice). SELECT count(*) FROM bodha_contradictions WHERE chart_id='1c826d5a-...' → 1 (live). synthesis_quality_scorecard row for same chart_id shows embedding_count=66816, contradiction_count=5. count_sql for bo_samskara (asset_registry) is accurate/live but 22% of target; the cached scorecard is the dishonest artifact.
- **Fix:** Re-run bo_samskara for the 4 missing ayanamshas (investigate why run_substep's _embed_batch call — not wrapped in try/except, unlike _batch_insert — silently drops a whole ayanamsha on any embedding-API exception, so a substep failure looks like a no-op rather than a build failure) and re-run bo_pramana_mapa to refresh the scorecard. Also add alerting/logging when embedding_count for a build doesn't match msr_signal_count so this can't go undetected again.
- **fix_type:** `code`
- **Status:** PARTIALLY FIXED (commit `a8a786a2` — `_embed_batch` now wrapped per-batch so one exception no longer drops a whole ayanamsha, plus a warning when inserted count < signal count; the actual re-run to backfill the missing 4 ayanamshas' embeddings and refresh the stale scorecard is a rebuild action, explicitly out of scope this session — see BA_AUDIT_FIX_PLAN)

### `bo_sangati`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bo_cdlm_summary`

**[MINOR] L1-Registry** — verification: `UNVERIFIED`

- **Finding:** asset_registry.target_table is NULL for both bo_cdlm_summary and bo_chart_gestalt even though each has a working count_sql pointing at a real table (bodha_cdlm_chart_summary, bodha_chart_gestalt respectively) and both build successfully. Any tooling that reads target_table (rather than parsing count_sql) for cockpit display, drift detection, or governance reporting will silently miss these two assets' tables.
- **Evidence:** SELECT target_table FROM asset_registry WHERE asset_id IN ('bo_cdlm_summary','bo_chart_gestalt') → both NULL, while count_sql for both correctly references bodha_cdlm_chart_summary / bodha_chart_gestalt (which do have 5 rows each for Abhinandan).
- **Fix:** Backfill target_table for these two rows in asset_registry.
- **fix_type:** `registry`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `bo_drishti`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bo_anveshana`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bo_chart_gestalt`

**[MINOR] L1-Registry** — verification: `UNVERIFIED`

- **Finding:** asset_registry.target_table is NULL for both bo_cdlm_summary and bo_chart_gestalt even though each has a working count_sql pointing at a real table (bodha_cdlm_chart_summary, bodha_chart_gestalt respectively) and both build successfully. Any tooling that reads target_table (rather than parsing count_sql) for cockpit display, drift detection, or governance reporting will silently miss these two assets' tables.
- **Evidence:** SELECT target_table FROM asset_registry WHERE asset_id IN ('bo_cdlm_summary','bo_chart_gestalt') → both NULL, while count_sql for both correctly references bodha_cdlm_chart_summary / bodha_chart_gestalt (which do have 5 rows each for Abhinandan).
- **Fix:** Backfill target_table for these two rows in asset_registry.
- **fix_type:** `registry`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `bo_upaya`

**[MAJOR] L3-Code / L4-Astro** — verification: `CONFIRMED`

- **Finding:** resonance_score_v1 is fed five hardcoded 0.0 inputs per graha (cancellation_burden, dispositor_chain_weakness, dasha_proximity_activation_score, cdlm_weakest_constituent_count, cgm_motifs_weakest_node) instead of real per-graha computations. Result: contradiction_factor, domain_burden, and motif_burden are literally 0 for all 45 rows for Abhinandan (distinct-value count = 1 for each), and resonance_score collapses to be numerically identical to weakness_score in every sampled row — the Remedial Measures (RM) scoring never actually reflects dispositor-chain weakness or dasha-timing proximity, both of which are classically required (BPHS/Jaimini) for prioritizing remedies to an affliction that is actually about to fructify vs. one that is dormant.
- **Evidence:** bo_upaya.py lines 448-452: cancellation_burden=0.0, dispositor_chain_weakness=0.0, dasha_proximity_activation_score=0.0, cdlm_weakest_constituent_count=0.0, cgm_motifs_weakest_node=0.0 (all literal constants, not fetched from any table). SQL: `select count(distinct motif_burden), count(distinct domain_burden), count(distinct weakness_score) from bodha_rm_resonances where chart_id=...` → 1, 1, 17 out of 45 rows (motif_burden and domain_burden are perfectly flat; only weakness_score varies).
- **Fix:** Wire dasha_proximity_activation_score from kala_* dasha tables (L3, already sealed and available), dispositor_chain_weakness from ga_structural dispositor chains, and cancellation_burden / motif+cdlm weakest-node scores from the already-written bo_karanajala/bo_sangati/bo_cgm_motifs outputs this writer's own depends_on already lists as upstream. This is a real computation gap, not a scope decision — flag for native confirmation only on which formula weighting to use, not on whether to compute it at all.
- **fix_type:** `code`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `bo_pramana_mapa`

**[BLOCKER] L2-Data / L5-DataEng** — verification: `CONFIRMED`

- **Finding:** bodha_signal_embeddings has only 13,383 rows for Abhinandan against a target_floor of 60,000 and against bodha_msr_signals=66,816 (should be 1:1, one embedding per signal per the writer's own docstring). Worse: the terminal synthesis_quality_scorecard row (scored_at 2026-07-04) still reports embedding_count=66816 and contradiction_count=5, i.e. the scorecard is stale/wrong relative to live data — 4 of 5 ayanamsha substeps' embeddings (and most contradiction rows) were lost after the scorecard was last computed, and bo_pramana_mapa was never rerun to reflect it.
- **Evidence:** SELECT count(*) FROM bodha_signal_embeddings WHERE chart_id='1c826d5a-...' → 13383 (live, re-checked twice). SELECT count(*) FROM bodha_contradictions WHERE chart_id='1c826d5a-...' → 1 (live). synthesis_quality_scorecard row for same chart_id shows embedding_count=66816, contradiction_count=5. count_sql for bo_samskara (asset_registry) is accurate/live but 22% of target; the cached scorecard is the dishonest artifact.
- **Fix:** Re-run bo_samskara for the 4 missing ayanamshas (investigate why run_substep's _embed_batch call — not wrapped in try/except, unlike _batch_insert — silently drops a whole ayanamsha on any embedding-API exception, so a substep failure looks like a no-op rather than a build failure) and re-run bo_pramana_mapa to refresh the scorecard. Also add alerting/logging when embedding_count for a build doesn't match msr_signal_count so this can't go undetected again.
- **fix_type:** `code`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

**[MAJOR] L3-Code / L5-DataEng** — verification: `CONFIRMED`

- **Finding:** Five of the scorecard's quality/trap columns are hardcoded constants regardless of actual data: divergent_flagged_count=0, trap2_narration_leak_count=0, no_pre_answer_pass=True, ledger_independence_pass=True, discovery_not_fabricated_pass=True. trap2_narration_leak_count in particular is supposed to detect the documented UCN-contamination trap (MSR_UCN_CONTAMINATION_AUDIT_v1_0.md, a named hard-won trap in this codebase's own governance docs) but is stubbed to always 0 — the scorecard can never report a narration-leak violation even if one exists. l1_assets_projected_count is also degenerate: hardcoded as `1 if msr_count>0 else 0` rather than actually counting distinct source L1 assets referenced via constituent_facts_array (the real number, per bo_laksana's depends_on, should be up to 9).
- **Evidence:** bo_pramana_mapa.py lines 190, 206, 217, 223, 225, 226 — literal constants assigned to columns whose names imply real verification/detection logic. Live row confirms: l1_assets_projected_count=1, l1_assets_projected_array=[] (empty despite non-zero count), trap2_narration_leak_count=0, ledger_independence_pass=true, discovery_not_fabricated_pass=true for the Abhinandan scorecard.
- **Fix:** Implement the actual narration-leak detector (scan configuration_jsonb / citation_human for UCN-pattern contamination per the documented audit), compute l1_assets_projected_count/array from DISTINCT source_l1_asset in bodha_msr_signals, and either implement or explicitly mark 'not yet implemented' (rather than hardcoded True/pass) the three stubbed boolean gates so the scorecard doesn't imply verification that never ran.
- **fix_type:** `code`
- **Status:** FIXED (commit `7295f1ff`)

**[MINOR] L5-DataEng / L2-Data** — verification: `UNVERIFIED`

- **Finding:** bodha_msr_signals.verification_pass_status carries 8 distinct raw values inherited pass-through from upstream L1 fact rows, with inconsistent casing/vocabulary (two_pass_verified, computed_extension, PASS [uppercase — stylistic outlier], single, floored, classical_match, documented_approximation, not_defined_for_nodes). bo_pramana_mapa's scorecard only buckets two of these (two_pass_verified_pct=94.26%, documented_approximation_pct=0.07%) — leaving ~5,791 signals (≈8.7%) in unclassified/unreported buckets, so the two published quality percentages don't account for the full population and understate how much of the chart is not two-pass-verified.
- **Evidence:** SELECT verification_pass_status, count(*) FROM bodha_msr_signals WHERE chart_id=... GROUP BY 1 → two_pass_verified 62980, computed_extension 1632, PASS 1095, single 649, floored 335, classical_match 60, documented_approximation 45, not_defined_for_nodes 20 (total 66816, only 63025/66816=94.33% covered by the two reported percentages' numerators).
- **Fix:** Normalize verification_pass_status vocabulary at the L1→L2 boundary (map to a canonical enum), and have bo_pramana_mapa report a full histogram (or at minimum a 'other/unclassified_pct') rather than only two named buckets, so the scorecard percentages sum to 100%.
- **fix_type:** `code`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `bo_samvada`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `bo_pratijna`

**[MAJOR] L2-Data / L4-Astro** — verification: `CONFIRMED`

- **Finding:** varga_confirmation column is 0% populated (0 of 110 rows for Abhinandan) — hardcoded to None in the writer. Varga (divisional-chart) confirmation of a promised/denied event is a core classical requirement (Parashari principle that a yoga/promise must be corroborated in the relevant divisional chart, e.g. D9/D10, to fructify) and this asset's entire purpose is adjudicating promised/conditional/denied event classes (45 conditional / 40 denied / 25 promised for Abhinandan) — yet the varga-confirmation dimension of that adjudication is never computed. This is the known scar pattern: a column exists, joins/feeds nothing, silently starving downstream consumers.
- **Evidence:** bo_pratijna.py line 186: `"varga_confirmation": None,` (unconditional). SQL: `count(varga_confirmation)` = 0 of 110 rows for chart_id=1c826d5a-....
- **Fix:** Implement varga_confirmation by checking the relevant divisional chart(s) (via ga_vargas / chart_divisionals, already an L1 asset, 21,635 rows) for corroboration of the event class's significator placement, per the classical rule cited in this asset's own spec.
- **fix_type:** `code`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)


## L3 — Kala

### `ka_kalasutra`

**[BLOCKER] L5-DataEng** — verification: `CONFIRMED`

- **Finding:** asset_throughput.rows_written is wildly stale/inflated relative to the live target tables for six of the fourteen Kāla assets: ka_sangam claims 1700 vs actual kala_convergence=71; ka_vighnakara claims 642 vs actual kala_obstruction=0; ka_kalasutra claims 66816 vs actual kala_activation=13383; ka_kala_darshana claims 750 vs actual kala_darshana=0; ka_bhavishya_lekha claims 36 vs actual kala_bhavishya=0; ka_avadhi claims 6672 vs actual kala_avadhi=1937. ka_yojaka, ka_taranga, ka_jivana_parva match exactly, so this isn't a systemic query issue — it's specific to assets whose live tables were emptied/shrunk by a later run that didn't correspondingly update asset_throughput.
- **Evidence:** Direct comparison of `SELECT rows_written FROM asset_throughput WHERE chart_id=... AND asset_id IN (...)` against `SELECT count(*) FROM <target_table> WHERE chart_id=...` for each asset (see numbers above).
- **Fix:** Treat asset_throughput as informational only (per CLAUDE.md §N.4 'Cockpit truth' — count_sql is the source of truth), but investigate why a partial/out-of-band re-run desynced it this badly; add a drift check comparing asset_throughput.rows_written to count_sql at build close and alert on divergence beyond a small tolerance.
- **fix_type:** `dag`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `ka_sangam`

**[BLOCKER] L5-DataEng** — verification: `CONFIRMED`

- **Finding:** asset_throughput.rows_written is wildly stale/inflated relative to the live target tables for six of the fourteen Kāla assets: ka_sangam claims 1700 vs actual kala_convergence=71; ka_vighnakara claims 642 vs actual kala_obstruction=0; ka_kalasutra claims 66816 vs actual kala_activation=13383; ka_kala_darshana claims 750 vs actual kala_darshana=0; ka_bhavishya_lekha claims 36 vs actual kala_bhavishya=0; ka_avadhi claims 6672 vs actual kala_avadhi=1937. ka_yojaka, ka_taranga, ka_jivana_parva match exactly, so this isn't a systemic query issue — it's specific to assets whose live tables were emptied/shrunk by a later run that didn't correspondingly update asset_throughput.
- **Evidence:** Direct comparison of `SELECT rows_written FROM asset_throughput WHERE chart_id=... AND asset_id IN (...)` against `SELECT count(*) FROM <target_table> WHERE chart_id=...` for each asset (see numbers above).
- **Fix:** Treat asset_throughput as informational only (per CLAUDE.md §N.4 'Cockpit truth' — count_sql is the source of truth), but investigate why a partial/out-of-band re-run desynced it this badly; add a drift check comparing asset_throughput.rows_written to count_sql at build close and alert on divergence beyond a small tolerance.
- **fix_type:** `dag`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

**[MAJOR] L3-Code** — verification: `CONFIRMED`

- **Finding:** kala_activation_predicates.dasha_eligibility_rule_jsonb->>'eligibility_score' is 0% populated across all 66,816 rows for Abhinandan (no writer — ka_yojaka/binder.py — ever sets this key). Yet ka_sangam.plan_substeps ranks predicates with `ORDER BY (dasha_eligibility_rule_jsonb->>'eligibility_score')::float DESC NULLS LAST LIMIT 200` to pick the near-tier working set, and again slices `pred_dicts[:_LIFETIME_MAX_PREDICATES]` (60) from that same list for the lifetime tier. With every row NULL, the ORDER BY is a no-op and the 'top predicates by eligibility' selection is actually arbitrary DB-order — silently defeating the intended prioritization documented in the query's own SQL.
- **Evidence:** SELECT count(*), count(dasha_eligibility_rule_jsonb->>'eligibility_score'), count(distinct ...) FROM kala_activation_predicates WHERE chart_id=... → total=66816, has_score=0, distinct_scores=0. grep for 'eligibility_score' in services/ka_yojaka/binder.py and classifier.py returns nothing.
- **Fix:** Either populate eligibility_score in build_predicate()/classify_signal() (e.g. from dignity_score, cgm_centrality_weight, or a composite), or replace the ORDER BY with a field that is actually populated (cgm_centrality_weight, dignity_score) so the LIMIT 200/60 selection is meaningful rather than incidental.
- **fix_type:** `code`
- **Status:** FIXED (commit `b9bb8b7c`)

**[MAJOR] L2-Data / L6-Coverage** — verification: `CONFIRMED`

- **Finding:** kala_convergence for Abhinandan has zero horizon_tier='lifetime' rows and zero mode='C' (SUBSYSTEM period) or mode='D' (AV-bindhu) rows — only 71 'near'-tier mode A/B rows exist. SUBSYSTEM predicates are 59,506 of 66,816 (89%) of the whole predicate population and are routed exclusively to Mode C; with Mode C producing zero output in the live data, the technique that covers the vast majority of MSR signals (sade-sati/āyur/vāstu period activations) is completely absent from the deliverable, and the dāśā-boundary-anchored 100-year lifetime tier (a documented U2 feature) is entirely missing.
- **Evidence:** SELECT horizon_tier, mode, count(*) FROM kala_convergence WHERE chart_id=... GROUP BY 1,2 → only ('near','A',40) and ('near','B',31); no 'lifetime' rows, no mode C/D rows. SELECT signature_class, count(*) FROM kala_activation_predicates WHERE chart_id=... → SUBSYSTEM=59506/66816.
- **Fix:** Investigate why _substep_lifetime produced 0 rows across all 60 lifetime predicates and why mode_c_subsystem_period/mode_d_av_bindhu produced 0 windows for this chart (check KaGocharaService availability, EnrichmentContext.ashtakavarga_bindu population, and whether lifetime substeps actually executed) before treating L3 as closed for this chart.
- **fix_type:** `code`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

**[MINOR] L4-Astro / L7-Optim** — verification: `UNVERIFIED`

- **Finding:** Actual convergence_score magnitudes for Abhinandan's near-tier windows are very low (min 0.039, max 0.162, avg ~0.08-0.11) against thresholds used downstream (ka_kala_darshana: 0.70/0.45/0.20 for auspicious tiers; ka_bhavishya_lekha: 0.70/0.45 for tier_1/tier_2). With every live convergence_score well under 0.20, all 71 windows fall into the lowest ('auspicious_speculative'/'neutral') bucket by construction — worth a native review of whether the convergence_score formula's scale matches the downstream tier thresholds, since as calibrated no window in this chart can ever reach 'auspicious_strong' or 'tier_1_high'.
- **Evidence:** SELECT min/max/avg(convergence_score) FROM kala_convergence WHERE chart_id=... GROUP BY horizon_tier, mode → near/A avg=0.110, near/B avg=0.077, both far below the 0.45/0.70 tier thresholds hardcoded in ka_kala_darshana.py and ka_bhavishya_lekha.py.
- **Fix:** Have the native/astrology owner review whether convergence_score's scale (as currently composed from constituent_factors) is meant to top out near 0.15-0.20 for this chart, or whether the scoring formula under-weights contributing factors relative to the tier thresholds it feeds.
- **fix_type:** `native_judgment`
- **Status:** SKIPPED (native_judgment queued — see BA_AUDIT_FIX_PLAN §NATIVE_JUDGMENT_QUEUE)

### `ka_vighnakara`

**[BLOCKER] L2-Data** — verification: `CONFIRMED`

- **Finding:** For Abhinandan (chart_id 1c826d5a...), kala_obstruction, kala_darshana, and kala_bhavishya are ALL 0 rows in the live DB right now, even though kala_convergence has 71 rows (all with peak_date populated) that should feed all three downstream writers, and asset_registry/asset_throughput record these three assets as 'lit' with substantial historical rows_written (642 / 750 / 36). The entire back half of the Kāla DAG (obstruction detection, display-ready windows, forward projections) is currently empty for the case-study chart.
- **Evidence:** SELECT count(*) FROM kala_obstruction/kala_darshana/kala_bhavishya WHERE chart_id='1c826d5a-...' all return 0; kala_convergence for same chart_id returns 71 rows with peak_date IS NOT NULL.
- **Fix:** Re-run ka_vighnakara → ka_kala_darshana → ka_bhavishya_lekha (in DAG order) against Abhinandan and verify non-zero output; add a post-build integrity_check_sql on each of these assets that fails the build if convergence rows exist but the derived table is empty.
- **fix_type:** `dag`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

**[BLOCKER] L5-DataEng** — verification: `CONFIRMED`

- **Finding:** asset_throughput.rows_written is wildly stale/inflated relative to the live target tables for six of the fourteen Kāla assets: ka_sangam claims 1700 vs actual kala_convergence=71; ka_vighnakara claims 642 vs actual kala_obstruction=0; ka_kalasutra claims 66816 vs actual kala_activation=13383; ka_kala_darshana claims 750 vs actual kala_darshana=0; ka_bhavishya_lekha claims 36 vs actual kala_bhavishya=0; ka_avadhi claims 6672 vs actual kala_avadhi=1937. ka_yojaka, ka_taranga, ka_jivana_parva match exactly, so this isn't a systemic query issue — it's specific to assets whose live tables were emptied/shrunk by a later run that didn't correspondingly update asset_throughput.
- **Evidence:** Direct comparison of `SELECT rows_written FROM asset_throughput WHERE chart_id=... AND asset_id IN (...)` against `SELECT count(*) FROM <target_table> WHERE chart_id=...` for each asset (see numbers above).
- **Fix:** Treat asset_throughput as informational only (per CLAUDE.md §N.4 'Cockpit truth' — count_sql is the source of truth), but investigate why a partial/out-of-band re-run desynced it this badly; add a drift check comparing asset_throughput.rows_written to count_sql at build close and alert on divergence beyond a small tolerance.
- **fix_type:** `dag`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `ka_yojaka`

**[MAJOR] L1-Registry** — verification: `CONFIRMED`

- **Finding:** ka_yojaka's writer runs a runtime query joining bodha_pratijna (owned by asset bo_pratijna) and brahma_event_ontology (owned by asset bg_ghatana) for P5A pratijna linkage enrichment, but asset_registry.depends_on for ka_yojaka is only ['bo_laksana','bg_transit_rules','ga_dashas','bo_bimba','bo_sangati'] — bo_pratijna and bg_ghatana are consumed but undeclared.
- **Evidence:** ka_yojaka.py lines ~63-89: `FROM bodha_pratijna bp JOIN brahma_event_ontology beo USING (event_class_id)`. asset_registry query: target_table mapping shows bodha_pratijna→bo_pratijna, brahma_event_ontology→bg_ghatana; neither appears in ka_yojaka.depends_on.
- **Fix:** Add 'bo_pratijna' and 'bg_ghatana' to ka_yojaka.depends_on in asset_registry so the orchestrator schedules it correctly and dag_edge_guard doesn't miss this soft dependency.
- **fix_type:** `registry`
- **Status:** PARTIALLY FIXED — migration `406_kala_mimamsa_dag_edge_completeness.sql` + `asset_registry_seed.ts` correction committed (`c68e65c4`), but **NOT YET APPLIED to the live database**: re-verified via direct query this session, `asset_registry.depends_on` for `ka_yojaka` is still `['bo_laksana','bg_transit_rules','ga_dashas','bo_bimba','bo_sangati']` live (pre-fix). See `BA_ORCHESTRATOR_INTEGRITY_REPORT_v1_0.md` §2.1/§4 — this is one of the 3 confirmed live HARD DAG-edge violations still blocking global REBUILD-READY.

### `ka_kala_darshana`

**[BLOCKER] L2-Data** — verification: `CONFIRMED`

- **Finding:** For Abhinandan (chart_id 1c826d5a...), kala_obstruction, kala_darshana, and kala_bhavishya are ALL 0 rows in the live DB right now, even though kala_convergence has 71 rows (all with peak_date populated) that should feed all three downstream writers, and asset_registry/asset_throughput record these three assets as 'lit' with substantial historical rows_written (642 / 750 / 36). The entire back half of the Kāla DAG (obstruction detection, display-ready windows, forward projections) is currently empty for the case-study chart.
- **Evidence:** SELECT count(*) FROM kala_obstruction/kala_darshana/kala_bhavishya WHERE chart_id='1c826d5a-...' all return 0; kala_convergence for same chart_id returns 71 rows with peak_date IS NOT NULL.
- **Fix:** Re-run ka_vighnakara → ka_kala_darshana → ka_bhavishya_lekha (in DAG order) against Abhinandan and verify non-zero output; add a post-build integrity_check_sql on each of these assets that fails the build if convergence rows exist but the derived table is empty.
- **fix_type:** `dag`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

**[BLOCKER] L5-DataEng** — verification: `CONFIRMED`

- **Finding:** asset_throughput.rows_written is wildly stale/inflated relative to the live target tables for six of the fourteen Kāla assets: ka_sangam claims 1700 vs actual kala_convergence=71; ka_vighnakara claims 642 vs actual kala_obstruction=0; ka_kalasutra claims 66816 vs actual kala_activation=13383; ka_kala_darshana claims 750 vs actual kala_darshana=0; ka_bhavishya_lekha claims 36 vs actual kala_bhavishya=0; ka_avadhi claims 6672 vs actual kala_avadhi=1937. ka_yojaka, ka_taranga, ka_jivana_parva match exactly, so this isn't a systemic query issue — it's specific to assets whose live tables were emptied/shrunk by a later run that didn't correspondingly update asset_throughput.
- **Evidence:** Direct comparison of `SELECT rows_written FROM asset_throughput WHERE chart_id=... AND asset_id IN (...)` against `SELECT count(*) FROM <target_table> WHERE chart_id=...` for each asset (see numbers above).
- **Fix:** Treat asset_throughput as informational only (per CLAUDE.md §N.4 'Cockpit truth' — count_sql is the source of truth), but investigate why a partial/out-of-band re-run desynced it this badly; add a drift check comparing asset_throughput.rows_written to count_sql at build close and alert on divergence beyond a small tolerance.
- **fix_type:** `dag`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `ka_jivana_parva`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `ka_bhavishya_lekha`

**[BLOCKER] L2-Data** — verification: `CONFIRMED`

- **Finding:** For Abhinandan (chart_id 1c826d5a...), kala_obstruction, kala_darshana, and kala_bhavishya are ALL 0 rows in the live DB right now, even though kala_convergence has 71 rows (all with peak_date populated) that should feed all three downstream writers, and asset_registry/asset_throughput record these three assets as 'lit' with substantial historical rows_written (642 / 750 / 36). The entire back half of the Kāla DAG (obstruction detection, display-ready windows, forward projections) is currently empty for the case-study chart.
- **Evidence:** SELECT count(*) FROM kala_obstruction/kala_darshana/kala_bhavishya WHERE chart_id='1c826d5a-...' all return 0; kala_convergence for same chart_id returns 71 rows with peak_date IS NOT NULL.
- **Fix:** Re-run ka_vighnakara → ka_kala_darshana → ka_bhavishya_lekha (in DAG order) against Abhinandan and verify non-zero output; add a post-build integrity_check_sql on each of these assets that fails the build if convergence rows exist but the derived table is empty.
- **fix_type:** `dag`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

**[BLOCKER] L5-DataEng** — verification: `CONFIRMED`

- **Finding:** asset_throughput.rows_written is wildly stale/inflated relative to the live target tables for six of the fourteen Kāla assets: ka_sangam claims 1700 vs actual kala_convergence=71; ka_vighnakara claims 642 vs actual kala_obstruction=0; ka_kalasutra claims 66816 vs actual kala_activation=13383; ka_kala_darshana claims 750 vs actual kala_darshana=0; ka_bhavishya_lekha claims 36 vs actual kala_bhavishya=0; ka_avadhi claims 6672 vs actual kala_avadhi=1937. ka_yojaka, ka_taranga, ka_jivana_parva match exactly, so this isn't a systemic query issue — it's specific to assets whose live tables were emptied/shrunk by a later run that didn't correspondingly update asset_throughput.
- **Evidence:** Direct comparison of `SELECT rows_written FROM asset_throughput WHERE chart_id=... AND asset_id IN (...)` against `SELECT count(*) FROM <target_table> WHERE chart_id=...` for each asset (see numbers above).
- **Fix:** Treat asset_throughput as informational only (per CLAUDE.md §N.4 'Cockpit truth' — count_sql is the source of truth), but investigate why a partial/out-of-band re-run desynced it this badly; add a drift check comparing asset_throughput.rows_written to count_sql at build close and alert on divergence beyond a small tolerance.
- **fix_type:** `dag`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `ka_tulana`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `ka_avadhi`

**[BLOCKER] L5-DataEng** — verification: `CONFIRMED`

- **Finding:** asset_throughput.rows_written is wildly stale/inflated relative to the live target tables for six of the fourteen Kāla assets: ka_sangam claims 1700 vs actual kala_convergence=71; ka_vighnakara claims 642 vs actual kala_obstruction=0; ka_kalasutra claims 66816 vs actual kala_activation=13383; ka_kala_darshana claims 750 vs actual kala_darshana=0; ka_bhavishya_lekha claims 36 vs actual kala_bhavishya=0; ka_avadhi claims 6672 vs actual kala_avadhi=1937. ka_yojaka, ka_taranga, ka_jivana_parva match exactly, so this isn't a systemic query issue — it's specific to assets whose live tables were emptied/shrunk by a later run that didn't correspondingly update asset_throughput.
- **Evidence:** Direct comparison of `SELECT rows_written FROM asset_throughput WHERE chart_id=... AND asset_id IN (...)` against `SELECT count(*) FROM <target_table> WHERE chart_id=...` for each asset (see numbers above).
- **Fix:** Treat asset_throughput as informational only (per CLAUDE.md §N.4 'Cockpit truth' — count_sql is the source of truth), but investigate why a partial/out-of-band re-run desynced it this badly; add a drift check comparing asset_throughput.rows_written to count_sql at build close and alert on divergence beyond a small tolerance.
- **fix_type:** `dag`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

**[MAJOR] L1-Registry** — verification: `CONFIRMED`

- **Finding:** ka_avadhi.depends_on = ['ka_yojaka','bo_pratijna'], but the writer never reads any table owned by ka_yojaka (kala_activation_predicates is not referenced anywhere in ka_avadhi.py) — a phantom edge — while it DOES read chart_dashas (owned by ga_dashas), chart_facts (owned by ga_positions/ga_nakshatra/ga_panchanga), and brahma_event_ontology (owned by bg_ghatana), none of which are declared.
- **Evidence:** ka_avadhi.py: _FETCH_MD_SQL/_FETCH_AD_SQL read chart_dashas; _FETCH_FACT_REFS_SQL reads chart_facts; _FETCH_PRATIJNA_SQL joins brahma_event_ontology. None of ga_dashas/ga_positions/ga_nakshatra/ga_panchanga/bg_ghatana appear in ka_avadhi.depends_on, while ka_yojaka (never read) does.
- **Fix:** Replace 'ka_yojaka' with 'ga_dashas' (real hard dependency) in depends_on, and add 'bg_ghatana' as a soft dependency; ga_positions/nakshatra/panchanga share the chart_facts table so at minimum one of them (or a canonical L1 facts marker) should be declared.
- **fix_type:** `registry`
- **Status:** PARTIALLY FIXED — migration `406_kala_mimamsa_dag_edge_completeness.sql` committed (`c68e65c4`), but **NOT YET APPLIED to the live database**: re-verified via direct query this session, `asset_registry.depends_on` for `ka_avadhi` is still `['ka_yojaka','bo_pratijna']` live (pre-fix, phantom edge still present).

### `ka_taranga`

**[MAJOR] L1-Registry** — verification: `CONFIRMED`

- **Finding:** ka_taranga.depends_on = ['ka_avadhi','bo_pratijna'], but the writer reads kala_convergence directly (owned by ka_sangam) for transit contribution, plus chart_dashas (ga_dashas) and brahma_event_ontology (bg_ghatana) — none of ka_sangam/ga_dashas/bg_ghatana are declared.
- **Evidence:** ka_taranga.py: `SELECT domain, window_start::date, window_end::date, convergence_score FROM kala_convergence WHERE chart_id = %s` and `SELECT lord_graha, start_date AS ds, end_date AS de FROM chart_dashas ...` and pratijna query joins brahma_event_ontology. asset_registry.depends_on for ka_taranga omits ka_sangam, ga_dashas, bg_ghatana.
- **Fix:** Add 'ka_sangam', 'ga_dashas', and 'bg_ghatana' to ka_taranga.depends_on.
- **fix_type:** `registry`
- **Status:** PARTIALLY FIXED — migration `406_kala_mimamsa_dag_edge_completeness.sql` committed (`c68e65c4`), but **NOT YET APPLIED to the live database**: re-verified via direct query this session, `asset_registry.depends_on` for `ka_taranga` is still `['ka_avadhi','bo_pratijna']` live (pre-fix). This is the other of the 3 confirmed live HARD DAG-edge violations still blocking global REBUILD-READY (see `BA_ORCHESTRATOR_INTEGRITY_REPORT_v1_0.md` §2.1/§4).

### `ka_graha_sancara`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `ka_dasha_kala`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `ka_muhurta_seva`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `ka_gochara`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)


## L4 — Phala

### `ph_nimitta`

**[BLOCKER] L4-Astro/L3-Code** — verification: `CONFIRMED`

- **Finding:** The BA-P5B posterior model (compute_posterior) is fed entirely from hardcoded literal defaults in writer._build_ctx() (pratijna_grade=5.0, pratijna_status='conditional', multi_system_confirmation_count=0, av_transit_potency=0.0, base_rate=0.10, ayanamsha_robustness=3) for every anchor, regardless of source/domain/signal. None of bodha_pratijna, ka_yojaka, or AV-transit tables are actually queried despite being named in code comments as the intended source. Result: posterior/confidence_high collapse to one constant value across 100% of an entire chart's anchors — a scoring column collapsed to a single value.
- **Evidence:** services/ph_nimitta/engine.py lines 505-513 (writer) and NimittaContext defaults; for Abhinandan (100 phala_anchors rows) confidence_high = 0.211 EXACTLY for all 100 rows (min=max=avg=0.211), posterior likewise fixed at ~0.161 by the formula (0.10 x promise_lift(5.0,'conditional')=1.75 x activation_lift(0)=1.0 x trigger_lift(0.0)=1.0 x rob_mod(3)=0.92 = 0.161). dasha_consensus_count=0 and ayanamsha_robustness=3 are likewise flat across all 100 rows.
- **Fix:** Wire _build_ctx to query bodha_pratijna (grade/status per event_class), ka_yojaka (multi_system_confirmation_count), and the AV/SAV transit gate (av_transit_potency) per anchor/window instead of using literal defaults; until that wiring lands, treat every posterior/confidence value in phala_anchors as non-differentiated placeholder data unsuitable for anomaly detection, muhurta scoring, or phaladesa ranking.
- **fix_type:** `code`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

**[MAJOR] L2-Data/L3-Code** — verification: `REFUTED`

- **Finding:** karmic_frame (one of the 5 documented 'elevations' V1-V5) is NULL for 100% of rows in phala_anchors (500/500 across both charts). Root cause: derive_karmic_frame(root_graha) needs ctx.root_graha, which is only populated from bodha_cgm_paths keyed off signal_id; but discovery-sourced anchors (100% of Abhinandan's anchors) are loaded with signal_id hardcoded to NULL (_load_discoveries: 'NULL::uuid AS signal_id'), so cgm_meta lookup is always empty and root_graha is always None. The ph_nimitta SPINE-FIRST gate (_spine_gate) does not check karmic_frame at all, so a chart can pass D26 with zero karmic-frame coverage.
- **Evidence:** SELECT karmic_frame, count(*) FROM phala_anchors GROUP BY karmic_frame -> {null: 500}. _load_discoveries SELECT explicitly casts 'NULL::uuid AS signal_id'; _build_ctx sid=str(row.get('signal_id') or '') -> '' for every discovery row; _load_cgm_meta returns {} when signal_ids list is empty.
- **Fix:** Either derive root_graha for discovery anchors from a discovery-specific signal (bodha_discoveries has its own graha/cross_subsystem linkage that could substitute), or add karmic_frame completeness to the D26 spine gate so a 0%-coverage build is caught rather than silently passing.
- **fix_type:** `code`
- **Status:** N/A (finding refuted — no fix needed)
- **Refutation rationale:** The top-line symptom is real and independently reproduced: `SELECT karmic_frame, count(*) FROM phala_anchors GROUP BY karmic_frame` returns exactly {null: 500} across both charts. The code-level facts cited are also literally true (`_load_discoveries` casts NULL::uuid AS signal_id; `_build_ctx` computes sid='' for discovery rows; `_spine_gate` never checks karmic_frame). However, the finding's causal chain — that cgm_meta lookup is always empty and root_graha is always None — is demonstrably false for 300 of the 500 affected rows (the native chart's bhavishya+convergence anchors, which DO carry a resolvable signal_id and a non-empty cgm_meta result with a real path_label_human) yet karmic_frame is still NULL for them. The actual root cause for those rows is a separate, more fundamental format-mismatch bug in derive_karmic_frame()'s exact-match dict lookup against bare planet-name keys, which never match the multi-planet arrow-chain / parenthetical path_label_human strings actually stored. Because the finding's root-cause analysis is materially incomplete and the proposed fix would not resolve the majority of the 100%-NULL condition, it is not confirmed as stated despite the real underlying symptom.

**[MAJOR] L2-Data/L6-Coverage** — verification: `REFUTED`

- **Finding:** 100% of Abhinandan's 100 phala_anchors rows are anchor_source='discovery'. kala_convergence has 71 rows for this chart_id and is loaded by the writer (_load_convergence returns 71 rows per the query), yet ZERO convergence-sourced anchors made it into phala_anchors — every one of the 71 derive_anchor_from_convergence calls must have raised inside the per-row try/except (silently logged as a warning, not surfaced). kala_bhavishya is genuinely empty (0 rows) for this chart so 0 bhavishya anchors is at least consistent with upstream data, but the convergence miss has no visible cause and needs runtime-log investigation.
- **Evidence:** kala_convergence count for chart_id=1c826d5a...: 71 rows (verified, valid jsonb constituent_factors, valid signal_id). phala_anchors anchor_source GROUP BY for the same chart_id returns only {'discovery': 100} -- zero 'convergence' or 'bhavishya' rows.
- **Fix:** Re-run ph_nimitta with warning-level logging surfaced/inspected to capture the actual exception per convergence row (likely a KeyError/type coercion issue specific to this chart's kala_convergence rows); add a chart-level assertion/warning if convergence_rows loaded > 0 but anchors_from_convergence == 0, since that is itself anomalous and currently invisible in the build summary.
- **fix_type:** `code`
- **Status:** N/A (finding refuted — no fix needed)
- **Refutation rationale:** The observational evidence (100 rows all anchor_source='discovery'; kala_convergence=71 valid rows; kala_bhavishya=0 rows) is independently confirmed. However, the finding's proposed root-cause mechanism — that all 71 derive_anchor_from_convergence calls raised inside the per-row try/except — does not survive direct reproduction: running the actual unmodified writer code (PhNimittaWriter._load_convergence / _build_ctx and engine.py's derive_anchor_from_convergence) against the real 71 kala_convergence rows for this chart produced 71/71 successful derivations with zero exceptions, and a savepoint-wrapped probe insert of the same 71 rows into phala_anchors succeeded with zero constraint violations. Timestamps also rule out a stale-load race (kala_convergence committed ~3 hours before ph_nimitta's last recorded run). The finding's specific claimed mechanism is refuted by this reproduction; the true cause in the actual production run remains unexplained (possible stale deployed image or connection/DAG-ordering issue, neither confirmed).

**[MAJOR] L6-Coverage** — verification: `CONFIRMED`

- **Finding:** Of the 7 canonical domains (career, relationship, financial, spiritual, health, transition, psychological), only 2 (career=22, transition=78) have any anchors for Abhinandan; relationship, financial, spiritual, health, and psychological have zero anchors. This cascades: phala_phaladesa's 5 corresponding domain rows are entirely null (anchor_count=0, no magnitude/confidence/window), and ph_muhurta/ph_pratikara/ph_sankrama/ph_pramana have no material for those 5 domains at all.
- **Evidence:** SELECT domain, count(*) FROM phala_anchors WHERE chart_id=Abhinandan GROUP BY domain -> {transition:78, career:22}. phala_phaladesa rows for character/health/relationship/spirituality/wealth all show anchor_count=0, magnitude=NULL.
- **Fix:** Investigate why 100% discovery-sourced anchors concentrate into only 2 of 7 domains -- likely the _SUBSYSTEM_DOMAIN fallback map in ph_nimitta.py (many bodha_discoveries subsystem values map to 'career' or default to 'transition'); broaden/correct the subsystem-to-domain mapping so bodha_discoveries' actual domain diversity is preserved rather than collapsed.
- **fix_type:** `code`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

**[MINOR] L6-Coverage** — verification: `UNVERIFIED`

- **Finding:** malleability is a single constant value ('influenceable') across 100% of Abhinandan's 100 anchors. derive_malleability() can only return 'fated' when magnitude=='pivotal' AND direction=='suppressed', but discovery-sourced anchors (100% of this chart) hardcode direction='elevated' unconditionally (engine.py line 653) and magnitude is always 'minor' given the flat confidence_score inputs -- so 'fated' and 'semi_influenceable' (which requires a domain outside {career,health,transition,financial}) are structurally unreachable for this chart's anchor population (career/transition are both in the influenceable set).
- **Evidence:** SELECT malleability, count(*) FROM phala_anchors WHERE chart_id=Abhinandan GROUP BY malleability -> {'influenceable': 100}.
- **Fix:** Once the discovery pathway's direction/magnitude are no longer hardcoded/flat (see the posterior-model finding), malleability diversity should follow naturally; track as a downstream consequence rather than a separate code fix.
- **fix_type:** `code`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `ph_muhurta`

**[MAJOR] L3-Code/L2-Data** — verification: `CONFIRMED`

- **Finding:** _load_condition_scores queries ga_condition_composite (which DOES have varying, non-flat condition_score data for Abhinandan: e.g. Mercury 0/0.165/0.165/0.165/0.165, Saturn 0.285/0.31/0.285/0.285/0.285), but every phala_muhurta row for this chart shows chart_personalization_score = exactly 0.5 for both graha groups (mercury n=24, saturn n=9; min=max=avg=0.5) -- the literal fallback constant from `condition_scores.get(relevant_graha, 0.5)`. This means the query's result dict was empty at runtime despite matching source rows existing, and the surrounding except block (logger.debug) suppressed the actual cause at a log level unlikely to be reviewed.
- **Evidence:** ga_condition_composite for chart_id=Abhinandan has 5 rows per graha with real variation (not 0.5) for Mercury and Saturn specifically. phala_muhurta.chart_personalization_score for the same chart is 0.5 for all 33 rows regardless of personalization_graha.
- **Fix:** Investigate why _load_condition_scores's plain cursor (no row_factory, positional row[0]/row[1]) returns nothing usable for this chart at runtime -- also note the query has no ORDER BY over 5 rows per graha, so even a working path would be nondeterministic about which of the 5 rows 'wins' in the dict overwrite. Elevate the except's log level from debug to warning (matching the ph_pratikara/ph_sankrama pattern already fixed elsewhere) so this stops being invisible.
- **fix_type:** `code`
- **Status:** FIXED (commit `4cfdeefd`)

**[MINOR] L4-Astro** — verification: `UNVERIFIED`

- **Finding:** tarabala_score and chandrabala_score are hardcoded 0.5/0.5 for all 33 Abhinandan rows (natal_moon_nakshatra_idx=0, i.e. the natal-Moon lookup also fell back to its default), and gochara-based transit_score is unconditionally the neutral 0.5 default because there is no kala_gochara table (ka_gochara is compute-only, documented as an honest known gap in the writer). Composite_quality collapses to only 2 near-identical values (0.105 x27, 0.15 x6), both verdict='mediocre' -- every muhurta window for this chart reads as equally mediocre, which is astrologically uninformative for an auspicious-timing feature.
- **Evidence:** phala_muhurta tarabala_chandrabala_jsonb is identical for all 33 rows: {tarabala_score:0.5, chandrabala_score:0.5, natal_moon_nakshatra_idx:0}. composite_quality distinct values = {0.105:27, 0.15:6}.
- **Fix:** This is the already-documented L4-campaign gap (gochara service wiring, tarabala/chandrabala serve-time computation) -- queue as a native-review item on priority, since it makes ph_muhurta currently non-discriminating for any chart.
- **fix_type:** `native_judgment`
- **Status:** SKIPPED (native_judgment queued — see BA_AUDIT_FIX_PLAN §NATIVE_JUDGMENT_QUEUE)

### `ph_sodhana`

**[MAJOR] L2-Data/L6-Coverage** — verification: `CONFIRMED`

- **Finding:** phala_sodhana returns 0 anomaly rows for Abhinandan's 100 anchors, while for the native chart (482012f1, 400 anchors) it flags confidence_inflation on 400/400 (100%) and falsifier_absent on 100/400. The zero-flag result for Abhinandan is not because the anchors are healthy -- it's because the flat posterior/confidence (0.211, see ph_nimitta finding) happens to sit safely under the G-LADDER ceiling (~0.506 given dasha_consensus_count=0, ayanamsha_robustness=3), so detect_confidence_inflation never fires. The detector suite has no check for 'confidence value has zero variance across every anchor in the chart', which is arguably the single most informative anomaly present for this chart and currently passes as clean.
- **Evidence:** phala_sodhana chart-scoped counts: Abhinandan=0 rows; native=500 rows (400 confidence_inflation + 100 falsifier_absent). phala_anchors confidence_high for Abhinandan is a single constant (0.211) across all 100 rows.
- **Fix:** Add a 6th detector (e.g. detect_confidence_degenerate) that flags when the chart-wide stddev of confidence_high/posterior across anchors is ~0, since a hand-off audit or automated build would otherwise read '0 anomalies' as a clean bill of health for a structurally broken posterior model.
- **fix_type:** `code`
- **Status:** PARTIALLY FIXED — `detect_confidence_degenerate()` added to `services/ph_sodhana/engine.py` (commit `4d4f3adc`), but its companion migration `407_phala_sodhana_confidence_degenerate_check.sql` (widens `phala_sodhana.anomaly_type` CHECK to allow the new value) is **NOT YET APPLIED to the live database**: re-verified via direct query this session, the live CHECK constraint still only allows `{confidence_inflation, magnitude_drift, falsifier_absent, ledger_gap, layer_leakage}` — the new detector will raise a constraint violation on insert until the migration runs.

### `ph_pratikara`

**[BLOCKER] L5-DataEng/L2-Data** — verification: `CONFIRMED`

- **Finding:** phala_mitigation has 642 rows for Abhinandan, all with afflicting_graha='saturn' (100% degenerate), but kala_obstruction -- the writer's primary source table (_load_obstructions: FROM kala_obstruction o JOIN kala_convergence c) -- has ZERO rows for this chart_id right now. Since the writer's main loop is `for obs in obstructions`, an empty obstructions list would produce zero phala_mitigation rows; 642 existing rows can only be explained by a stale build (phala_mitigation was not rebuilt after kala_obstruction was subsequently cleared/rebuilt to empty for this chart).
- **Evidence:** SELECT count(*) FROM kala_obstruction WHERE chart_id=Abhinandan -> 0 rows. SELECT count(*) FROM phala_mitigation WHERE chart_id=Abhinandan -> 642 rows, 100% afflicting_graha='saturn'.
- **Fix:** Re-run ph_pratikara for this chart (it will correctly delete-then-insert to 0 rows given current empty kala_obstruction, or repopulate if kala_obstruction is itself missing data that should exist -- audit ka_vighnakara/ka_sangam upstream too). Add a DAG-level staleness check: if an upstream dependency's row count changed since a downstream asset's computed_at, flag for rebuild.
- **fix_type:** `code`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `ph_suddha_sodhana`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `ph_sankrama`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `ph_pramana`

**[MAJOR] L2-Data** — verification: `CONFIRMED`

- **Finding:** life_events (the LEL source table) has 0 rows in the entire database (not chart-scoped -- global check). ph_pramana's _load_lel therefore always returns an empty list for every chart, so window_status/evidence_type classification against real life-event outcomes never happens for any chart, including the native.
- **Evidence:** SELECT count(*) FROM life_events -> 0 (global, all charts). phala_pramana for Abhinandan has 100 rows (1 per anchor) but necessarily lel_entry_id/lel_entry_jsonb are NULL for all of them since no LEL rows exist to match.
- **Fix:** This is an ingestion/data gap (LEL v1.7 markdown was never loaded into the life_events table), not a writer bug -- ph_pramana's code path is correct and fails safe. Flag for native/ops: populate life_events from LIFE_EVENT_LOG_v1_2.md before evidence classification can be meaningful.
- **fix_type:** `seed`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `ph_phaladesa`

**[BLOCKER] L5-DataEng/L2-Data** — verification: `CONFIRMED`

- **Finding:** phala_phaladesa for Abhinandan is stale relative to the current phala_anchors state: career anchor_count=66 and transition anchor_count=270 (sum=336), but phala_anchors currently has only 22 career + 78 transition = 100 rows total for this chart. The domain-summary aggregation is recomputed fresh on every run from a straight 1:1 join (verified: pa/ss/pr join returns exactly 100 rows for the current phala_anchors), so the only way phala_phaladesa can show 336 is if it was last successfully built against an earlier, larger phala_anchors population and has not been rebuilt since phala_anchors was reduced to 100 rows.
- **Evidence:** phala_phaladesa (career): anchor_count=66, clean_anchor_count=63; (transition): anchor_count=270, clean_anchor_count=223. phala_anchors chart-scoped count = 100 (22 career + 78 transition). A fresh LEFT JOIN of phala_anchors x phala_suddha_sodhana x phala_pramana for this chart_id returns exactly 100 rows, not 336 -- confirming the join itself doesn't fan out; the phala_phaladesa row content is stale.
- **Fix:** Confirm ph_phaladesa was re-run as part of the current Abhinandan rebuild; if not, re-run it (and ph_pratikara/ph_muhurta if similarly stale) so downstream aggregates reflect the current phala_anchors state. Add a build-time consistency check (e.g. anchor_count per domain <= total phala_anchors row count for the chart) to catch this class of stale-aggregate bug automatically.
- **fix_type:** `code`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `ph_rectification`

**[BLOCKER] L4-Astro/L3-Code** — verification: `CONFIRMED`

- **Finding:** services/ph_rectification/engine.py hardcodes the ORIGINAL native's (Abhisek Mohanty) 19-event life-event log (TRAINING_EVENTS) and his natal dasha-lord sign positions (_DASHA_LORD_NATAL_SIGN_INDEX: Saturn=Scorpio, Mercury=Capricorn) as module-level constants. run_rectification() correctly takes recorded_birth_utc per-chart from the writer, but TRAINING_EVENTS and _DASHA_LORD_NATAL_SIGN_INDEX are never parameterized by chart_id — every chart's rectification scan is scored against Abhisek's own biography and his own graha positions, not the chart being rectified.
- **Evidence:** engine.py lines 71-102, 219-223: RECORDED_BIRTH_UTC/NATIVE_LAT/NATIVE_LON/TRAINING_EVENTS/_DASHA_LORD_NATAL_SIGN_INDEX are frozen module constants with docstring 'Canonical native birth params (NEVER fabricate; from CLAUDE.md §B)'. For Abhinandan (chart_id 1c826d5a...) phala_rectification shows lel_fit_score = 0.2105 EXACTLY across all 185 rows (5 ayanamshas x 37 offsets; min=max=avg=0.2105), and phala_rectification_best shows confidence_label='unresolved', win_margin=0.0000 — i.e. rectification is structurally incapable of discriminating any candidate for a non-native chart because the scoring events/dasha-lord positions are not this chart's.
- **Fix:** Parameterize score_candidate/run_rectification/select_best to accept a chart-scoped training_events list and a chart-scoped dasha-lord natal sign index (derived from that chart's own chart_facts/life_events), instead of the module constants. Only fall back to the Abhisek constants when chart_id == canonical native chart_id (482012f1...).
- **fix_type:** `code`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

**[ENHANCEMENT] L4-Astro** — verification: `UNVERIFIED`

- **Finding:** The engine docstring documents this as a deliberate 'sign-level scan' limitation (lel_fit_score is expected to be uniform across stable candidates within a lagna-sign-stable window, with confidence_label='unresolved' being the correct output) rather than a bug in the scoring math itself. However, combined with the cross-native TRAINING_EVENTS contamination (separate BLOCKER finding above), this chart's rectification result is doubly non-informative: even a correctly-generic scorer would only be sign-level for this window, and the current implementation additionally scores against the wrong native's events.
- **Evidence:** engine.py docstring lines 34-48 explicitly frames uniform lel_fit_score + 'unresolved' as B.10-compliant, not a defect, for the sign-level scan.
- **Fix:** Once TRAINING_EVENTS is chart-scoped (see BLOCKER above), consider prioritizing the documented D41 sub-degree tiered scorer (bhava cusps, navamsa, dasha sub-period alignment) so ph_rectification can actually discriminate within a stable lagna sign.
- **fix_type:** `native_judgment`
- **Status:** SKIPPED (native_judgment queued — see BA_AUDIT_FIX_PLAN §NATIVE_JUDGMENT_QUEUE)


## L5 — Mimamsa

### `mi_jivanaghatana`

**[BLOCKER] L5-DataEng / L2-Data** — verification: `CONFIRMED`

- **Finding:** The L5 root asset's primary evidence source produces ZERO rows in production for BOTH charts (native 482012f1 and case-study Abhinandan 1c826d5a), yet reports a clean 'lit' build state with no error. asset_throughput shows rows_written=0, last_error=null for both. life_events DB fallback table is also empty (0 rows). This silently collapses the entire downstream evidentiary chain: mimamsa_calibration=0, mimamsa_reliability=0, mimamsa_attribution=0, mimamsa_discoveries=0 for both charts, even though mi_pramana/mi_pariksha/mi_darshana all report successful builds — they are just running against no evidence.
- **Evidence:** asset_throughput rows for mi_jivanaghatana: {chart_id:1c826d5a...,state:'lit',rows_written:0,last_error:null}; {chart_id:482012f1...,state:'lit',rows_written:0,last_error:null}. `select count(*) from life_events` = 0. `select chart_id,count(*) from mimamsa_event_provenance group by chart_id` returns []. Writer at mi_jivanaghatana.py resolves the LEL markdown via a relative path (`Path(__file__).parents[4]/'01_FACTS_LAYER'/...`) that is fragile across deployment/container boundaries and silently falls back to the empty life_events table on any resolution/parse failure, returning a benign WriterResult('no events found...') rather than failing the build.
- **Fix:** Verify the sidecar's production/runtime container actually bundles 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md at the resolved path; if it does not, fix packaging or use an env-var-configurable absolute path. Additionally, make the writer fail loudly (raise, not return a clean WriterResult) when BOTH the markdown and the DB fallback yield zero events — a 0-row root asset with downstream calibration/reliability/attribution all also at 0 should never read as a healthy 'lit' build.
- **fix_type:** `code`
- **Status:** FIXED (commit `d8dc7ed0` — corrected the path resolution bug (`parents[4]` never resolved to a real directory; fixed to `parents[5]` = repo root, verified locally), added an env-var override, and made the writer raise instead of silently returning a clean `WriterResult` when both the markdown and the DB fallback yield zero events)

**[BLOCKER] L3-Code** — verification: `CONFIRMED`

- **Finding:** `_parse_lel_markdown()` silently discards any YAML block that fails `yaml.safe_load()` via a bare `except Exception: continue`, with no count of skipped-vs-parsed blocks logged separately from the final total. Reproducing the parse locally against the live LIFE_EVENT_LOG_v1_2.md, 33 of 63 ```yaml blocks fail to parse (unquoted colons inside narrative string values break YAML block-mapping parsing) — only 30 events survive.
- **Evidence:** Local repro: `re.findall(r'```yaml\n(.*?)\n```', ...)` found 63 blocks; `yaml.safe_load` raised on 33 of them (e.g. `date: 2001-03-XX ... and continued till June 2003.` — colon inside an unquoted narrative string breaks the mapping). The writer's log line only reports `len(events)` after the silent drops, e.g. 'parsed %d events from LEL markdown' — there is no 'skipped %d malformed blocks' signal anywhere.
- **Fix:** Fix the malformed YAML in LIFE_EVENT_LOG_v1_2.md (quote string values containing colons), and change the parser to log/surface a distinct skipped-block count (and ideally fail the build, not just log) instead of silently absorbing parse errors.
- **fix_type:** `code`
- **Status:** PARTIALLY FIXED (commit `d8dc7ed0` — added per-block skip logging and an aggregate parsed/skipped count so the drop is no longer silent/invisible; the underlying malformed YAML content in `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` — 33 of 63 blocks with unquoted colons in narrative text — was deliberately **not** hand-edited this session, since altering a versioned canonical fact artifact's content requires native review + a version bump per CLAUDE.md §B.8, not a code-only fix. 33/63 blocks still fail to parse today.)

### `mi_kula`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `mi_bhavisya`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `mi_pramana`

**[MINOR] L3-Code** — verification: `UNVERIFIED`

- **Finding:** `_score_manifestation()` is a hardcoded constant `return 0.5, None` for every match on every chart — one of the five weighted composite scoring dimensions (weight 0.10) contributes a flat, non-discriminative value to every single `mimamsa_calibration.composite_score`, silently shifting every composite by a fixed +0.05 regardless of actual outcome-channel evidence. This is documented as intentional (comment: '0.5 (unknown) until outcome channel data accrues, n_support<5') so it is a known placeholder rather than a hidden bug, but nothing in the calibration row distinguishes 'scored 0.5 on the merits' from 'not yet scored.'
- **Evidence:** mi_pramana.py: `def _score_manifestation(manifestation_channels, event): return 0.5, None` — no chart_id, event, or channel data actually consulted.
- **Fix:** Either wire manifestation-channel scoring to mimamsa_manifestation_grammar's learned propensities once n_support>=5 exists, or exclude the manifestation dimension from the weighted composite (re-normalize the other four weights) until real data exists, rather than silently averaging in a constant.
- **fix_type:** `native_judgment`
- **Status:** SKIPPED (native_judgment queued — see BA_AUDIT_FIX_PLAN §NATIVE_JUDGMENT_QUEUE)

### `mi_gunanaka`

**[BLOCKER] L3-Code / L4-Astro** — verification: `CONFIRMED`

- **Finding:** The hierarchical-shrinkage 'family-level' evidence pooling (cell→family→global, the entire point of mi_gunanaka v2) silently degenerates to per-individual-signal pooling because the `driving_signals` JSON it consumes (written by mi_bhavisya from `bodha_msr_signals`) never contains a `family_id` key — `bodha_msr_signals` has NO `family_id` column at all. `family_id = str(sig.get('family_id') or sig.get('signal_id') or 'unknown')` therefore always falls through to the signal's own UUID, so every 'family' cell in the shrinkage computation is actually n=1 (a single signal instance), never the intended pooled evidence-family (fam_graha_natal, fam_yoga, etc).
- **Evidence:** mi_bhavisya.py builds driving = [{'signal_id': sid, 'strength': salience}] — no family_id ever included. `information_schema.columns` for bodha_msr_signals (79 columns) confirms no family_id column exists anywhere upstream. mi_gunanaka.py line 138: `family_id = str(sig.get("family_id") or sig.get("signal_id") or "unknown")`.
- **Fix:** mi_bhavisya (or mi_gunanaka itself) must resolve each driving signal's family via the same `_signal_family_key()` mapping already implemented in mi_adhilepa.py, and stamp the resolved `fam_*` id into the driving_signals payload before it reaches mi_gunanaka/mi_pariksha.
- **fix_type:** `code`
- **Status:** FIXED (commit `1e5cc686` — fix applied at the source, `mi_bhavisya`, which now stamps resolved `family_id` into the `driving_signals` payload)

### `mi_adhilepa`

**[MINOR] L1-Registry** — verification: `UNVERIFIED`

- **Finding:** asset_registry.depends_on for mi_adhilepa declares `ga_positions`, but the writer never reads ga_positions or any ga_* table at runtime — it only queries bodha_msr_signals, chart_facts, kala_convergence, phala_anchors, and mimamsa_multipliers. This is a stale/over-declared DAG edge (the inverse of the 'undeclared edge' scar pattern).
- **Evidence:** asset_registry row depends_on=['mi_gunanaka','bo_laksana','ka_sangam','ph_nimitta','ga_positions']; mi_adhilepa.py's only conn.cursor().execute() targets are bodha_msr_signals, chart_facts, kala_convergence, phala_anchors, mimamsa_multipliers.
- **Fix:** Remove the stale ga_positions edge from depends_on, or confirm what transitive dependency it was meant to stand in for and replace it with the correct one.
- **fix_type:** `registry`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

**[MINOR] L2-Data / L6-Coverage** — verification: `UNVERIFIED`

- **Finding:** The fact-overlay slice is structurally thin: it only pulls chart_facts rows `WHERE fact_category IN ('graha','yoga') LIMIT 200` with no ORDER BY, so dasha/divisional/ashtakavarga/transit fact categories never receive a mimamsa_fact_adjustment row at all, and even within graha/yoga the 200-row cap is an arbitrary, non-deterministic-priority slice (whatever Postgres returns first, not a chosen top-200). Confirmed empirically: mimamsa_fact_adjustment = 0 rows for Abhinandan while mimamsa_signal_adjustment (same writer, same run) = 66,816 rows.
- **Evidence:** mi_adhilepa.py: `SELECT fact_id, fact_category FROM chart_facts WHERE chart_id=%s AND fact_category IN ('graha','yoga') LIMIT 200` — no ORDER BY. Live query: mimamsa_fact_adjustment count=0 for chart_id=1c826d5a... despite mimamsa_signal_adjustment=66816 for the same chart/run.
- **Fix:** Widen fact_category coverage to the categories that actually have multiplier families available (dasha_period, divisional, ashtakavarga per mi_kula's family catalog), and if a row cap is intentional, ORDER BY a meaningful salience/priority column before LIMIT.
- **fix_type:** `code`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `mi_pariksha`

**[BLOCKER] L3-Code / L4-Astro** — verification: `CONFIRMED`

- **Finding:** Same missing-family_id defect propagates into mi_pariksha's attribution substep: `family_id = str(sig.get('family_id') or sig.get('signal_id') or 'unknown')` (line 454) means per-family attribution/discovery statistics are actually per-signal-UUID statistics, undermining the 'candidate emergent calibration law' discovery logic which is supposed to operate on recurring signal-family patterns.
- **Evidence:** mi_pariksha.py line 454, same root cause as the mi_gunanaka finding — driving_signals never carries family_id from mi_bhavisya.
- **Fix:** Same fix as mi_gunanaka finding: populate family_id at the driving_signals source (mi_bhavisya).
- **fix_type:** `code`
- **Status:** FIXED (commit `1e5cc686` — fix applied at the source, `mi_bhavisya`)

**[MAJOR] L3-Code / L5-DataEng** — verification: `CONFIRMED`

- **Finding:** The 'ablation' and 'tail_only' substeps are non-functional stubs that always report zero marginal-skill with a misleading status='pass'. `_substep_ablation`'s masking loop copies `composite_score` verbatim into `masked_scores` (no family is actually masked), so `masked_mean` == `baseline_mean` and `marginal_skill` is exactly 0.0 for every signal family on every chart. `_substep_tail_only` does the same (`full_mean = tail_mean` verbatim). Both are labeled 'structural_proxy_only'/'structural_proxy' in the JSONB detail field, but the `mimamsa_qa_eval.status` column still reads 'pass', indistinguishable from a genuinely-executed QA check.
- **Evidence:** mi_pariksha.py `_substep_ablation` (lines ~347-351): `for cr in cal_rows: score=...; masked_scores.append(score)` — literally the unmasked score, then `status='pass'` (line 361) is written regardless. `_substep_tail_only` line 699: `full_mean = tail_mean  # structural proxy at build time`, status='pass' (line 708).
- **Fix:** Either implement the real per-family masked rerun (rescoring composite without that family's contribution) and real tail-vs-full comparison, or change `status` to a distinct non-'pass' sentinel (e.g. 'structural_proxy') so downstream consumers of mimamsa_qa_eval cannot mistake it for a completed validation.
- **fix_type:** `code`
- **Status:** FIXED (commit `7c91265b`)

**[MAJOR] L3-Code / L4-Astro** — verification: `CONFIRMED`

- **Finding:** The negative-control QA substep (`_substep_neg_control`) is architecturally guaranteed to always pass and never actually exercises the negative-control battery seeded by mi_kula (neg_random_uniform, neg_shuffled_birth, neg_future_leak, neg_antiphase — citing Carlson 1985). `null_score` is a hardcoded literal (0.05 or 0.50 purely from the control's `expected_score` string) and the pass/fail check compares that same literal against its own definition, so `abs(null_score - target) <= tolerance` is a tautology that can never fail. No real random-window, shuffled-birth-data, or backdated-signal simulation is ever run against actual chart data.
- **Evidence:** mi_pariksha.py `_substep_neg_control`: `null_score = 0.05 if expected == 'near_zero' else 0.50`; `status = 'pass' if abs(null_score - (0 if expected=='near_zero' else 0.5)) <= tolerance else 'FAIL'` — the two operands of the comparison are always trivially close by construction (0 vs 0.05, or 0.5 vs 0.50), independent of chart_id or any real prediction/event data.
- **Fix:** Implement the actual simulations described in mi_kula's binding_spec_json (random_uniform_window, shuffle_chart_id, backdated_signal_post_event, invert_yoga_combination) against real calibration data, or mark status as 'not_implemented' rather than 'pass' until it is.
- **fix_type:** `native_judgment`
- **Status:** SKIPPED (native_judgment queued — see BA_AUDIT_FIX_PLAN §NATIVE_JUDGMENT_QUEUE)

**[MINOR] L6-Coverage** — verification: `UNVERIFIED`

- **Finding:** The discovery-mining substep hard-truncates to 20 discoveries per chart (`if len(rows) >= 20: break`) but does not sort candidates by `mean_credit` before applying that cutoff — Python dict iteration order over `sig_dim_credits` reflects attribution-row scan order, not strength order, so the 20 discoveries actually persisted are an arbitrary subset rather than the 20 strongest candidate 'emergent laws.'
- **Evidence:** mi_pariksha.py `_substep_discovery`: iterates `for (signal_id, dimension), credits in sig_dim_credits.items(): ... if len(rows) >= 20: break` with no prior `sorted(..., key=..., reverse=True)`.
- **Fix:** Sort candidates by mean_credit (descending) before truncating to the top-20.
- **fix_type:** `code`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `mi_sambandha`

**[ENHANCEMENT] L3-Code** — verification: `UNVERIFIED`

- **Finding:** Dead/unused local variable: `covered_domains = {r[3] for r in rows}` is computed then immediately abandoned — the very next line's comment self-corrects ('Actually let's seed all prior domains...') and recomputes the real check as `empirical_keys`. Harmless but confusing leftover from an earlier (buggy) version of the dedup logic.
- **Evidence:** mi_sambandha.py lines 118-121: `covered_domains = {r[3] for r in rows}  # channel_id position is 3 in row... actually domain pos` followed immediately by `empirical_keys = {(r[1], r[2], r[3], r[4]) for r in rows}` which is what's actually used at line 128.
- **Fix:** Delete the unused covered_domains line.
- **fix_type:** `code`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `mi_darshana`

- **CLEAN.** No findings raised against this asset in the BA_FULL_ASSET_AUDIT pass. (Exhaustiveness-gate entry — not independently re-audited beyond the standard DAG/registry/code sweep applied to all 91 assets.)

### `mi_vistara`

**[BLOCKER] L1-Registry / L5-DataEng** — verification: `CONFIRMED`

- **Finding:** mi_vistara has no entry in `EXPLICIT_CLEAR_OPS` and its `count_sql` (`SELECT count(*) FROM mimamsa_export_log`, no WHERE clause — it's a global-scope append-only ledger) will be auto-transformed by `deriveDeleteSqlFromCountSql()` into an UNSCOPED `DELETE FROM mimamsa_export_log` on any single-asset clear, wiping the entire export-integrity ledger for ALL charts at once. This is the exact same bug shape that was already caught and explicitly stop-gapped for mi_seva (`mi_seva: null` in EXPLICIT_CLEAR_OPS, with a code comment describing precisely this danger) but the identical fix was never applied to mi_vistara. Additionally, the typed-confirmation safety net in clear/execute/route.ts only triggers when the overall clear request's `scope` param is `'global'`; a `scope:'asset'` clear targeting a single global-scope asset (which only requires super_admin, per the forbidden-scope check) does not get that extra confirmation step.
- **Evidence:** asset_registry row: mi_vistara count_sql='SELECT count(*) FROM mimamsa_export_log', scope='global'. assetClearSpec.ts EXPLICIT_CLEAR_OPS has an explicit `mi_seva: null` entry with a comment warning about exactly this unscoped-DELETE derivation for an unscoped count_sql, but no analogous entry for mi_vistara. deriveDeleteSqlFromCountSql regex `^SELECT\s+count\(\*\)...FROM\b` matches mi_vistara's count_sql and yields `DELETE FROM mimamsa_export_log` verbatim (no WHERE).
- **Fix:** Add `mi_vistara: null` to EXPLICIT_CLEAR_OPS (mirroring the mi_seva stopgap) since it is an append-only log that build-time never populates and should not be auto-cleared at all.
- **fix_type:** `registry`
- **Status:** FIXED (commit `e306c475`)

### `mi_seva`

**[MINOR] L1-Registry** — verification: `UNVERIFIED`

- **Finding:** Registry/seed drift: the live `asset_registry.count_sql` for mi_seva is `SELECT count(*) FROM mimamsa_preferences` (unscoped) and `target_floor=0`, but `scripts/seed/asset_registry_seed.ts` declares `count_sql: null` and `target_floor: null` for the same asset_id — the seed file and the live DB row disagree on the exact same field (B.8 'registries must not disagree'). mi_seva.scope is also declared `per_chart` in the registry even though its actual count_sql/clear shape is unscoped/global.
- **Evidence:** Live query: mi_seva count_sql='SELECT count(*) FROM mimamsa_preferences', target_floor=0, scope='per_chart'. asset_registry_seed.ts line ~1788: `count_sql: null,` and `target_floor: null,` for the same target_table='mimamsa_preferences' asset.
- **Fix:** Reconcile the seed script with the live registry row (pick one canonical value), and either correct scope to reflect the actual unscoped shape or implement the chart-scoped count_sql the assetClearSpec.ts comment says is planned for 'a later wave.'
- **fix_type:** `registry`
- **Status:** OPEN (not yet fixed — see BA_AUDIT_FIX_PLAN)

### `mi_abhilekha`

**[MAJOR] L1-Registry / L5-DataEng** — verification: `CONFIRMED`

- **Finding:** mi_abhilekha's writer creates zero build-time rows by design — mimamsa_journal holds the native's actual answered Q&A history (serve-time, user-authored, irreplaceable data). It has no EXPLICIT_CLEAR_OPS entry, so its chart-scoped count_sql auto-derives a correctly chart-scoped `DELETE FROM mimamsa_journal WHERE chart_id=$1`. This means every routine per-chart Mīmāṃsā layer clear/rebuild silently destroys the native's real journal answers for that chart, with no re-population mechanism at build time (matches previously-logged 'LOW: mi_abhilekha destructively clears serve-time journal data' — recommend re-evaluating severity given the data is genuinely irreplaceable, not a rebuildable artifact).
- **Evidence:** asset_registry: mi_abhilekha count_sql='SELECT count(*) FROM mimamsa_journal WHERE chart_id=$1', scope='per_chart'. assetClearSpec.ts EXPLICIT_CLEAR_OPS has no mi_abhilekha entry, so the default derive path applies verbatim.
- **Fix:** Exclude mimamsa_journal from the auto-derived per-chart clear (EXPLICIT_CLEAR_OPS: mi_abhilekha -> null), since the writer itself never repopulates it — clearing it on rebuild only causes data loss with no compensating rebuild.
- **fix_type:** `native_judgment`
- **Status:** SKIPPED (native_judgment queued — see BA_AUDIT_FIX_PLAN §NATIVE_JUDGMENT_QUEUE)


