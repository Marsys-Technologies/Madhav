---
lane: F-35
stream: S3_SATYA (spec + build)
stage: S — SPEC
author: SATYA sub-agent (sonnet)
status: DRAFT — awaiting VERIFIER review
---

# SPEC — mimamsa_insight_get: earn the "empirical" evidence_grade, don't just assign it

## Relationship to F-34 (CL-13 exemplar) — read this first

This is one of the five CL-13 siblings the plan (§2/§5) designates for exemplar-then-replicate:
F-34 (`lanes/F-34/SPEC.md`) establishes the reviewed, general disclosure predicate (§9 there):
locate the surface's own "actual extent served" signal, compare it to what was requested, expose
the comparison structurally rather than only in prose. **This spec does not re-argue that design
choice** — Stage R should treat "disclose structurally, not just in narration" as settled by F-34's
review, and scope this document's review to whether it correctly identifies *this file's* version
of "actual extent" and implements the comparison correctly. Where this spec diverges from a literal
reading of F-34's shape, it is because `DIAGNOSIS.md`'s mechanism trace found the audit's original
framing of F-35 was itself wrong (§0 below) — the adaptation is to the *real* mechanism, not a
loosening of the pattern.

## 0. Correction note (read first — governs everything below)

The audit corpus's original framing for F-35 (and the task brief handed to this Stage-S pass)
described the fix as disambiguating **population-level cross-chart mining** from **this chart's own
outcome calibration** via a field like `evidence_source: 'population_pattern'` vs
`'chart_own_history'`. `DIAGNOSIS.md` §3/§6 traced the actual mechanism and found that framing
**factually false**: every table in this call graph (`mimamsa_manifestation_grammar`,
`mimamsa_insight_units`, their writers `mi_sambandha.py`/`mi_darshana.py`) is chart-scoped by
construction (`WHERE chart_id = %s`, `DELETE ... WHERE chart_id = %s` — §N.3 idempotency standard).
There is no cross-chart join, no population table, anywhere in this path. Writing a
`population_pattern` marker into the response would itself be a fabricated claim — exactly what
B.10 and §N.7 item 6 forbid ("an honest null beats an invented judgment"). This spec follows
`DIAGNOSIS.md`'s corrected mechanism instead: the real defect is that `mi_sambandha.py` grants the
`"empirical"` `evidence_grade` on raw **assignment count** alone, with no floor on how many of
those assignments carry an actual **scored outcome** — so a zero-outcome chart earns `"empirical"`
exactly as if it had genuine calibration evidence. C1/C2 (the missing-marker disclosure claim)
stand as originally stated and are closed here by making `evidence_grade` itself the honest,
disambiguating marker — not by adding a false population/chart-own axis. C3 (population mining) is
retired, not carried into this spec.

## 1. Root-cause statement

`mi_sambandha.py`'s grade predicate (`platform/python-sidecar/pipeline/orchestrator/writers/
mi_sambandha.py:95-96`, `n = opp; grade = "empirical" if n >= 5 else "prior_only"`, where `opp` is
the raw count of predictions ever *assigned* to a channel) grants `"empirical"` without checking
whether any of those assignments has an actual scored `composite_verdict`
(`'confirmed'|'partial'|'denied'` — the documented value set at `platform/migrations/
348_mimamsa_pramana.sql:17`; `'pending'`/absent-row are not scored), and `mi_darshana.py`
(`platform/python-sidecar/pipeline/orchestrator/writers/mi_darshana.py:151,184`) then hardcodes the
literal string `"empirical"` into every `mimamsa_insight_units` row it synthesizes from a
`manifestation_grammar`-graded-empirical row — discarding the row's own `evidence_grade` field
entirely rather than reading it — so the string `query_insights.ts` (`platform/src/lib/retrieval/
registry/layers/L5_mimamsa/query_insights.ts:102-137`) serves verbatim in `insight_units[]` carries
no information distinguishing "empirical because ≥5 outcomes were confirmed/partial/denied" from
"empirical because ≥5 predictions were merely assigned, zero of which have been scored" — the exact
ambiguity C1/C2 named, now correctly diagnosed as an **earned-signal defect** (§N.8: "every status/
grade must be computed by a detector that measures the specific claim it asserts") rather than a
population-vs-chart-scope defect.

## 2. Files to change

All four files are inside S3's declared lease (`L5_mimamsa/**` maps to the `mi_*` python-sidecar
writers by extension of L5 asset ownership, per `DIAGNOSIS.md` §5 — no cross-stream lease conflict).

### 2a. `platform/python-sidecar/pipeline/orchestrator/writers/mi_sambandha.py` — earn the grade

**What:** track a third counter, `scored`, alongside the existing `fire`/`opp` counters in the
per-`(origin_kind, origin_ref, channel_id, domain)` aggregation loop (currently lines 68-84), and
gate the grade on it instead of on `opp`.

Current (lines 76-84):
```python
if key not in counts:
    counts[key] = {"fire": 0, "opp": 0}

counts[key]["opp"] += 1
verdict = row.get("composite_verdict") or ""
ch_fired = row.get("manifestation_channel") or ""
if verdict in ("confirmed", "partial") and ch_fired == channel_id:
    counts[key]["fire"] += 1
```
Fixed:
```python
if key not in counts:
    counts[key] = {"fire": 0, "opp": 0, "scored": 0}

counts[key]["opp"] += 1
verdict = row.get("composite_verdict") or ""
ch_fired = row.get("manifestation_channel") or ""
if verdict in ("confirmed", "partial", "denied"):
    counts[key]["scored"] += 1
if verdict in ("confirmed", "partial") and ch_fired == channel_id:
    counts[key]["fire"] += 1
```
Current (lines 90-96):
```python
opp = cnts["opp"]
fire = cnts["fire"]
propensity = fire / opp if opp > 0 else None
prior = _PRIOR_PROPENSITIES.get(domain, _PRIOR_PROPENSITIES["default"]).get(channel_id, 0.5)
delta = round(propensity - prior, 4) if propensity is not None else None
n = opp
grade = "empirical" if n >= 5 else "prior_only"
```
Fixed:
```python
opp = cnts["opp"]
fire = cnts["fire"]
scored = cnts["scored"]
propensity = fire / opp if opp > 0 else None
prior = _PRIOR_PROPENSITIES.get(domain, _PRIOR_PROPENSITIES["default"]).get(channel_id, 0.5)
delta = round(propensity - prior, 4) if propensity is not None else None
n = opp
grade = (
    "empirical" if scored >= 5
    else "assignment_only" if opp >= 5
    else "prior_only"
)
```
**Why:** `"empirical"` must mean "≥5 of this chart's own predictions have a recorded confirmed/
partial/denied outcome" (a real detector for outcome-groundedness), not "≥5 predictions happened to
be assigned to this channel" (a proxy that a zero-outcome chart satisfies trivially — exactly
`DIAGNOSIS.md`'s reproduced case, chart `1c826d5a`, `calibration_summary.total_matches: 0`). The new
`"assignment_only"` tier is itself the disambiguating marker C1/C2 asked for — folded into the
existing `evidence_grade` taxonomy per the task brief's own named alternative, grounded in the real
mechanism rather than a fabricated population axis.

**Also:** persist `scored` as a new `scored_count` column (§2c migration) on both the aggregation-
loop insert tuple (append after `opp`, before `channel_propensity`) and the prior-seed loop's insert
tuple (append `0`, lines ~123-141 — seeded prior-only rows have zero everything). This makes the
grade auditable against a real stored number, not just an in-memory Python variable that vanishes
after the writer runs (B.3 derivation-ledger spirit: a grade should trace to a number a later reader
can check).

### 2b. `platform/python-sidecar/pipeline/orchestrator/writers/mi_darshana.py` — stop discarding the grade

**What:** widen the manifestation-grammar SELECT to also pull `scored_count` and both grade tiers,
and pass the row's own `evidence_grade` through instead of hardcoding.

Current (lines 147-154):
```python
cur.execute(
    "SELECT channel_id, domain, channel_propensity, prior_propensity, "
    "       n_support, evidence_grade "
    "FROM mimamsa_manifestation_grammar WHERE chart_id = %s "
    "AND evidence_grade = 'empirical' ORDER BY n_support DESC LIMIT 20",
    (chart_id,),
)
gram_rows = cur.fetchall()
```
Fixed:
```python
cur.execute(
    "SELECT channel_id, domain, channel_propensity, prior_propensity, "
    "       n_support, scored_count, evidence_grade "
    "FROM mimamsa_manifestation_grammar WHERE chart_id = %s "
    "AND evidence_grade IN ('empirical', 'assignment_only') ORDER BY n_support DESC LIMIT 20",
    (chart_id,),
)
gram_rows = cur.fetchall()
```
(`'assignment_only'` rows must still be served, per §N.6 — a lower-density row is disclosed and
flagged, never silently dropped — this is why the filter widens rather than staying `= 'empirical'`.)

Current (lines 170-184, inside the per-row loop):
```python
n = r.get("n_support") or 0
statement = (
    f"For {dom} events, the '{ch}' channel fires with {prop:.0%} propensity "
    f"(n={n}, empirical learning)."
)
insight_id = f"gram_{dom}_{ch[:20]}_{i}"
rows.append((
    chart_id, insight_id, "manifestation_grammar",
    dom, None, None,
    statement,
    prop,
    None,   # confidence_band
    n,
    "not_assessed",
    "empirical",
    ...
```
Fixed:
```python
n = r.get("n_support") or 0
grade = r.get("evidence_grade", "prior_only")
scored = r.get("scored_count") or 0
if grade == "empirical":
    statement = (
        f"For {dom} events, the '{ch}' channel fires with {prop:.0%} propensity "
        f"(n={scored} outcome-scored predictions, empirical learning)."
    )
else:  # assignment_only — honest, not a promoted 'empirical' claim (§N.7 item 6)
    statement = (
        f"For {dom} events, the '{ch}' channel has been assigned to {n} predictions "
        f"with no outcomes scored yet — insufficient evidence for an empirical grade "
        f"(prior-based estimate: {prop:.0%})."
    )
insight_id = f"gram_{dom}_{ch[:20]}_{i}"
rows.append((
    chart_id, insight_id, "manifestation_grammar",
    dom, None, None,
    statement,
    prop,
    None,   # confidence_band
    n,
    "not_assessed",
    grade,
    ...
```
**Why:** this is the exact line (184) that discarded the row's real grade and the exact sentence
(171-174) that claimed "empirical learning" regardless of whether any outcome was ever scored — a
§N.7 item 4/6 narration-fidelity defect one layer inside the §N.8 earned-signal defect fixed in
§2a. Once `evidence_grade` is passed through honestly, `query_insights.ts` needs **no code change**
of its own for the core fix — it already `SELECT`s and returns `evidence_grade` verbatim
(`query_insights.ts:105`, `insight_units: insightResult.rows` at :137).

### 2c. New migration — `scored_count` column

**File:** next available integer after HEAD at build time (HEAD is `572_...` as of this spec's
drafting — **Build must re-check the live migration directory before naming this file**, per
CLAUDE.md §N.4 "Surgical migrations, verified"; illustrative name
`573_mi_sambandha_scored_count.sql`). **Must NOT edit `platform/migrations/
352_mimamsa_sambandha.sql`** — already applied; CLAUDE.md §N.4 forbids editing an applied migration.

```sql
BEGIN;

ALTER TABLE mimamsa_manifestation_grammar
  ADD COLUMN IF NOT EXISTS scored_count int NOT NULL DEFAULT 0;

COMMENT ON COLUMN mimamsa_manifestation_grammar.evidence_grade IS
  '''empirical''|''assignment_only''|''prior_only'' — empirical requires scored_count >= 5 '
  '(confirmed/partial/denied outcomes), not just opportunity_count >= 5 assignments. '
  'See F-35 (00_ARCHITECTURE/briefs/parisesa/lanes/F-35/).';

COMMIT;
```
**Why:** additive, `IF NOT EXISTS`/`DEFAULT 0`-guarded — safe against re-run and against any
already-built chart's existing rows (they backfill to `0`, which is the honest default: nothing
verified they were scored, matching the pre-fix data's actual evidentiary state).

### 2d. `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_insights.ts` — surface the split as data, not just per-row text

**What:** add a small in-process aggregate (no new query — computed from `insightResult.rows`,
already fetched) so a caller sees the evidence-grade split without having to scan `insight_units[]`
row by row.

At the `return` block (currently lines 133-141):
```ts
return {
  content: {
    chart_id,
    insight_units:       insightResult.rows,
    calibration_summary,
    filters:             { insight_type, domain, min_rank, top_k, include_neg },
    total_returned:      insightResult.rows.length,
  },
  is_error: false,
}
```
Fixed (add one field, computed inline, zero new queries):
```ts
const evidence_grade_counts: Record<string, number> = {}
for (const row of insightResult.rows as Array<Record<string, unknown>>) {
  const g = String(row.evidence_grade ?? 'unknown')
  evidence_grade_counts[g] = (evidence_grade_counts[g] ?? 0) + 1
}

return {
  content: {
    chart_id,
    insight_units:       insightResult.rows,
    calibration_summary,
    evidence_grade_counts,
    filters:             { insight_type, domain, min_rank, top_k, include_neg },
    total_returned:      insightResult.rows.length,
  },
  is_error: false,
}
```
**Why:** §N.6 ("density signaling is data, not narration") — a structured `evidence_grade_counts`
object (e.g. `{structural: 5, empirical: 0, assignment_only: 1}`) lets a caller confirm at a glance
that the response mixes tiers, without depending on catching the per-row distinction. This is the
part of the task brief's ask ("explicit marker... so a caller... cannot momentarily conflate") this
spec keeps, reshaped around the real mechanism instead of the retired population-mining framing.

## 3. Exit tests (both fail today, both named)

### 3a. `platform/python-sidecar/tests/test_mi_sambandha.py` (NEW FILE)

```python
"""
test_mi_sambandha.py — hermetic test for the F-35 earned-signal fix.

mi_sambandha's grade predicate (n = opp, the raw assignment count) granted
"empirical" on assignment count alone, with zero regard for whether any
assignment carries a scored composite_verdict ('confirmed'|'partial'|'denied' —
platform/migrations/348_mimamsa_pramana.sql:17; 'pending'/no-row are NOT scored).
This drives run() with 9 assignments to one channel, none of them scored (the
LEFT JOIN finds no mimamsa_calibration row for any of them — mirroring F-35's
live repro chart 1c826d5a, calibration_summary.total_matches=0), and asserts
the grammar row grades 'assignment_only', not 'empirical'.
"""
from __future__ import annotations

from pipeline.orchestrator.writers.mi_sambandha import MiSambandhaWriter

NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

# Mirror the INSERT column list in mi_sambandha.py post-fix (§2a/§2c add
# scored_count at index 7, shifting evidence_grade from 12 to 13).
CHANNEL_ID, EVIDENCE_GRADE = 3, 13


class _FakeCursor:
    def __init__(self, conn):
        self._conn = conn
        self._result: list = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if "FROM mimamsa_manifestation_sets" in s:
            self._result = list(self._conn.mset_rows)
        else:
            self._result = []

    def fetchall(self):
        return list(self._result)

    def executemany(self, sql, params_list):
        if "INSERT INTO mimamsa_manifestation_grammar" in " ".join(sql.split()):
            self._conn.inserted_rows.extend(params_list)


class _FakeConn:
    def __init__(self, mset_rows):
        self.mset_rows = list(mset_rows)
        self.inserted_rows: list[tuple] = []

    def cursor(self, row_factory=None):
        return _FakeCursor(self)


class _FakeCtx:
    def __init__(self, chart_id, db_conn, dry_run=False):
        self.config = {"chart_id": chart_id}
        self.db_conn = db_conn
        self.dry_run = dry_run


def _unscored_assignment(i, channel_id="ch_career_verbal", domain="career"):
    # LEFT JOIN mimamsa_calibration finds no row -> both fields NULL.
    return {
        "prediction_id": f"pred_{i}",
        "channel_id": channel_id,
        "domain": domain,
        "is_literal": True,
        "composite_verdict": None,
        "manifestation_channel": None,
    }


def test_nine_unscored_assignments_do_not_earn_empirical_grade():
    """FAILS TODAY: opp=9 >= 5 -> grade='empirical' with zero scored outcomes.
    AFTER FIX: grade must be 'assignment_only' -- 'empirical' is reserved for
    >=5 SCORED (confirmed/partial/denied) outcomes, not raw assignment count."""
    rows = [_unscored_assignment(i) for i in range(9)]
    conn = _FakeConn(rows)
    ctx = _FakeCtx(NATIVE_CHART_ID, conn, dry_run=False)

    MiSambandhaWriter().run(ctx)

    grammar_row = next(r for r in conn.inserted_rows if r[CHANNEL_ID] == "ch_career_verbal")
    assert grammar_row[EVIDENCE_GRADE] == "assignment_only"


def test_five_scored_assignments_do_earn_empirical_grade():
    """Boundary/regression guard: >=5 SCORED outcomes must still grade
    'empirical' -- this fix narrows the gate, it must not break the genuine
    positive case. 3 confirmed + 2 denied = 5 scored, non-matching channel on
    the denied ones so fire_count stays low (irrelevant to the grade check)."""
    rows = (
        [{"prediction_id": f"c{i}", "channel_id": "ch_career_verbal", "domain": "career",
          "is_literal": True, "composite_verdict": "confirmed",
          "manifestation_channel": "ch_career_verbal"} for i in range(3)]
        + [{"prediction_id": f"d{i}", "channel_id": "ch_career_verbal", "domain": "career",
            "is_literal": True, "composite_verdict": "denied",
            "manifestation_channel": "ch_career_material"} for i in range(2)]
    )
    conn = _FakeConn(rows)
    ctx = _FakeCtx(NATIVE_CHART_ID, conn, dry_run=False)

    MiSambandhaWriter().run(ctx)

    grammar_row = next(r for r in conn.inserted_rows if r[CHANNEL_ID] == "ch_career_verbal")
    assert grammar_row[EVIDENCE_GRADE] == "empirical"
```

**Confirmed fails today:** on today's code, `grade = "empirical" if n >= 5 else "prior_only"` with
`n = opp = 9` yields `"empirical"` for the first test regardless of scoring — the assertion
`== "assignment_only"` fails (actual value `"empirical"`). Today's code also has no `"assignment_only"`
branch and no `scored_count` column/index at all, so the module-level `EVIDENCE_GRADE = 13` index
itself points past the current 15-element tuple's `citation_ref`/`grammar_formula_version` boundary
— confirming the test targets code that does not yet exist.

### 3b. Extend `platform/python-sidecar/tests/test_mi_darshana.py` (existing file, new test)

Extend the existing `_grammar_row` helper (currently hardcodes `"evidence_grade": "empirical"`
internally) to accept an override, backward-compatible with every existing call:
```python
def _grammar_row(channel_propensity, prior_propensity, channel_id="ch1", domain="career", n=10,
                  evidence_grade="empirical"):
    return {
        "channel_id": channel_id,
        "domain": domain,
        "channel_propensity": channel_propensity,
        "prior_propensity": prior_propensity,
        "n_support": n,
        "scored_count": 0,
        "evidence_grade": evidence_grade,
    }
```
Add:
```python
EVIDENCE_GRADE = 11  # mirror the INSERT column list in mi_darshana.py (unaffected by §2c)

def test_assignment_only_grade_passed_through_not_hardcoded_empirical():
    """FAILS TODAY: mi_darshana.py:184 hardcodes 'empirical' regardless of the
    source row's own evidence_grade. AFTER FIX: an 'assignment_only'-graded
    grammar row must surface as 'assignment_only' in mimamsa_insight_units, not
    be silently promoted to 'empirical'."""
    conn, result = _run_grammar([
        _grammar_row(channel_propensity=0.0, prior_propensity=0.4, evidence_grade="assignment_only")
    ])

    assert result.rows_inserted == 1
    row = conn.inserted_rows[0]
    assert row[EVIDENCE_GRADE] == "assignment_only"
    assert "empirical learning" not in row[STATEMENT]
```
**Confirmed fails today:** line 184 of `mi_darshana.py` inserts the literal `"empirical"` regardless
of `r.get("evidence_grade")` — today `row[EVIDENCE_GRADE]` is `"empirical"`, not
`"assignment_only"`, and the statement always reads "...empirical learning." for every
manifestation-grammar row it emits — both assertions fail on today's code.

## 4. Sibling sites covered (from `DIAGNOSIS.md` §4)

| Site | Disposition |
|---|---|
| `mi_sambandha.py:95-96` (`mimamsa_manifestation_grammar`) | **Fixed — §2a.** This finding. |
| `mi_darshana.py:151,184` (manifestation-grammar → `mimamsa_insight_units`) | **Fixed — §2b.** The C1/C2 serving-adjacent site. |
| `query_insights.ts` (`mimamsa_insight_get`) | **Fixed — §2d** (aggregate summary; core passthrough needs no change, §2b explains why). |
| `mi_darshana.py` emergent-law block (`mimamsa_discoveries` → `emergent_law` insights, same `"empirical" if n >= 5` textual pattern) | **Excluded, with reason.** `DIAGNOSIS.md` §4 flagged this as a "candidate sibling, not confirmed" — `n` there sources from `mi_pariksha.py`'s own retrodiction/pattern-mining `n_support`, not traced within Stage-D's budget. Fixing it here would require an unverified assumption about `mi_pariksha.py`'s semantics (Stage-R Q7 would fail this). Recommend a fresh Stage-D pass on `mi_pariksha.py` before any fix; not touched by this spec's Build. |
| `mi_pramana.py:454-474` (`mimamsa_reliability` → `calibrated_outlook` insights) | **Excluded — not a defect.** `DIAGNOSIS.md` §4 confirmed this is the clean, correct-pattern sibling: `n = len(items)` over real `mimamsa_calibration` rows with `hit = (verdict == "CONFIRMED")` — genuinely outcome-derived already. No change. |
| `query_calibration.ts` (`mimamsa_calibration_get`) | **Excluded — separate capability, out of F-35's own claim.** Reads `evidence_grade` from `mimamsa_reliability`, which is confirmed clean (row above) — no known defect today. `DIAGNOSIS.md` §4 flags the *shape* (mixing multiple source tables) as worth a one-line follow-up note only; recommend a new finding if a future writer ever feeds `mimamsa_reliability` a proxy-graded value. |
| `query_manifestation_grammar.ts` | **Excluded — not applicable.** Single-source (`mimamsa_manifestation_grammar` only), no tier mixing, confirmed by `DIAGNOSIS.md` §4. Note: after §2a lands it will start returning `"assignment_only"`-graded rows verbatim (it already selects `evidence_grade` — `query_manifestation_grammar.ts:95`) — this is more honest data than before, not a regression, and needs no code change. |

No other file in the S3 lease (`L4_phala/**`, `ph_nimitta/**`, `muhurta.py`) touches
`mimamsa_insight_units` or `mimamsa_manifestation_grammar` (`DIAGNOSIS.md` §4).

## 5. Recurrence guard

`3a`'s two tests together are the guard: `test_nine_unscored_assignments_do_not_earn_empirical_grade`
fails closed the moment anyone reverts the predicate to gate on `opp`/assignment count again, and
`test_five_scored_assignments_do_earn_empirical_grade` fails closed if a future edit over-corrects
and stops granting `"empirical"` to genuinely-scored data (guards the positive case, not just the
negative one — the same "grade a real detector, not a proxy" property in both directions). `3b`'s
test guards the adjacent pass-through defect independently: any future re-introduction of a
hardcoded `evidence_grade` literal in `mi_darshana.py`'s manifestation-grammar block fails it
immediately, regardless of what `mi_sambandha.py` computes.

## 6. Dependencies and rollback

**Dependencies:** none on other in-flight S3 lanes — `DIAGNOSIS.md` §5 confirms no other stream
claims `mi_sambandha.py`/`mi_darshana.py`/`query_insights.ts`, and no CL-00 control asserts on
`mimamsa_insight_get`'s `insight_units[]` shape or `mi_sambandha`'s grade computation. §2c's
migration number must be re-checked against the live `platform/migrations/` HEAD at build time
(other PARISESA lanes may claim numbers concurrently) — do not hardcode `573` blindly.

**Rebuild dependency — PENDING NATIVE PERMISSION (ND-PARISESA-1), do not trigger.** This fix is
writer-level (`mi_sambandha.py`/`mi_darshana.py`, both `@register` orchestrator writers): existing
built charts keep their stale `"empirical"` grade and hardcoded narration until `mi_sambandha` →
`mi_darshana` are rebuilt for them (per-chart delete-then-insert, §N.3). Per the campaign-binding
native directive (`00_ARCHITECTURE/briefs/parisesa/NATIVE_DIRECTIVE_NO_REBUILD_WITHOUT_PERMISSION.md`),
**Stage V must NOT trigger a rebuild** to manifest this fix on already-built charts — the exit
tests in §3 verify correctness hermetically (fresh writer invocation in a test harness) and that
is sufficient for Stage R/B. Live-chart verification (canonical `482012f1-…` and diagnosis chart
`1c826d5a-…`) is honestly reported as **PENDING** in Stage V's evidence file, not skipped, faked,
or silently triggered — it proceeds only once the conductor relays explicit native permission for
a batched rebuild covering this and any other in-flight writer-level S3 fix that turns out to need
one (F-117/`bo_upaya` confirmed shares this gate; F-68/F-69 do NOT — both were specced as
read-boundary/serving-layer fixes requiring no rebuild — see LEDGER_S3.md's rebuild-dependency
table for the full per-lane breakdown).

**Rollback:** revert the code commit(s). The `scored_count` column (§2c) is additive and
`DEFAULT 0`-guarded — safe to leave in place even if the code is rolled back (older code simply
never reads it). If the migration itself must be rolled back:
`ALTER TABLE mimamsa_manifestation_grammar DROP COLUMN IF EXISTS scored_count;` — no data loss
beyond that one column. No schema or contract change to any table or tool outside this lane's four
files.

## 7. Coverage table — every D-2 sub-claim mapped

| Sub-claim | Spec element |
|---|---|
| C1 — response mixes chart-specific `structural` insights with `evidence_grade='empirical'` manifestation-grammar insights in one undifferentiated `insight_units[]` array | §2a (grade now split into two honest tiers) + §2b (tier passed through, not collapsed) + §2d (aggregate summary makes the mix visible without per-row scanning) |
| C2 — no inline marker disambiguates the "empirical" grade, so a caller filtering on `evidence_grade` alone could momentarily conflate the two | §2a + §2b — `evidence_grade` itself becomes the honest marker (`'empirical'` now means *only* ≥5 scored outcomes); §2d adds the structured summary on top |
| C3 — corpus's causal claim that "empirical" reflects population-level cross-chart mining | **Retired, not fixed** — `DIAGNOSIS.md` §6 found this false (everything is chart-scoped by construction); §0 of this spec records the retirement and the corrected mechanism C1/C2 are actually closed against |
