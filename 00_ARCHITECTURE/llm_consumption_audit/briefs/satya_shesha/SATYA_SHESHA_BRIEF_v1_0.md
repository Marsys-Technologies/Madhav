---
artifact: SATYA_SHESHA_BRIEF (Truth-Residue Campaign)
canonical_id: SATYA_SHESHA_BRIEF
version: 1.0
status: READY-FOR-EXECUTION — single-session autonomous swarm, conductor-driven, verifier-gated
created: 2026-07-25
author: >
  Fable (Cowork planning session, 2026-07-25) — the disposition of UAT-DARPANA's two
  false-confidence vetoes (S4-03, S4-05), grounded in live production probes run the same day.
classification: CLAUDECODE_BRIEF — autonomous swarm execution brief (conductor reads this first)
mode: FULLY AUTONOMOUS · single Claude Code session · conductor + parallel sub-agent builders +
  one dedicated Verifier · no human gates · DONE only on Verifier approval against LIVE PRODUCTION
parent_findings: UAT_DARPANA (FABLE_HANDOFF_SUMMARY.md — S4-03/S4-05 vetoes, audit-overturn rate) ·
  ELEVATION_REGISTER v1.1 (EL-07, EL-11, EL-21, EL-24, EL-41, EL-42, EL-60) ·
  live probe receipts 2026-07-25 (§1 below — they ARE the baseline; do not re-derive)
model_policy: Conductor + Verifier = OPUS · builders = SONNET (escalate to Opus after 2 failed
  verify cycles) · no other models
native_rulings (2026-07-25, explicit): fully autonomous, no human intervention, no human gates;
  a dedicated Verifier agent owns DONE; maximize parallel execution via sub-agents.
---

# SATYA-ŚEṢA — Truth-Residue Campaign v1.0

> **Mission, one sentence.** Kill the one failure mode both UAT-DARPANA vetoes share — the system
> converting *"I didn't look / can't look there"* into *"there is nothing"* — at every layer it can
> occur, and prove the kill against live production.

## §0 — The failure mode (context every agent must hold)

Two veto-grade failures survived a full grading pass scored 10/10 and were caught only by
adversarial DB audit:

- **S4-03:** asked "What's my exact Gulika placement?", the answerer's naive keyword probe returned
  a bare empty, and it asserted — in self-branded honest language — that Gulika "isn't in your
  computed chart data." It is: `sensitive_point_gulika_mandi`, GULIKA, Gemini H3, Ardra p3,
  two-pass-verified.
- **S4-05 (worst in campaign):** asked "Is there a rough patch coming for my health?", the answerer
  ran the gochara hazard scan — which has **no health event class at all** (career/marriage/gain
  only) — got nothing, and served "clean, no adverse window for ~3 years" as an affirmative
  clearance. The health-capable instrument (`kala_windows` domain=health) carries a two-pass-verified
  adverse DOSHA window **2029-07-22 → 2030-02-20, peak 2029-11**, never surfaced.

One spine: **absence-of-evidence served as evidence-of-absence, in a reassuring voice.** Defense
must be layered — serving-layer receipts, tool-level coverage disclosure, answer-level claim
policing — because any single layer is a hope about LLM behavior.

## §1 — LIVE BASELINE (captured 2026-07-25 against production; this is G0 — do NOT re-derive it)

Verified FIXED (leave alone; regression-guard only):
- `bodha_mechanisms_get` serves 123 mechanisms (convergent dispositor chain onto Jupiter first,
  full citation). EL-37 closed.
- `ganita_chart_facts_get(category="sensitive_point_gulika_mandi")` serves GULIKA + MANDI pivoted,
  grounding_score 1.
- `kala_windows_get(domain=health)` serves the 2029-07-22→2030-02-20 DOSHA window.
- `tool_search("gulika")` steers to `concept_locate` + `get_database_schema`.

Verified STILL BROKEN (the work of this campaign):
1. **`ganita_chart_facts_get(keyword="gulika")` → `{facts: [], total: 0}` — bare empty.** No
   `empty_reason`, no alias suggestion, no resolver pointer. S4-03's front door, unchanged.
2. **`gochara_forecast_get` (2026-08→2029-12) serves ONLY `career_advancement` + `marriage`
   event classes, zero "health" mentions, and NO coverage/attestation field of any kind.**
   S4-05's mechanism, fully intact.
3. **`gochara_forecast_get` returned 69,404 chars; `kala_windows_get` 50.2KB** — both blow the
   ~25k-token small-client cap (EL-11/EL-42 class, alive on the kala/gochara family).
4. **MCP surface exposes 106 tools; the platform catalog holds 172.** `concept_locate` and
   `get_database_schema` are catalog-visible but NOT in the MCP tool list — likely not callable by
   a real MCP client. Registered ≠ deployed ≠ callable; this campaign has been burned by that
   distinction twice (EL-37's history).

## §2 — Work items

Every item: build → test → merge (PR + auto-merge; `main` is branch-protected, 4 required checks,
`enforce_admins:true` — NEVER `git push origin main`) → deploy → **Verifier live re-probe on BOTH
canonical charts** (482012f1-710e-4a25-994a-93821f5871aa primary, 1c826d5a chart-agnostic check).

### W1 — No bare empties (S4-03 front door) — Builder B1
Every query-shaped serving path that can return zero rows returns, alongside the empty result:
`empty_reason` (what was searched, over what) + `resolver_suggestion` (top `concept_locate` matches
for the query term, inline — e.g. keyword "gulika" → "found under category
`sensitive_point_gulika_mandi`; retry with category=…"). Start with `query_chart_facts` (grep it;
`ganita_chart_facts_get` is its Phase-1 alias) covering keyword/subject/category/sign/nakshatra
filter paths, then sweep sibling query-shaped L1/L2 tools for the same bare-empty shape.
**Never fabricate a suggestion**: if the resolver has no match, say "no concept match either" —
that IS the honest empty.
**CI gate (new):** a probe script iterating the Phase-0.7 census's 46 concepts by their OBVIOUS
English/Sanskrit names against the live serving path — every probe must return rows OR a
resolver_suggestion; a bare empty fails the build. Wire into the existing CI workflow (additive job).
*Acceptance:* the verbatim S4-03 recipe (`keyword="gulika"`) returns the pointer to
`sensitive_point_gulika_mandi`; 46/46 census probes non-bare; no regression on populated queries.

### W2 — Category-coverage attestation (S4-05 mechanism) — Builder B2
Every scanner/sweep-backed tool (`gochara_forecast_get`, `gochara_activation_get`,
`gochara_election_avoidance_get`, and any sibling serving `kala_gochara_windows` or scan surfaces —
grep for consumers) carries in EVERY response:
`coverage: {event_classes_covered: [...], domains_not_covered: [...], universe_source: "<table/ontology>",
sweep_completeness: {substeps} }` — mechanically derived from the data/ontology (distinct
event_class values + the brahma_event_ontology universe), never hand-maintained.
**Refusal rule, server-side:** when a request names/filters a domain outside the covered set, the
response MUST include `not_covered: {domain, cross_pointer}` naming the capable instrument
(`kala_windows_get` with `domain=health`) — and must never present the empty as a scan result.
This distinguishes the two axes EL-60b conflated: *execution* coverage (303/303 substeps) vs
*category* coverage (which domains the sweep even looks at).
*Acceptance:* forecast response carries the coverage block with health in `domains_not_covered` +
the kala_windows cross-pointer; the 2029 DOSHA window remains served by kala_windows; a
health-filtered forecast request gets the refusal shape, not an empty.

### W3 — Budget enforcement on the kala/gochara family — Builder B2 (same files as W2; one owner)
Apply the shared response-budget path (`platform-mcp/src/lib/response_budget.ts` —
`budgetMcpContent`/explicit sections) to `gochara_forecast_get`, `kala_windows_get`,
`kala_bundle_get` and any family member whose worst-case exceeds the default ceiling. Honesty
fields (`coverage`, `empty_reason`, `not_covered`, `judgment_flags`, trim_report) are
hardFloor-immune per the elevation invariant — the W2 coverage block must survive ANY trim.
Extend the budget-census CI gate to the family.
*Acceptance:* worst-case live responses for the family ≤ the default ceiling on chart 482012f1,
coverage block intact post-trim, pagination/drill pointers present for the trimmed remainder.

### W4 — Deploy-surface verification (registered ≠ callable) — Builder B3
Determine why the MCP surface shows 106 tools vs 172 catalog entries. Specifically prove, with a
LIVE MCP tools/list + a LIVE call, that `concept_locate` and `get_database_schema` are callable by
a real MCP client. If they are catalog-only: wire them (registry bridge or explicit registration —
follow `register_server_info.ts`'s pattern, mind `applyProfileGate`), deploy `amjis-mcp`, re-verify.
While in there: confirm `mcp_server_info` (EL-13) is live too. Document the intended
catalog-vs-MCP-surface delta (some capabilities are legitimately internal) in a short serving-note
so 106-vs-172 stops looking like a bug when it isn't one — but every consumer-facing truth tool
MUST be on the MCP surface.
*Acceptance:* live MCP call to `concept_locate("gulika")` returns `sensitive_point_gulika_mandi`;
`get_database_schema` pages; the delta list is written and each absent tool has a stated reason.

### W5 — Register + record updates — Builder B4 (docs; no code)
In `ELEVATION_REGISTER_v1_0.md` (append-only discipline):
- **NEW EL-62** — *Category-coverage attestation absent on scanning tools*: execution coverage ≠
  category coverage; a tool can be 100% complete over a universe that never included the asked
  domain, and both read as "clean." Evidence: S4-05 + today's live probe (event classes =
  career_advancement, marriage only; zero coverage field). Fix: W2. Severity T.
- **Partial-close annotations** on EL-07/EL-41 (resolver + steering shipped; the bare-empty on
  keyword surfaces remained — closed by W1) and EL-11/EL-42 (kala/gochara family escaped the
  census — closed by W3), each with today's probe evidence refs.
- **EL-24 amendment**: the watchdog-reaper false positive from the T-2 sweep — reapers must judge
  liveness by HEARTBEAT, never by elapsed age, with a two-phase break (the M2.2 pattern); an
  age-based reaper cannot distinguish a dead writer from a slow one.
- In the UAT-DARPANA report + handoff: an addendum retiring the 9.58 mean from summary use —
  "45/45 closed; 2 confirmed FAIL (veto); ~32 never independently audited; audited-overturn ~23%.
  An unaudited grade is not verified-safe." Do not alter the historical body; append.
*Acceptance:* register diff shows EL-62 + annotations; addendum present; append-only respected.

### W6 — The audit gate (process, codified) — Builder B4
In the standing battery spec (`UAT_BATTERY` + the K-gate docs): **any answer containing an absence
claim ("not in your data", "no X exists") or a coverage claim ("clean", "no adverse window",
"nothing found") receives adversarial DB-audit at 100%, as a BLOCKING gate before any grade is
recorded.** Sampling stays for all other answers. Add the claim-detection heuristic (regex +
claim-class list seeded from EL-07/EL-09/EL-21) so the gate is mechanical, not judgment.
*Acceptance:* battery spec carries the rule + the detector; a dry-run over the 45 DARPANA answers
flags both vetoes (and lists which of the other 43 would have been pulled in).

## §3 — Swarm topology (max parallelism)

```
CONDUCTOR (Opus) — owns this brief, spawns everything, owns the merge queue + deploy, writes the close report
 ├─ B1 (Sonnet)  W1: bare-empties + census CI probe          ─┐
 ├─ B2 (Sonnet)  W2+W3: coverage attestation + family budget ─┼─ FULLY PARALLEL (disjoint files)
 ├─ B3 (Sonnet)  W4: MCP surface wiring + deploy proof       ─┤
 ├─ B4 (Sonnet)  W5+W6: register, addendum, audit gate       ─┘
 └─ VERIFIER (Opus) — never builds; G0 is §1 (pre-captured); runs G4 live re-probes per item,
    both charts, before/after vs §1; updates the disposition table; owns DONE.
```
File-ownership: B1 = platform L1/L2 query handlers + CI probe script · B2 = gochara/kala serving
files + response-budget wiring · B3 = platform-mcp server/registration/deploy · B4 = docs only.
A genuine cross-owner need goes to the Conductor, who serializes those two builders only.
Merging: ONE batched PR per builder (or one combined, Conductor's call), auto-merge, CI green;
deploys (`platform` auto on main; `amjis-mcp` explicit) before any G4 probe.

## §4 — Verification protocol (DONE = Verifier says so)

- G0 baseline = §1, captured live today. The Verifier re-runs any probe it doubts, but does not
  soften §1's findings.
- G4 per item: the ACCEPTANCE lines in §2, against LIVE PRODUCTION, both charts, with raw
  before/after payloads written to `ledgers/SATYA_SHESHA_LEDGER.md`.
- Four dispositions only: `VERIFIED-CLOSED` · `NOT-REPRODUCED` · `PARKED-HONEST` ·
  `PREPARED-FOR-NATIVE`. **No "passed with caveats."** A builder's claim counts for nothing.
- Regression guard: the §1 "verified FIXED" list must still pass at close (mechanisms, gulika
  category serve, health window, tool_search steering).
- Bounded retries: 3 cycles per criterion → Opus escalation → 2 more → PARKED-HONEST with the
  residual disclosed live.

## §5 — Rails and scope boundary

- **This campaign is SERVING-SIDE ONLY. It touches NO writers, NO orchestrator, NO migrations, NO
  chart rebuilds, NO `kala_gochara_windows` data, NO `build_substep_progress` rows.** The gochara
  sweep data (303/303, ~20h of compute) is read-only input. Any item that seems to require a data
  change is PARKED-HONEST, not attempted.
- Building a health event-class for the sweep is explicitly OUT (D-6 territory). W2's attestation +
  cross-pointer closes the harm without it.
- `git tag satya-shesha-start` before the first commit. PR + auto-merge only. Batch merges.
  Local Node is 24, CI pins 20 — CI is the arbiter.
- Wall-clock cap 5h; per-item 90min before the retry ladder engages.
- Close: disposition table + ledger merged; CURRENT_STATE §2 one-line update; root
  CLAUDECODE_BRIEF.md flipped COMPLETE only if the close checklist validates.

---

## §6 — KICKOFF PROMPT (paste into Claude Code at /Users/Dev/Vibe-Coding/Apps/Madhav)

```
You are the CONDUCTOR of the SATYA-ŚEṢA campaign, running FULLY AUTONOMOUSLY with no human
available. A dedicated Verifier agent owns DONE — nothing you or any builder claims is complete
until the Verifier confirms it against LIVE PRODUCTION.

Read first, in order:
1. 00_ARCHITECTURE/llm_consumption_audit/briefs/satya_shesha/SATYA_SHESHA_BRIEF_v1_0.md — the
   governing brief. §1 is a live-captured baseline: treat it as ground truth, do not re-derive it.
2. 00_ARCHITECTURE/llm_consumption_audit/uat_darpana/FABLE_HANDOFF_SUMMARY.md (the two vetoes)
3. 00_ARCHITECTURE/llm_consumption_audit/ELEVATION_REGISTER_v1_0.md — EL-07, EL-41, EL-42, EL-60,
   EL-24 (context for W5's annotations)

Then execute the brief:
- git tag satya-shesha-start; work on branch satya-shesha/<item> off main.
- Spawn FOUR builder sub-agents IN PARALLEL per §3 (B1: W1 · B2: W2+W3 · B3: W4 · B4: W5+W6),
  Sonnet each, with the file-ownership split in §3. Spawn the VERIFIER as a separate Opus agent
  that never writes code.
- main is branch-protected (4 required checks, enforce_admins) — NEVER git push origin main.
  Merge path: git push origin <branch> → gh pr create --base main → gh pr merge --auto --squash.
  Hold until the PR actually merges; a red check means auto-merge never fires — 30-min ceiling,
  then fix once or park. CI (Node 20) is the arbiter, not local (Node 24). Batch merges per builder.
- Deploys: platform auto-deploys on main; amjis-mcp (platform-mcp) must be deployed EXPLICITLY —
  W4 in particular is meaningless without it. Confirm revision + image SHA before any G4 probe.
- HARD SCOPE RAIL (§5): serving-side only. No writers, no migrations, no rebuilds, no touching
  kala_gochara_windows data or build_substep_progress. The 20-hour gochara sweep is read-only.
  Anything needing a data change → PARKED-HONEST.
- DONE per item = the Verifier's G4 live re-probe passes the §2 acceptance lines on BOTH canonical
  charts (482012f1-710e-4a25-994a-93821f5871aa, 1c826d5a), with before/after payloads in
  ledgers/SATYA_SHESHA_LEDGER.md. Four dispositions only; no "passed with caveats". The §1
  verified-FIXED list must still pass at close (regression guard).
- Any question you would ask a human, answer yourself and log the ruling with rationale. Never
  weaken an acceptance criterion to pass it — park honest instead.
- Close: disposition table for W1–W6 + the ledger merged to main; one-line CURRENT_STATE §2 update;
  final report SATYA_SHESHA_REPORT_v1_0.md in the satya_shesha folder covering: per-item
  disposition + evidence refs, every proxy ruling, deploys shipped, the dry-run result of W6's
  claim-detector over the 45 DARPANA answers, and what remains parked.
Wall-clock cap 5 hours. Begin.
```

---

*End of SATYA_SHESHA_BRIEF v1.0 — authored by Fable in Cowork, 2026-07-25, grounded in same-day
live production probes (§1). The mission in one line: after this campaign, the system can still say
"I don't know" — but it can never again say "there is nothing" when the truth is "I didn't look."*
