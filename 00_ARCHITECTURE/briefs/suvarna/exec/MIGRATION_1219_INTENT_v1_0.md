---
artifact: MIGRATION_1219_INTENT
version: "1.2"
status: MIGRATION FILE WRITTEN (1219) on PR #2851; applied via deploy pipeline after merge, verified by production structure. 1221 (a29) is split out to its own HELD PR (see section 4).
produced_by: exec-suvarna
produced_on: 2026-10-02
for: PR #2851 (ga_structural argala) and design note DESIGN_ARGALA_L1_GRAHA_ROWS_v1_0.md (#2850)
files:
  - platform/migrations/1219_nirmana_l1_ga_structural_argala_graha_natal_ownership_and_digest.sql
tests: platform/python-sidecar/tests/test_argala_migration_1219_sql.py executes the real migration file against a disposable local Postgres
changelog:
  - "1.2 (2026-10-02): SS decisions on the migration-guard review. (a) 1221 (the a29 integrity conjunct) leaves PR #2851 for its own HELD draft PR, because the runner applies every merged file at the next deploy before that deploy's images roll, so a 1221 merged with the writer would apply before the writer image: this document keeps only 1219 (renamed from MIGRATION_1219_1221_INTENT; the 1221 explanation moved to MIGRATION_1221_A29_INTENT_v1_0.md on that PR). (b) ga_strength's retained 'ashtakavarga_%' clause now excludes ashtakavarga_anubindu (owned by ga_structural), closing a latent double count; 0 rows today so no count moves. (c) 1219 sets SET LOCAL lock_timeout = '5s' (1218 pattern)."
  - "1.1 (2026-10-02): owner authorized migration files in the 1200-1299 range. The fenced SQL blocks of v1.0 became the real migration files (1219 replaces the stale draft of commit 9c038a663); the blocks are removed from this document so no SQL copy can drift from the files; the test reads the files. Header comments rewritten (no draft/hold wording; normal runner; verify by production structure per CLAUDE.md N.4, Trap 103; ordering rule). Every guard (md5 guards, ownership guard, idempotence) is byte-for-byte the v1.0 text. Addendum: migration-guard review folded in (freshness note and more post-apply queries in the header)."
  - "1.0 (2026-10-02): first version; replaces the pending edits to the 1219 draft and the 1221 split, held for the owner."
---

# Migration 1219: explanation

## 1. Status

The owner authorized migration files in the 1200-1299 range (never editing one that was applied; 1219 was never merged or applied; a read-only check of `_migrations_applied` shows no 1219 row). Numbers re-checked against `origin/main` and every open PR head immediately before writing: 1219 (this PR's own stale draft only) was free; 1220 and 1222 belong to other PRs. The file `platform/migrations/1219_nirmana_l1_ga_structural_argala_graha_natal_ownership_and_digest.sql` replaces the stale draft of commit `9c038a663`. It is applied by the normal runner after merge and verified by production structure afterwards (CLAUDE.md N.4, Trap 103: never trust the deploy log). Nothing is applied by hand.

## 2. What 1219 changes against the pushed 1219 draft

1. The integrity conjunct (a29) leaves 1219: it is migration 1221, a separate HELD PR (section 4).
2. **No floor is touched** (`target_floor` is in the column list of the live trigger `nirmana_registry_receipt_invalidation`; floors are re-declared from achieved counts after S-L1 in one registry migration).
3. `ga_strength.count_sql` is narrowed so that no row is counted by two assets: it drops the 420 `bhava_bala_*` rows, the 35 `vimsopaka_bala_per_graha` rows, the 35 `graha_saptavargaja_bala_component` rows and (v1.2) any `ashtakavarga_anubindu` row, which `ga_structural` emits and owns. The retained `ashtakavarga_%` clause becomes `(LIKE 'ashtakavarga_%' AND <> 'ashtakavarga_anubindu')`; every other `ashtakavarga_*` category stays `ga_strength`'s. Guard: md5 of the live text.
4. `ga_condition.count_sql`: only the stale `graha_yuddha` clause is removed (`ga_structural` emits and owns `graha_yuddha`; the clause double-counts it on charts that have it). The earlier draft cut it to the composite table (45); the independent review points out that this would hide the 2,925 `chart_facts` rows it owns (CLAUDE.md N.4, cockpit truth). **For SS:** Q-L1-04's text says "`count_sql` on the primary table"; I followed the review and left the multi-table count shape to I-30 (no multi-formula count declaration is added here). One line to change if SS prefers the ruling's text.
5. Ownership: the five panchanga categories (216 rows) are **dropped from `ga_structural`** (it never emits them) and owned by `ga_panchanga`; the three categories a writer emits with no ownership row (`ashtakavarga_bindu_contributor`; `graha_degree_flags`, `nakshatra_exchange`) and the three inert `esoteric_point_trisphuta` / `chatushphuta` / `panchasphuta` are added. Derivation: `derive_q04_ownership.py` (predicate and live data) and `derive_writer_categories.py` (writer source), outside the repo in `/Users/Dev/suvarna-evidence/TrackI/argala_l1/`. After 1219 every live category (all charts) and every category a `ga_*` chart_facts writer emits has an owner (the 62 other writer-source hits are reads, GA3-overlap lists and `chart_divisionals` categories).
6. `SET LOCAL lock_timeout = '5s'` is the first statement (1218 pattern): a blocked migrate job fails fast instead of hanging a shared deploy.

The live trigger `l1_data_plane_mutation_guard` refuses an L1 write to a `chart_facts` category with no ownership row for that asset, so 1219 is a hard prerequisite of the S-L1 `ga_structural` rebuild.

## 3. Canonical chart, chart_facts-based counts, before to after 1219

  asset                 before    after    change
  ga_structural        102,037  106,707    +4,670  (+4,816 the 12 unowned categories, +70 vimsopaka_bala_per_graha
                                                     and graha_saptavargaja_bala_component, -216 the five panchanga
                                                     categories; equals its 106,707 build record)
  ga_strength           14,141   13,651      -490  (-420 bhava_bala_*, -70 vimsopaka / saptavarga component; the
                                                     anubindu exclusion moves nothing: 0 rows)
  ga_condition           2,970    2,970         0  (only the graha_yuddha clause leaves its predicate: 0 canonical rows)
  ga_panchanga             437      437         0  (the five categories were already inside its predicate)
  ga_nakshatra 2,847; ga_positions 1,205; ga_sade_sati 6,287; ga_sensitive 8,775; ga_sensitive_degree 335;
  ga_ayurdaya 130: unchanged.
The narrowed ga_strength predicate (including the anubindu exclusion) was run as SQL against the live canonical chart (read-only): 13,651.

Before 1219 the double claims on the canonical chart are the 420 `bhava_bala_*` rows (`ga_structural` by ownership, `ga_strength` by predicate) and the 216 panchanga rows (`ga_structural` by ownership, `ga_panchanga` by predicate): 636 rows. After it, none (`count_claims_before_after.py`; the test `test_no_category_is_claimed_by_two_assets_after_1219` pins the same property by category, including `ashtakavarga_anubindu`). `count_sql` is not in the trigger's column list, so no freshness is staled by it; it is in the Nirmana registry-contract fingerprint, so the frozen manifests of `ga_strength` and `ga_condition` go to `evidence_refresh_required` (design note, section 5). The digest-spec swap does change the receipt's `output_digest_spec_sha256`, so the stored `ga_structural` receipt reads stale at the next reconciliation; S-L1 rebuilds it anyway.

## 4. Application order and the split of 1221

- 1219 applies before the S-L1 `ga_structural` rebuild launches (hard prerequisite) and **may apply independently of the writer deploy**.
- 1221 (the a29 integrity conjunct) is a **separate HELD PR** (`suvarna/land/TI-mig-1221-a29-001`; explanation in its own `MIGRATION_1221_A29_INTENT_v1_0.md`). The routine runner applies every merged file at the next deploy and every deploy job waits on the migrate job, so a 1221 merged with the writer change would apply before the new writer image rolls. 1221 merges only in the S-L1 window, after this PR's writer image is deployed and verified, immediately before the `ga_structural` launch.
- After 1219 applies, verify by production structure with the post-apply queries in the file header (never the deploy log).

## 5. The SQL

There is no SQL copy in this document: the file is the migration. Its header carries the post-apply verification queries and the ordering rule. `test_argala_migration_1219_sql.py` runs it against a disposable local Postgres (including the refusal and sabotage cases).
