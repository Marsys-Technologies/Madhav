---
artifact: ASTRA_REVIEW_REPIN_TOOL_DELTA
version: "1.0"
reviewer: "Codex gpt-6-astra"
date: "2026-10-04"
verdict: REJECT
reviewed_commit: 5c5f39f3dc339ce3ada2e63f1a13dfc1456562b9
authority: "Review only; authorizes nothing."
---

Commit, three-commit delta, and supplied tool SHA verified. Two blockers in [preflight_problems](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-repin/platform/python-sidecar/scripts/gochara/repin_dasha_contract.py:321):

1. **A — P1: declarations can bless an incomplete, mixed-build rebuild.** In-memory reproduction: observed and declared **44 non-scope + 0 scope-cap, builds `{NEW, OLD}`**, both assets `lit`: the reviewed base returns STOPs **(ii), (iii)**; HEAD returns **no pre-flight problems**. If OLD survives outside Vimśottarī/Lahiri, G6(a) and the new verifier check also pass. Nothing distinguishes a legitimate declaration from one copied from the broken state.

2. **A — P1: acceptance exceeds “default OR exactly declared.”** Counts and builds are accepted independently. Declare `(47,1,{NEW,OTHER})`; HEAD also accepts `(45,1,{NEW,OTHER})` and `(47,1,{NEW})`. Neither equals either complete allowed state.

Partial declarations are refused. The raw notice SHA-256 binds all three fields, but hashing does not establish their correctness. **G6(a) remains unchanged and unrelaxable.** Other existing comparison/apply and `--capture-old` refusal paths are preserved.

**B — sound for the canonical chart.** Compared with the verifier at `699638fbe` and composed head `20ad1bd6e`: identical chart/system/ayanāṃśa selection, all levels and tiers including NULL, NULL builds included. Exact `system_id='vimshottari'` excludes `vimshottari_kp`. HEAD additionally rejects an empty build set; the existing reader already refuses that case.

**C — capture refactor is sound.** Old capture selection, normalization and data-digest construction are unchanged. Identical captured payload would retain data SHA  
`d6a9b80d22b05d7b6f062a955532a317bd6cb5bfa5b3fa86a3314956c461e5d6`; the supplied capture itself was not independently rehashed. Whole-file bytes change through provenance/timing metadata.

`--capture-new` refuses absent/foreign builds and incompatible modes before writing an artifact. The normal CLI retains one REPEATABLE READ, READ ONLY snapshot, one rollback, one close, no commit, and validation before file writing. Reference-row validation remains mandatory whenever capturing the pinned build.

**D — tests unverified here.** The single permitted pytest attempt failed **before collection**: the read-only sandbox has no usable writable temporary directory. Thus **126 passed / 2 skipped is not confirmed**. No database was contacted.

Missing regression tests: declared OLD+NEW, declared missing partitions, and both hybrid combinations above. Existing refusal branches without explicit tests include `transaction_read_only='off'`, missing truncation flags, and mismatched recorded per-level counts.

**MAY THE OPERATOR USE HEAD 5c5f39f3d (tool sha256 5524b15c444c3470a2463780e7f275f4db6c1b712bbd9067211671683b6b7a3b) INSTEAD OF 5a46c9c97 for the SETTLED-1 comparison, apply and post capture — NO.**

Required changes: restore unconditional **45+1 partitions and exactly `{new_build_id}`** for this SETTLED-1; prevent declarations from overriding those refusals. Retain hunks 2–3, add the counterexample regressions, and rerun the database-free suite.