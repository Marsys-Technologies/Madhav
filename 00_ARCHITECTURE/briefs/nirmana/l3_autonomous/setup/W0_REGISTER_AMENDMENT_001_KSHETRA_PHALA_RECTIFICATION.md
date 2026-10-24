---
artifact: W0_REGISTER_AMENDMENT_001_KSHETRA_PHALA_RECTIFICATION
version: "1.0"
status: FILED_AWAITING_FOLD_IN
amends: MADHAV_DATA_PLANE_L3_W0_FIELD_CONTRACT_REGISTER_v1_0.md
amendment_class: undeclared_upward_read
asset: ka_kshetra
measured_on: 2026-09-22
measured_against: production (read-only, as amjis_app)
folded_in_by: null
---

# W0 FIELD_CONTRACT_REGISTER — Amendment 001
## `ka_kshetra` has an undeclared upward read of L4 `phala_rectification`

**This file does not edit the W0 register.** The register is another campaign's artifact and is
amended by its owner, not in place by a passing session. This is the amendment filed alongside
it. **Who must fold it in:** the owner of
`00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_W0_FIELD_CONTRACT_REGISTER_v1_0.md` (the W0
inventory campaign), at the next register revision. Until then the register's own census
invariant — "22/22 active identities represented", 699 unique explicit field rows — is
**incomplete by at least this one input edge.**

---

## 1. What is missing

The register carries, for `ka_kshetra`, the fifteen output relations and their field rows. It
does not carry this **input** edge, and carries no row whose producer path is
`services/ka_kshetra/uncertainty.py`.

Verified by grep over the register file, 2026-09-22:

```
grep -n 'phala_rectification' MADHAV_DATA_PLANE_L3_W0_FIELD_CONTRACT_REGISTER_v1_0.md   -> no match (exit 1)
grep -cin 'rectif'            MADHAV_DATA_PLANE_L3_W0_FIELD_CONTRACT_REGISTER_v1_0.md   -> 0
grep -c 'uncertainty'         MADHAV_DATA_PLANE_L3_W0_FIELD_CONTRACT_REGISTER_v1_0.md   -> 1   (the word, in a unit/scale cell; not the module)
grep -c 'stage3_clocks'       MADHAV_DATA_PLANE_L3_W0_FIELD_CONTRACT_REGISTER_v1_0.md   -> 25  (stage3 IS covered — as a producer, never as this consumer)
```

`stage3_clocks.py` appears 25 times as the producer of `kala_field_clocks` /
`kala_field_boundaries` rows. The one thing those rows are *derived from* — an L4 table — appears
nowhere.

## 2. The exact read

**Call site:** `platform/python-sidecar/services/ka_kshetra/stage3_clocks.py:1012`

```python
sigma_t_birth_days, sigma_t_source = U.fetch_sigma_t_days(chart_id, conn)
```

It is the first statement of `compute_boundaries_for_system()` (stage3_clocks.py:998), called
unconditionally — no feature flag, no `try/except`, no `SAVEPOINT`.

**The SQL:** `platform/python-sidecar/services/ka_kshetra/uncertainty.py:185-196`

```python
def fetch_sigma_t_days(chart_id: str, conn: Any) -> tuple[float, str]:
    """DB-facing wrapper: read `phala_rectification` rows for this chart and
    derive sigma_T. See `compute_sigma_t_days` for the aggregation."""
    rows = conn.execute(
        """
        SELECT offset_minutes, lel_fit_score, lagna_stable
        FROM phala_rectification
        WHERE chart_id = %s
        """,
        [chart_id],
    ).fetchall()
```

**Columns consumed:** three, all of `phala_rectification` —

| column | type | how it is consumed |
|---|---|---|
| `offset_minutes` | INTEGER | `offset_minutes / 1440.0` → the candidate's birth-time offset in days; the *value* whose weighted spread becomes sigma_T (`uncertainty.py:181`) |
| `lel_fit_score` | NUMERIC | dual role: the admission filter (`lel_fit_score is not None and lel_fit_score > 0`, :176-178) **and** the weight in the weighted mean/variance (:180,:182-184) |
| `lagna_stable` | BOOLEAN | admission filter only (:177) |

**Aggregation** (`compute_sigma_t_days`, uncertainty.py:149-183): filter to candidates that are
`lagna_stable` with `lel_fit_score > 0`; if fewer than 2 survive, return
`(DEFAULT_SIGMA_T_DAYS, 'default_120s_assumption')` where `DEFAULT_SIGMA_T_DAYS = 120.0/86400.0`
(uncertainty.py:57). Otherwise return the `lel_fit_score`-weighted standard deviation of the
offsets, floored at the default, tagged `'rectification_posterior_weighted_std'`.

## 3. Where the value lands (the receiving output)

`sigma_t_source` and the sigma_T it carries are **persisted**, so this is not an ephemeral
internal:

| receiving relation | receiving fields | write site |
|---|---|---|
| `kala_field_boundaries` | `sigma_t_days`, `sigma_t_source`, `dominant_uncertainty_source`, `interval_lo`, `interval_hi`, `precision_state` | `stage3_clocks.py:1106-1129` (`INSERT … ON CONFLICT … DO UPDATE`) |
| `kala_field_clocks` | via the same stage-3 computation | `stage3_clocks.py:846` |

`interval_lo`/`interval_hi`/`precision_state` are derived from sigma_T through
`U.evaluate_precision_support(t_boundary, sigma_t_days, period_days)` (stage3_clocks.py:1052), so
the L4 read's influence is not confined to the two provenance-looking columns — it reaches the
**interval identity of every dasha boundary the layer publishes.**

## 4. F12 operator role

Per `MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md:39` (F12: "Every important input
declares an operator: `computation`, `applicability`, `counterevidence`, `uncertainty`,
`interpretation`, `exclusion`, `relevance_navigation` or `evaluation`"), this input's operator is

> **`uncertainty`**

unambiguously: its entire product is sigma_T, the birth-time uncertainty that widens or narrows
every boundary interval. It is not `computation` (it does not produce a chart quantity), not
`applicability` (it gates nothing), and not `evaluation` (it scores nothing).

F12's stated proof obligation is "Operator field plus receiving output and test." Of the three,
the register today supplies none for this edge: no operator field, no declared receiving output,
no test. §3 above supplies the receiving output; §7 proposes the test.

## 5. Why it is undeclared

Not a transcription slip — a **scope shape**. The W0 register's own reading rules define a field
row as "one physical persisted column or one typed service-response member," and its census is
built per *asset → output relation/producer partition*. It is an **output** inventory. An input
this asset reads from another layer's table has no cell in that shape, so an upward read is
exactly the class of edge the register is structurally unable to notice. It is missing for the
same reason `bg_transit_moorti`, `bg_synthetic_cohort` and `bg_synthetic_cohort_md` are missing:
they are inputs, not producer partitions.

The difference — and the reason this one gets an amendment rather than a footnote — is that those
three are **downward** reads (L3 reading L0 reference corpora, which §N.5 endorses: reference,
never restate). This one points **upward**, L3 → L4, which the Strategy rules on.

## 6. The ruling that governs it

`MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md` §6.2, closing paragraph:

> "Legacy Gochara cross-checks are validation inputs, not automatically contributors to lambda;
> bind their exact data for acceptance. **Rectification and L5 weight inputs require separately
> admitted, purpose-compatible immutable artifacts. An earlier timestamp does not make an
> event-derived rectification posterior admissible under the event-free prospective contract.**
> No same-run L3→L4/L5→L3 cycle is proposed."

Applied to this edge, three things follow and none is discretionary:

1. **A live table read is not a separately admitted immutable artifact.** `phala_rectification`
   is a mutable per-chart table rewritten delete-then-insert on every `ph_rectification` build
   (`writers/ph_rectification/__init__.py:291,:336`). Reading it at stage-3 time binds L3's
   published boundary intervals to whatever L4 last wrote, with no admission receipt, no pinned
   generation and no content digest.
2. **The posterior is event-derived.** `lel_fit_score` is a fit against the Life Event Log — the
   register of *what actually happened to the native*. Letting it set sigma_T on prospective
   boundary intervals is precisely the flow §6.2 and F15 (event-free generation kept separate
   from protected evaluation) forbid.
3. **Timestamp ordering does not rescue it.** §6.2 names this defence and rejects it by name: an
   `ph_rectification` run that predates the `ka_kshetra` run does not make its output admissible.

`MADHAV_DATA_PLANE_L3_W0_FOUNDATION_SAFETY_v1_0.md` §3 adds the fence from the other side:
"L4/L5 elevation and empirical outcome evaluation remain out of scope" and the L4 references it
discusses are "a preservation fence, not authority to edit L4." Reading L4 live is not editing
L4, but it is equally not the admitted-artifact path §6.2 requires.

## 7. Measured contribution — re-verified, with one correction

A parallel lane reported "185 rows with 0 having `lel_fit_score > 0`, and all 261,998 boundary
rows carrying `default_120s_assumption`." Re-measured independently against production,
read-only as `amjis_app`, 2026-09-22. **The direction is right and the mechanism is confirmed;
two of the three numbers are per-chart figures and are restated here with their scope:**

| claim | as reported | measured | disposition |
|---|---|---|---|
| rows in `phala_rectification` | 185 | **185 per chart**; 370 total across 2 distinct `chart_id`s (185 + 185) | correct **per chart** — 185 is exactly `ph_rectification`'s own documented `37*5 = 185 rows` per chart (`writers/ph_rectification/__init__.py:13`); the table-wide total is 370 |
| rows with `lel_fit_score > 0` | 0 | **0** (of 370; 95 rows have a non-NULL `lel_fit_score`, none of them `> 0`) | **confirmed exactly** |
| boundary rows on `default_120s_assumption` | 261,998 | **261,998** for the canonical chart `482012f1-…`; **511,320** table-wide, of which **511,320 (100%)** carry `default_120s_assumption` and **no row carries any other value** | correct **for the canonical chart**; table-wide the claim is stronger than reported — it is 100%, not merely "all 261,998" |

Queries used (all read-only):

```sql
SELECT count(*) FROM phala_rectification;                                  -- 370
SELECT count(*) FROM phala_rectification WHERE lel_fit_score > 0;          -- 0
SELECT count(*) FROM phala_rectification WHERE lel_fit_score IS NOT NULL;  -- 95
SELECT count(DISTINCT chart_id) FROM phala_rectification;                  -- 2
SELECT chart_id, count(*) FROM phala_rectification GROUP BY 1;             -- 185 each
SELECT coalesce(sigma_t_source,'(null)'), count(*)
  FROM kala_field_boundaries GROUP BY 1;                 -- default_120s_assumption | 511320  (only row)
SELECT chart_id, count(*) FROM kala_field_boundaries GROUP BY 1;
  -- 482012f1-710e-4a25-994a-93821f5871aa | 261998
  -- 1c826d5a-41cb-4450-b4dc-59d440e5f75a | 249322
```

**What this means, stated exactly.** With 0 rows passing `lel_fit_score > 0`, the `usable` list
at `uncertainty.py:176-178` is empty for every chart, `len(usable) < 2` always holds, and
`compute_sigma_t_days` always returns `(DEFAULT_SIGMA_T_DAYS, 'default_120s_assumption')`. The
measured contribution of this upward read to L3's published output is therefore **zero** —
confirmed from both ends: the input can never pass its own filter, and the output shows one
distinct `sigma_t_source` value across all 511,320 rows.

Two things this does **not** mean, which must not be inferred:

* **It is not dead code.** The read still executes on every stage-3 run, still requires the
  privilege, and still hard-fails the build if it is denied (§8). Contributing nothing and doing
  nothing are different.
* **It is not permanently inert.** The moment any `lel_fit_score` becomes positive — one
  `ph_rectification` improvement, one LEL revision — two or more candidates pass the filter and
  `'rectification_posterior_weighted_std'` starts setting sigma_T on published boundary
  intervals, silently, with no admission step and nothing in the register that would have
  predicted it. **The zero contribution is a property of today's data, not of the design.** That
  is the argument for fixing the design now rather than after it starts mattering.

Corroborating independent evidence that the flat score is a known condition, not an artefact of
this measurement: `platform/src/lib/retrieval/registry/layers/L4_phala/__tests__/
non_discriminating_flag.test.ts:4` — "phala_rectification's lel_fit_score is flat 0 across all
185 candidates on the native".

## 8. Current operational state of the edge

`data_plane_builder` has **no SELECT on `phala_rectification`** (measured live 2026-09-22:
`has_table_privilege('data_plane_builder','public.phala_rectification','SELECT')` → `f`). Because
the call at `stage3_clocks.py:1012` is unguarded, `ka_kshetra` cannot complete a stage-3 substep
under the current identity. This matches the independently-filed
`KALA_ENVIRONMENT_READINESS_AUDIT_v1_0.md` §F4 ("CONFIRMED HARD FAIL — mandatory substep, no
try/except") and `LANE_C_HARD_ASSETS.md` F12.

So the edge is simultaneously **build-blocking** and **contributing nothing**. That combination
is what makes the disposition below cheap.

## 9. Recommended disposition

**Do not grant the privilege. Remove the live read.** Three steps, in order:

1. **Hold the grant.** Migration `1073_data_plane_builder_l3_reference_read_grants.sql` grants
   `bg_transit_moorti`, `bg_synthetic_cohort` and `bg_synthetic_cohort_md` and **deliberately
   withholds `phala_rectification`**, citing §6.2 in the migration comment and asserting the hold
   in its verification block (the migration fails if the privilege is present). A grant would
   cement the upward read as the design at the exact moment it is cheapest to remove.

2. **Replace the live read with an admitted immutable artifact — a design change for the Kshetra
   brief, not a privilege change.** The shape §6.2 requires already exists in this layer:
   `kala_field_snapshots` is L3's own publication-identity structure (content hash, corpus pin,
   config pin, substrate build ids). A sigma_T input admitted the same way — pinned generation,
   content digest, explicit purpose code, an admission receipt that predates the run — satisfies
   "separately admitted, purpose-compatible immutable artifact." Until such an artifact exists,
   the correct behaviour at `stage3_clocks.py:1012` is to **take the instrumental default
   directly**, without the DB round-trip: `DEFAULT_SIGMA_T_DAYS` with
   `sigma_t_source='default_120s_assumption'`. That is byte-identical to what all 511,320
   published rows already carry, so the change is provably output-neutral on today's data — and
   it removes both the build blocker and the §6.2 violation in one edit.

3. **Declare the edge, whatever the outcome.** Even resolved, the register should carry it, so
   that the next session reading the register does not conclude — as this one nearly did — that
   `ka_kshetra` has no L4 input. If the admitted-artifact path is built, the register gains an
   input row with operator `uncertainty`, its receiving outputs (§3), and its test (§7 below).

**Explicitly NOT recommended, with reasons:**

* *Grant SELECT and move on.* Cheapest to type, and wrong: it makes an inadmissible flow
  permanent and silent, in exchange for a contribution measured at zero.
* *Wrap the read in `try/except` + `SAVEPOINT`.* This is a real and separate fix for the sibling
  cohort-path defect (`writer.py:1754-1770` catches but has no savepoint, so the aborted
  transaction poisons the next statement). Applied *here* it would convert a §6.2 violation from
  a loud failure into a silent fallback — the worse outcome. Fix the savepoint gap on the cohort
  path; delete the read on this one.
* *Leave it because it contributes nothing.* §7 shows why: the contribution is zero for a
  data-dependent reason that one upstream improvement reverses.

## 10. Proposed falsifying test (to accompany the fold-in)

In the register's own exact-identifier style:

```
FUTURE platform/python-sidecar/tests/l3/test_w0_field_contract_register.py::
       test_ka_kshetra_has_no_live_phala_rectification_read
```

Asserting, source-level and cheap: `'phala_rectification'` does not appear in any module under
`platform/python-sidecar/services/ka_kshetra/`. It fails today (uncertainty.py:191), passes after
disposition step 2, and — unlike a data-level assertion — cannot be satisfied accidentally by the
score staying flat. If the admitted-artifact path of step 2 is built instead, the test inverts to
assert that the sigma_T input carries an admission receipt and a pinned generation, never a bare
table name.

---

**Filed by:** L3 Kāla pre-elevation setup, Phase 1.2b.
**Companion artifacts:** `PHASE1_2_3_GRANTS_AND_TIMEOUT.md` (same directory);
`platform/migrations/1073_data_plane_builder_l3_reference_read_grants.sql` (the hold).
