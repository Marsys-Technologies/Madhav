---
version: 1.0
status: DRAFT_FOR_SS_REVIEW
lane: TI-i-fl2-007
item: TI-L2-19 (Q-L2-06 design REVIEW; gate for TI-L2-30)
branch: suvarna/land/TI-i-fl2-007
basis: origin/main 7773df1f9 (bo_bimba.py / bo_karanajala.py unchanged since adb0db29d); production DB read 2026-10-03, reader-only SELECT, chart 482012f1
changelog:
  - 1.0 -- design REVIEW for SS: classification of the non-name yoga/dosha node subjects and the id-change list. Document only; nothing is coded.
---

# TI-L2-19: yoga/dosha node subjects -- classification and id-change list (design REVIEW for SS)

Ruling Q-L2-06 (N-59): do the name fix and the identity fix together in the one `bo_bimba` rebuild (identity =
`signal_type_id` + configuration key), and BEFORE coding classify the non-name subjects: "a real yoga with a bad
name gets its catalogue name; a flag, timestamp or number that is not a yoga gets NO yoga node". This is that
classification and the id-change list. SS approves it (or changes it) before TI-L2-30 is coded. No code, data or
registry change is made here.

## 1. What is live (chart 482012f1, production, 2026-10-03)

* 100 yoga/dosha signals (74 yoga, 26 dosha); 85 yoga/dosha nodes (69 yoga, 16 dosha), 17 per ayanamsha.
* The node subject today is `<class>:<slug of the first of fact_value_text / yoga_name / dosha_name / name / label,
  else signal_type_id>` (`bo_bimba.py:252-271`); node id = `uuid_v5(chart, ayanamsha, node_type, node_subject)`
  (`bodha_cgm_node_identity`, migration 714). Of the 17 per ayanamsha, 10 are real catalogue names and 7 are not.
* 15 signals have no node of their own because their subject collides (3 per ayanamsha).
* **No edge attaches to any yoga/dosha node**: 0 edges of type `yoga_member` on the chart, and every yoga/dosha
  node has `degree_in = degree_out = 0`. So re-keying these nodes re-wires nothing today (the reason there are no
  membership edges was not traced here).

## 2. Classification of the signal types behind the subjects

All 13 yoga/dosha `signal_type_id`s on the chart, the subject each gives today, and the proposed disposition
(5 signals each, one per ayanamsha, unless stated):

| signal_type_id | subject today | what the signal is | proposed disposition |
|---|---|---|---|
| `yoga_label:yoga_name` | `yoga:<name>_yoga` (7 names: shoola, gola, yuga, kedara, vasi, anapha [4 signals, one ayanamsha lacks it], sasa) | a catalogue yoga, named | **keep a yoga node**, label = catalogue name |
| `panchanga_special_yoga_combinations:combination_name` | `yoga:panchaka` | a catalogue combination, named | **keep a yoga node** |
| `panchanga_yoga:name` | `yoga:<panchanga yoga name>` | the birth-time panchanga yoga, a catalogue name | **keep a yoga node** |
| `dosha_label:dosha_name` | `dosha:manglik_dosha` (5), `dosha:kemadruma_dosha` (1) | a catalogue dosha, named | **keep a dosha node** |
| `kendradhipati_dosha:doshas_kendradhipati` | `dosha:afflicted` (10) / `dosha:unafflicted` (10) | one signal **per graha** (`planet` in the configuration; `ruled_houses`; `kendradhipati_active` true or false; `doctrine_status = PROPOSED`) | **split by `kendradhipati_active`**: the `true` rows ("afflicted", 2 per ayanamsha) are instances of a real dosha with a bad name: one dosha node each, label from the catalogue name plus the graha, keyed by `planet`; the `false` rows ("unafflicted") assert the dosha does NOT apply and get **no node** (a Dosha node for an absent dosha would read as a finding). SS call, see 5.1 |
| `graha_yoga_karaka_flag:is_yoga_karaka` | `yoga:false` | the flag `is_yoga_karaka = false` for a graha | **no node** (named by SS as the example) |
| `panchanga_yoga:inauspicious_flag` | `yoga:false` | the flag `inauspicious_flag = false` | **no node** (named by SS) |
| `panchanga_special_yoga_combinations:active_at_birth_flag` | `yoga:true` | the flag `active_at_birth_flag = true` | **no node** (flag) |
| `panchanga_yoga:end_iso` | `yoga:<ISO timestamp slug>` | the end time of the panchanga yoga | **no node** (timestamp) |
| `panchanga_yoga:number` | `yoga:panchanga_yoga_number` | the yoga's ordinal number | **no node** (number) |
| `panchanga_special_yoga_combinations:constituent_facts_jsonb_atomic` | `yoga:panchanga_special_yoga_combinations_constituent_facts_jsonb_atomic` | the combination's constituent-fact payload | **no node** (a payload column; the combination itself is the `combination_name` node) |

The seven non-name subjects the ruling counted are exactly: `true`, `false`, the timestamp, `panchanga_yoga_number`,
the `constituent_facts_jsonb_atomic` slug, `afflicted`, `unafflicted`. Nothing in the 13 types needs a yoga node
named by something other than a catalogue name, so no new catalogue lookup is required.

The signals without a node stay as MSR signals (they are not deleted); they simply stop pretending to be yogas in the
graph. Their facts remain reachable through `bodha_msr_signals`.

## 3. Numbers after the change (canonical chart)

| | today | after |
|---|---|---|
| yoga/dosha nodes per ayanamsha | 17 (10 catalogue names + 7 non-name subjects) | 12 (10 catalogue names + 2 afflicted-graha dosha nodes) |
| yoga/dosha nodes on the chart | 85 | 60 |
| signals with no node by design | 0 (15 collide onto a shared node) | 8 per ayanamsha = 40: six one-per-ayanamsha types (`is_yoga_karaka`, `inauspicious_flag`, `active_at_birth_flag`, `end_iso`, `number`, `constituent_facts_jsonb_atomic`) plus 2 `unafflicted` graha signals |

The ruling's earlier estimate "85 to up to 100 nodes" assumed every signal would get a node; under this classification the
node count goes down to 60, not up.

## 4. Id-change list

Node id depends on `(chart, ayanamsha, node_type, node_subject)`. Two ways to meet "identity = `signal_type_id` +
configuration key":

* **Option B (the ruling's wording)**: `node_subject = <class>:<signal_type_id>:<configuration key value>`, where the
  configuration key is `fact_value_text` / `yoga_name` / `dosha_name` for the named types and `planet` for
  kendradhipati. **All 60 nodes get new ids** (50 catalogue-name nodes and 10 kendradhipati graha nodes, 12 per
  ayanamsha). 85 old ids are retired: 35 of them (the non-name nodes) disappear, 50 re-key. Two signal types that happen
  to carry the same catalogue name can no longer collide.
* **Option A (smaller churn, same rule for what gets a node)**: keep `<class>:<slug of catalogue name>` for the 50
  catalogue-name nodes and add the graha for kendradhipati. The 50 existing ids stay; 35 retire; 10 are new. Risk: two
  signal types carrying one catalogue name would collide again (none do today: the 50 names are distinct within an
  ayanamsha), which is the defect class being removed.

Either way, edges: no live edge attaches to these nodes (section 1), so no edge id moves on this chart. The code
that must follow (TI-L2-30): `bo_karanajala.py:927-941` (`_yoga_node_subject` lookup for membership edges, which would
simply find no node for the 10 no-node types), `bo_bimba.py` (`yoga_best` dedup, the label and the citation
`"{Class} node: {name}"` at `:523`).

## 5. Decisions needed from SS

1. **Kendradhipati `unafflicted` rows**: no node (proposed). The alternative, a node that says the dosha is absent, is
   a negative finding presented as a Dosha node. Also `doctrine_status = PROPOSED` on all 20 signals: the 10 afflicted
   nodes inherit a proposed (not ratified) doctrine; say so in the node, or hold them out until ratified.
2. **Option A or B** (section 4). B follows the ruling's words; A avoids re-keying 50 catalogue-name nodes. Because no
   edge is attached today the extra cost of B on this chart is the id churn only; on a chart whose membership edges
   exist it would also re-wire them.
3. **Flag types stay MSR signals only**: confirm that nothing downstream wants a graph node for `is_yoga_karaka` or
   `active_at_birth_flag` (a yoga-karaka graha is a graha property; `bo_chart_gestalt` and `bo_pramana_mapa` do not read
   yoga nodes by subject).

## 6. Things that move with TI-L2-30 (so the review is not read as a one-file change)

* `tests/l2/test_bo_wp23_graph_structure.py:223-263` pin the current `yoga_node_subject` behaviour.
* The E6 narration test `platform/scripts/governance/__tests__/test_e6_1_declarations.py` cites `bo_bimba.py`'s
  `_yoga_config_name` (cited line 252, with the source head `def _yoga_config_name(cfg: d`, around `:1417`) and asserts
  the node-citation site `f'{sig_class.capitalize()} node: {name}'` at line 523 (around `:2346-2349`). Any edit to those
  functions needs the citations re-derived from the final source (never by offset), not hand-edited.
* The fingerprint contract of `bo_bimba` / `bo_karanajala` (node natural key) and the Q-L2-15 (2) node move to
  `bo_bimba` ride the same change.
* Rebuild consequence per N-59: this is a batched item, one canonical L2 rebuild; `bo_karanajala`, `bo_cgm_motifs`,
  `bo_cgm_paths`, `bo_yantra_mechanism` rebuild after it.

## 7. What is NOT done

No code, no registry or declaration change, no rebuild, no ids computed or written. The counts are a live reading.
Queries: `ti_l2_19_queries.sql`. The classification is mine, for SS to approve; the bracketed "SS call" items are not
decided here.
