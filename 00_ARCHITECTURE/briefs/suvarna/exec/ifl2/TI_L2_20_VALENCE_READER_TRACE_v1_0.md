---
version: 1.0
status: CURRENT
lane: TI-i-fl2-003
item: TI-L2-20 (Q-L2-16 reader trace; gate for TI-L2-32)
branch: suvarna/land/TI-i-fl2-003
basis: origin/main adb0db29d (code read); production DB read 2026-10-03, reader-only SELECT, chart 482012f1
changelog:
  - 1.0 -- trace of every reader of bodha_msr_signals.valence on main; no reader breaks on NULL; one served summary changes shape. Evidence only.
---

# TI-L2-20: every reader of `bodha_msr_signals.valence`, and what NULL does to each

SS ruling Q-L2-16 (N-59): "trace every reader of `valence` first; if any reader breaks on NULL,
ASK SS before coding". The change being gated is TI-L2-32: keep `valence` where a category or
keyword rule matched (a matched neutral too) and store NULL where nothing matched and the code
falls through to `'neutral'` (`bo_laksana` and `bo_laksana_rerank`, one rebuild).

## Answer

**No reader breaks on NULL, so no ASK is triggered by breakage.** Every Python and SQL reader is
NULL-safe or counts NULL together with neutral; the TypeScript readers pass the value through as
`string | null`. **One served summary changes shape** and SS should know before TI-L2-32 lands: the
`valence_counts` tally in the ranked-signal summary would stop showing a `neutral` bucket for rows
that become NULL (see R-7).

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
| R-7 | `src/lib/retrieval/ranking/composite_ranker.ts:83, 618` | `if (r.valence) valenceCounts[r.valence] += 1` -- builds the `valence_counts` tally of the ranked-signal summary | **NULL rows are skipped, so the summary's `neutral` count would fall by the number of rows that become NULL** (served-output change, not a break) |
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
  (plus the database's own views and functions). A reader that builds the column name dynamically
  would be missed; none was seen.

## Recommendation for TI-L2-32 (for SS; nothing is built here)

No ASK is needed for breakage. SS may still want to decide R-7/R-9: either accept that the served
`valence_counts` tally and the served `valence` field show NULL for "no rule matched" (with
`valence_source` already naming the computation), or have the tally count NULL as its own
`unassessed` bucket in the same PR as the writer change. That is a served-surface edit and so a
regeneration of the capability census; it is not part of this note.
