---
artifact: L4_W1_ANALYSIS_BATCH_D.md
canonical_id: NIRMANA_V21_L4_W1_BATCH_D
version: "1.0"
status: CURRENT
campaign_id: nirmana-elevation
session: L4
wave: W1 ANALYZE
assets: ph_pramana, ph_phaladesa, ph_rectification (verdict spine + rectification)
produced_on: 2026-09-05
method: writer/engine/helper source read at origin/main 20323fae4 + 24 live production SQL queries
---

# L4 W1 ANALYZE — BATCH D — verdict spine + rectification

**VERIFIED** = query run / line read. **INFERRED** = reasoned, not executed.

---

## 0. Headline findings

| # | Finding | Grade |
|---|---|---|
| **A** | `phala_phaladesa` (L4's terminal verdict asset) and `phala_pramana` (the honest-probability surface) have **ZERO MCP consumers**. Their only readers — `query_domain_result` / `query_falsifiers` — are registered in the retrieval registry but **not bridged to any MCP tool**. | MUST |
| **B** | The `life_event_match` detector **cannot ever fire**: `life_events.domain` uses 53 slug values (`career/award_selection`), `phala_anchors.domain` uses the canonical 13. Exact-equality match ⇒ 0 matches on both charts. Every past-window anchor is therefore stamped `life_event_miss` — a *refutation-shaped* claim from a detector that structurally cannot return "match". §N.8. | MUST |
| **C** | The **same vocabulary mismatch kills the rectification LEL fit**: `_DOMAIN_HOUSES` is keyed on bare domains, `ev.domain` arrives as `career/award_selection` ⇒ empty significator set ⇒ `lel_fit_score = 0.0000` and `lel_events_matched = 0` on **all 95** scored rows, `win_margin = 0`. Yet `judgment_flags.calibration_state = 'calibrated'`, `load_bearing = true`. §N.8. | MUST |
| **D** | `mimamsa_predictions.source_pramana_id` is populated with an **anchor_id, not a pramana_id** (`mi_bhavisya.py:178`, comment `anchor_id, # source_pramana_id`). 195/195 resolve as `phala_anchors.anchor_id`, **0/195** as `phala_pramana.pramana_id` — while five generated projections + `query_predictions.ts:25` tell callers "references link to ph_pramana (L4 via source_pramana_id)". The P7 seam's *evidence* half is unwired and falsely labelled. | MUST |
| **E** | `ph_pramana` declares 6 deps, **reads 1**. `ph_phaladesa` declares 7, reads 6 (one only as a presence-count). | NOW |
| **F** | **13 and 186 are genuine structural constants**, both derived from module constants, with chart-dependent *values* present. NOT chart-independence bugs. | — (clean) |
| **G** | D-GROUNDING (`grounding_tier`) and D-SALIENCE (`tail_watch`) have **no representation anywhere in the codebase** — `grep -rl` returns nothing across `platform/src`, `platform-mcp/src`, `platform/python-sidecar`. New-doctrine gap, not a regression. | NEVER-LATER |

---

# ASSET 1 — `ph_phaladesa` (the verdict surface)

`writers/ph_phaladesa.py` (444 L) · `services/ph_phaladesa/engine.py` (262 L)

## 1.1 The "13" question — answered

**13 = `len(CANONICAL_DOMAINS)`.** VERIFIED, derived not hardcoded:
`engine.py:60` `_ALL_DOMAINS = CANONICAL_DOMAINS_SORTED` · `brahmagyan/domain_vocabulary.py:52-73`
the frozenset of 13, mirroring migration 386's CHECK · `engine.py:262` one record per domain
**unconditionally**, regardless of whether the chart has any anchor in it · DB CHECK
`phala_phaladesa_domain_canonical` enumerates the identical 13 · serving side imports the same SSoT
(`query_domain_result.ts:21`).

Both charts: 13 rows, 13 distinct domains.

**Verdict: genuine structural constant, correctly derived. NOT a chart-independence bug** — the
per-domain payload differs completely between charts (native: 7 populated / 6 empty; anchors 139 vs 56).

**But** the writer docstring (`:157`) and the engine's (`engine.py:262`) both still say **"7 domain
declarations per chart"** — stale since SHABDA-SHUDDHI Lane L5.

## 1.2 The verdict-voice audit — the central question

**(a) One voice per domain? — YES, structurally guaranteed.** One `PhaladosaRecord` per domain; DB
`UNIQUE (chart_id, domain)`; writer upserts `ON CONFLICT (chart_id, domain) DO UPDATE` (`:237`). Two
systems cannot produce two parallel rows for one domain.

**The real two-voice risk is one layer up, at serve time.** `phala_outlook` — the tool literally named
"outlook", the B.11 L4 entrypoint (`platform-mcp/src/tools/phala_outlook.ts`, backed by
`brahmagyan/phala/outlook.py`, router mounted `main.py:53`) — **never reads `phala_phaladesa`.** It
aggregates `phala_anchors` + `phala_mitigation` + `phala_get_rectification()` + panchanga. So a caller
can obtain an anchor-level picture from `phala_outlook_get` and a domain-verdict from
`query_domain_result` (chat plane only) with **no adjudication between them and no shared identity.**
That is D-SYNTHESIS's "second voice" hazard realised at the surface rather than in the table.

**(b) Divergence → drill pointer + changed confidence? — NO. Neither.**
- `contradiction_summary_jsonb` is set from **the top anchor's** `contradiction_jsonb` only (`:385`),
  never from the domain's other 28 anchors.
- The narration reduces it to a bare count (`_build_deterministic_narration:138-142`).
- `confidence_low`/`confidence_high` are copied verbatim from the top anchor (`:372-373`). **No code
  path modifies confidence in response to contradiction count.** Career: 3 contradictions, band still
  the raw 0.272–0.372.
- There is no `drill_pointers` field on the table, in the record, or in the served envelope.

Live (canonical, career): *"The career and profession domain rests on 29 predictive anchor(s), of
which 28 passed clean sodhana review. The assessed magnitude of effect is minor. … Confidence band
spans 0.272–0.372 … 3 contradiction signal(s) temper this reading and warrant caution."*

**A §N.7 item 5 fidelity problem in that sentence:** `magnitude`, `prediction_window_*`, `peak_date`,
`confidence_*`, `malleability` are **all one anchor's values** (the highest `confidence_high`,
`:348, 366`) presented as *the domain's*, in a sentence that opens by naming 29 anchors. The prose
asserts a domain-level judgment that the data underneath is a single-row selection.

**(c) `tail_watch`, hard-floored? — Does not exist.** `grep -rl tail_watch platform/src
platform-mcp/src platform/python-sidecar` → **no matches.**

On the trim side: `phalaOutlookSections()` (`phala_outlook.ts:48-68`) declares three sections —
`anchors` (minKeep 10), `mitigations` (10), `auspicious_windows` (5) — and **none declares
`hardFloor`.** VERIFIED by grep: `hardFloor` appears in `registry_bridge.ts` (×14),
`register_p1_aliases.ts:284`, `kala_views/ritual.ts`, `kala_views/elect.ts` — **zero occurrences in
any phala surface.** Under `response_budget.ts` PASS 2 (`:308` — `floorOverride === 'zero' &&
!section.hardFloor ? 0 : minKeep`), every phala outlook section is zeroable. The 30 KB
`PHALA_OUTLOOK_BUDGET_KB` against a measured 461 KB payload means **PASS 2 is the normal path, not the
edge case.**

**(d) Honest emptiness reporting (§N.6 item 3).** 6 of 13 canonical-chart domains are entirely empty
(`anchor_count = 0`: education, family, general, progeny, residence, travel). They are served **flat**,
in the same `domain_results` array as the 7 populated ones, with **no flags field** distinguishing
them — `phala_phaladesa` has no `judgment_flags` column and `query_domain_result` emits none. The only
signal is `anchor_count = 0` and a prose sentence a machine caller does not read.

Worse, the prose for an empty domain is self-contradicting:
> education: *"No predictive anchors were derived for the education and learning domain in this build.
> **170 cross-domain spillover(s) feed into this domain.**"*

`incoming_spillover_count` counts **anchor-pair rows** in `phala_sankrama`, not domain pairs
(`engine.py:196`). Career alone contributes 145 rows to *every* other domain (VERIFIED). So "170
spillovers feed into education" is arithmetically true and semantically a broadcast of one domain's
anchor count. `spillover_domains_jsonb` for career is a **1595-element array of undeduplicated dicts**
(`jsonb_array_length` = 1595, 3366 bytes) — the same non-aggregation on the outgoing side.

## 1.3 Real vs declared dependencies

`depends_on` (7): VERIFIED against source —

| declared | table actually read | line | verdict |
|---|---|---|---|
| `ph_nimitta` | `phala_anchors` | `:344` | **READ** |
| `ph_suddha_sodhana` | `phala_suddha_sodhana` (LEFT JOIN) | `:345` | **READ** |
| `ph_pramana` | `phala_pramana` (LEFT JOIN) | `:346` | **READ** |
| `ph_sankrama` | `phala_sankrama` | `:396` | **READ** |
| `ph_pratikara` | `phala_mitigation` | `:435` | **READ** (domain-coverage only) |
| `ph_muhurta` | `phala_muhurta` | `:425` | **READ** (domain-coverage only) |
| `bo_laksana` | — | — | **DECLARED, NEVER READ.** The B.11 read is `bodha_msr_signals` (`:297,308`) — MSR/`bo_bimba` territory, not `bo_laksana`. |

**Undeclared-but-read:** `bodha_msr_signals`. The B.11 whole-chart-read consults a table whose
producing asset is **not in the DAG edge set** — so the orchestrator has no ordering guarantee that
MSR is built first. The failure is silent: `_load_bodha_synthesis` swallows every exception (`:318`)
and logs at `debug`, `bodha_consulted` stays `false`, and the row is still written with
`b11_whole_chart_read: false` buried in `derivation_ledger_jsonb` — a column **no consumer selects.**

The docstring at `:19-20` also claims reads of `bodha_cdlm_cells` and `bodha_cgm_edges`. **Neither is
read.** `BodhaSynthesisContext.cdlm_linkage_summary` / `.cgm_paths_by_domain` are initialised empty and
never populated (`:291`), so `derivation_summary_jsonb.b11_cdlm_link_count` and `b11_cgm_path_count`
are **structurally always 0** — §N.7 item 4 / §N.8.

## 1.4 Leverage

`query_domain_result.ts:83-93` selects 21 columns. **Not selected, but populated:**

| column | population (canonical) | why it matters |
|---|---|---|
| **`narration_jsonb`** | 13/13 | The *only* prose verdict L4 produces. Fully computed, never served. The capability serves `narration_status` — the status of a thing it never returns. **Highest-value single item in the layer.** |
| **`contradiction_summary_jsonb`** | 7/13 | The divergence surface D-SYNTHESIS is built on. Never served. |
| **`precedent_refs_jsonb`** | 7/13 | Grounding/precedent references. Never served. |
| **`spillover_domains_jsonb`** | 5/13 | Outgoing spillover detail. Never served (only the incoming *count* is). |
| **`derivation_summary_jsonb`** | 13/13 NOT NULL | Carries `b11_bodha_consulted`, `b11_msr_score`. Never served. |
| **`derivation_ledger_jsonb`** | 13/13 NOT NULL | **B.3 derivation-ledger mandate.** Never served ⇒ no consumer can audit the claim. |

**Read-but-degenerate:** `mitigation_available` is `true` for **career only** — because
`phala_mitigation` is 536 rows all linked to career anchors. The field is honest about what it
measures; the upstream `ph_pratikara` distribution makes it a near-constant `false`.

**Descriptor claim with no detector (§N.8):** `query_domain_result.ts` declares
`grounds_to: { l1_fact_ids: true }` — the SQL selects **no fact_id of any kind**. No code path could
make this flag correctly read `false`.

`density_contract`: **absent.** (The sibling `query_prospective_ledger.ts:143` *does* declare one with
`empty_reason: true` — the pattern exists in this very directory and was not applied here.)

## 1.5 Latent §N.7 item 6 defect in the narration

`ph_phaladesa.py:97-98`:
```python
mag  = rec.magnitude or 'moderate'
mall = (rec.malleability or 'semi_influenceable').replace('_', '-')
```
`mag` is only emitted inside `if rec.magnitude:` (`:109`) so its default is dead. **`mall` is not so
guarded** — emitted inside `if rec.confidence_low is not None and rec.confidence_high is not None:`
(`:119-123`). A row with a confidence band but a NULL `malleability` would print *"the outcome is
classed as semi-influenceable"* — an invented, favourable-sounding judgment standing in for "I don't
know". No such row exists today, so **latent, not live** — but byte-for-byte the
`'elevated'`-on-missing-`direction` defect class §N.7 item 6 names.

---

# ASSET 2 — `ph_pramana` (the honest-probability surface)

`writers/ph_pramana.py` (213 L) · `services/ph_pramana/engine.py` (219 L)

## 2.1 The D5 NO-SCORING gate — located and characterised

**Three layers, all real:**
1. **Forbidden-name set** — `ph_pramana.py:34-37`: `{calibration_score, posterior_probability,
   accuracy_rate, hit_rate, precision, recall, brier_score, empirical_score}`.
2. **Per-record enforcement** — `:115-122` `_d5_gate(rec)`, called **before every INSERT** (`:75`).
   Raises `D5ViolationError` (a `RuntimeError` subclass) — a genuine build-halt, not a warning.
3. **Structural absence** — `PramanaRecord` (`engine.py:78-93`) has 12 fields, none numeric-score-
   shaped; `derive_pramana_records` performs only classification. The DB table has **no numeric column
   at all** — 13 columns, zero `numeric`/`double precision`. VERIFIED via `information_schema`.

**Forbids:** any *empirical accuracy metric* on an L4 evidence record. **Permits:** structural
classification labels (`evidence_type`, `evidence_strength_label`, `window_status`).

**§N.8 assessment of the gate itself:** `_d5_gate` uses `hasattr(rec, col)`. Since `PramanaRecord` is a
plain `@dataclass` (not slotted, not frozen), `hasattr` genuinely returns `True` if such a field or
dynamically-set attribute exists — so a code path *does* exist by which the gate correctly halts.
**This is an earned signal.** It is name-based and would not catch `score`, `p_hit`, `confidence`, or a
score smuggled inside `observable_criteria_jsonb` — honest scope, worth stating.

**Verdict on the mandate: the honest-probability surface is PRESERVED at the D5 boundary. No
calibration value is invented at L4. That part of the L4/L5 contract holds.**

## 2.2 …but the *evidence classification* is not earned

```
 evidence_type        strength   window_status   n    lel_id  lel_json
 pending_observation  proxy      pending        119     0        0
 life_event_miss      indirect   past_window     12     0        0
 pending_observation  proxy      open             8     0        0
```
Abhinandan: 45 / 8 / 3, same shape, `lel_entry_jsonb` = 0.

**`life_event_match` count across the entire database: 0.** And it structurally cannot be otherwise:
`engine.py:157` requires `lel.domain.lower() == anchor.domain.lower()`; `phala_anchors.domain` ∈
canonical 13 (migration 386 CHECK); `life_events.domain` holds **53 distinct slug values**
(`career/award_selection`, `spiritual/devata_adoption`, `residential+travel/foreign_move_start`,
`health/chronic_onset`, plus 1 NULL) — **not one is a canonical domain** except a single bare
`travel`. ⇒ the equality can essentially never hold. **`life_event_match` is unreachable code.**

**The §N.8 question — "what code path would have to run AND FAIL for this signal to read false?"** For
`life_event_miss` the answer is: *none exists.* It is assigned purely by `w_status == 'past_window'`
after a match attempt that cannot succeed (`engine.py:181-186`). **A "miss" is the strongest negative
claim the instrument makes** — it asserts the predicted event did not occur — and 12 canonical + 8
Abhinandan rows currently carry it on no evidence whatsoever. Per doctrine the correct value is
**null / `pending_observation` with an explicit `detector_unavailable` reason**, not a refutation.

**Second-order §N.7 item 6:** `classify_evidence_strength` (`engine.py:141-155`) returns `'indirect'`
for `life_event_miss` with `lel_domain = None`. `'indirect'` is a plausible-sounding *evidence
quality* label attached to rows where **no evidence object exists at all.** A miss has no strength.

**Dead vocabulary:** the CHECK allows five `evidence_type` values; the engine emits three —
`proxy_indicator` and `self_report` are unreachable. `LelEntry.outcome_valence` is documented as
`'positive'|'negative'|'neutral'`, populated by the writer as `'observed'|'not_observed'|None`
(`:191-193`), and **never read by the engine** — a dead field with a mismatched vocabulary.

**Where the honest null is correctly kept — credit where due:**
- `lel_entry_id` left `None` with an explicit docstring (`:170-175`): the source `id` is a uuid, the
  column is bigint, so the uuid is carried in `lel_entry_jsonb` rather than forced or fabricated. ✅
- `parse_observable_criteria` falls back to the literal `'(see falsifier_text)'` (`engine.py:132-133`)
  rather than inventing a criterion. 4 canonical rows hit it. ✅
- `_load_lel`'s `UndefinedTable` handling narrows the except and rolls back to SAVEPOINT (`:206-213`) —
  degrades to `[]`, not to a guess. ✅

## 2.3 §N.5 / §N.7 item 1 — re-derivation where a reference exists

`phala_anchors.structured_falsifier_jsonb` is **139/139 populated**. `ph_pramana` does not select it
(`:128-134`); it selects the free-text `falsifier` and **regex-parses it** (`engine.py:39-41,105-139`).
Exactly §N.7 item 1's prohibition: a downstream layer re-deriving a structure the upstream asset
already computed, inviting drift — and it is what produces the 4 `(see falsifier_text)` no-parse rows.

## 2.4 Latent cross-chart contamination (`ph_pramana.py:180-187`)

```sql
SELECT id, event_date, domain, description AS event_summary, outcome_observed
FROM life_events ORDER BY event_date          -- ← NO chart_id predicate
```
The docstring (`:163-165`) asserts *"`life_events` is a global, single-native log: it carries no
chart_id column."* **This is false as of migration 423.** `life_events.chart_id` exists, and the
sibling `ph_rectification` reads `WHERE chart_id = %s` and documents the migration explicitly
(`ph_rectification/__init__.py:96-106`). Today only one chart has events, so the bug is **latent** —
Abhinandan's 56 pramana rows were matched against the native's 64 events and produced no false match
**only because of finding B.** The instant a second chart records events, `ph_pramana` will match one
chart's anchors against another chart's life history: the JL-017 contamination class that
`ph_rectification` explicitly firewalls, un-firewalled in its sibling.

## 2.5 Real vs declared dependencies — the worst ratio in the layer

`depends_on` (6). The writer's **entire** DB read surface is `phala_anchors` (`:127-135`) and
`life_events` (`:180-187`).

| declared | read? |
|---|---|
| `ph_nimitta` | **READ** |
| `ph_sankrama` · `ph_muhurta` · `ph_pratikara` · `ph_sodhana` · `ph_suddha_sodhana` | never |

**5 of 6 declared deps are never read.** The `linked_sodhana_id` column (which would justify the
`ph_sodhana` edge) is **100% NULL** on both charts — nothing sets it. `query_falsifiers` nonetheless
advertises *"lel_entry_id / linked_sodhana_id where present"* (`query_phala_calibration.ts:204`) for
two columns that are never present.

**Undeclared-but-read:** `life_events` — not a registered asset, so no DAG edge is possible; build
ordering relative to LEL ingest is unmanaged.

## 2.6 Serving

Sole reader: `query_falsifiers` (`:195-256`). Selects 10 columns — **`derivation_ledger_jsonb` is not
among them** (B.3 ledger again unserved). No pagination, no `LIMIT`, `ORDER BY window_status` only
(non-total ⇒ non-deterministic row order). No `density_contract`, no `empty_reason`, no flags.
`grounds_to: { l1_fact_ids: true }` with no fact_id in the SELECT. And per finding **A**, the
capability is not reachable from MCP at all.

---

# ASSET 3 — `ph_rectification`

`writers/ph_rectification/__init__.py` (366 L) · `services/ph_rectification/engine.py` (628 L)

## 3.1 The "186" question — answered

**186 = 37 × 5 + 1**, wholly derived from module constants:
`engine.py:113-114` `SCAN_HALF_WIDTH_MIN = 90`, `SCAN_STEP_MIN = 5` · `:238-239` `range(-90, 91, 5)`
⇒ **37** offsets · `:110` `AYANAMSHAS = (lahiri, true_chitra, kp, raman, surya_siddhanta)` ⇒ **5** ·
`+ 1` row in `phala_rectification_best` (`UNIQUE (chart_id)`). DB: 185 + 1 on **both** charts, 37
distinct offsets each.

**Chart-identical count is NOT a bug — verified chart-dependent payload:**

| | native `482012f1` | Abhinandan `1c826d5a` |
|---|---|---|
| lagna @ offset 0, lahiri | Aries **12.4311°** | Aries **23.5265°** |
| lagna @ −90 | Pisces 14.2495° | Pisces 26.5033° |
| `lel_events_tested` | 40 | 0 |
| `lagna_stable` rows | 95 | 90 |
| `rectification_basis` | `lel_fit` | `structural_no_lel` |

The scan grid is chart-independent **by design** (a fixed ±90 min / 5 min lattice); the ascendants
computed on it are per-chart. **Genuine structural constant. Clean.**

## 3.2 The earned-signal defect

**The scoring is completely non-discriminating and the calibration flag does not know it.**
```
 chart 482012f1: lel_fit_score | matched | rows
                 0.0000        |    0    |  95    ← every stable candidate
                 NULL          |  NULL   |  90    ← unstable candidates, correctly unscored
```
`phala_rectification_best`: `best_lel_fit_score = 0.0000`, `win_margin = 0.0000`,
`lel_training_matched = 0` of `lel_training_events = 40`, `confidence_label = 'unresolved'`.

Yet the same row carries:
```json
{"calibration":"calibrated","calibration_state":"calibrated",
 "rectification_basis":"lel_fit","lel_event_count":64,"load_bearing":true}
```

**§N.8 test:** what code path would have to run *and fail* for `load_bearing` to correctly read
`false`? `lel_calibration.py:is_load_bearing` / `judgment_flags` are pure functions of **`event_count`
alone** — `state == STATE_CALIBRATED` iff `count >= n_min`. There is **no path** by which a
zero-discrimination fit could flip it. `load_bearing: true` asserts "this chart's empirical LEL
calibration is load-bearing" on a fit that contributed **exactly nothing**. The proxy is
*availability*; the claim is *efficacy*. **Same defect class as the orchestrator no-op-completion
predicate (§N.8 instance 4).**

**Root cause of the zero scores (finding C), traced:**
- `_load_chart_training_events` sets `domain=str(row.get("domain") or row.get("category") or
  "unknown")` (`__init__.py:140`) → `career/award_selection`.
- `_score_dasha_match` → `domain_significator_houses(ev.domain)` (`engine.py:206-212`) →
  `_DOMAIN_HOUSES.get('career/award_selection', ())` → **`()`**.
- `md_house in houses` is `False` for every event, every candidate ⇒ `matched = 0` ⇒
  `fit = 0/(2·40) = 0.0` (`engine.py:471-478`).
- The `"+"` handling at `:208-211` splits `residential+travel` but nothing splits on `/`.

**Two secondary defects in the same path:**
1. **The leakage firewall's date-confidence filter is neutered.** `__init__.py:141` hardcodes
   `date_confidence="month-exact"` for *every* event, ignoring the real column. Real values: `exact`
   58, `month_known` 3, `year_only` 3. `_firewall_filter` (`engine.py:227-234`) drops anything not in
   `("exact","month-exact")` — so the 3 `year_only` events **pass a filter designed to exclude them**,
   wearing a hand-stamped confidence they do not have. Note the separator mismatch too: the DB says
   `month_known`, the engine expects `month-exact` — they would never have matched had the real column
   been read.
2. **`confidence_low = −0.2000` is persisted.** `engine.py:591` — `conf_low = round(best_score -
   (1.0 - best_score) * 0.2, 4)` with `best_score = 0` ⇒ **−0.2**. There is **no CHECK constraint** on
   `phala_rectification_best.confidence_low/high` (the only CHECKs are on `auto_action` and
   `confidence_label`). A negative confidence is served raw by `query_rectification`.
3. **Two different counts of "the same thing" in one row.** `judgment_flags.lel_event_count = 64`
   (pre-firewall, `:270`) vs `lel_training_events = 40` (post-firewall, `engine.py:521`). Both
   persisted, both labelled as the chart's LEL events. The serving layer *does* disambiguate them; the
   storage layer does not.

## 3.3 Where this asset does it right — the counterweight

`query_rectification` (`query_phala_calibration.ts:676-731`) is the **best §N.6/§N.8 citizen in the L4
serving plane, and should be the template for the rest of the layer:**
- Computes variance across the served page's `lel_fit_score` and emits `non_discriminating: true` with
  a full `non_discriminating_note` — *"the ORDER BY … ranking is NOT discriminating … this flag exists
  so a caller never reads 'first row' as 'best candidate.'"*
- Cross-checks with `win_margin` as an independent corroborating signal.
- `lel_match_explanation` (`:672-674`) states in prose exactly the 64-vs-40-vs-0 accounting the storage
  layer leaves ambiguous.
- Emits an honest `note` when no best row exists — *"the correct resting state for a chart with
  lel_event_count=0 (structural calibration), not an error."*
- `override_note` restates the D43 NO-AUTO-OVERRIDE gate at serve time.

**The gap:** it ships `non_discriminating: true` and `load_bearing: true` **in the same envelope**,
with nothing reconciling them. A caller reading `judgment_flags` alone gets "calibrated,
load-bearing"; a caller reading `non_discriminating` gets "this ranking is meaningless". Both are in
`content`, neither defers to the other.

## 3.4 D43 gate (checked, and it holds)

`AUTO_ACTION = "stage_for_review"` (`engine.py:117`), re-asserted at `select_best` (`:608-611`,
raises), DB `CHECK (auto_action = 'stage_for_review')`, writer never issues UPDATE/DELETE against
`charts`, `native_adopted = false` on both rows. **Earned signal — there is a real path by which it
fails.**

## 3.5 Dependencies, serving, leverage

`depends_on = [ph_nimitta]`. The writer reads `charts` (via `resolve_birth_params`), `life_events`,
`chart_dashas`, `chart_facts`, `brahma_formula_constants` — and **never touches `phala_anchors`.** So
the **one declared dep is never read**, and four real upstream reads are **undeclared**. The DAG edge
is inverted from reality: it declares the L4 sibling it doesn't use and omits the L1 assets it does.

**Populated-but-unread:** `leakage_firewall_note` and `best_lagna_longitude` are not selected by
`query_rectification` (`competing_candidates`, a 3-element jsonb, *is* served).
**Read-but-degenerate:** `ORDER BY lel_fit_score DESC NULLS LAST LIMIT 50 OFFSET n` over 95 rows of an
identical score ⇒ **unstable pagination** — page 2 may repeat or skip page-1 rows. No total-order
tiebreak. `density_contract`: absent on all three capabilities in this batch.

---

# The P7 seam — condition report, column by column

**Verdict: INTACT at the anchor level; UNWIRED and FALSELY LABELLED at the evidence level. Not damaged
by this programme — damaged by construction.**

| link | column | type | resolves |
|---|---|---|---|
| `mimamsa_predictions` → `phala_pramana` | `source_pramana_id` | **text** | **0 / 195** |
| `mimamsa_predictions` → `phala_anchors` | same column | text | **195 / 195** |
| `mimamsa_anchor_adjustment` → `phala_anchors` | `origin_id` | uuid | **195 / 195** |
| `mimamsa_anchor_adjustment` → `phala_pramana` | `derived_from_pramana_ids` | array | **`[]` on 195/195** |
| `phala_phaladesa` → `phala_anchors` | `top_anchor_id` | uuid | 0 dangling |
| `phala_pramana` → `phala_anchors` | `anchor_id` | uuid | 0 dangling, **has FK CASCADE** |

**Root cause, not inference** — `writers/mi_bhavisya.py:178`: `anchor_id,          # source_pramana_id`.
The value written into the column named `source_pramana_id` **is the anchor_id.** Not staleness:
`max(computed_at)` on `phala_pramana` is `2026-08-13 01:16:21`, `max(emitted_at)` on
`mimamsa_predictions` is `01:16:29` — **8 seconds later, same build.** It was never a pramana_id.

**The false claim is served.** `query_predictions.ts:25` and four generated projections state:
*"emits_references: prediction_id references link to ph_pramana (L4 via source_pramana_id)."* A caller
following that pointer gets zero rows, forever.

**No foreign key protects any of it.** `pg_constraint` over `mimamsa_predictions` /
`mimamsa_anchor_adjustment` → **no FK to any `phala_*` table.** Meanwhile `phala_pramana.anchor_id` is
`ON DELETE CASCADE` from `phala_anchors`, and `ph_nimitta` is delete-then-insert with fresh uuids per
build. **The next `ph_nimitta` rebuild silently orphans all 195 predictions and all 195 anchor
adjustments**, with no constraint, no cascade, and no detector to notice.

**Columns a later prediction→outcome loop needs — present and populated:**

| need | column | populated |
|---|---|---|
| prediction identity | `prediction_id` (PK with chart_id) | 195/195 |
| time window | `observation_window` (daterange), `eval_date` | 195/195 |
| falsifiable claim | `outcome_claim`, `falsifier_jsonb` | 195/195 |
| constituent signals | `driving_signals` | 195/195 |
| frozen-bundle identity | `frozen_bundle_hash`, `bundle_formula_version` | 195/195 |
| lifecycle | `lifecycle_status` | 195 = `pending` |
| **base rate** | `base_rate` | **0/195** — correctly NULL, `mi_bhavisya.py:185` `# base_rate — computed by mi_pramana`. **Honest null. Preserve.** |
| adjudication seam | `mimamsa_adjudication_log` | **0 rows** (table exists, schema correct) |
| journal seam | `mimamsa_journal` | **0 rows** (table exists, schema correct) |
| independent ledger | `brahma_prospective_ledger` | 30 rows, with `matched_event_id` FK → `life_events` — **the one seam with a real FK** |

**Also on the seam, for the record:** `mimamsa_anchor_adjustment` carries `multiplier = 0.95` on **all
195 rows** with `evidence_n = 0`, `leakage_status = 'not_assessed'`. A non-neutral numeric adjustment
applied uniformly on zero evidence. **L5's asset — outside this batch's write scope**; recorded as
seam condition observed, not proposed for change.

**Nothing in this batch's three writers touches any `mimamsa_*` table or `standing_predictions`**
(VERIFIED by grep). The seam is verify-only, and the finding is: *the anchor half is intact and
fragile; the evidence half was never connected and is advertised as if it were.*

---

# Instrument fit, per asset

| doctrine | `ph_phaladesa` | `ph_pramana` | `ph_rectification` |
|---|---|---|---|
| **D-GROUNDING** | **MISSING.** A verdict asset with no grounding tier. `source_citation` is a self-referential string, not a grounding claim. | **MISSING.** `evidence_strength_label` is adjacent but is evidence-quality, not `sruti`/`yukti`/`pratyaksa`. | **MISSING** — though `rectification_basis` (`lel_fit`/`structural_no_lel`) is the closest existing analogue in the layer and a sound model to generalise from. |
| **D-SYNTHESIS** | Voice singular ✅. Convergence counters exist but **do not move confidence** ❌. Divergence: count only, **no drill pointer, no confidence change** ❌. Adjudication: none stored ❌. | N/A (not a verdict asset) — but it *is* the confidence substrate the verdict should consult, and `evidence_strength_label` reaches phaladesa unused in any confidence computation. | `competing_candidates` (top-3) is a **real, stored, inspectable adjudication record** ✅ — the only one in the layer. `non_discriminating` is a genuine confidence-change signal ✅. |
| **D-SALIENCE** | No salience term; no `tail_watch`; **6 empty domains flattened with 7 populated ones** — the opposite of a tail-watch reserve ❌. | No salience term. The 12 `life_event_miss` rows are precisely `low_salience_high_consequence` candidates and are indistinguishable in the served array ❌. | `lagna_stable` is a genuine chart-intrinsic partition (95/90) ✅ but is not a salience term and is not floored. |
| **D-TIME** | Window fields all from one anchor; no window tiling, no gap accounting. | `window_status` computed against `date.today()` — correct and cheap, but it makes every row **time-dependent with no `as_of` stamp**: a consumer cannot tell a stale `open` from a live one. | `candidate_birth_utc` is time-*of-birth*. Largely N/A. |
| **D-SERVICE** | Reader exists, **not MCP-reachable**; no floor, no `density_contract`, no empty-reason. | Same. | **MCP-reachable** (`register_p1_ganita.ts:1164`); honest flags; still no `density_contract`/floor. |

**Instrument-fit verdict:** all three are the *right instrument* — a deterministic domain verdict, a
scoring-free falsifiability registry, and a bounded birth-time scan are each correctly chosen. What is
missing is (i) the grounding/salience vocabulary the new doctrine adds, and (ii) two detectors built
against the wrong vocabulary that therefore measure nothing.

---

# Measured cost, natural keys, honest volume + integrity proposals

No proposal below is a bare `count(*) = N` equality pin.

### `ph_phaladesa`
- **Natural key:** `(chart_id, domain)` — already `UNIQUE`, already the writer's conflict target ✅
- **Driving upstream population:** none. Cardinality is `|CANONICAL_DOMAINS|`, independent of every dependency.
- `expected_volume_formula`: `card(canonical_domains)`
- `expected_volume_inputs`: `{"canonical_domains": "the CHECK arity of phala_phaladesa_domain_canonical"}`
```sql
-- 1. Complete, non-duplicated tiling of the canonical vocabulary.
SELECT count(*) = 0 FROM (
  SELECT d FROM unnest(ARRAY['career','wealth','relationship','progeny','health',
    'education','family','residence','travel','spirituality','character',
    'transition','general']) d
  EXCEPT SELECT domain FROM phala_phaladesa WHERE chart_id = $1) missing;
-- 2. anchor_count must equal the true anchor population for that domain (no drift).
SELECT count(*) = 0 FROM phala_phaladesa pd
 WHERE pd.chart_id = $1 AND pd.anchor_count <>
   (SELECT count(*) FROM phala_anchors a WHERE a.chart_id = pd.chart_id
      AND lower(a.domain) = pd.domain);
-- 3. clean + staged <= anchor_count; top_anchor_id present iff anchor_count > 0.
SELECT count(*) = 0 FROM phala_phaladesa WHERE chart_id = $1
  AND (clean_anchor_count + staged_revision_count > anchor_count
    OR (anchor_count > 0) <> (top_anchor_id IS NOT NULL));
-- 4. top_anchor_id must resolve (no dangling verdict anchor).
SELECT count(*) = 0 FROM phala_phaladesa pd WHERE pd.chart_id = $1
  AND pd.top_anchor_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM phala_anchors a WHERE a.anchor_id = pd.top_anchor_id);
```
- `target_floor`: **13** (achieved = expected, §N.4-compliant since derived, not aspirational).

### `ph_pramana`
- **Natural key:** the existing index is `(anchor_id, evidence_type, COALESCE(lel_entry_id,-1))`. Given
  the engine emits **exactly one record per anchor**, the *true* natural key is **`(chart_id,
  anchor_id)`**. The three-column index is wider than the writer's actual grain and cannot serve as an
  upsert target for identity preservation.
- `expected_volume_formula`: `count(phala_anchors WHERE chart_id = $1)`
```sql
-- 1. FULL-JOIN consistency: exactly one pramana row per anchor, no orphan either way.
SELECT count(*) = 0 FROM (
  SELECT a.anchor_id FROM phala_anchors a WHERE a.chart_id = $1
  EXCEPT SELECT p.anchor_id FROM phala_pramana p WHERE p.chart_id = $1
  UNION ALL
  SELECT p.anchor_id FROM phala_pramana p WHERE p.chart_id = $1
  EXCEPT SELECT a.anchor_id FROM phala_anchors a WHERE a.chart_id = $1) x;
-- 2. one row per anchor (grain assertion).
SELECT count(*) = 0 FROM (SELECT anchor_id FROM phala_pramana
  WHERE chart_id = $1 GROUP BY anchor_id HAVING count(*) > 1) d;
-- 3. window_status must agree with the anchor's window as of computed_at (no drift).
SELECT count(*) = 0 FROM phala_pramana p JOIN phala_anchors a USING (anchor_id)
 WHERE p.chart_id = $1 AND p.window_status <> CASE
   WHEN a.window_start IS NOT NULL AND p.computed_at::date < a.window_start THEN 'pending'
   WHEN a.window_end   IS NOT NULL AND p.computed_at::date > a.window_end   THEN 'past_window'
   ELSE 'open' END;
-- 4. D5: the table must carry no numeric column (structural gate, re-asserted in SQL).
SELECT count(*) = 0 FROM information_schema.columns
 WHERE table_name='phala_pramana' AND data_type IN ('numeric','double precision','real');
-- 5. EARNED-SIGNAL: a life_event_miss must cite a real, resolvable LEL comparison.
SELECT count(*) = 0 FROM phala_pramana WHERE chart_id = $1
  AND evidence_type IN ('life_event_match','life_event_miss')
  AND lel_entry_jsonb IS NULL;      -- ← fails 12/12 today. Correctly.
```
Check 5 is deliberately a **currently-failing** invariant: it is the detector §N.8 says must exist
before `life_event_miss` may be asserted.
- `target_floor`: **NULL until the vocabulary is reconciled** — a floor here would enshrine a count
  produced by a dead detector.

### `ph_rectification`
- **Natural key:** `(chart_id, offset_minutes, ayanamsha_id)` — already `UNIQUE` ✅;
  `phala_rectification_best`: `(chart_id)` — already `UNIQUE` ✅
- `expected_volume_formula`:
  `(floor(2 * scan_half_width_min / scan_step_min) + 1) * card(ayanamshas) + 1`
- `expected_volume_inputs`: `{"scan_half_width_min": 90, "scan_step_min": 5, "ayanamshas": 5}` — module
  constants (`engine.py:110,113,114`) that should be lifted to `brahma_formula_constants` so the
  formula *reads* them rather than restating them (the pattern `_load_calibration_min_events` already
  uses at `__init__.py:49-67`).
```sql
-- 1. Contiguous, gap-free offset lattice at the declared step.
SELECT count(*) = 0 FROM (
  SELECT offset_minutes, lead(offset_minutes) OVER (ORDER BY offset_minutes) nx
  FROM (SELECT DISTINCT offset_minutes FROM phala_rectification WHERE chart_id=$1) o
) g WHERE nx IS NOT NULL AND nx - offset_minutes <> 5;
-- 2. Symmetric, centred lattice.
SELECT min(offset_minutes) = -max(offset_minutes)
   AND bool_or(offset_minutes = 0) FROM phala_rectification WHERE chart_id=$1;
-- 3. Complete cross-product: every offset scored under every ayanamsha.
SELECT count(*) = 0 FROM (
  SELECT offset_minutes FROM phala_rectification WHERE chart_id=$1
  GROUP BY offset_minutes HAVING count(DISTINCT ayanamsha_id) <> 5) x;
-- 4. Exactly one best row, resolving to a real candidate of this chart.
SELECT (SELECT count(*) FROM phala_rectification_best WHERE chart_id=$1) = 1
   AND NOT EXISTS (SELECT 1 FROM phala_rectification_best b
      WHERE b.chart_id=$1 AND b.best_candidate_id IS NOT NULL
        AND NOT EXISTS (SELECT 1 FROM phala_rectification c
            WHERE c.id=b.best_candidate_id AND c.chart_id=b.chart_id));
-- 5. lagna_stable is an all-or-nothing property of an offset across ayanamshas.
SELECT count(*) = 0 FROM (SELECT offset_minutes FROM phala_rectification
  WHERE chart_id=$1 GROUP BY offset_minutes
  HAVING count(DISTINCT lagna_stable) > 1) x;
-- 6. FINGERPRINT DISTINCTNESS: two different charts must not produce an identical
--    lagna-degree fingerprint (the chart-independence detector this asset lacks).
SELECT count(*) = 0 FROM (
  SELECT md5(string_agg(lagna_degree_in_sign::text, ',' ORDER BY offset_minutes,
                        ayanamsha_id)) fp
  FROM phala_rectification GROUP BY 1 HAVING count(DISTINCT chart_id) > 1) x;
-- 7. Confidence band must be a probability band. Fails today (-0.2).
SELECT count(*) = 0 FROM phala_rectification_best WHERE chart_id=$1
  AND (confidence_low < 0 OR confidence_high > 1 OR confidence_low > confidence_high);
-- 8. EARNED-SIGNAL: load_bearing may not be true on a non-discriminating fit.
SELECT count(*) = 0 FROM phala_rectification_best WHERE chart_id=$1
  AND (judgment_flags->>'load_bearing')::bool
  AND coalesce(win_margin,0) = 0;   -- ← fails 1/1 today. Correctly.
```
- `target_floor`: **186** (derived; safe).

---

# Findings → W2

### MUST

**F1 — `phala_phaladesa` and `phala_pramana` are unreachable from MCP.** D-SERVICE; §N.6.
`grep "marsys://tool/L4" platform-mcp/src` returns only `query_predictive_anchors`,
`query_rectification`, `query_prospective_ledger`. `query_domain_result` / `query_falsifiers` appear
only in `chat_tool_defs.generated.json` + `docs_resource_catalog.generated.json`; **0 hits** in
`mcp_surface_profiles.generated.json` and `web_tool_bridge.generated.json`.
*Impact: the layer's terminal verdict and its entire falsifiability registry are invisible to every
MCP caller, including `judgment_query` and the `assess_*` family. **The single highest-leverage W2 item
in L4.***

**F2 — `life_event_match` is an unreachable detector; `life_event_miss` is an unearned refutation.**
§N.8; §N.7 item 6. `engine.py:157` exact-equality on `domain`; `life_events.domain` = 53 slug values vs
canonical 13; `life_event_match` count = **0** across the whole DB; 12 canonical + 8 Abhinandan rows
carry `life_event_miss`.
*W2 shape: normalise via `brahmagyan.domain_vocabulary`'s existing synonym map before comparison **and**
introduce an explicit `detector_unavailable` disposition so a miss is never asserted where a match was
impossible. Do **not** ship a fix that turns 0 misses into 0 matches silently.*

**F3 — `ph_rectification`'s LEL fit is identically zero; `calibration_state: calibrated` /
`load_bearing: true` cannot detect it.** §N.8; §N.6 item 1. `lel_fit_score = 0.0000` on all 95 scored
rows, `win_margin = 0`, `lel_training_matched = 0/40`; `_DOMAIN_HOUSES.get('career/award_selection')`
→ `()`; `is_load_bearing` is a pure function of `event_count`.
*W2 shape: (i) same vocabulary normalisation as F2; (ii) `load_bearing` must consult **discrimination**,
not availability — the serving layer already computes exactly that signal (`non_discriminating`), so the
honest minimum is to make the flag null/false when `win_margin == 0`.*

**F4 — `source_pramana_id` holds an anchor_id and the falsehood is served.** §N.5; the parked-P7
mandate. `mi_bhavisya.py:178`; 195/195 resolve as anchor_id, 0/195 as pramana_id; both written in the
same build 8 s apart. `query_predictions.ts:25` + 4 generated projections advertise the ph_pramana link.
*W2 shape: **verify-only in this programme.** Report the seam's true shape; do not rename a column or
rewire L5. The actionable near-term act is to **correct the served descriptor text** so the instrument
stops claiming a link it does not have — that is provenance preservation, not P7 construction.*

**F5 — No FK anywhere on the P7 seam; `ph_nimitta`'s next rebuild silently orphans 390 rows.**
parked-P7 mandate ("nothing may make the later loop harder"). `pg_constraint` → no FK to any `phala_*`;
`phala_pramana.anchor_id` is `ON DELETE CASCADE` from a delete-then-insert parent.
*W2 shape: an integrity check (proposed above), not a schema change. A failing detector is the correct
first act; the FK is a P7-programme decision.*

### NOW

**F6 — `ph_pramana` reads `life_events` without a `chart_id` predicate; its docstring asserts the
column does not exist.** §N.5; JL-017 contamination class. `:180-187` vs
`ph_rectification/__init__.py:109-117`; `life_events.chart_id` exists (migration 423). Latent today.

**F7 — `ph_pramana` declares 6 deps and reads 1; `ph_rectification` declares 1 and reads 0 of it.**
§N.8 applied to the DAG (a declared edge is a claim). `linked_sodhana_id` 100% NULL on both charts.

**F8 — `narration_jsonb` (13/13), `contradiction_summary_jsonb` (7/13), `precedent_refs_jsonb` (7/13),
`derivation_ledger_jsonb` (13/13) are computed and never served.** §N.6; B.3 (the derivation-ledger
mandate is unauditable if never emitted). `query_domain_result.ts:83-93`.

**F9 — `derivation_summary_jsonb.b11_cdlm_link_count` / `b11_cgm_path_count` are structurally always
0.** §N.7 item 4 / §N.8. `ph_phaladesa.py:19-20` docstring claims the reads; the context fields are
never populated (`:291`).

**F10 — The date-confidence leakage firewall is neutered by a hardcoded `"month-exact"`.** §N.7 item 3
(no wrapper-local constant may shadow a stored value); §N.8. `__init__.py:141` vs real values
{exact 58, month_known 3, year_only 3}. The separator mismatch means the filter would reject real
month-known events too.

**F11 — `confidence_low = -0.2000` persisted; no CHECK constraint prevents it.** §N.7 item 6.
`engine.py:591`; CHECKs exist only on `auto_action` and `confidence_label`.

**F12 — No phala serving section declares `hardFloor`; `phala_outlook` runs a 30 KB cap over a 461 KB
payload.** §N.6 item 2. `phala_outlook.ts:48-68`; `grep hardFloor` → 0 phala hits, 14 in
`registry_bridge.ts`.

**F13 — Unearned `grounds_to: { l1_fact_ids: true }` on `query_domain_result` and `query_falsifiers`.**
§N.8. Neither SELECT list contains any fact identifier.

**F14 — `query_rectification` paginates a total tie with no tiebreak ⇒ unstable paging.** §N.7 item 2.
`ORDER BY lel_fit_score DESC NULLS LAST LIMIT 50 OFFSET n` over 95 identical scores.

**F15 — `incoming_spillover_count` and `spillover_domains_jsonb` are un-aggregated anchor-pair row
counts.** §N.6 item 1. `engine.py:196`; career→each of 11 targets = 145 rows;
`spillover_domains_jsonb` for career = 1595 elements; education (0 anchors) narrates "170 cross-domain
spillover(s) feed into this domain".

**F16 — Stale docstrings: "7 domain declarations" in writer + engine; "150 rows" / "7-domain result
map" in capability descriptions.** §B.8 (registries must not disagree). `ph_phaladesa.py:157`,
`engine.py:262`, `query_phala_calibration.ts:8`, `chat_tool_defs.generated.json:2508`.

### NEVER-LATER

**F17 — `grounding_tier` (D-GROUNDING) has no representation anywhere.** `ph_phaladesa` is the verdict
class, and verdicts are a named required-grounding class. `grep -rl grounding_tier` → no matches.
*Nearest existing analogue to generalise from: `rectification_basis` (`lel_fit`/`structural_no_lel`) —
an honest, availability-driven basis label already in production.*

**F18 — `tail_watch` (D-SALIENCE) has no representation; the phaladesa envelope has no reserved section
and no salience term.** `grep -rl tail_watch` → no matches; `phalaOutlookSections()` declares three
sections, none hard-floored. *The `low_salience_high_consequence` population is identifiable today: the
12 `life_event_miss` rows; the 6 zero-anchor domains carrying 170–315 incoming spillovers.*

**F19 — No `density_contract` on any of the three L4 capabilities; no `empty_reason` on the two
verdict-spine readers.** §N.6 item 4. The pattern exists in the same directory —
`query_prospective_ledger.ts:143-146`.

**F20 — Seam observation, not a proposal: `mimamsa_anchor_adjustment` applies `multiplier = 0.95` to
all 195 rows with `evidence_n = 0`, `leakage_status = 'not_assessed'`, `derived_from_pramana_ids =
[]`.** §N.8. **L5's asset — outside this batch's write scope**; recorded so the P7 programme inherits
it rather than rediscovers it.

---

## What is verified-clean and must not be "fixed"

- **The D5 NO-SCORING gate.** Three real layers, a genuine build-halt path, and a table with no numeric
  column. The honest-probability surface is preserved. **Do not add a score.**
- **`base_rate = NULL` on all 195 predictions** — explicitly deferred to `mi_pramana`. An honest null.
- **`lel_entry_id = NULL`** with a documented uuid/bigint type rationale, uuid carried auditably in
  jsonb.
- **`'(see falsifier_text)'`** rather than an invented criterion.
- **The D43 NO-AUTO-OVERRIDE gate** — constant + runtime raise + DB CHECK + `native_adopted = false`.
  Earned.
- **13 and 186** — both genuine, derived structural constants with chart-dependent payloads. Not bugs.
- **`query_rectification`'s `non_discriminating` / `lel_match_explanation` / `structural`-resting-state
  note** — the layer's best §N.6/§N.8 work. **The template the other two capabilities should be brought
  up to**, not something to trim.
