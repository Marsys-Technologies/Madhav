---
version: 1.1
status: CURRENT
lane: TI-i-fl2-003
item: TI-L2-20 (Q-L2-16 reader trace; gate for TI-L2-32)
branch: suvarna/land/TI-i-fl2-003
basis: origin/main adb0db29d (code read); production DB read 2026-10-03, reader-only SELECT, chart 482012f1
changelog:
  - 1.1 -- addendum after independent review: the registry-stored integrity_check_sql gates (R-14) and two pass-through projections (R-15) were missing from the reader list; 'every reader' softened to 'every reader found'. Conclusion unchanged.
  - 1.0 -- trace of every reader of bodha_msr_signals.valence on main; no reader breaks on NULL; one served summary changes shape. Evidence only.
---

# TI-L2-20: every reader found of `bodha_msr_signals.valence`, and what NULL does to each

SS ruling Q-L2-16 (N-59): "trace every reader of `valence` first; if any reader breaks on NULL,
ASK SS before coding". The change being gated is TI-L2-32: keep `valence` where a category or
keyword rule matched (a matched neutral too) and store NULL where nothing matched and the code
falls through to `'neutral'` (`bo_laksana` and `bo_laksana_rerank`, one rebuild).

## Answer

**No reader found breaks on NULL, so no ASK is triggered by breakage** (readers R-1 to R-15; R-14 is a gate that stops binding on NULL rows, see the addendum). Every Python and SQL reader found is
NULL-safe, counts NULL together with neutral, or (the `bo_laksana` closed-set gate, R-14a) passes without checking the NULL rows; the TypeScript readers pass the value through as
`string | null`. **One served field changes meaning, and one registry gate covers less,** and SS should know before TI-L2-32 lands: the per-entity
`dominant_valence` in the hierarchical profiles (`orientation`) is a most-frequent-bucket count that
skips NULL, so it would stop saying `neutral` for entities whose rows become NULL and could name a
non-neutral valence from the few assessed rows (see R-7).

## Schema facts (production, 2026-10-03)

* `bodha_msr_signals.valence` and `valence_source` are `text`, **nullable**, no default, and **no
  CHECK constraint** mentions `valence` on this table (the only valence CHECKs in the database are on
  `chart_vichara.vichara_family`, `ka_gochara_relationship_record` and `ka_gochara_eval_window`,
  none on MSR). So storing NULL needs no migration.
* The rerank guard `public.l2_data_plane_guard_active_mutation` lists `valence` and `valence_source`
  among the six columns `bo_laksana_rerank` may update, so a rerank that sets `valence` to NULL
  passes the guard.
* Live canonical chart, by producer (`valence` / `valence_source` / rows):
  `bo_laksana` benefic ga_vichara_v1 2,371; benefic keyword_heuristic_v1 3,033; malefic ga_vichara_v1
  2,047; malefic keyword_heuristic_v1 6,581; mixed ga_vichara_v1 1,632; **neutral keyword_heuristic_v1
  34,865**. The five satellite emitters (`bo_arudha`, `bo_nakshatra_semantic`, `bo_special_lagna`,
  `bo_sudarshana`, `bo_vargottama_dhana`) use `categorical_deterministic_v1` / `valence_doctrine_v1`
  and are not part of TI-L2-32. So the change can touch **at most 34,865 of the 50,678 rows** (the
  exact number depends on how many of those neutrals were "matched neutral"; the writers decide).

## Readers (file:line at origin/main adb0db29d) and the effect of NULL

| # | reader | what it does with `valence` | effect of NULL |
|---|---|---|---|
| R-1 | `pipeline/orchestrator/writers/bo_chart_gestalt.py:242-246` | `COUNT(*) FILTER (WHERE valence = 'neutral' OR valence IS NULL) AS neutral_count`; benefic/malefic/mixed counted by equality | none: NULL already counts as neutral, so `neutral_count` is unchanged |
| R-2 | `bo_chart_gestalt.py:211, 273` (domain verdict map) | selects `valence`; stores `str(ds.get("valence") or "") or None` | NULL stays NULL |
| R-3 | `bo_chart_gestalt.py:330, 355, 420-428` (malefic list, benefic list, contested-domain HAVING) | equality on `'malefic'` / `'benefic'` only | none: neutral and NULL are both outside these filters |
| R-4 | `pipeline/orchestrator/writers/bo_sangati.py:204, 237` | `str(signal.get("valence") or "").lower() in {"malefic","mixed","antagonistic"}` | none: NULL reads as "" and is not a qualified contradiction, same as neutral |
| R-5 | `pipeline/orchestrator/writers/ka_yojaka.py:82, 215, 922-925` (Kāla) | copies `valence` into the signal dict; `signal_valence` is `str(v) if v is not None else None` | NULL passes through as NULL (explicit None branch). Kāla file: read only, not touched |
| R-6 | `src/lib/retrieval/spine/compute_spine_bundle.ts:185`, `spine/types.ts:9` | `valence: string \| null` (already typed nullable; test fixture uses `valence: null`) | none |
| R-7 | `src/lib/retrieval/ranking/composite_ranker.ts:83, 613-641` (`buildHierarchicalProfiles`; served via `src/lib/retrieval/orientation.ts:50, 228`) | `if (r.valence) valenceCounts[r.valence] += 1`, then `dominant_valence` = the most frequent bucket per entity profile | **NULL rows are skipped, so an entity whose rows are mostly keyword-fallthrough neutral would stop reporting `dominant_valence: "neutral"`: the dominant bucket becomes the largest non-neutral one (benefic/malefic/mixed), or `null` if every row is NULL.** A served-output change, not a break; it can read as a stronger claim than before ("dominant: malefic" over a handful of assessed rows among many unassessed ones) |
| R-8 | `src/lib/retrieval/registry/layers/register_d9_judgment.ts:1466-1472` | `WHERE valence IN ('malefic','mixed')` (adverse-valence layer) | none: neutral and NULL are both excluded |
| R-9 | `src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts:100, 142`, `query_domain_reading.ts:206, 427` | projection of the column in the served rows | served field is `null` instead of `"neutral"` for those rows (a visible value change; consumers must read it as "no rule matched", which `valence_source` already labels) |
| R-10 | `src/lib/retrieval/registry/knowledge/source_query_availability.ts:3216, 3807, 3925, 3971` | `SELECT ... valence ... LIMIT 0` availability probes | none (probes only, zero rows) |
| R-11 | `public.mv_msr_top_signals_per_chart` (materialized view) | passes `valence` through for `top_k_salience_rank <= 100` | none (plain column; stale until refreshed) |
| R-12 | `public.l2_data_plane_guard_active_mutation` | lists `valence` among the rerank's six updatable columns | none (see above) |
| R-13 | `brahmagyan/bodha/l2_embeddings.py:124` (`sig.get("valence", "context-dependent")`) | builds the embed text `"{domain} | {valence} | ..."` | a NULL `valence` read from a dict that has the key would print `None` into the text. **Legacy standalone script**: not imported by any module and not a registered asset (only two governance allowlists name it); not on any build path. The live embedding input is `bo_samskara._build_input_summary`, which does not read `valence` |

Not readers of this column despite the name: `bo_pramana_mapa.py:595` (`bodha_cgm_edges.valence`),
`bo_karanajala.py` edge valence (`bodha_cgm_edges`), `query_mechanisms.ts` / `register_p1_aliases.ts`
(`bodha_mechanisms.valence`), `reading_checklist.ts` (gochara windows), `traverse_chart_graph.ts` (edges).

## What this does not cover (stated so nobody reads it as complete)

* The stored dossier slices (`platform-mcp/src/resources/vidhi/dossier_slices/{career,wealth}_*.json`)
  and the eval harness runs (`evals/omega7/harness_runs/*.json`) hold copies of earlier served rows;
  they are static files and were not individually checked for a NULL-sensitive consumer.
* Readers outside this repository (hosted clients of the served tools) cannot be traced from here;
  R-7 and R-9 are the two places they could see a difference.
* The reader list is by text search for `valence` in files that also name `bodha_msr_signals`
  (plus the database's own views, functions and, after the addendum, the registry's `integrity_check_sql`). A reader that builds the column name dynamically
  would be missed; none was seen.

## Recommendation for TI-L2-32 (for SS; nothing is built here)

No ASK is needed for breakage. SS may still want to decide R-7/R-9: either accept that the served
`dominant_valence` and the served `valence` field show NULL / the non-neutral mode for "no rule
matched" rows (with `valence_source` already naming the computation), or have
`buildHierarchicalProfiles` count NULL as its own `unassessed` bucket (and not let a small assessed
minority win) in the same PR as the writer change. That is a served-surface edit and so a
regeneration of the capability census; it is not part of this note.

## Addendum (v1.1): readers the first pass missed

Found by the independent review of this PR; verified against the live registry and the migration files at origin/main adb0db29d.

| # | reader | what it does with `valence` | effect of NULL |
|---|---|---|---|
| R-14a | `asset_registry.integrity_check_sql` for `bo_laksana` (migration `931_nirmana_l2_bo_laksana_integrity_check.sql:100`, live) | `NOT EXISTS (SELECT 1 FROM laksana WHERE valence NOT IN ('benefic','malefic','neutral','mixed'))` | **not a failure, but the gate stops binding on NULL rows**: `NULL NOT IN (...)` is NULL, so the row is never counted as a violation. TI-L2-32 would make up to 34,865 rows invisible to this closed-set check. The gate passes, it just no longer checks those rows; SS should know before relying on it |
| R-14b | `bo_laksana_rerank` (migration `932_..._rerank_integrity_check.sql:151`, live) | closed-set check limited to `valence_source = 'ga_vichara_v1'` and written `valence IS NULL OR valence NOT IN (...)` | unaffected: it binds only judged rows, which TI-L2-32 does not NULL, and it fails on NULL there by design. Rows that fall to keyword fallthrough carry `keyword_heuristic_v1` and are outside its scope |
| R-14c | `bo_arudha` (migration `710_bo_arudha_integrity_check.sql:83-92`, live) | per-`signal_type_id` closed sets on arudha rows | unaffected by TI-L2-32 (arudha rows are `categorical_deterministic_v1` / `valence_doctrine_v1`); same `NOT IN` NULL behaviour if a NULL ever appeared |
| R-14d | `bo_yantra_mechanism` (719:62-66) and `ga_vichara` | closed sets on `bodha_mechanisms.valence` / `chart_vichara` | different tables; not readers of `bodha_msr_signals.valence`; listed because the registry text search finds them |
| R-15 | `platform-mcp/src/tools/register_p1_synthesis.ts:803-806` and `platform/src/lib/retrieval/registry/layers/L2_bodha/query_ucd.ts:323-328` | pass-through projections of the column in served rows | same class as R-9: served field is `null` instead of `"neutral"` for rows that become NULL |

Registry check (production, 2026-10-03): `integrity_check_sql` mentions `valence` for exactly five assets: `bo_arudha`, `bo_laksana`, `bo_laksana_rerank`, `bo_yantra_mechanism`, `ga_vichara`; the only one containing `valence IS NULL` is `bo_laksana_rerank`.

Consequence for TI-L2-32: the conclusion stands (nothing found breaks). One more item belongs in the same change as the writer edit: the `bo_laksana` closed-set gate (R-14a) should be rewritten to say what it means for NULL (for example `valence IS NOT NULL AND valence NOT IN (...)` for rows with a rule source, and `valence IS NULL` only where `valence_source` says no rule matched), otherwise it silently covers less. That is a registry migration and is not built here.
