---
finding: F-43
stream: S1 DVARA
class: CL-11 (dead recover_via pointer — 'unknown_tool' placeholder)
role: CENSUS lane — 19 additional sites beyond F-17's exemplar (line 1244) and F-18's site (line 652)
stage: S revised-1 — closes REVIEW.md INCOMPLETE-RETURN deficiencies
delegates_to: F-17/SPEC.md (root cause, fix pattern, exit test, recurrence guard)
---

## 1. Root cause (by delegation to F-17/SPEC §1)

Same mechanism as F-17: `register_p1_aliases.ts`'s `dualOutput(data, toolName='unknown_tool')`
helper (**line 183**, verified against main-ro) silently defaults `toolName` to a placeholder
whenever a call site omits the second argument. F-43's 19 sites are all such bare call sites.

## 2. Files to change — F-43's 19 sites (correct line numbers, verified against main-ro)

One file: `platform-mcp/src/tools/register_p1_aliases.ts`

All 19 bare `return dualOutput(data)` sites for F-43, with **verified-correct** line numbers
(DIAGNOSIS.md §3–4 cited these at +5 offset from current main-ro; the table below is authoritative):

| Correct line (main-ro) | Stale DIAGNOSIS.md line | Note |
|---|---|---|
| 601 | 606 | bodha_signals_get outer wrapper |
| 1150 | 1155 | — |
| 1202 | 1207 | — |
| 1363 | 1368 | — |
| 1494 | 1499 | — |
| 1517 | 1522 | — |
| 1553 | 1558 | — |
| 1565 | 1570 | — |
| 1577 | 1582 | — |
| 1589 | 1594 | — |
| 1601 | 1606 | — |
| 1613 | 1618 | — |
| 1625 | 1630 | — |
| 1665 | 1670 | — |
| 1776 | 1781 | — |
| 1839 | 1844 | inside mimamsa_outcome_record handler |
| 1855 | 1860 | inside mimamsa_calibration_get handler |
| 1869 | 1874 | inside ganita_natal_positions_compute handler |
| 1966 | 1971 | — |

All 19 confirmed by `grep -n 'return dualOutput(data)$' register_p1_aliases.ts` on main-ro.
Removing F-17's site (1244) and F-18's site (652) from the 21-site total leaves exactly 19.

Each bare `return dualOutput(data)` becomes `return dualOutput(data, '<real_tool_name>')` where
`<real_tool_name>` is the exact string literal of the enclosing `server.tool('<name>', ...)` call.

**DIAGNOSIS.md correction note:** DIAGNOSIS.md §3 cites dualOutput def at `:188` (actual: `:183`);
§4 cites all 19 lines at +5 from current source. This spec's table above is authoritative. The
+5 drift is the same uniform offset identified in the REVIEW.md (Q7 deficiency).

## 3. Exit test — reference to F-17/SPEC §3 (anchored regex, comment-safe)

F-43 shares F-17's exit test (`platform-mcp/src/tools/__tests__/dual_output_tool_name.test.ts`).
F-17/SPEC §3 already carries the corrected anchored regex:

```ts
const bare = [...src.matchAll(/^\s*return\s+dualOutput\(data\)/gm)]
expect(bare.length).toBe(0)
```

This regex anchors to `return` statements and does **not** match comment lines. Specifically,
line 1794 (`// RC-04 drill-crawl (2026-07-23): dualOutput(data) with no toolName arg was…`) is
a comment — the `/^\s*return\s+dualOutput\(data\)/gm` pattern does NOT match it post-fix.
After all 21 sites are fixed, `bare.length === 0` and the test reaches green.

This closes REVIEW.md Deficiency 1 (comment-match flaw): F-17/SPEC §3 already carries the
corrected regex. No additional change to the test file is required beyond what F-17 specifies.

## 4. Sibling coverage

All 19 F-43 sites enumerated in §2 with verified correct line numbers. Total 21-site census:
19 (F-43) + 1 (F-18 at 652) + 1 (F-17 at 1244) = 21. No site silently excluded.

## 5. Recurrence guard

Inherited from F-17/SPEC §5: the anchored exit test is permanent. Any future bare
`return dualOutput(data)` in `register_p1_aliases.ts` fails CI immediately. Variable-name
gap (dualOutput(result), dualOutput(output)) documented as a follow-up, not blocking.

## 6. Dependencies and rollback

No dependency beyond F-17. This lane's fixes are merged into F-17's PR (or a sibling PR
in the same batch). Rollback: same as F-17 (revert commit; toolName reverts to default;
zero risk to any currently-working path).
