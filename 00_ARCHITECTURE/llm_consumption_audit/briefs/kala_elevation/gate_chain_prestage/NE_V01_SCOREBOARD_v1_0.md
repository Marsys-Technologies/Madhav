---
artifact: NE_V01_SCOREBOARD (ṢAḌ-DARŚANA skill/GOF scoreboard, ne_v01 N_e-prior generation)
canonical_id: NE_V01_SCOREBOARD
version: 1.0
status: LIVE — first publication, GATE-1 builder session, 2026-08-06
schema: kala_field_skill / kala_field_gof (KALA_W2_FIELD_DESIGN_v1_0.md §7.3), refined to a
  three-state cell vocabulary (score / underpowered(n) / empty-no-overlap) per this session's
  governing brief. Every number below is a live query against production Postgres, cited by
  table; nothing here is estimated or carried over from a prior report without re-verification.
---

# ne_v01 Skill/GOF Scoreboard — both canonical charts

## Provenance note (read before trusting this artifact's "ruling" citation)

This scoreboard's governing brief cited it as built "per ruling R1 (three-refinement ruling in
the ledger)." A targeted search of `SHAD_DARSHANA_STATE.md` (full 3,385-line file, current
`origin/shad-darshana/integration` tip `39105d7c`), all 18 numbered ADJUDICATION rulings, the
five dedicated `SHAD_DARSHANA_ADJUDICATION_*` artifacts, `SHAD_DARSHANA_BRIEF_v2_0.md`,
`SHAD_DARSHANA_NIGHT_RUN_v1_0.md`, `KALA_W2_FIELD_DESIGN_v1_0.md`, and
`PRODUCTION_GATE_EXECUTION_POLICY_v1_0.md` found **no artifact literally labeled "R1"** and no
separate ruling document containing the exact three-state vocabulary
(`score` / `underpowered(n)` / `empty-no-overlap`) or the "baselines per (chart × scope),
permanent for scope" framing. The nearest ratified precedent is
`KALA_W2_FIELD_DESIGN_v1_0.md` §7.3's own three-state `skill_state`
(`established` / `not_established` / `underpowered`) and `gof_state`
(`pass` / `fail` / `underpowered`) design, with `n_e < 8` as the underpowered threshold, and
E7.5's "first published SS per chart becomes the CI baseline" regression-gate rule — both
ratified, both cited below.

**Disclosed, not silently assumed:** the specific refinement this scoreboard implements —
splitting the design's single `underpowered` state into `underpowered(n)` (a class with a real
N_e prior and a real field, scored zero or few times) versus `empty-no-overlap` (a class with
**no** N_e prior overlap at all, structurally unscoreable until the corpus widens) — is taken
from this session's own governing brief, not from a separately-citable ledger ruling I could
independently verify existed beforehand. Per `PRODUCTION_GATE_EXECUTION_POLICY_v1_0.md` §2's
own "Irreversible-artifact strictness" clause, a first-publication baseline must be held
strictly to its recorded native ruling; **this scoreboard publishes zero scores** (see below),
so nothing here becomes an irreversible artifact today — but the native/independent reviewer
should confirm this three-state refinement is the intended, ratified design before any future
session's first real score publication treats it as settled.

## Three-state cell definition (as implemented here)

- **`score`** — `kala_field_skill`/`kala_field_gof` carries a published row for this
  (chart, scope): a real `skill_state` (`established`/`not_established`) or `gof_state`
  (`pass`/`fail`), `n_e ≥ 8`.
- **`underpowered(n)`** — the scope has a real N_e prior (the event class exists in
  `brahma_class_priors` with `fact_kind='lifetime_count_per_100y'`) **and** the promise is not
  denied (`bodha_pratijna.status != 'denied'` for at least one row), so `ka_kshetra` builds a
  real field for it — but `n_e < 8` scoreable LEL events exist, reported with the exact `n`.
- **`empty-no-overlap`** — the scope has **no** N_e-class overlap at all: either the class has
  no `brahma_class_priors` row (`kala_field_snapshots.skipped_classes` reason
  `no_class_prior_row`), or the promise itself is `denied` for every row so `ka_kshetra` never
  discovers the class in the first place. Structurally distinct from `underpowered(n)`: no
  amount of waiting for more LEL will ever populate this cell — only an N_e corpus-widening
  decision (a separate, not-yet-commissioned native decision per the ledger's "N_e corpus
  widening (Tranche-2 re-sourcing)" note) or a change in the chart's own promise grade can.

## Live verification, both charts (queried this session, production Postgres)

| Table | 482012f1 | 1c826d5a |
|---|---|---|
| `kala_field_skill` rows | 0 | 0 |
| `kala_field_gof` rows | 0 | 0 |
| `life_events` (LEL) rows | 63 | **0** |
| `kala_field_windows` rows | 0 | 2 |
| `kala_field_snapshots` | `kfs_87484404af9d6fe9dc66a3d78812f8bc` (built 2026-08-06T06:51:43Z, `v0_classical`) | `kfs_b3bcf77a5a4c3ce5296254bac3809451` (built 2026-08-06T05:06:00Z, `v0_classical`) |
| `brahma_class_priors` N_e classes (global, both charts) | childbirth (3.09), marriage (0.984), separation (0.00806), relocation (0.376), foreign_settlement (0.0129), surgery (0.356) — 6 classes, `fact_kind='lifetime_count_per_100y'` | (same table, chart-independent) |

**`kala_field_skill`/`kala_field_gof` are empty for both charts — no skill score or GOF has ever
been published for either canonical chart, at any scope. There is currently no permanent
baseline to protect for any (chart × scope) pair.**

## Scoreboard — 482012f1 (native, Abhisek Mohanty) — DISCLOSED-EMPTY

`kala_field_snapshots kfs_87484404af9d6fe9dc66a3d78812f8bc`: 7 promised (non-denied)
event classes, **all 7 skipped** with `reason='no_class_prior_row'`. Independently confirmed at
the promise layer: `bodha_pratijna` for this chart carries 5 rows per N_e class for all 6
N_e classes (childbirth, foreign_settlement, marriage, relocation, separation, surgery) —
**every single row is `status='denied'`** (30/30). Zero N_e-class overlap, by two independent
measurements (the field-build's own skip log, and the promise layer beneath it).

| scope | cell state | n | evidence |
|---|---|---|---|
| chart-level aggregate | `empty-no-overlap` | — | 0/6 N_e classes have any non-denied `bodha_pratijna` row; `kala_field_windows`=0 rows |
| childbirth | `empty-no-overlap` | — | `bodha_pratijna`: 5/5 rows `denied` |
| marriage | `empty-no-overlap` | — | `bodha_pratijna`: 5/5 rows `denied` |
| separation | `empty-no-overlap` | — | `bodha_pratijna`: 5/5 rows `denied` |
| relocation | `empty-no-overlap` | — | `bodha_pratijna`: 5/5 rows `denied` |
| foreign_settlement | `empty-no-overlap` | — | `bodha_pratijna`: 5/5 rows `denied` |
| surgery | `empty-no-overlap` | — | `bodha_pratijna`: 5/5 rows `denied` |

This chart has 63 real LEL events (`life_events`, verified live) — the emptiness is not a
missing-biography problem, it is a structural N_e-corpus-coverage gap: none of this chart's own
promised event classes (27 total, per `bodha_pratijna`) happen to fall inside the 6 classes the
N_e prior corpus currently covers. Matches the ledger's documented "482012f1's structural
zero-N_e-overlap gap" finding, re-verified live and unchanged since that finding.

## Scoreboard — 1c826d5a (Abhinandan Mohanty) — FIELD-BUILT, ZERO RECORDED OUTCOMES

`kala_field_snapshots kfs_b3bcf77a...`: 13 promised classes, 11 skipped
(`no_class_prior_row`), **2 NOT skipped — marriage and separation** (both have real
`brahma_class_priors` rows and a non-denied `bodha_pratijna` promise: marriage 4 conditional/1
denied, separation 4 conditional/1 denied). Real field data exists: `kala_field_windows`=2,
`kala_field`=20, `kala_field_salience`=2 rows for this chart (verified live). But
`life_events`=**0 rows for this chart_id** — Abhinandan Mohanty has no LEL entries in the
database at all, so there is nothing to score the built field against.

| scope | cell state | n | evidence |
|---|---|---|---|
| chart-level aggregate | `underpowered(n=0)` | 0 | `life_events` chart_id=1c826d5a: 0 rows |
| marriage | `underpowered(n=0)` | 0 | N_e prior exists (0.984/100y), promise non-denied, field built (`kala_field_windows`, `kala_field` rows present); 0 LEL events to score |
| separation | `underpowered(n=0)` | 0 | N_e prior exists (0.00806/100y), promise non-denied, field built; 0 LEL events to score |
| childbirth | `empty-no-overlap` | — | `bodha_pratijna`: 5/5 rows `denied` |
| relocation | `empty-no-overlap` | — | `bodha_pratijna`: 5/5 rows `denied` |
| foreign_settlement | `empty-no-overlap` | — | `bodha_pratijna`: 5/5 rows `denied` |
| surgery | `empty-no-overlap` | — | `bodha_pratijna`: 5/5 rows `denied` |

`asset_throughput` for `mi_bhara` on this chart reads `state='dormant', rows_written=0`
(verified live, last_built_at 2026-08-06T05:15:08Z) — consistent with an honest zero-events
scoring pass, not a crash or a skipped dispatch.

## Baselines per (chart × scope) — status

**None exist yet, for either chart, at any scope.** Per `KALA_W2_FIELD_DESIGN_v1_0.md` §7.3
E7.5, "the first published `SS` per chart becomes the CI baseline" — this scoreboard confirms
that trigger condition has not fired for any (chart × scope) pair. When it does (real LEL
accrues for 1c826d5a, or the N_e corpus widens to cover a class 482012f1 or 1c826d5a actually
has a live promise for), that first published value becomes permanent for that scope per the
existing E7.5 rule, and this scoreboard's `empty-no-overlap`/`underpowered(n=0)` cell is
superseded in place, not silently overwritten.

## What would change a cell's state (disclosed, not speculative)

- `underpowered(n=0)` → `score`: real LEL events accrue for that chart in that class (native
  intake only — LEL entries remain native-only per campaign convention) until `n_e ≥ 8`.
- `empty-no-overlap` → anything else: requires either (a) the N_e prior corpus widening to cover
  a class this chart's `bodha_pratijna` actually promises (the ledger's disclosed, not-yet
  commissioned "N_e corpus-widening (Tranche-2 re-sourcing)" candidate — native decision
  required, same Tier N-i bar as ADJUDICATION-2), or (b) a `bo_pratijna` rebuild changing a
  `denied` verdict to `conditional` for one of the 6 covered classes (chart geometry is fixed,
  so this would only happen from a genuine promise-grading defect fix, not from waiting).
