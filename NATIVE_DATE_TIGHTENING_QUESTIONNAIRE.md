---
artifact: NATIVE_DATE_TIGHTENING_QUESTIONNAIRE
type: NATIVE-FACING ARTIFACT — for offline completion, not an in-session interview
status: DELIVERED — placed at project root for this one handoff per native's D-3 closeout
  directive, 2026-07-18 (item 4). Logged as a ROOT_FILE_POLICY exception, see
  00_ARCHITECTURE/ROOT_FILE_POLICY.md §6. Canonical copy remains
  00_ARCHITECTURE/llm_consumption_audit/briefs/doctrine_waves/NATIVE_DATE_TIGHTENING_QUESTIONNAIRE.md
  — this root copy is a delivery convenience, not a second source of truth.
firewall: >
  This document contains ONLY Life Event Log ground-truth data (event_id, recorded event_date,
  category/domain, and the description already on file) and blank fields for the native to fill.
  It contains ZERO curve outputs, peak dates, activation scores, threshold values, or any other
  model-derived information. The native pins dates blind — the same discipline the §G gate itself
  runs under. Do not add model output to this document before it is returned; doing so would
  contaminate the tightening process the same way it would contaminate the gate.
depends_on: DR_13_EVENT_SCORING_SEMANTICS_DRAFT.md (the shape/anchor-type vocabulary used below)
authored_by: D-3 conductor session, pre-D-4 wrap-up pass, 2026-07-18
---

# Native Date-Tightening Questionnaire

For each event below: what's currently recorded, and a blank for you to fill with (a) the
tightest anchor-type you can honestly assign — `irreversibility_moment` (a single day the thing
became true/false and stayed that way), `interval_bounds` (a start/end you're confident of, even
approximately), or `milestone_chain` (this is really several separately-dateable events, list
them) — and (b) the actual date(s)/bounds if you have them. Leave blank ("no tighter data
available") wherever true — DR-13(d) scores honestly at whatever resolution the data supports;
there is no penalty for leaving something vague.

## Part 1 — the 16 vagueness-excluded events (currently unscoreable in the primary battery)

| # | event_id | recorded event_date | category/domain | what's recorded | anchor-type + tightened date (native to fill) |
|---|---|---|---|---|---|
| 1 | `64c475da-5248-5332-9127-9331fae79f23` | 1995-07-01 | health / chronic_onset | Severe headaches onset around 1995 (age 11) | ___ |
| 2 | `3e96c6da-3ad6-5329-a40b-0b9240a1cbdb` | 1995-07-01 | psychological / speech_pattern_arc | Stammering onset in childhood (~1995), three-phase arc through 2024 | ___ (note: this is a strong `milestone_chain` candidate — phase 1/2/3 transitions each independently dateable?) |
| 3 | `d5db1b9a-b8c5-5b90-9641-c9ae9b1c2035` | 1998-07-01 | spiritual / transmission | Father's late-night spiritual dialogues, native joined in limited capacity ~1997-2001 | ___ |
| 4 | `39f8395f-dfa6-5deb-9d3d-e4881c905e29` | 2000-06-01 | education / advanced_course_partial | Joined Aptech computer education course post-10th boards (~2000, age 16) | ___ |
| 5 | `123eee97-8885-5d50-b0f1-94281f8f2d49` | 2002-07-01 | psychological / chronic_episode | Vertigo/head reeling peaked during engineering entrance exam prep (~2001-2004) | ___ |
| 6 | `62f0460d-0cf1-5eab-bedc-47ecfcb04657` | 2002-07-01 | spiritual / sadhana_initiation | Father instructed nightly Shani Puja (age ~18-19), Shani Shtotram read ~7-10 years | ___ |
| 7 | `8573c0ca-9fc5-52a0-8309-f1b324a51d4a` | 2007-09-01 | health / chronic_onset | Sleep disorder onset from knee-arthroscopy medical negligence | ___ (see Part 2, item C — this event has a SCORABLE resolution counterpart already on file, `a95552d7`, dated 2025-07-01) |
| 8 | `1dc207bc-a85e-5383-b39d-39be4629a582` | 2009-06-15 | loss / grandparent_passing | Paternal grandfather passed away (June or July 2009) | ___ |
| 9 | `bd7f5711-8668-5315-8e25-94dc94f2a101` | 2010-07-01 | finance / family_windfall | Father received large sum from real estate sale (~2010) — **§G's named windfall anchor event** | ___ (native's own correction already on file, see Part 2 item B — this is being reclassified `interval` under DR-13, not point; if you have ANY bound on the payment-flow period, even approximate month range, it directly sharpens the re-score) |
| 10 | `56a1222d-8c88-5445-b2a2-1fd89d470719` | 2015-07-01 | spiritual / devata_adoption | Gravitating toward Mahadev/Shiva ~2014-2016, deepening over the following decade | ___ |
| 11 | `74e527bb-1b22-51a8-bafb-8d4d7d80ae1d` | 2021-07-01 | career / business_stalled | Second sand quarry acquired, stalled by public hearing requirement ~2021-2022 | ___ (see Part 2 item A — chain with #17 below) |
| 12 | `86cbb042-8c3b-54e0-bf79-8f51b5850c13` | 2022-07-01 | relationship / romantic_concurrent | Affair during CMU Tepper Executive MBA period (2022-2023) | ___ |
| 13 | `021e49f5-9c6a-5e0e-ad6c-84c8ea2ad83f` | 2022-10-15 | relationship / romantic_concurrent_ended | Relationship #3 ended (~Oct 2022, 10-year duration) | ___ (already day-precision — flagged as excluded by the vagueness heuristic possibly in error; confirm if this should actually be scorable as-is) |
| 14 | `63e90113-eb35-5be4-9bce-1da7eda7d82d` | 2024-07-01 | spiritual / practice_intensification | Daily abhisheka, independent yajna, panchang study from ~2024 | ___ |
| 15 | `275b0c18-a159-5560-95f7-2a6cfbec58c4` | 2025-06-15 | spiritual / ritual_infrastructure | Personal yantra mandala established in bedroom | ___ |
| 16 | `732a4119-a333-5ce5-afbf-082453e1f6d5` | 2026-04-08 | career / business_milestone_clearance | Sand quarry public hearing cleared (8 April 2026) | ___ (already day-precision, see Part 2 item A — this is likely the CHAIN's clean anchor date; #11 above is its stalled-start counterpart) |

(The 17th excluded row, the birth event `5d039007-...` 1984-02-05, is excluded as the birth
anchor, not for vagueness — not a tightening candidate, omitted from this table.)

## Part 2 — chain candidates you named directly

**A. Sand-quarry arc (2021 → 2026-04-08)** — rows #11 and #16 above are almost certainly two
milestones of one chain (acquisition/stall → regulatory clearance). Native to confirm: are there
OTHER milestones in between (e.g. a specific filing date, a specific hearing date that failed
before the 2026-04-08 one succeeded) that should be their own chain rows? List any you recall,
even approximately.
___

**B. Windfall payment-flow period (2010)** — row #9 above. Already flagged for `interval`
reclassification under DR-13. If you have ANY bound tighter than "around 2010" (e.g. "the sale
closed in Q2, payments arrived over the following 6 months") — even a rough month range — record
it here.
___

**C. Sleep-disorder onset/resolution** — row #7 (onset, 2007-09, vague) pairs with an ALREADY
SCORABLE resolution event already on file: `a95552d7-0c6c-5188-8ab2-e972a8d13118`, dated
2025-07-01, "chronic sleep disorder (onset 2007, ~18 years) resolved via Lemborexant." Question:
is the ONSET tightenable to a specific week/month around the knee arthroscopy (a medical
procedure likely has a recorded date even if the sleep-disorder consequence's own onset felt
gradual)? If you have the arthroscopy date, that may serve as the `irreversibility_moment` anchor
for the onset milestone.
___

**D. Mahindra career arc** — NOT in the vagueness-excluded list (all rows below are already
day-precision and currently scorable as individual point events), but flagged here because it is
structurally a chain and DR-13(c) asks whether collapsing related milestones was ever done
elsewhere in the corpus. These are already independently recorded — no action needed unless you
believe any of these dates themselves need correction:
- `6f5ee9cb...` 2013-05-15 — joined Mahindra Retail
- `b5ea6a4d...` 2016-07-01 — Mahindra Retail "crashed" (**this row IS in the vagueness-excluded
  set implicitly by its `_07_01` placeholder date — if you have a tighter month/week for when
  this became apparent, record it**): ___
- `e3b2f1d5...` 2017-03-15 — switched to Tech Mahindra
- `928a1f56...` 2019-05-15 — moved to US on deputation
- `b8884cbe...` 2021-07-01 — selected for Tepper Executive MBA (**also a `_07_01` placeholder —
  tighter date?**): ___
- `d506f3e6...` 2023-06-15 — Tepper MBA completed

**E. XIMB MBA chain (2010-12 → 2011-06)** — you named this specifically; it is ALREADY recorded
as 3 separate, already-precise milestone rows, not collapsed:
- `4e96f4b9...` 2011-01-15 — admission secured
- `95138517...` 2011-06-15 — formally enrolled
- `c143ce2a...` 2013-03-15 — graduated
No action needed unless one of these three dates itself needs correction: ___

## Part 3 — anything not on this list

If there is a life event you know is currently recorded with a placeholder/approximate date (the
`_07_01`/`_06_01` mid-year pattern is usually the tell) that ISN'T in Part 1's 16, list it here
with a tighter date if you have one:
___
