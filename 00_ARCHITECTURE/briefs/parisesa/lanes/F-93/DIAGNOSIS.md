---
finding_id: F-93
tier: TIER2-HONESTY
campaign: PARIŚEṢA
stream: S4-VĀCA
status: DIAGNOSIS-COMPLETE (was DIAGNOSIS-INCOMPLETE)
exemplar_for: [F-120, F-121]
---

# F-93 Diagnosis — prashna_ask MD/AD boundary-date narration defect

## Live Reproduction

Ran the exact repro command against chart `482012f1-710e-4a25-994a-93821f5871aa`.

**prashna_ask** (`job_id: 6242b7ca-21f5-4d36-8a26-9c8542e67e68`, question: "What is the
current Vimshottari mahadasha lord for this chart?", `response_format: concise`) completed
with `query_class: "factual"`, `chart_header.current_maha_antar: "Mercury MD / Saturn AD"`,
and this synthesized `reading`:

> Based on your chart data, the current Vimshottari Mahadasha (major period) lord is
> **Mercury (Budha)**.
>
> This major period of Mercury began on **July 7, 2010**, and will end on **July 7, 2027**.

This reproduces the finding's defect class live: the MD lord (Mercury) is correct, but the
boundary dates are wrong. (This run's reading is shorter than the one quoted in the finding
— it omits the Antardasha sentence entirely, which is expected LLM non-determinism between
synthesis calls; the core MD-date defect reproduces identically in form and even in exact
value: "July 7" both times.)

**ganita_dashas_get** (`chart_id: 482012f1-…`, `level: 1`, `ayanamsha_id:
lahiri_chitrapaksha`) — the authoritative, `two_pass_verified` row:

```json
{
  "lord_graha": "Mercury", "ayanamsha_id": "lahiri_chitrapaksha",
  "start_date": "2010-08-18", "end_date": "2027-08-18",
  "verification_pass_status": "two_pass_verified"
}
```

**kala_now_get**'s independent `dasha_sandhi` block confirms the same boundary
(`Mahadasha … boundary_date: "2010-08-18"` / `"2027-08-18"`; `Antardasha … Saturn …
boundary_date: "2024-12-08"` / `"2027-08-18"` — i.e. AD end = MD end, both 2027-08-18).

Raw JSON for all three calls captured in this diagnosis session (see Mechanism section below
for the decisive fourth artifact: the actual `query_dasha_periods` evidence bundle
`prashna_ask` fed to its own synthesis LLM, recovered from the completed job's `results`
array).

## Claim Decomposition

| Claim | Verdict |
|---|---|
| (a) MD lord = Mercury | **Correct.** |
| (b) MD start/end dates wrong by ~6 weeks | **Confirmed, but the finding undersells it** — see Mechanism. The "~6 weeks off" framing (comparing `2010-07-07`/`2010-08-18`) is literally correct arithmetic, but it is not a rounding/approximation error — the narrated dates are a **different ayanāṁśa's row wholesale** (Krishnamurti, not Lahiri Chitrapaksha), not a distorted version of the Lahiri row. |
| (c) AD lord (Saturn) correctness | **Not evaluable from this reproduction** — this run's synthesized reading dropped the Antardasha sentence entirely (see Live Reproduction). The original finding's Saturn AD lord claim is independently corroborated correct by `kala_now_get.dasha_lord_transit_condition[1].lord_graha: "Saturn"` and `dasha_sandhi`'s AD band, so Saturn-as-AD-lord itself is right; only the finding's specific AD **end date** ("July 7, 2027") is addressed below. |
| (d) AD end-date ("July 7, 2027") doesn't match any served boundary | **Confirmed AND now explained.** It doesn't match any *Lahiri* boundary — but it matches the **Krishnamurti-ayanāṁśa MD end date** (`2027-07-07`) exactly (see Mechanism). The original finding treated this as an unexplained fabrication; it is not fabricated, it is the Krishnamurti row's own MD end date, misapplied to the AD sentence. |

## Mechanism (file:line, quoted code)

**This is not case (a) "LLM paraphrased a correctly-scoped cited row wrong," not case (b)
"the row was never fetched," and not a clean instance of either option the task brief
offered. It is a third, more specific mechanism: the tool call omitted a required
disambiguating filter, so the row THAT WAS fetched was multiply-scoped (5 ayanāṁśas), and
nothing downstream told the model which of the 5 rows was canonical.**

### Step A — the tool dispatch that produced the bad evidence

The completed job's `completeness.tools_dispatched` shows `query_dasha_periods` ran
successfully (`status: "done"`, `result_count: 1`). Its raw evidence bundle (recovered from
`result.results[]` in the completed job, tool_name `query_dasha_periods`) shows:

```
"invocation_params": {}
```

— i.e. **no `ayanamsha_id` was passed.** The bundle's `rows` array (facet: `system:
vimshottari`, `level: cap<=3`) contains, among others, these level-1 (MD) rows for
**Mercury**, one per ayanāṁśa:

```
krishnamurti        Mercury  2010-07-07  2027-07-07   <- what the LLM narrated
lahiri_chitrapaksha  Mercury  2010-08-18  2027-08-18   <- the canonical, two_pass_verified row
raman                Mercury  2008-11-22  2025-11-22
```

The narrated "July 7, 2010 – July 7, 2027" is not an invented or distorted date. It is the
**Krishnamurti ayanāṁśa's own MD row, verbatim**, restated by the model as if it were the
chart's single unqualified answer. Krishnamurti's MD end date (`2027-07-07`) is also, not
coincidentally, an exact match for the finding's reported (but unattributed) Antardasha
end-date "July 7, 2027" — strong corroborating evidence the same 5-ayanāṁśa evidence dump is
also the source of the AD-date defect in the original finding's fuller transcript, even
though this repro run's shorter reading didn't include an AD sentence to re-confirm it
directly.

### Step B — why omitting `ayanamsha_id` produces exactly this

`platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts:15–24` (the tool
`query_dasha_periods` resolves to, per `tool_name_bridge.ts:86`:
`query_dasha_periods: 'marsys://tool/L1/get_dashas'`) documents this exact trap in its own
header, unresolved:

```
IMPORTANT — `ayanamsha_id` is NOT defaulted server-side (unlike `system`/`level`/`window`):
... omitting it returns ALL 5 ayanamshas ...
ALWAYS pass `ayanamsha_id: "lahiri_chitrapaksha"` ... when the gate/current-dasha shape is
what's wanted. Flagged (not fixed here — a silent default would change existing
multi-ayanamsha callers' results): a future wave should consider defaulting `ayanamsha_id`
server-side ...
```

The tool's own `input_schema.ayanamsha_id.description` (lines 133–138) repeats the warning.
This is a **known, previously-flagged, deliberately-unfixed gap** — not a new defect this
diagnosis discovered from scratch, but its live consequence (a wrong ayanāṁśa's dates
reaching the reader as unqualified fact) had not previously been traced end-to-end to a
concrete `prashna_ask` transcript.

**Attribution of the `{}` call, with an honest confidence caveat:** `query_dasha_periods`
was NOT injected by either of the two floor-guarantee code paths that could otherwise explain
it:
- `ensureDashaContextFloor` (`platform/src/lib/pipeline/compiled_floor_adapter.ts:374–390`)
  only fires when `plan.query_class` is `'predictive'` or `'holistic'`
  (`compiled_floor_adapter.ts:376`). The completed job's own `query_class` is `"factual"` —
  this guarantee never ran.
- `compileFloorForPlan`'s `dasha_window` primitive (`platform/src/lib/vidhi/registry_data.ts:398–408`,
  `tool_args: { chart_id: '{chart_id}', level: '{level}', start: '{start}', end: '{end}' }`)
  would, after `compiled_floor_adapter.ts:282`'s `chart_id`-only stripping, leave **literal
  unfilled placeholder strings** (`{level}`, `{start}`, `{end}`) in `params` — not an empty
  object. `compileContract` (`platform/src/lib/vidhi/compiler.ts:127`) only ever substitutes
  `{chart_id}` and `{question_frame}`; no other template token is ever filled. This doesn't
  match the observed `{}` either.

By elimination, the `query_dasha_periods` call with `params: {}` was most likely selected
directly by the LLM **planner** (`callPipelinePlanner`, `platform/src/lib/pipeline/pipeline_planner.ts`)
as part of its own JSON `tool_calls` output — i.e. the planner LLM chose the right tool but,
like the synthesis LLM one step later, never pinned `ayanamsha_id`. I did not capture the
planner's raw JSON output for this specific trace (only the completed job's
`completeness`/`results`), so this attribution is high-confidence process-of-elimination, not
a directly-observed planner transcript — flagged honestly rather than overstated.

### Step C — why the synthesis LLM then picked the wrong one of the 5 rows

The evidence reaches the synthesis LLM verbatim via
`platform/src/lib/pipeline/prashna_ask_synthesis.ts:246–281` (`formatEvidenceBlock`), which
JSON-serializes the tool bundle's `results` (here, all 5 ayanāṁśas' rows) into an
`<evidence tool="query_dasha_periods">...</evidence>` block with no filtering by ayanāṁśa —
correct behavior for a "restate the evidence verbatim" contract, since the tool call (not
this formatter) is what should have scoped the row set to one ayanāṁśa.

Critically, **nothing anywhere in the prompt chain tells the model which ayanāṁśa is
canonical**, so when 5 candidate rows for "Mercury MD" arrive, the model has no
disambiguation rule and picks one (Krishnamurti) without noting the ambiguity or qualifying
its answer:

- `formatTemporalAnchor` (`prashna_ask_synthesis.ts:292–301`) only supplies
  `currentMahaAntar` as **lord names** ("Mercury MD / Saturn AD") — never dates, never an
  ayanāṁśa.
- `NO_LIVE_TOOLS_OVERRIDE` (`prashna_ask_synthesis.ts:90–105`) instructs the model to
  "Synthesize your reading directly and only from the `<evidence>` provided" and to disclose
  genuine gaps — it says nothing about disambiguating multiple rows for the same fact.
- The base acharya system prompt this call reuses
  (`consumeSystemPromptV2`, `@/lib/claude/system-prompts.ts`) and
  `synthesis_prompt_v2.ts` contain **zero occurrences of "ayanamsha"** (grepped both files
  directly) — there is no standing instruction anywhere in the synthesis prompt stack that
  "lahiri_chitrapaksha is this project's canonical ayanāṁśa; when evidence carries multiple
  ayanāṁśas for the same fact, cite that one and note the others exist."

### Which of the task's three options this is

Neither cleanly. It is closest to a **hybrid of (a) and (b)**: the row IS passed verbatim
into the prompt (a)-style — nothing paraphrases or recomputes the date string itself — but
the tool dispatch (not the synthesis formatter) failed to scope the query to one
disambiguated row first, so what "verbatim" means is ambiguous across 5 candidates, and (b)
applies one level down: the model effectively "estimates" *which row is truth* from
under-specified context, even though it never estimates the date value itself. **The
practical fix implied is not "cite date fields verbatim with an instruction not to alter
them" (a pure prompt-engineering fix) and not "the row isn't being fetched at all" (a pure
plumbing fix) — it is (1) close the already-flagged, already-documented `get_dashas.ts`
`ayanamsha_id` default gap at the tool-dispatch layer (whoever calls it — planner LLM,
compiled floor, or agentic loop — should default to `lahiri_chitrapaksha` when omitted,
exactly as `get_dashas.ts`'s own header already proposes), AND (2) as defense in depth, teach
the synthesis prompt the project's canonical-ayanāṁśa convention so a future multi-row leak
from any other evidence source is caught rather than silently resolved by the model's own
guess.**

## Sibling Census

LLM-mediated synthesis composers over dated/numeric facts found in this stream's lease:

1. **`platform/src/lib/pipeline/prashna_ask_synthesis.ts`** (this finding) — single
   non-agentic LLM call over pre-fetched evidence. **Confirmed vulnerable** — traced above.
2. **`platform/src/app/api/chat/consult/route.ts`** (consult door) — uses a **live agentic
   tool-calling loop** (`runAgenticLoop`, per `prashna_ask_synthesis.ts`'s own header
   comment contrasting itself: "not the model choosing tools live, unlike consult's
   `runAgenticLoop`"). Consult calls the identical `get_dashas`/`query_dasha_periods`
   capability under the identical B.11+dasha-floor guarantees
   (`consult/route.ts:574–615` references the same `ensureB11WholeChartReadFloor` /
   `ensureDashaContextFloor` guarantees prashna_ask uses). Because the model itself picks
   tool-call params live in this architecture, it is exposed to the **same underlying
   `get_dashas.ts` `ayanamsha_id`-omission gap** whenever the model calls the tool without
   pinning the param — same root tool defect, different calling architecture (live agentic
   vs. pre-fetch-then-synthesize). Not independently reproduced in this pass (out of this
   lane's scope/budget) — flagged as same-root-cause-exposed, not confirmed-live.
3. **`platform/src/app/api/pariprashna/route.ts`** (Paripraśna door) — also agentic/live per
   its `dasha_context_required` floor-forcing logic (`pariprashna/route.ts:462–464`) and its
   own `current_maha_antar` read (`pariprashna/route.ts:603`) mirroring prashna_ask's W6.3
   fix. Same exposure class as consult — not independently reproduced here.
4. **`platform-mcp/src/tools/register_p1_synthesis.ts`** (synth_chart_brief family) —
   grepped for LLM/model-call patterns (`runAdapter`, prompt-building, model_id) and found
   **none** — this composer is deterministic string/data assembly, not LLM-mediated. **Not
   vulnerable to this defect class.**
5. **`platform/src/lib/retrieval/registry/layers/L2_bodha/query_remedies.ts`**
   (bodha_remedies_get) — same check, same result: **no LLM call found, deterministic.**
   **Not vulnerable.**
6. **`platform/src/lib/synthesis/panel/adjudicator.ts` / `member_runner.ts`** and
   **`platform/src/lib/pariprashna/summaries/worker.ts`** — located as other LLM-synthesis
   call sites in this stream's lease but **not individually traced** in this pass (budget);
   flagged for a follow-up lane if the campaign wants full coverage — do not treat as
   cleared.

## Blast Radius

**F-120 and F-121 do NOT share this mechanism — the task brief's own hypothesis is correct,
confirmed, not just presumed.**

`kala_now_get`'s narration (`platform-mcp/src/tools/kala_views/now.ts:1163`) is explicitly
commented in its own source as **"template-over-computed-data — B.10; no generative call"**
— the `thesis`/`reading_prose` strings are built by deterministic string concatenation over
already-computed fields (`thesisParts.push(...)`, `now.ts:1175–1217`), never passed through
an LLM. A wrong or dropped fact in `kala_now_get`'s narration (F-121: "not in a junction"
while one is active) or in `ganita_dasha_periods_get`'s narration (F-120: dropped level-4
sandhi) — this second tool not independently opened in this pass, but it is the identical
narration-serving pattern family (`get_dashas.ts` and its sibling `L1_ganita`/`L3_kala`
serving-layer files, all under the same B.10 "template-over-computed-data" convention
observed directly in `now.ts` and consistent with CLAUDE.md §N.4's "Deterministic-first"
doctrine) — would be a **logic/branch-selection bug in a deterministic string template**
(the template reads the wrong field, or skips a branch it should have entered), not an LLM
inventing or mis-restating prose.

**Conclusion: these are two genuinely different defect mechanisms wearing the same surface
description ("the narration doesn't match reality").** F-93 is an LLM-synthesis
evidence-disambiguation failure compounding an unfixed tool-parameter-default gap. F-120/F-121
are (presumptively, for F-120; confirmed by direct source read, for the F-121 tool) template
logic bugs in deterministic code with no model in the loop. **Do not force a unified fix
across all three** — F-93's fix belongs in `get_dashas.ts`'s default-parameter handling
and/or the synthesis prompt's ayanāṁśa-disambiguation instructions; F-120/F-121's fixes (once
similarly traced) belong in their respective template-construction logic, most likely a
missing branch/field-read, not a prompt change.

## Verdict

**CONFIRMED-LIVE, MECHANISM TRACED TO FILE:LINE.**

- Root cause (tool layer): `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts:15–24`
  — `ayanamsha_id` has no server-side default; omitting it returns all 5 ayanāṁśas; this gap
  is pre-existing, self-documented, and explicitly deferred ("Flagged (not fixed here)").
- Proximate trigger (dispatch layer): `query_dasha_periods` invoked with `invocation_params:
  {}` in this trace — attributed with high confidence (not a captured raw transcript) to the
  LLM planner's own tool-call JSON, since neither `ensureDashaContextFloor`
  (`compiled_floor_adapter.ts:374–390`, gated to `predictive`/`holistic`, and this trace's
  `query_class` was `factual`) nor `compileFloorForPlan`'s `dasha_window` primitive
  (`registry_data.ts:398–408`, would leave literal unfilled template placeholders, not `{}`)
  match the observed empty-params shape.
- Compounding gap (synthesis layer): `platform/src/lib/pipeline/prashna_ask_synthesis.ts:246–301`
  passes the resulting 5-ayanāṁśa evidence to the model verbatim with no canonical-ayanāṁśa
  disambiguation instruction anywhere in the prompt chain (confirmed by grep: zero
  "ayanamsha" occurrences in the base acharya system prompt).
- The narrated dates are not fabricated or distorted — they are the Krishnamurti ayanāṁśa's
  real, correctly-recorded MD row, misattributed to the chart's canonical (Lahiri
  Chitrapaksha) answer.
- F-120/F-121 are a **different mechanism** (deterministic template logic, not LLM
  synthesis) — confirmed directly for the `kala_now_get` narration path; presumed (same
  serving-layer pattern family, not independently opened) for `ganita_dasha_periods_get`.
  This is stated plainly per the brief's own instruction not to force a false unification.
