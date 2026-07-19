---
canonical_id: GOCHARA_RESONANCE_MAP_SPEC
version: 1.0
status: CURRENT
owner: D-5 Lane G-1
created: 2026-07-19
---

# Gochara Resonance Map — Spec (D-5 Lane G-1)

## §0 — What this is

`gochara_resonance_map` is a per-chart × event-class table of *classical-prior-weighted
target sets* — the concrete bhavas, lords, karakas, transit mechanism nodes, sensitive
degrees, arudha padas, yoga constituents, and dasha-lord portfolios that resonate with a
given `brahma_event_ontology` event class for one chart. It is consumed **read-only** by
D-5 Lane G-3's transit-intensity engine (λ_e = PROMISE × PERMISSION × exp(β_e·X(t)) −
suppression), which needs, for each event class, "what to point the transit-scanner at"
before it can compute anything.

Table: `gochara_resonance_map`. Migration: `platform/migrations/459_gochara_resonance_map.sql`
(renumbered from the brief's suggested 458 — that number collided with a concurrently-landing
D-5 lane's `platform/supabase/migrations/458_brahma_prospective_ledger.sql`; both migration
directories share one global numbering sequence).
Writer: `ka_gochara_resonance` (L3 Kāla, per-chart asset). Writer files:
`platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_resonance.py` (orchestrator
registration shim) + `platform/python-sidecar/services/ka_gochara_resonance/writer.py`
(implementation).

Not to be confused with `ka_gochara` — a pre-existing, unrelated L3 service-health
self-test asset (`platform/python-sidecar/services/ka_gochara/`). This is a fresh
asset_set addition; `ka_gochara` was not modified.

## §1 — Schema

```sql
CREATE TABLE gochara_resonance_map (
  id BIGSERIAL PRIMARY KEY,
  chart_id UUID NOT NULL,
  event_class TEXT NOT NULL,          -- one of brahma_event_ontology's 27 event_class_id values
  target_type TEXT NOT NULL,          -- 8 values, see §3
  target_ref TEXT NOT NULL,           -- unique identifier of the target WITHIN target_type
  weight NUMERIC NOT NULL,            -- classical-prior weight, see §2
  classical_citation TEXT,            -- required UNLESS uncited_extension = true
  uncited_extension BOOLEAN NOT NULL DEFAULT FALSE,
  source_rule_id INTEGER REFERENCES bg_transit_rules(id),
  computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(chart_id, event_class, target_type, target_ref)
);
```

A `CHECK` constraint (`gochara_resonance_map_citation_or_flag`) enforces the B.10
invariant at the database level: `classical_citation IS NOT NULL OR uncited_extension = true`.
Every row must carry either a real citation or an explicit, honest flag that it doesn't have one
— never a silent gap, never a fabricated citation string.

## §2 — Weight scale

Weight is a classical-prior strength on an open scale, not a probability. Two families:

**Signature-model rows (`bhava` / `lord` / `karaka`)** — weight `1.0` uniformly. These are the
event class's own declared signature (`brahma_event_ontology.signature_model`); the model does
not currently rank its own houses/lords/karakas against each other, so this writer does not
invent a ranking either (B.10) — G-3's PERMISSION/PROMISE math is where differential weighting
by house-strength etc. actually happens, using this row as one clean, undifferentiated input.

**`mechanism_node` rows** (from `bg_transit_rules`) — weight keyed to `rule_type`:

| rule_type | weight | rationale |
|---|---|---|
| `favourable` | `+1.0` | BPHS ch.29 direct positive gochara-phala |
| `unfavourable` | `-1.0` | BPHS ch.29 direct negative gochara-phala (signed — the adverse-class doctrine, D-2, applies the same machinery with signed valence) |
| `double_transit` | `0.75` | Phaladeepika ch.26 dual-transit combination — real but compound/conditional (requires both grahas present), so weighted below a single-graha direct hit |
| `vedha` | `0.3` | a *modifier* on a primary-house result (obstruction/nullification), not itself a primary signal — the smallest magnitude of the four |

**Extension rows** (`sensitive_degree` / `arudha` / `yoga_constituent` / `dasha_lord_portfolio`)
— fixed weights below `1.0`, reflecting that these are this writer's own synthesis (§3), not a
directly classically-cited target-for-this-event-class claim:

| target_type | weight | rationale |
|---|---|---|
| `sensitive_degree` | `0.5` | a real classical primitive (mrityu-bhaga / gandanta / kartari / pushkara), but its relevance to THIS event class is inferred from karaka overlap, not stated |
| `arudha` | `0.6` | the event class's houses' arudha padas — a standard Jaimini cross-reference technique, but the specific event-class binding here is this writer's own extension |
| `yoga_constituent` | `0.7` | a *fired* (not merely catalog) yoga from `ga_yoga_firings` whose constituent houses/planets overlap the event class — firings-authoritative (§N.6) but the event-class attribution is inferred |
| `dasha_lord_portfolio` | `0.8` | the chart's actual Vimśottarī MD lords matching the event class's karakas — highest extension-weight because dasha-lord activation is the single most load-bearing classical mechanism for "when," even though the portfolio *grouping* itself is this writer's construction |

These are the writer's own documented scale, not a citable classical numeric — deliberately
below the signature-model/mechanism-node rows' weights so G-3 can down-rank extension-sourced
targets relative to directly-cited ones without a separate confidence column.

## §3 — target_type taxonomy

| target_type | Source | citation | uncited_extension |
|---|---|---|---|
| `bhava` | `brahma_event_ontology.signature_model.houses` | `brahma_event_ontology.citations` (joined) | `false` |
| `lord` | `brahma_event_ontology.signature_model.lords` (e.g. `"7L"`) | same | `false` |
| `karaka` | `brahma_event_ontology.signature_model.karakas` | same | `false` |
| `mechanism_node` | `bg_transit_rules` rows where `graha` ∈ event class's karakas and `primary_house` ∈ event class's houses | `bg_transit_rules.classical_citation` (verbatim); `source_rule_id` set | `false` |
| `sensitive_degree` | `chart_facts` (`fact_category='sensitive_degree_check'`) for the event class's karaka(s) | `NULL` | `true` |
| `arudha` | `chart_facts` (`fact_category='arudha_pada'`, `fact_key='sign'`) for the event class's houses (`ARUDHA_A<n>`) | `NULL` | `true` |
| `yoga_constituent` | `ga_yoga_firings` (`fired=true`) whose `constituent_houses`/`constituent_planets` overlap the event class's houses/karakas | `NULL` | `true` |
| `dasha_lord_portfolio` | `chart_dashas` (`system_id='vimshottari'`, `level_n=1`) lords matching the event class's karakas | `NULL` | `true` |

`target_ref` per type: `bhava` → house number as text; `lord` → the raw signature-model lord
string (e.g. `"7L"`); `karaka` → planet name; `mechanism_node` → `"<graha>:<rule_type>:h<house>"`
(unique per rule); `sensitive_degree`/`arudha` → the source `chart_facts.fact_id` (L1 fact
reference, not a restated value — §N.5); `yoga_constituent` → `ga_yoga_firings.yoga_canonical_id`;
`dasha_lord_portfolio` → the dasha lord's graha name.

### Why the four extension types are `uncited_extension = true`

`chart_facts.citation_human` and `ga_yoga_firings.citation_human` frequently DO carry a real
classical citation for the underlying primitive itself (e.g. mrityu-bhaga's BPHS/Jataka Parijata
source, or `neecha_bhanga_raja_yoga`'s BPHS ch.39 citation). That citation is about the
primitive's own classical grounding — it is NOT a citation for "this primitive is a resonance
target for event class X." That specific linkage (karaka-overlap → sensitive-degree relevance;
house-arudha → event-class relevance; constituent-overlap → yoga relevance; karaka-match →
dasha-portfolio relevance) is this writer's own reasoned construction, not something stated in
any source row keyed to the event class. Per B.10 ("Claude never invents numerical chart values"
/ "zero silent gaps"), the honest representation is `classical_citation = NULL,
uncited_extension = true` — never copying the primitive's own citation into `classical_citation`
as if it justified the event-class linkage itself (that would misrepresent an inference as a
citation).

## §4 — Event-class coverage: why these 3 (of 27)

The writer populates `TARGET_EVENT_CLASSES = ("marriage", "major_gain", "career_advancement")`
— chosen from the full 27-class ontology (§B.1, BRIEF_D5) by inspecting `bg_transit_rules`
BEFORE picking (per the brief's instruction not to guess): for each candidate class, its
`brahma_event_ontology.signature_model.karakas` × `.houses` was cross-joined against
`bg_transit_rules(graha, primary_house)` live, and the 3 classes below returned the most
non-empty `mechanism_node` matches:

| event_class | karakas | houses | `bg_transit_rules` matches (live-counted) |
|---|---|---|---|
| `marriage` | Venus | 7, 2 | 2 (favourable h2, unfavourable h7) |
| `major_gain` | Jupiter, Mercury | 2, 11 | 6 (Jupiter favourable×2, Jupiter double_transit×2, Mercury favourable×2) |
| `career_advancement` | Sun | 10, 11 | 2 (favourable h10, favourable h11) |

Every one of the 3 also has: a real `brahma_event_ontology.citations` entry (marriage: BPHS
ch.7 vivaha + Phaladeepika kalatra-bhava + Jaimini Sutram DK; major_gain: BPHS ch.2,11
dhana-bhava; career_advancement: BPHS ch.10 + Phaladeepika ch.10); live `chart_facts`
`sensitive_degree_check`/`arudha_pada` coverage for the native's chart
(`482012f1-710e-4a25-994a-93821f5871aa`); and at least one `ga_yoga_firings` fired row whose
constituents overlap. All three therefore produce non-empty target sets across every one of the
8 `target_type` values, satisfying the G-1 acceptance bar (BRIEF_D5 §1: "live query of
`gochara_resonance_map` for ≥3 event-classes confirming non-empty target sets with real
citations, no `uncited_extension` on a primitive that has a known classical source").

Extending `TARGET_EVENT_CLASSES` to more of the 27 classes is a follow-on, not a G-1 blocker —
the writer's per-event-class fetch/build path (`_fetch_event_class_rows` /
`build_resonance_rows`) is class-agnostic and takes the class list as a plain tuple; adding a
class is a one-line change once its own `bg_transit_rules` coverage is inspected the same way.

## §5 — Citation-sourcing methodology

1. **Direct classical citation, verbatim, never fabricated (B.10).** Every `classical_citation`
   value this writer emits is copied character-for-character from an existing DB row
   (`bg_transit_rules.classical_citation` or `brahma_event_ontology.citations`) — the writer
   never constructs, paraphrases, or invents a citation string.
2. **No re-derivation of rules that already exist as data.** Per the lane brief, this writer does
   not re-derive Gochara rules from BPHS text; it reads them from `bg_transit_rules` (L0,
   BPHS ch.29 / Phaladeepika ch.26-sourced, migration 266) and `brahma_event_ontology`
   (migration 388/456), both pre-populated, BPHS-cited reference tables.
3. **L1-authority discipline (§N.5).** For chart-specific facts (sensitive degrees, arudha padas,
   dasha lords, yoga firings), the row stores the L1 **fact reference** (`fact_id` /
   `yoga_canonical_id` / dasha `lord_graha`) rather than restating a computed value — if the
   underlying L1 fact changes on rebuild, this table does not go stale with a copied-out number.
4. **Explicit extension flag over silent gap or fabricated citation.** Where the writer connects
   an event class to a primitive not itself keyed to that class in source data, it says so
   (`uncited_extension = true`) rather than either dropping the row (a B.10 "silent gap") or
   inventing a citation to make the row look more grounded than it is.

## §6 — Idempotency

Per-chart delete-then-insert (§N.3): `DELETE FROM gochara_resonance_map WHERE chart_id = %s`
immediately before the batch `INSERT`, in the same transaction the orchestrator owns. A rebuild
under any `build_id` replaces the chart's rows; it never accretes.
