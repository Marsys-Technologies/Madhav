---
artifact: WL7_FINANCIAL_LEL_GAP
canonical_id: WL7_FINANCIAL_LEL_GAP
version: 1.0
status: CLOSED (T9 LEKHA-PARĪKṢĀ, read-only audit)
created: 2026-07-27
author: Builder T9 "LEKHA-PARĪKṢĀ" (ŚODHANA remediation campaign)
source_documents:
  - 01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md (primary source; version 1.7 per frontmatter changelog)
  - 00_ARCHITECTURE/llm_consumption_audit/LLM_ENDPOINT_CONSUMPTION_REGISTER_v1_0.md §H (WL-7, WL-8)
  - 00_ARCHITECTURE/llm_consumption_audit/ANALYSIS_LLM_ENDPOINT_CONSUMPTION_REGISTER_v1_0.md §3, §5
  - 00_ARCHITECTURE/llm_consumption_audit/briefs/shodhana/SHODHANA_BRIEF_v1_0.md (T9 task spec)
  - live mimamsa_lel_query MCP call against chart_id 482012f1-710e-4a25-994a-93821f5871aa
mandate: READ-ONLY audit. No LEL writes, no data writes, no code changes. Every "missing" claim
  below is cited against the actual LEL file (line-anchored) or the live query response — none
  is asserted from memory or assumption, per the S4-03 near-miss this task exists to prevent.
---

# WL-7 / WL-8 Financial LEL Gap Analysis

## 0 — Verdict up front

The register's WL-7 ("native-supplied dated financial event history (10–15 events) → LEL
enrichment") was written as if the LEL doesn't exist. **It exists.** `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md`
is CURRENT (frontmatter `version: 1.7`, `status: CLOSED`), holds **57 point events** in §3
(`EVT.*`, confirmed by direct count — see §1 below), 8 chronic patterns (§4), 5 period summaries
(§5), and a 16-item gap register (§6) that **already names the exact financial gaps** WL-7 was
about to re-solicit blind. This document replaces the blank-intake framing with a verified
coverage table and a gap list narrowed to what §6 itself flags as open.

**Path/version check (per task step 1):** no rename. `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` is
still the live filename; `CANONICAL_ARTIFACTS_v1_0.md` and `CLAUDE.md`'s cached snapshot both
still point to it as `LEL v1.7 CURRENT`. The "65 events" figure quoted in the register/analysis/
brief is an approximation — the file's own frontmatter says `total_events_logged: 57` point
events (`+ 5 period summaries + 8 chronic patterns` = 70 logged items total across all sections);
my direct count of `EVT.*` block headers in §3 is also 57. Close enough to "~65" that the
register's characterization is fair, but the precise number for anyone building against this
file is **57 point events**, not 65.

**Live-query cross-check (per task step 2):** `mimamsa_lel_query` against
`482012f1-710e-4a25-994a-93821f5871aa` **did not error** in this session (contrary to the
register's MC-002 finding against `bodha_bundle_get`'s LEL sub-tool — a different code path).
It served `total_matching: 63` rows from the `life_events` DB table. The delta (63 vs. 57) is
**not missing financial data** — it is 5–6 correction/amendment rows appended 2026-07-19 by a
concurrent, unrelated workstream (`NATIVE_DATE_TIGHTENING_RESPONSES_v1_0.md`, D-4a Lane A-1,
date-tightening only: stammering onset, a spiritual-dialogue start date, a sleep-disorder onset
day-lock, the Mahadev-adoption date, and the R#3-end date). None of the correction rows are
financial. Every markdown-sourced row the query returned matched the markdown file's content
verbatim (same descriptions, same `source_citation: LIFE_EVENT_LOG_v1_2.md`). **One serving
defect found and worth flagging separately from WL-7/8:** the tool's `query` text parameter and
`offset` parameter appear non-functional in this deployment — three calls with different query
strings and an `offset=50` all returned an identical `result_hash` (`sha256:f91bcc2d…`), i.e. the
same static first page regardless of input. This did not block the audit (the markdown file is
the authoritative source and was read in full) but is noted here as an observed serving gap, not
folded into the WL-7/8 verdict below.

---

## 1 — Coverage table: existing financial/wealth-tagged LEL events

Of the 57 point events in §3, **13 carry direct financial/wealth/business content** (2 formally
`category: finance`; 11 more under `category: career` with business/employment subcategories that
carry hard financial facts — contract wins, launches, closures, employer instability). Every row
below is cited to its exact `EVT.*` ID and file line so the claim is checkable.

| EVT ID | Line | Date | Category / subcategory | Financial content |
|---|---|---|---|---|
| `EVT.2010.XX.XX.01` | 581 | 2010 (year-approx) | finance / `family_windfall` | Father's real-estate sale windfall; family-level, not native's direct income |
| `EVT.2013.05.XX.01` | 824 | 2013-05 | career / `corporate_job_joined` | Joined Mahindra Retail — start of 10-yr Mahindra Group tenure (income event) |
| `EVT.2016.XX.XX.01` | 919 | 2016 | career / `employer_instability` | Mahindra Retail "crashed" (native's word) — employer-side financial distress, job search |
| `EVT.2017.03.XX.01` | 950 | 2017-03 | career / `employer_switch` | Mahindra Retail → Tech Mahindra — internal promotion/platform upgrade |
| `EVT.2021.XX.XX.03` | 1105 | 2021 (year-approx) | career / `business_stalled` | Second sand quarry acquired but non-operational (public-hearing block) ~4–5 yrs — a **capital tied up, non-producing** event |
| `EVT.2023.07.XX.01` | 1288 | 2023-07 | career / `entrepreneurship_founded` | Founded Marsys Group (mining, AI, tech, exports) |
| `EVT.2024.02.16.01` | 1319 | 2024-02-16 | career / `business_milestone_major` | Launched Kotadwara sand-mining operation at Bhanti — first concrete mining-vertical asset |
| `EVT.2025.05.XX.01` | 1350 | 2025-05 | **loss / `financial_deception`** | "One of the big scams... deceived" — major fraud/deception event, magnitude `major`, details not elaborated per native's comfort |
| `EVT.2025.07.XX.01` | 1381 | 2025-07 | **finance / `business_milestone_windfall`** | First major Marsys Technology contract — "the big one," windfall-class revenue |
| `EVT.2026.03.20.01` | 1500 | 2026-03-20 | career / `business_project_closed` | Marsys Technology primary project wrapped "with enormous profits"; revenue stream ran 2023–2026 |
| `EVT.2026.04.08.01` | 1529 | 2026-04-08 | career / `business_milestone_clearance` | Second quarry's public-hearing obstacle cleared after ~4–5 yrs; quarry due operational late Oct 2026 |
| `EVT.2004.XX.XX.02` | 367 | 2004 | education / `opportunity_declined` | CMU exchange declined citing "financial constraints" (secondary financial signal, not primary) |
| `EVT.2007.06.10.01` / `EVT.2008.06.09.01` | 487, 517 | 2007–2008 | career / `first_job_joined`, `first_job_exited` | First salaried income event (Cognizant) and its exit — income-history bookend, not wealth-class |

**Formal `category: finance` tag count: 2 of 57** (`EVT.2010.XX.XX.01`, `EVT.2025.07.XX.01`) —
verified by direct grep of `^  category: finance` in the file (lines 584, 1384; no other matches).
The other 11 rows above are financially load-bearing but tagged `career` or `loss`, which is why
a naive "count the finance category" read would undercount coverage — the register's authoring
session likely made exactly this undercount before its `bodha_bundle_get` LEL sub-tool errored
and it stopped looking altogether.

**Category distribution, full file (verified by grep, `^  category: ` top-level field only,
excluding the schema-template line at line 79):** career 11, education 10, spiritual 8,
relationship 6, health 5, loss 3, family 3, residential+travel 2, psychological 2, other 2,
**finance 2**, creative 2, travel 1. Total 57.

---

## 2 — What the register's WL-7 wishlist actually asked for, mapped to what exists

WL-7 (register §H, line 463–466): *"Native-supplied dated financial event history (10–15 events:
launch, contracts, thresholds crossed, losses, loans, partnerships) → LEL enrichment → mi_*
retrodiction and calibration."*

| Requested class | Status | Evidence |
|---|---|---|
| Business/venture **launch** | **COVERED** | `EVT.2023.07.XX.01` (Marsys Group founded), `EVT.2024.02.16.01` (Kotadwara mine launch) |
| **Contracts** won | **COVERED** | `EVT.2025.07.XX.01` (first major Marsys Technology contract, "windfall-class") |
| **Thresholds crossed** (revenue/profit milestones) | **PARTIALLY COVERED** | `EVT.2026.03.20.01` (project closed "with enormous profits" — a threshold-crossing event in prose, but no numeric figure logged) — see §3 gap below |
| **Losses** | **COVERED** | `EVT.2025.05.XX.01` (financial deception/scam, magnitude `major`) |
| **Loans** | **NOT FOUND** | No `EVT.*` or gap-register item mentions a loan, debt instrument, or credit facility anywhere in the file (verified: no hits for "loan" in a full read of §3–§9) |
| **Partnerships** | **PARTIALLY COVERED** | `EVT.2026.03.20.01` names "Marsys Technology (IT company co-founded with a MasterCard executive)" — a named business partnership exists in the log, but no dedicated partnership-formation `EVT.*` (the partnership is mentioned in passing inside a project-closure event, not logged as its own dated milestone) |
| **Family-level windfall** (not explicitly requested but present) | **COVERED** | `EVT.2010.XX.XX.01` |
| **Employer-side financial instability** (not explicitly requested but present) | **COVERED** | `EVT.2016.XX.XX.01` |

**Net: 5 of 6 requested classes have at least one dated event; only "loans/debt" is genuinely
absent.** This is a dramatically different picture from WL-7's framing of "10-15 events" needed
from scratch — the corpus already covers launch, contracts, losses, and (loosely) partnerships;
what's missing is much narrower than advertised.

---

## 3 — Targeted intake list: genuinely missing classes only

Each item below is verified absent (not assumed) by direct inspection of §3 (all 57 events),
§4 (chronic patterns), §5 (period summaries), and §6 (the file's own gap register). Framed as
specific asks, not a blank form.

1. **Loans / debt instruments.** No `EVT.*` mentions a loan taken, loan repaid, mortgage,
   credit line, or debt default anywhere in the file. Ask: *has the native ever taken a
   business loan, personal loan, or mortgage — and if so, when, for what purpose, and was it
   repaid on schedule or restructured?* This is the one WL-7-requested class with zero existing
   coverage.

2. **Named-figure thresholds on the events that already exist.** `EVT.2026.03.20.01` says the
   Marsys Technology project closed "with enormous profits" and `EVT.2025.07.XX.01` calls the
   first contract "the big one" — both are qualitative. Ask: *what was the approximate revenue
   or profit figure (even a coarse range, e.g. "$50K–100K" or "7-figure INR") for (a) the first
   Marsys Technology contract (Jul 2025) and (b) its closure (Mar 2026)?* This is not a new
   event — it is a numeric enrichment of two events already logged, and it is exactly the kind
   of addition that "converts structural verdicts to calibrated ones" (the register's own phrase
   for WL-7's value).

3. **Partnership formation as its own dated milestone.** The MasterCard-executive co-founder of
   Marsys Technology is named only inside the March 2026 closure event's description (line
   1505). Ask: *when was Marsys Technology itself founded/formed as a partnership (distinct from
   Marsys Group's July 2023 founding), and who are the partner(s)?* — closes
   `GAP.FINANCIAL_LOSSES.01`-adjacent territory and gives `mi_*` retrodiction a partnership-onset
   anchor it currently lacks.

4. **`GAP.FINANCIAL_LOSSES.01` (file's own §6, line 2055–2057, quoted verbatim):** *"Besides the
   May 2025 scam, any other significant financial losses (investments gone wrong, debt
   events)?"* — the file already flags this as unresolved. This item folds in with #1 above
   (loans/debt) and should be asked together.

5. **`GAP.US_JOB_LOSS.01` / `GAP.US_JOB_LOSS_PRECISE.01` (§6, lines 2027–2029, 2071–2073):** the
   exact date of the native's US job loss (before the May 2023 India return) is still not
   captured — flagged twice in the gap register as unresolved. This is career-financial, not
   pure-wealth, but it directly bookends `EVT.2023.05.XX.01` (the pivot event) and is worth
   asking alongside the above since it's the same "precise financial/career transition dating"
   class of gap the file already knows it's missing.

**Explicitly NOT re-asking:** launch dates, contract-win dates, the scam/deception event, the
family windfall, or the employer-crash/switch events — all five are already logged with
native-dictated dates and reflections (§1 table above). Soliciting these again would be the
exact repeat-request mistake this task exists to avoid.

---

## 4 — WL-8 status: margin/retention figures

**WL-8 (register §H, line 467–468):** *"Margin/retention figures (even coarse %) to empirically
test the weak-Venus retention-bottleneck hypothesis against reality."*

**Verdict: genuinely absent, confirmed by two independent checks, not merely undiscovered.**

- Full-text search of `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` for `margin`, `retention`,
  `profit margin`, `% of revenue`, `customer retention` — **zero matches** anywhere in the
  document (schema §1.4, all 57 events, §4 chronic patterns, §5 periods, §6 gap register, §7
  retrodictive summary, §9 PPL subsection).
- Repo-wide search (excluding worktree copies) for schema fields that would carry such a metric
  — `margin_pct`, `retention_rate`, `profit_margin`, `customer_retention` — across all `.ts`,
  `.sql`, `.md`, `.py` files — **zero matches**. There is no table column, no L1 asset, and no
  downstream serving field anywhere in the codebase that carries a margin or retention figure.

WL-8 is not a case of data existing-but-unseen (unlike WL-7). It is a true blank: no field, no
table, no partial coverage. If the native supplies even coarse margin/retention percentages for
the Marsys Technology contract (`EVT.2025.07.XX.01`) or the mining vertical, it would need a
**new** field — there is nothing to enrich, only something to create. That is a genuine "breadth"
gap in the sense WL-8 originally claimed; no re-scoping needed here (unlike WL-7).

---

## 5 — Cross-references to the original register

- **WL-7** — `LLM_ENDPOINT_CONSUMPTION_REGISTER_v1_0.md` line 463–466 (the wishlist item as
  originally stated); re-scoped by `ANALYSIS_LLM_ENDPOINT_CONSUMPTION_REGISTER_v1_0.md` §3 line
  177–184 (*"WL-7 needs a cross-reference before anyone builds it... should be re-scoped to:
  audit which of the 65 events carry financial tags; enrich only the gap"*) and §5 line 236–238
  (*"WL-7 re-scoped per §3 (audit existing 65 LEL events first), then WL-8... highest leverage
  per hour of the native's time"*). This document is that re-scoped audit.
- **WL-8** — register line 467–468; not separately re-scoped in the analysis document (the
  analysis treats WL-7 and WL-8 as a pair at §5 line 236–238). This document confirms WL-8 needs
  no re-scoping — it was accurately described as a blank gap from the start.
- **MC-002** — the `bodha_bundle_get` LEL sub-tool error that caused the original register's
  authoring session to miss the LEL entirely (analysis §3, line 179–180). This task's step-2
  live check used `mimamsa_lel_query` directly rather than the `bodha_bundle_get` bundle path,
  and it did not reproduce that error — consistent with MC-002 being scoped to the bundle
  sub-tool wiring, not the underlying `lel_query` capability itself (T2's parallel track is
  fixing MC-002 proper; this document does not depend on that fix).
- **SHODHANA_BRIEF_v1_0.md** — T9 task spec, `§`"T9 · LEKHA-PARĪKṢĀ" (line 239–246): acceptance
  criteria satisfied — this document exists, every "missing" claim above is cited to a specific
  file line, event ID, grep result, or live-query response, and both WL-7 and WL-8 are
  cross-referenced to their register origins.

---

## 6 — Summary for the native (breadth intake, if desired)

If the native wants to close the two remaining gaps in one pass, the complete, non-redundant ask
is:

1. Any business loan, personal loan, or mortgage — ever — with approximate date(s).
2. Approximate revenue/profit figures (coarse ranges are fine) for the first Marsys Technology
   contract (Jul 2025) and its Mar 2026 closure.
3. When Marsys Technology (the MasterCard-partner venture) was itself formed, distinct from
   Marsys Group's Jul 2023 founding.
4. Exact US job-loss date (pre-May-2023 return) — already flagged twice in the file's own gap
   register, now bundled here.
5. (WL-8, separate class) Any margin or retention percentage the native can estimate for the
   Marsys Technology contract or the mining vertical — coarse is acceptable; none exists today.

That is 4 financial items (not 10-15) plus WL-8's one open metric class — a native-facing ask an
order of magnitude smaller than the register's original framing, because most of what WL-7 asked
for was already sitting in the file.
