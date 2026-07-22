---
artifact: VERIFY_RC-04.md
canonical_id: RETRIEVAL_VERIFY_RC04
version: 1.0
status: VERDICT — REJECT (closable; genuine work, DONE bar not fully met)
governed_by: 00_ARCHITECTURE/briefs/RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md §E RC-04, §D.4
verifier: Independent VERIFIER agent (opus, high effort) — NOT the RC-04 implementer
verified_against: res/rc04-census-probe-rerun @ 237f3a45 (base main@651c64789bbc)
date: 2026-07-23
---

# VERIFY RC-04 — Independent Verification Verdict

## VERDICT: REJECT

Not because the work is fabricated — it is not; every live trace and census number I
independently re-ran reproduced exactly. **REJECT because the residual's verbatim DONE
bar is unmet on 3 of its 4 clauses, and the implementer's hand-off summary ("RC-04 is
complete") overclaims relative to the residual's own honest artifacts** (which themselves
concede "This document does not claim RC-04 is fully ACCEPTED"). The gap is closable with
bounded follow-up; this is a REJECT-with-credit, not a fabrication finding.

## What the DONE bar says (verbatim, §E RC-04)

> **DONE:** 100% concepts at a terminal healthy state (or each exception dispositioned
> via the five-state taxonomy), drill-crawl zero dead ends, probe-suite diff shows only
> intended changes; `CENSUS_v2_0.md` + `PROBE_DIFF_v2_0.md` saved.

## Clause-by-clause verdict

| # | DONE-bar clause | Verdict | Evidence |
|---|---|---|---|
| 1 | 100% concepts terminal-healthy, OR each exception dispositioned via five-state taxonomy | **UNMET** | fact_category (218/218) and signal_class (19/19) ARE 100% terminal. But CENSUS_v2_0.md §2 explicitly names **5 genuinely-open dark tables** (`chart_facts_history`, `chart_facts_supersedence`, `mimamsa_export_log`, `mimamsa_pool_contributions`, + `kala_convergence_staging` out-of-scope) that it deliberately did NOT disposition ("that is RC-09's Resolver authority, not RC-04's"). The DONE-bar parenthetical requires each exception to BE dispositioned; they are surfaced, not dispositioned. |
| 2 | drill-crawl zero dead ends | **UNMET (not demonstrated)** | No drill-crawl harness was run. CENSUS §2/§4 concede "This session did not build a new drill-crawl harness" and offer only a ~10-response `drill_pointers` spot-check as a "partial substitute … not a full crawl and does not claim to be one." The rigorous clause is undischarged. |
| 3 | probe-suite diff shows only intended changes | **UNMET** | PROBE_DIFF §3.1 + §7 find `phala_anchors_get` now 422s where it succeeded at W0 — an **unintended, undocumented** behavior change. I independently reproduced it (below). §4 adds a second unintended change (`ref_yogas_get`/`ref_doshas_get` uncapped size blowup). Neither was recorded in `MARSYS_DEFECT_GAP_REGISTER` nor opened as a new RC-row, which §G requires for any defect discovered outside the residual set. |
| 4 | CENSUS_v2_0.md + PROBE_DIFF_v2_0.md saved | **MET** | Both present on branch, frontmatter-bearing, substantive. |

## Independent re-verification I performed (not trusting transcripts)

1. **DB counts — CONFIRMED.** `mcp__postgres__query`:
   `count(DISTINCT fact_category) FROM chart_facts = 218`;
   `count(DISTINCT signal_type_class) FROM bodha_msr_signals = 19`. Matches the census
   headline exactly (two independent credential paths agree).
2. **Regenerated JSON is a genuine fresh run — CONFIRMED.** Timestamps are sequential and
   fresh (E1 19:38:24Z → E2 19:40:26Z → E3 19:40:31Z → E4 19:40:53Z → census 19:41:15Z,
   all 2026-07-22). Headline numbers in the committed JSON match CENSUS_v2_0.md verbatim:
   E1 `total_declared_capabilities: 165`, E3 `218`, E4 `signal_type_class distinct 19`,
   census `dark_table_rows: 42`. This is a real cumulative re-run, refuting FINAL_REPORT
   §H.2's "requires Next.js server runtime" blocker framing — that leg is legitimately
   **no longer BLOCKED**, exactly as claimed.
3. **`phala_anchors_get` regression — CONFIRMED (live).** My own call
   `phala_anchors_get(chart_id=482012f1)` returned
   `sidecar /api/compute/phala/event_anchors failed (422): date_range Field required`.
   The loaded MCP tool schema lists only `chart_id` in `required` (`date_range` optional),
   so the tool contract and the live sidecar have genuinely drifted. The finding is real
   and precisely characterized.
4. **`envelope_version: "v3"` fix — CONFIRMED (live).** My own
   `get_chart_orientation(482012f1, envelope_format=v3)` returned
   `"envelope_version":"v3"` with `chart_header` populated (`"name":"Abhisek Mohanty"`,
   Aries lagna). The W0 defect (v1 label on v3-shaped response) is fixed, as claimed.

## Blocker check (§D.4c)

The implementer claimed NOTHING was blocked and actively refuted the prior session's
blocker. I concur: the census leg's "requires Next.js server runtime" was a shortcut
around doable work (missing `node_modules` + the documented `cloud-sql-proxy` credential
path), and the implementer surmounted both legitimately. **BLOCKED-CONFIRMED does not
apply.** No leg is genuinely blocked; the REJECT is about DONE-bar completeness, not a
real external wall.

## must_not_touch check (§E task e) — CLEAN

Full diff vs main touches only: the two required deliverables, five regenerated
`retrieval_impl/*.md` generator outputs (overwritten in place by design), and seven
regenerated `platform/src/generated/{harvest,census}/*.json`. **No FROZEN
orchestrator/WriterBase, no `ga_*`/`bo_*`/`ka_*`/`ph_*`/`mi_*` writer logic, no
`chart_facts` computation semantics, no `kala_*`/gochara serving code, no D-4b branch**
was modified. The one `chart_facts_categories_authoritative_v1.json` in the diff is a
generated census enumeration artifact, not chart-computation semantics. Notably, the
census correctly flagged `kala_convergence_staging` as D-4b territory and left it
untouched (§J respected).

## What must happen for RC-04 to reach ACCEPT (bounded, closable)

1. **Disposition the 5 open dark tables** (`chart_facts_history`,
   `chart_facts_supersedence`, `mimamsa_export_log`, `mimamsa_pool_contributions`, and a
   ruling on out-of-scope `kala_convergence_staging`) via the five-state taxonomy — either
   fold them into RC-09's `DARK_TABLE_DISPOSITIONS` under a Resolver ruling, or record a
   Resolver ruling that RC-04's scope is measure-only and the disposition is formally
   handed to RC-09 as new rows. As it stands the DONE-bar parenthetical is unmet.
2. **Record the two unintended probe changes** (`phala_anchors_get` 422 contract drift;
   `ref_yogas_get`/`ref_doshas_get` uncapped size) in `MARSYS_DEFECT_GAP_REGISTER` and/or
   open new RC-rows per §G — a prose flag in PROBE_DIFF is not the register entry §G
   mandates. "diff shows only intended changes" cannot be asserted while these sit
   untriaged.
3. **drill-crawl:** either run a real drill-crawl pass (zero dead ends) or obtain a
   Resolver ruling that the `drill_pointers` spot-check substitute suffices for RC-04's
   bar. Currently the clause is undischarged.

## Credit where due

The census/reachability leg is genuinely and honestly closed; the probe leg is real,
substantive, and self-critical to a commendable degree (it surfaces its own regression
rather than smoothing it over). The artifacts do not overclaim — the **hand-off summary**
does. Route the three items above (largely RC-09 / Resolver / defect-register work) and
RC-04 closes cleanly.

---

*End of VERIFY_RC-04 v1.0 — verdict REJECT (closable). Independent live re-verification
performed 2026-07-23 against the deployed connector + production DB; every reproduced
claim held.*
