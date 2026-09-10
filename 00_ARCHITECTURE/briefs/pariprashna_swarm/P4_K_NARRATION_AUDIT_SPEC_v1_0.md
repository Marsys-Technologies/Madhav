---
artifact: P4_K_NARRATION_AUDIT_SPEC
canonical_id: P4_K_NARRATION_AUDIT_SPEC
version: 1.0
status: BUILT — harness built and self-tested (FILLER phase); NOT yet executed
  against any live surface. Execution is post-flip, per PLAN.yaml's `P4-K` row
  ("FILLER(build) / post-flip(run)") and the P4-K charter (§10.2, §10.5).
role: >
  The spec/rubric for P4-K, "the post-six-views narration audit"
  (PARIPRASHNA_IMPLEMENTATION_ROADMAP_v1_0.md G8-G / GAP-18). Names the six
  views this audit exercises, the question frames the harness sends through
  the live conversation door to elicit them, the deterministic checks the
  harness runs, the judgment items it surfaces but never scores, and how a
  finding becomes a DD entry or an in-lane fix.
companion: platform/scripts/probe/p4k_views.ts (the six-view source of
  truth) · p4k_sequence_driver.ts (drives the live sequence) ·
  p4k_narration_analyzer.ts (runs the checks) · p4k_narration_audit.sh (the
  one-command wrapper) · fixtures/p4k/{clean,broken}/ (the §N.8 self-test
  fixtures).
---

# P4-K — the post-six-views narration audit (spec)

## 1 — What "six views" empirically means here

Not invented for this lane. The charter's phrase "post-six-views narration audit"
names a documented, already-shipped concept: the six Kāla (L3) retrieval views
built by the ṢAḌ-DARŚANA campaign.

> `00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/SHAD_DARSHANA_BRIEF_v2_0.md`
> §1: "**Eight tools:** six views (`kala_now_get`, `kala_ahead_get`,
> `kala_elect_get`, `kala_story_get`, `kala_priority_get`, `kala_explain_get`)
> + two capabilities (`kala_upaya_get`, `kala_ritual_get`)."

Confirmed against the live vidhi-compiler registry
(`platform-mcp/src/resources/vidhi/registry_data.ts`, the "ṢAḌ-DARŚANA W5
primitives" block), which labels each primitive `VIEW 1` through `VIEW 6`
explicitly:

| # | View | primitive_id | live_tool | question_frame (verbatim from registry_data.ts) |
|---|---|---|---|---|
| 1 | NOW | `now_read` | `kala_now_get` | "what is my temporal state right now?" |
| 2 | AHEAD | `ahead_read` | `kala_ahead_get` | "what is coming?" |
| 3 | ELECT | `elect_read` | `kala_elect_get` | "when should I…?" |
| 4 | STORY | `story_read` | `kala_story_get` | "what has my life been?" |
| 5 | PRIORITIZE | `priority_read` | `kala_priority_get` | "what matters most right now?" |
| 6 | EXPLAIN | `explain_read` | `kala_explain_get` | "why do you say that?" |

`kala_upaya_get`/`kala_ritual_get` are CAPABILITIES per the same source, not
views — excluded here on purpose, not by oversight.

This audit does **not** test the six MCP tools directly. It tests the SERVED
SURFACE a reader actually experiences: six natural-language questions sent
through the live `/api/pariprashna` conversation door (the same door P3's
flip makes the default for everyone), chained in one thread. Whichever
compiled floor the vidhi planner routes each question to is exactly what a
real reader would get — testing the tools in isolation would miss the entire
class of defect this audit exists for (planner mis-routing, cross-turn
context loss, a wrapper narrating differently than the tool it wraps).

## 2 — The sequence, and why this order

`platform/scripts/probe/p4k_views.ts` is the single source of truth for the
six question frames actually sent. Order is a deliberate reader-movement
path, not the registry's listing order:

1. **NOW** — "What is my temporal state right now — what's active for me at
   this moment?"
2. **AHEAD** — "What is coming for me over the next few months?"
3. **PRIORITIZE** — "Of everything going on in my chart right now, what
   matters most?"
4. **STORY** — "What has my life been like so far, as this chart tells it?"
5. **ELECT** — "When should I start a new business venture?"
6. **EXPLAIN** — "Why do you say that about what's active for me right now —
   what's the reasoning, step by step?" (deliberately back-references turn
   1's claim, operationalizing registry_data.ts's own rule that "every
   served row id pre-authorizes one EXPLAIN hop" as a real cross-turn probe)

NOW → AHEAD → PRIORITIZE mirrors the registry's own "machine-band default...
compiled into every domain deepdive alongside" grouping (these three travel
together in a real deepdive). STORY is the life-arc read a reader reaches
for next; ELECT is the "when should I act" question once they know where
they stand; EXPLAIN closes the loop on a specific earlier claim.

All six turns run in ONE conversation thread (`--conversation-id` chained
turn to turn by the driver) — this is what makes the cross-view questions
meaningful; six independent threads would not be a "sequence" at all.

## 3 — The harness

- `platform/scripts/probe/p4k_views.ts` — the six-view source of truth
  (question frames, primitive_ids, live_tools).
- `platform/scripts/probe/p4k_sequence_driver.ts` — drives the six turns by
  shelling out to the repo's EXISTING auth harness,
  `platform/scripts/probe/ask.ts`, six times, chaining
  `--conversation-id`. **This is not a second auth path** — `ask.ts` alone
  owns the credential seam (mint a fresh Firebase session cookie for
  `probe-service-account`); the driver only reads the JSON transcripts that
  script already writes. Synthetic test chart ONLY
  (`1c826d5a-41cb-4450-b4dc-59d440e5f75a`, `ask.ts`'s own default) — the
  driver does not expose a `--chart-id` flag at all, on purpose.
- `platform/scripts/probe/p4k_narration_analyzer.ts` — reads the driver's
  manifest + the six transcripts, runs the checks in §4, emits a findings
  report (JSON + human-readable) and the judgment items in §5.
- `platform/scripts/probe/p4k_narration_audit.sh` — **the one command**:
  ```
  ./platform/scripts/probe/p4k_narration_audit.sh --service-url <URL>
  ```
  Point `<URL>` at a tagged 0%-traffic revision, the live default surface
  post-flip, or a local dev server. `--self-test` runs the offline
  structural + fixture self-check instead (no network) — this is what
  tonight's BUILD phase actually exercises.

## 4 — Deterministic checks (mechanical, re-runnable, never a judgment call)

| ID | Check | What it reads | Fails when |
|---|---|---|---|
| **D1** | Honest-verdict-non-empty | `block.commit` events, `role` field | A turn completes (`terminal_status: 'ok'`, not partial) with zero non-empty `role: 'verdict'` blocks — the silently-empty-verdict-layer defect (§N.6 item 3 / §N.7 item 6). |
| **D2** | Independent taxonomy-leak scan | Full reader-visible text (prose + every committed block's text) | Any internal identifier reaches the reader: asset-id prefixes (`bo_/ga_/ka_/ph_/mi_/bg_`), DB table prefixes (`bodha_/mimamsa_/kala_/phala_/ganita_/brahma_/chart_/asset_`), primitive_ids (`now_read`, …), live MCP tool names (`kala_now_get`, …), verdict-tier literals (`structural_prior`, `calibrated_provisional`), bare register acronyms (`MSR`/`UCN`/`CGM`/`CDLM`). **Deliberately reimplemented independently of `register_leak_lint.ts`'s own regex table** — an audit that only asks the leak-lint's own code whether it caught something is not an independent check (§N.8). |
| **D3** | Cross-view current-mahādaśā-lord consistency | `prose` of NOW/AHEAD/PRIORITIZE/STORY, regex-extracted "currently in the Mahādaśā of X" | Two or more views name a **different** planet as the current mahādaśā lord. One concrete, checkable instance of "does view N contradict view N-1?" — a *template*, not the general case (see J5). `< 2` extractable mentions ⇒ reported `info`/"insufficient signal", never a false PASS. |
| **D4** | Server self-reported flag surfacing | `flag` SSE events (`code`, `level`) | Any `flag` event at `level: 'error'` (surfaced as `fail`); `level: 'warn'` surfaces as `warn`. **Labeled explicitly as NOT independent** — this is the system grading itself, kept separate from D2's independent check, never conflated with it. |
| **D5** | Server self-reported `citation_gate` grade | `grade` SSE events where `subject === 'citation_gate'` | The gate reports `FAIL` (→ `fail`). **Absence of any such event on a completed turn is itself a `warn` finding** — an unrun/unobserved detector is reported honestly, never silently treated as a pass (§N.8, direct application of the "no detector ⇒ null, not green" rule). |
| **D6** | EXPLAIN-hop `signal_id` overlap | `citation.define` events on the NOW and EXPLAIN turns | Zero overlap between the two turns' cited `signal_id` sets → `warn` (not `fail` — a legitimate EXPLAIN could cite adjacent material; this is a **proxy**, not proof of a wrong explanation; the substantive question is J1). |

Every deterministic check above has been demonstrated capable of failing
**before** its first real pass counted — see §6.

## 5 — Judgment items (never auto-scored — hand to CONDUCTOR/VERIFIER/LLM judge)

These are questions the harness poses and gathers evidence for, but cannot
itself answer, because they require semantic understanding of free text or
comparison against the chart's true underlying facts. **They are never
scored PASS/FAIL by the analyzer — dressing one of these as a deterministic
result is exactly the defect §N.6/§N.7 exist to catch.**

- **J1** — Does the EXPLAIN turn's causal chain (promise → confirmation →
  activation → trigger) actually and correctly explain the NOW claim it was
  asked about, in substance — not just `signal_id` overlap (D6)?
- **J2** — Does any turn's grade/label/verdict read as an invented plausible
  default (the `'elevated'`-on-missing-`direction` / `5.0`-on-zero-`grade`
  defect class, §N.7 item 6) rather than a genuinely computed value?
  Requires cross-referencing the chart's true underlying facts.
- **J3** — Tone/register/valence consistency across the six views: does the
  same underlying life period or fact get narrated with a different
  emotional valence depending on which view frames it?
- **J4** — Catalog-only vs. confirmed-finding flattening (§N.6 item 1): are
  any citations presented as confirmed classical findings when the
  underlying signal is actually a single-pass/catalog-only match?
- **J5** — General cross-view fact contradiction beyond the one tracked
  class (D3 covers ONLY the current mahādaśā lord). Any other fact pair — a
  planet's dignity, a house lord, a yoga's presence/absence — could
  contradict across two views and this harness does not mechanically catch
  it. Read all six transcripts side by side.

## 6 — §N.8 demonstration (the harness shown red, then green)

Per CLAUDE.md §N.8 and the P4-K charter's explicit mandate: fed a
deliberately narration-broken transcript first, observed to fail, before
trusting the clean pass. Fixtures at
`platform/scripts/probe/fixtures/p4k/{broken,clean}/`; reproduce with
`platform/scripts/probe/p4k_narration_audit.sh --self-test`.

The broken fixture plants, on purpose:
- an empty verdict on an `'ok'` turn (PRIORITIZE) → **D1 FAIL**
- three leaked internal tokens in one sentence (`kala_elect_get`,
  `structural_prior`) → **D2 FAIL** ×3
- a server-reported `level: 'error'` flag → **D4 FAIL**
- a server-reported `citation_gate: FAIL` → **D5 FAIL**
- a contradicting current-mahādaśā-lord claim (NOW says Saturn, STORY says
  Jupiter) → **D3 FAIL**
- an EXPLAIN turn citing an unrelated signal → **D6 WARN** (correctly
  non-fatal — see D6's own definition)

Result: **RESULT: FAIL**, 6 independent `fail`-severity findings, one
`warn`. The clean fixture (same six-view shape, no planted defects):
**RESULT: PASS**, all findings `info`. Both runs are reproduced verbatim in
this lane's BUILDER report to the CONDUCTOR — see that report for the exact
console output, not a re-description of it here.

## 7 — Filing a finding

A post-flip run's `fail`-severity deterministic findings and any judgment
item the CONDUCTOR/VERIFIER/LLM judge closes as "yes, this is a real defect"
each become either:
- an **in-lane fix** if narrowly scoped and owned by an already-open lane, or
- a **new DD entry** in `PARIPRASHNA_SWARM_REVIEW_AND_AMENDMENTS_v1_1.md §2`
  if it names a new defect class or crosses lane boundaries.

The analyzer's `report.json` (finding `id`, `check_id`, `severity`, `view`,
`message`, `evidence`) is structured precisely so this step never requires
re-deriving what was found — copy the finding, cite the transcript path, file.

---

*End P4_K_NARRATION_AUDIT_SPEC v1.0. Built by lane p4-k (FILLER build phase);
execution against a live surface is a post-flip act by the CONDUCTOR/VERIFIER,
per PLAN.yaml and the charter's own §10.2/§10.5 phasing.*
