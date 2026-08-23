---
lane: F-124
stream: S2 (MĀTRĀ)
stage: D — DIAGNOSE
status: REPRODUCES (finding's own suspected mechanism is confirmed correct, and traced further than the finding itself does)
diagnosed: 2026-08-16
files_owned_this_lane: platform-mcp/src/tools/registry_bridge.ts (S2 HOT lease)
companion_lanes: F-14 (full trace lives there), F-15
---

# F-124 DIAGNOSIS — assess_career vs. assess_marriage/assess_health depth asymmetry

**This finding shares its full mechanism trace with F-14 (`../F-14/DIAGNOSIS.md`) — read
that document for the complete file:line trace (§3.1-3.4), sibling census (§4), and blast
radius (§5). This document covers what's specific to F-124: its own live reproduction
(all three tools, diffed) and the direct answer to the question F-124 itself poses — "is
this the same root cause as F-14/F-15, or a deeper/different wiring gap?"**

## 1. Live reproduction

**Reproduce_cmd (per the finding's own phrasing):** "Q1/Q2/Q3. Compare
`jq '.object|has("reading"),has("completeness_directive"),has("domain_completeness")'`
across `E2_q2_raw_assess_career.json` (all true) vs. `E2_q1_raw_assess_marriage.json` and
`E2_q3_raw_assess_health.json` (all false)."

Ran the live equivalent directly: `assess_career`, `assess_marriage`, `assess_health`, and
(added) `assess_wealth` for completeness, all against the canonical chart, at both default
depth and `deep_dive`. Structural diff saved to `evidence_comparison_standard_depth.json`.

**At standard depth** (`evidence_comparison_standard_depth.json`):

| Tool | `reading` present | `domain_completeness` present | `completeness_directive` present |
|---|---|---|---|
| `assess_career` | **true** (12 families) | **false** | **false** |
| `assess_wealth` | **true** (13 families) | **false** | **false** |
| `assess_marriage` | false | false | false |
| `assess_health` | false | false | false |

**At `deep_dive` depth**, all four tools return neither `reading` nor `domain_completeness`
nor `completeness_directive` for anyone, including career/wealth — the entire `grounding`
layer is dropped for all four (see F-14 DIAGNOSIS §3.3/§5 "NEW" item — a distinct,
budget-side effect of the forced full-form B.11 orientation pre-fetch, not what this finding
is about).

**Verdict: REPRODUCES, partially updated.** The finding's core claim — a `reading` asymmetry
between career/wealth and marriage/health — reproduces exactly as stated, live, today
(confirmed at standard depth; the response envelope shape has changed since the finding's
own evidence files were captured — see §3 — but the substantive gap it describes is
unchanged). **The finding's `completeness_directive`/`domain_completeness` half is now
STALE**: today, NEITHER side of the asymmetry gets those two fields — even `assess_career`,
which the finding's evidence file recorded as returning them, no longer does. This is not a
partial fix; it's a NEW regression on top of the old gap (see §3.4 in F-14's diagnosis). Not
`ALREADY-FIXED` — if anything, the surface got structurally worse in one dimension
(`domain_completeness`) while staying exactly as broken in another (`reading`).

## 2. Claim decomposition

F-124's claim has more sub-assertions than F-14/F-15 because it's a comparative finding:

| # | Sub-claim | Verified today? |
|---|---|---|
| C1 | `assess_career` returns a substance-inline `reading` array (11-12 concept families, fact_id-cited sentences) | TRUE — 12 families, 11 `served`/1 `domain_block_not_served` (D9), live-verified |
| C2 | `assess_career` returns `completeness_directive` | **FALSE today** — was true when the finding's evidence was captured; regressed since (§3.4 in F-14 diagnosis) |
| C3 | `assess_career` returns a `domain_completeness` accounting (~13,825 concepts) | **FALSE today** — same regression as C2. The *number* (13825) still appears, but only inside `kernel.flags[0]`'s free-text message, never as a structured field |
| C4 | `assess_marriage`/`assess_health` return NO `reading`, NO `completeness_directive`, NO `domain_completeness` | TRUE for all three fields, on both tools, confirmed live |
| C5 | `assess_career` returns 2 CONFIRMED domain-bearing yoga firings that marriage/health don't | NOT independently re-verified this session (yoga-firing content wasn't the focus of this diagnosis pass; flagging as unverified rather than asserting either way — B.10) |
| C6 | The depth difference is invisible in the tool schema/envelope (`orientation_ok:true` on all three, `reading_checklist` populated on all three) | Partially re-verified: `orientation_ok:true` confirmed present and `true` on all three live calls. `reading_checklist` was NOT observed in any of the four live responses' `grounding` at standard depth (it's in `buildAssessResponse`'s grounding allow-list at line 2914, but `response['reading_checklist']` was `undefined` for all four tools in this session's calls — plausibly it's set only under specific conditions this session didn't trigger, e.g. `max_signals_per_lens` used, or a bundle a different upstream capability sets). Not fully re-verified; flag for SPEC stage to re-check if `reading_checklist` is load-bearing to any remediation. |
| C7 | Suspected mechanism: "the Omega5 gather-then-compose reading/completeness layer has been wired to assess_career only; the sibling handlers still return the older bundle shape" | **CONFIRMED CORRECT, and traced further** — see §3 |

## 3. Mechanism — is this the same as F-14/F-15, or different?

**Answer: it is exactly the same missing-map-key + missing-call-site mechanism as F-14/F-15
— not a separate or deeper defect.** F-124's own suspected mechanism text turns out to be
precisely right, and this diagnosis traces it to the exact lines:

1. `DOMAIN_READING_FAMILIES` (`registry_bridge.ts:1034`) has `wealth`/`career` only — no
   `health`/`relationship`.
2. `attachDomainReading` (`registry_bridge.ts:1569`, early-return at `:1573`) never sets
   `response['reading']` for a domain not in that map.
3. **The decisive evidence for "wired to assess_career only"**: reading the actual handler
   bodies (`registry_bridge.ts:2959-3078`), `assess_career` (`:3030`, `:3032`) and
   `assess_wealth` (`:3112`, `:3114`) call `attachDomainCompleteness`+`attachDomainReading`;
   `assess_marriage` (`:2959-2995`) and `assess_health` (`:3042-3077`) call **neither** — the
   call sites are simply absent from those two handlers' code, not merely gated by a
   condition that evaluates false. This is F-124's "sibling handlers still return the older
   bundle shape" claim, confirmed literally true at the source level.

So F-124 is **not** a deeper/different wiring gap than F-14/F-15 — it is the same finding
observed from the comparative angle (looking at all three tools side-by-side surfaces the
same defect F-14/F-15 each describe from a single tool's perspective). **One spec, one fix,
closes all three lanes' `reading` sub-claims together.**

**What F-124 adds beyond F-14/F-15**: its `completeness_directive`/`domain_completeness`
sub-claims (C2/C3 above) surface a FOURTH thing worth naming precisely — those two fields
are not currently gated by `DOMAIN_READING_FAMILIES` or by the missing call sites at all, but
by a completely separate, newly-discovered defect: `buildAssessResponse`
(`registry_bridge.ts:2925`) checks `response['completeness']` for inclusion in the served
`grounding` layer, but `attachDomainCompleteness`/`attachDomainReading` set
`response['domain_completeness']` and `response['completeness_directive']` — different key
names, so the check never fires, for ANY of the four assess_* tools. Full trace in F-14
DIAGNOSIS.md §3.4. **This is the one piece of F-124 that is NOT closed by the F-14/F-15 fix
alone** — a remediation that only adds `health`/`relationship` to the family maps and wires
the two call sites will restore `reading` for all four tools, but will still leave
`domain_completeness`/`completeness_directive` absent everywhere, including
`assess_career`/`assess_wealth`, unless `buildAssessResponse`'s allow-list is also corrected.
The SPEC stage must cover both, or F-124's C2/C3 remain open after B-stage lands.

## 4. Sibling census

Identical to F-14 §4 (same maps, same four tools, same call-site table). No further siblings
found specific to the comparative angle.

## 5. Blast radius

Identical to F-14 §5, plus: F-124's severity is `TIER3-EXPERIENCE` (vs. F-14/F-15's
`TIER1-CORRECTNESS`) — worth flagging to the conductor that the `domain_completeness`/
`completeness_directive` regression discovered in §3 above (F-14 §3.4) is arguably a
TIER1-class correctness defect in its own right (it silently drops fields the tool
description and prior evidence both promise, for the tools that are supposed to be the
*working* half of this comparison) even though it surfaces here inside a TIER3 finding. Not
this diagnosis's call to re-tier it — flagging for PRATINIDHI/conductor at SPEC/REVIEW stage.
