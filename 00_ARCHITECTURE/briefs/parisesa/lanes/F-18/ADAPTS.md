---
finding: F-18
adapts: F-17/SPEC.md (approved-pending-REVIEW as of this writing)
stage: thin adaptation — VERIFIER reviews F-17's SPEC.md once; this document just pins the
  one-line delta for F-18 so review load isn't duplicated.
---

# F-18 adapts F-17's spec — one-line delta

F-17's SPEC.md (§2) already lists all 21 bare `dualOutput(data)` call sites in
`platform-mcp/src/tools/register_p1_aliases.ts` as the files-to-change, **including line 657**,
which is F-18's own site (`bodha_graph_traverse_get`). F-17's exit test (§3) already asserts zero
bare `dualOutput(data)` sites remain file-wide — that assertion covers line 657 by construction,
not by a separate check.

**Nothing in this document adds a new file, a new exit test, or a new design decision.** VERIFIER's
Stage-R review of F-17's SPEC.md is this finding's review; once F-17 is COMPLETE, F-18 is COMPLETE
by the same verdict — no independent REVIEW.md is produced for F-18.

**Live re-confirmation this finding's own call shape still reproduces:** deferred to F-17's own
Stage-V re-run (both sites are fixed in the same commit, so one post-build live check exercising
both `bodha_graph_subgraph_get` and `bodha_graph_traverse_get` — F-18's own reproduce_cmd — is
sufficient; see F-17's SPEC.md §3 "Live confirmation" note, to be extended to name both tools
explicitly at Stage V).

See `lanes/F-18/DIAGNOSIS.md` for the full D-stage record (live repro, mechanism, sibling census)
already on file.
