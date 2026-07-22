---
artifact: VERIFY_RC-04.md
canonical_id: RETRIEVAL_VERIFY_RC04
version: 2.0
status: VERDICT — ACCEPT (fix-cycle 2 re-verification 2026-07-23; cycle-1 REJECT below, retained for audit)
governed_by: 00_ARCHITECTURE/briefs/RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md §E RC-04, §D.4
verifier: Independent VERIFIER agent (opus, high effort) — NOT the RC-04 implementer (both cycles)
verified_against: res/rc04-census-probe-rerun @ 266ea935 (fix-cycle), on top of REJECT @ 5787cf94, base main@651c64789bbc
date: 2026-07-23
---

# VERIFY RC-04 — Fix-cycle 2 re-verification (2026-07-23)

## VERDICT: ACCEPT

The cycle-1 REJECT (retained verbatim below) named 3 bounded, closable gaps against the
§E RC-04 DONE bar. The fix-cycle (commit `266ea935`, on top of REJECT `5787cf94`) addresses
all 3 with real evidence, not relabeling. I re-verified independently against the live
deployed connector + production DB and the branch source; every claim I could test held.

## Item-by-item re-verification

### Item 1 — Disposition the 5 previously-open dark tables → ADDRESSED (real evidence, not relabel)

`RESOLVER_RULINGS.md` Ruling **RC-04-001** (appended; RC-09/RC-10 region byte-unchanged —
confirmed the only two `-` lines vs `5787cf94` are the footer replacement, append-only
respected) dispositions:
- `chart_facts_history` → **OPERATIONAL** — DB-trigger audit log (`trg_chart_facts_audit`,
  migration 128/206), zero application-code reads, sibling of already-dispositioned
  `chart_grants`.
- `chart_facts_supersedence` → **OPERATIONAL** — `fn_supersede_build()`-populated (migration
  129/206), zero reads.
- `mimamsa_export_log` → **OPERATIONAL** — write-only export bookkeeping from `mi_vistara.py`
  (migration 355), sibling of already-dispositioned `mimamsa_event_provenance`.
- `mimamsa_pool_contributions` → **OPERATIONAL** — capture-only cross-chart pool table
  (migration 425); the migration header itself is dispositive ("no serving path reads this
  table while the flag is off").
- `kala_convergence_staging` → **formally routed to D-4b as a deliberate, reasoned
  non-disposition**, respecting the brief's §J must_not_touch on `kala_*` serving semantics.
  This is a terminal state for RC-04's purposes (dispositioned-as-out-of-scope), not a
  silent open item.

Each of the 4 OPERATIONAL rulings carries a concrete migration/trigger citation and the
same "grep the tree for serving-surface reads → zero" method RC-09 used — this is genuine
dispositioning under §D.5(iv), not cosmetic relabeling. `CENSUS_v2_0.md` §2/§4 updated: the
"5 genuinely-open" table now shows terminal disposition for all 5; the "5 named exceptions
remain genuinely open" prose is gone, replaced by "Zero tables in this census remain
undispositioned." DONE-bar clause-1 parenthetical discharged. **MET.**

### Item 2 — Record the 2 unintended regressions in the defect register → ADDRESSED (new OPEN entries; live-reproduced)

`MARSYS_DEFECT_GAP_REGISTER_v2_0.md` gains **CR-122** (phala_anchors_get 422), **CR-123**
(ref_yogas_get/ref_doshas_get uncapped), and **CR-124** (22 unaudited `dualOutput(data)`
siblings) — all **OPEN**, all explicitly **not fixed** (correctly scoped: RC-04 is
measurement-not-remediation per §G). Not silently fixed-and-forgotten; not still missing.
I independently reproduced both regressions **live** against the deployed connector:
- `phala_anchors_get(482012f1)` with no `date_range` → `422 date_range Field required`. The
  loaded MCP tool schema lists only `chart_id` in `required` (`date_range` optional) — the
  contract drift CR-122 describes is real and precisely characterized.
- `brahma_yoga_catalog` = **179 rows**, `brahma_dosha_catalog` = **79 rows** (direct SQL) —
  exactly the growth CR-123 cites as the cause of the 87KB/61KB uncapped responses.
- CR-124's 22 line numbers (440…1583) match `grep -n "return dualOutput(data)"` **exactly**.

Register changelog bumped to v3.11 with honest OPEN framing and §G citation. **MET.**

### Item 3 — Drill-crawl: run it OR adequately justify skipping → ADDRESSED (justified + 2 real fixes)

The task offered an either/or. The fix-cycle takes the "adequately-justified substitute"
branch via Ruling **RC-04-002**, and strengthens it by actually finding and fixing two real
navigability defects (evidence the spot-check was substantive, not a rubber-stamp):
- **`phala_outlook_get`** emitted `recover_via.instrument: "unknown_tool"` because
  `dualOutput(data)` was called without its optional `toolName` (default `'unknown_tool'`,
  `register_p1_aliases.ts:181` — source-confirmed). Fixed to `dualOutput(data,
  'phala_outlook_get')` at `register_p1_aliases.ts:1434` (source-confirmed).
- **`register_d9_judgment.ts:1051`** drill pointer `query_classical_texts` was the internal
  registry URI, not a live MCP tool — same SC-18 class as two already-fixed siblings in the
  same array. Fixed to `ref_rules_search`. I confirmed live that `ref_rules_search` **is** a
  registered, responding MCP tool and that it resolves to `marsys://tool/L0/
  query_classical_texts` (`register_p1_reference.ts:211`); `query_classical_texts` itself is
  not exposed as an MCP tool name — so the old pointer was genuinely dead and the new one is
  genuinely live and semantically equivalent.

The ruling grounds the substitution in existing project precedent (RS-4 proportionality
carve-out; RC-10's DEFERRED-not-force-built rulings) and honestly names the 22 unaudited
siblings as CR-124 rather than claiming a false "crawl clean." Adequate. **MET.**

## must_not_touch check → CLEAN

Full branch diff vs `main@651c6478` touches only: the RC-04 deliverables + registers
(`retrieval_residual/**`, `MARSYS_DEFECT_GAP_REGISTER`), regenerated `retrieval_impl/*`
generator outputs + `generated/{harvest,census}/*.json` (census re-run artifacts, overwritten
in place by design), and two serving-plane MCP-registration files (`register_p1_aliases.ts`,
`register_d9_judgment.ts`) — all within `may_touch` (`platform/**`, `platform-mcp/**`). **No**
FROZEN orchestrator/WriterBase, **no** `ga_*/bo_*/ka_*/ph_*/mi_*` writer build logic, **no**
`chart_facts` computation semantics, **no** `kala_*`/gochara serving semantics (notably
`kala_convergence_staging` was deliberately NOT dispositioned precisely to respect §J), **no**
D-4b branch/brief/ledger, **no** root `CLAUDECODE_BRIEF.md`.

## Minor, non-blocking imprecisions (noted, do not affect verdict)

1. The `register_p1_aliases.ts:1434` comment and Ruling RC-04-002 attribute the
   `ref_rules_search`→URI resolution to `mcp_capability_bridge.ts`; the actual alias→URI
   binding lives in `register_p1_reference.ts:211` (the bridge maps platform-side capability
   names). Substance correct (the tool is live and equivalent); file citation slightly off.
2. `CENSUS_v2_0.md` §2 NAVIGABLE paragraph refers to the 22 siblings being recorded in
   "CR-122/CR-123 companion entries' neighborhood" where it means **CR-124**. The CR-124
   entry itself is present and correct; this is a cosmetic cross-reference slip.

Neither touches the substance of any of the 3 items. Recommend they be tidied opportunistically,
not gated on.

## Build-state note (not a gate on this verdict)

The two source one-liners are type-safe by inspection (a second string arg to a function
with an optional-defaulted `toolName`; a string-literal value change on an existing object
property) and are consistent with the implementer's reported `tsc --noEmit` clean + 987/987
registry-suite pass. They are **not yet deployed**, so the `phala_outlook_get` fix cannot be
observed live until the campaign's batched deploy (§I) — this is expected and not an RC-04
acceptance blocker (the source fixes both target confirmed-live tools).

---

*End of fix-cycle 2 re-verification. VERDICT: ACCEPT. Cycle-1 REJECT retained below verbatim
for audit trail.*

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
