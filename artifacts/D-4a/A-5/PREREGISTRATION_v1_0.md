---
artifact: D4A_A5_DRY_RUN_PREREGISTRATION
version: 1.0
status: PRE-REGISTERED (committed BEFORE any scoring run — DIS.028/DR-15(d) anti-gaming rule)
lane: D-4a Lane A-5 ("Harness dry-run", wave gate lane)
authored_by: Claude Code (Sonnet 5), 2026-07-19
governs: the score tables committed to this same directory AFTER this file, in a LATER commit
---

# D-4a Lane A-5 — Dry-Run Pre-Registration

## §0 — What this commits to, and why it is separate from the results commit

Per DIS.028/DR-15(d): "Pre-registration: thresholds, event sets, and win criteria commit to the
ledger BEFORE any scoring run; post-hoc adjustment is gate-gaming." This file is committed in its
own commit, before the runner script or any score table exists in the repo. Anyone auditing this
lane can diff commit timestamps to confirm the methodology below was fixed before the numbers were
known.

## §1 — CRITICAL FRAMING (repeated here because it belongs in every artifact this lane produces)

**These are DIAGNOSTIC scores only.** This dry-run is explicitly NOT the DR-12 model adjudication
ruling — that determination is reserved for wave D-4b (DIS.025/DR-12: "the data retires the loser",
but that adjudication happens at D-4b, not here). Do not cite the numbers this lane produces as a
model-comparison verdict. A model scoring worse in this run is not "losing" anything; a model
scoring well is not "winning" anything. This run measures; it does not adjudicate.

## §2 — Models in scope (BRIEF_D4A.md §F1 Lane A-5)

Per live inspection of `platform/scripts/audit/t0_retrodiction/lib/a3_scoring_harness/model_interface.ts`
(Lane A-3's harness, used here as a black box, not modified):

1. **`pratyantar_lord`** — the one real, wired model (`pratyantarLordModel`, wraps
   `dasha_lord_confluence_v1` / `buildCurve` from `curve.ts`). SCOREABLE.
2. **`midpoint_triangle`** — `midpointTriangleModel()` throws `NotImplementedModelError`
   unconditionally; no substrate exists anywhere in the codebase. Pre-registered expectation:
   **NOT SCOREABLE**, will be reported as a gap, not fabricated.
3. **`transit_kernel`** — `transitKernelModel()` throws `NotImplementedModelError`
   unconditionally. A repo-wide search (`grep -rl transit_kernel`) confirms no ephemeris/transit
   curve-building implementation exists anywhere outside this stub and the doctrine-register
   commentary about it. Pre-registered expectation: **NOT SCOREABLE**. Note the brief's framing
   ("should be scoreable now that Lane A-0 fixed CR-109/110/111 — the whole point of repaired
   substrate") does not hold: CR-109/110/111 repaired DASHA-PERIOD serving cardinality/spine
   issues, not ephemeris/transit substrate — the two are orthogonal, and no transit-kernel curve
   function exists to consume either substrate. This is pre-registered as an expected gap, not
   discovered post-hoc as an excuse.

Pre-registering an expected failure for (2) and (3) is deliberate: it forecloses any reading of
"the harness just happened not to work for two models" as something decided after seeing scores.

## §3 — Event set (post-A-1 ingestion, full DR-13-shaped LEL corpus)

Source: `life_events` table, `chart_id = '482012f1-710e-4a25-994a-93821f5871aa'` (the canonical
chart; sealed test-split discipline — READ-ONLY access, no writes performed by this lane). Live
count at pre-registration time: **62 rows** (migration 457 shape columns present on every row;
no chain-shaped rows exist in the live corpus — see §3.4).

### §3.1 — Exclusions (fixed here, before scoring)

| # | event_id | reason | rows |
|---|---|---|---|
| 1 | `5d039007-0244-58c6-ad39-152c179c6ac8` | birth anchor (`other/birth`) — A-2 ontology `birth_anchor.epoch_tautology` kill-switch: the chart's own birth is t=0, never scored | 1 |
| 2 | `5278d97c-e769-529a-b0c2-be1e965c2d6b` | explicitly marked in its own description as `[TEST FIXTURE - D-4a Lane A-4 append-hook live demonstration, NOT real native data]` — data-hygiene exclusion, not a real LEL event | 1 |
| 3 | `3e96c6da-3ad6-5329-a40b-0b9240a1cbdb` (original stammering-onset row) | superseded by its `-corr-congenital` correction (append-only discipline: original retained in DB, but not double-counted in scoring) | 1 |
| 4 | `8573c0ca-9fc5-52a0-8309-f1b324a51d4a` (original breathlessness-onset row) | superseded by its `-corr-day-lock` correction | 1 |
| 5 | `56a1222d-8c88-5445-b2a2-1fd89d470719` (original Mahadev-devotion row) | superseded by its `-corr-2021-04` correction | 1 |
| 6 | `021e49f5-9c6a-5e0e-ad6c-84c8ea2ad83f` (original relationship-end row) | superseded by its `-corr-2022-07-14` correction | 1 |
| 7 | `3e96c6da-3ad6-5329-a40b-0b9240a1cbdb-corr-congenital` | A-2 ontology `psychological_arc.congenital_onset` kill-switch — description states the condition is "CONGENITAL (present since birth)... a lifelong, open-ended trait" with no discrete trigger transit; scoring it against a timing model is a category error per the ontology's own worked rationale | 1 |

**7 rows excluded. Scorable corpus = 62 − 7 = 55 events.** (Rows 3–6's correction replacements
ARE in the scorable set — only the pre-correction originals are excluded, to avoid double-counting
the same underlying life event twice.)

### §3.2 — Shape/date-confidence breakdown of the 55 scorable events

| shape | date_confidence | count |
|---|---|---|
| point | exact | 51 |
| point | month_known | 1 (`8573c0ca-...-corr-day-lock`) |
| interval | month_known | 2 (`bd7f5711-...` windfall; `56a1222d-...-corr-2021-04`) |
| interval | year_only | 2 (`64c475da-...` health/chronic_onset; `123eee97-...` psychological/chronic_episode) |
| **chain** | — | **0** |

### §3.3 — DR-13(d) secondary-battery routing

The 2 `year_only` interval events route to the secondary battery only, per DR-13(d) ("never
silently folded into primary"). `MirroredScoringParams.includeSecondaryBattery = true` is set
(§4) so they are exercised and reported, but the harness's own `secondaryBattery` flag on each
`CurveEventScore` keeps them visibly distinct in the output — never counted as if they were
primary-battery hits.

### §3.4 — Chain-shape gap (pre-registered, not discovered post-hoc)

No row in the live corpus carries `shape = 'chain'`. Two rows (`123eee97-...`,
`8573c0ca-...-corr-day-lock`) carry a non-null `chain_parent_event_id`, but their OWN `shape`
column is `interval`/`point` respectively, not `chain` — Lane A-1 tagged the parent linkage without
promoting either row to a genuine `chain`-shaped parent record. **DR-13(c)'s chain-scoring path
(`scoreChain` in `shape_scoring.ts`) is therefore exercised zero times in this run.** This is
reported as a structural gap in the LEL corpus relative to the ontology's `chain` shape class
(§3 of `EVENT_CLASS_ONTOLOGY_v1_0.md` lists several `chain`-shaped classes — `career_change`,
`business_launch`, `education_milestone`, `separation`, `foreign_settlement`), not fabricated by
scoring the two tagged rows as if they were a synthesized chain.

## §4 — Domain / event-class resolution (documented substitute for A-2's not-yet-wired join)

`EVENT_CLASS_ONTOLOGY_v1_0.md §8` states explicitly: `life_events` has no `event_class` column yet
(that is Lane A-1's migration scope, not landed as of this lane's open) — so there is no live join
from an LEL row to one of the ontology's 27 canonical `event_class_id`s. Rather than fabricate a
27-way hand-classification of 55 events (a real risk of silent misclassification B.10 forbids doing
casually), this lane reuses the EXISTING, already-verified-live significator resolution T-0/A-3
already established: `mechanisms.ts`'s `domainForCategory(category)` maps each LEL `category` to one
of 5 domains (`wealth`, `career`, `health`, `marriage`, `general`), and `DOMAIN_LORDS` supplies each
domain's significator weights (sourced from `ganita_dasha_lord_capability_get`, verified live on
482012f1 2026-07-17, per `mechanisms.ts`'s own header). Events sharing a domain are scored against
ONE shared curve for that domain (matching `runMirroredScoringHarness`'s one-`eventClass`-per-call
contract) — this is the same design T-0's Check (c) blind battery already used, extended here to
the full corpus. This substitution is a documented judgment call, not a silent one: **the true A-2
`event_class_id` → LEL-row join is a gap this lane surfaces for D-4b**, not something this lane can
close (that is Lane A-1 territory, and this lane makes zero kernel/weight/threshold/orb/valence
changes).

Domain groupings, fixed before scoring (55 events total):

| domain | LEL categories folded in | event count |
|---|---|---|
| `wealth` | finance, loss | 5 |
| `career` | career | 11 |
| `health` | health, psychological | 6 |
| `marriage` | family, relationship | 9 |
| `general` | creative, education, other, residential+travel, spiritual, travel | 24 |

## §5 — Scoring bounds

`boundsStart = 1984-02-05` (birth). `boundsEnd = 2030-12-31` — chosen (not the full chart-relative
birth→birth+100y horizon A-0 restored for the SERVING substrate) because no LEL event in the
scorable corpus falls after 2026-08-01 (the excluded test fixture) or 2026-04-17 (the latest real
event); 2030-12-31 gives >4 years of margin past the latest real event for curve-shape context
without adding ~50 years of zero-event dasha-period computation that would not change a single
event's score. This is a documented scope choice for THIS scoring exercise, not a statement about
what the serving surface should show a user (A-0's fix stands, unmodified, for that surface).

## §6 — Harness parameters (`MirroredScoringParams`, applied IDENTICALLY to real + every control by
the harness's own structural guarantee — `runMirroredScoringHarness` takes exactly one params
object)

```
percentile: 0.9           # DR-13(a) top-decile, point-check convention (matches T-0 precedent)
shuffleCount: 7            # matches T-0's SHUFFLE_COUNT discipline
includeSecondaryBattery: true   # year_only events exercised, kept visibly distinct (§3.3)
```

## §7 — Primary / secondary metrics (DIS.028/DR-15(b), unchanged from the harness's own contract)

Primary: CRPS / log-score against the model's curve, `skill = 1 − CRPS_model / CRPS_control`,
computed against BOTH the shuffled-birth control (7 shifts, mean) and the antiphase control
(half-span circular shift) — both real, both already implemented in `curve_controls.ts`, neither
touched by this lane. Secondary (legacy): hit-rate ±45d/top-decile (exact), ±75d (month_known),
via `runBlindBattery`.

## §8 — Controls

Both controls are the harness's own, unmodified: shuffled-birth (`shuffledBirthControlCurve`, 7
evenly-spaced shifts) and antiphase (`antiphaseControlCurve`, half-span circular shift, PRIMARY
reading per that module's own header). Control-mirroring is enforced STRUCTURALLY by
`runMirroredScoringHarness` (one `params` object, no code path in this lane's runner constructs two
separately-authored configs) — this lane does not call `runComparativeHarness` at all, so
`assertMirrored`'s refusal path is not separately exercised here (it is A-3's own acceptance proof,
not re-demonstrated by this lane).

## §9 — What counts as "done" for this dry-run (fixed before scoring)

- All 3 models attempted, per §2's pre-registered expectation (1 scoreable, 2 gaps).
- All 5 domain groups scored for `pratyantar_lord` (11 harness runs: 5 domains × [primary+secondary
  in one `HarnessResult` per domain] — one `HarnessResult` per domain, not per model×domain×metric).
- Per-event tables (every `CurveEventScore` + `ProperScoreResult`) committed as JSON under this
  directory, in a commit STRICTLY AFTER this one.
- The DR-12-deferral disclaimer (§1, verbatim) present in the header of every committed results
  file, not only in this pre-registration document.
- No threshold, event-set member, domain grouping, or control construction decided in this file is
  altered after scores are seen. If a genuine defect is found in this methodology AFTER scoring
  begins, it is recorded as a NEW dated addendum below this line, not a silent edit above it.

---
*(no addenda — this file was not edited after the scoring run in §C1 of REPORT below.)*
