---
lane: F-50
stream: S4
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-2
draft_verdict: COMPLETE
ratified_by: ratifier-2
---

## Method

Read: PROTOCOL.md, DIAGNOSIS.md (full), SPEC.md (full — post-revision, substantive), existing REVIEW.md (pool-1, INCOMPLETE-RETURN because prior SPEC was a placeholder).
Source verification: read `main-ro/platform/src/lib/retrieval/registry/layers/L2_bodha/query_remedies.ts` lines 320–466 against all SPEC.md file:line citations.
No REVIEW_LEADS.md present in lane directory.
Context: post_revision=true; prior INCOMPLETE-RETURN was due to absent spec, not a spec deficiency — the spec has since been written.

## Q1 — Mechanism vs symptom

The spec addresses the mechanism directly: the lead-sentence template at lines 447–460 applies superlative framing (`#1`, `highest-leverage`) unconditionally to `orderedResRows[0]` without branching on whether the `graha` SQL filter (line 346) reduced `orderedResRows` to a singleton. The fix prescribes a conditional guard on the in-scope `graha` variable — when truthy, emit factual `weakest_rank_in_chart`/`remedy_priority_class` wording instead of rank-superlative wording. This is mechanism-level, not symptom-level.

## Q2 — Sub-claims mapped to spec elements

Diagnosis claim (a): filtered call labels graha "#1" regardless of actual rank → SPEC §1/§2 describe exactly this and cite line 457 (non-leverage) and line 452 (leverage). Both branches called out.
Diagnosis claim (b): `weakest_rank_in_chart` and `remedy_priority_class` already present in `topRow` (line 359 SELECT) → SPEC §2 line 359 cites this; fix prescription reads these fields directly.
Diagnosis claim (c): unfiltered call correctly ranks Saturn 8/9 → SPEC §6 regression guard test asserts unfiltered lead still contains `#1` and `Venus`.
Diagnosis leverageActive-branch note → SPEC §1 and fix prescription handle both branches in the same edit.
Diagnosis sibling census (no other hits) → SPEC §5 reproduces the census result verbatim and explicitly excludes `get_dashas.ts:492` with a stated reason.

All diagnosis sub-claims have corresponding spec elements. No unmapped claims.

## Q3 — Exit test fails on today's code

Traced against main-ro source (lines 450–460 confirmed verbatim):

With `graha='Saturn'`, `resRows` is filtered to one row (line 346 SQL filter). `orderedResRows = resRows` (one row). `topRow = orderedResRows[0]` = Saturn row. `leverageActive` is false for a standard call.

Line 457 emits: `"Your Bodha remedy layer flags Saturn as your #1 remedy-priority target — resonance_score 0.094, priority class low."`

This string contains `#1`. First assertion `expect(lead).not.toMatch(/#1/)` → FAILS on current code. ✓

After fix, `graha` is truthy → guard branch: `"Saturn's remedy priority is low (rank 8 of 9 chart-wide) — resonance_score 0.094."` → does not match `/#1/`, matches `/low/i`, matches `/rank|chart-wide|8 of 9/i` → all three assertions PASS. ✓

Regression guard (unfiltered call): `graha` is falsy → fix falls through to existing branches (leverage or standard), preserving `#1`/`Venus` output. ✓

## Q4 — Sibling sites covered

SPEC §5 covers:
- Literal `"as your #1"` / `"your #1"` grep: one hit only at `query_remedies.ts:457` — stated explicitly.
- `leadSentence` / narration-lead repo-wide: two files — `query_remedies.ts` (in-scope) and `get_dashas.ts:492`. Exclusion reason stated: `get_dashas.ts:492` emits a deterministic current-state sentence not derived from a caller-filtered ranked set.
- Both branches within `query_remedies.ts` (leverage line 452, non-leverage line 457) addressed by the single prescribed edit.

No sibling left uncovered or unexplained.

## Q5 — Recurrence guard

SPEC §7: Guard is a conditional on `graha` (line 327), colocated with the variable that controls the SQL filter. A regression requires simultaneously keeping `graha` param active and removing the guard branch — the exit test's first assertion (`not.toMatch(/#1/)` on a filtered call) would fail immediately. The guard detects the actual defect class (superlative applied to filter-singleton), not a weak proxy. Adequate.

## Q7 — Unverified assumptions / file:line citations

All SPEC citations verified against main-ro:
- `query_remedies.ts:327` — `const graha = args['graha'] as string | undefined` — CONFIRMED.
- `query_remedies.ts:346` — `if (graha) { resConds.push(\`LOWER(graha) = LOWER($${rp++})\`); resParams.push(graha) }` — CONFIRMED.
- `query_remedies.ts:359` — `remedy_priority_class, is_yoga_karaka_flag, weakest_rank_in_chart,` in SELECT list — CONFIRMED.
- `query_remedies.ts:447–460` — U-a verdict-first lead block matches SPEC quotation verbatim, including line 452 (leverage branch) and line 457 (non-leverage branch) — CONFIRMED.
- `writer_asset: none` / `data_delta: none` — confirmed: fix is TypeScript serve-layer only; no writer sidecar, no DB write. Shadow run not required per PROTOCOL (serving-layer, not writer-layer).
- `bo_upaya.py:248` and `:1230` — cited in DIAGNOSIS only as explanatory context; SPEC does not quote these lines as load-bearing claims. Not a blocking omission.

No unverified assumptions found.

## Verdict: COMPLETE
