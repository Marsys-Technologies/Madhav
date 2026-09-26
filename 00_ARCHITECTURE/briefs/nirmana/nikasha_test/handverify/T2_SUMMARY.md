# T2 summary — per-check false-positive rates, all six layers

Population: hand-verified stratified samples, 60 assets total (L0 8, L1 12, L2 8, L3 11, L4 9, L5 12),
every census verdict cell checked against independent production queries/greps.
Reports: handverify/{L0,L1,L2,L3,L4,L5}_T2.md. L3 census run on the sandbox (R40/R41 make the
production run impossible); count-dependent cells there verified against sandbox contents.

## Verdict-level disagreements per check (census wrong)

| check | L0 | L1 | L2 | L3 | L4 | L5 | total | register row |
|---|---|---|---|---|---|---|---|---|
| Build.completion | 0 | 12 | 8 | 8 | 9 | 4 | **41** | R42 |
| Build.registered | 0 | 0 | 0 | 4 | 1 | 2 | **7** | R43 |
| Build.contract | 0 | 0 | 0 | 4 | 1 | 2 | **7** | R43-derived (N/A cascade) |
| Idem.pattern | 0 | 0 | 1 | 1 | 1 | 2 | **5** | R43-derived / R46 (bo_samvada) |
| all other 14 checks | 0 | 0 | 0 | 0 | 0 | 0 | **0** | — |

Total verdict disagreements: **60**, every one an instance of an already-registered defect
(R42, R43, R46). No new false-positive pattern beyond the registered ones.

## Evidence-inaccuracy (verdict holds, measured string wrong)

| check | instances | register row |
|---|---|---|
| Earn.build_record | L1 7, L3 5, L4 3, L5 several — non-latest asset_throughput row quoted | R44 |
| Cost.baseline | L1 3, L3 5, L5 3 — same non-latest row selection | R44 |
| Build.history | L3 2 — quoted error text is not the latest error | R49 |
| Build.dep_liveness | L2 4, L3 5, L4 1 — "all lit" literally false under stale-only deps; FAIL lists incomplete | R45 |
| Build.exercised | L1 1 — count 108 vs actual 107 (off-by-one in run counting) | new — see below |
| Dens.served | L4 4 — measured module lists wrong (wrong files included) | new — see below |
| L0 | 1 rationale string wrong (bg_text_index Idem.pattern claims delegation; writer does conditional UPDATE) | rolled into R20 fix semantics |

## New rows needed (in addition to R40–R49 already written)

- Build.exercised off-by-one run count (L1 ga_dashas: 108 vs 107).
- Dens.served module-list attribution errors (L4: query_predictive_anchors.ts, index.ts wrongly included).
- Layer-level `registered_ids` counts wrong wherever R43 fires (L4 8 vs 9; L5 12 vs 14) — same root cause as R43, recorded here for the report.

## Reading

Two root causes produce all 60 verdict-level false positives: the completion check's broken
count_sql/build-state logic (R42) and the registration check's literal-grep limitation (R43).
That is the same shape the L0 run found (3 findings behind most rows) — see Phase 6 clustering.
