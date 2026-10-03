---
version: 1.2
status: DECIDED_N-106 (SS ruled all three decisions as recommended; TI-L2-30 may be coded from this design after the batch is released)
lane: TI-i-fl2-007
item: TI-L2-19 (Q-L2-06 design REVIEW; gate for TI-L2-30)
branch: suvarna/land/TI-i-fl2-007
basis: origin/main 7773df1f9 (bo_bimba.py / bo_karanajala.py unchanged since adb0db29d); production DB read 2026-10-03, reader-only SELECT, chart 482012f1
changelog:
  - 1.2 -- review-ifl2b fixes: no chart-derived catalogue/combination names in the table (generic placeholders); FACT vs PROPOSAL labelled in the section 2 table; 're-wires nothing' stated as true of the live graph only.
  - 1.1 -- SS ruling N-106 recorded: all three decisions (section 5) DECIDED as recommended; section 4 Option A is the decided identity; option analysis kept as history.
  - 1.0 -- design REVIEW for SS: classification of the non-name yoga/dosha node subjects and the id-change list. Document only; nothing is coded.
---

# TI-L2-19: yoga/dosha node subjects -- classification and id-change list (design REVIEW for SS)

Ruling Q-L2-06 (N-59): do the name fix and the identity fix together in the one `bo_bimba` rebuild (identity =
`signal_type_id` + configuration key), and BEFORE coding classify the non-name subjects: "a real yoga with a bad
name gets its catalogue name; a flag, timestamp or number that is not a yoga gets NO yoga node". This is that
classification and the id-change list. SS approved it as recommended (ruling N-106, section 5) before TI-L2-30 is coded. No code, data or
registry change is made here.

## 1. What is live (chart 482012f1, production, 2026-10-03)

* 100 yoga/dosha signals (74 yoga, 26 dosha); 85 yoga/dosha nodes (69 yoga, 16 dosha), 17 per ayanamsha.
* The node subject today is `<class>:<slug of the first of fact_value_text / yoga_name / dosha_name / name / label,
  else signal_type_id>` (`bo_bimba.py:252-271`); node id = `uuid_v5(chart, ayanamsha, node_type, node_subject)`
  (`bodha_cgm_node_identity`, migration 714). Of the 17 per ayanamsha, 10 are real catalogue names and 7 are not.
* 15 signals have no node of their own because their subject collides (3 per ayanamsha).
* **No edge attaches to any yoga/dosha node**: 0 edges of type `yoga_member` on the chart, and every yoga/dosha
  node has `degree_in = degree_out = 0`. So re-keying these nodes re-wires nothing **in the live graph**. This does not hold after a rebuild
  by itself: `bo_karanajala.py:927-941` builds `yoga_member` edges from exactly these nodes whenever a signal's
  configuration names a graha or house, and why the live build produced none was not traced here. The identity
  decision therefore should not rest on "no edges today".

## 2. Classification of the signal types behind the subjects

All 13 yoga/dosha `signal_type_id`s on the chart, the subject each gives today, and the proposed disposition
(5 signals each, one per ayanamsha, unless stated):

| signal_type_id | subject today (FACT) | what the signal is (FACT) | disposition (PROPOSAL, decided in section 5 where marked) |
|---|---|---|---|
| `yoga_label:yoga_name` | `yoga:<name>_yoga` (7 distinct catalogue names; one ayanamsha lacks one of them, so 34 signals) | a catalogue yoga, named | **keep a yoga node**, label = catalogue name |
| `panchanga_special_yoga_combinations:combination_name` | `yoga:<combination name>` | a catalogue combination, named | **keep a yoga node** |
| `panchanga_yoga:name` | `yoga:<panchanga yoga name>` | the birth-time panchanga yoga, a catalogue name | **keep a yoga node** |
| `dosha_label:dosha_name` | `dosha:<name>` (2 distinct catalogue names, 6 signals) | a catalogue dosha, named | **keep a dosha node** |
| `kendradhipati_dosha:doshas_kendradhipati` | `dosha:afflicted` (10) / `dosha:unafflicted` (10) | one signal **per graha** (`planet` in the configuration; `ruled_houses`; `kendradhipati_active` true or false; `doctrine_status = PROPOSED`) | **split by `kendradhipati_active`**: the `true` rows ("afflicted", 2 per ayanamsha) are, in my reading (a judgment, not a fact; all 20 signals carry `doctrine_status = PROPOSED`), instances of a real dosha with a bad name: one dosha node each, label from the catalogue name plus the graha, keyed by `planet`; the `false` rows ("unafflicted") assert the dosha does NOT apply and get **no node** (a Dosha node for an absent dosha would read as a finding). DECIDED (N-106, section 5.1) |
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

*Option analysis (history; **Option A is the decided identity, N-106**):*

* **Option B (the ruling's wording)**: `node_subject = <class>:<signal_type_id>:<configuration key value>`, where the
  configuration key is `fact_value_text` / `yoga_name` / `dosha_name` for the named types and `planet` for
  kendradhipati. **All 60 nodes get new ids** (50 catalogue-name nodes and 10 kendradhipati graha nodes, 12 per
  ayanamsha). 85 old ids are retired: 35 of them (the non-name nodes) disappear, 50 re-key. Two signal types that happen
  to carry the same catalogue name can no longer collide.
* **Option A (DECIDED; smaller churn, same rule for what gets a node)**: keep `<class>:<slug of catalogue name>` for the 50
  catalogue-name nodes and add the graha for kendradhipati. The 50 existing ids stay; 35 retire; 10 are new. Risk: two
  signal types carrying one catalogue name would collide again (none do today: the 50 names are distinct within an
  ayanamsha), which is the defect class being removed.

Either way, edges: no live edge attaches to these nodes (section 1), so no live edge id moves; that is a statement about the live graph only (section 1): a rebuilt graph may carry `yoga_member` edges from these nodes, whose ids depend on the node ids, and Option A (decided) keeps the 50 catalogue-name node ids so those edges would not re-key. The code
that must follow (TI-L2-30): `bo_karanajala.py:927-941` (`_yoga_node_subject` lookup for membership edges, which would
simply find no node for the six flag/attribute types and the unafflicted rows), `bo_bimba.py` (`yoga_best` dedup, the label and the citation
`"{Class} node: {name}"` at `:523`).

## 5. Decisions (SS ruling N-106: all three DECIDED as recommended)

1. **DECIDED. Kendradhipati `unafflicted` rows get NO node; one dosha node per AFFLICTED planet, keyed by planet.**
   (Reasoning kept: a node that says the dosha is absent would be a negative finding presented as a Dosha node.)
   Note carried into the implementation: all 20 kendradhipati signals have `doctrine_status = PROPOSED`, so the 10
   afflicted-planet nodes inherit a proposed (not ratified) doctrine and the node should say so.
2. **DECIDED. Option A identity**: the 50 existing catalogue-name node ids stay, 35 retire (the non-name subjects),
   10 are new (the afflicted-planet dosha nodes). Result: 60 nodes on the canonical chart, 12 per ayanamsha. Option B
   (re-key all 60) is not taken.
3. **DECIDED. The six flag/attribute types stay MSR-only** (`is_yoga_karaka`, `inauspicious_flag`,
   `active_at_birth_flag`, `end_iso`, `number`, `constituent_facts_jsonb_atomic`): no graph node. The signals remain
   in `bodha_msr_signals`.

Open item that is not a decision here: the section 6 list of things that move with TI-L2-30 is unchanged.

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
Queries: `ti_l2_19_queries.sql`. The classification was mine; SS approved it with the three decisions (N-106).
