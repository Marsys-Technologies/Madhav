---
artifact: STATIC_VIDHI_AUDIT
type: STATIC (pre-run) AUDIT of the Vidhi planning layer — reads code, runs nothing
initiative: UAT-DARPANA (pre-flight; feeds the battery and the §6.2 Vidhi track)
version: 1.0
status: COMPLETE — Fable 5 (Cowork), 2026-07-23, read-only static pass over the vendored
  Vidhi registry + compiler + scope resolver. Findings are candidates for native disposition;
  this audit ships ZERO code changes (UAT-DARPANA §10 scope).
sources_read:
  - platform-mcp/src/resources/vidhi/registry_data.ts  (VIDHI_PRIMITIVES, VIDHI_INTENT_FLOORS)
  - platform-mcp/src/resources/vidhi/compiler.ts        (compileContract, bandsForDepth)
  - platform-mcp/src/resources/vidhi/scope_resolver.ts  (resolveScopeTuple + keyword fallback)
  - platform-mcp/src/prompts/vidhi_plan.ts              (render scaffold)
---

# STATIC VIDHI AUDIT — planning-layer coverage, before the dynamic UAT

## §0 — What Vidhi actually is (corrects the "prompt" model)

Vidhi is **not** an LLM that reads a prompt to invent a retrieval plan. It is a **deterministic
compiler** (`compileContract`) over a **vendored capability registry** (`registry_data.ts`).
`vidhi_plan.ts` is only a render scaffold around the compiled output. Therefore planning
quality is fully determined by three static, inspectable artifacts — and can be audited without
running anything:

1. **Intent taxonomy** — a FIXED enum of 8 `IntentClass` values. Both the authoritative
   `intent_classify` (DR-8) and the fallback resolver can only ever emit one of these 8. A life
   domain absent from this enum is UNREACHABLE by any path.
2. **Per-intent floor sets** (`VIDHI_INTENT_FLOORS`) — the non-skippable "acharya floor" +
   machine band of retrieval primitives compiled for each intent. This is where "is a bearing
   astrological aspect covered?" is decided.
3. **Scope resolution + band gating** (`scope_resolver.ts` + `bandsForDepth`) — how a question
   becomes (intent, depth, intervention), and how depth/intervention trim the compiled plan.

## §1 — The 8 intent classes and floor sizes (as built)

| Intent | Floor items | Timing primitive? | Remedy primitive? |
|---|---|---|---|
| wealth_deepdive | 26 (flagship) | yes (taranga_curve) | yes (intervention_synthesis) |
| career_deepdive | 20 | yes (taranga_curve) | yes (intervention_synthesis) |
| health_deepdive | 18 | yes (taranga_curve) | yes (remedy_scan) |
| marriage_deepdive | 16 | **NO** | yes (remedy_scan) |
| structure_read | 5 | no (by design) | no |
| panoramic_breadth | 8 | no (spine in machine band) | no |
| retrieval_only | 1 | no (by design) | no |
| general_synthesis | 6 (fallback) | spine in machine band | yes |

## §2 — Findings (severity-ranked, from a senior-acharya coverage lens)

### F1 — TAXONOMY INCOMPLETE: no spirituality / education / progeny deepdive. **[HIGH — native-critical]**
Only four life-domain deepdives exist (wealth, career, health, marriage). There is **no
spirituality/moksha, no education/vidyā, no progeny/children** intent class. Because the intent
enum is fixed at 8, these are unreachable by BOTH the authoritative classifier and the fallback —
a spiritual-life question collapses to `general_synthesis`'s 6 generic items (lagna condition,
shadbala rank, mechanism read, dasha spine, contradiction scan, remedy). For THIS native, whose
spiritual arc is chart-central (LEL #3/#6/#10/#14/#15), a question about his spiritual life would
receive NO 9th (dharma), NO 12th (mokṣa), NO Ketu, NO Jupiter-as-guru, NO ātmakāraka/karakāṃśa
mokṣa-trikoṇa reading, NO Jaimini spiritual yogas. This is the single most consequential planning
gap for him. (Education → 5th/Mercury/Jupiter/D24; progeny → 5th/Jupiter/D7/putra-kāraka —
similarly unreachable, lower native-priority.)

### F2 — MARRIAGE FLOOR HAS NO TIMING SPINE. **[HIGH]**
wealth/career/health floors each carry `taranga_curve` (domain temporal window). The marriage
floor carries **zero temporal primitives** — no taranga_curve, no dasha_window, no
transit_window_scan. "When will I marry / how is this marriage period / is the current window
supportive" — among the highest-frequency marriage questions a user asks — has **no planned
timing surface**. The plan would return structure with no "when."

### F3 — MARRIAGE FLOOR MISSING THE JAIMINI SPOUSE TOOLS + dusthāna axis. **[MEDIUM-HIGH]**
The marriage floor is 7th-/D9-/Venus-centric (bhāva7, bhāveśa7, Venus kāraka, D9, D1/D9
ratification, dosha, karakāṃśa). Absent: **Upapada Lagna (UL) + 2nd-from-UL** (the flagship
Jaimini marriage-sustainability tool — no primitive exists for it at all), **Dārā-kāraka** (the
chāra kāraka for spouse — the `chara_karaka_read` primitive EXISTS but the marriage floor never
invokes it with DK), and the **2nd house** (kuṭumba/family) and **8th house** (māṅgalya/longevity
of the union). A senior acharya reads all of these for marriage; the plan reaches for none.

### F4 — HEALTH FLOOR MISSING LONGEVITY / ĀYURDĀYA + 8th house. **[MEDIUM-HIGH]**
The health floor is 6th-/roga-centric (bhāva6, bhāveśa6, Mars kāraka, D6, dosha, dignity). Absent:
the **8th house (āyuṣ)**, **Saturn** (karaka of chronic disease & longevity), **Moon** (mind/mental
health), and any **āyurdāya/longevity** primitive — despite a live `ganita_ayurdaya_get` tool
existing in the MCP surface with NO Vidhi primitive wrapping it. A health deepdive that cannot
reach the longevity axis is materially incomplete.

### F5 — NAIVE-USER DEPTH TRAP: the machine band is silently stripped. **[MEDIUM — confirmed in compiler]**
`bandsForDepth`: `structure` depth compiles the acharya floor but **NO machine band**; only
`deepdive` compiles both. The fallback resolver sets `depth = 'structure'` UNLESS the question
contains a deep-keyword (`deep|detailed|thorough|full|assessment|deep.?dive`). So a maximally-naive
"tell me about my money" → wealth_deepdive intent but `structure` depth → the ENTIRE machine band
is dropped: `dasha_spine_lord_capability`, `taranga_curve`, `lel_retrodiction`,
`statistical_context`, `intervention_synthesis` (wealth floor orders 22–26). The naive user loses
the whole timing + remedy + calibration layer for lack of a magic word. This bites specifically on
the fallback path (i.e. when `intent_classify` is not consulted first — which is exactly what a
naive answerer might skip). This is the UAT's S1 "maximally naive" query, and the planner is
primed to under-serve it.

### F6 — INTERVENTION TRAP: remedies stripped without a magic word. **[LOW-MEDIUM]**
`intervention=false` strips ALL remedy-category items from both bands. The fallback sets
`intervention=true` only on `remedy|upaya|mantra|yantra|mitigat|remediation`. So "how do I improve
my wealth / what should I do about my health" (no remedy-word) → `intervention_synthesis` /
`remedy_scan` stripped → the plan carries no guidance layer for a guidance question.

### F7 — CAREER FLOOR: Amātyakāraka absent. **[LOW]**
Career reads Sun (naisargika) but not the **AmK chāra kāraka** — the Jaimini profession
significator — even though the wealth floor DOES read a chāra kāraka (AmK). Minor asymmetry; a
Jaimini-minded acharya would want AmK for career specifically.

### F8 — PLAN ≠ DELIVERY: ~11 floor primitives are DARK by construction. **[MEDIUM — caps every floor]**
Even a perfect plan hits self-disclosed known-gap routes. Primitives carrying an OPEN `known_gap`
that nonetheless sit in floors: `dhana_yoga_scan`(CR-56), `taranga_curve`(CR-66),
`lel_retrodiction`(CR-68), `intervention_synthesis`(CR-69), `nakshatra_semantics`(CR-64),
`mechanism_read`(CR-24), `arudha_read`(CR-61), `dosha_scan`(CR-73), `remedy_scan`(CR-67),
`kp_cusp_sublord_read`(CR-30), `special_lagna_read`(CR-16). These cluster in the TEMPORAL,
REMEDY, and RANKING layers. The completeness receipt honestly surfaces them in its `dark` bucket
(good), but delivered coverage is capped below planned coverage regardless of plan quality — and
the cluster names where the data layer, not the planner, is the ceiling.

### F9 — POSSIBLE REGISTER STALENESS. **[LOW — reconcile]**
`dhana_yoga_scan` still carries `known_gap: 'CR-56'` marked OPEN/ELEVATED, though it routes to
`ganita_yoga_firings_get` and the project memory records the yoga-engine gap RESOLVED post-D-1.6
(NBRY/Dhana/Sarasvatī/Budha-Āditya now fire). Either the tag is stale or the memory is optimistic;
reconcile so the `dark`-bucket accounting is truthful.

## §3 — What is GOOD (so the audit is balanced)

The wealth floor is genuinely acharya-grade (26 items: multi-varga D2/D9/D11, Indu/Sree special
lagnas, AmK, dhana-yoga family, per-varga NBRY, karakāṃśa, KP sublords, Sudarśana, bhāvat-bhāvam,
sensitive degrees). Career and health inherit the full §B0.4 mandatory-tag set. The compiler is
pure/deterministic (auditable, reproducible). The completeness-receipt discipline (served/empty/
dark, dark citing its CR) is honest by construction — the system does not hide its gaps. The
`known_gap` self-disclosure on primitives is exactly the transparency the vision demands. The
architecture (fixed floor + LLM band-3 extension) is sound; the gaps are in COVERAGE, not design.

## §4 — How this feeds UAT-DARPANA

1. **Sharpen the battery (Phase 1).** Add deliberately-targeted queries that will expose F1–F6
   dynamically: a spiritual-life question (F1), a "when will/did marriage happen" question (F2),
   a Jaimini-flavored marriage question (F3), a longevity/health-span question (F4), the
   maximally-naive "tell me about my money" with NO deep-word (F5), and a "what should I do
   about X" with no remedy-word (F6). The §6.2 Vidhi track's replay will then confirm each gap
   live and measure whether the Opus answerer's band-3 extension RESCUES it (F5/F6 especially).
2. **Pre-seed the Vidhi gap ledger (§6.2 V3).** F1–F4/F7 are the expected `aspects_missed`
   entries; the dynamic run confirms and quantifies them per query.
3. **Separate planner gaps from data gaps.** F8's DARK cluster tells the Synthesist which weak
   answers to attribute to the data layer (known-empty routes) vs. the planner (missing floor
   items) vs. the answerer (failed band-3 rescue) — the §8.11 cross-read.

## §5 — Candidate remediation (native disposition; NOT executed here)

- **R1 [HIGH]** Add a `spirituality_deepdive` intent class + floor (9th/12th/Ketu/Jupiter-guru/
  ātmakāraka/karakāṃśa mokṣa-trikoṇa/Jaimini spiritual yogas) and its keyword + classifier route.
- **R2 [HIGH]** Add a timing spine to the marriage floor (`taranga_curve` domain=marriage +
  dasha_spine, machine band), matching the other deepdives.
- **R3 [MED-HIGH]** Add Jaimini spouse tools: a UL primitive (+2nd-from-UL) and DK invocation of
  `chara_karaka_read` to the marriage floor; add 2nd/8th bhāva reads.
- **R4 [MED-HIGH]** Add āyurdāya/8th/Saturn/Moon to the health floor; wrap `ganita_ayurdaya_get`
  as a primitive.
- **R5 [MED]** Reconsider the depth/intervention keyword gating (F5/F6) so naïvely-phrased deep
  questions don't silently lose the machine/remedy bands — e.g. default deepdive for *_deepdive
  intents, or infer depth from intent rather than keywords.
- **R6 [LOW]** Add AmK to the career floor; add education/progeny classes if the roadmap wants
  full domain coverage; reconcile F9's stale CR tag.

These are candidates. The UAT will provide the empirical weight (how badly each gap hurts a real
answer) before any becomes a campaign.
