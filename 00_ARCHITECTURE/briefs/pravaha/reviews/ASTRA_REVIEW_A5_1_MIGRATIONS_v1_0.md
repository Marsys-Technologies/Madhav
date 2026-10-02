---
artifact: ASTRA_REVIEW_A5_1_MIGRATIONS
version: "1.0"
reviewer: "Codex gpt-6-astra"
date: "2026-09-30"
verdict: REJECT
reviewed_commit: b7b729378
authority: "Review only; authorizes nothing."
---

**Verdict: REJECT.** The migrations contain substantial structural gaps against the frozen contracts. Most seriously, they conflate boundary events with transit contacts, permit unversioned and dangling references, incompletely enforce tagged states, and break atomicity between migration DDL and the applied-migration ledger.

The review covers `b7b729378366036e5b6a6b2cffa981805039110d`, using `git diff origin/main...HEAD`. The diff contains exactly ten added files: five migrations and five preflights. No files were written and no database was contacted.

For citations below:

- **S** = [GOCHARA_DESIGN_SPECS_v1_4.md](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_DESIGN_SPECS_v1_4.md), FROZEN.
- **O** = [GOCHARA_TEST_ORACLES_v1_4.json](/Users/Dev/madhav-l3/pravaha/00_ARCHITECTURE/briefs/pravaha/design/GOCHARA_TEST_ORACLES_v1_4.json).
- **M1153–M1157** identify the migration files linked in the table; **PF1153–PF1157** identify their corresponding `preflight_…sql` files under `platform/python-sidecar/scripts/kala_gochara_cutover/`.

**Per-migration contract assessment**

| Migration / table | Spec clause → implemented? | Evidence and discrepancies |
|---|---|---|
| [1153 — `ka_gochara_sky_convention`](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765/platform/migrations/1153_gochara_sky_event_substrate.sql:86) | §6.1 substrate dimensions and pinned ordinal domain; §7.2 method version → **largely implemented** | `convention_id` PK; required generation, ayanāṃśa, node convention, grid, method version and domain bounds; ordered-domain CHECK; immutable rows. M1153:86–125 matches S:610–633, 702–703. Hash derivation remains a writer obligation. |
| 1153 — `ka_gochara_physical_object` | §6.1 physical identity → **partial** | UUID PK and `UNIQUE(body, relation_kind, canonical_target, convention_id)` correctly represent the prescribed tuple; convention FK exists. M1153:129–169. Missing body-domain validation and consistency between an event’s duplicated body/convention and its referenced object. See amendments 1 and 4. |
| 1153 — `ka_gochara_sky_event` | §6.1 boundary-event schema, contact identity and publication lifecycle; §7 precision → **not conformant as the contact target** | Five boundary-event kinds, ordinal uniqueness, solver enum and station refinement CHECK are present. But this table is also made the universal contact relation despite lacking contact kinds and interval storage. `coverage.truncated` can be absent; exact events can lack longitude/uncertainties; the mutation guard permits changes to published precision and lineage. M1153:173–274 versus S:611–646, 662–675, 687–703. |
| [1154 — `ka_gochara_rule_path`](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765/platform/migrations/1154_gochara_rule_path_registry.sql:106) | §2.1 versioned registry → **partial** | Composite PK, provenance/operator enums, frame presence and insert-only behavior are present. `prerequisites` and `soft_factors` validate JSON reference **shape**, not existence. `frame_arg` accepts arbitrary text; selector/set JSON has no typed validation; `score_rule` is nullable; the ruling CHECK is stronger than the frozen wording. M1154:83–162 versus S:70–71, 110, 152–181. |
| 1154 — `ka_gochara_predicate` | §2.1 predicate → **partial** | Composite PK, all seven operators and `unknown_is_false = false` are correct. `operands` accepts arbitrary JSON, including prose strings, despite the named-selector contract. The registry need not contain a mutable evaluation-result column, but the associated evaluation/admission result lacks a declared persistence representation elsewhere. M1154:166–201 versus S:160–163 and 103. |
| 1154 — `ka_gochara_factor` | §2.1 numeric function, calibration and codomain → **partial** | Composite PK, selector, direction, function, bounds, units, calibration status, null state and effect fields exist. The bounds CHECK correctly restricts stored ranges to `[0,1]`. However, there is no declared machine-readable representation for category mappings or function parameters. M1154:205–255 versus S:165–181. |
| [1155 — `ka_gochara_relationship_record`](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765/platform/migrations/1155_gochara_relationship_record.sql:90) | §1 typed record, lineage and scoping → **not conformant** | All listed field names have storage equivalents. Generation, frame, enums and fixture-only empty lineage are partly enforced. Missing/wrong constraints include nullable path/version references, wrong contact target, transit precision nullability, incomplete support-state validation, unbound coverage scope, untyped fact-array elements, nullable valence and insufficient frame-argument validation. M1155:90–240 versus S:88–134. |
| [1156 — `ka_gochara_eval_window`](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765/platform/migrations/1156_gochara_eval_window.sql:63) | §2.1 evaluated window and score algebra; §3 valence → **not conformant** | Fields exist, but `record_ids` is a nullable UUID array without the specified FKs; path/version references are nullable; coverage is not scope-bound; score has no `[0,1]` CHECK; valence permits SQL NULL. Empty intervals and a P4 peak outside its overlap are also accepted. M1156:63–110 versus S:167–185, 209–213, 321–323, 451–475. |
| [1157 — `ka_gochara_av_polarity_declaration`](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765/platform/migrations/1157_gochara_av_polarity_declaration.sql:58) | §8.1 declaration → **structurally implemented** | All five specified fields exist and are NOT NULL; `convention` is the PK. No convention FK is prescribed by S:717–720, so its absence is not independently a defect. The declaration-to-evaluation binding and write-time citation rejection remain unimplemented obligations under S:741–742 and O:330–335. An empty table does not establish that gate. |

Both `event_class` CHECK lists match the protocol’s **27 classes exactly**, with no missing or extra members.

Representation additions are mostly justified: `frame_kind/frame_arg` implements enum-plus-argument; `range_lower/range_upper` implements the closed interval; `fixture` is required by S:107; physical-object and occurrence fields support §6 identity; `precision_regime` comes from §7. `created_at` on all nine tables is harmless operational metadata. A separate `root_id` column is unnecessary because S:194–197 defines it from existing columns.

**Production safety**

The migration bodies perform **no business-data INSERT, UPDATE or DELETE against existing tables**. On a clean, correctly privileged target, they create new tables, indexes, functions, triggers and comments. This is additive at the business-data level.

It is not lock-free. The FKs in 1155 and 1156 acquire `SHARE ROW EXCLUSIVE` locks on existing referenced tables, including `charts` and `kala_gochara_publication`. These are DDL locks that can block concurrent writes. Each migration sets a five-second lock wait and a 120-second statement timeout; those settings do not establish a five-second maximum lock-holding duration. [PostgreSQL CREATE TABLE documentation](https://www.postgresql.org/docs/current/sql-createtable.html).

The more serious execution defect is transaction ownership. Every new migration contains its own `BEGIN` and terminal `COMMIT`. The [runner](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765/platform/scripts/migrate.ts:791) does:

```text
BEGIN
execute migration SQL — including its COMMIT
INSERT applied filename/hash into ledger
COMMIT
```

PostgreSQL does not nest these transactions: the inner `BEGIN` warns, and the migration’s `COMMIT` ends the active transaction. Consequently, a failed ledger insert or interrupted connection can leave committed DDL without its tracking row; the catch-path `ROLLBACK` cannot undo that DDL. The migrations’ “one transaction” comments therefore overstate the guarantee supplied by this runner. [PostgreSQL BEGIN documentation](https://www.postgresql.org/docs/current/sql-begin.html).

The [deployment workflow](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-2765/.github/workflows/deploy.yml:1186) invokes the general runner against production. Neither that workflow nor the runner invokes these five preflights.

Numbering verification passed locally: **zero guard errors**, highest number `1157`, next number `1158`; the guard reports 86 existing warnings. All five additions are in `platform/migrations/`, and `git diff --check` passed. This verifies the checkout’s combined migration directories, not live reservations or production’s applied ledger.

Re-run behavior is stated in every header, but needs correction:

| Migration | Actual re-run behavior |
|---|---|
| 1153 | Tables/indexes are skipped if their names exist; functions are replaced; triggers are dropped/recreated; comments are rewritten. This is not a literal no-op or a schema-equivalence check. |
| 1154 | Same, including replacement of the helper used by CHECK constraints. Existing table definitions are not repaired or compared. |
| 1155 | Existing table/index names are skipped and the comment is rewritten. Missing constraints on an existing table remain missing. |
| 1156 | Same as 1155. |
| 1157 | Existing table is skipped; function and trigger are recreated; comment is rewritten. |

For a **properly tracked** migration, the runner checks the stored hash and skips unchanged content; changed applied content fails its hash check. For an **untracked pre-existing object**, `IF NOT EXISTS` provides no assurance that its definition matches this migration. [PostgreSQL CREATE TABLE documentation](https://www.postgresql.org/docs/current/sql-createtable.html).

The preflights are useful first-application queries, but are incomplete:

| Preflight | Correct checks | Missing or incorrect checks |
|---|---|---|
| PF1153 | New relation/index/function names and applied-number lookup | No effective-schema/privilege verification; trigger lookup is global rather than scoped to the intended table/schema; function collision checks ignore signatures. |
| PF1154 | Registry/helper name collisions and ledger lookup | Same scope/signature problems; no subsequent schema-conformance assertions. |
| PF1155 | Parent relation existence and expected column types | Despite the comments, it does **not** verify parent PK/UNIQUE definitions. Helper lookup checks only `proname`, not `(jsonb,text) → boolean`. Missing-column output selects the NULL side of the join, losing the expected object’s identity. |
| PF1156 | Parent relation existence and column types | Does not verify referenced keys. It also omits the relationship-record parent because the required record FKs were omitted from the migration. |
| PF1157 | New names and ledger lookup | Same trigger/function scoping problems; no privilege/schema verification. |

All five use `LIKE '115N_%'`, where `_` is a wildcard rather than a literal underscore. Index collision queries inspect `pg_indexes`, although index names share a namespace with other relation kinds. The scripts return failure rows but do not themselves turn those rows into an execution failure. A caller must reject both query errors and nonempty results.

PF1155/PF1156 also require their newly created parents to exist: they must run **after prerequisite migrations**, not as one undifferentiated preflight batch against the original database.

**Ranked merge-blocking amendments**

1. **P1 — Separate boundary events from the contact ledger and define their lifecycle.**

   M1155:105 points every transit record at `ka_gochara_sky_event.event_id`. That table permits only `sign_ingress`, `nakshatra_ingress`, `kakshya_crossing`, `station` and `eclipse_instant`—M1153:181–183. It has no contact relation field or `t_in/t_out`/range representation.

   S:91, 96 and 621–640 require transit-contact identities; S:664–668 requires truncated spans and residence intervals. O-RX-1 explicitly persists conjunction crossings at `point:198.52`—O:64–69. Those are not one of the five boundary-event kinds. A writer must currently mislabel them or use a different table that the FK cannot reference.

   The inherited `kala_gochara_contacts` does contain intervals, but its key is `(chart_id, generation, contact_id TEXT)` and there is no mapping to the new UUID FK. Moreover, the new contact target has neither chart/generation ownership nor a lifecycle compatible with per-chart delete-then-insert. Resolve that against S:803–805 and **CLAUDE.md:276–279**, while preserving published physical identities. Moon-on-demand storage must also respect O:281–285.

2. **P1 — Restore atomic DDL-and-ledger application.**

   Remove transaction ownership from these unapplied migration bodies, or supply an explicitly reviewed execution mechanism that preserves a single transaction around DDL **and** ledger insertion. The current runner passes file SQL through unchanged—`migrate.ts:532–534, 791–801`.

   Validation must include a forced failure between DDL execution and ledger recording. A successful normal apply cannot establish this property. This is directly relevant to **CLAUDE.md:288**, which forbids relying on a superficially successful migration run.

3. **P1 — Make version-bound references and window membership real integrity constraints.**

   `path_id` and `rule_version` are nullable in **both** M1155:162–163 and M1156:78–79. Their FKs use default `MATCH SIMPLE`; therefore `('P4', NULL)` bypasses reference validation. This contradicts S:156–158. Use mandatory complete references for these path-produced objects; any genuinely optional reference needs an explicitly contracted state and, at minimum, all-or-none matching. [PostgreSQL foreign-key null semantics](https://www.postgresql.org/docs/current/ddl-constraints.html).

   `ka_gochara_composite_refs_ok` only checks JSON shape. References to nonexistent predicate/factor versions pass. Implement ordered, version-bound references with actual referential enforcement for:

   - `rule_path.prerequisites`;
   - `rule_path.soft_factors`;
   - `relationship_record.prerequisites`;
   - `eval_window.record_ids`.

   The last is explicitly `[FK]` in S:185. PostgreSQL’s lack of array-element FKs is a reason to normalize membership or provide equivalent enforced integrity—not to replace the FK contract with a comment. Window membership must also prevent cross-chart/generation references and survive the prescribed rebuild ordering.

4. **P1 — Resolve coverage identity and enforce scope consistency.**

   M1155:172 and M1156:98 reference a **publication** manifest, selected because it has a UUID. S:104 requires a resolvable **coverage** manifest. The inherited publication table contains a horizon and counts; coverage partitions are a different relation, keyed by chart, generation and partition.

   Even accepting publication as an approved aggregate coverage handle, the current FKs allow a generation `5.0` row to reference another chart’s or generation’s manifest. They do not guarantee any relevant coverage partition exists. Define the coverage handle/bridge and bind it to the consuming chart, generation and applicable partition scope.

   Likewise, M1153 permits an event’s `body` and `convention_id` to disagree with its referenced physical object. M1155 permits its transit `object_id` and `agent` to disagree with its referenced contact. Add composite consistency constraints or an equivalent enforced representation. These are lineage contradictions, not alternative interpretations of S:88–104 and 615–629.

5. **P1 — Close NULL loopholes and persist the distinct qualification states.**

   M1155:218–220 accepts `temporal_support = '{}'`: the missing state produces SQL NULL, which satisfies a CHECK. It also accepts `{"state":"computed","intervals":[]}` and `computed_empty` with nonempty intervals. Require the tag and typed `grain/intervals` payload, with state-dependent cardinality matching S:103. [PostgreSQL CHECK semantics](https://www.postgresql.org/docs/current/ddl-constraints.html).

   M1153:214–218 similarly accepts an exact event with `coverage = '{}'`. Require an explicit boolean `truncated` key.

   The transit branch of M1155:231–237 requires `contact_id`, but omits **`precision IS NOT NULL`**. Add the conditional requirement and validate its solver/uncertainty payload—S:91, 105. For reported exact sky events, nullable `longitude`, `delta_lambda`, `delta_t` and `precision_regime` leave §7’s precision contract incomplete—M1153:190–202 versus S:687–697.

   Both relationship/window valence columns permit SQL NULL despite the declared four-state vocabulary, including explicit `unqualified`—S:113, 451–475. Establish the declared null-state discipline.

   Finally, S:103 requires unknown-prerequisite admission to be **recorded as unqualified**. There is no declared admission-result field or typed result object. M1155:53 instead associates unknown admission with outcome valence. Those are different concepts. Define the persistence representation for admission, prerequisite results and the frame arithmetic required by S:126; do not make A5.3 invent extra JSON keys or repurpose valence.

6. **P1 — Complete publication immutability and resolve same-tuple corrections.**

   M1153:249–266 protects identity columns, `t_exact` and longitude, but permits changes to existing non-NULL `solver_method`, uncertainties, `precision_regime`, coverage metadata and `supersedes_event_id`. S:643–646 limits in-place changes to enrichment of NULL/truncated/unresolved fields; S:702–703 requires a new convention for method changes.

   A same-tuple correction also has no consistent representation: changing only an already published exact time requires a new ID, but `(physical_object_id, occurrence_ordinal)` remains unique and the prescribed hash inputs remain unchanged. Deleting or renumbering the predecessor is prohibited.

   This exposes a **contract decision that must be settled**, not guessed by dropping uniqueness or substituting random IDs. Define correction identity, retirement/supersession and permitted enrichment precisely. Prevent self-supersession and mutable supersession history.

7. **P1 — Specify numeric mappings and enforce the resulting score contract.**

   S:165–181 requires the numerical mapping to reside on the versioned factor row. `function TEXT`, two output bounds and `effect TEXT` do not specify step thresholds, category values, linear coefficients or ratio conventions. `operand_selector` has no declared mapping payload either. Define a machine-readable function representation and validate it before the insert-only registry is populated.

   `rule_path.score_rule` is nullable without a declared scored-row exception. Complete that requirement.

   Add a conditional `[0,1]` CHECK to `eval_window.score`. S:167–170, 187–188 and 209–213 establish that both product and cross-path maximum preserve this range. Evidence sums being unbounded does not justify leaving **score** unbounded, as M1156:39–43 suggests. Preserve NULL for explicitly unqualified scores.

   Also reject empty evaluated intervals and enforce P4’s peak being within its overlap when computed—S:321–323. Numeric evidence fields need their nonnegative contribution semantics preserved; they must not receive the score’s upper bound of one.

8. **P1 — Make first-apply checks and schema verification an effective gate.**

   Correct the preflight shortcomings listed above and establish a fail-closed execution sequence or reviewed pre-merge receipts. A comment saying “must return zero rows” is not evidence that the automatic production path observes that condition.

   The migration must not silently adopt a same-named table with missing constraints, or replace an unrelated same-signature function. Pin the intended schema and verify the actual create/reference privileges.

   Supply post-application definition checks for columns, nullability, keys, CHECKs, FKs and triggers. Fresh apply, repeat execution and deliberately drifted-object cases must have distinct, documented outcomes. This is the verification required by **CLAUDE.md:288**.

9. **P2 — Finish typed selector, frame, provenance and lineage validation.**

   `frame_arg` in M1154:111/134 and M1155:130/212 is merely present or absent. It accepts invalid graha arguments and invalid house numbers. Implement the typed argument domains from S:70–71, 94. The relative-person frame invariant is also unguarded—S:126–128.

   The JSON fields `agent_set`, `relation_set`, `object_selector`, predicate `operands` and factor `operand_selector` accept scalar/null JSON instead of a declared selector/set structure. Define and validate their encoding; S:160–162 explicitly excludes free prose for predicate operands.

   `source_fact_ids` accepts values such as `[null]` or `[123]`, which evade the empty-array rule without supplying fact IDs—M1155:223–224 versus S:107. Validate element types and require resolvable lineage at the contracted write boundary.

   `verse_cited` records can have both `source_text` and `source_page` NULL—M1155:180–181. Add the conditional citation requirement implied by S:62–64 and 106–108.

   The ruling biconditional in M1154:137–138 and M1155:227–228 both requires a ruling for **all** testimony and forbids retaining one on a verse-cited scored row. S:110 says testimony **under a ruling**; “required iff” does not itself establish “forbidden otherwise.” Align the constraint with the frozen condition rather than imposing this stronger interpretation.

   Finally, S:89’s canonical-chart restriction is only a comment beside M1155’s general chart FK. Its enforcement boundary needs an explicit disposition.

Two smaller amendments are not independently merge-blocking: `idx_kgse_object` duplicates the index already supplied by `ka_gochara_sky_event_ordinal_uq`; and neither consuming table indexes `coverage_ref`, potentially making future manifest deletion checks expensive.

**Can A5.3 proceed without guessing?**

**No.** It would have to choose a contact-storage model, coverage-manifest interpretation, same-tuple correction identity, numerical function encoding, and persistent qualification/result representation.

The AV declaration’s five-column shape is usable, but the meaning of its `convention` identifier and the exact evaluation-lineage binding still need to be fixed before authoring P5 data. O-BP-3 requires a write-time rejection when the declaration join is absent; the table alone supplies no such guarantee.

Solver mathematics, deterministic ID generation, ordering of prerequisites, testimony exclusion, Moon scheduling and the remaining evaluation oracles are legitimate writer/evaluator responsibilities. Their deferral does not cure the structural gaps above.

**What I could not verify**

- Production schema, applied hashes, object collisions, privileges, actual locks or existing data: no database connection was made.
- Fresh apply, rollback, replay, mutation rejection or delete-then-insert behavior in PostgreSQL.
- Live migration-number reservations or remote changes beyond the local `origin/main` reference.
- A5.3 execution or A5.5 oracle results. The oracle inventory was verified as **57: 21 literal and 36 executable-at-A5.5**, not executed.
- Whether any reviewed migration has already been applied. **If applied anywhere governed by §N.4, corrections require new forward migrations; these files must remain unchanged.**

The frozen inputs read for this review were SHA-256 `d5097ca18a721d8005cab593f3c3865227d22ff1435b8adc9973275d3f786a47` for S and `19951b06ce672ac4cff82d74fb6c7bb7babe4315582ec1c142a0a7871752c277` for O.

