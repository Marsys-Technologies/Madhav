---
artifact: CLAUDECODE_BRIEF_M5A_S1_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: READY
authored_by: Cowork-M5-S2-PLAN-AMENDMENT-2026-05-13
authored_at: 2026-05-13
session_id: M5-A-S1
session_name: M5-A-S1 — Substrate, Entry Cleanup, PPL Cadence (Full Execution)
executor: Claude Code (Antigravity / VS Code extension)
execution_mode: long-running single session, --dangerously-skip-permissions
worktree:
  name: marsys-m5-dbn
  branch: feature/m5-probabilistic-model
  base: main
  path_relative_to_project: ../marsys-m5-dbn
governing_plan: 00_ARCHITECTURE/PHASE_M5_PLAN_v1_0.md (v1.1)
active_sub_phase: M5-A
---

# CLAUDECODE_BRIEF — M5-A-S1
## Substrate, Entry Cleanup, PPL Cadence — Full Execution

---

## §0 — How to start this session

**Step 1 — Create and enter the worktree (run in project root):**
```bash
git worktree add ../marsys-m5-dbn feature/m5-probabilistic-model 2>/dev/null || \
  (git checkout -b feature/m5-probabilistic-model && \
   git worktree add ../marsys-m5-dbn feature/m5-probabilistic-model)
cd ../marsys-m5-dbn/platform && npm install
```

**Step 2 — Launch Claude Code in Antigravity with bypass permissions:**
```
Open the marsys-m5-dbn folder in VS Code / Antigravity
Launch Claude Code with: --dangerously-skip-permissions
```

**Step 3 — Paste this prompt to kick off the session:**

```
Read CLAUDE.md, then read 00_ARCHITECTURE/PHASE_M5_PLAN_v1_0.md (active plan is v1.1),
then read 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_M5A_S1_v1_0.md and execute it.
You are in the marsys-m5-dbn worktree on branch feature/m5-probabilistic-model.
Active session: M5-A-S1. Execute all 14 scope items in §3 of the phase plan.
Emit session_open handshake first, then proceed item by item.
```

---

## §1 — Session identity

| Field | Value |
|---|---|
| Session ID | M5-A-S1 |
| Cowork thread name | `M5-A-S1 Substrate Entry Cleanup PPL Cadence 2026-05-13` |
| Branch | `feature/m5-probabilistic-model` |
| Worktree | `marsys-m5-dbn` |
| Execution mode | Long-running, --dangerously-skip-permissions |
| Predecessor | Cowork-M5-S2-PLAN-AMENDMENT-2026-05-13 (this brief authored here) |
| Next session | M5-A-S2 (if M5-A requires multiple sessions) or M5-B-S1 if M5-A closes |

---

## §2 — Mandatory reads at session open (in order)

1. `CLAUDE.md` (§C mandatory list — full read)
2. `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` §2 (state block — confirm M5-A OPEN)
3. `00_ARCHITECTURE/PHASE_M5_PLAN_v1_0.md` (v1.1 — this is the governing plan)
4. `00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` §C.1–§C.6 + §K
5. `06_LEARNING_LAYER/` README or directory listing (LL scaffold state)
6. `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` §6 (gap register) + most recent changelog entry
7. `00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md` DIS.009 entry (for item 13 closure)

Then emit SESSION_OPEN per `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md`.

---

## §3 — Scope (14 items — execute in order unless parallel-safe)

Items 1–7 are sequential substrate work. Items 8–14 can partially overlap once the
directory scaffolds (items 1–2) are done. Item 11 (held-out partition) MUST be declared
before item 8 (PPL retroactive predictions) begins.

### Item 1 — LL.8 scaffold
**What:** Create `06_LEARNING_LAYER/dbn/ll8_bayesian_update/` directory with:
- `LL8_SPEC_v1_0.md` — spec document: activation condition (DBN params exist from M5-D),
  update mechanism (posterior update on new PPL outcome), kill-switch definition
  (update suspended if credible-interval width > 2× prior width), parameter register stub
- `parameter_register_stub.json` — empty JSON with declared schema

**AC:** AC.M5A.1 — directory exists; spec present; stub present; kill-switch defined.

### Item 2 — LL.9 scaffold
**What:** Create `06_LEARNING_LAYER/miss_registry/` directory with:
- `LL9_SPEC_v1_0.md` — spec document: activation condition (M6 open), miss definition
  (prediction emitted but outcome contradicts at ≥2σ), registry schema
- `miss_registry_stub.json` — empty JSON with declared schema

**AC:** AC.M5A.2 — directory exists; spec present; stub present.

### Item 3 — CF.LL7.1 CDLM patch confirmation
**What:** Confirm whether the M4-D-P1 parallel CDLM patch landed:
1. Read `025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md` — check version/status and whether
   8 MED-tier Pancha-MP sanity anchors were updated from `novel` → `confirmed`
2. If patch landed: re-emit `ll7_discovery_prior_v1_0.json` with the expected flip
3. If patch did NOT land: this becomes a M5-A blocker — apply the patch first, then re-emit

**AC:** AC.M5A.3 — re-emitted JSON committed; 8 MED-tier status confirmed.

### Item 4 — Gemini mirror sync (R.LL1TPA.1)
**What:** Re-attempt Gemini-side mirror propagation for accumulated M4 surrogate decisions.
Read `.gemini/project_state.md` — check last-sync state. Attempt ratification per
GOVERNANCE_INTEGRITY_PROTOCOL §K.3. If unreachable: extend surrogate-disclosure ledger
entry and declare `FINAL_NOT_REACHABLE_M5` in the ledger. Do not block M5-A close on this.

**AC:** AC.M5A.4 — disposition recorded (REACHABLE+ratified OR FINAL_NOT_REACHABLE_M5).

### Item 5 — MP.1 + MP.2 mirror catch-up
**What:** CURRENT_STATE v3.9→v4.0 delta was not propagated at pre-M5 session.
Propagate now: update `.geminirules` (MP.1) and `.gemini/project_state.md` (MP.2) to
adapted-parity reflection of CURRENT_STATE v4.0. Record propagation in close-checklist
`mirror_updates_propagated` block.

**AC:** AC.M5A.5 — both mirror files updated; parity confirmed.

### Item 6 — MSR signal-completeness reconciliation
**What:** 4 absent signal IDs: SIG.MSR.207 + SIG.MSR.497/498/499.
1. Read `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` §I (declared count) and the signal list
2. Check `platform/` for `msr_domain_buckets.json` or equivalent — what does the platform
   see vs what MSR declares?
3. Resolve: either populate the 4 missing signals with proper frontmatter/content, or update
   the declared count (with rationale in MSR changelog)

**AC:** AC.M5A.6 — 4 absent IDs resolved; MSR version bumped; platform count matches declared count.

### Item 7 — LL.2 per-edge promotion campaign (Phase 1)
**What:** Initiate two-pass approval for 8 MED-tier Pancha-Mahapurusha anchor edges.
1. Read `06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/shadow/` — locate the 8 MED-tier
   Pancha-MP edges identified at M4-B-S5
2. For each of the 8 edges: emit a per-edge approval request in the SESSION_LOG or a
   dedicated campaign document, with the signal pair, current weight, proposed weight,
   and classical justification
3. Campaign is submitted; native review happens asynchronously (not a M5-A session blocker)

**AC:** AC.M5A.7 — 8 edges submitted for two-pass native review; campaign document committed.

### Item 8 — PPL volume audit + retroactive prediction protocol
**IMPORTANT: Item 11 (held-out partition declaration) must precede this item.**

**What:**
(a) Audit 16 existing PPL entries — confirm format, falsifiers present, outcomes recorded
    where elapsed horizon allows
(b) Execute retroactive prediction protocol on held-out partition:
    - For each held-out LEL event: write the prediction (domain, direction, confidence band,
      falsifier) BEFORE opening the LEL entry for that event in the same session
    - After prediction is committed to the PPL log, open the LEL entry and score it
    - Minimum 4 retroactive predictions to reach ≥20 gate; aim for all 9 held-out events
    - Each prediction entry must include: `generated_session: M5-A-S1`,
      `outcome_revealed_session: M5-A-S1`, `blinding_method: prediction_first_then_reveal`
(c) Document the feedback loop: how a PPL outcome triggers an LL.8 update (once LL.8
    activates at M5-D)
(d) Propose ongoing prospective cadence: how many predictions per M5 session; which
    life-domains to prioritize (spiritual, finance, career); falsifier definitions

**NAP.M5.0 — native approval required at M5-A close for the cadence proposal.**

**AC:** AC.M5A.8 — retroactive protocol executed (≥4 predictions); cadence proposal authored;
feedback loop documented; NAP.M5.0 submitted for native approval.

### Item 9 — JH-export workstream scheduling
**What:** Agree a window with native for Jagannatha Hora export. Three items to schedule:
(a) Sthana (positional strength) + Drik (aspectual strength) export for all natal planets
(b) ECR for Sthana/Drik discrepancies vs v8.0 FORENSIC values
(c) Narayana Dasha verification for the native's chart
Record the agreed window in SESSION_LOG and in a JH_EXPORT_SCHEDULE note.

**AC:** AC.M5A.9 — window agreed; three items scoped; schedule note committed.

### Item 10 — Gate IV deferred ACs (non-blocking tracking)
**What:** Record current status. Do not block M5-A close.
- AC.IV.6 (recall=0.9355): no action yet; target M5-B after LL.3 fixes
- AC.IV.7 (latency_ms null): check audit_events table — has 7-day prod traffic accumulated?
  If yes: re-run latency regression. If not yet: record "still pending, re-check M5-B."

**AC:** AC.M5A.10 included in close only after items 1–9 and 11–14 are done.

### Item 11 — Held-out partition formal declaration
**PREREQUISITE for Item 8. Execute first within the PPL/held-out block.**

**What:** Declare the held-out LEL partition before any retroactive prediction work:
1. Identify the 9 most recent point events in the LEL by EVT ID (approximate range 2019–2026)
   — list them by ID and date
2. Create `01_FACTS_LAYER/LEL_HELD_OUT_PARTITION_v1_0.md` with:
   - The list of held-out EVT IDs (frozen from this point)
   - Training partition: all remaining events
   - Declaration: "These events are blinded from topology and prior design sessions.
     They may be read for retrodictive-prediction scoring in M5-A PPL work only, under
     the blinding protocol specified in PHASE_M5_PLAN_v1_0.md §3 Item 8."
3. Once declared: topology and prior sessions (M5-B, M5-C) must not read held-out event
   outcomes; this file is the enforcement record

**AC:** AC.M5A.11 — partition file created; 9 events listed; training/held-out split recorded.

### Item 12 — LEL domain enrichment (10 new events)
**What:** Add 10 new events to `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` as YAML entries.
Events were approved by native in Cowork session 2026-05-13. Each entry follows the
standard LEL YAML schema (EVT ID, date, date_confidence, category, subcategory,
description, magnitude, valence, native_reflection, chart_state_at_event,
retrodictive_match, notes).

For chart_state_at_event: use Swiss-Ephemeris proxy-date computation where exact date
is unknown (document computation_date and proxy_date_used per existing convention).
For year-vague events (~1997–2001 range), use mid-point proxy and flag `year-approx`.

**Events to add (use these as source data):**

**SPR.A — Father spiritual dialogue transmission**
- date: ~1998-XX-XX, date_confidence: year-approx, category: spiritual, subcategory: transmission
- description: Father (Late Shri Soumya Ranjan Mohanty) held late-night spiritual dialogues
  with close friends; native joined in limited capacity during teens (~1997–2001). These
  conversations planted the seed of spirituality. Father's approach intermingled Hinduism
  and spirituality — became the native's foundational spiritual orientation.
- magnitude: significant, valence: positive
- native_reflection: "My father was a very spiritual person. I would join late night conversation
  between my father and one or two specific friends of his who might be staying over in these
  spiritual conversations in a limited way."

**SPR.B — Shani Puja initiation by father**
- date: ~2002-XX-XX, date_confidence: year-approx, category: spiritual, subcategory: sadhana_initiation
- description: Father instructed native (age ~18–19) to perform Shani Puja nightly. Native
  read Shani Shtotram every night for approximately 7–10 years. This became the first formal
  sustained sadhana practice. Father as transmitter of Saturn-discipline is astrologically
  significant: Saturn rules native's Arudha Lagna (Capricorn, 10th house).
- magnitude: significant, valence: positive
- native_reflection: "My father asked me to do Shani Puja. So every night I used to read
  Shani Shtotram for a good seven, eight years or ten years."

**SPR.C — Ugratara Shakti pitha devotion onset**
- date: ~2010-XX-XX, date_confidence: year-approx, category: spiritual, subcategory: devata_adoption
- description: Began regular devotion to Maa Ugratara at the Ugratara Shakti pitha near
  Bhubaneswar (~15 years running as of 2026). A tantric Shakti form. This is the native's
  longest-sustained single devata relationship. Commenced during mid-to-late twenties.
- magnitude: significant, valence: positive
- native_reflection: "During my mid-twenties and until today, I became a devout devotee of
  Mah Ugratara. Near to Bhubaneswar, there is a Ugratara Shakti peat, which I have been
  visiting for the last ten years or more, close to about fifteen years."

**SPR.D — Mahadev/Shiva devotion onset**
- date: ~2015-XX-XX, date_confidence: year-approx, category: spiritual, subcategory: devata_adoption
- description: In early thirties (~2014–2016), native began gravitating toward Mahadev/Shiva.
  This deepened over the following decade to the point of daily abhisheka (see SPR.E).
  Concurrent with Ugratara devotion; no conflict perceived until Krishna re-emerged.
- magnitude: significant, valence: positive
- native_reflection: "In my early thirties I started gravitating towards Mahadev or Shiv,
  and until today, I am a devout devotee of Mahadev."

**SPR.E — Daily abhisheka + yajna practice convergence**
- date: ~2024-XX-XX, date_confidence: year-approx, category: spiritual, subcategory: practice_intensification
- description: From ~2024: daily pouring of water on shivalinga (abhisheka); independent
  yajna execution (fire ritual, self-conducted); systematic panchang study (transit, muhurta,
  tithi); identification and planning of yajna timings using astrological data. Simultaneous
  with entrepreneurial transition and dharma-embrace (self-described "I must align my life
  to Dharma"). Highest concentration of new spiritual practices in native's life.
- magnitude: major, valence: positive
- native_reflection: "For the last two years I have been pouring water on the shiveling almost
  every day... I have been doing enormous amount of yajna. Now I have developed a skill that
  I do a yajna on my own... I have been following astrological data, looking at the panchang."

**SPR.F — Yantra mandala established**
- date: 2025-06-XX, date_confidence: month-approx (native confirmed mid-2025), category: spiritual
- subcategory: ritual_infrastructure
- description: Native established a personal yantra mandala in his bedroom — a permanent
  ritual space. Prayers offered almost daily, sometimes more than once. Combined with daily
  ritual routine (~1.5–2 years running as of 2026). Represents formalization of the
  private ritual life begun in ~2024.
- magnitude: significant, valence: positive
- native_reflection: "I have my own yantra mandala established in my bedroom, which I offer
  prayers almost every day, sometimes more than once. There is a daily ritual that I follow."

**SPR.G — Ma Kamlatmika (tantric Mahalakshmi) devotion onset**
- date: ~2025-11-XX, date_confidence: month-approx (native said "last six months" as of
  2026-05-13), category: spiritual, subcategory: devata_adoption
- description: Native began praying intensely to the tantric form of Mahalakshmi — Ma
  Kamlatmika (one of the Dasha Mahavidyas). Coincides with financial recovery and business
  intensification. A Lakshmi-form alongside the existing Ugratara (Shakti) and Mahadev
  lineages — now three tantric streams active simultaneously.
- magnitude: significant, valence: positive
- native_reflection: "Over the last six months, I have started praying a lot to Mahalakshmi
  the tantric form of Mahalakshmi that is Ma Kamlatmika."

**CRE.A — Painting competition awards, childhood**
- date: ~1993-XX-XX, date_confidence: year-approx, category: creative, subcategory: award
- description: Mother enrolled native in painting classes at early age; native excelled and
  won multiple awards in childhood painting competitions. Creative visual skill established
  early. Subsequently moved away from painting; creative output shifted to digital/professional
  domains (presentations, brand design). The visual-spatial gift persisted as a latent trait
  activated selectively in professional/entrepreneurial contexts.
- magnitude: moderate, valence: positive
- native_reflection: "At an early age my mother had put me to learn painting and I was pretty
  good at it. I won several awards in my childhood in painting competitions."

**PSY.A — Vertigo/head reeling peak debilitation (engineering exam prep)**
- date: ~2002-XX-XX, date_confidence: year-approx, category: psychological, subcategory: chronic_episode
- description: Inherited vertigo/head reeling (maternal line — mother and maternal grandmother
  both affected) reached peak debilitation during engineering competitive exam preparation
  (~2001–2004). Bouts were described as "debilitating" and directly impacted academic
  performance. The fear of recurrence persisted for approximately one decade. Onset likely
  earlier (teen years); peak impact on career trajectory was during exam prep.
- magnitude: significant, valence: negative
- native_reflection: "The period between 2001 to 2004 especially 2001 to 2002 when I was
  preparing for my competitive exams, engineering exams. I was hit hard by vertigo and that
  left a deep mark, psychological mark and I've feared it with all my life for close to a decade."

**PSY.B — Stammering: onset, overcome, resurgence**
- date: ~1995-XX-XX, date_confidence: year-approx (onset; use as anchor), category: psychological
- subcategory: speech_pattern_arc
- description: Three-phase arc. Phase 1 (childhood): significant stammering; nickname "sacca"
  given by a friend (school years). Phase 2 (engineering/MBA years): sustained practice
  substantially overcame it — contemporaries unaware native stammered. Phase 3 (resurgence,
  2025–present): stammering has resurfaced over the last ~1 year; diagnosis unknown
  (psychological, neural, or genetic). Native manages it but carries psychological impact.
  NOTE: this is a three-phase arc; the EVT captures the onset as the anchor date; phases 2
  and 3 are noted in the description and can be split into separate EVTs if warranted.
- magnitude: moderate, valence: negative (phases 1+3); positive (phase 2 overcome)
- native_reflection: "In my childhood I used to stammer quite a bit. I practiced a lot and
  during my engineering days and my MBA days I significantly got over it... That stammering
  has resurfaced over the last one year and I'm struggling with it."

**Also add to §5 Chronic Patterns:**
- Cockroach phobia: early childhood, likely triggered by village environment with high
  cockroach density; persists to present, mildly subdued. Psychological fear response.
- Manasa puja gift: lifelong capacity for deep visualized inner ritual — offering prayers,
  small rituals, and puja entirely in the mind with elaborate emotional and visual detail.
  Distinct from seated meditation. Selectively applied during bead-counting, physical puja,
  and independent visualization sessions.

Bump LEL version to v1.3 with changelog entry. Total event count after addition: 57
(47 existing + 10 new). Update confidence self-assessment.

**AC:** AC.M5A.12 — 10 new YAML entries committed; 2 chronic patterns added; version bumped to v1.3.

### Item 13 — DIS.009 formal closure
**What:** Update `00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md` DIS.009 entry:
- status: RESOLVED_R1
- verdict: R1 accepted — PAT.008 split into PAT.008-AL and PAT.008-KMC
- PAT.008-AL: Arudha Lagna = Capricorn (10th house from Lagna); lord = Saturn (exalted 7H).
  L1 grounding: FORENSIC §10.1 or equivalent AL-calculation section. Native confirmed:
  "I would like to confirm that my Aruddha Lagna is in the tenth house, Capricorn."
  Confirmation session: Cowork-M5-S2-PLAN-AMENDMENT-2026-05-13.
- PAT.008-KMC: Karakamsa = Gemini; lord = Mercury. L1 grounding: FORENSIC §20.1
  (Moon D9 = Gemini; AK = Moon at 27°02'). No JHora required; FORENSIC is authoritative.
  Confirmation: FORENSIC §20.1 read in Cowork-M5-S2.
- arbitration: native adjudicated R1; both sub-patterns confirmed from FORENSIC L1 data.
- closed_at: 2026-05-13

**AC:** AC.M5A.13 — DIS.009 entry updated; both PAT.008 sub-patterns recorded with L1 citations.

### Item 14 — answer:eval scaffold (DeepSeek)
**What:** Create `platform/scripts/eval/` directory with:
- `eval_runner.py` — reads a production query+response pair; calls DeepSeek API;
  returns a scored rubric JSON
- `eval_rubric_v1_0.json` — rubric schema:
  ```json
  {
    "b11_whole_chart_read": { "score": 0-10, "notes": "" },
    "citation_completeness": { "score": 0-10, "notes": "" },
    "calibration_language": { "score": 0-10, "notes": "" },
    "b10_no_fabricated_computation": { "score": 0-10, "notes": "" },
    "overall": { "score": 0-10, "notes": "" }
  }
  ```
- `eval_prompt_v1_0.txt` — DeepSeek system prompt for the evaluator role; includes
  rubric definitions, B.11 explanation, B.10 definition, and worked examples

LLM: DeepSeek (not Anthropic; per Cowork session 2026-05-13 decision).
The scaffold is runnable but does not require live eval in M5-A; it is ready for M5-B+.

**AC:** AC.M5A.14 — `platform/scripts/eval/` directory with three files committed; eval runnable
against a sample query-response pair.

---

## §4 — Constraints

**may_touch:**
`06_LEARNING_LAYER/dbn/`, `06_LEARNING_LAYER/miss_registry/`, `06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/shadow/`,
`025_HOLISTIC_SYNTHESIS/` (CDLM re-emit only), `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md`,
`01_FACTS_LAYER/LEL_HELD_OUT_PARTITION_v1_0.md` (new file),
`00_ARCHITECTURE/CURRENT_STATE_v1_0.md`, `00_ARCHITECTURE/SESSION_LOG.md`,
`00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md` (DIS.009 closure only),
`.geminirules`, `.gemini/project_state.md`, `platform/scripts/eval/` (new directory)

**must_not_touch:**
`platform/src/`, `platform/lib/` (no app code changes in M5-A),
`01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_*.md` (facts layer frozen),
`06_LEARNING_LAYER/SIGNAL_WEIGHT_CALIBRATION/production/` (production weights frozen),
`00_ARCHITECTURE/PHASE_M5_PLAN_v1_0.md` (plan is locked at v1.1 — no in-session edits),
held-out LEL partition events (do not read outcomes before predictions are committed)

---

## §5 — Session-close checklist (must complete before claiming close)

- [ ] SESSION_OPEN artifact emitted and validates against SESSION_OPEN_TEMPLATE
- [ ] All 14 AC checks completed (AC.M5A.1 through AC.M5A.14)
- [ ] NAP.M5.0 submitted for native approval (cadence plan document committed)
- [ ] All new files/directories committed to `feature/m5-probabilistic-model` branch
- [ ] LEL version bumped to v1.3; changelog entry added
- [ ] CURRENT_STATE_v1_0.md updated: `last_session_id = M5-A-S1`; if M5-A closes:
      `active_phase_plan_sub_phase = M5-B INCOMING`; if more M5-A sessions needed:
      `active_phase_plan_sub_phase = M5-A OPEN`, `next_session_objective = M5-A-S2`
- [ ] SESSION_LOG.md M5-A-S1 entry appended (atomic open+body+close block)
- [ ] Mirror propagation: MP.1+MP.2 updated (item 5); MP.4 pointer updated if sub-phase changed
- [ ] SESSION_CLOSE artifact emitted and validates against SESSION_CLOSE_TEMPLATE
- [ ] Branch ready for PR to main (or flag blockers if not merge-ready)

---

## §6 — LLM stack for M5 (all sessions)

| Role | Model | Notes |
|---|---|---|
| Primary inference | Gemini (gemini-2.5-pro or flash) | Default for all LLM calls |
| Fallback | DeepSeek v4 Pro | If Gemini unreachable or quota exceeded |
| Tertiary | NIM (NVIDIA Inference Microservices) | Emergency fallback |
| Anthropic/Claude API | **BANNED** | Too expensive; do not use |
| answer:eval | DeepSeek | Per Cowork session 2026-05-13 decision |

---

## §7 — Context carried from plan-authoring session

The following decisions were made in the Cowork M5-S2 session (2026-05-13) and do not
need to be re-derived:

- **AL = Capricorn (10th house)** — native confirmed in this session. L1: FORENSIC §10.1.
- **AK = Moon (27°02')** — FORENSIC §20.1.
- **Karakamsa = Gemini** — Moon in D9 = Gemini per FORENSIC §20.1; lord = Mercury.
- **DBN tooling = Hybrid-C** — JSON CPT manually computed; LLM does inference; LLM selects signals.
- **M6 PPL gate = ≥20 predictions** — retroactive held-out approach; calendar-time gate ELIMINATED.
- **Held-out partition target = 9 most recent LEL events** — approximate range 2019–2026.
- **DIS.009 verdict = R1** — PAT.008 split accepted; both sub-patterns L1-groundable.
- **LEL count at session open = 47 point events** — after M5-A-S1 addition: 57.
- **Father's passing = EVT.2018.11.28.01** — already in LEL; no new entry needed.
- **Knee surgery = EVT.2007.06.XX.01** — already in LEL; breathlessness = EVT.2007.XX.XX.03.
- **Panic attacks USA = EVT.2021.01.XX.01** — already in LEL.

---

*End of CLAUDECODE_BRIEF_M5A_S1_v1_0.md — authored 2026-05-13.*
*Executor: Claude Code (Antigravity). Branch: feature/m5-probabilistic-model.*
*Governing plan: PHASE_M5_PLAN_v1_0.md v1.1. Session: M5-A-S1.*
