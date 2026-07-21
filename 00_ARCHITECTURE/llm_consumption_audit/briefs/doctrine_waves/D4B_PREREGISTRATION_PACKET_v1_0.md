---
artifact: D4B_PREREGISTRATION_PACKET
type: PRE-REGISTRATION PACKET (COMMITTED)
version: 1.2
status: FROZEN — committed to the ledger 2026-07-21 per D-4b Binder review of
  D4B_PREREGISTRATION_PACKET_DRAFT_v1_0.md (0.1-draft). This is the binding specification B-1's
  bakeoff scores against. Per DR-17 §2's harness-refusal guard, the harness itself refuses to run
  if its live tie-band/threshold parameters differ from what is committed here. Any amendment
  after this freeze requires a new version committed BEFORE the next scoring call — never
  a silent edit to this file once B-1 has consumed it.
supersedes: D4B_PREREGISTRATION_PACKET_DRAFT_v1_0.md (0.1-draft, uncommitted) — content carried
  forward where unchanged, corrected where the draft's own figures did not survive fresh
  reconciliation against the live LEL corpus (see §0).
prerequisite_check_superseded_v1_2: this packet's original assumption (B-1 requires a FULLY
  MATERIALIZED ka_gochara_sweep, BRIEF_D4B's original §0) is SUPERSEDED per BRIEF_D4B.md's
  "§0 RECONCILIATION (2026-07-21, native ruling via Cowork)" — B-1 scores via on-demand
  curve(chart, event_class, [t1,t2]) computation over each event's window + grade buffers, not
  full-horizon materialization; forward-span (2026-2055) materialization gates only B-6's serving
  assertions. The Binder re-verifies BRIEF_D4B §0's current text fresh at first scoring call —
  this packet's event coverage below is bounded by the chart's LEL corpus, not by sweep
  completeness, either way.
not_yet_ratified: DR-17's anti-hit double-weight constant (−1.0, §4 below) — RATIFIED VERBATIM,
  NP-D4B-001; the circular-time-shift null proposal — REFUSED for gate-bearing use, admitted only
  as a disclosed non-gate-bearing diagnostic, NP-D4B-002; the §4 tie-band widths (day ±3d / week
  ±7d / month ±45d / year ±180d, corrected in v1.1 from a mis-attribution to DR-17 §2) — ADOPTED
  subject to the mandatory DR-13(d)-width sensitivity recompute, NP-D4B-003. Still genuinely
  PROPOSED/unruled as of v1.2: this packet's own control sample-design parameters (N, seed; §6
  below) and the week point-tolerance (§3). See §9 and `NATIVE_PROXY_LEDGER_D4B.md`.
changelog:
  - "v1.2 (2026-07-21, same session, post-Opus-reverify): fixes the Opus re-verifier's finding that
    v1.1's §4/§9 text described the Native-Proxy ruling on the tie-band widths as still-pending when
    NP-D4B-003 had already issued (ADOPTED, subject to mandatory condition (d) — DR-13(d)-width
    sensitivity recompute). §4 and §9 now state the ruling and its binding conditions; frontmatter
    prerequisite note updated to reflect BRIEF_D4B's §0 event-driven-scoring reconciliation
    (materialization gate superseded for B-1, retained only for B-6 serving); not_yet_ratified list
    updated to show all three NP-D4B rulings' actual dispositions instead of describing them as open."
  - "v1.1 (2026-07-21, same session, post-Opus-verify defect fix): corrects the ONE confirmed
    verifier defect. §4's tie-band table was headed 'Tie-band widths (DR-17 §2)' and committed 'as
    the binding values for B-1' — but DR-17 §2 contains no such numbers; it only defines the
    tie-band AS DR-13(d)'s date_confidence-scaled tolerance (exact ±45d / month ±75d / year-only
    secondary battery), which the day ±3d / month ±45d rows CONTRADICT, and the week ±7d / year
    ±180d rows appear in NO doctrine artifact at all. Fix applied per verifier-required option (b):
    (i) §4's heading and attribution corrected — DR-17 §2 does not specify these widths, it points
    to DR-13(d)'s confidence-scaled tolerance instead; (ii) the four widths (±3d/±7d/±45d/±180d) are
    now explicitly re-cast as NEWLY-PROPOSED operational constants for THIS run, pre-registered by
    this Binder pass, NOT doctrine-derived, pending the Native-Proxy/Adjudicator's ruling on
    adoption; (iii) §4's table added to §9's 'PROPOSED, not ratified' list, alongside the
    week point-tolerance and control sample design already there; (iv) §3's week-tolerance
    justification de-circularized — it previously anchored its own ±7d proposal on §4's tie-band
    value as if that were an independent, sourced figure; both §3's ±7d and §4's tie-band widths
    are now stated as jointly-proposed, mutually-consistent operational constants of EQUAL
    (unratified) standing, neither deriving authority from the other."
---

# D-4b Pre-Registration Packet (v1.0, FROZEN)

## §0 — Event-count reconciliation (live count, this session, superseding all prior figures)

The kickoff brief (BRIEF_D4B.md §1 B-2) says "all 57 LEL events." The 0.1-draft said "58 entries."
A prior ground-truth pass (this project's memory record, 2026-07-21 09:49p) found "56 unique EVT
IDs" by direct grep. **All three numbers are correct simultaneously** once you know what each one
counts — they were never in real conflict, only under-specified. Reconciled live, this session,
against `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` (LEL v1.7, canonical, chart `482012f1-710e-4a25-
994a-93821f5871aa`):

```
grep -cE '^EVT\.[0-9A-Za-z.]+:$' LIFE_EVENT_LOG_v1_2.md            → 58
  minus 1 (line 76: `EVT.YYYY.MM.DD.XX:` — the §1.4 SCHEMA TEMPLATE, not a real event)
grep -cE '^EVT\.[0-9A-Za-z.]+:$' … | excluding the template        → 57
  minus 1 (`EVT.CURRENT.01` — LEL's OWN frontmatter: "EVT.CURRENT.01 not counted as a
  point event"; it is the ongoing marital-separation STATUS marker as of the log's version
  date, not a discrete dated manifestation)
grep -cE '^EVT\.[0-9A-Za-z.]+:$' … | excluding template + CURRENT  → 56
```

- **58** = the 0.1-draft's figure — a raw grep artifact that swept in the schema template. Not a
  real event count; the draft's own authoring process miscounted. **Corrected here.**
- **57** = LEL's own `total_events_logged: 57` (frontmatter: `46 prior + 10 new at M5-A-S1` +
  `EVT.CURRENT.01` counted separately in the total but flagged non-point = 46+10+1 = 57). This is
  what BRIEF_D4B.md §1 B-2 means by "all 57 LEL events" — the full corpus row count, including the
  one status-marker entry.
- **56** = the number that matters for B-1's bakeoff: every EVT.* record that is a genuine dated
  point/interval/chain manifestation, per LEL's own explicit exclusion of `EVT.CURRENT.01`.
  **This is the pre-registered event set for scoring** (§1 below).

**Live count, this session, is 56 scoreable events across 46 main-log entries (Eras 1–8) + 10 M5-A
enrichment-batch entries.** Both sub-totals independently verified by line-offset grep (main log:
lines 146–1529; M5A batch: lines 1592–1854; `EVT.CURRENT.01` at line 1558, excluded).

**One further honest flag, not present in any prior draft:** two of the 56 carry their own scoring
ambiguity that the Binder must resolve, not this packet silently:
- `EVT.1984.02.05.01` (birth) — LEL's own retrodictive note calls this "the source event…
  retrodictive match is tautological." Scoring a model's ability to "predict" the birth event
  against the very chart that birth generates is circular. **This packet does not exclude it from
  the 56 (LEL counts it as a real dated record), but flags it as `scoring_status:
  structural_anchor_not_scored_for_bakeoff` — recommended excluded from B-1's actual λ-scoring
  pass, included here for corpus completeness.**
- `EVT.1995.XX.XX.02` (stammering onset) — native's date-tightening response (item #2) corrects
  this to CONGENITAL ("present SINCE BIRTH, continues till date"), i.e. not independently dateable
  from the birth event itself, and recommends reclassification to §4's chronic-pattern register
  rather than a dated §3 event. **This packet retains it in the 56 for count-fidelity to the live
  corpus, flags it `scoring_status: congenital_onset_not_independently_scoreable`, recommended
  excluded from B-1's λ-scoring pass alongside birth.**

Net: **56 events in the full corpus set (§1); 54 recommended for B-1's actual scoring pass** after
excluding the two structural/congenital entries above. The Binder ratifies or overrides this
recommendation at D-4b open — it is not silently baked into the harness.

## §1 — Full event set (56 events, DR-13 shapes, windows)

Shapes and windows below apply the ratified `DR_13_EVENT_SCORING_SEMANTICS_DRAFT.md` (DIS.026) plus
every native date-tightening correction from `NATIVE_DATE_TIGHTENING_RESPONSES_v1_0.md` (2026-07-19,
partial submission) that the native has confirmed. Corrections still QUARANTINED (native tightening
item #3 only) are marked and NOT applied to the live encoding below, per that document's own
explicit instruction ("do NOT ingest that row until native confirms").

Legend — **shape**: `point` (single date ± tolerance) · `point±bounds` (point with an explicit
best-estimate + native-stated bounds, still scored as point) · `interval` (start–end span, scored
by overlap per DR-13(b)) · `chain` (named independently-dateable milestones, each scored under
point/interval rules per DR-13(c)). **conf**: `exact` (day) / `week` / `month` / `year-approx`.

### Era 1–2: Birth & Adolescence (1984–2000) — 5 events

| EVT ID | Date (tightened) | conf | Category | Shape | Window / tolerance | Notes |
|---|---|---|---|---|---|---|
| EVT.1984.02.05.01 | 1984-02-05 | exact | other/birth | point | ±45d | `structural_anchor_not_scored` — see §0 |
| EVT.1995.XX.XX.01 | onset ~1995; active [~1995→~2010]; subsiding [2010→2021]; resolved ~2021 | year (chain milestones) | health | **chain** | onset year-secondary; active-interval overlap; resolution ~2021 year-secondary | Native tightening #1 (chain/interval hybrid); linked to EVT.2002.XX.XX.01 (peak sub-interval) |
| EVT.1998.02.16.01 | 1998-02-16 | exact | relationship | point | ±45d | R#1 start (→ marriage EVT.2013.12.11.01) |
| EVT.2000.XX.XX.01 | [2000-06→2000-12] | month (interval) | education | **interval** | overlap, ~6mo span | Native tightening #4 |
| EVT.1995.XX.XX.02 | congenital (since birth) | n/a | psychological | interval, open [1984-02-05→present] | not independently scoreable | `congenital_onset_not_independently_scoreable` — see §0; native tightening #2 recommends relocation to §4 |

### Era 3–4: Teens, SRM, First Job (2001–2009) — 13 events

| EVT ID | Date (tightened) | conf | Category | Shape | Window / tolerance | Notes |
|---|---|---|---|---|---|---|
| EVT.2001.03.XX.01 | 2001-03 | month | education | chain milestone 1/2 | ±75d | IIT-prep start; chain w/ EVT.2003.06.XX.01 |
| EVT.2003.06.XX.01 | 2003-06 | month | education | chain milestone 2/2 | ±75d | IIT-prep end |
| EVT.2004.01.XX.01 | 2004-01 | month | relationship | point | ±75d | R#2 start; narrative-only ~3y span, no independently dated end-EVT exists — NOT scored as interval (B.10) |
| EVT.2004.XX.XX.02 | 2004 | year-approx | education | point (chain link 1/3) | secondary battery | CMU declined; deja-vu chain w/ EVT.2021.XX.XX.02, EVT.2023.06.XX.01 |
| EVT.2007.06.XX.01 | 2007-06 | month | health | point (chain anchor) | ±75d | Knee arthroscopy; hard same-day link to sleep-disorder onset (tightening #7) |
| EVT.2007.XX.XX.03 | onset locked to EVT.2007.06.XX.01 (month); resolved EVT.2025.XX.XX.02 | month→year (chain) | health | **chain** | onset ±75d; resolution secondary battery | Native tightening #7: irreversibility_moment = arthroscopy day |
| EVT.2007.06.XX.02 | 2007-06 | month | education | point | ±75d | Engineering completed |
| EVT.2007.06.10.01 | 2007-06-10 | exact | career | point | ±45d | Cognizant joined |
| EVT.2008.06.09.01 | 2008-06-09 | exact | career | point | ±45d | Cognizant exited |
| EVT.2009.06.XX.01 | best_estimate 2009-06-30; bounds [2009-06-15→2009-07-15] | month (point±bounds) | loss | point±bounds | ±75d around best_estimate | Grandfather's passing; native tightening #8 |
| EVT.2002.XX.XX.01 | [~2001/2002→~2004/2005] | year (interval) | psychological | **interval** | overlap | Vertigo peak; native tightening #5, sub-interval of EVT.1995.XX.XX.01 |
| EVT.2002.XX.XX.02 | onset ~2002, open-ended | year (interval, open) | spiritual | **interval** | overlap from onset | Shani Puja initiation; native tightening #6 |
| EVT.1998.XX.XX.02 | 1998 (recorded); correction to 2001 QUARANTINED | year-approx | spiritual | point | secondary battery | Father's spiritual dialogues — tightening item #3 date-correction (1997/1998→2001) NOT applied; mapping ambiguity unresolved per native responses' own instruction. Scored at LEL's recorded 1998 value until Binder lifts the quarantine. |

### Era 5: Peak-Life Period (2010–2013) — 12 events

| EVT ID | Date (tightened) | conf | Category | Shape | Window / tolerance | Notes |
|---|---|---|---|---|---|---|
| EVT.2010.XX.XX.01 | **[2010-07 → 2011-03]** | month (interval) | finance | **interval** — NAMED SPECIMEN | overlap | Windfall; native-tightened per approved reclassification (task directive + tightening #9) |
| EVT.2010.12.XX.01 | 2010-12 | month | travel | point | ±75d | Thailand trip |
| EVT.2011.01.XX.01 | 2011-01 | month | education | chain milestone 1/2 | ±75d | XIMB admission |
| EVT.2011.06.XX.01 | 2011-06 | month | education | chain milestone 2/2 | ±75d | XIMB enrolled |
| EVT.2012.09.XX.01 | 2012-09 | month | creative | point | ±75d | Modeling |
| EVT.2012.XX.XX.02 | 2012 | year-approx | education | point | secondary battery | IRC presidency |
| EVT.2012.10.XX.01 | 2012-10 | month | relationship | point (chain link 1/2) | ±75d | R#3 start; end corrected below |
| EVT.2013.03.XX.01 | 2013-03 | month | education | point | ±75d | MBA graduation |
| EVT.2013.05.XX.01 | 2013-05 | month | career | point | ±75d | Mahindra Retail joined |
| EVT.2013.XX.XX.01 | onset 2013 (year-exact) | year (chain milestone 1/2) | family | **chain** | year secondary; overlap to terminus | Father's illness onset; terminus = EVT.2018.11.28.01 |
| EVT.2013.12.11.01 | 2013-12-11 | exact | family | point — **NAMED SPECIMEN (double-transit)** | ±45d | Marriage; OPEN-RESIDUAL per §8 |
| EVT.1993.XX.XX.01 | 1993 | year-approx | creative | point | secondary battery | Painting awards (M5A) |

### Era 6–7: Corporate Ascendance, Loss, US, Rupture (2016–2022) — 12 events
(4 further spiritual/psychological-arc events chronologically inside this calendar window —
`EVT.1995.XX.XX.02`, `EVT.1998.XX.XX.02`, `EVT.2002.XX.XX.01`, `EVT.2002.XX.XX.02` — are tabulated
once only, in the Era their LEL entry sits under above; not repeated here, to avoid double-counting
the 56-total below.)

| EVT ID | Date (tightened) | conf | Category | Shape | Window / tolerance | Notes |
|---|---|---|---|---|---|---|
| EVT.2016.XX.XX.01 | 2016 | year-exact | career | point | secondary battery | Mahindra Retail crash |
| EVT.2017.03.XX.01 | 2017-03 | month | career | point | ±75d | Switch to Tech Mahindra |
| EVT.2018.11.28.01 | 2018-11-28 | exact | loss | point (chain terminus) | ±45d | Father's passing; terminus of EVT.2013.XX.XX.01 |
| EVT.2019.05.XX.01 | 2019-05 | month | residential+travel | point (chain link 1/2) | ±75d | US move; chain w/ EVT.2023.05.XX.01 |
| EVT.2021.01.XX.01 | 2021-01 | month | health | point | ±75d | Panic/anxiety episode |
| EVT.2021.XX.XX.02 | 2021 | year-approx | career | point (chain link 2/3) | secondary battery | Tepper selection; deja-vu chain |
| EVT.2021.XX.XX.03 | 2021 (tentative) | year-approx | career | point (chain link 1/2) | secondary battery | 2nd quarry stalled; native tightening #11 leaves tentative; terminus EVT.2026.04.08.01 |
| EVT.2022.01.03.01 | 2022-01-03 | exact | family | point | ±45d | Twins born |
| EVT.2022.XX.XX.02 | best_estimate 2022-08-20; bounds [2022-08-15→2022-08-20] | week (point±bounds) | relationship | point±bounds — NAMED SPECIMEN (valence/anti-hit test) | ±7d (proposed week tier, §4) | Tepper-period affair start; native tightening #12 |
| EVT.2022.10.XX.01 | **CORRECTED → 2022-07-14** | day | relationship | point (chain link 2/2) | ±45d | R#3 end; native tightening #13 — supersedes recorded ~2022-10-XX; now precedes affair start (chronology re-ordered per native) |
| EVT.2010.XX.XX.02 | 2010, open-ended | year (interval, open) | spiritual | **interval** | overlap from onset | Ugratara devotion begins (M5A) |
| EVT.2015.XX.XX.01 | **CORRECTED → [2021-04→2021-05]** | month | spiritual | point (bounds) | ±75d | Mahadev/Shiva gravitation; native tightening #10 supersedes recorded ~2015 — MAJOR correction, not a tightening of the same estimate |

### Era 8: India Return, Business, Sand Mines (2023–2026) — 10 events

| EVT ID | Date (tightened) | conf | Category | Shape | Window / tolerance | Notes |
|---|---|---|---|---|---|---|
| EVT.2023.05.XX.01 | 2023-05 | month | residential+travel | point (chain link 2/2) | ±75d | US return; chain w/ EVT.2019.05.XX.01 |
| EVT.2023.06.XX.01 | 2023-06 (TBC) | month | education | point (chain link 3/3) | ±75d | Tepper completed; deja-vu chain terminus |
| EVT.2023.07.XX.01 | 2023-07 | month | career | point | ±75d | Marsys founded |
| EVT.2024.02.16.01 | 2024-02-16 | exact | career | point | ±45d | Kotadwara sand mine launch |
| EVT.2025.05.XX.01 | 2025-05 | month | loss | point | ±75d | Financial deception/scam |
| EVT.2025.07.XX.01 | 2025-07 | month | finance | point (chain link 1/2) | ±75d | First Marsys contract; recorded as point (windfall-CLASS language in description, but no interval bounds native-confirmed — NOT reclassified interval absent explicit tightening) |
| EVT.2026.03.20.01 | 2026-03-20 | exact | career | point (chain link 2/2) | ±45d | Marsys Technology project closed; terminus of EVT.2025.07.XX.01 |
| EVT.2026.04.08.01 | 2026-04-08 | exact | career | point (chain terminus) | ±45d | Quarry hearing cleared; terminus of EVT.2021.XX.XX.03 |
| EVT.2025.XX.XX.02 | 2025 (chain terminus) | year-approx | health | point (chain terminus) | secondary battery | Sleep-disorder resolution; terminus of EVT.2007.XX.XX.03 |
| EVT.2025.XX.XX.01 | 2025 | year-approx | spiritual | point | secondary battery | Shift toward Vishnu/Venkateshwara |

### Remaining 2025–2026 spiritual/psychological events — 6 events

| EVT ID | Date (tightened) | conf | Category | Shape | Window / tolerance | Notes |
|---|---|---|---|---|---|---|
| EVT.2026.01.XX.01 | 2026-01 | month-approx | other | point | ±75d | Psychological focus shift |
| EVT.2024.XX.XX.01 | 2024 | year-approx | spiritual | point | secondary battery | Practice intensification; native tightening item #14 not addressed, stands as recorded |
| EVT.2025.06.XX.01 | milestone 1: undated (earlier); milestone 2: ~2025-06-15 | month (chain, tentative) | spiritual | **chain** | milestone 2: ±75d; milestone 1 not independently scoreable (no date) | Yantra mandala; native tightening #15 |
| EVT.2025.11.XX.01 | 2025-11 | month-approx | spiritual | point | ±75d | Ma Kamlatmika devotion |

**Total rows above = 56** (46 main-log + 10 M5A), matching §0's reconciled live count. `EVT.CURRENT.01`
is intentionally NOT listed — excluded per LEL's own frontmatter (§0).

## §2 — DR-13 shape methodology (ratified, DIS.026 — restated, not amended here)

- **point**: scored HIT if the model's served top-decile window/peak falls within the
  confidence-scaled tolerance of the true date (§3).
- **interval**: scored by OVERLAP — the served top-decile window overlapping the event's
  `[start,end]` span by ANY nonzero duration counts (DR-13(b)/DR-15/DR-17-corrected per D-5's own
  gate_run_2 native disposition — not lag-to-midpoint).
- **chain**: decomposes into named, independently dateable milestones, each scored under point or
  interval rules per its own shape (DR-13(c)). Collapsing a chain to one fuzzy date is a recording
  error, not scored that way here.
- **Control-mirroring (DR-13(e), non-negotiable):** every loosening above applies identically to
  the shuffled-birth control (§6). A criterion loosened for the real chart but not the control is
  gate-gaming by definition and the harness must refuse to run under such an asymmetry.

## §3 — Thresholds

- **Point tolerance** (DR-13(d)): `exact`/day-confidence → ±45 days. `month`-confidence → ±75 days.
  `year-only` → **not scored in the primary battery**; scored in a labeled SECONDARY battery,
  reported separately, never folded into the primary hit-rate.
- **Week-confidence tolerance — GAP, proposed here:** DR-13(d) as ratified defines only
  exact/month/year tiers. Native date-tightening introduced `week`-confidence dates (item #12, the
  Tepper-affair specimen) that DR-13(d) does not cover. **This packet proposes ±7 days** for the
  week tier. **Correction (v1.1):** the prior text justified this figure by "consistency with
  DR-17's own week tie-band width (§4)" — this was circular. §4's tie-band widths are THEMSELVES
  this packet's own proposed operational constants (see §4's v1.1 correction below), not an
  independently-sourced DR-17 value; citing one unratified packet-proposed number to justify
  another manufactures an appearance of derivation neither has. The honest framing: §3's ±7d
  week-tolerance and §4's ±7d week-tie-band are two SEPARATE proposed constants this packet chose
  to keep numerically aligned for internal consistency (so a week-confidence event's matching
  criterion and its tie-band don't silently diverge) — neither derives authority from the other,
  and neither is DR-13-ratified. **PROPOSED, not yet DR-13-ratified — Binder/Adjudicator confirms
  or amends before B-1 consumes it** (same disposition as the DR-17 anti-hit constant and §4's
  tie-band widths, §9).
- **Interval-shape scoring**: OVERLAP assertion (§2), evaluated under DR-17's graded scale (§4),
  never a binary hit/miss.
- **Win criterion (DR-15(b), CRPS primary):** `skill = 1 − CRPS_model / CRPS_control` > 0 AND
  statistically distinguishable from 0 (not merely numerically positive), against the model's own
  coverage-matched shuffled-birth control (§6). Hit-rate (±45d top-decile, D-3 continuity) retained
  as legacy secondary, reported alongside CRPS, never substituted for it.

## §4 — DR-17 grading scale + tie-bands

Grading scale (`DR_17_18_MANIFESTATION_CENSUS_DOCTRINE_v1_0.md` §1, restated verbatim):

| Grade | Weight |
|---|---|
| `peak` | 1.0 |
| `sub_peak` | 0.75 |
| `elevated` | 0.5 |
| `neutral` | 0.0 |
| `contra` | −0.5 |

**Tie-band widths — CORRECTED ATTRIBUTION (v1.1): these are this packet's OWN newly-proposed
operational constants for THIS run, NOT a DR-17 §2 figure.** The prior (v1.0) heading read
"Tie-band widths (DR-17 §2)" and committed the table "as the binding values for B-1" — that
attribution was wrong and has been corrected. DR-17 §2 defines the tie-band mechanism only as "the
model's OWN pre-registered date-uncertainty band... (DR-13's date_confidence-scaled tolerance:
exact ±45d / month ±75d / year-only secondary battery)" — DR-17 §2 names no day/week/month/year
day-count table at all, and where it does point to a source (DR-13(d)), that source's actual
values (exact ±45d / month ±75d) CONTRADICT the ±3d / ±45d figures below. The week ±7d and year
±180d rows appear in no doctrine artifact whatsoever — they were authored fresh for this packet.

Fixed at pre-registration, harness-refusal-guarded against post-hoc widening — **pre-registered
HERE, this packet, as THIS RUN's operational constants, explicitly NOT doctrine-derived from DR-17
§2. Native-Proxy ruling NP-D4B-003 (`NATIVE_PROXY_LEDGER_D4B.md`) has ADOPTED this table under the
v1.1 corrected attribution, subject to binding condition (d): a MANDATORY deterministic sensitivity
recompute of every contender's grading under the DR-13(d) substitute widths (exact ±45d / month
±75d), with per-contender disagreement counts, both weighted totals, `tie_band_sensitive: true`
flagging, and any gate/ordering flip named as its own B-6 finding (asymmetric — may only make a
result look worse, never rescue a failure). See §9 for the full binding-conditions summary.**

| date_confidence tier | tie-band width (PROPOSED, this packet, pending ratification) |
|---|---|
| day (exact) | ±3 days |
| week | ±7 days |
| month | ±45 days |
| year | ±180 days |

These are the model's OWN declared `date_confidence` tier widths, never computed post-hoc from a
scoring run's own results (DR-17 §2's harness-refusal guard applies to the MECHANISM — freezing
whatever width is committed before the first scoring call — independent of whether the specific
widths above are doctrine-ratified or, as here, newly pre-registered by this packet). Note these
are a DIFFERENT mechanism from §3's point-tolerance (matching criterion for a hit) — the tie-band
governs when TWO candidate served peaks are treated as equivalent-rank rather than separately
graded and summed. Note also these widths do NOT reconcile with DR-13(d)'s actual ratified
point-tolerance figures (exact ±45d / month ±75d) — that is a deliberate choice, not an oversight:
DR-13(d) tolerances answer "does a served point count as a hit against the true date," while this
table answers a different question ("when are two served peaks the same signal, not two"), and
this packet elects to pre-register the latter as its own constants for the Binder's ratification
rather than force a false equivalence with DR-13(d)'s numbers, which were never intended to answer
this question.

**Anti-hit constant — NOT RATIFIED, flagged pending, per task instruction:** DR-17 §1's ordinary
`contra` grade is −0.5. DR-17 §1's ANTI-HIT double-weight — a confidently-wrong VALENCE call on an
adverse-class specimen (model calls `contra` in a way that crosses gain/loss sign) — is proposed at
**−1.0**. Per `DR_17_18_MANIFESTATION_CENSUS_DOCTRINE_v1_0.md` §4 itself: **"this is a PROPOSAL for
the D-4b Binder to ratify verbatim or amend before B-1 consumes it… DR is proposed, not
self-ratifying."** This packet does NOT silently ratify it. It remains `pending_adjudication` —
Fable/Adjudicator per CONDUCTOR_PROTOCOL §4.1 — until an explicit ratification record exists. B-1
must not treat −1.0 as binding without that record.

## §5 — Top-K local-maxima definition

Per the D-5 gate_run_2 finding-2 fix (`shape_output._local_maxima`), K is **not specimen-tuned and
not a fixed numeric cap**. K = every genuine local maximum above the event_class's own
structural-prior baseline threshold. Response-row-count limiting (§N.6 serving-density discipline)
is a strictly later, separate concern from how many peaks the model is permitted to find — never
conflated with the scoring definition of K itself.

## §6 — Control construction (DR-15(c))

**Mechanism (ratified, unchanged):** coverage-matched shuffled-birth control per model — the SAME
model, SAME harness, run against N synthetic birth dates drawn to match this chart's real coverage
span, not a single alternate date (D-3's own finding that a single-shuffle control understates
variance). Antiphase control (C-4, BRIEF_D4 v2.0) retained as a secondary robustness check, not the
primary comparator.

**Sample design — PROPOSED here, not previously specified anywhere in ratified doctrine (no N or
seed methodology exists in any DR/BRIEF/ADDENDUM read for this packet). Binder/Adjudicator ratifies
or amends before B-1's first scoring call, same disposition as §3's week-tier tolerance and §4's
anti-hit constant:**

- **N = 1000 synthetic birth dates** per model under test. Rationale: stable empirical
  percentile-of-manifestation and CRPS-control distributions at DR-17's graded (non-binary) scale
  need enough draws that the 54–56-event scoring set (§0) isn't dominated by control sampling
  noise; `curve(chart, event_class, [t1,t2])` is deterministic and cheap per the DR-15(c) contract,
  so N=1000 is computationally inexpensive. This is a proposed default, not derived from a power
  calculation — flagged as such.
- **Coverage-matching constraint:** a synthetic birth date `b_synth` is valid only if
  `[b_synth, b_synth + 100y]` (the chart-relative sweep horizon, TEMPORAL_ENGINE_ARC_PLAN §10 Q3)
  fully contains the real event corpus's calendar span. Using this packet's own §1 event set:
  earliest non-structural-anchor event ≈ 1993-XX-XX (painting awards, M5A); latest ≈ 2026-04-08
  (quarry hearing). That constrains `b_synth ∈ [1926-04-08, 1993-XX-XX]` approximately (a ~67-year
  valid window), EXCLUDING the true birth date 1984-02-05 itself. Time-of-day and birthplace
  (10:43 IST, Bhubaneswar) held fixed — DR-15(c) names this a "shuffled-BIRTH" control, i.e. date
  only; shuffling time/place is a different, unspecified perturbation this packet does not
  introduce.
- **Seed — PROPOSED:** a fixed, reproducible seed derived deterministically from
  `sha256(chart_id + "|" + this packet's artifact_id + "|" + version)` truncated to a 64-bit
  integer, logged verbatim in the harness's own run manifest at first execution. This packet does
  not compute that hash value here (no run has occurred yet — computing it now would be inventing
  a number ahead of the actual harness invocation, which B.10 forbids); the harness computes and
  logs it as part of §D's pre-registration commit at first call, and every subsequent re-run of the
  SAME model against the SAME packet version reuses the SAME logged seed (reproducibility), never a
  fresh random seed per run.
- **Every scoring loosening in §2/§3/§4 mirrors identically onto the shuffled-birth control's own
  56-event (or 54, per §0's recommended scoring subset) synthetic scoring pass** — DR-13(e),
  non-negotiable.

## §7 — Named specimens (carried, task-directed)

- `EVT.2010.XX.XX.01` — major_gain windfall, interval **[2010-07 → 2011-03]**, month-confidence
  bounds (native-tightened, item #9). See §1 Era 5.
- `EVT.2013.12.11.01` — marriage, double-transit specimen, day-confidence, exact 2013-12-11.
  **OPEN-RESIDUAL, IMPROVED NOT YET CERTIFIED** (§8) — `chara_karaka` vs
  `guru_shani_double_transit` residual pair, per `ADDENDUM_D-5_PRE_D4B_READINESS_v1_0.md`.
- `EVT.2022.XX.XX.02` — Tepper-period affair, week-confidence point±bounds
  [2022-08-15→2022-08-20], best_estimate 2022-08-20. Flagged here as the natural anti-hit/valence
  specimen candidate given DR-17's own anti-hit framing (adverse-class valence-crossing) — NOT
  independently confirmed as such by any doctrine artifact; this packet observes the fit, does not
  assert it.
- Sarvatobhadra (~2025-05) — **no scoreable LEL anchor exists**, per LEL's own honest gap and
  DR-18's own census finding (classical vedha-pair grid TESTED-NO-SIGNAL, migrations 140/144 zero
  rows). Carried as a structural/primitive-level demonstration only, NOT part of the scored event
  set for B-1.

## §8 — Dependencies not yet satisfied (carried forward, not resolved by this packet)

1. **§0 materialization-completeness gate (BRIEF_D4B §0):** `ka_gochara_sweep` for chart
   `482012f1` must show 100% of its planned substeps committed BEFORE B-1's first scoring call.
   This packet's event set and thresholds are independent of that gate's state, but B-1 itself
   cannot run until it is green — verified fresh at D-4b open, not assumed from this packet.
2. **Marriage-specimen residual (`EVT.2013.12.11.01`):** OPEN-RESIDUAL, IMPROVED NOT YET CERTIFIED
   per `ADDENDUM_D-5_PRE_D4B_READINESS_v1_0.md` §4 — 52 candidate peaks found, `guru_shani_
   double_transit` active at 2013-12-07/15 bracketing the true date, but this was assessed against
   a still-partially-materialized sweep. Must be re-derived fresh against the FULLY materialized
   sweep before B-3's residual-pair mining treats it as resolved either way.
3. **Native date-tightening submission is PARTIAL** (16 of a larger questionnaire, 2026-07-19).
   Item #3 (father's spiritual dialogues) is explicitly QUARANTINED by the native's own response
   document pending confirmation — NOT applied in §1. Items #14 (practice intensification tighter
   date) and several Part 2/3 items were never addressed and stand as originally recorded.

## §9 — What remains PROPOSED, not ratified, in this packet (explicit, per task instruction)

- **DR-17's anti-hit double-weight constant (−1.0)** — §4. Proposed by
  `DR_17_18_MANIFESTATION_CENSUS_DOCTRINE_v1_0.md` itself, explicitly flagged there as
  Binder/Adjudicator territory, NOT silently ratified by this packet's commit.
- **The week-confidence point-tolerance tier (±7 days)** — §3. No ratified DR-13 figure exists for
  this tier; this packet proposes a value, deliberately kept numerically aligned with §4's own
  proposed week tie-band width for internal consistency (see §3's v1.1 correction — neither figure
  derives authority from the other), flagged pending.
- **The §4 tie-band widths (day ±3d / week ±7d / month ±45d / year ±180d) — added to this list in
  v1.1.** Corrected in v1.1: these are NOT a DR-17 §2 figure (DR-17 §2 only points to DR-13(d)'s
  exact ±45d / month ±75d / year-only-secondary-battery tolerance, which these widths contradict
  for the day and month tiers, and which contains no week or year day-count at all). This packet
  pre-registers ±3d/±7d/±45d/±180d as its OWN newly-proposed operational constants for THIS run's
  tie-band mechanism — explicitly NOT doctrine-derived. **RULED (NP-D4B-003, `NATIVE_PROXY_LEDGER_D4B.md`):
  ADOPTED**, not rejected, not still-pending — subject to mandatory binding condition (d), the
  DR-13(d) substitute-width sensitivity recompute described in §4 above, plus conditions (a)-(c)/(e)-(f)
  (this-run scope only; doctrine promotion is native-only at B-6; full-vector harness-refusal-guard
  frozen at first scoring call; symmetric control widths; no tie-band/hit-tolerance code-path leakage).
  B-1 may treat this table as binding FOR THIS RUN under those conditions — same disposition class as
  the anti-hit constant above (NP-D4B-001, ratified verbatim).
- **The control sample design (N=1000, coverage-matching window, seed derivation scheme)** — §6.
  No prior doctrine artifact specifies N or a seed methodology; this packet proposes concrete,
  reproducible values so B-1 has something committed to score against, flagged pending.
- **§0's own scoring-subset recommendation (54 vs 56 events)** — birth and the congenital-onset
  stammering entry are recommended excluded from B-1's actual λ-scoring pass; this is a
  recommendation in this packet, not an instruction the harness enforces automatically.

None of the above self-ratifies by virtue of appearing in this FROZEN packet. Per DR-17 §4's own
language, adopted here for all five items: proposed, not self-ratifying — the Binder/Adjudicator
ratifies or amends before B-1's first scoring call consumes any of them as binding.

## §10 — What this packet does

- Commits the full 56-event scoreable set, DR-13 shapes, and windows (§1) — reconciled live against
  the canonical LEL this session, not carried from any prior draft's count.
- Commits point/interval/chain tolerance thresholds (§3) and DR-17 grading + tie-bands (§4).
- Commits a concrete control sample design (§6), where none existed in ratified doctrine before.
- Flags, rather than resolves, every item still requiring Binder/Adjudicator sign-off (§9).
- Does NOT verify BRIEF_D4B §0's materialization gate — that is the Binder's own first action at
  D-4b open, independent of this packet's commit.
- Does NOT dispatch any scoring run. Committing this packet is a ledger action; B-1's first scoring
  call is a separate, later action gated on §8 item 1.

---

*D4B_PREREGISTRATION_PACKET v1.1 FROZEN 2026-07-21 (status unchanged: FROZEN pending the Binder's
final commit). Supersedes v1.0 and the 0.1-draft. Event count reconciled live (§0): 56 scoreable
events (58 raw grep artifact and 57 LEL-total both explained, not contradicted). v1.1 corrects the
one confirmed Opus-verifier defect: §4's tie-band table (day ±3d / week ±7d / month ±45d /
year ±180d) was mis-headed "DR-17 §2" and committed as binding — DR-17 §2 in fact only points to
DR-13(d)'s date_confidence-scaled tolerance (exact ±45d / month ±75d / year-only secondary
battery), which the day/month rows contradict and which has no source for the week/year rows at
all. Fixed by re-casting the table as this packet's own newly-proposed operational constants for
this run (§4), adding it to §9's PROPOSED-not-ratified list, and de-circularizing §3's week-tier
justification, which had cited §4 as if it were an independent source. Five items now remain
explicitly PROPOSED pending Binder/Adjudicator (Native-Proxy) ratification (§9) — this freeze locks
the SPECIFICATION for review, it does not pre-empt that review or the pending ruling.*
