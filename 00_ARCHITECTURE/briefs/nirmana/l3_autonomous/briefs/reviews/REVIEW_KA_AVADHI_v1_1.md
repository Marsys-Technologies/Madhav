---
artifact: KALA_BRIEF_INDEPENDENT_REVIEW
canonical_id: REVIEW_KA_AVADHI
version: "1.1"
status: REVIEW_ISSUED
date: 2026-09-24
brief_under_review: 00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/KA_AVADHI_ELEVATION_BRIEF_v1_0.md (frontmatter version "1.1")
prior_review: briefs/reviews/REVIEW_KA_AVADHI_v1_0.md (REWORK; 1 BLOCKER + 8 MAJOR + 16 MINOR/NOTE)
reviewer: "Fable 5.1 review agent, fresh context, read-only"
worktree: "/Users/Dev/madhav-l3/layer-briefs @ e82dd34a3 (branch l3/kala-layer-briefs)"
source_revision_check: "brief cites 9feac52d7 / 3387c9ac3; `git diff --name-only 3387c9ac3 HEAD` is 12 markdown files under briefs/ and briefs/reviews/ — no code, migration or seed changed; `git diff --stat 9feac52d7 HEAD` on ka_avadhi.py, tree_walk.py, migrations 670/859/1023/1034, query_dasha_dossier.ts, kala_temporal.ts, asset_registry_seed.ts is empty. 1023 (9a5835b02, 2026-09-10) is an ancestor of 9feac52d7."
method: "every v1.0 finding re-verified at source, not from §12; every file:line in v1.1 re-read with sed/grep/cat -n; no DB, no network, no git write, no test run"
---

# Independent re-review — `KA_AVADHI_ELEVATION_BRIEF` v1.1

## 1. Verdict

**`REWORK`.** v1.1 disposes the v1.0 BLOCKER structurally (orphan detection moved to read time) and
lands F2/F3/F5/F7/F10/F11/F13/F14/F16/F19–F22/F25 cleanly; but the rewrite adopted two reviewer
claims as `[R]` without re-checking the code beneath them and both are wrong at source — (i) the L2
writer emits **stable, content-addressed `pratijna_id`s** (`bo_pratijna.py:360-363,413-416`), so an
L2 regeneration does **not** orphan anything: the §4.16 ablation is false, the Relevant-influence
fixture cannot fire as written, and a resolver that reads "generation ≠ head" as
`pratijna_orphaned` would emit a false orphan on every regeneration; (ii) the "same-`start_iso`
`chara_karaka` MD rows" are the **five ayanāṃśa variants** (`stage3_clocks.py`'s SELECT has no
ayanāṃśa filter) which `ka_avadhi` already excludes, and 206's `UNIQUE(…, start_iso, build_id)` plus
`replace_prior_chart_dashas` make intra-build same-`start_iso` rows impossible at lahiri — §0's
defect (5) is unsupported. Add to that: the proposed "total" `ORDER BY` is not total; the stamp
conjuncts "(i)/(j)" are borrowed labels with no stated content (1023 ends at (e)); the
`domain_not_in_ontology` reason has no lord-level red path once the brief's own aliases land; and the
"cannot bind" cap arithmetic is pre-alias (Mars reaches exactly 10 after item 4; the ontology seeds
27 classes, not 26).

## 2. Findings

Severities: `BLOCKER` / `MAJOR` / `MINOR` / `NOTE`. "N-" ids are new in v1.1; the v1.0 finding each
one bears on is named.

| id | sev | brief claim (section) | found at source (exact lines read) | proposed correction |
|---|---|---|---|---|
| N1 | **MAJOR** (bears on F1/F3/F18) | §4.6: the serve-time resolver *"compares each ref's `generation` to the L2 head and reports `completeness_state='unavailable'`, `reason='pratijna_orphaned'`"*; §4.16 ablation: *"Regenerate L2 without rebuilding: today the dossier carries dangling ids silently"*; §3: *"(e) goes red again only when L2 regenerates without a Kāla rebuild"*; §7 Relevant influence: fixture *"regenerate `bodha_pratijna` ids in the fixture and do not rebuild"*. | `bo_pratijna.py:436` `@l2_producer("bo_pratijna")`; `:458` `DELETE FROM public.bodha_pratijna WHERE chart_id=%s`; `:360-363` and `:413-416` set `pratijna_id = stable_semantic_uuid("pratijna", {chart_id, ayanamsha_id, event_class_id})` (`data_plane_contracts.py:135`). An L2 regeneration therefore reproduces **identical** ids for the same (chart, ayanāṃśa, class): nothing dangles, conjunct (e) (`1023:177-184`, an anti-join on `pratijna_id`) stays green, and "regenerate ids in the fixture" produces zero orphans. The 3,087 orphans (`670:26`, 2026-09-05) predate stable ids (`fa9857f00`, 2026-09-16, `git log -S stable_semantic_uuid`) — they are real live orphans of the random-uuid era that a `ka_avadhi` rebuild clears. Under the current writers the orphan red path is **row deletion / class retirement / ayanāṃśa change**, not regeneration. Separately, "generation ≠ head" is a proxy: it fires on every regeneration while every id still resolves (§N.8 — the signal measures a proxy, not the claim). | (a) The orphan detector is the **read-time anti-join on `bodha_pratijna.pratijna_id`** (what (e) already does), reported as `pratijna_orphaned`; generation drift is a distinct `reason='pratijna_generation_stale'` (SC-9 still wants the stamp). (b) Fixture: *delete* one referenced `bodha_pratijna` row (or retire a class) and do not rebuild. (c) Restate §3 and §4.16: regeneration does not orphan under stable ids; state where the red path actually is, and that live incidence after the rebuild is expected to be ~0. |
| N2 | **MAJOR** (bears on F9) | §0 defect (5): *"L1 emits same-`start_iso` `chara_karaka` MD rows whose collapse under the writer's non-total `ORDER BY` plus `ON CONFLICT DO UPDATE` is invisible"*; §3 Observed; §4.9; §7 Duplication *"two L1 `chara_karaka` MD rows sharing `start_date`"*; §11.1 *"a Kṣetra code comment says yes"*. | The comment (`stage3_clocks.py:1071-1075`) sits under a SELECT with **no `ayanamsha_id` filter** (`stage3_clocks.py:1021-1025`: `WHERE chart_id = %s AND system_id = %s AND level_n BETWEEN 1 AND 4`) — "up to 5 MD rows with the same start_iso" is the five ayanāṃśa spines (the CR-110 pooling the writer's own comment describes, `ka_avadhi.py:52-70`). `ka_avadhi` filters to `lahiri_chitrapaksha` (`:80,:93`). Within one ayanāṃśa: `chart_dashas` is `UNIQUE (chart_id, ayanamsha_id, system_id, level_n, start_iso, build_id)` (`206:60`) and `replace_prior_chart_dashas` deletes the whole `(chart, system, ayanamsha)` scope before insert (`_idempotency.py:75-92`; `ga_dashas_writer.py:78`, `:3024`), so one `build_id` per scope — same-`start_iso` duplicates for one `(system, level)` at lahiri are **DDL-impossible**. The only residual collapse is same-`start_date` with different `start_iso` (sub-day periods), which nothing here evidences. | Withdraw §0 (5) / §3 / §4.9's premise; keep the Duplication row only as a *constructible* guard (two rows, same DATE, different instant) and say it is not a measured live defect; keep the collapse counter if wanted, but do not carry it as an observed failure to the native (§10.5 should be re-worded: L3-A12's key question stands on its own — `start_iso` vs `period_start` — not on this premise). |
| N3 | **MAJOR** (bears on F9) | §4.9: *"Both spine fetches gain a **total** `ORDER BY` (`system_id, start_date, level_n, lord_graha`)"*; §7 Duplication *"deterministic survivor under the total `ORDER BY`"*; §4.9 *"the build compares L1 candidate count to rows written per system"*. | `level_n` is constant per fetch (`:79` `level_n = 1`, `:92` `level_n = 2`) and adds nothing; two rows can share `(system_id, start_date, lord_graha)` (same DATE, different `start_iso`). The only guaranteed tie-breaker is the PK `dasha_row_id` (`206:37`); `start_iso` (`206:48`) is the semantic one. Calling a non-total order "total" is the §N.7 item 2 defect class inside the fix. Also `rows_inserted = len(all_rows)` (`:328`) is the **candidate** count, not rows written — the counter needs a post-insert `COUNT(*)`. | `ORDER BY d.system_id, d.start_date, d.start_iso, d.dasha_row_id`; collapse counter = `len(all_rows)` − `SELECT count(*) FROM kala_avadhi WHERE chart_id=%s` after the insert, per system. |
| N4 | **MAJOR** (bears on F4) | §4.4: *"A lord whose live domain set is empty emits `reason='domain_not_in_ontology'`"*; §4.14 Missing: *"a Rāhu period after item 4 → non-empty, or `reason='domain_not_in_ontology'` if the ontology DEMAND is declined"*; §7 Context: *"a Rāhu lord with the ontology DEMAND declined → `reason='domain_not_in_ontology'`"*. | After item 4's own aliases every graha keeps ≥ 1 in-CHECK domain: Rāhu gets `travel` via `foreign→travel` (two seeded classes: `foreign_settlement` `388:175`, `travel_event` `456:261`); Ketu keeps `spirituality` (`:49`). The DEMAND concerns the 14 *dropped* strings, which the alias half does not depend on. So no lord has an empty live set; the lord-level reason can never fire and the Context row's expected output is unreachable under the brief's own design (§N.8: a detector with no red path). | Emit the exclusion **per dropped string**: `exclusions[{kind:'domain_string', reason:'domain_not_in_ontology', dropped: n}]` (fires today: 19 distinct / 21 occurrences; after item 4: 14). Keep a lord-level reason only for a lord absent from `_GRAHA_DOMAINS` (`lord_not_a_graha`, already there). Rewrite §4.14 and the Context row accordingly. |
| N5 | **MAJOR** (bears on F8) | §0 (4) / §4.8 / §1 391-row: *"`bodha_pratijna` is UNIQUE … over 26 seeded classes so the largest per-graha union is 8"*; §4.8 *"Neither can bind under current vocabularies"*. | Seeded classes: 22 in `388:36-215` + 5 in `456:208-283` (`achievement_recognition`, `financial_deception`, `psychological_arc`, `birth_anchor`, `travel_event`), no DELETE in 456/555 → **27** (the `bg_ghatana` seed row says 27; `bo_pratijna_karyatva.py:26` "27-class"). Per-domain counts: career 5, education 2, relationship 3, progeny 1, family 1, transition 2, wealth 3, residence 2, travel 2, health 3, spirituality 1, general 1, character 1. Union per graha **after the brief's aliases** (`:41-49`): Sun 8, Moon 8, **Mars 10** (career 5 + residence 2 via `property` + health 3), Mercury 5, Jupiter 6, Venus 6, Saturn 8, Rāhu 2, Ketu 1. "Largest 8" is pre-alias; post-alias Mars sits exactly on `[:10]` (`:290`) and one new career/residence/health class — which the §10.6 ontology DEMAND would add — binds it. | Correct 26 → 27 and 8 → 10-after-aliasing; scope "cannot bind" to "cannot bind today, binds at Mars the moment one class is added to career/residence/health" — which strengthens the §10.4 recommendation to remove, and says why the regression guard matters. |
| N6 | **MAJOR** (new) | `may_touch`: *"successor to 1023 re-pinning conjunct (b) … and adding the stamp conjuncts (i)/(j)"*; §5 *"conjunct (b) + stamp conjuncts (i)/(j)"*; §7 Positive invariant *"(a)–(e) + stamps"*, detector *"a stamp absent"*. | 1023's contract has conjuncts **(a)–(e) only** (`1023:97-184`); no (f)–(h) exist for this asset. "(i)/(j)" are the labels of the *Sudarshana* brief (`KA_SUDARSHANA_VARSHA_ELEVATION_BRIEF_v1_0.md:17,219,232`), whose 670 contract has (a)–(h). Nowhere in §4 does the brief say what (i)/(j) assert, on which columns or JSONB paths — §10.3 leaves JSONB-vs-columns undecided. A conjunct with no stated predicate cannot be written and "a stamp absent" cannot be tested. | Name them (f)/(g); write their predicates (e.g. (f): every row's dossier carries `inclusivity ∈ {closed_open}`, `time_basis`, `claim_grain` from B1; (g): `pratijna_refs[*].generation` non-null when `pratijna_refs` non-empty) in §4.12/§4.6 and gate them on §10.3's answer. |
| N7 | MINOR (bears on F24) | `may_touch` / §1 / §5: the successor *"must not clobber migration 1034's output-digest spec on the same row (:53-55)"*. | 1034 does `INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)` (`1034:51-57`; table created `598:6`) — a **separate table**, not a column of `asset_registry`. An `UPDATE asset_registry SET integrity_check_sql` cannot touch it. The v1.0 review's own phrasing ("a registry packet on the same row") was loose; v1.1 hardened it into a false constraint. | State it correctly: 1034 lives in `asset_output_digest_specs`; the successor touches only `asset_registry.integrity_check_sql` (and `expected_volume_*`) and cannot affect it. |
| N8 | MINOR (bears on F18) | §1 1036-row / §4.6: *"`pratijna_refs[].generation` binds to `data_plane_l2_producer_generations` (1036:14-37) for `bo_pratijna`"*; §7: *"DEMANDS L2 `bodha_pratijna` generation (via 1036)"*. | The "L2 head" is `l2_data_plane_generation_heads.current_generation_id` (`1036:232-242`, PK `(chart_id, asset_id)`), not a column of the producer-generations table; the canonical join is `data_plane_contracts.py:270-285`. Serve-time visibility: 1036 `REVOKE ALL … FROM PUBLIC, role_orchestrator, …, amjis_app` (`:1958-1976`) then `GRANT SELECT ON … data_plane_l2_producer_generations, … l2_data_plane_generation_heads … TO data_plane_builder, data_plane_verifier, data_plane_migrator, amjis_app` (`:1979-1998`); the serve client runs as `DB_USER=amjis_app` (`deploy.yml:1217`; `client.ts:62`) — so **the resolver can see the head by grant**. A `bo_pratijna` head is opened per build by `@l2_producer` (`bo_pratijna.py:436`; `data_plane_contracts.py:479-525`) only when `_contract_sql_enabled` (`:143-150`, real psycopg conn) and not `dry_run` (`:579`); whether a production head row exists is [DB]. **`role_orchestrator` has no SELECT on the heads table** after 1036 — the brief's *build-time* stamp in `ka_avadhi` depends on the sidecar's DB principal, which this review could not determine (§4). | Cite the heads table and the grant; state the [DB] caveat; state which role `ka_avadhi` runs as and that it needs SELECT on `l2_data_plane_generation_heads` for the build-time stamp (or stamp at serve time only). |
| N9 | MINOR (bears on F17) | §4.7: blueprint §12.1's *"`clocks_consulted`/`clocks_unavailable` for the served projection (F17) — adopted there"*. | §4.13, §6 lens F, §7 Delivery (timeline) and the §7 asset-local list still name `systems_included` / `systems_available` (`brief:225-226,279,302,315`). Blueprint `:743` names `clocks_consulted` / `clocks_unavailable`. One packet, two vocabularies. | Use §12.1's names everywhere or declare the alias mapping once (binding "Rule of adoption"). |
| N10 | MINOR (bears on F6) | §7 binding: B3 *"either a content-addressed `sha256(chart_id, system_id, level_n, period_start, FORMULA_VERSION)` is added (§10.3) or B3 is honestly declined"*. | B3 has three rows (`KALA_SYNERGY_BINDING:53-55`): the sha256 id, **`generation` on every row, part of the PK**, and the `window_ref` handle. v1.1 offers only the first; `generation` and `window_ref` are not mentioned anywhere in the brief (grep empty). | Offer all three or decline B3 as a whole; a `generation` column is the §10.3 additive DDL's natural companion. |
| N11 | MINOR (bears on F2) | §1 1023-row: *"(d) rewritten (`:153-174`)"*. | v1.0 F2 asked the brief to *"at least name"* that (d)'s CASE (`1023:158-169`) is a wrapper-local copy of `norm_graha`'s alias table (§N.7 item 3) — 1023's own header admits it "mirrors" the SSoT (`1023:38-39`). Grep for "alias table", "item 3", "wrapper-local", "CASE" in the brief: empty. | One sentence in §1 or §4.2; a successor could call a SQL wrapper of `norm_graha` if one exists, else record the drift risk. |
| N12 | MINOR (bears on F12) | Citations. | `206:9,16` for `lord_graha NOT NULL` / `start_iso`/`end_iso` / `sandhi_flag` → the DDL is `206:36-61`: `lord_graha … NOT NULL` `:44`, `start_iso`/`end_iso TIMESTAMPTZ` `:48-49`, `sandhi_flag` `:51` (lines 9 and 16 are the header comment and a `chart_facts` index). `391:5,17` for `build_id` / UNIQUE → `:11` and `:22` (line 5 is `BEGIN;`). `REGISTER:147` → that row is `ka_yojaka`; `ka_avadhi` is `MADHAV_DATA_PLANE_ASSET_CONTRIBUTION_REGISTER_v2_0.md:153`. `_FETCH_MD_SQL :74-84` → `:73-82`; `_FETCH_AD_SQL :86-96` → `:84-95`; `_CANONICAL_AYANAMSHA :72` → `:71`. `source_query_availability.ts:3054-3064` → path is `platform/src/lib/retrieval/registry/knowledge/source_query_availability.ts` (content resolves, `:3050-3068`). `must_not_touch` "supabase/migrations/395" → `platform/supabase/migrations/395_kala_avadhi.sql`. | Re-pin. |
| N13 | NOTE (bears on F15) | §7 Irrelevant control: *"`activated_ids`/`pratijna_refs` set-equal and canonically ordered"*. | The nondeterminism's source is `_FETCH_PRATIJNA_SQL … ORDER BY bp.grade DESC` (`:108`) — non-total on ties — feeding insertion order at `:236`. The row can go red today (good); but the canonical order is never named. | Name it (e.g. `(domain, event_class_id)`) so the test asserts one thing. |
| N14 | NOTE | Header fields `interface_packet_targets_not_may_touch`, `status: DRAFT_FOR_INDEPENDENT_RE_REVIEW`. | Guide §2 (`:57-78`) lists the verbatim header; neither field is in it. Six sibling briefs now carry `interface_packet_targets_not_may_touch` (grep) — a convention born of reviews, not yet in the guide. | Accept as convention and amend the guide once, or fold into `must_not_touch` with a role annotation. |
| N15 | NOTE | §11.3 non-claim on the 3,087. | Dated: the count is from 2026-09-05 (`670`), stable ids landed 2026-09-16; so it is the pre-stable-id residue, cleared by one `ka_avadhi` rebuild, and not reproducible afterwards by regeneration (N1). | Say so; it changes what the read-time detector will show after the rebuild (expected ~0, red path = deletion/retirement). |

## 3. Citations verified

All paths from the worktree root. "resolves" = the lines say what the brief says.

| citation | result |
|---|---|
| `ka_avadhi.py:13-15` (docstring; `strength_factor`) | resolves |
| `:29` `ALL_DASHA_SYSTEMS` import; `:33` `FORMULA_VERSION`; `:37` `_DASHA_SYSTEMS` | resolve |
| `:40-50` `_GRAHA_DOMAINS` (36 strings; 21 out of CHECK; Rāhu 0/4) | resolves; counted |
| `:71-95` canonical ayanāṃśa + fetches; `:72` `_CANONICAL_AYANAMSHA` | `:71`; fetches `:73-82` / `:84-95` (brief `:74-84` / `:86-96`) |
| `:81,:94` `ORDER BY d.system_id, d.start_date` | resolve |
| `:101-109` `_FETCH_PRATIJNA_SQL`; `:105` ontology join | resolve; `:108` `ORDER BY bp.grade DESC` (N13) |
| `:132-143` fact refs SQL; `:142` `LIMIT 10`; 8 keys `:138-140` | resolve |
| `:145-163` `_INSERT_SQL` upsert | resolves |
| `:194-201` fetch calls; `:207-224` refusal; `:226-247` pratijñā savepoint; `:249-276` per-graha savepoint; `:259` `norm_graha` | resolve |
| `:280-309` `_build_row`; `:280-290` domain loop; `:290` `[:10]`; `:291-294` modulation; `:305-307` citations | resolve |
| `:324-327` delete-then-insert; `:328` `rows_inserted = len(all_rows)` | resolve (N3) |
| `tree_walk.py:40-43` | resolves |
| `1023:13-34, :36-43, :92-187, :118-132 (b), :122-123 'chara', :153-174 (d), :177-184 (e)` | resolve; (a)–(e) only (N6) |
| `670:25-26` header; `:101-109` old (d) | resolve |
| `859:15-24, :21-22, :60-77` | resolve |
| `395:3, :9-23, :22, :27, :34-37, :37` (`COMMENT ON` — correctable by a successor) | resolve; path `platform/supabase/migrations/` |
| `388:14-16` CHECK (13 values); `388:36-215` 22 classes | resolve; no later ALTER of the domain CHECK (grep both trees: 456 adds shape constraints only) |
| `456:208-283` +5 classes; `555` no domain edits/INSERT/DELETE | read; total 27 (N5) |
| `391:5,17` | **off**: `build_id` `:11`, UNIQUE `:22`; `pratijna_id … DEFAULT gen_random_uuid()` `:8` (overridden by the writer, N1) |
| `1034:53-55` | resolves — but into `asset_output_digest_specs` (N7) |
| `1036:14-37` DDL; `:232-242` heads; `:1958-1998` revoke/grant | read; basis of N8 |
| `206:9,16` | **off**: DDL `:36-61`; `:37` PK `dasha_row_id`; `:44`; `:48-49`; `:51`; `:60` UNIQUE incl. `start_iso, build_id` |
| `ga_dashas_writer.py:2026,2055,2084,2112` `"chara_karaka"`; `:882-896` sign lords; no `'chara'` literal | resolve |
| `_idempotency.py:75-92` `replace_prior_chart_dashas` | read; basis of N2 |
| `stage3_clocks.py:1071-1076` comment; `:1021-1025` its SELECT (no ayanāṃśa filter) | comment resolves; premise does not (N2) |
| `bo_pratijna.py:147, :165, :360-363, :413-416, :436, :458` | read; basis of N1 |
| `data_plane_contracts.py:135, :143-150, :270-285, :479-525, :557-600` | read; basis of N1/N8 |
| `asset_registry_seed.ts:2334-2353` (ka_avadhi); `:529-541` (`bg_ghatana`, `target_table: 'brahma_event_ontology'`) | resolve |
| `query_dasha_dossier.ts:5, :96, :103-110, :89-92` (dossier passthrough) | resolve |
| `kala_temporal.ts:116, :277-321, :278, :309, :314, :319` | resolve |
| `knowledge/source_query_availability.ts:3050-3068` | resolves at the `knowledge/` path |
| `tests/l3/test_m4_avadhi_lord_condition_refs.py:15` | resolves |
| `tests/test_migration_859_avadhi_expected_volume.py:36, :72-78, :105+` | resolve |
| Blueprint `:284, :289, :322, :394, :658, :672, :904`; §12.1 Clock row `:743` | resolve |
| Strategy `:47, :91, :282, :336, :346` | resolve |
| Foundation `:39` (eight F12 roles), `:72` (F06 companions) | resolve |
| `KALA_SYNERGY_BINDING:28-34 (B1), :40-46 (B2), :53-55 (B3), :69-70 (B5)` | read; basis of §5 |
| `REGISTER:147` | **off**: `ka_yojaka`; `ka_avadhi` at `:153` |
| Guide `:57-78` header; `:157` lenses as appendix | read |
| `deploy.yml:1217` `DB_USER=amjis_app`; `client.ts:45-70` | read; basis of N8 |
| `git log -S stable_semantic_uuid -- bo_pratijna.py` → `fa9857f00` 2026-09-16; 670 → `d13516739` 2026-09-05; 859 → `54174fca3` 2026-09-07 | read |
| `git cat-file -t 793972c75…` (parent contract blob) | commit exists |

## 4. What could not be verified, and why

- Whether `l2_data_plane_generation_heads` holds a `bo_pratijna` row for the canonical chart in
  production (the wrapper opens one only on a real psycopg connection, not in dry-run) — no DB.
- Which Cloud SQL principal the Python sidecar / orchestrator runs `ka_avadhi` under, and hence
  whether a *build-time* read of the heads table is permitted after 1036's REVOKE from
  `role_orchestrator` — not discoverable from the workflow lines read; [A].
- Whether `chart_dashas` at lahiri holds any two `chara_karaka` MD rows sharing a `start_date` with
  different `start_iso` (the only collapse the DDL permits) — no DB; the code path says
  "unlikely", not "impossible".
- The 3,087 / 1,169 / 2,930 figures — migration headers, not re-measured.
- Whether `chart_facts` carries more than one build generation per subject — no DB.
- No test was run; `[U]` rows were assessed for red paths by reading.

## 5. Conformance to the binding (B1–B7)

- **B1 — conformant** in spelling: `t_start/t_end` as `timestamptz` (L1 `start_iso/end_iso` are
  `TIMESTAMPTZ`, `206:48-49`), `inclusivity='closed_open'`, `time_basis='event_instant'`,
  `claim_grain='instant_grain'`, `sandhi_flag` by reference. The `resolver` row (import
  `ka_temporal/date_resolver` for date↔instant) is moot when instants are copied from L1, but should
  be said.
- **B2 — conformant** in spelling; `reason` now carries `owner`, `evidence_ref`,
  `next_eligible_action`. But `reason='pratijna_orphaned'` as *specified* is keyed to a proxy (N1)
  and `reason='domain_not_in_ontology'` has no lord-level red path (N4).
- **B3 — partial**: sha256 id offered via §10.3; `generation` on the row and `window_ref` not offered
  (N10).
- **B5 — conformant** in shape; `exclusions[reason='collapsed_same_start']` rests on a withdrawn
  premise (N2) and `reason='domain_not_in_ontology'` needs the per-string form (N4).
- **B4, B6** — n/a, correctly stated.
- **Outside the vocabulary**: `systems_included` / `systems_available` retained beside the adopted
  `clocks_consulted` / `clocks_unavailable` (N9). Asset-local fields (`pratijna_refs`, `match_basis`,
  `sublord_modulation`, `quality.domains`, `citations`) are declared as such — acceptable.

## 6. Disposition of the v1.0 findings (verified at source, not from §12)

| v1.0 | status | grounds |
|---|---|---|
| F1 BLOCKER | **PARTIAL** | Moved to read time and the accretion alternative named and rejected — the structural fix is right. But the resolver as specified compares generations (a proxy), the fixture "regenerate ids" cannot produce an orphan under `stable_semantic_uuid`, and the ablation sentence is false (N1). |
| F2 | **PARTIAL** | 1023 is the live contract in frontmatter/§1/§3/§5/§7; in `must_not_touch`; successor-of-1023 with byte-identical siblings — verified against `1023:36-43`. The wrapper-local CASE note is absent (N11). |
| F3 | **PARTIAL** | "(e) green after rebuild" verified. "(e) red again when L2 regenerates without a rebuild" is false under stable ids — red only on deletion/retirement (N1). |
| F4 | **PARTIAL** | Named as a defect; five aliases are right against `388:14-16` (`children→progeny`, `home→residence`, `moksha→spirituality`, `foreign→travel`, `property→residence` all in the CHECK, all with seeded classes); the 14 dropped strings are correctly listed (19 distinct + `dharma`/`karma` repeats = 21); `[U]` Vocabulary row fails today; §9 count removed. But the lord-level `domain_not_in_ontology` cannot fire post-alias (N4). |
| F5 | **RESOLVED** | Decision withdrawn; `bg_ghatana.target_table = 'brahma_event_ontology'` verified (`seed:537`); §5 says "nothing is dropped". |
| F6 | **PARTIAL** | Random-uuid offer withdrawn; sha256 over the DDL natural key + `FORMULA_VERSION` offered via §10.3. `generation` / `window_ref` not offered (N10). |
| F7 | **RESOLVED** | Value row is M4-only rebuild vs elevated rebuild on a frozen Q06 question; the measured difference is the elevation's own fields. |
| F8 | **PARTIAL** | Q8 no longer cited as ruled (`:658,:672` verified); caps put *to* Q8; no `cap_10.dropped` counter served. The arithmetic ("26 classes", "largest union 8") is wrong and pre-alias (N5). |
| F9 | **PARTIAL** | Duplication row, collapse counter and the L3-A12 key question added. But the adopted premise is the five-ayanāṃśa pooling, DDL-impossible at lahiri (N2), and the proposed `ORDER BY` is not total (N3). |
| F10 | **RESOLVED** | `vocabulary` dropped; the import is declared "not an F12 input … no `depends_on` edge" (§5), consistent with `FOUNDATION:39`. |
| F11 | **RESOLVED** | DP01 cited; SC-10 explicitly not; synergy-map amendment raised. |
| F12 | **PARTIAL** | Most lines re-pinned (`:37,:33,:142,:207-224,:305-307,:194-201,:280-309,:259` verified). New drift `:74-84/:86-96/:72`; `206:9,16` and `391:5,17` carried over unresolved; `REGISTER:147` off (N12). |
| F13 | **RESOLVED** | Path corrected; migration-text vs live-DB assertions distinguished (`:36,:72-78` vs `:105+` verified). |
| F14 | **RESOLVED** | `kala_temporal.ts` moved out of `may_touch`; guide boilerplate present in `must_not_touch`. |
| F15 | **RESOLVED** | Control now shuffles `pratijna_by_domain` insertion order — has a red path today (N13 asks only that the canonical order be named). |
| F16 | **RESOLVED** | `level_n: 3` (`kala_temporal.ts:319`) disclosed in §1/§2.3/§4.13/§7. |
| F17 | **PARTIAL** | `sandhi_flag` added to B1; §12.1 names adopted in §4.7 but `systems_included`/`systems_available` survive in four places (N9). |
| F18 | **PARTIAL** | Bound to 1036 rather than the build-id fall-through. The head table, the grant and the [DB] caveat are missing, and the stamp is conflated with orphan detection (N1, N8). |
| F19 | **RESOLVED** | Upgraded to [V] with `ga_dashas_writer.py:2026-2112` and `_verify_chara`; 859 dated against `fa9857f00` — both verified. |
| F20 | **RESOLVED** | Q-K01 cross-reference only. |
| F21 | **RESOLVED** | `owner`, `evidence_ref`, `next_eligible_action` named (§4.6). |
| F22 | **RESOLVED** | Zero readers cited as [R]; Delivery row asserts the named-jsonb passthrough. |
| F23 | n/a | Noted by the brief; nothing owed. |
| F24 | **PARTIAL** | 1034 mentioned — but as "the same registry row"; it is a separate table and cannot be clobbered by the successor (N7). |
| F25 | **RESOLVED** | Lenses moved to an appendix after §7 (guide `:157`). |
