# Step 9 evidence — Soak + second chart 1c826d5a (birth from ctx.config['birth_params']

Runbook step 9 (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9). Tranche 2
(requires `PRODUCTION_TRANCHE_2_AUTHORIZED=true`).

**Standing order acknowledged:** both flags were read from
GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md frontmatter before this step started;
no step proceeds past a red gate; a failed gate stops the tranche and
escalates.

- **What:** Soak for chart 1 `482012f1-710e-4a25-994a-93821f5871aa` (flipped
  to '4.0' at 2026-09-28T19:22:58Z per step08 evidence). Second chart
  `1c826d5a` NOT started — it runs after chart 1's soak closes, under the
  step-9 birth-epoch gate.
- **Gate:** integrity green on both charts; no pre-birth window
- **Reversal:** as step 8 (`step08_flip.py --reverse`, pre-authorized under
  Link 3 condition (a) if any abort trigger fires)
- **DSN target:** production `amjis` via own cloud-sql-proxy
  `127.0.0.1:55440` (`madhav-astrology:asia-south1:amjis-postgres`); fresh
  `amjis-pipeline-db-url` credentials from Secret Manager per connection;
  the native's 5433 session never touched.
- **Operator / principal:** l3/gochara-autonomous-wp0-7

## Soak window declaration (Link 3 condition (a))

- **Soak start:** 2026-09-28T19:22:58Z (step-8 flip commit)
- **Minimum soak duration: 24 hours** — the declared window spans at least
  24 h; **declared end not before 2026-09-29T19:22:58Z**
- Evaluations: #1 at soak start (recorded below); midpoint and end to follow.
  Abort triggers (step09_soak_checklist.md lines 13–36) are in force for the
  entire window, not only at evaluations.

## Soak EVALUATION #1 — 2026-09-28T19:25Z — ALL GREEN

1. **Integrity conjuncts (a)–(k)** (`ka_gochara` `integrity_check_sql`,
   post-1150 UTC date-compare text): **t under the session default (UTC) AND
   t under `SET TimeZone='Asia/Kolkata'`**. This is the first production
   evaluation with conjunct (k) engaged (authority now names '4.0': 4,415
   windows + published manifest behind it — passes).
   *Conjunct-(i) vacuity NOTE (per ADK-0024 §4):* conjunct (i) checks
   `active_sentences` elements for a `contact_id` KEY; step06b stores bare
   contact-id strings, so (i) passes VACUOUSLY for '4.0' rows — "integrity
   green" is not earned on sentence-reference integrity by an empty check.
2. **Cockpit vs count_sql:** registry `count_sql` =
   `SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1 AND
   generation='4.0'`; evaluated for this chart = **4,415**, equal to the
   direct relation count. No display/relation drift (cockpit reads count_sql).
3. **Guard-refusal check:** protection triggers present
   (`trg_kgw_generation_guard_row`, `trg_kgw_generation_guard_truncate`);
   `EXPLICIT_CLEAR_OPS['ka_gochara']` = {windows, contacts, coverage} intact;
   no guard-trigger refusals other than the expected protection rejections
   exercised by the step-7 gate-4 scratch rehearsal (which rolled back
   cleanly). 'v1'/'3.0' rows verified untouched: v1 = 38,287 / '3.0' = 1,830
   (unchanged); chart 2 has zero '4.0' windows and authority '3.0'.
4. **Pre-birth detector (#2534 class):** chart birth date 1984-02-05; '4.0'
   windows with `window_start < 1984-02-05` = **0**.
5. **F-02 walkthroughs** (served generation is now '4.0'):
   - *Ordinary quarter 2027-03→05:* **137 rows** (44 day / 49 era / 44
     month), **all 137 with non-empty `active_sentences`** (contacts
     present). Compare pre-flip '3.0': 22 rows, 0 timing windows, no
     contacts (F-01/F-02). PASS.
   - *Marriage touching 2013:* **0 rows** — 2013 is outside the '4.0'
     manifest's disclosed horizon `[2020-01-01, 2030-01-01)`. This is
     absence by design (conjunct (e) enforces the horizon), NOT "episodes
     without contacts" — abort trigger 5 is not met. Marriage-class windows
     inside the horizon: **152 rows, 152 with contacts**. Recorded for the
     native: if 2013 coverage is required, that is a horizon-extension
     decision, not a soak defect.

**Evaluation #1 verdict: GREEN — no abort trigger fired; soak continues.**

<!-- Run outcomes are appended below by the step scripts (--evidence). -->
