---
lane: F-69
stream: S3_SATYA
stage: D (DIAGNOSE) — COMPLETE
class: CL-08 tier leak (TIER2-HONESTY)
author: SATYA builder (sonnet)
---

# F-69 — mimamsa_insight_get serves full numeric scores under a permanent non-calibrated tag

## 1. Live reproduction (today, 2026-08-16, re-verified)

`mimamsa_insight_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, top_k=50)`

Raw JSON saved to `briefs/parisesa/lanes/F-69/reproduce_raw.json` (full envelope; server-side
trim_report shows 25/50 `insight_units` served in the page, `total_returned=50` reported
upstream of the trim).

Result (salient fields, exactly as claimed):
- Top-level envelope: `calibration_status: "prior_only"`, `mode: "STRUCTURAL"`, note: *"L5
  Mīmāṃsā is SEALED in STRUCTURAL mode. Empirical calibration accrues as outcome data is
  recorded."*
- Every `insight_type: "retrodiction"` row carries `evidence_grade: "prior_only"` — e.g.
  `disc_retro_021e49f5-…-corr-20` has `rank_consequence: 0.95`, `n_support: 3`.
- Every `insight_type: "verdict_object"` row carries `evidence_grade: "structural"` — e.g.
  `verdict_career_setback` has `rank_consequence: 0.88`, `confidence_band: "[0.68,0.98)"`,
  `provenance_chain.grade: 8.8`; `verdict_career_entry` → `0.786` / `[0.59,0.89)` / `7.86`;
  `verdict_career_change` → `0.774` / `[0.57,0.87)` / `7.74`.
- No field anywhere in the served payload masks, rounds, buckets, or flags these numbers as
  non-calibrated — they are full-precision floats served directly alongside the
  `prior_only`/`structural` tag.

CONFIRMED REPRODUCES exactly as claimed. Not ALREADY-FIXED.

## 2. Claim decomposition

- **C1** — the top-level envelope declares the whole L5 layer non-calibrated
  (`calibration_status: 'prior_only'`, `mode: 'STRUCTURAL'`). Confirmed: `register_p1_synthesis.ts`
  line 560-562 hardcodes this wrapper on every response, unconditionally.
- **C2** — every `verdict_object` row's `evidence_grade` is permanently `'structural'`, never
  `'empirical'`, "by construction — confirmed in source, not merely observed live." Confirmed for
  the two verdict_object code paths (see §3) — both write the literal string `"structural"` with
  no branch that could ever produce `"empirical"` for this row type.
- **C3** — every `retrodiction` row's `evidence_grade` is `'prior_only'` unless `n_support>=5`.
  Confirmed: `mi_darshana.py:215` — real conditional, not a permanent literal (`"empirical" if n >=
  5 else "prior_only"`) — but the sampled live rows (`n_support: 3`) fall on the `prior_only` side.
  This sub-claim is technically NOT a permanent-tag defect the way C2 is (C3's tag can flip to
  `empirical` given enough support) — worth noting as a refinement: the finding's framing groups C2
  and C3 together as "permanent non-calibrated tagging," but only C2 (verdict_object) is provably
  permanent from source; C3 (retrodiction) is honestly conditional and currently unmet.
- **C4** — despite C1-C3, both row types are served with full numeric `rank_consequence`,
  `confidence_band`, and `provenance_chain.grade` (0-10 scale) with **no suppression applied
  anywhere in the served payload.** Confirmed: no rounding/bucketing/suppression code path exists
  between the writer (mi_darshana.py) and the MCP tool wrapper (register_p1_synthesis.ts) for any
  of these three fields.

## 3. Mechanism (file:line, read directly — corrects the finding's own mechanism pin)

**Writer side** — `platform/python-sidecar/pipeline/orchestrator/writers/mi_darshana.py`,
`MiDarshanaWriter._substep_insight_units`:

- Line 215 (retrodiction/emergent_law rows, `_substep_insight_units` §3 "Emergent-law insights"):
  ```python
  "empirical" if n >= 5 else "prior_only",
  ```
  Confirms C3 as claimed by the finding — line number matches exactly.

- Line 366 (verdict_object §5, the `status == "no_evidence"` branch): the row is appended with
  `"structural"` hardcoded as the `evidence_grade` positional argument. Confirmed — matches the
  finding's citation.

- Line 509 (verdict_object §5, the main promised/conditional/denied branch): same —
  `"structural"` hardcoded as the `evidence_grade` positional argument, immediately after
  `rank_consequence` is set to `g_norm = grade / 10.0` (line 505) and `confidence_band` is set to
  the computed `f"[{conf_lo},{conf_hi})"` (line 506). Confirmed — matches the finding's citation.

**CORRECTION to the finding's mechanism trace:** line **247** is NOT a verdict_object site. It is
inside `_substep_insight_units` §4, "Load-bearing signal insights" (the `for r in lb_rows:` loop,
lines 232-253), which appends rows with `insight_type: "load_bearing"` (line 240), not
`verdict_object`. Line 247's `"structural"` literal hardcodes `evidence_grade` for **load_bearing**
rows — a real, adjacent instance of the same defect class (see §4), but not itself a verdict_object
citation. The finding's claim text ("every served `insight_type='verdict_object'` row carries a
HARDCODED evidence_grade: 'structural' literal") is fully supported by lines 366 and 509 alone;
line 247 should be re-filed as a sibling (§4), not a third verdict_object instance.

**Serving side** — `platform-mcp/src/tools/register_p1_synthesis.ts`, `mimamsa_insight_get` tool
handler (lines 526-570). Line 559-564:
```ts
const wrapped = {
  calibration_status: 'prior_only',
  mode: 'STRUCTURAL',
  note: 'L5 Mīmāṃsā is SEALED in STRUCTURAL mode. Empirical calibration accrues as outcome data is recorded.',
  ...(typeof data === 'object' && data ? data : { content: data }),
}
return dualOutput(envelope(wrapped, 'mimamsa_insight_get', 'synthesis_calibration'))
```
The `wrapped` object literally spreads the raw `data` payload (which already contains each row's
full `rank_consequence` / `confidence_band` / `provenance_chain` with no transformation) directly
into the response after slapping the `calibration_status`/`mode`/`note` fields on top. There is no
intermediate step anywhere in this handler — no rounding, no bucketing into a coarse tier, no
`judgment_flags` entry — that reduces numeric precision or otherwise discloses the tension between
"STRUCTURAL, not calibrated" and "here is a precise 0.88 score and an 8.8/10 grade." This confirms
C4: the leak is real and exists at both the writer (raw numbers computed and stored) and the
serving layer (raw numbers passed through unmodified).

Note a **related but distinct** existing safety mechanism in the SAME file: `MC-010` (lines 419,
440, 456, 487 — "P0-safety, ŚODHANA T1") masks the verdict **verb** ('promised'/'denied') when
`n_support === 0`, in the `verdict_summary`/`bodha_domain_reading_get` code path elsewhere in this
file. That proves the file's authors are capable of exactly the kind of numeric/verb suppression
F-69 asks for — they just never applied it to `mimamsa_insight_get`'s raw `insight_units` array
(this tool bypasses `verdict_summary` entirely and serves `data` straight from the registry
capability response).

## 4. Sibling census

Grep across `mi_darshana.py` for every hardcoded `evidence_grade` literal (not a DB-read value, not
a genuine conditional):

| Line | Insight type | Value | Hardcoded / conditional | Same defect class? |
|---|---|---|---|---|
| 117 | `calibrated_outlook` | `r.get("evidence_grade", "prior_only")` | reads real DB column | NO — legitimate passthrough |
| 184 | `manifestation_grammar` | `"empirical"` | hardcoded literal, but SQL already filters `WHERE evidence_grade = 'empirical'` (line 151) | NO — echoes a real filter, not fabricated |
| 215 | `emergent_law` / retrodiction | `"empirical" if n >= 5 else "prior_only"` | real conditional | NO — this is C3, honestly conditional |
| **247** | **load_bearing** | `"structural"` | **hardcoded literal, no branch** | **YES — genuine sibling, same class as C2** |
| **366** | **verdict_object** (no_evidence) | `"structural"` | **hardcoded literal, no branch** | **YES — this finding (F-69), C2** |
| **509** | **verdict_object** (main) | `"structural"` | **hardcoded literal, no branch** | **YES — this finding (F-69), C2** |

The `load_bearing` sibling at line 247 is served identically unsuppressed: its
`rank_consequence` is the raw `sensitivity` float (e.g. `0.70`, `0.60`) with no
`confidence_band` but the same permanent `"structural"` tag and no suppression — same defect,
same fix surface (one predicate in the serving layer or one shared row-shaping helper in the
writer would cover both `verdict_object` and `load_bearing` in one pass).

No other `mi_*` writer hardcodes `evidence_grade` to a fixed literal without either reading a real
DB column or filtering on it first: `mi_sambandha.py` and `mi_pramana.py` both write
`evidence_grade` as a bound SQL parameter (computed upstream, not inspected in this pass — flagged
for the SPEC stage to confirm, not confirmed clean here) rather than an inline hardcoded string
literal in an append-row call; grep found no second `"structural"`/`"prior_only"` append-row
literal pattern outside `mi_darshana.py` in the writers directory.

**Cross-layer parallel (already diagnosed separately, not re-diagnosed here):** F-68 is the same
numeric-leak-under-non-calibrated-tag defect class in L4 Phala (`ph_nimitta`) — a distinct file,
distinct writer, distinct serving tool. F-69 (L5 Mīmāṃsā, `mi_darshana.py` +
`register_p1_synthesis.ts`) and F-68 are two independent surfaces of one design gap: a served
numeric confidence/rank field with no suppression predicate tied to its own non-calibrated tag.
Worth one shared suppression predicate/utility at SPEC stage if feasible (e.g. a single
`suppressUnderCalibration(row)` helper both `mimamsa_insight_get` and the ph_nimitta serving path
call), rather than two independently-authored fixes that could drift apart.

## 5. Blast radius

- **CL-00 controls:** none of the 27 known CL-00 controls assert on `mimamsa_insight_get`'s
  `evidence_grade`/`rank_consequence`/`confidence_band` shape (checked
  `platform/scripts/governance/` control list headings) — low risk of control regression from a
  suppression fix.
- **Other lanes sharing these files:** `mi_darshana.py` is inside the S3 lease
  (`L5_mimamsa/**`/`mi_*` pattern) per the S3 OWNS declaration in the plan. No other stream's lease
  lists `mi_darshana.py` or `register_p1_synthesis.ts`'s `mimamsa_insight_get` block; F-68 (the CL-08
  sibling in ph_nimitta) is also S3-owned, so both P3-b lanes sit inside one stream — sequencing
  them together (or building the shared predicate once) is a same-stream call, not a cross-stream
  coordination cost.
- **MC-010 precedent risk:** any fix here should NOT touch the `MC-010` verb-masking logic
  (lines 419-487, a different code path in the same file guarding `verdict_summary`) — that is
  settled P0-safety behavior for a different consumer surface
  (`bodha_domain_reading_get`/`judgment_query`'s verdict_summary), not `mimamsa_insight_get`'s raw
  `insight_units` array. A SPEC that touches `_substep_insight_units`'s row-construction code (for
  the writer-side hardcodes at 247/366/509) must not perturb the MC-010 branches, which live in a
  separate function/consumer path in the same file.
- **Downstream consumers of `mimamsa_insight_get`:** any caller currently reading
  `rank_consequence` / `provenance_chain.grade` numerically (dashboards, other MCP tools chaining
  off this one) would see those fields change shape if SPEC chooses bucketing/suppression over a
  pure disclosure-flag addition — flag this trade-off explicitly for SPEC (additive
  `judgment_flags`/`catalog_only`-style flag is lower blast-radius than mutating the numeric fields
  themselves, consistent with §N.6's established pattern of flagging rather than dropping/mutating
  data).
