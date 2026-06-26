---
artifact: 08_mi_sambandha_SPEC_v1_0.md
canonical_id: L5_SPEC_MI_SAMBANDHA
asset_id: mi_sambandha
asset_kind: data
scope: per_chart
activation: v1 (structural) → enriched by outcomes
version: 1.0
status: DRAFT — build-ready spec (NEW asset, G2)
authored_by: Cowork 2026-06-23
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
matrix_rows_owned: [§A G2 manifestation grammar]
---

# mi_sambandha — Personal Manifestation Grammar

> Sanskrit: *Sambandha* ("relation / connection"). The synthesized, per-native **grammar of how this
> chart speaks** — which channel each signal/house/karaka *actually expresses through* for THIS person.
> Built from the channel data the scorecard records across every event. A deeply superhuman artifact: it
> requires holding every event × every channel at once, and it is the richest possible input to future
> predictions. (G2.)

## §1 — Purpose & value
The comparison model records *which* alternate channel fired for each match. Aggregated across a life,
that data forms a **manifestation grammar**: "this native's 4th-house stress reliably expresses as
mother's-health, rarely property"; "his Saturn returns express as career-rupture, not health." No acharya
could compute this stable per-native channel profile. It sharpens every future prediction (the right
alternate channel to weight) and is a flagship retrievable insight.

## §2 — Inputs
| source | what |
|---|---|
| `mimamsa_calibration.manifestation_channel` (`mi_pramana`) | which channel fired per scored match |
| `mimamsa_attribution.channel_fired` (`mi_pariksha`) | per-signal channel attribution |
| `mimamsa_manifestation_sets` (`mi_bhavisya`) | the legitimate channel universe per signal (the denominator) |
| `bg_rules`/significations (L0) | the classical channel definitions + citations (the structural prior) |

## §3 — Output schema (build-ready)

### Table: `mimamsa_manifestation_grammar` (per chart × origin × channel)
```
chart_id                 uuid       not null
origin_kind              text       not null     -- 'house'|'graha'|'karaka'|'signal_family'
origin_ref               text       not null     -- e.g. 'house_4','graha_Saturn','SIG.x'
channel_id               text       not null     -- 'mother_health','property','career_rupture',...
domain                   text       not null
fire_count               int        not null     -- times this channel fired for this origin (empirical)
opportunity_count        int        not null     -- times the origin was active + this channel possible (denominator)
channel_propensity       numeric                  -- fire_count / opportunity_count (NULL if < min_n)
prior_propensity         numeric    not null      -- the classical-prior expectation (the structural baseline)
propensity_delta         numeric                  -- empirical − prior (where this native differs from the textbook)
n_support                int        not null
confidence_band          numrange
evidence_grade           text       not null      -- 'empirical'|'prior_only'|'structural'
citation_ref             jsonb      not null       -- the classical source for the channel (L0)
grammar_formula_version  text       not null
updated_at               timestamptz not null
PRIMARY KEY (chart_id, origin_kind, origin_ref, channel_id)
```

## §4 — Computation logic (deterministic)

### 4.1 — Structural baseline (v1-active, no outcomes needed)
- From `bg_rules`/significations + the frozen manifestation sets, populate every origin's **legitimate
  channels** with their `prior_propensity` (the classical expectation) and citation. This exists from day
  one — the grammar's structural skeleton, retrievable immediately.

### 4.2 — Empirical enrichment (as outcomes accrue)
- Tally `fire_count` (channel actually fired in a confirmed/partial match) and `opportunity_count` (origin
  active + channel was a legitimate option). `channel_propensity = fire/opportunity` — **NULL below
  `min_n`** (no fabricated propensity). `propensity_delta = empirical − prior` surfaces *where this native
  diverges from the textbook* (the most interesting, most superhuman cell).
- `evidence_grade`: `structural`/`prior_only` until enough confirmed channel-fires → `empirical`.

### 4.3 — Determinism
- Pure counting + division over recorded channel fires; deterministic; no LLM. Frozen formula version.

### 4.4 — No-LEL behavior
- Only the structural baseline exists (`prior_only`); `channel_propensity` NULL everywhere; the grammar is
  the classical expectation, honestly labeled, retrievable. The first confirmed channel-fire begins
  enrichment.

## §5 — Retrievability contract (feeds mi_darshana)
- The grammar is a flagship retrievable insight unit: "for this native, house-4 stress → {mother_health
  0.7, property 0.1, …}", each cell carrying n, evidence_grade, citation, propensity_delta (R5). The LLM
  pulls this to choose the right manifestation framing when narrating a prediction — a uniquely
  personalized, uniquely superhuman input.

## §6 — Determinism & seal gates
- No LLM (D-1). Frozen `grammar_formula_version` (D-2); re-run identical (RL-1).
- **Min-n honesty:** no `channel_propensity` below min_n (B.12).
- **Citation present:** every channel has a classical citation (no un-grounded grammar cell).
- Degenerate-distribution guard on `channel_id`, `domain`, `evidence_grade`.
- Registered with drift_detector + schema_validator (RL-5).

## §7 — Frozen-orchestrator conformance
`@register('mi_sambandha')` `WriterBase`; per_chart; delete-then-insert on
`(chart_id × origin_kind × origin_ref × channel_id)`; `conn=ctx.db_conn` never committed; `count_sql`:
`SELECT count(*) FROM mimamsa_manifestation_grammar WHERE chart_id = $1`.

## §8 — `depends_on`
`['mi_pramana', 'mi_pariksha']` (+ reads `mi_bhavisya`, `bg_rules`). `[P2 reconcile]`.

## §9 — Matrix rows satisfied
G2 manifestation grammar (§A) ✅ · structural baseline v1-active ✅ · empirical enrichment tiered ✅ ·
propensity_delta (native-vs-textbook) ✅ · min-n honesty + citation gate ✅ · R5 retrievable unit ✅ ·
determinism (§G) ✅.

*End 08_mi_sambandha_SPEC v1.0.*
