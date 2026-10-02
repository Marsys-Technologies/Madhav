---
artifact: MIGRATION_1219_1221_INTENT
version: "1.1"
status: MIGRATION FILES WRITTEN (1219, 1221) on PR #2851; applied via deploy pipeline after merge, verified by production structure
produced_by: exec-suvarna
produced_on: 2026-10-02
for: PR #2851 (ga_structural argala) and design note DESIGN_ARGALA_L1_GRAHA_ROWS_v1_0.md (#2850)
files:
  - platform/migrations/1219_nirmana_l1_ga_structural_argala_graha_natal_ownership_and_digest.sql
  - platform/migrations/1221_nirmana_l1_ga_structural_a29_integrity_conjunct.sql
tests: platform/python-sidecar/tests/test_argala_migration_intent_sql.py executes both real migration files against a disposable local Postgres
changelog:
  - "1.1 (2026-10-02): owner authorized migration files in the 1200-1299 range. The two fenced SQL blocks of v1.0 became the real migration files (1219 replaces the stale draft of commit 9c038a663; 1221 created as 1221_nirmana_l1_ga_structural_a29_integrity_conjunct.sql); the blocks are removed from this document so no SQL copy can drift from the files; the test now reads the files. Header comments rewritten: no more draft/hold wording; normal runner, verify by production structure (CLAUDE.md N.4, Trap 103); the ordering rule is stated in both headers (1219 hard prerequisite of the S-L1 ga_structural rebuild, may apply independently of the writer deploy; 1221 a named S-L1 step immediately before the ga_structural launch and never before the writer deploy). Every guard (md5 guards, ownership guard, idempotence) is byte-for-byte the v1.0 text."
  - "1.1 addendum (2026-10-02): migration-guard review folded in. Header-comment-only additions (no SQL change): 1219 gains a freshness note (the digest-spec swap makes the stored ga_structural receipt stale at the next reconciliation) and three more post-apply queries (panchanga five owned by ga_panchanga and no longer by ga_structural; ga_condition count_sql); 1221 gains the runner consequence (merge-timing rule) and a note to evaluate the full integrity text read-only. Open for SS, not changed here: (a) 1221 cannot stay in the same merge as the writer; (b) ashtakavarga_anubindu is owned by ga_structural in 1219 but still matched by ga_strength's retained LIKE 'ashtakavarga_%' clause, a latent double count that appears when S-L1 emits those rows (0 rows on every chart today); (c) no lock_timeout in either file (1218 precedent sets SET LOCAL lock_timeout)."
  - "1.0 (2026-10-02): first version; replaces the pending edits to the 1219 draft and the 1221 split, held for the owner."
---

# Migration 1219 / 1221: explanation

## 1. Status

The owner authorized migration files in the 1200-1299 range (never editing one that was applied; neither 1219 nor 1221 was ever merged or applied). Numbers re-checked against `origin/main` and every open PR head immediately before writing: 1219 (this PR's own stale draft only) and 1221 were free; 1220 belongs to the Pravaha PR #2884 and 1222 to #2858. Block A is now the file `platform/migrations/1219_nirmana_l1_ga_structural_argala_graha_natal_ownership_and_digest.sql` (it replaces the stale draft of commit `9c038a663`); block B is the integrity conjunct, split out as SS decided, now the file `platform/migrations/1221_nirmana_l1_ga_structural_a29_integrity_conjunct.sql`. Both are applied by the normal runner after merge and verified by production structure afterwards (CLAUDE.md N.4, Trap 103: never trust the deploy log). Nothing is applied by hand. Read section 4 for what the runner cannot enforce about 1221.

## 2. What block A (1219) changes against the pushed 1219 draft

1. The integrity conjunct (a29) leaves 1219 (it is block B).
2. **No floor is touched** (`target_floor` is in the column list of the live trigger `nirmana_registry_receipt_invalidation`; floors are re-declared from achieved counts after S-L1 in one registry migration).
3. `ga_strength.count_sql` is narrowed so that no row is counted by two assets: it drops the 420 `bhava_bala_*` rows, the 35 `vimsopaka_bala_per_graha` rows and the 35 `graha_saptavargaja_bala_component` rows, which `ga_structural` emits and owns. Guard: md5 of the live text.
4. `ga_condition.count_sql`: only the stale `graha_yuddha` clause is removed (`ga_structural` emits and owns `graha_yuddha`; the clause double-counts it on charts that have it). The earlier draft cut it to the composite table (45); the independent review points out that this would hide the 2,925 `chart_facts` rows it owns (CLAUDE.md N.4, cockpit truth). **For SS:** Q-L1-04's text says "`count_sql` on the primary table"; I followed the review and left the multi-table count shape to I-30 (no multi-formula count declaration is added here). One line to change if SS prefers the ruling's text.
5. Ownership: the five panchanga categories (216 rows) are **dropped from `ga_structural`** (it never emits them) and owned by `ga_panchanga`; the three categories a writer emits with no ownership row (`ashtakavarga_bindu_contributor`; `graha_degree_flags`, `nakshatra_exchange`) and the three inert `esoteric_point_trisphuta` / `chatushphuta` / `panchasphuta` are added. Derivation: `derive_q04_ownership.py` (predicate and live data) and `derive_writer_categories.py` (writer source), outside the repo in `/Users/Dev/suvarna-evidence/TrackI/argala_l1/`. After block A every live category (all charts) and every category a `ga_*` chart_facts writer emits has an owner (the 62 other writer-source hits are reads, GA3-overlap lists and `chart_divisionals` categories).

The live trigger `l1_data_plane_mutation_guard` refuses an L1 write to a `chart_facts` category with no ownership row for that asset, so block A is a hard prerequisite of the S-L1 `ga_structural` rebuild.

## 3. Canonical chart, chart_facts-based counts, before to after block A

  asset                 before    after    change
  ga_structural        102,037  106,707    +4,670  (+4,816 the 12 unowned categories, +70 vimsopaka_bala_per_graha
                                                     and graha_saptavargaja_bala_component, -216 the five panchanga
                                                     categories; equals its 106,707 build record)
  ga_strength           14,141   13,651      -490  (-420 bhava_bala_*, -70 vimsopaka / saptavarga component)
  ga_condition           2,970    2,970         0  (only the graha_yuddha clause leaves its predicate: 0 canonical rows)
  ga_panchanga             437      437         0  (the five categories were already inside its predicate)
  ga_nakshatra 2,847; ga_positions 1,205; ga_sade_sati 6,287; ga_sensitive 8,775; ga_sensitive_degree 335;
  ga_ayurdaya 130: unchanged.
The narrowed ga_strength predicate was also run as SQL against the live canonical chart (read-only): 13,651.

Before block A the double claims on the canonical chart are the 420 `bhava_bala_*` rows (`ga_structural` by ownership, `ga_strength` by predicate) and the 216 panchanga rows (`ga_structural` by ownership, `ga_panchanga` by predicate): 636 rows. After it, none (`count_claims_before_after.py`). `count_sql` is not in the trigger's column list, so no freshness is staled; it is in the Nirmana registry-contract fingerprint, so the frozen manifests of `ga_strength` and `ga_condition` go to `evidence_refresh_required` (design note, section 5).

## 4. Application order

- Block A (1219) applies before the S-L1 `ga_structural` rebuild launches (hard prerequisite) and **may apply independently of the writer deploy**.
- Block B (1221, (a29), `integrity_check_sql`) applies as a **named step of S-L1, immediately before the `ga_structural` launch, and never before the `ga_structural` writer deploy**: (a29) reads red on live canonical data until S-L1 writes the NULL cells; `UPDATE OF integrity_check_sql` stales `ga_structural`'s freshness (trigger 596); and after (a29) a `ga_structural` rebuild by the OLD writer image fails its post-write integrity check.
- **Runner caveat for 1221 (migration-guard review, HIGH).** `platform/scripts/migrate.ts` applies every unapplied file in `platform/migrations` on the next deploy, and every deploy job `needs` the migrate job, so a merged 1221 is applied before that deploy's images roll. The runner cannot enforce "never before the writer deploy": if 1221 merges in the same deploy as the `ga_structural` writer change it applies before the new writer image exists. The rule is therefore a merge-timing rule: merge 1221 only at the S-L1 step, in a deploy after the writer deploy is confirmed (repo precedent for a held migration: 1211, kept unmerged on a branch). Merging PR #2851 with 1221 in it breaks the rule; this is a decision for SS (split 1221 into its own later PR, or hold it).
- After each applies, verify by production structure with the post-apply queries in the file header (never the deploy log).

## 5. The SQL

There is no SQL copy in this document. Block A is `platform/migrations/1219_nirmana_l1_ga_structural_argala_graha_natal_ownership_and_digest.sql` and block B is `platform/migrations/1221_nirmana_l1_ga_structural_a29_integrity_conjunct.sql`; each file's header carries the post-apply verification queries and the ordering rule. `test_argala_migration_intent_sql.py` runs both files against a disposable local Postgres (including the refusal and sabotage cases and the six (a29) mutants).
