# F-93 SPEC (TIER2-HONESTY) — prashna_ask MD/AD boundary-date narration defect

Stream S4 VĀCA · Stage S SPEC, from DIAGNOSIS-COMPLETE (`DIAGNOSIS.md`).
`exemplar_for: [F-120, F-121]` — per DIAGNOSIS's own Blast Radius section, F-120/F-121 do
**not** share this mechanism (confirmed directly for F-121, presumed-not-independently-opened
for F-120); this spec does not attempt a unified fix and says so again below.

## Source-file spot-check (this session, before writing this spec)

Read the actual cited files, not just DIAGNOSIS's prose, per the Stage S brief's instruction
to confirm the mechanism before writing. Confirmed directly:

- `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts:15–26` (header) and
  `:127–138` (`input_schema.ayanamsha_id.description`) — both self-document the exact gap
  DIAGNOSIS traced, in the DIAGNOSIS's own quoted words.
- `:210–213` — `if (args.ayanamsha_id) { sql += ' AND ayanamsha_id = $N' ... }` — confirmed
  there is no `else` branch and no default; omitting the arg genuinely applies no filter.
  Contrast with the `system` facet immediately below (`:227–242`), which DOES have a
  default-else branch (`systemInput` falls back to `'vimshottari'`) — the exact asymmetry
  the header comment describes.
- `:545–547` — a **second**, independent SQL block (`levels_available` sub-query) has its
  own separate `if (args.ayanamsha_id)` check with no default either. Not mentioned in
  DIAGNOSIS (which focused on the row-fetch path, not this secondary meta-field query) —
  found during this spec's file read. See Files to change item 1.
- `platform/src/lib/pipeline/prashna_ask_synthesis.ts:88–105` (`NO_LIVE_TOOLS_OVERRIDE`) and
  `:237–282` (`formatEvidenceBlock`) — confirmed zero mention of "ayanamsha" anywhere in
  either, and confirmed `formatEvidenceBlock` serializes `e.bundle.results` verbatim with no
  per-row filtering — exactly as DIAGNOSIS Step C describes.
- `platform/src/lib/pipeline/compiled_floor_adapter.ts:374–390` (`ensureDashaContextFloor`)
  — confirmed gated to `predictive`/`holistic` (`:376`), confirmed this trace's `query_class`
  was `factual` so this guarantee could not have produced the observed `{}` call. Also
  confirmed (not in DIAGNOSIS): even when this guarantee DOES fire, its own injected params
  (`:381`, `{ system: 'vimshottari', level: 2 }`) **also omit `ayanamsha_id`** — a second,
  independent exposure of the same root gap, inert only because this specific trace's
  `query_class` didn't route through it.
- `platform-mcp/src/tools/register_p1_synthesis.ts` — grepped for `runAdapter`, `model_id`,
  `prompt` (case-insensitive): **zero matches**. Confirms DIAGNOSIS sibling-census item 4
  ("not vulnerable, no LLM call") independently, and confirms this lane's files are entirely
  disjoint from the file F-135 holds under an S5 lease — see Dependencies below.

## Root-cause statement

`get_dashas.ts`'s `ayanamsha_id` facet has no server-side default (unlike `system`/`level`/
`window`, which all default), so any caller that omits it — confirmed here to be the LLM
planner's own tool-call JSON, not a floor-guarantee path — receives all 5 ayanāṁśas' rows for
the same dasha slot with no signal of which is canonical, and the `prashna_ask_synthesis.ts`
prompt chain that later serializes this evidence verbatim into the LLM's context contains no
instruction telling the model which ayanāṁśa is this project's canonical one, so the model
picks one (here, Krishnamurti) and narrates its dates as the chart's single unqualified answer.

## Files to change

**1. `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts`** — close the root
gap at the tool-dispatch layer, exactly as the file's own header (`:20–24`) already proposes
("ALWAYS pass `ayanamsha_id: "lahiri_chitrapaksha"`... a future wave should consider defaulting
`ayanamsha_id` server-side the same way `system` defaults to vimshottari").

- Import `DEFAULT_AYANAMSHA` from `../../constants` (`platform/src/lib/retrieval/registry/
  constants.ts:2`, value `'lahiri_chitrapaksha'`) — the exact pattern three sibling
  `L1_ganita` files already use for this same constant (`get_chart_snapshot.ts:35,152`,
  `get_strength.ts:27,121`, `get_positions.ts:38,150`). Do **not** hardcode a new literal
  `'lahiri_chitrapaksha'` string in this file — §N.7 item 3 ("no wrapper-local constant may
  shadow a project value").
- At the top of `handler` (near `:203–206`, alongside `chartId`/`limit`/`offset`), resolve
  once: `const ayanamshaId = (args.ayanamsha_id as string | undefined) ?? DEFAULT_AYANAMSHA`.
- Replace the `:210–213` block's raw `args.ayanamsha_id` reads with this resolved
  `ayanamshaId` (the filter now always applies — the `if` becomes unconditional since
  `ayanamshaId` is never undefined).
- **Also** update the `:545–547` `levels_available` sub-query's own `if (args.ayanamsha_id)`
  check to use the same resolved `ayanamshaId` (found during this spec's file read, not in
  DIAGNOSIS — see spot-check above). If only the row-fetch path is patched, `levels_available`
  silently reverts to reporting the max level across all 5 ayanāṁśas while `rows` is scoped to
  one — a fresh, narrower version of exactly the "declared-but-silently-unfiltered" defect this
  fix is closing, introduced by an incomplete patch. Both SQL-building sites must read the same
  resolved variable.
- Minor, non-blocking (does not gate the exit test): echo the applied ayanāṁśa in
  `facets_applied` (`:565–573`), e.g. `ayanamsha: ayanamshaId`, matching this file's own
  established convention that every applied filter is echoed back (`:270–273`'s F-0471/0485
  comment: "a requested date/window must NEVER be silently dropped"; the same logic already
  covers `system`, `level`, `window`, `date_filter`, `fields` but not `ayanamsha`). Useful for
  API-level debugging; not load-bearing for the LLM-visible fix, since `formatEvidenceBlock`
  (below) serializes the row array, not the wrapping `content.facets_applied` object — confirmed
  by DIAGNOSIS Step A quoting `bundle.results` as the `rows` array directly, not the envelope.

**2. `platform/src/lib/pipeline/prashna_ask_synthesis.ts`** — defense in depth, per DIAGNOSIS's
own two-part fix conclusion ("(2) ... teach the synthesis prompt the project's canonical-
ayanāṁśa convention so a future multi-row leak from any other evidence source is caught rather
than silently resolved by the model's own guess").

- Append a new paragraph to `NO_LIVE_TOOLS_OVERRIDE` (`:90–105`), after the existing
  gap-disclosure paragraph, instructing: this project's canonical ayanāṁśa is
  `lahiri_chitrapaksha`; if `<evidence>` for any tool contains multiple rows for what is
  otherwise the same fact (same lord/level/system) tagged with different `ayanamsha_id`
  values, cite ONLY the `lahiri_chitrapaksha` row as the chart's answer, and if a
  non-canonical-ayanāṁśa row is mentioned or compared at all, it must be explicitly labeled
  by its ayanāṁśa name rather than presented as the single unqualified answer.
- This is explicitly a **second, independent layer** — item 1 above is expected to make the
  multi-row leak structurally impossible for `get_dashas.ts` specifically (the tool now
  returns one row unless a caller deliberately asks for `ayanamsha_id="all"` or similar), but
  this prompt instruction protects against the same class of leak from any *other* evidence
  source this call's evidence block ever serializes, present or future — DIAGNOSIS's own
  framing, not a new judgment call made here.

**No change to `chart_dashas`, any migration, or `register_p1_synthesis.ts`.**

## Exit test

Two existing test files, each already covering this tool/module — no new test file needed
(both already have the right scaffolding and mocking in place).

**A. `platform/src/lib/retrieval/registry/layers/L1_ganita/__tests__/get_dashas.integration.test.ts`**
(live-DB integration test, run with `INTEGRATION=true`) — primary, deterministic exit test for
the root-cause fix.

- The existing test at lines 53–75, titled `REGRESSION: omitting ayanamsha_id silently
  returns one row PER AYANAMSHA and busts the gate (pins the documented failure mode)`,
  currently asserts `rows.length` **greater than** 1 and payload bytes **greater than**
  1024 — i.e. it pins today's defective behavior as expected. **This assertion inverts
  after the fix and must be rewritten in the same commit**, not left as a follow-up (see
  Dependencies below — otherwise CI breaks on merge). Rewritten to assert, for both
  `NATIVE_CHART_ID` and `ABHINANDAN_CHART_ID` (same loop structure the file already uses):
  - `rows.length === 1` (not `> 1`)
  - `rows[0].ayanamsha_id === 'lahiri_chitrapaksha'`
  - payload bytes `<= 1024` (mirrors the sibling "COMPLETE facet set" test's own assertion
    two tests above it — omitting the arg now produces the SAME shape as passing it
    explicitly, which is the whole point of the fix)
  - Rename the test title to something like `omitting ayanamsha_id now defaults to
    lahiri_chitrapaksha (server-side default closes the documented failure mode)`.
- **New assertion** (not in the existing test, needed to pin the exact live-reproduction
  values DIAGNOSIS captured): for `NATIVE_CHART_ID` specifically, with `system: 'vimshottari',
  level: 1, as_of_date: today` and `ayanamsha_id` omitted, assert `rows[0].start_date ===
  '2010-08-18'` and `rows[0].end_date === '2027-08-18'` — the exact Lahiri MD row DIAGNOSIS's
  live repro pinned as the `two_pass_verified` canonical answer, and explicitly NOT
  `'2010-07-07'`/`'2027-07-07'` (the Krishnamurti row the defect narrated). This is the
  assertion that would fail today (wrong/absent row) and is the one a wrong-but-present
  default (e.g. accidentally defaulting to `'krishnamurti'` instead of
  `'lahiri_chitrapaksha'`) would also fail — not just a field-presence check.
- **New test**: `levels_available` consistency — call with `ayanamsha_id` omitted vs. explicit
  `ayanamsha_id: 'lahiri_chitrapaksha'`, assert `content.levels_available` is IDENTICAL between
  the two calls. This is the regression guard for the `:545–547` sub-query fix (Files to
  change item 1) — without it, the two SQL sites could silently drift back out of sync in a
  future edit and nothing would catch it.

**B. `platform/src/lib/pipeline/__tests__/prashna_ask_synthesis.test.ts`** — defense-in-depth
exit test for the prompt-layer fix. Follows the file's own established pattern (already used
at lines 93–95 for the "do not attempt to call" / "acharya" assertions) of reading
`mockRunAdapter.mock.calls[0][0].systemPrompt` rather than asserting on any LLM output text —
this is a deterministic precondition on what reaches the model, not a claim about what the
(non-deterministic) model does with it, per the Stage S brief's own guidance for LLM-synthesis
defects.

- New test: call `synthesizeReading` with a `baseInput()`-shaped fixture, assert
  `req.systemPrompt` contains the literal substring `lahiri_chitrapaksha` in a canonical-
  ayanāṁśa-declaring sentence (e.g. match `/canonical ayan[aā]ṁśa is.*lahiri_chitrapaksha/i`
  or an equivalent anchored regex — not a bare substring match on `'lahiri_chitrapaksha'`
  alone, since that string can appear incidentally elsewhere; the regex must anchor to the
  instructional sentence so a hollow/rephrased instruction that drops the actual guidance
  still fails the check).
- This test fails today (no such instruction exists anywhere in `NO_LIVE_TOOLS_OVERRIDE`,
  confirmed by this session's own grep) and passes once item 2's paragraph is added.

## Sibling sites covered

From DIAGNOSIS's Sibling Census (all 6 items addressed, none silently dropped):

1. **`prashna_ask_synthesis.ts`** — this finding. Fixed directly (Files to change item 2).
2. **`platform/src/app/api/chat/consult/route.ts`** (consult door, live agentic loop) —
   DIAGNOSIS flagged as same-root-cause-exposed, not independently reproduced. **Covered
   structurally, not independently exercised**: because the fix lands at the tool-dispatch
   layer (`get_dashas.ts` itself, item 1), ANY caller of this tool that omits `ayanamsha_id`
   — regardless of whether the model chose the call live (consult) or it was pre-fetched
   (prashna_ask) — now gets the same one-row-per-slot default. No consult-specific test is
   added in this lane (matches DIAGNOSIS's own scope/budget statement); the tool-layer fix
   closes this exposure by construction, not by a parallel patch.
3. **`platform/src/app/api/pariprashna/route.ts`** (Paripraśna door) — same as item 2:
   structurally covered by the tool-layer fix, not independently exercised in this lane.
4. **`platform-mcp/src/tools/register_p1_synthesis.ts`** — re-confirmed **not vulnerable**
   (independent grep this session found zero LLM/prompt call sites). No fix, no test. Also
   confirms no file-lease conflict with S5's hold on this file (see Dependencies).
5. **`platform/src/lib/retrieval/registry/layers/L2_bodha/query_remedies.ts`**
   (`bodha_remedies_get`) — DIAGNOSIS confirmed no LLM call, not vulnerable. Not re-verified
   independently this session (DIAGNOSIS's own direct-read finding is not in dispute); no
   fix, no test.
6. **`platform/src/lib/synthesis/panel/adjudicator.ts` / `member_runner.ts`** and
   **`platform/src/lib/pariprashna/summaries/worker.ts`** — DIAGNOSIS explicitly left these
   untraced (budget) and flagged them for a follow-up lane, "do not treat as cleared." This
   spec does not clear them either — carried forward as open, not silently dropped from this
   spec's scope. Out of scope for F-93's Stage B.

**Additional exposure found during this spec's own file read, not in DIAGNOSIS's census**
(both are non-LLM call sites of the same underlying tool gap, structurally closed by item 1,
same reasoning as items 2–3 above — flagged for completeness, no separate fix needed):

7. `platform/src/lib/pipeline/compiled_floor_adapter.ts:381` (`ensureDashaContextFloor`'s own
   injected `query_dasha_periods` call) omits `ayanamsha_id`.
8. `platform/src/lib/synthesis/b11_floor.ts:61` (`current_dasha` pattern's `query_dasha_periods`
   params) and `platform/src/lib/mcp/bundle_adapters.ts:379` (`DASHA` case params) both omit
   `ayanamsha_id` too.

## Recurrence guard

Per §N.7/§N.8: a guard must detect the defect class (a wrong/hardcoded value silently
substituted), not just field presence.

- **Tool layer**: the real guard is the Exit-test-A assertion on the *exact* Lahiri dates
  (`2010-08-18`/`2027-08-18`) and the *exact* `ayanamsha_id` string, not merely `rows.length
  === 1`. A row-count-only check would pass even if the default were silently wrong (e.g.
  defaulted to `'krishnamurti'` by a typo, or to some other single ayanāṁśa) — it would still
  return exactly one row, just the wrong one. The dates/ayanāṁśa-value assertions are what
  actually catch a wrong-but-present default, which is the specific defect class this
  finding is about (a plausible-looking value silently substituted for the correct one).
- **Sub-query drift**: the new `levels_available` consistency test (Exit test A) is the guard
  against the two SQL sites (`:210–213` and `:545–547`) drifting back out of sync in a future
  edit — a defect class this spec's own file read caught once already (DIAGNOSIS's mechanism
  trace only covered the row-fetch path).
- **Prompt layer**: the real guard is the anchored regex on the instructional sentence
  (Exit-test-B), not a bare substring match on `lahiri_chitrapaksha` — a prompt edit that
  keeps the string present but drops or waters down the actual instruction (e.g. rephrases it
  into something that no longer tells the model to PREFER that row) would still pass a bare
  substring check but fails the anchored one.
- **Exemplar-unification, respected not re-litigated**: DIAGNOSIS's Blast Radius section
  already determined F-120/F-121 do not share this mechanism — F-121 confirmed directly
  (`kala_now_get`'s narration is deterministic string concatenation, "B.10; no generative
  call," `now.ts:1163`), F-120 presumed same serving-layer template-bug pattern family, not
  independently opened. This spec does not build a unified recurrence guard across all three
  findings — a guard against "wrong ayanāṁśa/date silently narrated by an LLM with ambiguous
  evidence" (this spec's two guards above) would not catch "a deterministic template skips a
  branch or reads the wrong field" (F-120/F-121's presumed mechanism), and forcing one would
  produce a guard that's either too narrow to help F-120/F-121 or too generic to actually
  detect either defect precisely — exactly what §N.7/§N.8 warn against. F-120/F-121's own
  recurrence guards belong in their own future specs, once traced to file:line the same way
  this one was.

## Dependencies and rollback

- **No lease conflict.** `prashna_ask` (this tool) does NOT touch
  `platform-mcp/src/tools/register_p1_synthesis.ts` — verified independently this session by
  direct grep (zero `runAdapter`/`model_id`/prompt-pattern matches in that file) in addition
  to DIAGNOSIS's own finding. F-93's full file set (`get_dashas.ts`,
  `prashna_ask_synthesis.ts`, and their two test files) is entirely disjoint from the file
  F-135 holds under S5's `ordered_handoff_pending` lease. **This lane is not blocked by S5**
  and may proceed to Stage B without waiting for `PAR-register_p1_synthesis-RELEASE`.
- **Caller-impact check on the `get_dashas.ts` default** (the tool's own header explicitly
  flags this risk: "a silent default would change existing multi-ayanamsha callers'
  results"). Repo-wide grep this session for all non-test callers of `query_dasha_periods` /
  `get_dashas` found: two disciplined call sites already explicitly resolve and pass
  `ayanamsha_id` before calling (`register_d9_judgment.ts`, `register_d10_pact.ts` — both
  default to `'lahiri_chitrapaksha'` themselves at the call site, working around the exact
  gap this spec closes at the source) — unaffected by the new default, since they never omit
  the arg. Two further sites (`compiled_floor_adapter.ts:381`, `b11_floor.ts:61`,
  `bundle_adapters.ts:379`) currently omit it and would themselves benefit from — not be
  broken by — the fix (see Sibling sites items 7–8). **No caller was found that relies on the
  "omit → all 5 ayanāṁśas" behavior as a deliberate multi-ayanāṁśa query shape.** This
  resolves the header's own flagged caveat rather than overriding it without checking.
- **Existing-test conflict, must land atomically.** `get_dashas.integration.test.ts`'s current
  "REGRESSION: omitting ayanamsha_id..." test pins today's defective behavior and will fail
  the moment the production fix lands. Stage B must include the test rewrite (Exit test A) in
  the SAME commit as the `get_dashas.ts` change — not a follow-up PR — or CI breaks on merge.
- **Rollback**: single logical change across two source files + two test files, purely
  additive default-fill and a prompt-string addition — no migration, no schema change,
  `chart_dashas` itself untouched (serving-layer read path only). A `git revert` of the one
  commit fully restores prior (defective) behavior, including the test files reverting to
  their pre-fix assertions in lockstep since they're part of the same commit.

## Sub-claim coverage table (from DIAGNOSIS)

| DIAGNOSIS element | Spec element that closes it |
|---|---|
| Claim (a): MD lord = Mercury (correct) | Unaffected — no fix needed; lord identification was never wrong. |
| Claim (b): MD dates wrong — confirmed a wholesale wrong-ayanāṁśa row, not a distortion | Files to change item 1 (tool default) + Exit test A's exact-date assertion. |
| Claim (c): AD lord (Saturn) — independently corroborated correct, not evaluable from this repro | Unaffected — no fix needed. |
| Claim (d): AD end-date matches Krishnamurti MD end date, not fabricated | Files to change item 1 — once only one ayanāṁśa's rows are ever fetched, no other ayanāṁśa's date can leak into any sentence, AD or MD. |
| Mechanism Step A: `query_dasha_periods` dispatched with `params: {}` | Files to change item 1 (the fix that matters regardless of which layer chose the empty params — planner, floor guarantee, or agentic loop). |
| Mechanism Step B: `get_dashas.ts`'s pre-existing, self-documented, deliberately-deferred `ayanamsha_id` default gap | Files to change item 1 — the gap the header literally proposed closing. |
| Mechanism Step C: no disambiguation instruction anywhere in the synthesis prompt chain | Files to change item 2 + Exit test B. |
| "Which of the task's three options" — hybrid of (a)/(b), not a pure prompt fix or pure plumbing fix | Both Files-to-change items land together — neither alone is DIAGNOSIS's stated fix; this spec keeps them as one coupled change, matching DIAGNOSIS's own conclusion ("(1) ... AND (2) ..."). |
| Blast Radius: F-120/F-121 are a different, deterministic-template mechanism — do not force a unified fix | Recurrence guard section, explicitly not unified; Sibling sites section scopes this spec to F-93's own mechanism only. |
| Sibling census items 1–6 | Sibling sites covered section, one row per item, including the two explicitly-not-cleared items (6). |
| Attribution caveat: the `{}` call is high-confidence-by-elimination, not a captured planner transcript | Not a spec element to close — this is an evidentiary caveat about how the defect was diagnosed, not a residual claim the fix needs to separately address. The fix (item 1) closes the gap regardless of which exact layer produced the empty params, so this caveat does not weaken the spec. |

## PAR-R-7 check

No ESCALATE-TO-PRATINIDHI raised for this lane. The candidate judgment call — whether to add
the `ayanamsha_id` server-side default despite the tool's own header caveat about changing
existing callers' results — was already decided by DIAGNOSIS (which quotes the header's own
proposed remediation as the fix direction), and this spec's own repo-wide caller check (see
Dependencies) found no caller that would actually break, resolving the caveat on the merits
rather than requiring a policy call. Everything else in this spec (which file/line, which
constant, which test file, wording of the prompt instruction) is an ordinary code-level
authoring choice, not a reserved design decision.

## Verdict

Stage S complete. No Stage-R prior return on this lane (first submission). Awaiting independent
Stage R review before Stage B. No lease block — this lane may proceed to Stage B as soon as
Stage R approves, independent of S5's `register_p1_synthesis.ts` release gate that blocks F-135.
