---
finding: F-43
adapts: F-17/SPEC.md (approved-pending-REVIEW as of this writing)
stage: thin adaptation — VERIFIER reviews F-17's SPEC.md once; this document just pins the
  19-site delta for F-43 so review load isn't duplicated.
---

# F-43 adapts F-17's spec — 19-site delta, already enumerated

F-17's SPEC.md (§2) already lists all 21 bare `dualOutput(data)` call sites in
`platform-mcp/src/tools/register_p1_aliases.ts` as the files-to-change. F-43's own contribution
(DIAGNOSIS.md §4) was the exhaustive line-numbered census confirming the corpus's informal "~19
more sites" claim resolves to exactly 19: lines 606, 1155, 1207, 1368, 1499, 1522, 1558, 1570,
1582, 1594, 1606, 1618, 1630, 1670, 1781, 1844, 1860, 1874, 1971 — every one of these is already
in F-17's SPEC.md §2 file-list, and F-17's exit test (§3) asserts zero bare `dualOutput(data)`
sites remain file-wide, which covers all 19 by construction.

**Nothing in this document adds a new file, a new exit test, or a new design decision.** VERIFIER's
Stage-R review of F-17's SPEC.md is this finding's review; once F-17 is COMPLETE, F-43 is COMPLETE
by the same verdict — no independent REVIEW.md is produced for F-43.

**Live re-confirmation:** F-43's own DIAGNOSIS.md §1 already live-reproduced the defect on
`catalog_assets_list` (one of the 19); the other 18 named sites were source-grep-identified, not
independently live-retested, per the corpus's own PASS-not-retroactively-downgraded discipline.
At Stage V, spot-checking 2-3 of the 19 (not necessarily all 19) against the post-build response
is sufficient given the fix is one mechanical regex-shaped change applied identically to every
site — the exit test's file-wide assertion is the actual correctness guarantee, live spot-checks
are corroboration, not the primary proof.

See `lanes/F-43/DIAGNOSIS.md` for the full D-stage record already on file.
