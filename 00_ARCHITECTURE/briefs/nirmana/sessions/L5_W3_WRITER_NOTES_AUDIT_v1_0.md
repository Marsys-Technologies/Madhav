---
artifact: L5_W3_WRITER_NOTES_AUDIT_v1_0.md
canonical_id: NIRMANA_L5_W3_WRITER_NOTES_AUDIT
version: "1.0"
status: CURRENT — W3 IMPLEMENT batch 3 spec, L5 (Mīmāṃsā)
session: L5
produced_on: 2026-09-05
ruling: >
  Adjudication #1738 (L5-filed, Conductor-ruled): WriterResult.notes is write-only across the
  codebase; `notes` is documentation, never a signal; any condition that should stop or degrade a
  build must RAISE. Each layer audits its own writers as W3 work and reports counts. The
  orchestrator-side `degraded` flag is PARKED to the native (frozen writer contract).
scope: 14 mi_* writers + services/mi_bhara/ + services/mi_sankalpa/
---

# L5-W3 — `WriterResult.notes` degradation audit

## Counts (reported to #1738)

| category | count |
|---|---|
| **A — disguised failure, must raise** | **10 sites across 7 of 14 writers** |
| **B — honest degradation, correctly non-fatal (leave + disclose)** | 17 sites |
| **C — purely informational (leave)** | 10 sites |
| **UNKNOWN** | 1 site |
| **Exception swallows (separate class)** | 18 substantive across 7 writers, + 4 benign |

Total `notes=` sites on a `WriterResult`: **38**. 27 of 38 are correctly left alone — the ruling's
"judgement, not a blanket rewrite" was the right call.

**Correction to the filing's own wording:** there are **zero bare `except:` clauses** in L5; all 22
handlers are `except Exception` or `except ValueError`. The defect is identical; the wording was
loose and should not survive into the Conductor's detector spec.

## The line L5 drew — mechanically checkable, and it may transfer

> **A table-existence guard is an *inability* check. A per-chart row-count guard is a *state* check.**

Every A falls on the first side, every B on the second. `mi_vistara.py:50-53` raises on a
table-existence guard (the correct precedent); `mi_bhara`'s LEL-absent branch returns a note on a
row-count guard (also correct). Only three sites needed judgement beyond this line.

## Category A — the 10 must-raise sites

| # | site | condition | why green misleads |
|---|---|---|---|
| A1 | `mi_seva.py:56-65` | any of 4 required tables absent | the writer's *entire* job is verifying serve-time apply infrastructure; a missing table means the verification could not run. Sibling `mi_vistara` raises on the identical check. |
| A2 | `mi_sankalpa.py:104-113` (`NOTE_LEDGER_TABLE_ABSENT`) | ledger table absent | zero rows reads as "this native filed no interventions" — a different claim from "the table does not exist" |
| A3 | `mi_bhara.py:189-199` (`NOTE_SKILL_TABLES_ABSENT`) | migration 497 not applied | phases 2–5 are the writer's whole output |
| A4 | `mi_bhara.py:119-131` (`NOTE_FIELD_ABSENT`) | `kala_field` absent | the docstring's justification **has expired**: `ka_kshetra` is now a declared, DEP-ASSERT-gated dependency, so an absent table is a deployment defect, not a chart state |
| A5 | `mi_bhara.py:356-360` (`NOTE_BIO_JOIN_DEFERRED`) | `-1` sentinel from `upsert_biographical_echo_insights` | `-1` means "could not run"; reported on a result whose `rows_inserted` is the *fit* count, so a healthy positive row count can coexist with phase 4 never executing. **Lowest-confidence A — held pending Conductor word (see below).** |
| A6 | `mi_bhavisya.py:62-68` | `phala_anchors` absent | L4 is CLOSED and three `ph_*` assets are declared deps. The per-chart-empty case is **already handled separately at :78-84**, so this branch only masks a schema failure |
| A7 | `mi_pramana.py:285-288` | `mimamsa_predictions` absent | three substeps each report an honest-looking zero when the truth is "the input table does not exist" |
| A8 | `mi_jivanaghatana.py:206-228`, **`expected_rows > 0` sub-path only** | zero events built but `life_events` has rows | the code says so itself at :214-220 — *"This is NOT a healthy empty build."* The detector exists and its finding goes nowhere |
| A9 | `mi_jivanaghatana.py:329-335` | `raw_events` non-empty, `rows` empty | the note text is **factually false** here: events were found and every one was discarded |
| A10 | `mi_darshana.py:751-764` (`_substep_views_verify`) | any of 4 serving views fails to query | a substep *named* verify catches a broken view, embeds the error in a note nothing reads, and returns success. §N.8 verbatim |

Exact raise text for each is recorded in the W3 implementation PR.

**A8 is a split, not a whole site:** the `expected_rows == 0` path stays exactly as it is (category
B — zero per-chart life events is the normal build for a non-native chart).

## The finding that never touched `notes`

**The worst instance of this defect class in L5 does not use the `notes` channel at all.**

- `mi_jivanaghatana.py:143-149` queries `brahma_event_ontology.category` / `.subcategory` —
  **neither column exists** (they are `lel_category` / `domain`). Returns `None` every call.
- `mi_pramana.py:90-96` queries `brahma_event_ontology.base_rate` — **no such column** (it is
  `base_rate_by_age`, jsonb, populated on all 27 rows). Returns `{}` every call.

They compound at `mi_pramana.py:388`:
`base_rate = float(base_rates.get(event_class_id, 0.10)) if event_class_id else 0.10` — both
branches resolve to the literal.

**Re-verified live by the L5 session (not taken on the audit's word):**

```
mimamsa_calibration: 57 rows
  base_rate = 0.10 ................. 57 / 57
  distinct base_rate values ........ 1
  brier_vs_null populated .......... 57 / 57
  distinct brier_vs_null values .... 46
```

A hardcoded `0.10` stands in as a **measured climatology base rate**, and `brier_vs_null` — the
skill-versus-null metric the whole L5 calibration loop rests on — is computed from it on every row.
**The 46 distinct brier values are what makes it invisible**: it looks like a real distribution
because the varying half *is* real and only the baseline is invented. The SAVEPOINT wrappers
guarantee the failure is survivable and therefore permanent. Live proof:
`mimamsa_event_provenance` = 64 rows, **0** with `event_class_id`.

**No replacement value is proposed.** Deriving a real base rate from `base_rate_by_age` is separate
work with its own correctness question; inventing one here would repeat the defect. The fix is:
correct the column names, delete the swallow, let a genuine failure propagate.

## Other swallow classes (recorded, lower priority)

- **Favourable-default swallows (§N.7 item 6):** `mi_pramana.py:151-152` returns `1.0` on a
  falsifier JSON parse failure — `1.0` means *"not falsified"*, the favourable verdict;
  `:117-118` returns a fabricated `0.5` mid-score straight into the weighted composite;
  `mi_jivanaghatana.py:74-77` returns `None` on a bad ISO string, which classifies **every** event
  as `training` — a malformed config value silently disables the leakage firewall.
- **Registry-fallback swallows:** four sites fall back to hardcoded defaults; two log a warning, two
  `pass` silently. None firing today (all constants present), but a deliberately tuned registry
  weight could be ignored with no trace.
- **Availability swallow:** `mi_gunanaka.py:382-388` — a failure to write
  `mimamsa_calibration_snapshot` (the two-key publication audit record) is a warning and the build
  succeeds. Its own docstring records that this handler already masked a real bug for an unknown period.
- **`mi_adhilepa` skips below the `notes` channel entirely:** four `_table_exists` guards
  (`:230, :268, :294, :314`) each skip a whole overlay category with **no note, no log, no counter**.

## `target_floor` cross-reference — and a distinct sub-defect

**12 of 14 L5 assets promote to `'lit'` on zero rows.** The other two (`mi_bhara`, `mi_sankalpa`)
carry `target_floor = NULL` rather than an explicit `0` and land in **perpetual re-queue**:
`zero_rows_is_complete` false → `dormant`; `plan.ts` treats `dormant` as a build candidate every
pass; and where `count_sql` targets an absent table the no-op-completion probe returns `None`, so it
never resolves. **`mi_sankalpa` is in that state in production now.**

A NULL floor is not a declaration that zero is correct — it is the *absence* of a declaration, and
it produces a third state neither `lit` nor `dormant` semantics were designed for. Migration **690**
sets both to an explicit `0`. **No other L5 floor value needs to change**: for the service assets
that legitimately write no build-time rows the floor stays 0 and the writer raises on inability,
which is exactly the ruling's requirement.

## Held / open

- **A5 (`NOTE_BIO_JOIN_DEFERRED`) is HELD** pending a Conductor word: if ṢAḌ-DARŚANA Lane D
  deployment is optional *by design* rather than merely not-yet-done, it is a B and raising would be
  wrong. `kala_insights` exists in production so raising is safe today either way. **Defaulting to
  leaving it as B and recording it** unless told otherwise.
- **UNKNOWN (1): `mi_bhavisya.py:227-233`** — reached when anchors exist but every one was skipped
  for missing timing. Live: **195/195 `phala_anchors` rows carry both `window_start` and
  `window_end`**, so the branch does not currently fire. *What would settle it:* whether
  `ph_nimitta`/`ph_phaladesa` can emit an untimed anchor by design.
- **`mi_seva.count_sql` counts the wrong table, unfiltered** — `SELECT count(*) FROM
  mimamsa_preferences` with no `WHERE chart_id = $1` on a `per_chart` asset, and that table is not
  one of the four the writer verifies. A §N.4 cockpit-truth defect independent of this ruling.
- **Not audited, declared:** the TypeScript serve-time paths. Whether the serve-time filing path has
  its own silent-degradation surface is an open question this audit did not answer.

## Recommendation carried to the Conductor's CI detector (#1738)

> **An exception handler that returns a substituted value and continues is a `notes=` with the
> string omitted.**

The `notes` rule alone closes the *channel*; this closes the *class*. Narrower high-yield version if
that is too broad: **flag any swallowed exception around a SQL execution** — L5's two worst
instances are both exactly that, and both are schema drift converted into a quiet constant, which
cannot be caught by reading the code, only by running it.
