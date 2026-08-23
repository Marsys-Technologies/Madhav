---
lane: F-78
stream: S3_SATYA
stage: D (DIAGNOSE) — COMPLETE
author: SATYA sub-agent (sonnet)
---

# F-78 — kala_field_snapshots.event_classes conflates "attempted" with "built",
no field-level disambiguation, no documented caller obligation to subtract
skipped_classes

## 1. Live reproduction (today, 2026-08-16, verified — DB-column finding, no MCP
tool call; direct read-only SQL per the assignment)

```sql
SELECT chart_id, array_length(event_classes,1) AS ec_len,
       jsonb_array_length(skipped_classes) AS n_skipped,
       event_classes, skipped_classes
FROM kala_field_snapshots
WHERE chart_id = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
ORDER BY built_at DESC LIMIT 1;
```

Raw result saved: `raw_reproduce.json` (this dir). Confirmed:
- `event_classes` (27 items) — the full canonical event-class list:
  `achievement_recognition, bereavement, birth_anchor, business_launch,
  career_advancement, career_change, career_entry, career_setback, childbirth,
  chronic_onset, education_milestone, exam_outcome, financial_deception,
  foreign_settlement, illness_acute, major_gain, major_loss, marriage,
  parental_event, property_acquisition, psychological_arc, relocation,
  romantic_start, separation, spiritual_turn, surgery, travel_event`.
- `skipped_classes` (21 items) — every entry `{"reason": "no_class_prior_row",
  "detail": "no bg_class_priors lifetime-count row for this event class",
  "event_class": "<name>"}`.
- `event_classes` minus `skipped_classes` = exactly **6**: `childbirth,
  foreign_settlement, marriage, relocation, separation, surgery` — matching the
  finding's claim precisely.

**CONFIRMED REPRODUCES.** Not ALREADY-FIXED. This is an honest-skip pattern by
design (per §2 below), not silent data loss — but the conflation the finding
names (event_classes = attempted, not built) is real and present exactly as
claimed.

## 2. Claim decomposition

- **C1** — `event_classes` declares 27 classes; only 6 have actual rows in
  `kala_field`/`kala_field_null`; the other 21 are honest-skips recorded in
  `skipped_classes` with reason `no_class_prior_row`.
- **C2** — this is NOT silent data loss (the skip is recorded, logged, and
  reasoned) — it is a **naming/documentation conflation**: `event_classes` reads
  as "classes this snapshot covers" when it actually means "classes this writer
  attempted," with no field-level comment and no documented caller obligation to
  compute `event_classes − skipped_classes` before treating the column as the
  built set.
- **C3** — no serving-layer TypeScript code currently reads
  `kala_field_snapshots.event_classes`, so the defect is presently dormant, not
  user-facing — but any future reader risks misreporting build coverage.

## 3. Mechanism (file:line, read directly — confirms the audit's line pin was
already accurate; corrects only the vagueness in the truncated docstring
quote)

Writer: `platform/python-sidecar/services/ka_kshetra/writer.py`.

**Discovery (the "attempted" set).** `_discover_event_classes` (static method,
line 2186):

```python
@staticmethod
def _discover_event_classes(conn, chart_id) -> list[str]:
    """LIVE discovery from Lane A's promise register — never a hardcoded list.
    ...ALL event classes with a bodha_pratijna row are discovered, regardless
    of status..."""
    cur.execute(
        'SELECT DISTINCT event_class_id FROM bodha_pratijna '
        'WHERE chart_id = %s ORDER BY event_class_id', (chart_id,))
    classes = [r['event_class_id'] for r in S4._rows(cur)]
    ...
    return classes
```
(lines 2201–2220, docstring 2186–2200). This is a *candidate* list — every class
with any `bodha_pratijna` row, unconditionally, "regardless of status" per the
docstring's own words. It is assigned to `self._event_classes` at **line 285**:
`self._event_classes = self._discover_event_classes(conn, self._chart_id)`.

**Honest-skip mechanism.** `ClassSkipped` is raised by
`platform/python-sidecar/services/ka_kshetra/stage4_field.py`'s `_lifetime_count`
helper (or equivalent hazard-prior lookup) at **line 734**:
```python
raise ClassSkipped(event_class, 'no_class_prior_row',
                   'no bg_class_priors lifetime-count row for this event class')
```
— exactly the reason/detail text confirmed live in §1. `ClassSkipped`'s own
docstring (`stage4_field.py` lines 128–134) states its purpose precisely: *"Not an
error condition to be swallowed: the reason is recorded on
`kala_field_snapshots.skipped_classes` so a reader sees WHY a class has no
windows rather than inferring the chart has no hazard for it (LAW ZERO)."* Caught
in `writer.py`'s `_record_skip` (line 1962): appends `{'event_class', 'reason',
'detail'}` to `self._skipped` and logs a warning explicitly naming
`kala_field_snapshots.skipped_classes` as the recording target (lines 1962–1970).

**The write itself.** `_run_snapshot` (`writer.py` line 1732), the INSERT at
**lines 1745–1761**:

```python
cur.execute(
    """INSERT INTO kala_field_snapshots (
           chart_id, field_snapshot_id, field_content_hash, weights_version,
           x_schema_version, corpus_pin, config_pin, cohort_version,
           substrate_build_ids, hashed_tables, event_classes, skipped_classes,
           horizon_days)
       VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s::jsonb,%s,%s,%s::jsonb,%s)
       ON CONFLICT (chart_id, field_snapshot_id) DO UPDATE SET
           field_content_hash = EXCLUDED.field_content_hash,
           skipped_classes = EXCLUDED.skipped_classes,
           event_classes = EXCLUDED.event_classes,
           built_at = now()""",
    (self._chart_id, self._snapshot_id, content_hash, self._weights_version,
     hazard.X_SCHEMA_VERSION, self._pins.corpus_pin,
     json.dumps(dict(self._pins.config_pin)), self._pins.cohort_version,
     json.dumps({}), list(_HASHED_TABLES),
     list(self._event_classes), json.dumps(self._skipped), HORIZON_DAYS),
)
```

`list(self._event_classes)` — the full 27-item discovery-time candidate list,
**unconditionally**, is bound at **line 1760**. It is never filtered against
`self._skipped` before this write. The audit corpus's pin ("line ~1760") is
confirmed **accurate as-is** — no correction needed there, unlike F-34's pin. The
one thing the corpus left truncated ("nothing enforces event_cl[ass
subtraction]...") is now closed: nothing in `writer.py`, `stage4_field.py`, or
the INSERT statement itself performs or documents a `event_classes −
skipped_classes` step. `self._skipped` and `self._event_classes` are two
independently-populated lists that happen to be written to the same row; no code
path relates one to the other at write time. (There IS a read-time use of the
relationship elsewhere in the writer — line 1182-1183 and line 1983 both compute
`{s['event_class'] for s in self._skipped}` locally to decide what to iterate/
build next — but that derived set is never itself persisted or exposed; a
consumer of the stored row has no equivalent without recomputing the same
set-difference the writer already had in memory and discarded.)

## 4. Sibling census

**TS-consumer re-verification (per the assignment's explicit ask):**
```
grep -rn "event_classes" platform/src platform-mcp/src
grep -rn "kala_field_snapshots" platform/src platform-mcp/src
```
Confirmed **zero** TypeScript readers of the `kala_field_snapshots.event_classes`
or `.skipped_classes` columns specifically:
- `platform/src/lib/event_classes.ts` — an unrelated static TS mirror of the
  27-class taxonomy (compile-time constant, not a DB read).
- `platform-mcp/src/tools/retrieval/register_gochara_windows.ts`'s
  `event_classes_covered` / `event_classes_targeted_not_swept` — derived from
  `gochara_resonance_map` / `build_substep_progress` (a **different** table
  family, `gochara_*`, F-34's own file) — not `kala_field_snapshots`.
- `platform-mcp/src/lib/kala_envelope.ts` and
  `platform/src/app/api/mcp/db/query/route.ts` are the only two files that
  actually query `kala_field_snapshots` — both select only
  `field_snapshot_id, field_content_hash` (confirmed by direct grep of both
  files); neither touches `event_classes` or `skipped_classes`.
- `platform-mcp/src/tools/kala_views/*.test.ts` references to
  `kala_field_snapshots` are all about the "no row yet" honest-empty path
  (`field_snapshot_reason`), not the columns in question.

**C3 (zero TS consumers) is CONFIRMED, independently re-verified — not inherited
from the corpus unchecked.**

**Same-writer sibling check** — does any other `kala_*` snapshot/summary column
in `writer.py` suffer the identical "attempted list written unconditionally,
built list requires a subtraction the schema doesn't do for the caller" shape?
Grep of `writer.py` for other unconditional list-writes alongside a
skip/exception-tracking list found none — `hashed_tables` (line 1759,
`list(_HASHED_TABLES)`) is a static module-level constant, not a discover-then-
skip pair; `substrate_build_ids` is written as `{}` (unused placeholder). No
other column in this INSERT shares the two-independent-lists shape. This appears
to be a single-site defect, not a class with siblings inside `ka_kshetra`.

## 5. Blast radius

- CL-00 controls: no known control asserts on `kala_field_snapshots.event_classes`
  or `.skipped_classes` (checked `platform/scripts/governance/` control
  headings) — zero risk of control regression from documenting or fixing this.
- Other lanes sharing this file: `writer.py` and `stage4_field.py` are inside
  S3's declared lease (`platform/python-sidecar/services/ph_nimitta/**` /
  `muhurta.py` are the named S3 L4/L5 files, but S6 (ĀDHĀRA) owns
  `platform/python-sidecar/ga_writers/**` and `pipeline/orchestrator/writers/**`
  — `ka_kshetra` is an L3 Kāla service directory, not explicitly claimed in any
  stream's OWNS list in the plan; flag `PAR-F78-NEEDS-LEASE
  platform/python-sidecar/services/ka_kshetra/writer.py` per plan §2.1's rule,
  since this file is not one of S3's listed OWNS paths (`L4_phala/**`,
  `L5_mimamsa/**`, `ph_nimitta/**`, `muhurta.py`) — it is L3, not L4/L5.
- Because C3 confirms zero live TS consumers, a fix here is schema/writer-only
  (add a computed `built_event_classes` column or a doc comment plus a
  recurrence-guard test) with no downstream serving-layer change required — low
  blast radius on any currently-running query surface.
- Risk if unfixed: the very next TS surface that reads this column (e.g. a
  future coverage-reporting tool) will misreport build coverage exactly the way
  F-34's `gochara_forecast_get` and its siblings misreport horizon coverage — the
  same CL-13 defect class, latent rather than live.

## 6. Note on lease scope

Unlike F-35 (squarely `L5_mimamsa/**`, S3-owned) and F-34/others in
`gochara_forecast_get` (also S3-owned per plan §2's CL-13 list), F-78's owning
file — `platform/python-sidecar/services/ka_kshetra/writer.py` /
`stage4_field.py` — is an **L3 Kāla** service, not enumerated in S3's OWNS list
(`L4_phala/**`, `L5_mimamsa/**`, `ph_nimitta/**`, `muhurta.py`). The finding
itself is legitimately CL-13-class (missing disclosure / attempted-vs-built
conflation), matching S3's charter — but the file is out of S3's declared file
lease per §2.1's ordered-handoff rule. Recommend the conductor either (a)
re-lease this one file to S3 for this lane only (it is a documentation/schema-
comment fix with no cross-file blast radius per §5), or (b) hand the completed
spec to whichever stream's OWNS list actually covers L3 `ka_kshetra` service
code (not clearly named in any of the six streams' OWNS lists in the plan as
read — worth flagging to the conductor/PRATINIDHI rather than guessing).
