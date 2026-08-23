---
lane: F-62
stream: S6_ADHARA
stage: S (SPEC) — corrected post-VERIFIER Stage R (REVIEW.md deficiencies 1/2 addressed here; deficiency 3 in the code diff)
author: ADHARA-LEAD (sonnet)
---

# F-62 — SPEC

## 0. Revision note (VERIFIER Stage R, INCOMPLETE-RETURN)

VERIFIER reviewed this SPEC against PR #1296's actual head (`7843cf3df`) and found it
described an earlier state of the branch — written before PAR-R-6/PAR-R-7 forced the real
degree-table extraction, so §5 still said "deliberately not done" about work that was, by
the time of review, already on the PR. This revision brings the doc back in sync with the
code. Full REVIEW.md: `lanes/F-62/REVIEW.md` (VERIFIER's independent re-derivation of
PAR-R-1/2/3/6/7, its own re-run of the exit test on both `origin/main` and the PR head, and
the three named deficiencies this revision + the paired code fix close).

## 1. Root cause

Three dignity-classification call sites (`ga_structural_writer.py`, `ga_vargas_writer.py`,
`bo_pratijna_v4_engine.py`) each carried independent, drifted local dignity logic — one
missing moolatrikona entirely, one over-emitting it with no degree gate — because no shared,
degree-aware classifier existed for them to share. A fourth site
(`brahmagyan/ganita/l1_strength.py:65`) was found during this lane's own build and is
tracked separately (§4).

## 2. Files changed (current PR #1296 head `7843cf3df`, `gh pr view 1296 --json files`)

- `platform/python-sidecar/brahmagyan/l0_dignity_reference.py` (**new**) — the single,
  dependency-free L0 source of the degree table (PAR-R-6 extraction). Stdlib-only
  (`json`, `typing.Any`); no import from `pipeline.orchestrator.*` or any other
  writer-layer module.
- `platform/python-sidecar/brahmagyan/dignity_oracle.py` — shared
  `classify_dignity(graha, sign_name, degree_in_sign)`. `_DATA` is now derived from
  `l0_dignity_reference.DIGNITY_REFERENCE` (a dict comprehension over the shared rows),
  not a hand-maintained copy.
- `platform/python-sidecar/pipeline/orchestrator/writers/bg_dignity_reference.py` —
  now imports `DIGNITY_REFERENCE as _DIGNITY_REFERENCE` from `l0_dignity_reference`
  instead of declaring the 9-graha list + the Rahu/Ketu variant-traditions JSON inline;
  the now-unused `json` import and the module-local `_BPHS_CH3`,
  `_RAHU_VARIANT_TRADITIONS`, `_KETU_VARIANT_TRADITIONS` constants were removed (moved
  into the new module). `@register`, `WriterBase`, `run(ctx)` and every other FROZEN
  contract point are unchanged (VERIFIER independently confirmed this by reading the
  diff — REVIEW.md §"verdict").
- `platform/python-sidecar/ga_writers/ga_structural_writer.py` — wired to the oracle,
  replacing the 4-way inline conditional (closes C1).
- `platform/python-sidecar/ga_writers/ga_vargas_writer.py` — `_compute_dignity` now
  delegates to the oracle with a threaded `degree_in_sign` param at all 3 call sites
  (closes C2); `_build_saptavargaja_rows`'s separate, independently-discovered
  moolatrikona check is also routed through the oracle (§4). The module-level
  `DIGNITY_TABLE` dict itself is kept (now dead code for classification, still read for
  `_build_saptavargaja_rows`' plain own-sign lookup — see the allowlist entry in §5).
- `platform/python-sidecar/pipeline/orchestrator/writers/bo_pratijna_v4_engine.py
  ::dignity_of` — wired to the same oracle (third original consumer).
- `platform/python-sidecar/brahmagyan/__tests__/test_dignity_oracle.py` — 39 tests: the
  6 lane goldens, boundary-exclusive/inclusive pair, unknown-graha, PAR-R-2's
  exact-boundary goldens for every MT-bearing graha (Sun/Mars/Venus/Saturn added this
  pass; Jupiter/Moon/Mercury already present — Moon/Mercury document the "currently
  unreachable" open question, see DIAGNOSIS.md §"HN-2 candidate"), the `is`-identity +
  field-equality guard against `l0_dignity_reference.DIGNITY_REFERENCE`, and a new test
  parsing migration 250's own SQL to cross-check the Python data against the seeded DB
  rows (the Python↔DB-seed seam PAR-R-6 named as the one thing extraction does not
  close on its own).
- `platform/python-sidecar/tests/test_ga6_writer.py` — expectations aligned to the
  5-tier oracle output.
- `platform/scripts/governance/no_local_dignity_table_allowlist.json` — D-01b allowlist
  fix (VERIFIER deficiency 3): the `ga_vargas_writer.py` entry is repinned from an
  exact line number (which this PR's own import line shifted from 134→135, flipping
  D-01b PASS→FAIL for zero new content) to a content `pattern` match on the dict's
  opening entry, immune to future line drift. The now-stale `ga_structural_writer.py`
  entry (that file's dignity chain no longer exists — replaced by the oracle call) is
  removed rather than left pointing at fixed code.

## 3. Exit test

`platform/python-sidecar/brahmagyan/__tests__/test_dignity_oracle.py` — run via
`python3 -m pytest brahmagyan/__tests__/test_dignity_oracle.py -q` from
`platform/python-sidecar/`. **39/39 pass** on PR head `7843cf3df`; import of
`brahmagyan.dignity_oracle` alone (pre-fix, on `origin/main` today) fails collection
with `ModuleNotFoundError` — both directions independently re-run by VERIFIER in Stage R
(REVIEW.md §3), not just carried forward from Stage D/B.

Every MT-bearing graha now has an exact-boundary golden (PAR-R-2's explicit requirement):
Sun, Mars, Venus, Saturn (upper bound → own), Jupiter (upper + lower), Mercury/Moon
(document the currently-unreachable finding rather than asserting a guessed resolution
to an open classical-doctrine question — see DIAGNOSIS.md).

## 4. Sibling sites coverage

All three originally-known consumers (`ga_structural_writer.py`, `ga_vargas_writer.py`
`_compute_dignity`, `bo_pratijna_v4_engine.py`) are wired. CI (`D-01b`) caught a real gap
in this lane's own first-pass census: `ga_vargas_writer.py::_build_saptavargaja_rows` had
a second, independent, non-degree-gated MT check — fixed (commit `933f680a0`), see
DIAGNOSIS.md §4 for detail.

**`brahmagyan/ganita/l1_strength.py:65` (`PLANET_DIGNITY`, Shadbala Sthana Bala) —
correction to the exclusion reason (VERIFIER deficiency 2).** This lane's DIAGNOSIS.md
and an earlier version of this SPEC excluded the site as "out of S6's lease." That is no
longer the real reason: `LEASES.json`'s `S6_ADHARA.owns` array was updated post-Phase-0
to include this exact file ("4th dignity-oracle consumer site found during F-62 build,
kept with the same team already touching the other 3 sites") — the lease question is
resolved, in S6's favor. The site is **still excluded from this PR**, but for the real,
substantive reason DIAGNOSIS.md §4 item 2 already stated: whether BPHS's Sthana Bala
wants a degree-gated moolatrikona distinct from own-sign credit (the same shape as
Shadbala's exaltation-degree treatment) is a genuinely open classical-semantics question
this session did not determine, not a mechanical wiring task like the other three sites
were. Rushing an answer to close the site in this PR would be exactly the "guess at a
mechanism nobody has traced" pattern PAR-R-7/SP-8 warn against elsewhere in this
campaign. **Tracked as an explicit follow-up lane**, not silently dropped now that the
lease question is settled.

## 5. Recurrence guard

Two real detectors (per CLAUDE.md §N.8 — each has a code path that produces red, not
just a currently-passing assertion):

- `test_data_matches_bg_dignity_reference_source_of_truth` — asserts `bg_dignity_
  reference._DIGNITY_REFERENCE is l0_dignity_reference.DIGNITY_REFERENCE` (object
  identity, not just value equality — catches a reintroduced local copy, the exact
  §N.7 item 3 shape) and field-equality between `dignity_oracle._DATA` and the shared
  source.
- `test_l0_dignity_reference_matches_seeded_migration_250` — parses migration 250's own
  SQL `VALUES` block (no live DB in this test environment) and cross-checks it against
  `l0_dignity_reference.DIGNITY_REFERENCE`, field-by-field. This is the real detector
  for the Python↔DB-seed seam PAR-R-6 explicitly named as the one thing extraction does
  not close by itself.

**Extraction status (correcting the prior "deliberately not done" language — VERIFIER
deficiency 1):** the full extraction IS done. `brahmagyan/l0_dignity_reference.py` is
the single Python source; both `bg_dignity_reference.py` and `dignity_oracle.py` import
it. This followed PAR-R-6 (LEDGER_PRATINIDHI.md, `par/pratinidhi-ledger`): extraction
does not touch the FROZEN WriterBase contract (`@register`/`run(ctx)`/`ctx.db_conn`/
`asset_throughput` writes/`ctx.config` — none of the five are read, written, or
reshaped by moving a module-level constant's address), and matches the established
`brahmagyan/l0_*` sibling convention six other L0 writers already follow. PAR-R-7
separately ruled that shipping the earlier equality-guard-only fallback as a substitute
for asking whether extraction was contract-safe was itself a process error (blocked-and-
asking was always available; shipping the lighter fallback was not a form of waiting) —
noted for the record, not re-litigated here; REVIEW.md independently confirmed both
rulings against source.

## 6. Dependencies / rollback

- Depends on nothing else landing first. Rebases cleanly onto `origin/main`.
- PR #1296 entered GitHub's merge queue once with an earlier commit
  (`bc0441280`, pre-extraction) before the extraction was ready; INTEGRATOR dequeued it
  (verified independently via `gh api graphql` before and after) so the real fix
  (`7843cf3df`) could be pushed. No content from the withdrawn state merged.
- D-01b ("No Local Dignity Table", WARN-only, not in the branch ruleset's required-checks
  list) is fixed to PASS by this revision's allowlist change (§2); prior to it, merging
  would have flipped D-01b PASS→FAIL on `main` for zero new content (VERIFIER deficiency
  3, independently confirmed by pulling `main`'s own check-run state).
- Rollback: `git revert` the merge commit; no migration, no schema change, no data
  backfill involved (pure classification-logic change, re-derived at read/build time).
- `l1_strength.py:65` remains open as a tracked follow-up (§4) — not a blocker to this
  PR, not silently dropped.

## 7. Sub-claim coverage table

| Sub-claim | Spec element that closes it |
|---|---|
| C1 — missing MT tier in `ga_structural_writer.py` | §2 `ga_structural_writer.py` wiring |
| C2 — `ga_vargas_writer` MT over-emission, no degree gate | §2 `ga_vargas_writer.py` `_compute_dignity` rewrite + degree threading + `_build_saptavargaja_rows` sibling fix (§4) |
| C3 — no shared oracle | §2 `dignity_oracle.py` + `l0_dignity_reference.py` extraction + 3 consumers wired + §5 recurrence guards |

## 8. Status

PR #1296 head: `7843cf3df` at time of writing, plus this revision's allowlist commit.
`mergeable: MERGEABLE`. **This lane has not merged PR #1296 or pushed to `main`** — that
remains INTEGRATOR's action once CI is green.
