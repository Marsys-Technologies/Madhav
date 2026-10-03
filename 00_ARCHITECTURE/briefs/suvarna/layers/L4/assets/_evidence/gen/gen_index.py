#!/usr/bin/env python3
import collections, json
from gen_common import *

CFS = [
 dict(id='CF-L4-02', title='Rebuild blockers: the integrity-SQL coupling to frozen L5 rows, the FK cascades, the builder grant gap',
  why='no L4 rebuild can be accepted until these are decided; one migration and three SS answers; tier-dependent but small.',
  gate='Build (integrity, completion); assets: ph_nimitta (a), all five CASCADE children (b), ph_rectification (c)',
  evidence="(a) `ph_nimitta.integrity_check_sql` ends a term with `mimamsa_predictions ... source_pramana_id ... a.anchor_id IS NULL ... = 0`; reader count of that term = 135 (all charts) and the orchestrator rolls back and errors a writer whose post-write check is false (`asset_runner.py:1200-1210`). (b) `phala_anchors.convergence_id -> kala_convergence ON DELETE CASCADE` and four CASCADE children (`pg_constraint`); the canonical chart's `kala_convergence` is empty while `ka_sangam` records 14,868 rows written. (c) `has_table_privilege('data_plane_builder', 'phala_rectification'|'phala_rectification_best', 'INSERT'|'DELETE'|'SELECT')` = false x6; the other eight `phala_*` tables are granted.",
  design="(a) scope the term to the chart and to non-frozen predictions, or move it to L5 (`mi_bhavisya` integrity SQL), by a surgical registry migration verified by production structure; (b) SS decides keep / SET NULL / drop FK (the F-3 precedent `F3_MSR_FK_DROP_v1_0.md`); (c) a grant migration mirroring the other eight tables, plus plan membership.",
  test='failing-first: the new SQL is true on today\'s 135-pending state and false for a NEW dangling reference; mutation: restore the global term -> false. For (b): deleting a `kala_convergence` row in a fixture leaves/removes the anchor as decided. For (c): `has_table_privilege` true.',
  blast='registry rows + two FKs + one grant; (a) decides what happens to frozen predictions (T1 7.3: a rebuild must not reset chronology)',
  rebuild='none for the migrations; they unblock the rebuild', cls='registry/declaration + migration', j1='tier-dependent: no tier says whether an L3 rebuild may delete L4 or who owns the L5->L4 reference check', decision='OPEN - Q-L4-02, Q-L4-03, Q-L4-04'),
 dict(id='CF-L4-07', title='Edge correction batch (one surgical registry migration)',
  why='tier-independent, no rebuild, changes freshness semantics only.', gate='Build (dag, dep_liveness); assets: ph_nimitta, ph_rectification, ph_muhurta, ph_sodhana, ph_pramana',
  evidence='Fresh census Build.dag FAIL x2 (`ph_nimitta -> bo_pratijna`, `-> ka_yojaka` at `ph_nimitta.py:463,477`; `ph_rectification -> ga_dashas` at `ph_rectification/__init__.py:111`). Declared-unread edges (writer reads no table the producer owns): `ph_nimitta` bo_bimba, bo_karanajala; `ph_muhurta` ka_gochara (explicit, `:358-382`), ka_kalasutra; `ph_sodhana` bo_laksana; `ph_pramana` x5 siblings; `ph_rectification` ph_nimitta.',
  design='Add the three missing edges; remove or annotate the declared-unread edges (`ph_phaladesa` already carries the sibling ordering). Migration 1210 (12 direct edges) is the precedent; L0 bedrock edges were deliberately excluded and are untouched. Number = max+1 across every origin head at execution time, verified by production structure.',
  test='failing-first: fresh-census Build.dag PASS for the three assets; mutation: delete an added edge -> reads-match FAIL naming it.', blast='the three assets become stale when the new producers rebuild (correct); the five unread-edge removals stop spurious staleness; the canonical rebuild plan (25 assets) is unchanged in membership but not in strict order (`ph_nimitta` after `ka_yojaka`/`bo_pratijna`, both already earlier waves)',
  rebuild='none', cls='registry/declaration', j1='tier-independent', decision='no question; Steward'),
 dict(id='CF-L4-01', title='Stored state versus current code and dangling references: the canonical-chart rebuild chain',
  why='the largest delta: every stored L4 row on the canonical chart is stale, most predate nine W3 fixes, and many point at rows that no longer exist.',
  gate='Build (completion, count_integrity), Count, Carr; assets: all 9',
  evidence='All nine are `stale`, last built 2026-08-13 01:15-01:16 UTC (run `cbd6ea44`). 16 distinct commits (`5f097e738` 2026-08-21; `ea2f8a49a` and W3-3a..m 2026-09-05/06; `b9d2d254b` 2026-10-02) landed after it. Upstream on the canonical chart: `kala_convergence` 0, `kala_bhavishya` 0, `kala_obstruction` 0; `bodha_discoveries` ids regenerated 2026-09-10 (0 of 4 stored `discovery_id`s exist); `bodha_cdlm_cells` ids regenerated (0 of 155 `cdlm_cell_id`s exist); `phala_anchors` 4 of 139; `mimamsa_predictions` 4 of 139 resolve. The canonical rebuild plan (`CANONICAL_CHART_REBUILD_PLAN_v1_0.md` on branch rebuild-plan-001, fixture `f3_canonical_rebuild_plan_waves.json`) puts waves 7-11 = `ph_nimitta`; `ph_muhurta ph_pratikara ph_sankrama ph_sodhana`; `ph_suddha_sodhana`; `ph_pramana`; `ph_phaladesa`, then `mi_bhavisya`. `ph_rectification` is not in it.',
  design='No code change: dispatch in the plan order after the L3 waves, after CF-L4-02 and after the must-fix items (ph_pramana chart scope, ph_phaladesa narration, ph_pratikara cost tiering) so that the first rebuild does not write new defects over old ones.',
  test='per-asset: Build.completion PASS and Count.floor PASS on the new live counts; referential terms true (anchors resolve; `cdlm_cell_id` resolves; obstructions resolve); mutation: delete a parent row -> the relevant term goes false.', blast='all of L4 and `mi_bhavisya` (which deletes only pending/due predictions, rebuild-plan evidence: 139 pending)', rebuild='needs production rebuild of 8 assets (REVIEW item for SS; Exec Suvarna runs it, never this lane); 9th (rectification) needs a grant first', cls='data (rebuild)', j1='tier-independent for the dispatch; sequencing and the fate of frozen predictions are SS\'s', decision='OPEN - Q-L4-01'),
 dict(id='CF-L4-03', title='The silent-clean chain and completion PASSes that earn nothing',
  why='an absent signal is being read as a good one at three consecutive assets and in prose.', gate='Earn; assets: ph_sodhana -> ph_suddha_sodhana -> ph_phaladesa; plus ph_pratikara, ph_phaladesa, ph_sankrama integrity/completion',
  evidence='4 identical anchors -> 0 anomaly rows (`offline_checks.txt`: chart-wide detectors need >= 5, `ph_sodhana engine.py:300`); `ph_suddha_sodhana` reads zero flags as `clean` (4 of 4); `ph_phaladesa` narrates "passed clean sodhana review" (7 of 7). Census Build.completion PASS: `ph_pratikara` 536 = 536 (all 536 obstruction ids dangle, programmes empty), `ph_phaladesa` 13 = 13 (describes 139 anchors, 4 exist), and the `ph_sankrama` integrity clause is true over 155 dangling cell ids.',
  design='ph_sodhana writes a coverage statement when a check cannot run; ph_suddha_sodhana gains `not_assessed` (CHECK change); ph_phaladesa narrates only assessed anchors; add anti-join terms (every reference resolves) to the pratikara/sankrama/phaladesa integrity SQL; ask Track E whether Build.completion for count-only PASS should require the registry integrity SQL to be true (Q-L4-18).',
  test='failing-first: 4 identical anchors -> a coverage record / `not_assessed`; a dangling reference makes the integrity SQL false; mutation: restore the `< 5` guard / the one-sided join -> passes wrongly.', blast='ph_suddha_sodhana status vocabulary; narration; three integrity SQLs', rebuild='needs production rebuild (rides CF-L4-01)', cls='writer code + migration', j1='tier-dependent (TG-L4-019)', decision='OPEN - Q-L4-12, Q-L4-18'),
 dict(id='CF-L4-04', title='Constants, proxies and decorative bands stored as measurements (and the policy for score-like columns)',
  why='TG-L4-019 found no tier types the L4 score columns; the data shows what they hold.', gate='Earn, Null, Narr; assets: ph_nimitta, ph_muhurta, ph_sankrama, ph_rectification, ph_phaladesa (prose)',
  evidence='`ph_nimitta`: posterior 0.322 (1 distinct value) with constants robustness 3 / consensus 0 / AV potency 0.0, a +/-0.05 band (`engine.py:349-358`); `ph_muhurta`: `panchanga_score` is `condition x 0.8 + 0.2`, one value per action class, `hora_lord` = action graha, transit factor constant 0.5; `ph_sankrama`: `asymmetry_score` 0.0 over an all-NULL column, `spillover_confidence` = band x linkage; `ph_rectification`: `confidence_low = -0.2000`, fit 0.0000 x95; `ph_phaladesa`: "Confidence band spans ..." in prose. Score-bearing columns by table are listed in the L4 layer instance 2.1a.',
  design='SS classifies each score-like column (permitted structural score / permitted with a different name / NULL until measured / remove); the writers then store NULL, not a constant, where nothing was measured, and the names say what they hold. The code changes are per-asset FDs; the classification is one SS ruling.',
  test='per-asset: a context without sources stores NULL; mutation: restore the constant -> the test fails. Cross-asset: a CI check that no L4 numeric column is written from a bare literal.', blast='readers of `confidence_high`: ph_sodhana, ph_sankrama, ph_phaladesa, ph_muhurta ordering, serving, `mi_pariksha`', rebuild='needs production rebuild', cls='writer code + SS classification', j1='tier-dependent (T1 11, T2 3.1: "no unqualified composite score")', decision='OPEN - Q-L4-05, Q-L4-06'),
 dict(id='CF-L4-05', title='Loaders that swallow errors and return empty',
  why='the F-16 pattern fixed in ph_suddha_sodhana and ph_pratikara survives elsewhere; a read failure becomes a completed build of empty rows.', gate='Null, Build; assets: ph_sankrama (1), ph_phaladesa (4), ph_muhurta (4 + career-lord fallback), ph_pramana (narrowed, fine)',
  evidence='`ph_sankrama.py:273-275`; `ph_phaladesa.py:318-323,396,421,452`; `ph_muhurta.py:320-326,354-356,489-491,512-519`. By contrast `ph_suddha_sodhana._load_flags_grouped` and `ph_pratikara._load_obstructions` fail loud with comments naming the pattern.',
  design='Required inputs raise; optional inputs return an explicit `unavailable` that is stored; keep SAVEPOINT guards only where a missing table is a normal case.', test='failing-first: a forced read error fails the build; mutation: restore the swallow -> completes with empty rows.', blast='none on healthy reads', rebuild='rides CF-L4-01', cls='writer code', j1='tier-independent', decision='no question; Steward'),
 dict(id='CF-L4-06', title='`rows_inserted += 1` beside `ON CONFLICT DO NOTHING`',
  why='the build-record honesty defect W1 found in ph_muhurta (139 claimed, 134 stored), fixed in three writers, latent in three more.', gate='Build (completion); assets: ph_sodhana, ph_pratikara, ph_pramana (latent)',
  evidence='`ph_sodhana.py:85-96`, `ph_pratikara.py:182-198`, `ph_pramana.py:108-110`; fixed in `ph_nimitta.py:287-290`, `ph_muhurta.py:239-242`, `ph_sankrama.py` (`cur.rowcount == 1`).', design='Increment only when `cur.rowcount == 1`.', test='failing-first: a duplicate key yields a lower count; mutation: restore -> equal.', blast='build record only', rebuild='none', cls='writer code', j1='tier-independent', decision='no question; Steward'),
 dict(id='CF-L4-08', title='Calendar- and computation-date-dependent outputs',
  why='a rebuild on a different day, or after an L2 rebuild, writes different identities and statuses.', gate='Idem (fingerprint), Carr; assets: ph_nimitta (identity), ph_pramana (window_status), ph_pratikara (re_evaluation_date), ph_phaladesa (narration date), ph_muhurta (stored instant)',
  evidence='`ph_nimitta engine.py:136` and `ph_nimitta.py:837` read `date.today()`; discovery windows derive from the discovery\'s `computed_at` (`:692-696`) and `anchor_id` hashes them; `ph_pramana.py:51`; `ph_pratikara engine.py:236-239`; `ph_phaladesa.py:150`; `ph_muhurta` naive 06:00 stored as UTC.',
  design='Pass an explicit `as_of` through the context (default today) and record it in the ledger; hash only date-independent fields into identities; fingerprint contracts fix `as_of`.', test='failing-first: the same inputs with a different system date give the same identity (or a recorded `as_of`); mutation: use `date.today()` -> differs.', blast='anchor identity moves once', rebuild='needs production rebuild', cls='writer code', j1='tier-independent', decision='no question for plumbing; discovery windows are Q-L4-08'),
 dict(id='CF-L4-09', title='UUID chart_id serialisation: one shared encoder',
  why='the bo_*/ph_* adapter defect: confirmed once in this layer, protected twice, absent in seven.', gate='Build (history); assets: ph_sodhana (hit), ph_phaladesa (protected), the rest (not present)',
  evidence="`ctx.config['chart_id']` is a `uuid.UUID` on the real path (`asset_runner.py:1121`; comment `:166-170`; #1856 coerced only the provenance capture). Registry history: `ph_sodhana` 2 x `TypeError: Object of type UUID is not JSON serializable` (2026-07-11, traceback `asset_runner.py:459 _run_data_writer`), fixed by `6c0d98614` (`str(ctx.chart_id)` + a local `_UUIDEncoder`); `ph_phaladesa` keeps a raw chart_id in its ledger (`engine.py:222`) and a second copy of the encoder (`ph_phaladesa.py:35-40`); `ph_rectification`'s 2026-07-06 error text shows `chart_id=UUID('...')`. No `canonical_json`, `stable_uuid` or `uuid5` call in any `ph_*` file (grep); the only `uuid_generate_v5` is SQL `phala_anchor_identity`, which receives `chart_id::text` (inside the function) and a `%s::uuid` parameter. The other seven writers' `json.dumps` payloads contain only `str()` ids (file:line in each brief section 1.5).",
  design='One shared `JsonEncoder` (or a `to_jsonable()` helper) in the writers package used by every `json.dumps` in `ph_*`; a test that serialises every ledger/payload with a `uuid.UUID` chart_id in `ctx.config`; coerce `chart_id` to `str` once at the top of each `run`.', test='failing-first: a fake `ctx` with `uuid.UUID` chart_id runs each writer\'s serialisation path without error; mutation: put the UUID into a ledger without the encoder -> TypeError.', blast='none', rebuild='none', cls='writer code', j1='tier-independent', decision='no question; Steward'),
 dict(id='CF-L4-10', title='prose_fields and null_convention declarations (Null and Narr gates)',
  why='declarations-file edit only; moves Null/Narr off NO_DETECTOR for three assets and off PARTIAL for the rest.', gate='Null, Narr; assets: ph_pramana, ph_pratikara, ph_suddha_sodhana (undeclared); the other six declared with PARTIAL',
  evidence='Fresh census: `prose_fields` undeclared for ph_pramana, ph_pratikara, ph_suddha_sodhana (all Null.* / Narr.* NO_DETECTOR, "never read as no prose"); ph_sankrama Narr.agree PARTIAL (`falsifier` written but undeclared); ph_sodhana Narr.checkable INCONCLUSIVE on an empty table.',
  design='Per asset: declare the prose columns with `file:line` evidence or `[]` with evidence, and a `null_convention` for the NULL-by-rule columns named in each brief.', test='`platform/scripts/governance/__tests__/test_e6_1_declarations.py` passes; mutation: declare `[]` for an asset whose writer composes text -> Narr flags.', blast='none (census inputs)', rebuild='none', cls='registry/declaration', j1='tier-independent', decision='no question; Track E owns the file'),
 dict(id='CF-L4-11', title='Dens: density_contract on the L4 serving modules (and the scanner desync)',
  why='Dens FAIL x6, NO_DETECTOR x3 in the fresh census; ownership is TG-L4-021.', gate='Dens; assets: all nine reach a serving module',
  evidence='Fresh census Dens.served: FAIL for ph_phaladesa, ph_pramana, ph_pratikara, ph_sankrama, ph_sodhana, ph_suddha_sodhana; NO_DETECTOR for ph_muhurta, ph_nimitta, ph_rectification because the string scanner desyncs on `platform-mcp/src/tools/register_p1_synthesis.ts` / `register_p1_ganita.ts`. `density_contract` is declared only in `query_prospective_ledger.ts` of the L4_phala modules. Offline static re-scan under main (`rollup_L4.json`): FAIL 6 / NO_DETECTOR 3.',
  design='Declare `density_contract` facets on `query_phala_calibration.ts` (7 capabilities), `query_predictive_anchors.ts`, `query_domain_result.ts`; fix the scanner desync (Track E) so the three NO_DETECTOR cells can be read. Which layer owns the declaration is TG-L4-021.', test='Dens.served leaves FAIL; mutation: remove the declaration -> FAIL returns.', blast='serving metadata only', rebuild='none', cls='served surface (TS) + detector', j1='tier-dependent (TG-L4-021)', decision='no question; Track I / retrieval owner'),
 dict(id='CF-L4-12', title='Registry refresh: floors and descriptions',
  why='floors and prose are numbers and claims of a state that no longer exists.', gate='Count (information), Narr; assets: ph_nimitta 139, ph_sankrama 2,510, ph_suddha_sodhana 139, ph_pratikara 536 (+DRAFT), ph_muhurta 134, ph_phaladesa 13, ph_rectification 186; none for ph_sodhana, ph_pramana',
  evidence='Fresh census Count.floor FAIL x3 (nimitta -135, sankrama -2,355, suddha -135). Descriptions: `ph_phaladesa` "7 domains x 1 row ... narration pending via Gemini/DeepSeek" (13 rows, template narration); `ph_pramana` "L5 onboarding contract + evaluation-staging + portfolio/reverse-calibration channel"; `query_predictive_anchors.ts` "150 rows"; `L4_phala/index.ts` row counts.',
  design='After the rebuild set `target_floor` to the achieved count (CLAUDE.md N.4: floors aspirational, never fabricate rows); correct the descriptions in one registry migration + docs.', test='Count.floor PASS after the rebuild; mutation: restore the old floor -> FAIL.', blast='cockpit counts only', rebuild='none (after CF-L4-01)', cls='registry/declaration', j1='tier-independent', decision='Q-L4-06 (confirm)'),
 dict(id='CF-L4-13', title='One-way rule: upward readers and cross-layer coupling',
  why='T2 3.2: a chart-specific L4 conclusion must not feed an L3 computation; the registry edge check cannot see it.', gate='Carr; assets: ph_rectification (read by L3 `ka_kshetra`), ph_pramana (read by an L3 serving module), ph_nimitta (read by `ka_bhavishya_lekha` as a guard; reads `mimamsa_predictions` in its SQL)',
  evidence='`services/ka_kshetra/stage3_clocks.py:1012` -> `uncertainty.fetch_sigma_t_days` reads `phala_rectification` (no declared edge); `L3_kala/query_projections.ts` selects `phala_pramana` (fresh census Dens text); `ka_bhavishya_lekha.py:253-286` reads `phala_anchors.bhavishya_id` to refuse deleting referenced rows (a guard, not a computation).',
  design='Declare or remove each reader; for ka_kshetra either remove the L4 source of sigma_T or declare it as a documented exception.', test='a registry/grep test lists every cross-layer reader and fails on an undeclared upward read.', blast='ka_kshetra\'s sigma_T source (inert today)', rebuild='none', cls='registry/declaration + writer code', j1='tier-dependent', decision='OPEN - Q-L4-04'),
 dict(id='CF-L4-14', title='Domain / category vocabulary at L4 readers',
  why='the same defect class as the CR-66 and F2 fixes survives in three more places.', gate='Vocab; assets: ph_muhurta, ph_phaladesa, ph_pramana, ph_rectification',
  evidence='`ph_muhurta._DOMAIN_TO_ACTION` legacy keys (`:710-718`): 9 of 13 canonical domains fall to `new_venture`; `ph_phaladesa._ANCHOR_TO_PHALADESA_DOMAIN` dead legacy keys; `ph_pramana` cannot resolve 10 of 63 life-event categories; `ph_rectification` passes the compound `life_events.domain` slug to a plain-key table and uses ayanamsha short codes.', design='Resolve through `brahmagyan/domain_vocabulary.py` only; unmapped values are counted in the ledger, never silently defaulted; acharya decides the domain -> action and category -> domain mappings.', test='`test_domain_vocabulary_census.py` extended to these four readers.', blast='see assets', rebuild='rides CF-L4-01', cls='writer code + acharya', j1='tier-dependent (acharya)', decision='OPEN - Q-L4-11, Q-L4-15, Q-L4-17'),
 dict(id='CF-L4-15', title='Instruments absent: Earn / Cost / Carr / Vocab.alias / Ldgr',
  why='Track E instruments; nothing to change in an asset beyond declarations.', gate='Earn, Cost, Carr, Vocab, Ldgr; assets: all nine (Ldgr NO_DETECTOR for ph_rectification: no citation column)',
  evidence='Earn.build_record / Cost.baseline NO_DETECTOR x9 (no probe receipt names the run); Carr NO_DETECTOR x9; Vocab rollup NO_DETECTOR x9; Ldgr PASS x8, NO_DETECTOR for ph_rectification. Build.history PARTIAL x9 (0-3 errors, 9 aborts each; every latest run complete).', design='Per asset the brief names the carriage check (D1/D2/D3) and the claims that need a detector able to read false; Build.history follows the A.L0 Q11 definition (runs since the last change to the writer or registry row).', test="Track E's own.", blast='none', rebuild='none', cls='detector/tooling', j1='tier-dependent for Carr/Ldgr definitions', decision='no question; Track E'),
]

QS = [
 ('Q-L4-01', 'Rebuild authority, order and the frozen predictions', 'May Exec Suvarna run the canonical-chart L4 rebuild (waves 7-11) after the L3 waves, and what happens to the 139 frozen `mimamsa_predictions` (135 whose source anchors are gone)? Options: (A) leave them as historical records marked `source_retired`, re-freeze from the rebuilt anchors; (B) re-point by content identity where an anchor reappears; (C) retire them.', 'Rebuild after CF-L4-02 and the must-fix items; (A) because a rebuild must not reset chronology (T1 7.3).', 'SS (touches L5 frozen history)', 'all 9; mi_bhavisya'),
 ('Q-L4-02', 'Where does the L5->L4 reference check live?', '`ph_nimitta`\'s integrity SQL requires zero `mimamsa_predictions` without an anchor (135 now): it deadlocks any rebuild. Scope it to the chart and non-frozen rows, remove it, or move it into L5\'s own check?', 'Move it to `mi_bhavisya` (L5 owns those rows); scope the L4 term to the chart.', 'SS', 'ph_nimitta; mi_bhavisya'),
 ('Q-L4-03', 'May an L3 rebuild delete L4 rows?', '`phala_anchors.convergence_id ... ON DELETE CASCADE` removed 135 anchors and their children without any L4 writer running. Keep, SET NULL (as `bhavishya_id`), or drop the FK as F-3 did for MSR?', 'Drop or SET NULL and report orphans by function, as C13 does for `signal_id`.', 'SS (cross-layer)', 'ph_nimitta + 4 CASCADE children'),
 ('Q-L4-04', 'Rectification: grants, plan membership, the L3 reader', 'Grant `data_plane_builder` on `phala_rectification` / `_best`, add `ph_rectification` to the rebuild plan, and decide whether `ka_kshetra` may keep reading it (one-way rule).', 'Grant + plan membership after Q-L4-17; declare or remove the reader.', 'SS', 'ph_rectification; ka_kshetra'),
 ('Q-L4-05', 'Which L4 columns are scores, and what may they be called?', 'Classify `posterior`, the +/-0.05 confidence band, `composite_quality`, `panchanga_score`, `chart_personalization_score`, `linkage_strength`, `spillover_confidence`, `lel_fit_score`, rectification `confidence_*`: permitted structural score / rename / NULL until measured / remove (T1 11, T2 3.1, TG-L4-019). Does a D3 recompute-and-compare replace ph_sodhana\'s ceiling?', 'Keep as clearly named structural scores where the arithmetic is real (composite, linkage); NULL where nothing was measured (robustness, asymmetry, a zero fit); remove the decorative bands.', 'SS', 'ph_nimitta, ph_muhurta, ph_sodhana, ph_sankrama, ph_pramana (D5 scope), ph_rectification'),
 ('Q-L4-06', 'Floors and the DRAFT/CURRENT discipline', 'After the rebuild set `target_floor` = achieved count (CLAUDE.md N.4) for all assets that have one?', 'Yes.', 'Steward confirms; SS informed', 'CF-L4-12'),
 ('Q-L4-07', 'Source of `direction` for bhavishya anchors', '`probability_tier` (`tier_1_high` on every row) is a probability label, not a valence, yet maps to `elevated`. Use `mixed` until a valence exists, or name the valence source?', '`mixed` until a valence source is named.', 'SS + acharya', 'ph_nimitta'),
 ('Q-L4-08', 'Are discovery-seeded rows predictions?', 'Their window is the discovery\'s `computed_at` + 90 days with no signal context; their identity moves with every L2 rebuild. Keep as labelled "watch windows", move out of the prediction table, or drop?', 'Keep with a ledger `timing_basis` and exclude them from muhurta/mitigation linkage until SS rules.', 'SS', 'ph_nimitta; downstream readers'),
 ('Q-L4-09', '(acharya) Karmic frame and causal chain', 'Which graha is the root of a CGM path (the `derive_karmic_frame` input), should the chain be per anchor (needs a signal -> path join), and is a chart-level chain acceptable in a per-anchor field?', 'NULL-by-declaration until a per-anchor path exists.', 'Acharya review', 'ph_nimitta'),
 ('Q-L4-10', 'What is `phala_muhurta` for?', 'A live electional finder (`phala_muhurta_finder.ts`, `query_muhurat.ts`) scores real candidate times. `phala_muhurta` grades an anchor window at one instant (06:00 of its first day) with proxy factors. Keep as anchor-linked quality annotation (rename), make it a real slot ranker, or consolidate into the finder?', 'Keep with honest names and drop the muhurta claim; slots come from the finder.', 'SS + acharya', 'ph_muhurta'),
 ('Q-L4-11', '(acharya) Domain -> action-class map', 'Which action class (or none) for each of the 13 canonical domains? Today 9 default to `new_venture`.', 'Acharya table; NULL where no electional action exists.', 'Acharya', 'ph_muhurta'),
 ('Q-L4-12', 'What may "clean" mean, and where does an approval live?', 'Allow a `not_assessed` disposition (CHECK change)? Is "passed clean sodhana review" allowed in prose while `clean` can mean unassessed? Where does a native approval of a staged revision persist given the table is rebuilt per chart (same for `native_adopted` in rectification)? Should `ph_suddha_sodhana` be merged into `ph_sodhana` (T2 6.5 overlap)?', 'Add `not_assessed`; store approvals outside rebuilt tables; decide the merge after the rebuild shows what the split buys.', 'SS', 'ph_sodhana, ph_suddha_sodhana, ph_phaladesa, ph_rectification'),
 ('Q-L4-13', 'ph_pratikara: promotion, grain, provenance', 'Criteria to move DRAFT -> CURRENT; is one row per obstruction with an identical per-graha programme the intended grain; may `classical_tradition` flow into `source_id` (A.L0 Q3 ruled it is not provenance)?', 'Promote only after a rebuild shows non-empty, correctly tiered, per-remedy-cited programmes; carry the L0 attribution state when it lands.', 'SS', 'ph_pratikara'),
 ('Q-L4-14', 'ph_sankrama grain and cascade', 'Add an ayanamsha column (155 rows stay) or collapse to one row per (anchor, target, relationship) with an agreement count (31 rows)? Implement the multi-hop cascade or drop `cascade_depth`?', 'Collapse with an ayanamsha agreement count (it is the measured robustness the nimitta field pretends to carry).', 'SS', 'ph_sankrama; ph_phaladesa'),
 ('Q-L4-15', 'ph_pramana: what is a match, who maps life-event categories', 'May an in-window same-domain life event be called `direct` evidence when the falsifier\'s magnitude/direction is not evaluated? Mapping for the four unresolved categories (`residential+travel`, `loss`, `other`, `creative`).', 'Rename the label until criteria are evaluated; acharya maps the categories.', 'SS + acharya', 'ph_pramana'),
 ('Q-L4-16', 'ph_phaladesa: stored summary or served view', 'Keep a stored per-domain declaration with template narration, or serve the same from the base tables (T2 6.5 overlap investigation)?', 'Decide after the rebuild; narration fixes are needed either way.', 'SS', 'ph_phaladesa'),
 ('Q-L4-17', '(acharya) Is the rectification rule acceptable, and what is the product?', '"A dasha lord\'s house from the candidate lagna is a domain-significator house" as the fit rule; a sign-level scan cannot choose among stable offsets. Is the product a lagna-stability map, or a rectifier needing D41 whole-instrument scoring?', 'Describe and serve it as a stability map until a discriminating rule is approved.', 'Acharya + SS', 'ph_rectification'),
 ('Q-L4-18', 'Census definition', 'Should Build.completion for count-only PASS (ph_pratikara 536 = 536, ph_phaladesa 13 = 13) require the registry integrity SQL to be true?', 'Yes (Track E detector item).', 'SS / Track E', 'CF-L4-03'),
]

TIS = [
 ('TI-L4-01', 'all nine (wave order in CF-L4-01)', 'canonical-chart rebuild of the L4 chain after CF-L4-02 and the must-fix items', 'rebuild', 'y', 'Q-L4-01'),
 ('TI-L4-02', 'ph_nimitta', 'decouple the integrity SQL from `mimamsa_predictions`', 'registry', 'n', 'Q-L4-02'),
 ('TI-L4-03', 'ph_nimitta', 'NULL (not 3 / 0 / 0.0) for unmeasured robustness, consensus, AV potency; neutral robustness modifier', 'writer code', 'y', 'Q-L4-05'),
 ('TI-L4-04', 'ph_nimitta, ph_muhurta, ph_sodhana, ph_sankrama, ph_rectification', 'classify the score-like columns and apply the ruling (CF-L4-04)', 'writer code + SS ruling', 'y', 'Q-L4-05'),
 ('TI-L4-05', 'ph_nimitta', 'per-anchor CGM path or NULL-by-design for karmic frame / causal chain / precedent', 'writer code', 'y', 'Q-L4-09'),
 ('TI-L4-06', 'ph_nimitta', 'neutral `NimittaContext` defaults; reconcile JL-009 text', 'writer code', 'n', '-'),
 ('TI-L4-07', 'ph_nimitta', 'declare `bo_pratijna`, `ka_yojaka` edges; review `bo_bimba`, `bo_karanajala`', 'registry', 'n', '-'),
 ('TI-L4-08', 'ph_nimitta', 'FK cascade decision; discovery-window labelling', 'migration / writer code', 'n', 'Q-L4-03, Q-L4-08'),
 ('TI-L4-09', 'ph_nimitta', 'persist candidate attrition; `null_convention` declaration', 'writer code + declaration', 'n', '-'),
 ('TI-L4-10', 'ph_nimitta', 'bhavishya `direction` source', 'writer code', 'y', 'Q-L4-07'),
 ('TI-L4-11', 'ph_muhurta', 'name the proxy columns or measure them (`panchanga_score`, `hora_lord`, transit factor)', 'writer code (+ migration)', 'y', 'Q-L4-10'),
 ('TI-L4-12', 'ph_muhurta', 'decide the table\'s purpose and window semantics', 'writer code', 'y', 'Q-L4-10'),
 ('TI-L4-13', 'ph_muhurta', 'complete the domain -> action map (13 domains)', 'writer code + acharya', 'y', 'Q-L4-11'),
 ('TI-L4-14', 'ph_muhurta', 'fail loud on required reads; pin the LAGNA fact (ayanamsha + order)', 'writer code', 'n', '-'),
 ('TI-L4-15', 'ph_sodhana', 'coverage statement when chart-wide checks cannot run; minimum-anchor guard', 'writer code (+ CHECK)', 'y', 'Q-L4-12'),
 ('TI-L4-16', 'ph_sodhana', 'retire or re-ground the G-LADDER ceiling (D3 recompute)', 'writer code (engine)', 'y', 'Q-L4-05, Q-L4-12'),
 ('TI-L4-17', 'ph_sodhana', 'tighten `falsifier_absent`, `ledger_gap`; deterministic chart-wide anchor', 'writer code (engine)', 'y', '-'),
 ('TI-L4-18', 'ph_sodhana', 'count accepted rows; drop `bo_laksana` edge; declarations', 'writer code + registry', 'n', '-'),
 ('TI-L4-19', 'ph_suddha_sodhana', '`not_assessed` disposition', 'migration + writer code', 'y', 'Q-L4-12'),
 ('TI-L4-20', 'ph_suddha_sodhana, ph_rectification', 'durable home for native approval state', 'migration + writer code', 'n', 'Q-L4-12'),
 ('TI-L4-21', 'ph_suddha_sodhana', 'reachable magnitude/confidence deltas from ledger fields; declarations', 'writer code + declaration', 'y', '-'),
 ('TI-L4-22', 'ph_pratikara', 'tier remedies by `cost_tier` (never default to free)', 'writer code (engine)', 'y', '-'),
 ('TI-L4-23', 'ph_pratikara', 'remove the Jupiter / obstruction_type fallbacks; decide the grain', 'writer code', 'y', 'Q-L4-13'),
 ('TI-L4-24', 'ph_pratikara', 'carry upstream attribution state per remedy (after A.L0 TI-L0-09)', 'writer code', 'y', 'Q-L4-13'),
 ('TI-L4-25', 'ph_pratikara', 'count accepted rows; wire or drop `initiation_muhurta_ref`; declarations', 'writer code + declaration', 'n', '-'),
 ('TI-L4-26', 'ph_pratikara', 'DRAFT -> CURRENT criteria', 'registry', 'n', 'Q-L4-13'),
 ('TI-L4-27', 'ph_sankrama', 'ayanamsha fan-out: column or collapse', 'migration + writer code', 'y', 'Q-L4-14'),
 ('TI-L4-28', 'ph_sankrama', 'NULL asymmetry; record timing basis; cascade depth', 'writer code (engine)', 'y', 'Q-L4-14'),
 ('TI-L4-29', 'ph_sankrama', 'fail loud on CDLM read; non-vacuous integrity clause', 'writer code + registry', 'n', '-'),
 ('TI-L4-30', 'ph_sankrama', 'declare wealth divergence and `falsifier` prose', 'declaration', 'n', '-'),
 ('TI-L4-31', 'ph_sankrama', '`spillover_confidence` naming/NULL rule', 'writer code', 'y', 'Q-L4-05'),
 ('TI-L4-32', 'ph_pramana', 'chart-scope the `life_events` read (isolation)', 'writer code', 'y', '-'),
 ('TI-L4-33', 'ph_pramana', 'evidence labels; unresolved life-event categories', 'writer code + acharya', 'y', 'Q-L4-15'),
 ('TI-L4-34', 'ph_pramana', 'populate or drop never-populated columns', 'migration + writer code', 'n', '-'),
 ('TI-L4-35', 'ph_pramana', 'drop five unread edges; count accepted rows; declarations', 'registry + writer code', 'n', '-'),
 ('TI-L4-36', 'ph_phaladesa', 'narration fixes (contradiction, clean, band, spillovers) with the real jsonb shape', 'writer code', 'y', 'Q-L4-12, Q-L4-05'),
 ('TI-L4-37', 'ph_phaladesa', 'fail loud; make B.11 a real read or rename the flag', 'writer code', 'n', '-'),
 ('TI-L4-38', 'ph_phaladesa', 'align description / docstrings / model_policy literal / engine-vs-stored narration_status', 'registry + docs', 'n', '-'),
 ('TI-L4-39', 'ph_phaladesa', 'stored summary vs served view', 'design', 'n', 'Q-L4-16'),
 ('TI-L4-40', 'ph_phaladesa', 'delete the dead legacy domain map', 'writer code', 'n', '-'),
 ('TI-L4-41', 'ph_rectification', 'repair domain-slug and natal-index inputs; real `date_confidence`', 'writer code', 'y', 'Q-L4-17'),
 ('TI-L4-42', 'ph_rectification', 'clamp `confidence_*`; `calibrated` from the firewall count and fit', 'writer code (+ CHECK)', 'y', 'Q-L4-05'),
 ('TI-L4-43', 'ph_rectification', 'describe/serve as a stability map; `best_*` NULL when `win_margin` = 0', 'writer code + docs', 'y', 'Q-L4-17'),
 ('TI-L4-44', 'ph_rectification', 'builder grant; plan membership; `ga_dashas` edge; the `ka_kshetra` reader', 'migration + registry', 'n', 'Q-L4-04'),
 ('TI-L4-45', 'ph_rectification', 'remove personal constants from the engine module; ayanamsha vocabulary', 'writer code (engine)', 'n', '-'),
 ('TI-L4-46', 'ph_rectification', 'table-level provenance declaration for the candidate table; record input event ids and engine version on the best row', 'declaration + writer code', 'y', '-'),
 ('TI-L4-47', 'ph_muhurta', 'store the evaluated instant (UTC), natural-key effect', 'writer code', 'y', 'Q-L4-10'),
 ('TI-L4-48', 'ph_muhurta', 'drop declared-unread edges; `null_convention`', 'registry + declaration', 'n', '-'),
]

ORDER = ['ph_nimitta', 'ph_muhurta', 'ph_sodhana', 'ph_pratikara', 'ph_suddha_sodhana', 'ph_sankrama', 'ph_pramana', 'ph_phaladesa', 'ph_rectification']


def build(contents):
    byid = {c['id']: c for c in contents}
    L = []
    w = L.append
    cls_counts = collections.Counter()
    rows = []
    for a in ORDER:
        c = byid[a]
        cc = collections.Counter(g[2] for g in c['gaps'])
        cls_counts.update(cc)
        rb = any(fd['rebuild'].startswith('needs production rebuild') for fd in c['fds'])
        fix_classes = []
        for fd in c['fds']:
            t = fd['cls'].lower()
            for key, lab in (('data', 'data (rebuild)'), ('writer', 'writer code'), ('registry', 'registry/declaration'), ('declaration', 'registry/declaration'), ('migration', 'migration'), ('docs', 'docs')):
                if key in t and lab not in fix_classes:
                    fix_classes.append(lab)
        fix_classes = sorted(fix_classes)
        rows.append((a, c, cc, rb, fix_classes))
    total_gaps = sum(cls_counts.values())
    fresh()
    w('---')
    w('artifact: ASSET_ELEVATION_BRIEF_INDEX')
    w('layer: L4 Phala (ph_*)')
    w('version: "1.0-provisional"')
    w('status: "PROVISIONAL - until J1; may register gaps, may not certify; no SS answer recorded yet"')
    w('produced_by: track-a-l4 (worker under Exec Suvarna)')
    w(f'produced_on: {PRODUCED}')
    w('plan_item: A.L4 (briefs, dispositions, designs)')
    w(f'base_commit: "main {BASE}"')
    w('census_revision_used: "fresh census census_fresh/1e5781a/census_L4.json (2026-10-02T10:12:59+05:30, inspector 1e5781a, REGISTRY_REVISION 10; outside the repo) compared with the saved layers/census/census_L4.json (2026-09-30, 2a78ec64d); offline rollup under main asset_census.py REGISTRY_REVISION 15; NOT a live re-measure"')
    w('layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L4/L4_LAYER_INSTANCE_v1_0.md (1.1, PROVISIONAL)"')
    w('briefs: 9 (one per ph_* asset, `<ASSET_ID>_ELEVATION_BRIEF_v1_0.md` in this directory)')
    w('---')
    w('')
    w('# L4 Phala asset briefs - layer index (provisional)')
    w('')
    w('> **PROVISIONAL - until J1; may register gaps, may not certify.** Every figure is from a stated read-only query (suvarna_reader SELECTs on 2026-10-03; receipts in `_evidence/`), from the census, from the repository at main `' + BASE + '` (file:line), or from running the repository\'s own pure engine functions locally with no database (`_evidence/offline_checks.txt`). Nothing here certifies a gate or approves a disposition; every disposition and fix is a proposal under Track A section 10, no SS answer has been given, and every fix marked `needs production rebuild` or `needs migration` is a REVIEW item for Strategic Suvarna. Where a fact could not be determined the section 10 below says so.')
    w('')
    w('## 1 - What this index rests on, and what is stale')
    w('')
    w('- **Format:** the A.L0 brief format (approved by SS 2026-10-01, "the same format is used for L1-L5"; A.L0 INDEX section 10): frontmatter + sections 0-7, fix designs inside each brief, no separate dispositions file. Each brief carries one `DISPOSITION:` line and one `EVIDENCE_POINTER:` line in section 3 for machine extraction.')
    w('- **Scope:** the 9 `ph_*` assets (CLAUDE.md section E, registry `layer=phala`, all active, none `dead_flag`). The L5 `mi_*` assets are a separate lane (SS N-96).')
    w('- **Measured state:** fresh census (see frontmatter). Differences from the saved 2026-09-30 run: Build.dag FAIL x2 (new reads-match clause: `ph_nimitta`, `ph_rectification`), Null / Narr cells now exist, `Ldgr` unchanged. Offline rollup re-run under main REGISTRY_REVISION 15 (`_evidence/rollup_L4.json`).')
    w('- **Production reads (2026-10-03):** `asset_registry`, `asset_throughput`, `build_run_assets`, the ten `phala_*` tables, their upstreams (`kala_convergence`, `kala_bhavishya`, `kala_obstruction`, `bodha_discoveries`, `bodha_cdlm_cells`, `bodha_rm_remedy_prescriptions`, `life_events`, `mimamsa_predictions`, `chart_facts`, `chart_dashas`), `pg_constraint`, `has_table_privilege`. Counts are for the canonical chart unless marked "other chart" (counts only; no other chart\'s content is reproduced).')
    w('- **Last build and later code:** all nine assets were last built 2026-08-13 01:15-01:16 UTC (state `stale`). 16 distinct commits touching their writers/engines (`5f097e738` 2026-08-21; `ea2f8a49a` and the W3-3a..m fixes 2026-09-05/06; `b9d2d254b` Swiss-backend helper 2026-10-02) landed afterwards; the per-asset list is in each brief section 1.2. **The deployed writer version is not observable** (`built_against_writer_hash = unknown`).')
    w('- **Upstream is not what the stored rows were built from:** on the canonical chart `kala_convergence`, `kala_bhavishya` and `kala_obstruction` have 0 rows, `bodha_discoveries` and `bodha_cdlm_cells` ids were regenerated (2026-09-10), and `phala_anchors` has 4 of the 139 anchors the build record counts.')
    w('- **Evidence outside the repo:** `/Users/Dev/suvarna-evidence/A_L4/` (read-only receipts, scripts, rollup, offline checks). A compact copy of the scripts and receipts is committed beside this index in `_evidence/`.')
    w('')
    w('## 2 - Rollup counts')
    w('')
    disp = collections.Counter(byid[a]['disp_value'] for a in ORDER)
    w(f"**Dispositions proposed (9):** " + ', '.join(f"{k} {v}" for k, v in sorted(disp.items())) + '; consolidate 0, historical 0, retire 0, integrate 0, unresolved 0. Consolidation is raised only as a question (ph_sodhana + ph_suddha_sodhana, ph_phaladesa vs the serving capability, ph_muhurta vs the electional finder): T2 section 6.5 asks for the overlap investigation and the evidence supports opening it, not concluding it.')
    w('')
    w(f"**Gap rows across the 9 briefs ({total_gaps} rows):** " + ' - '.join(f"{k} {v}" for k, v in sorted(cls_counts.items(), key=lambda kv: -kv[1])) + '.')
    fm = fresh()
    cells = collections.Counter()
    for a in ORDER:
        for k, m in fm[a]['measurements'].items():
            cells[m['v']] += 1
    w('')
    w(f"**Fresh-census cells over the nine assets ({sum(cells.values())}):** " + ' - '.join(f"{k} {v}" for k, v in sorted(cells.items(), key=lambda kv: -kv[1])) + '.')
    fails = collections.Counter()
    for a in ORDER:
        for k, m in fm[a]['measurements'].items():
            if m['v'] == 'FAIL':
                fails[k] += 1
    w('FAIL by criterion: ' + ' - '.join(f"{k} {v}" for k, v in sorted(fails.items(), key=lambda kv: -kv[1])) + '.')
    rr = roll()['runs']['fresh_2026-10-02_1e5781a']['rollup']
    gates = ['Ldgr', 'Idem', 'Earn', 'Null', 'Vocab', 'Carr', 'Narr', 'Dens', 'Build']
    w('')
    w('**Nine-gate cells, offline rollup of the FRESH census under main\'s rules (assets of 9; not a re-measure, not a certification):**')
    w('')
    w('| gate | ' + ' | '.join(gates) + ' |')
    w('|---|' + '|'.join(['---'] * len(gates)) + '|')
    cellsr = []
    for g in gates:
        c = collections.Counter(rr[a][g]['v'] for a in ORDER if g in rr[a])
        cellsr.append(' - '.join(f"{k} {v}" for k, v in sorted(c.items())))
    w('| rollup | ' + ' | '.join(cellsr) + ' |')
    rs = roll()['runs']['saved_2026-09-30']['rollup']
    w('')
    cs = []
    for g in gates:
        c = collections.Counter(rs[a][g]['v'] for a in ORDER if g in rs[a])
        cs.append(' - '.join(f"{k} {v}" for k, v in sorted(c.items())))
    w('Same rules over the SAVED 2026-09-30 census: ' + '; '.join(f"{g} {x}" for g, x in zip(gates, cs)) + '.')
    w('')
    w('**What the gates miss (the point of this layer\'s briefs):** Build.completion reads PASS for `ph_pratikara` (536 = 536) and `ph_phaladesa` (13 = 13), and the integrity SQL of `ph_sodhana`, `ph_suddha_sodhana`, `ph_sankrama`, `ph_muhurta` returns true, on rows that are empty programmes, dangling references, an unassessed "clean" and a summary of 139 anchors when 4 exist. The findings in the briefs section 1.4 come from reading values against the claim each flag makes (CLAUDE.md N.7, N.8), not from the census.')
    w('')
    w('## 3 - Assets x disposition x gaps x fix class x rebuild')
    w('')
    w('Columns: **real** = shortfall in code, rows, registry row or served surface; **stored** = real-stored (current code already fixes it; cured by a rebuild); **design** = needs SS or acharya; **detector** = absent or open instrument; **other** = history + information + opportunity; **rebuild** y = a fix needs a production rebuild.')
    w('')
    w('| asset | disposition | real | stored | design | detector | other | fix class | rebuild | risk | shared fixes |')
    w('|---|---|---:|---:|---:|---:|---:|---|---|---|---|')
    for a, c, cc, rb, fcs in rows:
        other = cc.get('history', 0) + cc.get('information', 0) + cc.get('opportunity', 0)
        w(f"| [{a}]({a}_ELEVATION_BRIEF_v1_0.md) | {c['disp_value']} ({c['disp_code'].split('(')[1].split(')')[0]}) | {cc.get('real', 0)} | {cc.get('real-stored', 0)} | {cc.get('design', 0)} | {cc.get('detector', 0)} | {other} | {'; '.join(fcs)} | {'y' if rb else 'n'} | {c['risk'].split(' ')[0]} | {', '.join(x[0] for x in c['cfs'])} |")
    w('')
    w('**Rebuild needed (y):** ' + ', '.join(a for a, c, cc, rb, f in rows if rb) + '. All nine are `stale`; the rebuild is one chain (CF-L4-01), not nine independent ones.')
    w('')
    w('## 4 - Cross-asset fixes, ordered by value for J1 (Tracks I and B)')
    w('')
    w('Order rule (A.L0): assets served x gate movement, then tier-independence and absence of a rebuild first. CF-L4-02 and CF-L4-07 come first because they unblock or cost nothing; CF-L4-01 follows because it cannot be accepted before them. Each shared fix is designed once here; the briefs say how it applies.')
    w('')
    for i, cf in enumerate(CFS, 1):
        w(f"### {i}. {cf['id']} - {cf['title']}")
        w('')
        w(f"- **Why this rank:** {cf['why']}")
        w(f"- **Gate / assets:** {cf['gate']}")
        w(f"- **Evidence:** {cf['evidence']}")
        w(f"- **Design:** {cf['design']}")
        w(f"- **Failing-first test and mutation:** {cf['test']}")
        w(f"- **Blast radius:** {cf['blast']}")
        w(f"- **Rebuild:** {cf['rebuild']}")
        w(f"- **Fix class:** {cf['cls']}; **buildable before J1:** {cf['j1']}")
        w(f"- **Decision:** {cf['decision']}")
        w('')
    w('## 5 - Rebuild consequences Track B needs per asset')
    w('')
    w('Facts found while reading the writers (N-29 impact statement inputs). The canonical plan\'s waves 7-11 are `ph_nimitta` | `ph_muhurta ph_pratikara ph_sankrama ph_sodhana` | `ph_suddha_sodhana` | `ph_pramana` | `ph_phaladesa`; `ph_rectification` is absent.')
    w('')
    w('- **`ph_nimitta` (wave 7):** rebuilding before `ka_sangam` / `ka_bhavishya_lekha` yields discovery-only anchors (emulation: about 2). `anchor_id` hashes the window and tier, so discovery anchors move with every L2 rebuild and with the calendar. Its integrity SQL cannot pass while 135 frozen predictions dangle (CF-L4-02a).')
    w('- **`ph_muhurta` (wave 8):** needs a working Swiss ephemeris path in the build environment for the live tara/chandra factor (otherwise 0.5/0.5 and a NULL verdict); stored `window_start` is a naive 06:00 labelled UTC.')
    w('- **`ph_pratikara`, `ph_sankrama` (wave 8):** depend on regenerated `kala_obstruction` and `bodha_cdlm_cells`; `ph_pratikara` with 0 obstructions writes 0 rows (dormant, floor 536). Cost tiering and the Jupiter fallback must be fixed before the first non-empty build.')
    w('- **`ph_sodhana` (wave 8):** an empty result on a small chart is not a clean result until FD-1 lands.')
    w('- **`ph_suddha_sodhana` (wave 9), `ph_pramana` (wave 10), `ph_phaladesa` (wave 11):** pure functions of their siblings; `ph_pramana` must be chart-scoped before any second-chart rebuild; `ph_phaladesa` narration must be fixed first. The other built chart\'s rows were produced by the same older code and carry the same defects (counts only checked).')
    w('- **`ph_rectification`:** needs the builder grant; not in the plan; its fit will become non-zero only after the input repairs and an acharya review of the rule.')
    w('- **L5:** `mi_bhavisya` deletes only pending/due predictions (rebuild-plan evidence); the 135 dangling predictions are not touched by an L4 rebuild, which is exactly why Q-L4-01/02 must be answered first.')
    w('')
    w('## 6 - Dispositions that differ from the layer instance (section 3.2), and who approves')
    w('')
    w('The layer instance carries the companion register\'s provisional codes (T2c, status PROPOSED) as non-verdicts. This index proposes (Track A section 10; approver Steward, SS for output changes):')
    w('')
    w('| asset | T2c provisional code | this index | reason |')
    w('|---|---|---|---|')
    t2c = {'ph_nimitta': 'P/E/I/Q', 'ph_muhurta': 'P/I/Q/E', 'ph_pratikara': 'P/I/Q', 'ph_sankrama': 'P/I/Q', 'ph_sodhana': 'P/I/Q', 'ph_suddha_sodhana': 'P/I/Q', 'ph_rectification': 'P/E/Q/H', 'ph_pramana': 'P/E/I/Q', 'ph_phaladesa': 'P/I/Q'}
    reason = {
     'ph_nimitta': 'qualify - spine with real consumers; several emitted values are constants/proxies, stored state stale and orphaned',
     'ph_muhurta': 'qualify - keep the row set, qualify the muhurta claim (Q-L4-10)',
     'ph_pratikara': 'enrich - never produced a non-empty programme; cost tiering would label all remedies free',
     'ph_sankrama': 'enrich - 5-fold fan-out, unmeasured asymmetry shown as 0, constant cascade depth',
     'ph_sodhana': 'enrich - detectors silent below 5 anchors, mismatched ceiling; keep the firewall',
     'ph_suddha_sodhana': 'qualify - `clean` echoes upstream silence; approval has no durable home',
     'ph_rectification': 'qualify (not H): reads by L3 and a real stability map; scoring half never non-zero',
     'ph_pramana': 'keep - small and structural; one isolation must-fix',
     'ph_phaladesa': 'qualify - truthfulness is a function of the other eight; narration defects'}
    for a in ORDER:
        c = byid[a]
        w(f"| {a} | {t2c[a]} | {c['disp_value']} | {reason[a]} |")
    w('')
    w('No asset receives R (T2 section 10.1 l.541: "No asset receives unconditional R in this master"), H, or C: the consolidation candidates are questions Q-L4-10, Q-L4-12, Q-L4-16.')
    w('')
    w('## 7 - Questions for Strategic Suvarna (and the acharya): OPEN')
    w('')
    w('No question has been answered. The decider column says who can answer; "acharya" means a Jyotish judgment, not an engineering one. Recommendations are this lane\'s reading and bind nobody.')
    w('')
    w('| id | topic | question | recommendation | decider | assets |')
    w('|---|---|---|---|---|---|')
    for q in QS:
        w(f"| {q[0]} | {q[1]} | {esc(q[2])} | {esc(q[3])} | {q[4]} | {q[5]} |")
    w('')
    w(f"**{len(QS)} questions.** The five that block the rebuild: Q-L4-01 to Q-L4-04 and Q-L4-12 (not-assessed). The ones that change what a reader may believe about a stored number: Q-L4-05, Q-L4-07, Q-L4-08, Q-L4-17.")
    w('')
    w('## 8 - Track I items arising')
    w('')
    w('Id, asset(s), fix, class, rebuild needed, source question. `y` items are REVIEW items for SS at their level. Fix designs remain in the per-asset briefs (section 4) and section 4 here.')
    w('')
    w('| id | asset(s) | fix | class | rebuild | from |')
    w('|---|---|---|---|---|---|')
    for t in TIS:
        w('| ' + ' | '.join(esc(x) for x in t) + ' |')
    cc = collections.Counter(t[3].split(' ')[0] for t in TIS)
    w('')
    w(f"**{len(TIS)} items.** Rebuild y: " + ', '.join(t[0] for t in TIS if t[4] == 'y') + '.')
    w('')
    w('## 9 - Decisions applied')
    w('')
    w('None. SS has not answered the A.L4 questions. The A.L0 rulings that bear on L4 and are carried as PROVISIONAL inputs, not applied: Q3 (`classical_tradition` is not provenance; `attribution_state`) bears on `ph_pratikara.source_id`; Q11 (Build.history window) bears on every Build.history PARTIAL here (0-3 errors and 9 aborts each, every latest run complete); Q12 (Idem claim for upsert writers) does not apply (all nine are delete-then-insert).')
    w('')
    w('### 9.1 - Static Dens re-measure')
    w('')
    d = roll()['runs']['fresh_2026-10-02_1e5781a']['dens_static']
    w('Main\'s `capability_scan` + `_grade_dens` run offline over the nine assets with the fresh census\'s column lists (`_evidence/offline_rollup_L4.py`): ' + ', '.join(f"{a} {d[a]['now']}" for a in ORDER) + '. Same as the fresh census (FAIL 6, NO_DETECTOR 3); the three NO_DETECTOR cells are the scanner desync on two `platform-mcp` register files (CF-L4-11).')
    w('')
    w('## 10 - What could not be determined')
    w('')
    for t in [
        '**Whether `ph_nimitta`\'s stored `anchor_id`s equal their computed identity** (integrity clause b): `suvarna_reader` has no EXECUTE on `phala_anchor_identity()` or `phala_anchor_identity_namespace()`; the whole registry SQL cannot be run by the reader. Clause (a) was evaluated piecewise.',
        '**Which writer version production runs** (`built_against_writer_hash = unknown` on all nine); no writer was run, so the post-fix outputs quoted are from local calls to the repository\'s pure functions, not from production.',
        '**Whether the build environment can reach the live Moon-strength path** (`SE_EPHE_PATH`, N-28) for `ph_muhurta`, and whether PyJHora\'s ascendant agrees with the Swiss backend below sign level for `ph_rectification` (sign-level agreement at offset 0 was checked).',
        '**How many anchors a rebuild yields once L3 is rebuilt**: only the discovery-only case was emulated (about 2).',
        '**Whether the 135 anchors were removed by the FK cascade**: consistent with the FK catalogue and empty parents, but no delete event was read (TG-L4-023).',
        '**Whether the 8 `life_event_miss` rows on the other chart came from the unscoped read or from the old default** (the stored rows cannot tell); the code path is certain.',
        '**The producer of `bodha_contradictions`** (no registry `target_table` equals it), so `ph_nimitta`\'s edge for it cannot be classified.',
        '**Served behaviour** beyond static scans: no tool was called; density and tier carriage are the census\'s static readings.',
        '**Anything on L5 or on the 12 `mi_*` assets**: out of scope (N-96).',
    ]:
        w('- ' + t)
    w('')
    w('## 11 - Notes on method and path')
    w('')
    w('- **Path:** `00_ARCHITECTURE/briefs/suvarna/layers/L4/assets/<ASSET_ID>_ELEVATION_BRIEF_v1_0.md` (Track A section 8; revalidation bumps to v1.1). Fix designs live inside each brief (section 4).')
    w('- **Gap ids:** `ph_<asset>-Gnn` are this lane\'s; the ledger ids (`ph_<asset>-<Criterion>`) are listed in each brief\'s frontmatter from the census ledger copy `census_fresh/1e5781a/main_ledger.jsonl`, which is not on main.')
    w('- **Risk class:** R1 declaration/doc/test only; R2 writer code with no schema or served-number change; R3 schema, rebuild-visible or cross-asset semantics; R4 needs an SS ruling on layer doctrine or touches frozen L5 history.')
    w('- **Honesty rules applied:** no invented counts (each comes from a stated query or file:line); the native\'s birth data is not reproduced anywhere (the engine module that embeds it is cited by line only); other charts appear as counts only; nothing was fixed, nothing was written to production.')
    w('- **Frozen orchestrator:** every fix goes in an asset, a registry row or a declaration, never in the orchestrator (T4 4.2); the one place an orchestrator behaviour matters (a false post-write integrity check rolls the writer back, `asset_runner.py:1200-1210`) is used as written.')
    return '\n'.join(L)
