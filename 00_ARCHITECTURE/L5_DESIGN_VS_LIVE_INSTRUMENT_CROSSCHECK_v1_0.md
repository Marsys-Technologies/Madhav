---
artifact: L5_DESIGN_VS_LIVE_INSTRUMENT_CROSSCHECK_v1_0.md
canonical_id: L5_DESIGN_VS_LIVE_INSTRUMENT_CROSSCHECK
version: 1.0
status: CURRENT — cross-check of the L5 design against the live L0–L4 instrument (PLAIN_LANGUAGE_INSTRUMENT_MAP v1.1, real sample data)
authored_by: Cowork 2026-06-23
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
role: >
  Validates (and sharpens) the L5 Mīmāṃsā design against what L0–L4 ACTUALLY produces, using the live
  sample data in PLAIN_LANGUAGE_INSTRUMENT_MAP v1.1. Confirms the ph_pramana → L5 contract maps cleanly;
  flags upstream maturity gaps L5 depends on; and surfaces strong real-world evidence that the
  degenerate-distribution guard (P6.13 / GAP RL-6) catches a SYSTEMIC pattern, not a one-off bug.
source: PLAIN_LANGUAGE_INSTRUMENT_MAP_v1_1 (Cowork-authored descriptions + Claude-Code-filled live sample rows, 2026-06-23)
---

# L5 Design ✕ Live Instrument — Cross-Check

> The plain-language instrument map (with real sample rows from Abhisek's chart) lets us check the L5
> design against what L0–L4 genuinely produces — not what handoffs claimed. Verdict: **the design holds;
> the ph_pramana contract is confirmed; and the live data strongly validates several L5 choices.**

## §1 — CONFIRMED: the ph_pramana → L5 contract maps cleanly (no rework)

The live `ph_pramana` samples match exactly what L5 was designed to consume:
- `evidence_type=pending_observation`, `window_status=open`, **explicitly NOT scored**
  ("Recording happens in L5 Mīmāṃsā, not yet built"). → Our D5/D6 boundary is real in the data.
- Frozen falsifiers carry the structure our scorecard needs: *"REFUTED if no notable health event within
  ±21 days of Oct 31, 2026"* = `{metric, observation_window, domain}`. → Our `mi_bhavisya` frozen-bundle
  + `mi_pramana` multi-dimensional scorecard (timing/magnitude/domain/falsifier) maps directly onto this.
- `ka_bhavishya_lekha` falsifiers are already domain-tagged + windowed (health/relationship, ±21 days).
  → confirms the comparison model's inputs exist.

**Consequence:** no L5 rework from the live data. `mi_bhavisya`'s corrected `depends_on phala_pramana`
is right.

## §2 — CONFIRMED: the instrument's culture already matches L5's discipline

- **Staged-never-auto-applied** is already the L4 norm: `ph_suddha_sodhana` reports
  `confidence_delta_if_applied=-0.146 … Awaiting native review before application`. → Same philosophy as
  our **two-key lock** + suggestion-mode reverse channel. L5 extends an existing culture, not a new one.
- **Honest confidence ceiling:** L4 confidence is capped ~0.506 (the **G-LADDER ceiling for n=0, rob=3**);
  `ph_sodhana` flags anything above it as `confidence_inflation/major`. → This is the n=1 humility we
  designed around, already enforced upstream. **L5's whole job is to let that ceiling rise HONESTLY as the
  Prediction Journal earns outcome data.** The live data proves the ceiling is real and waiting for L5.
- **Canonical chart immutable:** `ph_rectification` tests birth times and **stages** them
  (`lagna_stable=false` for -90min across all ayanamshas → confirms recorded 10:43/Aries) without
  changing the chart. → Matches B.10 + our FORENSIC-exclusion (P4).

## §3 — STRONG VALIDATION: the degenerate-distribution guard catches a SYSTEMIC pattern

The map's "NOTICED WHILE SAMPLING" flags are not one bug — they are a recurring family, exactly what
guard P6.13 / GAP RL-6 exists to catch:

| asset | degenerate pattern observed | what a distribution guard would do |
|---|---|---|
| `ka_convergence` | all 660 rows planet=Jupiter (the fixed bug) | HALT — single value where dāśā diversity expected |
| `ph_muhurta` | only 1 unique row (all travel/Mercury/0.3/mediocre) | HALT — no differentiation by undertaking/time |
| `ph_pratikara` | all reviewed rows Jupiter/low/light (downstream of the Jupiter bug) | HALT — single afflicting graha |
| `ph_sodhana` | uniformly confidence_inflation/0.652 | FLAG — suspicious uniformity |
| `bo_bimba` | all graha nodes strength=0.506, null centrality | FLAG — identical strengths + null metric |
| `bo_karanajala` | valence + affected_domains NULL across all 360 edges | FLAG — unpopulated annotation layer |
| `ka_vighnakara` | 2 unique records repeated | FLAG — near-degenerate |

**Action:** ELEVATE the degenerate-distribution guard from an L5-only seal gate to a **recommended
general data-build hygiene check** for every layer's writers (it would have caught at least 4 of these at
build time). Already saved as a reusable lesson ([[feedback-degenerate-distribution-guard]]). For L5
specifically, the guard applies to: planet/graha attribution, manifestation channel, signal-family,
domain, confidence tier — any column where diversity is expected.

## §4 — FLAGGED: upstream maturity L5's overlay quality depends on

L5 reads from L2/L3/L4; some of that substrate is still maturing, which bounds L5's near-term overlay
quality (not a blocker, but a known dependency):
- **`bo_sangati` CDLM** has a domain-vocabulary issue being fixed; **`bo_karanajala`** has null
  valence/affected_domains across all edges; **`bo_bimba`** graph centrality is unpopulated. → L5's
  signal-level overlays (keyed to `bodha_msr_signals`) are fine, but cross-domain (CDLM) and causal-graph
  inputs are partial. L5 should degrade gracefully where these are null (the §5-S5 graceful-degradation
  ladder covers this).
- **L3 `kala_*` mid-rebuild** (convergence fix in flight): `ka_kalasutra`/`ka_kala_darshana`/
  `ka_jivana_parva` rows are unpopulated/null pending the ka_sangam rebuild. → L5 must not compute against
  the pre-fix L3 state; the P0 blocker (ph_pratikara rebuild) + a fresh L3/L4 build precede L5 anyway.
- **`ga_yoga` low fire count** (1 yoga) + **`ka_jivana_parva` pre-birth start years** — open upstream
  questions noted in the map; L5 inherits whatever L1/L3 finalize. Not L5's to fix; L5 references them.

## §5 — NET

The live instrument map **validates the L5 design end-to-end**: the input contract is real and matches,
the discipline (staged, honest-ceiling, immutable-chart) is already the house style, and the
degenerate-distribution guard is proven to address a systemic need. The only new actions are: (1) elevate
the distribution guard to general hygiene; (2) note the upstream-maturity dependencies so L5 degrades
gracefully where CDLM/causal/centrality inputs are still null; (3) confirm L5 builds only against a
post-rebuild, post-L4-seal instrument state (already enforced by P0). No design changes required.

---

*End of L5_DESIGN_VS_LIVE_INSTRUMENT_CROSSCHECK v1.0. The live L0–L4 data confirms the ph_pramana→L5
contract, shows the instrument already shares L5's staged/honest discipline, and proves the
degenerate-distribution guard catches a systemic pattern (≥6 assets show it). L5 design holds; actions are
elevate-the-guard, note-upstream-maturity, and build-only-post-rebuild.*
