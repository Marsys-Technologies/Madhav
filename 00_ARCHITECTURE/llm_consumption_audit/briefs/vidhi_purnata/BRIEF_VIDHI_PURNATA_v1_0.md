---
artifact: BRIEF_VIDHI_PURNATA
type: WAVE BRIEF (planner-completeness fix; precedes and enables UAT-DARPANA)
wave: VIDHI-PŪRṆATĀ — make the Vidhi planner complete + default-deep
version: 1.0
status: DESIGN-COMPLETE — native-commissioned via Cowork 2026-07-23; authored by Fable 5.
  Executes as a governed BUILD wave (it changes system code) BEFORE UAT-DARPANA runs, so the
  UAT tests the fixed planner. Opus for all astrological/judgment work; Sonnet coordinates;
  verifier-gated; FROZEN orchestrator untouched.
governing: CLAUDE.md (§N build standards) · GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md ·
  STATIC_VIDHI_AUDIT_v1_0.md (the finding base — F1–F9, R1–R6) · UAT_DARPANA_DESIGN_v1_0.md
  (the exhaustive test that runs AFTER this wave closes)
source_of_findings: 00_ARCHITECTURE/llm_consumption_audit/briefs/uat_darpana/STATIC_VIDHI_AUDIT_v1_0.md
---

# VIDHI-PŪRṆATĀ — planner completeness + default-depth

## §0 — Goal + native directive + product identity (final, 2026-07-23)

**Product identity (native, verbatim intent — governs every design choice in this wave):** this
instrument's primary purpose is insights BEYOND an acharya and beyond any existing astrological
AI system — cross-varga cancellations, firing chains, temporal intensity, personal retrodiction,
standing falsifiable predictions, all converging on one question. That depth-carved insight is
the ONLY differentiation and value proposition. Direct narrow questions are catered to, but the
system is built for depth and breadth first.

**Depth doctrine (BINDING; supersedes any weaker phrasing in P-1):** DEEPDIVE IS THE DEFAULT
STATE OF THE INSTRUMENT. The full floor + machine band + intervention layer + elevation bands
compile for every question EXCEPT a question that is unmistakably a pointed single-fact lookup
(RS-4 retrieval class: "where is my Moon?", "what dasha am I in?"). The exception must be
EARNED by the question's own narrowness — ambiguity, generality, or unclassifiability all break
toward MORE depth, never less (an unclassifiable question gets the E-0 foundational floor, the
deepest plan of all). A trimmed plan for a non-pointed question is a gate-failing defect.

Make the Vidhi planner "perfectly working" before the exhaustive UAT: (1) every life-domain a
user asks about is REACHABLE and gets an acharya-grade floor; (2) depth per the doctrine above.
Close STATIC_VIDHI_AUDIT findings F1–F7 + F9; honor F8 honestly (ask for the right aspects even
where data is DARK — never fake).

**The honesty line (binding).** Fixing the PLANNER (which aspects it asks for) is distinct from
fixing the DATA (whether a live tool serves that aspect). This wave makes the planner ask for
everything an acharya would. Where no live tool backs an aspect, the new floor item is added AND
marked `known_gap: <CR>` — surfaced in the completeness receipt's `dark` bucket, never presented
as served. Data-layer gaps this exposes become a named backlog, not a blocker for this wave.

## §1 — The registry three-copy trap (READ FIRST)

`platform-mcp/src/resources/vidhi/registry_data.ts` is a GENERATED mirror. Do NOT hand-edit it.
- **Canonical source:** `platform/src/lib/vidhi/registry_data.ts` — edit HERE.
- **Regenerate mirror:** `npm run codegen:vidhi` (in platform/); `npm run codegen:vidhi:check` in CI.
- **Third copy:** the migration-440 DB seed — update in lockstep (new migration, surgical).
- Parity test: `platform-mcp/src/__tests__/vidhi_codegen_parity.test.ts` must stay green.
Also in scope, all three where they carry the taxonomy: the `IntentClass` enum (`types.ts`),
`intent_classify` (DR-8 authoritative classifier rules), and `scope_resolver.ts` (fallback
keywords). A new intent is not "reachable" until the enum + BOTH resolution paths know it.

## §2 — Lanes

### P-0 — Discovery + reconciliation (do first; no floor edits yet)
- Map all three registry copies + the codegen path; confirm the edit→regenerate→seed flow live.
- Read `intent_classify` (authoritative path) — audit its rules for the SAME taxonomy gaps the
  fallback has (F1). The enum bounds both paths; both must gain the new classes.
- For EVERY new aspect this wave wants to plan (spirituality set, Upapada Lagna, Dārā-kāraka,
  2nd/8th bhāva reads, āyurdāya/8th/Saturn/Moon for health, AmK for career), PROBE the live MCP:
  is there a tool + real data (→ live primitive) or not (→ add primitive but `known_gap`-flag,
  file the data-gap CR)? Produce a `data_backed` vs `data_gap` table — this is the wave's
  honesty ledger.
- Reconcile F9: is `dhana_yoga_scan`'s CR-56 gap actually closed (memory says yoga engine
  resolved post-D-1.6)? Correct the tag to match live truth.

### P-1 — Depth-default inversion (doctrine ruling; native-directed)
Replace keyword-gated depth (default `structure`, upgrade on magic word) with **intent-driven
default depth**: any `*_deepdive` / `panoramic_breadth` intent defaults to `deepdive` (full
floor + machine band); `structure_read` → `structure`; `retrieval_only` → `retrieval`. A
question only drops below deepdive when it is genuinely a single-fact lookup (RS-4 retrieval
class). Same principle for `intervention`: a domain deepdive INCLUDES the remedy/intervention
layer by default (it is part of a complete reading), not gated behind the words
"remedy/mantra". Record as a doctrine note (DR-class if the conductor deems it) so the
default-deep policy is law, not an implementation detail. Effect: closes F5 + F6; the naive
"tell me about my money" now compiles the full wealth floor incl. timing + remedy + calibration.

### P-2 — Taxonomy completeness (F1)
Add `spirituality_deepdive` [MANDATORY] to the enum + `intent_classify` rules + fallback
keywords, with an acharya floor: 9th (dharma) + lord, 12th (mokṣa) + lord, Ketu, Jupiter-as-
guru kāraka, ātmakāraka, karakāṃśa mokṣa-trikoṇa (from-karakāṃśa 12th/4th), Jaimini spiritual
yogas, D20 (vimśāṃśa) if data-backed, relevant nakshatra/pada. Add `education_deepdive` +
`progeny_deepdive` [CANDIDATE — add if P-0 confirms data support and the native wants full
coverage] (5th/Mercury/Jupiter/D24; 5th/Jupiter/putra-kāraka/D7). Every new class ships with a
worked floor, not a stub.

### P-3 — Floor completeness for existing domains (F2/F3/F4/F7)
- **Marriage:** add the timing spine (`taranga_curve` domain=marriage + `dasha_spine_lord_
  capability` in machine band) [F2]; add Jaimini spouse tools — a Upapada Lagna primitive
  (UL + 2nd-from-UL) and a Dārā-kāraka invocation of `chara_karaka_read`; add 2nd (kuṭumba) and
  8th (māṅgalya/longevity of union) bhāva reads [F3].
- **Health:** add 8th (āyuṣ) bhāva, Saturn (chronic/longevity kāraka), Moon (mind), and an
  āyurdāya primitive wrapping the live `ganita_ayurdaya_get` tool [F4].
- **Career:** add AmK (`chara_karaka_read` mode) [F7].
Each new floor item: `data_backed` → live route; `data_gap` → added + `known_gap`-flagged.

### P-4 — Parity + tests
Regenerate the mirror; update the migration-440-equivalent DB seed via a new surgical
migration; `codegen:vidhi:check` + `vidhi_codegen_parity.test.ts` + the full vidhi test suite
green; compiler determinism (hash-equality) preserved.

## §3 — Gate (Opus verifier, fresh context; no green on the primary runner alone)
- Re-run the STATIC_VIDHI_AUDIT checklist programmatically: F1–F7 CLOSED (each domain floor now
  covers its acharya checklist) or explicitly deferred with a data-gap CR + reason; F9 reconciled.
- Depth-default inversion verified: a keyword-free naive domain question now compiles the full
  deepdive floor (assert on `wealth_deepdive` + `spirituality_deepdive`).
- Every new floor item resolves to a live tool OR carries a truthful `known_gap`; the honesty
  ledger (P-0) is committed — zero items silently pretend-live.
- Determinism + three-copy parity green; FROZEN orchestrator untouched; §N idempotency/no-fab
  standards held. NO fabricated data to fill a floor.
- Gate does NOT run the dynamic UAT — that is the separate UAT-DARPANA initiative, which opens
  only after this wave closes and the static audit re-confirms closure.

## §4 — Sequence out of this wave
VIDHI-PŪRṆATĀ closes → re-run STATIC_VIDHI_AUDIT_v1_0 (confirm F1–F7 closed; publish v1.1 with
the closure deltas + the surviving data-gap backlog) → THEN launch UAT-DARPANA against the fixed
planner. The UAT's §6.2 Vidhi track will now measure a completed planner and confirm the fix
held under real questions.

## §A — Data-support ledger + concrete floor designs (Fable live-probe, 2026-07-23)

Fable probed chart 482012f1 live during design. Result: the new domains are almost entirely
DATA-BACKED — the audit gaps were planner-coverage, not data. Evidence below; the executor
re-verifies at P-0 but starts from this, not from zero.

**Data-support ledger (probed live):**

| Aspect needed | Live source (confirmed) | Status |
|---|---|---|
| Āyurdāya / longevity (Piṇḍa/Aṃśa/Naisarga, maraka grahas) | `ganita_ayurdaya_get` | ✅ data-backed |
| Vaidya medical (per-graha organ/dosha watch) | `ganita_medical_get` | ✅ data-backed |
| Dārā-kāraka, Amātyakāraka, Putra-kāraka (all chara karakas) | `ganita_condition_get facet=karakas` | ✅ data-backed |
| Upapada Lagna (A12) + bhava-arudha UPA | `ganita_condition_get facet=karakas` (arudha_pada.A12 / bhava_arudha.UPA) | ✅ data-backed (raw); RANKING is CR-61 |
| D20 Vimśāṃśa (spirituality) + `spirituality_karya` marker + deities | `ganita_chart_facts_get divisional_chart=D20` | ✅ data-backed |
| D24 Chaturviṃśāṃśa (education) + `education_karya` marker | `ganita_chart_facts_get divisional_chart=D24` | ✅ data-backed |
| D7 Saptāṃśa (progeny) | `ganita_chart_facts_get divisional_chart=D7` | ✅ data-backed (verify karya-label: D7 row read `spouse_karya` — likely a label quirk; confirm at P-0) |
| 2nd-from-UL, from-karakāṃśa 12th (moksha), beeja/kshetra sphuta | derived from the above (computed-from, not a new tool) | ⚠ derivation — compute in floor logic; flag if a dedicated fact is absent |

**New intent classes (all data-backed; add to enum + intent_classify + fallback keywords):**

- **`spirituality_deepdive`** floor: bhava_condition H9 + H12; bhavesha H9 + H12; karaka_condition
  Jupiter (guru) + Ketu (mokṣa-kāraka); chara_karaka_read AK (ātmakāraka); karakamsa_read
  (+ from-karakāṃśa 12th); divisional_facts D20; varga_ratification [D1,D9,D20]; nakshatra_semantics
  (Ketu/Jupiter); dhana_yoga_scan family=`spiritual` (pravrajyā/sannyāsa yogas — flag if the
  family key is absent → known_gap, do not fake); mechanism_read; sudarshana_agreement_check;
  [machine] dasha_spine_lord_capability + intervention_synthesis.
- **`education_deepdive`** floor: bhava_condition H4 + H5 + H9; bhavesha H4 + H5; karaka_condition
  Mercury (buddhi) + Jupiter (jñāna); divisional_facts D24; varga_ratification [D1,D9,D24];
  nakshatra_semantics (Mercury); dignity_scan; sensitive_degree_check; [machine]
  dasha_spine_lord_capability + taranga_curve domain=education (flag phala-anchor gap if empty).
- **`progeny_deepdive`** floor: bhava_condition H5 (+ H9 as 5th-from-5th derivation); bhavesha H5;
  karaka_condition Jupiter (putra-kāraka) + chara_karaka_read PuK; divisional_facts D7;
  varga_ratification [D1,D9,D7]; dosha_scan; [machine] dasha_spine_lord_capability + remedy_scan.

**Expanded existing floors:**

- **marriage_deepdive** +: taranga_curve domain=marriage + dasha_spine_lord_capability [F2 timing
  spine]; chara_karaka_read DK [F3]; arudha_read scoped to UPA + a 2nd-from-UL derivation [F3 UL];
  bhava_condition H2 (kuṭumba) + H8 (māṅgalya) [F3].
- **health_deepdive** +: NEW `ayurdaya_read` primitive; NEW `medical_read` primitive;
  bhava_condition H8 (āyuṣ); karaka_condition Saturn (chronic/longevity) [all F4].
- **career_deepdive** +: chara_karaka_read AmK [F7].

**New primitives to define (all map to a confirmed live tool):**
`ayurdaya_read` → `ganita_ayurdaya_get`; `medical_read` → `ganita_medical_get`; UL via
`arudha_read` scoped to UPA (routes to `ganita_condition_get facet=karakas`); DK/PuK/AmK via the
existing `chara_karaka_read` with the karaka param. Only genuinely-absent aspects (e.g. a
`spiritual` yoga family, education phala anchors, beeja/kshetra sphuta if unstored) get added AND
`known_gap`-flagged per §0's honesty line — never faked.

**One caution the probe surfaced:** the D7 `varga_karya_bhava` row read `spouse_karya` — D7 is
classically progeny (Saptāṃśa). Confirm at P-0 whether this is a label quirk or a mapping bug
before keying the progeny floor off it (use H5/Jupiter/PuK as the spine regardless; D7 is
corroboration).

## §B — Elevation lanes (native + Fable brainstorm, 2026-07-23 — BINDING; the "beyond acharya" layer)

Reviewed by Fable at native direction. These seven elevations are part of the wave, executed as
lane **P-3b** (after P-3, before P-4). Priority order below; if the wave must split, E-0/E-1/E-5
ship first and the rest carry to an immediate follow-on — but none are dropped silently.

- **E-0 — Pūrṇa-Ādhāra foundational floor (NATIVE-ORIGINATED; the resilience principle).**
  *"When the planner does not recognize the territory, it lays the entire foundation on the
  table and lets the intelligence judge."* Replace the thin 6-item `general_synthesis` floor
  with a comprehensive whole-chart foundation: positions+degrees, all 12 bhava conditions +
  lords, dignity/shadbala/avasthas, yoga FIRINGS (authoritative surface), full dasha spine,
  core vargas (D9 + D2/D10/D7/D20 digest level), all chara karakas + arudhas incl. UL,
  sensitive degrees, aspects/parivartana/argala structure, contradiction scan, current
  activation windows (E-1), LEL retrodiction. **Budget discipline (§N.6, binding):** served
  LAYERED — digest/rollup/verdict-bearing rows first (`bodha_chart_digest_get` + rollups),
  drill pointers to full detail, `hardFloor` on the densest layer; foundation means everything
  PRESENT and prioritized, never an undifferentiated dump. Also expose the same set as a
  `foundation` band any intent can request. Gate assertion: an unclassifiable question now
  compiles ≥ the foundational floor; AND domain questions still route to their dedicated
  floors (the net is a safety net, not the default path).
- **E-1 — Wire the D-5 temporal engine into the planner (highest-value gap).** The registry
  predates Gochara-Chitra: `gochara_activation_get` / `gochara_forecast_get` /
  `gochara_election_avoidance_get` have NO Vidhi primitives. Add primitives
  `gochara_activation_read` / `gochara_forecast_read` / `election_read`; put activation in
  EVERY deepdive's machine band (horizon=current), forecast where horizon=multi_year,
  election_read when the question is an undertaking/timing ask. DR-16 gating and
  `structural_prior` honesty ride along unchanged.
- **E-2 — Prospective-ledger surface in every deepdive.** New primitive `standing_predictions_
  read` (route: the ledger query face; P-0 confirms the exact tool) serving the OPEN filed
  predictions for the question's domain — every reading becomes falsifier-bearing by default.
  Confirmation/disclosure only; never a calibration write.
- **E-3 — Anusaraṇa (chart-adaptive) expansion rules.** Deterministic, auditable follow-rules
  compiled AFTER the static floor resolves, bounded to ONE hop: (a) follow each floor bhavesha
  to its occupied house → add that bhava_condition; (b) follow the domain karaka's dispositor
  → add its condition; (c) if a floor item's tool response carries a firing/contradiction/
  drill flag, the PLAN pre-authorizes that drill target (executor-side expansion, listed in
  the plan's `adaptive_expansions` section). Pure function of chart facts + registry —
  determinism test extends to cover it. Expansion depth hard-capped (one hop, no transitive
  closure) so §N.6 budgets survive.
- **E-4 — Multi-domain composition.** `scope_tuple.domains[]` is already plural: intent_classify
  emits ALL matched domains (fallback matcher collects all hits, not first-hit-wins); the
  compiler UNIONS the matched intents' floors (dedup on primitive_id+args, orders stable).
  Gate: a two-domain question ("does my career support my wealth?") compiles the union.
- **E-5 — Cross-domain awareness everywhere (B.11).** `contradiction_scan` added to every
  deepdive's machine band, not just panoramic/general.
- **E-6 — Personal retrodiction everywhere.** `lel_retrodiction` added to every domain
  deepdive's machine band (domain-scoped), confirmation-only framing preserved.

- **E-7 — The insight band (the differentiation made structural).** Every deepdive plan ENDS
  with an explicit insight-carving band directing the answerer beyond fact-gathering to the
  non-obvious: `contradiction_scan` (discoveries/CDLM), a `tail_divergence_read` primitive
  (route: `synth_tail_divergence_get` — rarity/where-this-chart-diverges-from-the-typical),
  `mechanism_read` (chain/circuit motifs), `statistical_context`, and the plan's own
  `llm_extension_note` upgraded to an INSIGHT MANDATE: "the floor is evidence; the deliverable
  is the insight an acharya could not reach — name the confluences, the contradictions and
  their resolution, the rarities, and what only this convergence of surfaces reveals." This
  band is `hardFloor`-protected in budget terms (§N.6): the insight surfaces are never the
  rows a trim sacrifices first.

**Two lines held (Fable review):** no unbounded expansion (E-3's one-hop cap is part of the
gate); and the foundational floor never becomes an excuse for lazy classification (E-0's dual
gate assertion). Honesty line §0 applies to every E-lane: an elevation aspect with no live
tool is added + `known_gap`-flagged, never faked.

## §5 — Scope guards
may_touch: `platform/src/lib/vidhi/**` (canonical registry + classifier), `platform-mcp/src/
resources/vidhi/**` (regenerated, not hand-edited), `platform-mcp/src/tools/*intent*` /
`*plan*` (classifier/plan tools), `platform/migrations/<new>_vidhi_*.sql` (surgical seed
update), the two audit/design docs (status/closure notes). must_not_touch: the FROZEN
orchestrator/WriterBase, L1–L5 writers + data tables, calibration tables, sealed split, any
non-Vidhi serving tool. No fabricated computation to populate a floor (§N B.10).
