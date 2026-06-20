---
artifact: CLAUDECODE_BRIEF_STREAM_F_SILENT_WRITE_FIX_v1_0.md
brief_id: STREAM_F_SILENT_WRITE_FIX
version: 1.0
status: ACTIVE — executable
authored_at: 2026-06-01
authored_by: cowork-planner
follows: CLAUDECODE_BRIEF_STREAM_F_FORENSIC_RENDER_v1_0.md (S3, merged f74b8b78 — passed tests, fails in prod)
implementation_surface: Claude Code in Google Antigravity IDE (full autonomy incl deploy)
autonomy: code → commit → merge to main → deploy amjis-sidecar → rebuild native chart → verify. No human gate.
why: >
  Post-merge production run (PYJHORA-POSTMERGE-DEPLOY-B, 2026-06-01) showed A2_forensic_render
  reported status=complete with rows_written=0 across all 6 ayanamsha slots — 0 rows in
  chart_documents, no error surfaced. The S3 writer is correct in unit/integration tests
  (mocked conn + synthetic chart_output) but breaks on the REAL pyjhora_adapter.compute_chart()
  output shape, and the build dispatch path SWALLOWS the resulting exception.
not_a_rescope: >
  Stream F design questions Q1/Q3 are RESOLVED (markdown render to chart_documents; render
  infra exists). The superseded STREAM_F_FORENSIC_RENDER_SCOPING brief is NOT the path. This
  is a debug-and-fix of already-merged code.
diagnosis_grounded:
  - "forensic_writer.write() returns 1 on success or RAISES (RuntimeError on empty md; exception in to_render_input; NarrationViolation). It cannot return 0."
  - "Therefore rows_written=0 + status=complete + no error ⇒ write() raised AND the dispatch/retry wrapper swallowed it and recorded the step complete with 0 rows."
  - "S3 integration tests used mocked conn + synthetic chart_output ([[ship-but-dont-mount-pattern]]); they never exercised real compute_chart() output shape."
  - "build_chart dispatch_asset() catches only ImportError; the retry wrapper (build_chart.py ~line 492+) is the swallow point — it must hard-fail a registered non-stub writer that raises or returns 0."
may_touch:
  - platform/python-sidecar/pipeline/render/_chart_output_adapter.py
  - platform/python-sidecar/pipeline/writers/forensic_writer.py
  - platform/python-sidecar/pipeline/build_chart.py            (dispatch/retry swallow fix)
  - platform/python-sidecar/pipeline/render/*.py               (ONLY a genuine renderer bug; prefer the shim)
  - platform/python-sidecar/pipeline/__tests__/                (add a REAL-output test)
  - platform/python-sidecar/pipeline/render/__tests__/
must_not_touch:
  - platform/python-sidecar/pyjhora_adapter/   (read its real output; don't change the engine)
  - migrations, src/, the other workstreams' scope
hard_bans:
  - No Anthropic models.
  - No JH-parity / FORENSIC-v8.0 value oracle.
  - Do NOT weaken the no_narration_linter to make rendering pass.
  - Do NOT fix the shape by rewriting the tested section renderers — fix the shim.
  - Do NOT make the swallow "pass" by lowering A2 to a stub or catching+ignoring. The fix is HARD-FAIL.
prime_directive: only computed facts. no narrative.
---

# Stream F silent zero-write — debug and fix

## 1 · Find the swallowed exception (do this first, read-only)

Two equivalent ways; do at least one and paste the traceback into the PR:

- **Cloud Run logs.** Pull `amjis-sidecar` logs for the last native build's `A2_forensic_render`
  step (build on chart `362f9f17-95a5-490b-a5a7-027d3e0efda0`). The swallowed traceback is
  almost certainly logged even though the step was marked complete. Find the exception type +
  the field/key that broke.
- **Local repro against REAL engine output.** In a scratch script:
  ```python
  from pyjhora_adapter import compute_chart
  from pipeline.render._chart_output_adapter import to_render_input
  out = compute_chart('lahiri', <native jd_ut>)   # REAL output, not a fixture
  print(sorted(out.keys()))
  ri = to_render_input(out)                         # <-- expect this (or a renderer) to raise
  ```
  This is the empirical real-shape diff that S4a was supposed to do against live output.

Record: the exception type, the exact key/shape mismatch, which layer raised
(`to_render_input` vs a specific renderer vs `_upsert_chart_document`).

## 2 · Fix the shape (the trigger)

Correct `_chart_output_adapter.to_render_input()` to handle the REAL
`pyjhora_adapter.compute_chart()` output. Likely deltas (confirm against §1): planet keys,
`longitude_arcsec` vs `degree`, 2-letter sign codes vs full names, `nakshatra_pada` vs `pada`,
`varga_positions` assembly, houses 6-system dict, dashas system-keyed shape. **Fix in the
shim, not the renderers.** If a renderer has a genuine `.get()` that can't tolerate a missing
optional field, give it a safe default in the renderer's input (still via the shim) — do not
delete fields or weaken the linter.

## 3 · Fix the silent swallow (the dangerous part)

In `build_chart.py`, the retry/dispatch path must **fail loudly** when a registered,
non-stub writer raises or returns 0:

- A writer in `WRITER_REGISTRY` that raises after exhausting retries → mark the asset step
  `status=failed` with the error text, surface to the cockpit (build_event), and fail the
  build (or the asset, per the existing per-asset rollback pattern). **Never record
  `status=complete, rows_written=0` for a registered asset.**
- A registered writer that returns 0 for an asset whose `EXPECTED_ROW_COUNTS` is > 0 → also a
  failure, not a complete.
- Keep the stub fall-through (asset NOT in `WRITER_REGISTRY`) returning 0 — that path is
  legitimately "no writer yet." The distinction is **registered vs stub**, not 0 vs non-0.

This enforces the Stream F brief's hard-fail rule and prevents the next silent regression
([[silent-param-feature-toggle]], [[ship-but-dont-mount-pattern]]).

## 4 · Close the test gap

Add a test that feeds **real `compute_chart()` output** (or a captured snapshot of it,
committed as a fixture generated FROM the live engine — not hand-authored) through
`forensic_writer.write()` with a real/SQLite-backed conn, asserting a `chart_documents` row
is written. The S3 tests passed on synthetic data; this test must fail before the §2 fix and
pass after. Add a `build_chart` test asserting a raising registered writer marks the step
`failed`, not `complete`.

## 5 · Verify in production

1. Merge to main; deploy `amjis-sidecar` from main (`gh workflow run deploy.yml --ref main`).
2. Rebuild the native chart (via `/api/build/start`, Cloud Tasks path).
3. Assert `chart_documents` has **6 `forensic_render` rows** (1 per ayanamsha) for the latest
   build, `content_md` non-empty, no-narration linter clean.
4. Confirm `rag_embedder` produces `rag_chunks(source_type='forensic_render')`.
5. Confirm a deliberately-broken render now FAILS the build step (don't ship this; just prove
   the swallow is fixed in a test).

## 6 · Acceptance criteria

1. §1 traceback captured + root-cause documented in the PR (exact shape mismatch).
2. `to_render_input` handles real `compute_chart()` output; section renderers unmodified
   (or only safe-default tweaks).
3. Registered writer that raises/returns-0 now **fails the build step** — no silent
   complete-with-0. New `build_chart` test proves it.
4. Real-output forensic test added; fails pre-fix, passes post-fix.
5. `pytest platform/python-sidecar/` green.
6. Production: native rebuild → 6 `forensic_render` docs, content non-empty, linter clean,
   `rag_chunks` present.
7. `EXPECTED_ROW_COUNTS` forensic_render expectation now actually met by a real build.

## 7 · Antigravity kickoff prompt (paste verbatim)

```
You are an autonomous executor. --dangerously-skip-permissions. Full autonomy: code, commit,
merge to main, deploy amjis-sidecar, rebuild the native chart, verify. No human gate.

Setup:
  cd /Users/Dev/Vibe-Coding/Apps/Madhav && git fetch origin
  git worktree add /Users/Dev/Vibe-Coding/Apps/MadhavSF-Fix -b fix/stream-f-silent-write origin/main
  cd /Users/Dev/Vibe-Coding/Apps/MadhavSF-Fix

Execute 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_STREAM_F_SILENT_WRITE_FIX_v1_0.md end-to-end.
This is a DEBUG-AND-FIX of merged code, NOT a re-scope — ignore the superseded SCOPING brief.
§1 FIRST: capture the swallowed traceback (Cloud Run logs OR local repro against REAL
pyjhora_adapter.compute_chart() output). Paste it before any fix. Then §2 fix the shim for the
real shape (never the renderers), §3 make the dispatch path HARD-FAIL a registered writer that
raises/returns-0 (no silent complete-with-0), §4 add a real-output test that fails pre-fix.

Do NOT weaken the linter. Do NOT lower A2 to a stub. Do NOT touch pyjhora_adapter/ or migrations.
Do NOT edit SESSION_LOG / CURRENT_STATE (a follow-up governance session owns those).

Verify in prod (§5): merge → deploy amjis-sidecar → rebuild native chart 362f9f17-95a5-490b-
a5a7-027d3e0efda0 → assert 6 forensic_render docs in chart_documents, content_md non-empty,
linter clean, rag_chunks present. Keep amjis-web PUBLIC; do not touch its IAM.

Append "SF-FIX MERGED <sha> AC=<n/n>" + the prod doc count to
00_ARCHITECTURE/CONDUCTOR/pyjhora-followups/RUN_LOG.md. Report the traceback, the shape fix,
the swallow fix, and the prod chart_documents count.
```

---

*End of CLAUDECODE_BRIEF_STREAM_F_SILENT_WRITE_FIX_v1_0.md*
