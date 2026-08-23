# F-120 DIAGNOSIS — ganita_dasha_periods_get narration drops finest running period + sandhi_flag

TIER3-EXPERIENCE · stream S4 VĀCA · PARIŚEṢA campaign

## Live Reproduction

Called `ganita_dasha_periods_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa,
ayanamsha_id='lahiri_chitrapaksha', as_of_date='2026-08-15', all_levels=true, fields='compact')`
live against the canonical chart. Result:

- `levels_available: 4`, `total: 4` — payload returns rows for level_n 1..4.
- `rows[3]` (level_n=4): `lord_graha: "Mercury"`, `start_date: "2026-08-13"`,
  `end_date: "2026-08-25"`, `sandhi_flag: true`. This is the currently-running Sūkṣma-level
  period as of `as_of_date=2026-08-15` (falls inside 2026-08-13..2026-08-25), and it is flagged
  as a junction period.
- `narration` field (verbatim from the response):

  > "You are in Mercury Mahadasha (ends 2027-08-18, age ~43) -> Saturn Antardasha (ends
  > 2027-08-18, age ~43) -> Moon Pratyantardasha (current, ends 2026-09-17, age ~42). Saturn,
  > your Antardasha lord, is exalted in your 7 house (Vishakha). Moon, your Pratyantardasha
  > lord, is neutral in your 11 house (Purva Bhadrapada)."

The narration stops at level_n=3 (Moon Pratyantardasha, labeled "current"), never mentions the
level_n=4 Mercury Sūkṣmadaśā row or its `sandhi_flag=true`. Claim **reproduces live, exactly as
described**.

## Claim Decomposition

| # | Claim | Verdict |
|---|---|---|
| (a) | Payload correctly returns 4 levels including level_n=4 with sandhi_flag=true | CONFIRMED — `rows[3]`, `levels_available: 4` |
| (b) | Narration is hardcoded to exactly 3 levels | CONFIRMED — see mechanism, line 464 |
| (c) | Narration mislabels the level-3 row "current" without qualification | CONFIRMED — line 495, unconditional string literal |
| (d) | sandhi_flag is never consulted by the narrator regardless of level | PARTIALLY CONFIRMED, more precise: it IS consulted, but only at level 1 (Mahādaśā) via `md['sandhi_flag']` — never at level 3 (the row labeled "current") or level 4 (the row actually current). Net effect for this reproduction is identical to "never consulted" since MD's own sandhi_flag is `false` here, but the mechanism is "wrong level pinned," not "field never read." |

## Mechanism (file:line, quoted code)

`platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts`

**Line 460–469 — hardcoded 3-level cap when building the level→row map the narration draws from:**

```ts
460	          const byLevel: Record<number, Record<string, unknown>> = {}
461	          for (const rawRow of enrichedRows) {
462	            const row = rawRow as Record<string, unknown>
463	            const lvl = row['level_n'] as number
464	            if (lvl < 1 || lvl > 3) continue
465	            // Prefer the canonical (non-kp_sub) row per level; first-seen otherwise.
466	            if (byLevel[lvl] === undefined || isCanonicalRow(row)) {
467	              byLevel[lvl] = row
468	            }
469	          }
```

Level_n=4 rows (already present in `enrichedRows` — the same array the response's `rows` field is
built from) are filtered out of `byLevel` before the narration ever sees them. `md/ad/pd` are then
pinned to `byLevel[1]/[2]/[3]` (lines 483–485) unconditionally.

**Line 492–495 — the "current" label is a hardcoded string literal on whichever row lands in
`byLevel[3]`, with no check for a finer level actually running:**

```ts
492	            const leadSentence =
493	              `You are in ${md['lord_graha']} Mahadasha (ends ${mdEnd}, ${ageAtDate(mdEnd)}) -> ` +
494	              `${ad['lord_graha']} Antardasha (ends ${adEnd}, ${ageAtDate(adEnd)}) -> ` +
495	              `${pd['lord_graha']} Pratyantardasha (current, ends ${pdEnd}, ${ageAtDate(pdEnd)}).`
```

**Line 511–515 — `sandhi_flag` is consulted exactly once, and only at the Mahādaśā (level 1) row:**

```ts
511	            const sandhiSentence = md['sandhi_flag']
512	              ? `Note: the Mahadasha is in its sandhi (junction) window — classically a transitional ` +
513	                `caution period where both lords' effects blend — worth weighing against ${ad['lord_graha']}'s ` +
514	                `own placement above rather than reading as blanket alarm.`
515	              : null
```

There is no equivalent check against `ad['sandhi_flag']` or `pd['sandhi_flag']`, and level_n=4 is
never in scope to check at all (filtered at line 464). So even a Pratyantardasha- or
Sūkṣmadaśā-level sandhi is structurally invisible to this narrator regardless of which levels are
in `byLevel`.

The comment block at lines 438–446 explains *why* the narration exists (a Pratinidhi-R ruling,
"flat_fact/leaf archetype... narrated from rows already fetched in this call") but does not
address level-count extensibility — the 1..3 cap reads as an unexamined hardcode from when
`level<=3` was still this tool's own default cap (see the tool's `all_levels` param doc: "Disable
the default level<=3 cap"), not a deliberate decision re-justified for the `all_levels=true` case.

## Sibling Census

Searched the full narration/composer surface in the S4 Kāla-views lease for other hardcoded-N-level
loops: `now.ts`, `explain.ts`, `ahead.ts`, `upaya.ts`, `dasha_sandhi.ts`
(`platform-mcp/src/tools/kala_views/`).

| File:line | Pattern | Assessment |
|---|---|---|
| `now.ts` `fetchVimshottariMdAdBoundaries`, called from the `dasha_sandhi` (item 1-lite) field builder — dispatches `query_active_dashas` with `max_level: 2` | Hardcoded 2-level cap (MD/AD only) | **Not a sibling of F-120's defect class.** Explicitly documented in the file header (`now.ts` lines 24–28): "item 1-lite `dasha_sandhi`: a band around every currently-active MD/AD period's start AND end boundary... Full daśā-sandhi calendar (all levels, both directions) is item 1-full (wave W3), not this facade's job." The field's own name/scope is declared MD/AD-only and points to the all-level surface (`kala_dasha_sandhi_get`). No "current" mislabel found downstream of it in this file. |
| `ahead.ts` line 1759 — `.filter((e) => (e.level_n === 1 \|\| e.level_n === 2) && ...)` feeding `period_echo` | Hardcoded 2-level cap (MD/AD only) | **Not a sibling.** Different feature (item 31, "period-echo mining... same-lord Mahādaśā/Antardaśā recurrence in the native's own lived timeline"), documented at line 1618–1620 as intentionally MD/AD-scoped — not a "what dasha am I in now" claim, so no sandhi-at-finer-level omission risk of the same kind. |
| `ahead.ts` line 777 — `PERIOD_ECHO_LEVEL_NAME: Record<number, string> = { 1: 'Mahadasha', 2: 'Antardasha' }` | Hardcoded 2-entry label map | Same scope as the row above — cosmetic label lookup for the already-MD/AD-filtered `period_echo`, not an independent defect. |
| `explain.ts` line 302 — `.filter((p) => Number.isFinite(p.level_n) && p.level_n > 0)` | No upper bound | Not a sibling — all levels pass through. |
| `upaya.ts` | — | No dasha-level chain code present at all; not applicable. |
| `dasha_sandhi.ts` (`kala_dasha_sandhi_get`, item 1-full) | `all_levels: true` passed to `get_dashas` (line 180); no per-level filtering anywhere in `buildBoundaries` | **Correctly built** — genuinely all-level, all-direction; this is the surface the codebase itself designates as the fix/escape-hatch for the lite surfaces' documented MD/AD scope. |

**Net finding:** within the S4 Kāla-views lease, there are two other hardcoded-low-level caps
(`now.ts` max_level 2, `ahead.ts` level∈{1,2}), but both are documented, intentionally-scoped
fields with names that say what they cover, and neither makes an unqualified "current" claim the
way F-120's narration does. Zero undocumented siblings of F-120's exact defect (silent cap +
unconditional "current" label + sandhi_flag pinned to the wrong level) were found in this lease.
**The actual F-120 mechanism lives outside the S4 kala_views lease**, in the L1 registry layer
(`platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts`), which is the file that
needs the fix.

## Blast Radius / Exemplar Note

Read `dasha_sandhi.ts` in full (see Sibling Census row above — it is clean: genuinely all-level,
no cap). It is not itself implicated in F-120 or (on the evidence available to this lane) in F-121.

F-121 is described (per the assignment brief only — this lane did not independently reproduce it)
as a "kala_now_get 'not in a junction' claim." The candidate mechanism in `now.ts` is the
`dasha_sandhi` (item 1-lite) field, built by `fetchVimshottariMdAdBoundaries` →
`query_active_dashas` with `max_level: 2`. If F-121's actual defect is that some summary/verdict
text in `kala_now_get` reads "not in a junction" off this MD/AD-only band field without qualifying
that it never looked at Pratyantardaśā/Sūkṣmadaśā, then F-121's mechanism and F-120's mechanism are
**structurally analogous but not the same code path**:

- F-120: `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts` (L1 registry layer),
  narration built from `byLevel[1..3]` pinned from `enrichedRows` already in hand, `lvl > 3` cap.
- F-121 (candidate): `platform-mcp/src/tools/kala_views/now.ts` (L3 serving facade), a fresh
  `query_active_dashas` call with `max_level: 2` — different file, different function, different
  upstream capability (L3 active-chain query vs. L1 row-in-hand), different cap value (2 vs 3).

**Verdict on "one fix or two": TWO fixes, one shared defect class.** These are independent
implementations of the same anti-pattern — a narrative/summary-producing code path hardcodes a
fixed, low dasha-level ceiling and asserts a "current"/"not in a junction" claim without checking
whether a finer, currently-running level exists and is sandhi-flagged. They live in different
layers (L1 vs L3), different files, different functions, and would need independent patches (there
is no shared helper to fix once). This pairing is a good EXEMPLAR of the defect class for a shared
writeup, but the two are not one shared root cause requiring one shared code change. **This lane
did not verify F-121's live reproduction or its exact narration text — that determination belongs
to F-121's own lane; the above is inference from reading `now.ts`'s mechanism only, offered for the
exemplar-unification pass.**

No PAR-R-7 escalation needed — no ambiguous/reserved determination was hit in this lane; the
F-120 mechanism, its scope, and the sibling census all resolved on direct evidence.

## Verdict

**REPRODUCES LIVE — CONFIRMED DEFECT.**

- Mechanism: `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts` lines 460–469
  (hardcoded `lvl > 3` cap building `byLevel`), lines 492–495 (unconditional "current" label on
  the level-3 row), and line 511 (`sandhi_flag` consulted only at level 1, never at the labeled
  "current" row or any finer level).
- Sibling count in the S4 lease: 0 undocumented siblings of the exact defect class; 2 documented,
  intentionally-scoped hardcoded-level fields noted for completeness (`now.ts` max_level:2,
  `ahead.ts` level∈{1,2}) that are not defects themselves.
- F-121 relationship: structurally analogous candidate mechanism in a different file/layer;
  requires two separate fixes, not one shared fix. Not independently verified by this lane.
