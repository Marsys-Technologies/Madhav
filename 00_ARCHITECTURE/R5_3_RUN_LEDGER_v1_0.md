---
canonical_id: R5_3_RUN_LEDGER
version: 1.0
status: LIVE
created: 2026-07-10
author: Claude Code (per-lane implementers, one worktree PR per lane)
program: R5.3 content-depth iteration, grader-restoration-GATED (R5.2 A5 graders were
  INCONCLUSIVE). 16 rubric items with Pratinidhi-R rulings, executed as independent
  per-lane worktree PRs per CLAUDECODE_BRIEF_R5_3_CONTENT_DEPTH_v1_0.md. Governing law:
  R5_3_CONTENT_SPECS_v1_0.md's 16 rubric items + Pratinidhi-R per-lane rulings. Battery
  R5_ANSWER_BATTERY_v1_0.md and llm_grader.ts rubric prompt text remain READ-ONLY.
---

# R5.3 RUN LEDGER — Content-Depth Iteration

Append-only. Each lane's implementer appends its own entry; this document never edits prior entries.

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

---

## Lane: Entity portrait (graha_portrait v3 envelope) — CLOSED (implementation)

**Scope:** Q2-N-1, Q2-A-1, Q9-A-1 — all three route through `graha_portrait`'s v3 envelope.
Pratinidhi-R ruling (root_cause_applies: true) confirmed live against prod: `verdict` was a
completeness receipt (`completeness`, `sections_populated/requested`) with zero prose fields;
`content` rows carry `citation_ref` (internal MCP-lineage provenance, e.g.
`graha_dignity_per_varga.D1_SAT.dignity_state@chart=...:ay=...:eng=pyjhora/1.0.0` — never a
classical citation). No narration existed anywhere in the v3 schema `buildRetrievalEnvelope` emits.

**Root cause:** narration was never in scope of R5.1 C1's budget-fitting fix (matches that
finding's own framing). The MCP layer (`registry_bridge.ts`) builds `verdict`/`grounding` from
`inner` — the capability's pre-trim output — entirely mechanically (completeness counts only).

**Implementation (this session):** `platform-mcp/src/tools/registry_bridge.ts`, entirely inside
`registerRegistryBridgeTools`'s `graha_portrait` tool registration:

1. Added `buildGrahaPortraitNarration(...)` — assembles `verdict.narration` prose from sections
   `graha_portrait`'s capability handler ALREADY fetches (`inner`, pre-trim): functional
   role/lordship (classical whole-sign house-lordship table + the already-computed
   `functional_nature` fact, not a new derivation), D1×D9 dignity promise-vs-delivery tension
   (with an explicit dusthana-house counterweight clause for any exalted/own graha sitting in
   6/8/12), an honest neecha-bhanga check (dispositor looked up via the classical sign-lord table,
   dispositor's OWN dignity read from `cgm_neighborhood.nodes[].dignity_state` if present in the
   already-fetched depth-1 neighborhood, honestly caveated as partial-coverage if not), shadbala
   grade (rupas vs the classical required-rupas threshold table — same constants
   `ga_strength_writer.py` embeds), up to 2 avasthas, yoga/parivartana or an honest JL-004
   empty-with-reason restatement, current/next Mahadasha periods (with age-in-years ONLY for the
   documented canonical native chart_id `482012f1-...`, since birth date is not otherwise available
   to this call for arbitrary charts — never fabricated for other charts), CGM neighborhood top
   edges, and two standing honesty disclosures (single-tradition/JL-004 caveat; entity-scope vs
   bhava-level-claim honesty, paired with a new `judgment_query` drill_pointer).
2. `grounding.fact_ids` expanded (per the ruling's structural finding #1) to include every
   fact_id the narration actually cites — previously built ONLY from `position.rows`.
3. `citation_ref` stripped from every row in `inner` (new trim headroom per the ruling's general
   approach) AFTER narration is built from the untouched `inner` — narration reads
   `fact_id`/`fact_value_text`/`fact_value_jsonb`, never `citation_ref`, so this is safe and
   opens budget room for the added prose within the existing 12KB `graha_portrait` ceiling
   (`response_budget.ts`'s `MCP_RESPONSE_BUDGET_KB.graha_portrait` — unchanged, not raised).

**Not touched:** `platform/src/lib/retrieval/registry/layers/L2_bodha/graha_portrait.ts` (the
capability layer) — all narration assembly happens at the MCP envelope layer per the ruling's
stated preference, since `registry_bridge.ts` already owns the v3-population block and
`portraitSections` trim list. No new SQL, no new capability calls beyond the pre-existing
`get_chart_header` fetch (already made in this handler; only its position in the function was
moved earlier so `lagna_sign` is available before narration is built). No orchestrator/writer/
chart-data/salience/battery/grader touch.

**Verification:** `platform-mcp` `npm run typecheck` and `npm run build` (`tsc`) both pass clean
with no errors. `platform/` was not touched — its own lint/build were not re-run (no diff to
verify there).

**Honest gaps this implementation does NOT close:**
- No live re-grade against the restored grader was run by this implementer — that is the
  separate verifier's job per the dispatching instructions.
- The neecha-bhanga check's dispositor-dignity lookup depends on the dispositor graha actually
  appearing in the depth-1 `cgm_neighborhood` returned for THIS graha; when it doesn't, the
  narration says so honestly rather than asserting an unsupported "not formed" verdict (per the
  ruling's explicit instruction) — this is a real, disclosed coverage limit, not a bug.
- Age-in-years on dasha periods is native-chart-only (documented birth date). Abhinandan's chart
  (`1c826d5a-...`, used by Q2-A-1/Q9-A-1) gets plain dates without ages — birth date for that
  chart was not available to this call without adding new plumbing, which was out of scope
  (no new computation / no new stored-data changes).

PR: see branch `feature/r5-3-b2-entity-portrait`.
