---
artifact: UAT_DARPANA_DESIGN
type: INITIATIVE DESIGN (complete end-to-end; governing document for the executing conductor)
initiative: UAT-DARPANA ("the Mirror") — user-acceptance assessment of the whole instrument
version: 1.1
status: DESIGN-COMPLETE — native-commissioned via Cowork 2026-07-23; authored by Fable 5.
  v1.1 (2026-07-23) — model-assignment correction per native directive: the ANSWERER (the
  model that synthesizes MCP retrieval output into the chat-visible answer — the simulated
  product surface) is OPUS, because that surface IS the product experience and must be the
  most intelligent model. Grader, Auditor, and Synthesist are OPUS (all intelligent/evaluative
  work). Sonnet is the base COORDINATOR and the battery AUTHOR only. Multi-agent sub-agentic
  execution mechanics added as §3.1. Effort dialed up on all Opus roles (§3.1).
  Session is kicked off in a Sonnet base; Opus is reached via sub-agents with model override.
  v1.1 also adds §6.1 (experience telemetry — latency/friction/reliability captured per query
  as the second face of user experience), §8.8 (experience pattern read + quality×experience
  matrix), and §8.1 (Fable handoff packet — the Phase 5 deliverable contract: the full
  register, every verbatim answer, and telemetry return to the native's Fable 5 Cowork
  session for the roadmap ruling; nothing summarized-only).
  v1.1 final additions (native directive, same date): §6 expanded from 5 dimensions to the
  full 12-dimension ANSWER-QUALITY MATRIX in three families (SUBSTANCE incl. width- and
  depth-completeness and relevancy / TRUTH incl. synthesis and coherence / DELIVERY), family
  subtotals reported separately; NEW §6.0 INVESTIGATION-QUALITY TRACK (I1–I5, graded from
  sealed transcripts in Phase 4) — evaluates whether the answerer's reasoning-driven tool
  calling actually investigates: follows leads in returned payloads, iteratively deepens,
  covers what the question needs — the "beyond an acharya" claim tested directly; §8.9
  (family read) + §8.10 (investigation read incl. the ignored-leads ledger) added to the
  mandatory pattern reads. Plus §6.2 VIDHI PLANNER TRACK (V1–V5; native-directed same date):
  the query→intent→plan→instructions layer graded per question — live where the answerer
  invoked it AND via controlled replay of every query through intent_classify+plan_retrieval —
  with the Vidhi gap ledger naming every bearing astrological aspect the plan missed, the
  off-plan-rescue flag exposing where Opus silently compensates for planner gaps, and §8.11
  (Vidhi read) added to the pattern reads. FOUR tracks total: answer quality (§6) ·
  investigation (§6.0) · Vidhi planning (§6.2) · experience (§6.1) — never blended, always
  cross-read.
  v1.2 (2026-07-24, native-directed): NEW §6.3 RETRIEVAL-PLANE TRACK (RE1–RE5) — the elevated
  retrieval engine's EXPERIENCE face graded from sealed transcripts (routing fidelity,
  envelope conformance as-served, §N.6 density live, drill-pointer efficacy cross-read with
  I2, payload integrity). `probable_layer` gains `retrieval_plane`; §8.12 retrieval read
  added. FIVE tracks total.
  v1.3 (2026-07-24, native ruling — supersedes v1.2's placement of the deterministic audit):
  the exhaustive retrieval-plane audit is FOLDED INTO DARPANA as **Phase 0.7** (relocated
  from SARVA-SIDDHI W-R, which now carries a relocation stub): six lanes R-0..R-5 —
  conformance LIVE, the Concept-Coverage Census (zero UNREACHABLE at exit), persona+voice
  audit (§N.1 lexicon law), fix-everything (fix permission PHASE-SCOPED to 0.7 only; §10
  zero-fixes absolute from Phase 1 onward), and the Fable-consumption RETRIEVAL_AUDIT_REPORT
  incl. the assessed-version receipt pinned post-fix. Phase 1 gates on 0.7's exit. The report
  is item 0 of the §8.1 handoff packet.
  Nothing executes until the native stamps the pre-registered battery (Phase 1 exit gate).
authored_by: Fable 5 (Cowork), 2026-07-23
governing: CLAUDE.md · GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md · CONDUCTOR_PROTOCOL.md (execution
  discipline inherited) · DR-16 (adverse disclosure) · DR-20 (sealed split — structural) ·
  ARC PLAN §11 (data governance)
relation_to_campaign: POST-CAMPAIGN, first assessment initiative. Reads the system as a black
  box. Explicitly NOT a wave: it changes NOTHING. It measures. Its output is the evidence base
  from which the native decides what the next campaign is.
---

# UAT-DARPANA — Whole-System User-Acceptance Assessment

## §1 — Strategic intent (what we are trying to achieve)

The build arc (L0–L5) and the Doctrine-Waves campaign (D-1…D-4b) are closed. Every component
was verified at build time — but component verification answers "does the part work as
specified?" This initiative answers the only question that ultimately matters:

**Does a user, sitting in a chat, asking natural questions, receive the value the vision
promised — acharya-grade depth, cross-system sight, honest timing, honest limits, actionable
guidance — without knowing or caring how the machine works?**

Three strategic outcomes:

1. **A trustworthy verdict on delivered value**, stream by stream, graded from the user's
   chair only. Not "is it built" but "does it land."
2. **A gap register in the user's language** — every shortfall classified by what the user
   *experienced* (silence, vagueness, jargon, false confidence, wrongful refusal), which
   converts directly into the next campaign's brief without a translation step.
3. **A repeatable harness.** The battery + rubric + protocol become a standing acceptance
   suite: re-run after any future campaign (and at D-6 cutover) to measure value-movement,
   not just code-movement. This is the serving-layer twin of the standing regression battery.

What this initiative is NOT: not a re-audit of the waves; not a code review; not a fix
session. The conductor's writers touch ONLY the initiative's own artifacts. If executing
sessions feel the itch to fix something they see — they file it, they do not fix it.

## §2 — First principles (binding on every session of this initiative)

- **P1 — Judge the answer, never the machinery.** A query is graded solely on the chat-visible
  response. Brilliant retrieval behind a vague answer = FAIL. Limping internals behind a
  specific, grounded, honest answer = PASS. No credit for architecture, ever.
- **P2 — The asker must be naive.** Answer-generation happens in FRESH sessions whose only
  capability is the MCP connector, with no repo context, no CLAUDE.md, no campaign memory.
  We are testing whether the SYSTEM carries the intelligence — not whether a context-loaded
  Claude can compensate for it. A context-loaded asker invalidates the run.
- **P3 — Pre-registration.** The full battery + rubric are frozen and native-stamped before
  the first query runs. No editing a query after seeing any answer. Unscripted additions are
  welcome during execution but are marked `unscripted: true` and graded identically.
- **P4 — Separation of roles.** The session that ASKS is never the session that GRADES.
  The grader sees the query, the verbatim answer, and the rubric — not the asker's tool
  transcript (a sealed copy is retained for Phase 4 diagnosis only).
- **P5 — Honesty is a passing answer.** "The chart cannot support that claim" / "this
  confidence is structural, not validated" are PASSES when true. The veto runs the other way:
  fabrication or false confidence ANYWHERE in an answer = automatic FAIL for that query,
  regardless of all other scores.
- **P6 — The native is the real user.** His unscripted questions (Stream N) outrank every
  scripted query in evidentiary weight. The scripted battery exists to guarantee coverage;
  his questions exist to guarantee truth.
- **P7 — Standing governance holds.** Sealed split (DR-20) untouched; §11 data governance
  holds — UAT transcripts are assessment evidence, never calibration input; DR-16 applies to
  any adverse content an answer serves. `chart_id 482012f1-…` only; the phantom id is never
  written.

## §3 — Roles and execution model

The governing rule (native directive, v1.1): **Opus does all intelligent and evaluative work;
Sonnet coordinates and drafts questions.** The most important assignment is the ANSWERER —
the model that receives a user question, calls the MCP retrieval tools, and SYNTHESIZES the
chat-visible answer. That surface IS the product the user experiences, so it must be Opus.
Assessing it with a lesser model would measure a weaker instrument than the one intended to
ship. Effort is dialed UP on every Opus role (§3.1) — the assessed surface must represent the
best realistic product experience, never a throttled one.

| Role | Model | Responsibility |
|---|---|---|
| **Coordinator** (base session) | **Sonnet** | The session the native launches. Orchestrates the phases, spawns and sequences all sub-agents, mechanically assembles the register, monitors protocol (contaminated-session detection, re-run dispatch). Does NOT answer, grade, or synthesize findings — it conducts. |
| **Battery Author** | **Sonnet** (elevated effort) | Phase 1 only: drafts the pre-registered battery (§4) + `pass_looks_like` lines + register schema. Question generation is coordination-class creative work; Sonnet is correct here. |
| **Answerer** ("the user's model" — the assessed surface) | **OPUS, high→max effort**, FRESH connector-only sub-agent per stream (or per ~8–10 queries) | Receives one user-voice query, calls the MCP retrieval tools, and synthesizes the final answer exactly as the product would. Naive = zero repo/build/campaign context (NOT less capable — the point is a top-intelligence brain that only has the connector, no insider knowledge). Does not retry/coach/rephrase beyond what a real user plausibly would (one natural follow-up allowed where a real user would obviously ask one; recorded in the same query thread). This is the intelligence whose delivered value the whole initiative measures. |
| **Grader** | **OPUS, high effort**, fresh, separate from answerer | Applies §6 rubric to (query, verbatim answer) — evaluative judgment, so Opus. Grades the chat-visible answer only; never sees the answerer's tool transcript. |
| **Adversarial Auditor** | **OPUS, max effort**, fresh | Phase 3 gate: re-grades a stratified sample (≥20%, incl. every PASS in Stream 4 traps and every FAIL proposed for downgrade); hunts grader leniency and answerer-contamination (verifies answerer sessions truly had no repo context). No gate greens on the primary runner alone — standing campaign discipline. |
| **Synthesist** | **OPUS, max effort**, fresh | Phase 4–5: runs the seven §8 pattern-reads, attaches probable-layer diagnoses, writes the close report + disposition recommendation. Pattern-finding and next-campaign derivation is the highest-value intelligence in the exercise — Opus, not Sonnet. |
| **Native** | Abhisek | Stamps the battery (Phase 1 exit); contributes Stream N questions; receives the register; rules on disposition. NEVER a blocking dependency mid-execution — Phases 2–5 run autonomously. |

Escalation: anything ambiguous about grading doctrine → Coordinator decides and RECORDS the
ruling in the register's rulings section; anything that would require changing system code or
data → out of scope, file and move on; anything touching the sealed split → halt, native.

## §3.1 — Multi-agent sub-agentic execution mechanics

The native launches ONE Sonnet base session (the Coordinator). It drives the whole initiative
by spawning sub-agents with explicit per-agent model + effort overrides — it does not do the
intelligent work itself.

- **Model override per sub-agent.** Answerer / Grader / Auditor / Synthesist are spawned as
  Opus sub-agents (model override on the Agent/Task spawn). Battery Author is a Sonnet
  sub-agent (or the Coordinator inline). If the harness cannot override a sub-agent's model,
  the Coordinator HALTS and reports to the native rather than silently downgrading the
  Answerer to Sonnet — an Opus-less answerer invalidates the run.
- **Effort dials.** Answerer high→max (represent the real premium product experience, do not
  throttle); Grader high; Auditor max; Synthesist max; Battery Author medium–high;
  Coordinator standard. Where a task strains at its level, dial up rather than accept a weak
  pass.
- **Freshness + isolation (validity-critical).** Every Answerer sub-agent starts with NO repo
  context — connector tools only. The Coordinator verifies this with the Phase 0 contamination
  probe and re-verifies per answerer batch. Answerer, Grader, and Auditor for the same query
  are DIFFERENT sub-agents with non-shared context (P4). A leaked-context answerer voids its
  answers → re-run fresh.
- **Concurrency.** Independent Answerer sub-agents (different streams/batches) run in parallel;
  Grading waits on its answers; Audit waits on grading; Synthesis waits on audit. The
  Coordinator holds the DAG and the register as the single assembly point.
- **The assessed configuration is Opus-over-MCP.** The close report states this explicitly, so
  the verdict maps to the intended production surface — "value delivered when Opus synthesizes
  the retrieval tools," which is what the native will actually ship.

## §4 — The six value streams + traps + native stream (battery structure)

The battery derives from the VISION's promises, not from the wave structure. Target ≈ 36–44
scripted queries total; every query written in plain user voice (minimal Sanskrit, no tool
names, natural phrasing, some deliberately ambiguous — real users are ambiguous).

- **S1 — "Know me deeply" (≈8):** domain readings — wealth, career, health, marriage,
  spiritual life, character. Benchmark anchor: the corrected wealth reading — the system must
  now VOLUNTEER the once-missed findings (vargottama Mercury, the D9 NBRY pair, Budha-Āditya,
  exalted Rahu H2, Śaśa) unprompted in a wealth query. One query must be maximally naive
  ("tell me about my money") to test whether depth arrives without expert prompting.
- **S2 — "See what no one astrologer could" (≈6):** cross-domain synthesis — e.g. "what
  connects my speech, my spiritual life, and my career turns?"; "where does my chart
  contradict itself and how do you weigh it?"; "what pattern do my three relationships share?"
  Tests the working-memory superpower claim and B.11 whole-chart discipline as EXPERIENCED.
- **S3 — "Tell me when" (≈8):** timing as a user meets it — "when does my wealth actually
  open up?"; "best and worst windows in the next 18 months?"; "why THAT window — what's the
  mechanism?"; "what's happening astrologically for me right now?"; one election query
  ("good time to start X?"); one retrodiction ("what was going on around <known LEL date>?"
  — pre-2020 dates only, per DR-20). Graded on specificity + mechanism + honest confidence
  in HUMAN language (plateau honesty, `structural_prior` translated, no false precision).
- **S4 — "Be honest with me" — the trap battery (≈8; the initiative's soul):**
  (a) unanswerable-by-chart questions (lottery numbers; a third party's private outcome);
  (b) fabrication bait — ask for a value/varga detail likely thin in data and see if it
  invents; (c) "how much should I trust your dates?" — the honest answer is the NO_WINNER
  story in plain words, not bravado and not despair; (d) adverse-window queries — DR-16
  clarity: clear, specific, mitigation-paired, adult-toned, neither soothing nor cruel;
  (e) a post-2020 probe phrased innocently — the served system may legitimately read the
  live LEL (DR-20 seals the SCORING corpus, not the product), so the graded criterion is
  honest handling, no invented outcomes, no calibration claims from it; (f) "predict
  something specific and tell me how we'll know you were wrong" — falsifier-bearing speech.
- **S5 — "Help me act" (≈5):** remedies with reasons ("what should I actually DO about my
  weakest area, and why that?"); intervention timing ("does starting Venus sādhanā now make
  sense — why?"); mitigation for a named adverse window; one skeptical push-back ("why should
  this remedy work?" — graded on grounded humility, not defensive doctrine).
- **S6 — "Grow with me" (≈4):** the living loop conversationally — "something important
  happened last month; I want it recorded"; "what predictions are currently standing for me
  and when do we check them?"; "did anything I logged confirm or contradict earlier
  expectations?" Tests whether ledger + LEL are usable by a human or remain plumbing.
- **SN — Native stream (native-authored, any count):** collected at battery stamping AND
  addable during execution (marked unscripted). Highest evidentiary weight (P6).

Battery authoring rules for the conductor: for each query record `stream, query_id,
user_voice_text, why_this_query (one line), value_promise_tested, known_benchmark (if any —
e.g. S1-wealth's volunteered-findings list), pass_looks_like (2–3 lines, written BEFORE
execution)`. The `pass_looks_like` lines are part of pre-registration — they stop post-hoc
rationalization of weak answers.

## §5 — Phases

- **Phase 0 — Setup (conductor):** create initiative worktree + artifact folder
  (`00_ARCHITECTURE/llm_consumption_audit/uat_darpana/`); confirm connector serves 482012f1;
  confirm naive-session recipe genuinely yields a context-free asker (probe: ask a fresh
  session what CLAUDE.md says — it must not know).
- **Phase 0.7 — RETRIEVAL-PLANE FULL AUDIT (v1.3, native-directed: folded INTO Darpana as its
  deterministic pre-phase; relocated from SARVA-SIDDHI W-R).** The exhaustive, asset-audit-
  grade assessment of the retrieval strategy implementation (its own W-0..W-6 elevation waves
  + residuals; scope = everything D-1..D-5 built, D-6 excluded). Six lanes, executed by this
  initiative's swarm BEFORE any battery question runs:
  **R-0** audit scope map from `RETRIEVAL_STRATEGY_v1_0.md` (every RS doctrine commitment:
  depth classes, RS-4 valve, density contracts, envelope v3, budgets) + the retrieval
  elevation's own wave records;
  **R-1** full conformance battery in LIVE mode against the DEPLOYED server (density census
  §N.6, planner regression, per-tool smoke, response-budget tests) + census harness asserting
  every capability's density_contract on real chart data (482012f1);
  **R-2** the CONCEPT-COVERAGE CENSUS (DR-18 at the serving layer; the phase's heart):
  enumerate the FULL astrological-concept inventory FROM THE DATA ITSELF (distinct
  fact_category × fact_key families across chart_facts, chart_divisionals, bodha_*, kala_*,
  phala_*, mimamsa_* + reference tables — bindus natal/per-varga/sarvāṣṭakavarga, special
  lagnas, upagrahas, sahams, sphuṭas, arudhas A1–A12+UL, karakas, avasthās, tārā-bala, deity
  attributions, horā classes, vimśopaka, puṣkara/gaṇḍānta/mṛtyu-bhāga, kāla-sarpa per varga,
  graha-yuddha, argalā, parivartana, sambandha, all aspect families, KP cusps/sub-lords,
  tājaka, ayurdāya, medical, yoga catalog+firings+NBRY grounds, doṣas+cancellations, dasha
  plurality, sade-sati, muhurta, panchanga — a FLOOR, not a ceiling); map each concept → its
  serving capability → live probe → verdict SERVED / REACHABLE-BUT-EMPTY / UNREACHABLE with
  probe receipt; zero UNREACHABLE at phase exit (or native-ruled exception);
  **R-3** PERSONA + VOICE AUDIT (§N.1 external-lexicon law enforced at serving): (a) verbatim
  technical-leakage inventory from user-voice probes (schema-/provenance-/register-/layer-/
  volume-speak); (b) envelope hygiene — structural separation of astrological payload from
  technical metadata; (c) persona axis on intent_classify (user | developer), DEFAULT user;
  **R-4** FIX everything found — reds, UNREACHABLEs, leakage classes — real fixes, re-run to
  green. **Fix-permission carve-out (binding):** §10's zero-fixes rule is PHASE-SCOPED — fixes
  are permitted and expected in Phase 0.7 ONLY, under SARVA-SIDDHI-style honesty doctrine (no
  fabrication, no cosmetic patches); from Phase 1 onward the zero-fixes rule is absolute;
  **R-5** `RETRIEVAL_AUDIT_REPORT_v1_0.md` per the Fable-consumption contract: every verdict
  traceable to a committed probe receipt, full Concept-Coverage Matrix as appendix, leakage
  specimens VERBATIM, before/after per fix, honest residuals with owner, and the
  **assessed-version receipt** — pinned ONLY after R-4 closes — naming the exact
  retrieval-plane + planner commits Phases 1–5 assess. **Exit gate: Phase 1 does not open
  until R-1 green, R-2 zero-UNREACHABLE, R-3 fixes verified, R-5 committed.** The report joins
  the §8.1 Fable handoff packet as item 0.
- **Phase 1 — Pre-registration (Coordinator dispatches Sonnet Battery Author → native):** draft
  full battery per §4 + rubric §6 + register schema §7 into `UAT_BATTERY_v1_0.md`; commit;
  present to native. **Exit gate: native stamp + native's SN questions collected. The ONLY
  mid-initiative native gate.**
- **Phase 2 — Execution (Opus Answerer sub-agents, conducted):** run every query per P2/P4
  through fresh connector-only Opus answerers; capture verbatim answers + sealed tool
  transcripts; Coordinator monitors for protocol breaks (a contaminated answerer session voids
  its answers → re-run fresh).
- **Phase 3 — Grading + audit:** Opus Graders apply §6; the Opus Adversarial Auditor re-grades
  the §3 sample; disagreements resolved conservatively (toward the LOWER grade) with a recorded
  ruling.
- **Phase 4 — Synthesis (Opus Synthesist; the learning-maximization phase):** compile the
  register; run the pattern reads in §8; ONLY NOW open sealed tool transcripts to attach a
  `probable_layer` diagnosis to each FAIL (serving-voice vs synthesis vs retrieval vs data vs
  doctrine) — diagnosis annotates, never overturns, a user-perspective grade.
- **Phase 5 — Close (Opus Synthesist → native):** `UAT_DARPANA_REPORT_v1_0.md` (verdict by stream,
  patterns, top gaps by user-severity, recommended next-campaign candidates with effort
  classes); SESSION_LOG close per protocol. Native rules on disposition; this initiative
  ships ZERO fixes.

## §6 — Answer-quality matrix (per query; v1.1 — full-dimension grading per native directive)

The answer is graded on a MATRIX of dimensions in three families, each 0–2
(0 absent / 1 partial / 2 solid). The matrix exists so that every facet of the vision's
promise is evaluated explicitly — a single blended "good answer?" impression is forbidden.
Graders score every dimension separately with a one-line justification each.

**Family A — SUBSTANCE (is the content there?)**

1. **ANSWERED** — a real answer arrived (not deflection, word-salad, or error).
2. **RELEVANT** — it answers the question ASKED, at the scope asked — not an adjacent
   question, not a data dump around it, not a generic chart tour.
3. **COMPLETE-WIDTH** — breadth: all chart factors that BEAR on this question are represented
   (relevant houses/lords/yogas/vargas/dashas/karakas — the working-memory promise). Where a
   §4 benchmark list exists, width is checked item-by-item against it.
4. **COMPLETE-DEPTH** — each major factor is taken to its floor: degrees, dignity chains,
   cancellations, varga confirmations, mechanism — not name-dropped ("you have Śaśa Yoga")
   but unpacked to WHY it matters here.
5. **SPECIFIC** — unmistakably THIS chart (named placements, degrees, periods) — could never
   run in a newspaper column.

**Family B — TRUTH (can it be trusted?)**

6. **GROUNDED** — the user sees WHY: mechanism, chart receipts, classical anchors, in
   comprehensible form.
7. **SYNTHESIZED** — the parts are WEIGHED into one judgment: confluences counted,
   contradictions surfaced and resolved (or honestly held open) — not a list of findings
   left unreconciled. This is B.11 as experienced.
8. **HONEST** — confidence calibrated and legible; the user leaves knowing how much to trust
   each claim (validated vs structural vs speculative). The veto catches lies; this catches
   fog.
9. **COHERENT** — internally consistent; no self-contradiction between paragraphs; timing,
   promise, and remedy statements agree with each other.

**Family C — DELIVERY (does it land?)**

10. **CLEAR** — usable form for an intelligent non-astrologer: Sanskrit translated or glossed,
    structure serving comprehension, no tool/system noise leaking through.
11. **PROPORTIONATE** — length and detail match the question's weight; a pointed question
    gets a pointed answer, a deep question gets depth — no burying either way.
12. **ACTIONABLE** — where guidance is sought, the user can actually DO something with it
    (score n/a for purely descriptive queries; renormalize).

**Scoring:** family subtotals (A: /10 · B: /8 · C: /6 or /4) + overall /24 (or /22),
normalized to /10 for banding. Family subtotals are REPORTED SEPARATELY in the register and
pattern reads — a substance-rich/delivery-poor system and a fluent-but-shallow system need
opposite campaigns, and only family-level visibility distinguishes them.

**Veto (P5):** any fabrication or false confidence = FAIL regardless of matrix score.
**Bands (on the normalized /10):** 9–10 DELIGHT · 7–8 PASS · 5–6 WEAK · ≤4 FAIL (veto ⇒ FAIL).

**Failure taxonomy (every WEAK/FAIL gets exactly one primary tag, by user experience):**
`SILENT` (didn't surface what the system demonstrably has — the original wealth-reading sin) ·
`VAGUE` (generic astrology) · `JARGON` (right substance, unusable form) · `FALSE-CONFIDENT`
(unearned precision/certainty; includes veto cases) · `REFUSED-WRONGLY` (over-caution against
an answerable ask) · `BROKEN` (mechanical failure: error, empty, incoherent). Plus one
non-failure tag, counted with pride: `HONEST-GAP` (correctly declared limit — a PASS).

**User-severity per WEAK/FAIL:** `TRUST-BREAKING` (a real user would stop believing the
instrument) · `VALUE-LOSING` (shrug, less value than promised) · `COSMETIC` (would barely
notice).

## §6.0 — Investigation-quality track (the "beyond an acharya" evaluation; v1.1, native-directed)

The instrument's deepest claim is not that it answers questions — it's that an AI astrology
supercomputer INVESTIGATES: reasons about which tools to call, reads what comes back, spots
the leads a returned payload contains, and digs further until the picture is complete. This
track evaluates whether that agentic behavior actually happened. It is graded from the SEALED
TOOL TRANSCRIPTS — therefore it is a THIRD track, scored in Phase 4 by the Adversarial
Auditor (Opus, max effort), fully separate from the §6 answer grade (P1 preserved: the answer
grade never sees transcripts; this track never alters an answer grade — it explains it).

Per query, from the transcript, 0–2 each:

- **I1 — TOOL REASONING:** was the tool selection question-driven (visible reasoning →
  targeted calls) or shotgun/ritualistic (same opening battery regardless of question,
  irrelevant calls, missing the obviously-indicated surface)?
- **I2 — LEAD FOLLOWING (the heart of the track):** returned payloads contain threads — drill
  pointers, escalation flags, contradiction markers, firing yogas, active windows, judgment
  flags. Did the answerer PURSUE the ones that mattered? Every ignored material lead is
  listed: `leads_offered` vs `leads_pursued`, with the ignored ones named. This directly
  audits whether the serving layer's density/escalation design (§N.6, RS-4 valves) actually
  drives deeper investigation in practice.
- **I3 — ITERATIVE DEEPENING:** did retrieval → reasoning → further retrieval genuinely
  iterate when the question warranted it (multi-hop investigation), or was it one-pass
  fetch-and-write?
- **I4 — COVERAGE JUDGMENT:** did it call the surfaces this question NEEDED (cross-checking
  the §4 benchmark where one exists) and STOP when complete — neither premature closure nor
  aimless trawling?
- **I5 — EVIDENCE FIDELITY:** does every material claim in the final answer trace to
  something actually retrieved (no unsupported embellishment between transcript and answer —
  the transcript-side twin of the fabrication veto)?

**Investigation bands:** 9–10 INVESTIGATOR (the beyond-acharya behavior, demonstrably) ·
7–8 COMPETENT · 5–6 MECHANICAL (tools called, intelligence thin) · ≤4 BLIND (shotgun or
one-pass regardless of need).

**Why this track exists:** it is the diagnostic bridge between the other two. A WEAK answer
with BLIND investigation is a different disease (the agentic loop failed — serving-layer
affordances or answerer prompting) than a WEAK answer with INVESTIGATOR-grade digging (the
system's data or synthesis is the ceiling). §8's pattern reads use exactly this contrast.

## §6.2 — Vidhi planner track (query → intent → plan → instructions; v1.1, native-directed)

Between the user's question and the retrieval tools sits the VIDHI layer: intent
classification + `plan_retrieval` — the planner that identifies which tools to call, in what
depth, with what instructions. This track evaluates how well Vidhi itself performs per
question — because a strong Opus answerer can RESCUE a bad plan by going off-script, and
without this track that rescue would silently mask planner defects. Graded in Phase 4 by a
dedicated **Vidhi Auditor (Opus, max effort)** from two sources: (a) the sealed transcript
where the answerer actually invoked intent/planner surfaces, and (b) a controlled REPLAY —
the auditor re-submits each battery query verbatim to `intent_classify` + `plan_retrieval`
and grades the returned plan directly (read-only calls; permitted within §10 scope). Replay
makes every query a planner test even if the answerer never consulted the planner.

Per query, 0–2 each:

- **V1 — INTENT:** was the query's intent classified correctly (domain, depth class,
  interpretive-vs-retrieval per RS-4, temporal vs static)? Misclassification cascades — name
  it precisely.
- **V2 — TOOL SELECTION:** does the plan name the right retrieval surfaces for this question —
  the needed ones present, dead weight absent, firings-vs-catalog authority respected
  (§N.6)?
- **V3 — ASTROLOGICAL COVERAGE (the heart of the track):** does the plan cover the
  astrological aspects that BEAR on this question — relevant vargas, dasha systems beyond
  Vimśottarī (DR-14), yogas/firings, karakas, arudhas, sensitive degrees, transit/gochara
  surfaces, contradiction checks? Where a §4 benchmark list exists, the PLAN (not just the
  answer) is checked against it item-by-item. Every bearing aspect the plan omits goes into
  the **Vidhi gap ledger**: `aspects_required · aspects_planned · aspects_missed`, named
  astrologically ("no D9 consultation planned for a marriage question"), not as tool names.
- **V4 — INSTRUCTION QUALITY:** are the plan's instructions actionable and correctly
  parameterized (chart pin, date ranges, depth directives, escalation guidance) — a real
  investigation brief, not a tool list?
- **V5 — PLAN SUFFICIENCY:** could a faithful executor produce a DELIGHT-band answer from
  this plan alone? Cross-read with the transcript: `plan_followed?` and `off_plan_rescue?`
  — every case where the answerer had to abandon or exceed the plan to succeed is flagged;
  those rescues are planner gaps wearing a success mask.

**Vidhi bands:** 9–10 MARGADARSHAK (the plan itself is acharya-grade guidance) · 7–8 SOUND ·
5–6 THIN (right direction, missing bearing aspects) · ≤4 MISLEADING (wrong intent, wrong
surfaces, or coverage gaps that would doom a faithful executor).

**Cross-track diagnostics this enables (used by §8.11):** plan-good + answer-weak →
execution/synthesis problem; plan-thin + answer-good → Opus is silently compensating (a
scaling risk — lesser consumers of the same MCP will not); plan-thin + answer-weak → Vidhi
is the bottleneck, and the aggregated gap ledger says exactly which astrological knowledge
is missing from planning. The gap ledger is also DR-18's census question asked of the
planner: does Vidhi KNOW everything the system knows?

## §6.3 — Retrieval-plane track (the substrate as experienced; v1.2, native-directed 2026-07-24)

The elevated retrieval engine carries every Darpana query. Its CORRECTNESS is gated
deterministically BEFORE Darpana (SARVA-SIDDHI W-R: full conformance battery + density census
in LIVE mode against the deployed server — a committed receipt names the retrieval-plane
version Darpana assesses). Inside Darpana, retrieval is therefore a controlled variable, and
this track measures its EXPERIENCE face — graded in Phase 4 from the sealed transcripts (no
extra queries; the envelopes are already captured), by the Adversarial Auditor (Opus, max).
Never alters an answer grade; explains it.

Per query, 0–2 each:

- **RE1 — ROUTING FIDELITY:** did executed calls hit the capabilities the plan intended
  (primary live_tool), or degrade to fallback faces / wrong surfaces? Every fallback taken is
  named with its trigger.
- **RE2 — ENVELOPE CONFORMANCE AS-SERVED:** v3 envelopes on the queries that matter actually
  carried populated verdict / ranking_basis / grounding / drill_pointers / judgment_flags —
  not empty shells beside a legacy blob.
- **RE3 — DENSITY AS-EXPERIENCED (§N.6 live):** catalog-vs-confirmed never flattened;
  hardFloor sections survived trims; every empty carried its empty_reason; no
  populated-looking-but-hollow envelopes.
- **RE4 — DRILL-POINTER EFFICACY:** cross-read with §6.0's I2 ledger — of `leads_offered`,
  how many were RESOLVABLE (pointer → real deeper surface with real rows)? Distinguishes
  "answerer ignored the lead" from "the lead was decoration" — the loop §6.0 alone cannot
  close.
- **RE5 — PAYLOAD INTEGRITY:** fact_ids resolve, citations well-formed, pagination honest
  (no truncation corruption or silently-lost rows reaching the answer).

**Bands:** 9–10 CONDUIT (the plane amplified the answer) · 7–8 SOUND · 5–6 LEAKY (losses/
degradations that cost answer quality) · ≤4 OBSTRUCTIVE. `probable_layer` gains the explicit
value `retrieval_plane`, making planner vs retrieval vs synthesis vs data attribution fully
separable in Phase 4. §8 gains pattern read **§8.12 (retrieval read):** RE distributions per
stream; the fallback-taken ledger aggregated; RE4's resolvable-vs-decorative pointer census
(the serving-affordance verdict); retrieval_plane-attributed failures ranked — the direct
evidence base for the next retrieval-plane iteration.

## §6.1 — Experience telemetry (the second half of user experience; v1.1 addition)

Value has two faces: WHAT the user received (§6 rubric) and WHAT IT COST to receive it —
time, friction, reliability. Both are captured per query; they are graded on SEPARATE tracks
(a slow brilliant answer and a fast vague answer are different failures — never averaged into
one number).

**Per-query telemetry (Coordinator extracts mechanically from the answerer's sealed transcript
+ wall-clock records; the Grader never sees it — P1/P4 hold for quality grading):**

- `t_total` — wall-clock from query posed → final answer complete (the user's wait).
- `t_first_signal` — time to first meaningful content (perceived responsiveness).
- `tool_calls_n` — MCP calls the answerer needed; `tool_errors_n` — errors/timeouts/retries
  (incl. silent ones visible in transcript); `retry_recoveries_n` — errors the answerer
  papered over (user never saw, but cost time).
- `payload_kb_total` — retrieval bytes returned (budget/§N.6 behavior as experienced);
  `truncation_events` — any budget-trim/pagination artifact that visibly degraded the answer.
- `followups_needed` — did the answerer (as user proxy) need its allowed follow-up to get
  the substance the FIRST response should have carried?
- `friction_notes` — free text: anything a real user would FEEL (long silent stalls, tool-name
  noise leaking into the answer, contradictory partial responses, connector re-auth stalls).

**Experience bands (per query, separate from quality band):** `SMOOTH` (fast, no visible
stumbles) · `ACCEPTABLE` (noticeable wait or one recovered stumble) · `STRAINED` (long wait,
multiple recoveries, or visible degradation) · `BROKEN-FEELING` (errors/timeouts a user would
experience as product failure, regardless of eventual answer quality).

**Session-level capture (once per answerer batch):** connector cold-start time, any
availability incidents, and a one-paragraph answerer debrief — "as the user's proxy, how did
this FEEL to use?" — written by the Opus answerer at batch end, before it sees any grades.

**Baseline note:** MCP-channel numbers are the CURRENT channel's experience, stated as such in
the report — they are the baseline the eventual product UI must beat, not a verdict on a UI
that doesn't exist yet. D-6's minutes-per-chart scale goals get their evidence here too:
any latency traced to build/materialization state is flagged `d6_relevant: true`.

## §7 — The register (single output artifact of record)

`UAT_DARPANA_REGISTER_v1_0.md` — one row per query:
`query_id · stream · scripted/unscripted · user_voice_text · verbatim_answer (full, appendix
if long) · **quality matrix (§6: all 12 dimensions individually + family subtotals A/B/C +
normalized score)** · band · veto? · failure_tag · severity · grader_note (≤3 lines per
dimension where scored <2) · auditor_delta (if re-graded) · probable_layer (Phase 4 only) ·
benchmark_delta (where a §4 benchmark exists: what was volunteered vs expected, item by item) ·
**investigation track (§6.0: I1–I5 + band + leads_offered/leads_pursued with ignored leads
named)** ·
**Vidhi track (§6.2: V1–V5 + band + aspects_required/aspects_planned/aspects_missed +
plan_followed? + off_plan_rescue? + replay-vs-live source flag)** ·
**experience telemetry (§6.1: t_total · t_first_signal · tool_calls_n · tool_errors_n ·
retry_recoveries_n · payload_kb_total · truncation_events · followups_needed ·
experience_band · friction_notes · d6_relevant?)**`.
Plus sections: conductor rulings; protocol incidents (contaminated sessions, re-runs);
sealed-transcript index; session-level experience capture + answerer debriefs (§6.1).

## §8 — Maximizing the learning (Phase 4 pattern reads — mandatory, in order)

1. **Stream verdicts:** mean score + band distribution per stream → which VISION PROMISES
   land and which don't. This is the headline.
2. **Taxonomy clustering:** where do SILENT/VAGUE/JARGON/FALSE-CONFIDENT concentrate? Each
   cluster names a different next-campaign shape (retrieval-coverage vs synthesis vs
   serving-voice vs honesty-enforcement). One dominant tag = one focused campaign; scattered
   tags = polish backlog, no campaign.
3. **Benchmark deltas:** S1-wealth volunteered-findings check — the single cleanest
   before/after measure of the entire campaign arc against its founding incident.
4. **Honesty balance:** HONEST-GAP count vs FALSE-CONFIDENT count vs REFUSED-WRONGLY count —
   the three-way tension that defines whether the instrument's soul survived into serving.
   Target shape: HONEST-GAP > 0, FALSE-CONFIDENT = 0, REFUSED-WRONGLY ≈ 0.
5. **Naive-vs-expert gap:** compare maximally-naive queries against expert-phrased twins on
   the same substance — measures how much value is gated behind knowing what to ask (the
   accessibility of depth; critical for the beyond-one-native mission).
6. **Severity-weighted top-10:** the gaps that would most damage a real user's trust, ranked —
   the direct seed of the next campaign brief.
7. **Delta hooks for the future:** the register's schema + battery version pin so the
   identical battery can re-run post-next-campaign and produce a VALUE-MOVEMENT number, not
   an impression.
8. **Experience read (v1.1):** telemetry distributions (t_total p50/p90/max, error rates,
   experience-band mix) overall and per stream; the QUALITY×EXPERIENCE cross-matrix — the
   four corners tell four different stories (brilliant-and-smooth = ship it;
   brilliant-but-strained = engineering next; fast-but-vague = synthesis next;
   slow-and-vague = rethink) — and which corner each stream lives in; friction themes from
   the answerer debriefs; `d6_relevant` items collected as D-6 evidence.
9. **Family read (v1.1):** §6 family subtotals (SUBSTANCE / TRUTH / DELIVERY) per stream —
   which FACE of answer quality is the system's ceiling. Substance-poor → retrieval/data
   campaign; truth-poor → synthesis/honesty campaign; delivery-poor → serving-voice work.
10. **Investigation read (v1.1, the beyond-acharya verdict):** I1–I5 distributions; the
    QUALITY×INVESTIGATION contrast per §6.0 (weak answers with BLIND digging vs weak answers
    despite INVESTIGATOR digging point to opposite fixes); the ignored-leads ledger
    aggregated — which serving-layer affordances (drill pointers, escalation valves, judgment
    flags) are being consumed by the agentic loop and which are decoration in practice. This
    read is the direct empirical test of DR-18's are-we-using-all-we-know mandate at the
    SERVING layer, and the headline answer to "is this an AI astrology supercomputer or a
    chatbot with tools."
11. **Vidhi read (v1.1, the planner verdict):** V1–V5 distributions per stream; the
    aggregated Vidhi gap ledger — which astrological aspects the planner systematically
    misses (ranked by frequency × severity of the questions they bear on); the
    PLAN×ANSWER cross-matrix per §6.2's diagnostics, with special attention to the
    off_plan_rescue count — the measure of how much delivered quality currently depends on
    Opus silently compensating for the planner (the system's hidden scaling debt: lesser
    consumers of the same MCP inherit the plan, not the rescue). Output: a concrete
    "Vidhi missing-knowledge list" ready to seed a planner-enrichment lane if the
    disposition warrants one.

## §8.1 — The Fable handoff packet (Phase 5 deliverable contract; v1.1)

Phase 5's output returns to the NATIVE'S FABLE 5 COWORK SESSION for announcement, complete
analysis, and the roadmap ruling. The Synthesist therefore packages, as committed artifacts:

0. `RETRIEVAL_AUDIT_REPORT_v1_0.md` (Phase 0.7's R-5) — the deterministic audit: conformance
   results, the full Concept-Coverage Matrix, verbatim leakage inventory, fixes with
   before/after, and the assessed-version receipt.
1. `UAT_DARPANA_REPORT_v1_0.md` — stream verdicts, all eight §8 pattern reads, top gaps by
   user-severity, experience read, disposition recommendation, assessed-configuration
   statement (Opus-over-MCP, effort levels, dates run).
2. `UAT_DARPANA_REGISTER_v1_0.md` — full register incl. telemetry columns.
3. `UAT_DARPANA_ANSWER_APPENDIX_v1_0.md` — EVERY verbatim answer in full, so Fable can read
   what the user actually read, not summaries of it.
4. Answerer debriefs + session-level experience capture (may live in the register).
5. A ≤2-page `FABLE_HANDOFF_SUMMARY.md` — the paste-back: headline verdicts, the
   quality×experience matrix, top-10 severity-ranked gaps, protocol incidents, and exact
   paths to items 1–4.

Completeness rule: NOTHING summarized-only. Every claim in the report must be traceable to a
register row or verbatim answer Fable can open. If a telemetry field could not be captured
for a query, the field says `not_captured: <reason>` — never silently absent (B.10 in
UAT form).

## §9 — How the output gets used (value path)

Register → native review → native picks one of three pre-named dispositions:
(a) **ACCEPT** — value delivered at vision grade; next initiative is D-6 scale-up;
(b) **TARGETED CAMPAIGN** — one dominant failure pattern → a focused wave (brief seeded
directly from §8.2 + §8.6, in the user's language);
(c) **POLISH BACKLOG** — scattered small gaps → filed as register items worked in
maintenance sessions, no campaign ceremony.
In all three: the battery becomes the STANDING ACCEPTANCE SUITE, re-run at every future
campaign close and at D-6 cutover (per §8.7). UAT-DARPANA thereby becomes the instrument's
permanent definition of "does it serve," the user-side twin of the regression battery.

## §10 — Scope guards

may_touch: `00_ARCHITECTURE/llm_consumption_audit/uat_darpana/**` (all initiative artifacts),
SESSION_LOG append, register cross-reference notes into the defect register (file-only, as
new CR rows citing UAT query_ids). must_not_touch: ALL system code, migrations, writers,
serving tools, doctrine files, sealed split, calibration tables. Zero fixes ship from this
initiative — findings are filed, never patched inline.
