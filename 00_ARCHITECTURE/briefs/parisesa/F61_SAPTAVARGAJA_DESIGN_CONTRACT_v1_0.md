---
canonical_id: F61_SAPTAVARGAJA_DESIGN_CONTRACT
version: 1.0
status: CURRENT
campaign: PARIŚEṢA-V4
finding: F-61
authored: 2026-08-21
authored_by: PARIŚEṢA-V4 repair lane (GA-2 design authority)
execution_status: CODE REPAIR LANDED — DATA REBUILD NOT EXECUTED
supersedes_assessment: >
  The ledger's prior assessment ("the fix is an aggregate-calculation contract
  that has never been authored — design work requiring independent review")
  is CORRECT that no contract existed, but the design space turned out NOT to
  be open: this project's own L0 canonical reference already states the formula
  verbatim. See §3. No formula was invented by this lane.
---

# F-61 — `saptavargaja_score` was never materialized

## §1 — What this document is

The design record + rebuild specification for F-61. The **code repair is
implemented** (this PR). The **data rebuild is NOT executed** — see §7.

## §2 — The finding, verified live

`chart_facts.graha_saptavargaja_bala_component.<graha>.saptavargaja_score` is
served with `fact_value_num = NULL` and `fact_value_text = NULL` for every
graha, every ayanamsha, every build. Verified live (read-only) against
production for chart `482012f1-710e-4a25-994a-93821f5871aa`: 7 grahas × 15 rows
each, **100% NULL**, each carrying only a JSONB `constituent_fact_ids` array of
**6** `chart_divisionals.id` UUIDs.

A `fact_key` literally named `..._score` carried no score — only a pointer to
raw divisional rows the caller would have to re-derive the score from
themselves. This is the §N.8 Earned-Signal defect in its purest form: asking
"what code path would have to run, and fail, for this signal to correctly read
NULL?" has no answer, because **no code path produced a value at all**. The
aggregate had never been computed anywhere.

## §3 — The formula is NOT ambiguous (the key finding)

The ledger anticipated open design work. There is none. **Three independent
authorities agree**, one of which is this project's own L0 canonical table:

1. **This repo's own L0 authority** — `platform/python-sidecar/brahmagyan/l0_reference.py`,
   `strength_reference` row `saptavargaja_bala`:
   - `formula_text` = **"Sum of dignity points across D1,D2,D3,D7,D9,D12,D30"**
   - `units` = `"virupa"`, `source_citation` = `"BPHS Ch.27"`
   - `classical_interpretation` = "Moolatrikona 45, own 30, great-friend 22.5,
     friend 15, neutral 7.5, enemy 3.75, great-enemy 1.875"
   - and the varga-group table (`l0_reference.py:821`):
     `"saptavarga": {D1, D2, D3, D7, D9, D12, D30}`
2. **PyJHora 4.8.6** (the engine GA6 already delegates its Panchadha Maitri
   ladder to) — `jhora.const.sapthavargaja_factors == [1, 2, 3, 7, 9, 12, 30]`,
   consumed by `strength._sapthavargaja_bala1` whose aggregation is literally
   `svb_sum = list(map(sum, zip(*svb)))` — a plain SUM.
3. **BPHS Ch. 27** (Shadbala Adhyaya), Sthana Bala → Saptavargaja Bala.

The operation is a **plain sum of per-varga virupa scores**. GA6 already emits
exactly those per-varga virupa values (`varga_saptavargaja_bala_component`,
with the correct 45/30/22.5/15/7.5/3.75/1.875 ladder, landed by the M-18 fix).
**The values existed; only the summation was missing.** So F-61 required no
new astrology — it required GA8 to do the arithmetic its own fact_key promised.

## §4 — Second defect found en route: wrong saptavarga membership

`ga_vargas_writer.SAPTAVARGA_SET` read `{1, 2, 3, 9, 12, 30, 60}`. It

- **omitted D7 (Saptamsa)** — a real member, the division the group is named for; and
- **included D60 (Shashtiamsa)** — not a saptavarga member at all; D60 belongs to
  the Shodasavarga/Vimsopaka group (see `VIMSOPAKA_SHODA_WEIGHTS` in the same file).

This is not a judgement call — it contradicts **this project's own L0 reference
table** (§3 item 1), which is a §N.5 violation: an L1 writer restating an L0
authority as its own divergent truth. Fixed to `{1, 2, 3, 7, 9, 12, 30}`.

The contamination is **material, not cosmetic**. Live production values for the
native (lahiri_chitrapaksha), summed with vs. without the spurious D60 row:

| graha | with D60 (as built) | without D60 | delta |
|---|---|---|---|
| SUN | 93.750 | 71.250 | −22.5 |
| MOON | 52.500 | 48.750 | −3.75 |
| MAR | 93.750 | 78.750 | −15.0 |
| MER | 69.375 | 39.375 | −30.0 |
| JUP | 99.375 | 91.875 | −7.5 |
| VEN | 39.375 | 31.875 | −7.5 |
| SAT | 58.125 | 43.125 | −15.0 |

Mercury's score is inflated by **76%** by a varga that classically does not
belong to the group.

## §5 — What was implemented

**GA6** (`ga_writers/ga_vargas_writer.py`): `SAPTAVARGA_SET` corrected to the
classical seven, with the three-authority citation inline.

**GA8** (`ga_writers/ga_structural_writer.py`):
- new `_get_saptavargaja_components()` — reads the per-varga *values* (not just
  row ids, which is all `_get_divisional_constituent_ids` returned) from
  `chart_divisionals`. It **filters on the saptavarga group at read time**, so a
  stale pre-F-61 build's D60 rows can never be summed into a score whose stated
  formula is over D1,D2,D3,D7,D9,D12,D30. The aggregate is therefore
  correct-by-construction *even before the GA6 rebuild lands*.
- the `graha_saptavargaja_bala_component` row now materializes
  `fact_value_num` = the sum, `unit` = `virupa`, and keeps
  `constituent_fact_ids` intact (§N.5 references survive the aggregation).

**Honest coverage** (§N.7 item 6 / §N.8 / §N.6 item 1) — the sum is only as
complete as the GA6 rows behind it, and is never allowed to overclaim:

| GA6 coverage | `fact_value_num` | `fact_value_text` | `coverage_complete` |
|---|---|---|---|
| 7 of 7 | full sum | `complete_7_of_7` | `true` |
| partial | partial sum | `partial_N_of_7` | `false` + `vargas_missing` listed |
| none | **NULL** (not `0.0`) | `unavailable_0_of_7` | `false` |

`0.0` is explicitly refused for the empty case: it would read as a real "no
strength" verdict rather than "not computed". A `NULL`-scored GA6 row is
skipped and reported as missing coverage, never coerced to zero. The
`citation_human` string carries `INCOMPLETE — missing <vargas>` whenever
coverage is partial, so the gap is visible in prose as well as machine-readably.

## §6 — Test evidence

11 new tests in `tests/test_ga8_writer.py::TestF61SaptavargajaScoreMaterialized`,
2 new in `tests/test_ga6_writer.py`. Full GA6+GA8+vocab suites: **296 passed, 0 failed.**

- **Hand-computed golden value**: a fixture placing every rung of the ladder
  exactly once — 45 + 30 + 22.5 + 15 + 7.5 + 3.75 + 1.875 = **125.625 virupa** —
  asserted exactly. This pins both the summation and the ladder.
- **Regression guard**: `test_score_is_no_longer_null_when_ga6_rows_exist`.
- Partial/empty/NULL-row coverage paths, D60 exclusion, `conn=None` safety.
- `test_saptavarga_set_matches_l0_reference_authority` reads the membership
  straight out of `l0_reference.py` and diffs it against GA6 — so this specific
  §N.5 divergence cannot silently return.

**Independent scale corroboration**: PyJHora's own `_sapthavargaja_bala1` run
for this native (1984-02-05 10:43 IST, Bhubaneswar) returns 75.0–165.0 virupa
across the 7 grahas, against a structural max of 45 + 6×30 = 225. Our
aggregation is the same operation over the same ladder and group.

## §7 — DATA REBUILD REQUIRED — NOT EXECUTED BY THIS LANE

This is a **data-materialization** fix, not a serve-time one. Existing rows stay
NULL until the writers re-run. Per CLAUDE.md §N.3, `ga_vargas` and
`ga_structural` are L1 chart-scoped **delete-then-insert** writers: re-running
them DESTROYS and REPLACES existing rows. That is protected-data execution and
belongs to a GA-3 packet under its own scope declaration — not a code-repair
lane. **No production data was written by this lane.**

Rebuild order is **strict** (GA8 reads what GA6 writes):
1. `ga_vargas` (GA6) — regenerates `varga_saptavargaja_bala_component` with D7
   in and D60 out.
2. `ga_structural` (GA8) — aggregates into `saptavargaja_score`.

Running GA8 alone still yields a correct (D60-free) partial score, because of
the read-time group filter in §5 — but it will read `partial_6_of_7` with D7
missing until GA6 has re-run.

**Post-rebuild acceptance:** zero `saptavargaja_score` rows with NULL
`fact_value_num`; every row `unit='virupa'` with `fact_value_num` in
(0, 225]; `vargas_present` contains `D7` and never `D60`.

## §8 — Disclosed residuals (NOT fixed here — GA-2 review items)

**F-61-R1 — coverage caps at 6/7: the D30 chart is never built.** Verified live:
for the native, `chart_divisionals` holds **no `varga_position` rows for D30 at
all** (only 10 `varga_d30_lord_per_amsa` rows). GA6's per-varga loop therefore
`continue`s past D30 for all 12 category builders, so D30 never reaches
`_build_saptavargaja_rows`. This is a **pre-existing, independent GA6 defect**
that predates and outlives F-61 — it is why the constituent array held 6 ids,
not 7, even before the membership bug. Consequence: post-rebuild coverage will
honestly report `partial_6_of_7` with `vargas_missing: ["D30"]` rather than
silently pretending completeness. Fixing D30 generation is out of F-61's scope
and should be raised as its own finding.

**F-61-R2 — tatkalika relationship is recomputed per-varga, diverging from the
cited reference.** GA6's `_build_saptavargaja_rows` calls
`_compute_compound_relation_matrix(varga_positions)` using **each varga's own**
positions. PyJHora's `_sapthavargaja_bala1` — the reference the M-18 fix
docstring cites as its structural model — derives the compound (naisargika +
tatkalika) matrix **once from the rasi chart** and applies that same matrix
across all seven vargas. Classically, temporary friendship is a rasi-chart
relation (houses 2,3,4,10,11,12 from a graha). The current per-varga
recomputation is defensible but **is not what the cited source does**, and it is
why our per-graha totals will not equal PyJHora's even after a full rebuild.
This is a genuine domain decision requiring GA-2/native ruling — deliberately
**not** changed unilaterally by this lane.

**F-61-R3 — L0 vimsopaka saptavarga weights may be permuted.** `l0_reference.py:821`
gives `saptavarga` weights `{D1:5, D2:2, D3:3, D7:2.5, D9:4.5, D12:2, D30:1}`;
PyJHora's `const.sapthavarga_amsa_vimsopaka` gives `{1:5, 2:2, 3:3, 7:1, 9:2.5,
12:4.5, 30:2}`. **Membership is identical** (which is all F-61 relied on), but
the D7/D9/D12/D30 weight *values* appear transposed. These are Vimsopaka
weights, not Saptavargaja Bala inputs, so nothing in F-61 depends on them —
flagged only so the discrepancy is on the record.

---

*F-61 design contract v1.0 — formula resolved from this project's own L0
authority, not invented. Code landed; rebuild pending; three residuals disclosed.*
