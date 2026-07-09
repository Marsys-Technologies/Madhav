---
canonical_id: R5_3_RUN_LEDGER
version: 1.0
status: LIVE
created: 2026-07-10
author: Claude Code (lane implementer, CLAUDECODE_BRIEF_R5_3_CONTENT_DEPTH_v1_0.md)
program: R5.3 content-depth iteration, grader-restoration-GATED (R5.2 A5 graders were
  INCONCLUSIVE). 16 rubric items with Pratinidhi-R rulings, executed as independent
  per-lane worktree PRs. This ledger is append-only across lanes.
---

# R5.3 RUN LEDGER — Content-Depth Iteration

Append-only. Every lane's implementer appends its own entry; no entry edits a prior one.

---

## Lane: Verification/derivation (ganita_structural_get dosha_fires, ganita_yogas_get) — Q9-N-1 / Q9-N-3

**Ruling basis:** Pratinidhi-R ruling for this lane (root_cause_applies=true, with the
qualifier that ganita_structural_get has NO v3 envelope at all for any facet — legacy
format only — and a second, independent, higher-priority wiring bug where `facet` was
silently dropped by `get_yoga_dosha.ts`).

### What shipped

1. **`platform/src/lib/retrieval/registry/layers/L1_ganita/get_yoga_dosha.ts`**
   - `facet` is no longer a no-op: a `FACET_TO_TYPE` map now scopes `facet=yoga_fires` /
     `facet=dosha_fires` to their respective category subsets (previously every facet
     routed through this URI returned the identical unfiltered ~530-row union of all 6
     yoga/dosha categories).
   - When `facet=dosha_fires`, the handler now additionally SELECTs the already-computed
     `kala_sarpa_per_varga` fact_category (fact_key=`ks_detection`), scoped to the same
     chart_id/ayanamsha filter, and returns it as `kala_sarpa_per_varga: { natal,
     divisional_fired }`. This is the genuinely per-chart-computed Rahu/Ketu detection —
     the pre-existing `dosha_label` catalog row for "Kala Sarpa Dosha" cites an unrelated
     generic placeholder fact (confirmed live: chart `482012f1-…`, catalog row's
     `constituent_facts_array` resolves to Sun's sign, not Rahu/Ketu). Zero new
     computation — this SELECTs an L1 fact_category that already exists at rest.

2. **`platform-mcp/src/tools/register_p1_ganita.ts`**
   - `ganita_structural_get` gained a `response_format` param (`legacy` default / `v3`
     opt-in), mirroring `ganita_yogas_get`'s existing pattern. Previously this tool had
     no v3 envelope branch at all for any facet.
   - `v3` + `facet=dosha_fires` now states an explicit Kala Sarpa Dosha natal verdict
     (formed/not-formed, Rahu/Ketu house axis, classical all-seven-grahas-confined
     mechanism, and an explicit reconciliation note distinguishing the verified
     `kala_sarpa_per_varga` computation from the misleading catalog row) plus a
     divisional-chart note (D2/D4/D6/… `fires:true` rows, explicitly labeled divisional
     not natal).
   - `ganita_yogas_get`'s existing v3 `verdict` gained a `pancha_mahapurusha` block:
     per-yoga formed/not-formed sentences for all 5 Pancha Mahapurusha yogas (Ruchaka/
     Bhadra/Hamsa/Malavya/Sasa), built from rows this response already fetches
     (`yoga_label` presence = fired, per JL-004) plus a bounded, best-effort enrichment
     fetch of `graha_position` sign/house_d1 for the 5 karaka planets (already-computed
     L1 fact_category, fetched via the existing `get_positions` capability — zero new
     computation) to state the specific failed sign/kendra condition for the not-formed
     yogas. Live-verified against chart `482012f1-…`: only Sasa (Saturn, exalted in
     Libra, house 7 = kendra) is formed; Ruchaka/Bhadra/Malavya fail on the sign leg
     (Mars/Mercury/Venus in Libra/Capricorn/Sagittarius respectively — none own or
     exalted); Hamsa fails on the kendra leg (Jupiter in Sagittarius = own sign, but
     house 9 is a trikona, not a kendra).

### Verified against live DB (chart `482012f1-710e-4a25-994a-93821f5871aa`)
- `kala_sarpa_per_varga` D1 row: `fact_id=025b69663e8a93bc`, `fires=false, rahu_house=2,
  ketu_house=8` (lahiri_chitrapaksha).
- `dosha_label` "Kala Sarpa Dosha" catalog row: `constituent_facts_array=["e2b47b2c6d457725"]`
  → resolves to `graha_position.SUN.sign=Capricorn` (unrelated placeholder), confirming
  the ruling's finding (B) verbatim.
- `yoga_label` rows across all 5 ayanamshas: only "Sasa Yoga" present; Ruchaka/Bhadra/
  Hamsa/Malavya absent — confirming the ruling's finding (D).

### Not touched (out of scope per ruling)
- `parivartana` / `graha_yuddha` facets remain mis-routed through `get_yoga_dosha.ts`
  (their real per-varga/graha-yuddha data lives in `get_dispositors.ts` /
  `get_graha_yuddha.ts`) — this is a pre-existing routing mismatch, not addressed by
  this lane's ruling, and is flagged here for a future lane rather than fixed silently.

### Checks run
- `platform`: `npm run lint` (scoped to touched files — clean, pre-existing warnings
  only) + full `npm run build` (TypeScript compiles clean in 9.4s; the build's later
  static-page prerender failure on `/login` is a pre-existing local-env issue — missing
  Firebase/CloudSQL credentials — unrelated to this change).
- `platform-mcp`: `npm run typecheck` — clean.

### Must-not-touch boundaries
None hit. No orchestrator/writer/chart-data/frozen-constant/LEL/battery/grader edits.
