---
lane: F-117
stream: S3_SATYA (diagnosis only — see §6 LEASE NOTE, file is outside S3's normal lease)
stage: D (DIAGNOSE) — COMPLETE
class: CL-09 earned signal (TIER3-EXPERIENCE)
author: SATYA builder (sonnet)
---

# F-117 — bo_upaya "resonance" ranking is inverse-shadbala with two dead composite terms, and priority labels are unexplained rank-relative

## 0. LEASE NOTE (read first)

`bo_upaya.py` and `formulas.py` (`platform/python-sidecar/bodha_writers/formulas.py`) are **L2
Bodha** files. Per the plan's file-lease board, Stream S3 SATYA's owned lease is
`L4_phala/**`, `L5_mimamsa/**`, `ph_nimitta/**`, `muhurta.py` — this file is outside that lease.
This DIAGNOSIS.md is produced anyway per the dispatching instruction (Stage D is documents-only,
zero file-conflict risk), but **Stage B (BUILD) for this finding must not proceed under S3's
lease as-is.** Any fix requires either (a) SŪTRADHĀRA re-leasing `bo_upaya.py` /
`bodha_writers/formulas.py` / `bo_cgm_motifs.py` to S3 for this lane specifically, or (b) handing
this SPEC to whichever stream already owns L2 Bodha `bo_*` writers, before any code is touched.

## 1. Live reproduction (today, 2026-08-16, re-verified)

`bodha_remedies_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, limit=8, fields='compact')`

Raw JSON saved to `briefs/parisesa/lanes/F-117/reproduce_raw.json` (full `resonances` +
`resonance_ranked` arrays, verbatim).

Result — all 8 claims verified exactly as stated:
- `contradiction_factor = 0` for all 8 grahas.
- `domain_burden = 0` for all 8 grahas.
- `motif_burden = 0.4` for all 8 grahas (identical value, not merely similar).
- Rank order by `resonance_score` DESC: Venus (0.173195) > Ketu (0.138642) > Rahu (0.1261) >
  Moon (0.116022) > Jupiter (0.11466) > Mars (0.1027) > Sun (0.097822) > Saturn (0.094032).
- This is exactly the inverse of the `sha=` value in each row's own `citation` string: Venus
  0.84 < Moon 0.94 < Ketu 1.00 = Rahu 1.00 < Mars 1.11 < Jupiter 1.20 < Saturn 1.57 < Sun 1.69 —
  confirmed Venus (lowest sha) ranks #1 (highest resonance/weakness), Sun (2nd-highest sha) ranks
  #7, Saturn (highest sha) ranks #8. The one rank inversion relative to a pure sha sort (Jupiter
  sha=1.20 < Mars sha=1.11 but Jupiter ranks #5 ahead of Mars #6) traces to the real, non-constant
  `weakness_score` composite (shadbala + bhava_bala + dispositor + dasha_proximity terms — see §3)
  rather than sha alone, so "resonance ranking is exactly inverse-shadbala" is a very close but not
  100%-exact restatement; "inverse-shadbala-dominated" is the precise claim.
- Rahu and Ketu both carry `sha=1.00` exactly (visible in their `citation` strings) and rank #3
  and #2 respectively, both `remedy_priority_class: "high"`.
- Venus's `resonance_score=0.173195` (well under half of the theoretical 0-1 scale) is labeled
  `remedy_priority_class: "critical"`.

CONFIRMED REPRODUCES exactly as claimed. Not ALREADY-FIXED.

## 2. Claim decomposition

- **C1** — `contradiction_factor=0` for every graha. Confirmed real formula, but zero for
  chart-specific data reasons — see §3 (this is a genuine per-graha computed value, not a
  hardcoded literal; it happens to read 0 for this chart/build).
- **C2** — `domain_burden=0` for every graha, structurally, for every chart, not just this one.
  Confirmed **hardcoded** — see §3.
- **C3** — `motif_burden=0.4` for every graha, identically. Confirmed **effectively constant**
  for this chart via a class-level hardcoded constant one layer upstream (not a direct literal in
  `bo_upaya.py` itself) — see §3, this is the most consequential mechanism finding of this lane.
- **C4** — resonance rank order is (near-)exactly inverse shadbala, i.e. the nominally 4-factor
  composite collapses to a monotone function of `weakness_score` (itself shadbala-dominated) once
  C1-C3 are constant/near-constant. Confirmed by direct computation from the live data (§1).
- **C5** — Rahu/Ketu's `sha=1.00` is a placeholder (shadbala not classically computed for the
  nodes) yet they rank #2/#3 "high" priority on it. Confirmed — see §3 `_fetch_shadbala`
  docstring and fallback behavior.
- **C6** — a `resonance_score` of 0.173 (well under half-scale) is labeled `"critical"`. Confirmed
  as **intentional rank-relative design**, not a bug — see §3 `_priority_class` — but the served
  narration does not disclose the relative framing, which is itself a real narration-fidelity gap
  (§N.7-adjacent, distinct from C1-C5's computation-mechanism gap).

## 3. Mechanism (file:line, read directly)

**`platform/python-sidecar/bodha_writers/formulas.py`, `resonance_score_v1()`** (function starts
line 257):
```python
contradiction_factor = min(g.msr_signals_in_conflict, 1.0)   # line 271
domain_burden = min(g.cdlm_weakest_constituent_count, 1.0)    # line 272
motif_burden = min(g.cgm_motifs_weakest_node, 1.0)            # line 273
...
weakness_score * (1 + contradiction_factor * 0.20) * (1 + domain_burden * 0.15) * (1 + motif_burden * 0.10)  # lines 280-282
```
All three terms are genuinely read from the `ResonanceInputs` dataclass fields the caller
populates — the formula itself is not the defect; the defect is what `bo_upaya.py` supplies as
those three inputs.

**`platform/python-sidecar/pipeline/orchestrator/writers/bo_upaya.py`**,
`_build_resonances_and_prescriptions()`, the per-graha `ResonanceInputs(...)` construction
(function starts line 1062, the relevant block at lines 1153-1183):

- **C2 mechanism (domain_burden), line 1175:**
  ```python
  # BA-P2.5 #4 — honest placeholder: bodha_cdlm_cells.weakest_constituent_graha_jsonb
  # exists as a column but is never populated by bo_sangati (dead column) — no real
  # per-graha CDLM value exists yet to reference. Left at 0.0 per B.10.
  cdlm_weakest_constituent_count=0.0,
  ```
  Confirmed **hardcoded literal `0.0` for every graha, every chart** — the writer's own comment
  states the upstream column (`bo_sangati`'s `weakest_constituent_graha_jsonb`) is "never
  populated," i.e. this is a genuine unimplemented data path (§N.4/B.10-compliant honest zero,
  not a fabricated value), but the downstream consequence is exactly C2: `domain_burden` cannot
  vary by graha or by chart until that upstream column is populated.

- **C3 mechanism (motif_burden), line 1180:**
  ```python
  cgm_motifs_weakest_node=cgm_motif_weakness.get(graha, 0.0),
  ```
  This is NOT a hardcoded literal — it is a real per-graha dict lookup from
  `_fetch_cgm_motif_weakness()` (bo_upaya.py lines 497-535), which computes
  `weakness = 1.0 - MIN(motif_strength across the graha's bodha_cgm_motifs memberships)`. The
  uniform `0.4` across all 8 grahas traces one layer further upstream, to
  `platform/python-sidecar/pipeline/orchestrator/writers/bo_cgm_motifs.py`:
  - `_detect_mutual_aspects()`, line 461: every `mutual_aspect` motif (any pair of grahas in
    mutual aspect, regardless of which grahas, which aspect, or orb) is assigned
    `"strength": 0.6` — a **hardcoded class-level constant**, not a computed per-pair value.
  - Triangle variant, line 499: `"strength": 0.75`, same pattern.
  - `_detect_mutual_reception()`, line 291: `"strength": 0.8`, same pattern.
  - Per `bo_upaya.py`'s own comment at line 1176-1179, the stronger/differentiating motif classes
    (`stellium`, `parivartana_chain`) are "Tier-3-blocked on missing bo_karanajala dispositor
    edges" and so do not fire for any chart today — leaving `mutual_aspect` (constant 0.6) as
    the only reachable motif class in practice.
  - **Mechanism confirmed:** if every graha in a chart participates in at least one
    `mutual_aspect` motif (very common — mutual aspects between the 9 grahas are frequent) and no
    `mutual_reception`/`parivartana_chain`/triangle motif also touches that graha, then
    `MIN(motif_strength)` resolves to the same constant `0.6` for every graha, so
    `motif_burden = 1.0 - 0.6 = 0.4` for every graha identically — exactly the live result. This
    is a real per-graha computation whose *output happens to be constant* because its only input
    class assigns identical strength regardless of which specific grahas/degrees are involved,
    not because the field is dead-wired like C2. This distinction matters for SPEC: fixing C2
    means wiring a genuinely-missing data source; fixing C3 means varying `mutual_aspect`
    `strength` by a real astrological differentiator (e.g. orb tightness, aspect type, or the
    aspecting grahas' own dignity) rather than one flat constant per motif class.

- **C1 mechanism (contradiction_factor), line 1171:**
  ```python
  msr_signals_in_conflict=min(len(dosha_by_graha.get(graha, [])) * 0.1, 1.0),
  ```
  Real per-graha computation (dosha count × 0.1, capped at 1.0). It reads `0` for every graha in
  THIS chart/build because `dosha_by_graha` (built from `_fetch_msr_dosha_sigs_by_graha` +
  `_fetch_active_doshas_by_graha`, lines 1079-1088) returned zero doshas for all 9 grahas for this
  particular build — confirmed by every row's own `citation` string reading `dosha_count=0`. This
  is chart-specific data absence (or a genuine "no fires=true doshas resolve to a graha for this
  chart" state), not a hardcoded literal in the C2 sense — flagged for SPEC to confirm whether
  this chart genuinely has zero active dosha-graha associations (plausible) or whether the
  `_fetch_active_doshas_by_graha` backfill path (lines 808-845) has its own gap, which is outside
  this 45-minute diagnosis window to fully rule out.

- **C6 mechanism (`"critical"` label), `_priority_class()`, lines 1005-1034:**
  ```python
  if rank <= 1:
      return "critical"
  if rank <= max(1, -(-total // 3)):        # ceil(total/3)
      return "high"
  ...
  ```
  Confirmed: this is **rank-relative thirds of the chart's own N grahas**, not an absolute
  threshold on `resonance_score`. The function's own docstring (lines 1005-1025) documents this as
  a deliberate MC-025a design decision — absolute thresholds were tried first and produced
  degenerate "everyone high" or "everyone low" results, so the design intentionally moved to
  "remedy the relatively weakest of THIS native's own nine grahas." **C6 is confirmed-as-designed,
  not a computation bug** — but `bodha_remedies_get`'s served narration (`"priority class
  critical"` in both the `lead` sentence and the per-row `remedy_priority_class` field) discloses
  neither the rank-relative framing nor that `"critical"` here means "weakest 1-of-8-in-this-chart"
  rather than "objectively severe affliction." No `resonance_ranked`/`resonances` field or
  `narration` text anywhere in the live payload states this. This is a real, distinct
  narration-fidelity gap (§N.7-adjacent — a grade/label that a reader would reasonably interpret
  as absolute-severity is actually rank-relative, with the relative framing undisclosed).

## 4. Sibling census

`grep -rn "resonance_score_v1\|ResonanceInputs(" platform/python-sidecar/` — `bo_upaya.py` is the
only caller of `resonance_score_v1`/constructor of `ResonanceInputs` in the codebase; no sibling
writer duplicates this formula.

`grep -n '"strength":' platform/python-sidecar/pipeline/orchestrator/writers/bo_cgm_motifs.py` —
the class-constant-strength pattern (C3's root cause) appears at all three motif-class detectors
in this same file: `_detect_mutual_reception` (0.8, line 291), `_detect_mutual_aspects` pair
(0.6, line 461) and triangle (0.75, line 499), and the `parivartana_chain` detector (a computed
`strength` variable, line 403 — not a flat literal, though currently unreachable per the Tier-3
block). All three flat-literal sites are internally consistent with each other (same "one strength
per motif *class*, not per instance" design) — this is a single, contained defect surface inside
one file, not scattered across the writers directory.

`grep -n "cdlm_weakest_constituent_count\|weakest_constituent_graha_jsonb"` across
`platform/python-sidecar/` — `cdlm_weakest_constituent_count` (C2) is set only in `bo_upaya.py`
(the one hardcoded site, line 1175) and its counterpart source column
`bodha_cdlm_cells.weakest_constituent_graha_jsonb` is referenced in the writer's own comment as
dead/never-populated; no other consumer reads this field, so C2 has no sibling call site — the fix
is entirely upstream (populate the column in `bo_sangati`) or a formula change, not a
find-and-replace across multiple call sites.

`_priority_class()` (C6) has exactly one call site in `bo_upaya.py` (line ~1275, inside the
ranking loop) — no sibling copy of this rank-relative-thirds logic exists elsewhere in the
writers directory (confirmed via `grep -rn "_priority_class\|priority_class(" platform/python-sidecar/`
returning only `bo_upaya.py` hits).

## 5. Blast radius

- **CL-00 controls:** none of the 27 known CL-00 controls assert on `bodha_rm_resonances`'
  `domain_burden`/`motif_burden`/`remedy_priority_class` shape (checked
  `platform/scripts/governance/` control list headings) — low risk of control regression.
- **Downstream consumers:** `bodha_remedies_get` (MCP), `bodha_rm_chart_summary`
  (`top_3_resonance_targets_jsonb`, populated from these same `resonances` rows per the WP-2.2/LCA-5
  rollup writer noted in this file's own history), and any Bodha-layer chart digest that surfaces
  "weakest graha for remedy purposes" all inherit whatever C2/C3/C6 fix lands here — a formula
  change to `resonance_score_v1` or its inputs is a **build-time, not serve-time** change: it
  requires a chart rebuild (bo_upaya re-run) to take effect, not just a serving-layer patch, since
  `bodha_rm_resonances` rows are computed and stored at build time (§N.3 delete-then-insert
  idempotency applies — a rebuild REPLACES, never accretes).
- **Ranking stability risk:** because C4 shows the current ranking already closely tracks shadbala,
  a SPEC that varies `motif_burden`/`domain_burden` by real per-graha data could shuffle
  `weakest_rank_in_chart` and `remedy_priority_class` for this and every other built chart — this
  is a native-facing behavior change (which graha gets recommended first for remedy), not a purely
  internal fix, and should be flagged to PRATINIDHI/native review before Stage B lands, independent
  of the lease question in §0.
- **File-lease conflict:** per §0, `bo_upaya.py` and `bo_cgm_motifs.py` are outside S3's
  `L4_phala/**`/`L5_mimamsa/**`/`ph_nimitta/**`/`muhurta.py` lease. No S3 lane currently claims
  these files. Confirm with SŪTRADHĀRA which stream (if any) already owns L2 Bodha `bo_*` writers
  before Stage S/B proceeds — this diagnosis does not authorize S3 to build against them.
