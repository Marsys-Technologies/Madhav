---
artifact: S2_LEAD_SCOPING_NOTE
findings: F-112 (primary), cross-references F-56, F-111, F-14, F-15, F-124
author: MATRA-LEAD (S2), personal code read — not a dispatched Stage-D agent
source: ekv/a-09-sara-kernel HEAD ceadae8cb, read-only worktree
  .claude/worktrees/ekv-a-09, platform-mcp/src/tools/registry_bridge.ts
---

# Scoping the "adopt ekv/a-09-sara-kernel, needs extension" classification

Read `buildAssessResponse` (registry_bridge.ts:2886-2951) and the four assess_* handler bodies
(assess_marriage ~2960-2994, assess_career ~2996-3038, assess_health ~3040-3072, assess_wealth
~3074+) directly, plus `attachDomainCompleteness` (:835-838) and `attachDomainReading` (:1569-1574).

## Confirmed facts (code read, not yet live-verified — Stage-D agent on F-14/F-15/F-124 is doing
that independently; this note is a complement, not a substitute)

1. **assess_marriage and assess_health never call `attachDomainCompleteness` or
   `attachDomainReading` at all.** Only `assess_career`'s handler body calls both, immediately
   before `buildAssessResponse`. This directly confirms F-14/F-15's cited mechanism
   (DOMAIN_READING_FAMILIES / family-wiring gap) at the call-site level, one layer up from the
   registry_bridge.ts:1034 map the corpus originally cited — worth the Stage-D agent confirming
   whether :1034's DOMAIN_READING_FAMILIES map is what `attachDomainReading` consults internally
   (i.e. is the missing 'health'/'relationship' key THE reason these two calls were never added to
   the marriage/health handlers, or a second, independent gap?).

2. **NEW, not yet in the corpus:** `attachDomainCompleteness` sets `response['domain_completeness']`
   (:838) but `buildAssessResponse`'s grounding-layer assembly (:2925) checks
   `response['completeness']` — a different key. Even for assess_career, which DOES call
   `attachDomainCompleteness`, the sāra-kernel composition never picks it up: `domain_completeness`
   is computed, attached to the intermediate `response` object, and then silently dropped when
   `buildAssessResponse` builds `grounding`/`evidence`/`kernel` from named keys that don't include
   `domain_completeness`. `dualOutputBudgeted` (:1780) is a pure passthrough of whatever
   `buildAssessResponse` returns — nothing re-merges the original `response` object afterward.
   **Net effect on this branch, if merged as-is: F-56/F-111's byte-bloat from an unbudgeted
   domain_completeness block would be fixed, but by silently deleting the field from ALL four
   assess_* responses, not by budgeting it.** That is a new, undisclosed information loss, and
   itself a §N.6/§N.8-class defect (a field silently vanishes with no judgment_flag or
   `domain_completeness_empty_reason` explaining why) — needs its own line in F-112's spec, and
   likely needs a fresh sub-finding note if VERIFIER wants it tracked separately from F-112's
   original claim (which was about size, not disappearance).

## What this means for the "needs extension" board classification

- F-14 / F-15: CONFIRMED real gap exists (marriage/health handlers never call the attach
  functions) — a-09-sara-kernel does NOT close these; extension is genuinely required: add the two
  attach calls to assess_marriage/assess_health mirroring assess_career, AND fix whatever upstream
  map (DOMAIN_READING_FAMILIES or equivalent) blocks 'health'/'relationship' domains if that map is
  what `attachDomainReading`/`attachDomainCompleteness` key off internally (Stage-D agent to
  confirm the internal implementation of both functions, not yet read here).
- F-124: same root as F-14/F-15 for the missing-reading half of its claim; the
  domain_completeness half of its claim is affected by the NEW key-mismatch bug above.
- F-112: the classic form of the finding (fixed-size unbudgeted block dominating response bytes)
  is likely ALREADY neutralized by this branch merely because the field never reaches the output —
  but that trades an honesty violation (oversized, undisclosed) for a different honesty violation
  (silently absent, undisclosed). The correct fix is neither: budget `domain_completeness`
  properly as a real evidence/grounding-layer entry (bounded or explicitly excluded WITH a
  judgment_flag), not a silent drop. Spec stage must not treat this as "already fixed by adoption."
- F-56 / F-111: unaffected by this note — their core claim (activating_dasha/verdict_skeleton
  object-blindness) is what buildAssessResponse's evidence layer actually targets and appears
  correctly structured for. Live verification still owed (Stage V, not done here).

## Action for Stage S (spec) once Stage-D closes

Whoever specs F-112 (after F-14/F-15/F-124's Stage-D returns) should treat the fix as: (a) rename
or bridge the key so buildAssessResponse's grounding assembly reads `response['domain_completeness']`
correctly, (b) decide bounded-inclusion vs explicit-exclusion-with-flag for that field at the
declared budget_kb, mirroring how verdict_skeleton/activating_dasha are excluded WITH the caller
still able to tell they were excluded (via the kernel's pointers / a flag), not silently. This is a
single small fix inside registry_bridge.ts (S2's own hot file) — no NEEDS-LEASE required.
