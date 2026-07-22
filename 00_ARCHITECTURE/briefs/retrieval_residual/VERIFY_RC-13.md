---
artifact: VERIFY_RC-13.md
residual: RC-13 (R-4 / W-17) — session_pin → provenance_stamp rename
branch: res/rc13-session-pin-rename @ 9e5419c8 (from main @ 2df42b61)
verifier: independent VERIFIER agent (opus, high effort) — NOT the implementer
verified_at: 2026-07-22
verdict: ACCEPT
---

# RC-13 Independent Verification — VERDICT: ACCEPT

RC-13 (`session_pin` → `provenance_stamp` rename, W-17 / GT-F28, D-16-ratified)
is **VERIFIED ACCEPTED**. Every falsifiable clause of the brief §E RC-13 DONE bar
is met, with zero behavior delta proven by running both full suites myself on the
branch AND on `main` for baseline comparison. Scope is clean — no `must_not_touch`
path is touched.

## DONE bar (brief §E RC-13, verbatim) → evidence

> **DONE:** rename complete + consistent across code and the PARIPRASHNA doc;
> full suite green (no behavior delta); envelope/pin field consumers updated;
> a grep for the old name outside changelogs returns zero.
> Internal-only; zero behavior/contract/UX change.

**(1) Rename complete + consistent across code and the PARIPRASHNA doc — PASS.**
- Types `SessionPin*` → `ProvenanceStamp*`; functions `resolveSessionPin` →
  `resolveProvenanceStamp`, `getOrRefreshSessionPin` → `getOrRefreshProvenanceStamp`;
  served JSON field `session_pin` → `provenance_stamp`; drift-flag literals
  `chart_rebuilt_mid_session_pin_refreshed` /
  `concept_ledger_updated_mid_session_pin_refreshed` →
  `*_provenance_stamp_refreshed`. All four platform-mcp consumers
  (`session.ts`, `chart_selection.ts`, `session_tools.ts`, `capabilities.ts`)
  and the platform route (`app/api/mcp/session/route.ts`) moved in lockstep.
- Source module `platform/src/lib/retrieval/session_pin.ts` → `provenance_stamp.ts`
  and both test files renamed via `git mv` (similarity 70–80%); the old paths no
  longer exist on disk (verified `ls` → No such file). New paths present.
- PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md v0.8 → v0.9: §7.1 live-storage diagram
  vocabulary corrected at source (`session_pins`→`provenance_stamps`), §20
  changelog row added closing GT-F28. The only remaining `session_pin` string in
  the doc is the pre-existing v0.8 changelog row (historical record — correctly
  untouched).

**(2) Full suite green, no behavior delta — PASS (independently rerun).**
- `platform` (branch): `tsc --noEmit` exit 0; `vitest run` → **592 passed / 32
  skipped files; 6695 passed / 317 skipped / 1 todo; exit 0, fully green.**
- `platform-mcp` (branch): `tsc --noEmit` exit 0; `vitest run` → **75 failed /
  613 passed / 18 skipped (706).**
- `platform-mcp` (main baseline, rerun by me): **75 failed / 613 passed / 18
  skipped (706) — BYTE-IDENTICAL counts.** Zero test-count delta introduced by
  the rename.
- The 75 pre-existing platform-mcp failures are sidecar/network/contract tests
  (`phala_outlook`, `phala_event_anchors`, `kala_timeline`, `bo_2-8`, bench/accuracy
  harnesses, tool_health integration). None reference `provenance_stamp`/`session_pin`
  — the only "provenance" matches in the failure set are `provenance_envelope`,
  an unrelated pre-existing L1/phala subsystem.
- Targeted touched-code tests pass: `m3_m4_session` + `m2_chart_selection` → 33/33
  passed. Renamed platform tests (`provenance_stamp.test.ts`,
  `envelope.judgment_flags.test.ts`, `ledger.ledger_version.test.ts`) → 78 passed;
  the DB-gated `sessions.provenance_stamp.integration.test.ts` skips cleanly
  (no DATABASE_URL) — same as baseline, not a silent drop.

**(3) Envelope / pin-field consumers updated — PASS.**
- `platform/src/lib/retrieval/envelope.ts` closed-vocabulary literal renamed;
  `platform-mcp/src/generated/envelope.ts` regenerated via codegen (source sha256
  updated). `npx tsx scripts/generate_envelope.ts --check` →
  "OK: generated/envelope.ts is up to date." Not hand-edited.
- Both wire sides of the served field moved together: platform route emits
  `provenance_stamp: pin`; platform-mcp `session.ts` reads `data.provenance_stamp`
  and types it `ProvenanceStampResponse`. A repo-wide grep found NO other consumer
  of the `session_pin` served field (no web/frontend/Python reader), so the field
  rename cannot break an un-migrated caller.

**(4) Grep for old name outside changelogs returns zero — PASS.**
- `grep -rE "session_pin|SessionPin|sessionPin"` over `platform/src` +
  `platform-mcp/src` → only **two lines**, both inside `provenance_stamp.ts`'s own
  RC-13 audit note explicitly recording the prior name for traceability
  (lines 5–6). No live use. Old drift-flag literal `session_pin_refreshed` → zero
  hits anywhere.
- Remaining `SESSION-PIN` / "session pin" hits are design-document section titles
  ("§31.3 SESSION-PIN COLLISION", "§10.6 SESSION STABILITY") and opaque test-key
  string literals (`r5-w4-session-pin-integration-test`) — neither is the
  `session_pin` code token; renaming design section names would misrepresent the
  design doc, and the test keys are arbitrary unique strings with no behavioral role.

## Adversarial failure-mode hunt (brief §D.4(d)) — nothing blocking found

- **Missed consumer / incomplete sweep:** none. Repo-wide grep (ts/tsx/py/json)
  for the served field and identifiers is clean beyond the intentional audit note.
  `concept_ledger/ledger.ts` (a 2-line doc-comment ref to
  `session_pin.ts#getLatestChartBuild`) WAS correctly swept — worth noting the
  implementer's summary listed only its test file, but the code file change is
  present, correct, and in-scope.
- **Storage-key regression:** the internal `mcp_sessions.state_json.pins[chart_id]`
  key is deliberately **UNCHANGED** (verified). This is correct: renaming it would
  orphan every persisted session's pin data — a behavior/data change the "zero
  behavior/storage change" bar forbids. Right call.
- **Closed-vocabulary drift:** the second emitted flag
  `concept_ledger_updated_mid_provenance_stamp_refreshed` is NOT in
  `JUDGMENT_FLAG_CODES` — but it was NOT in the list on `main` either (only
  `chart_rebuilt_mid_*` was). The rename faithfully preserved this pre-existing
  latent condition (renamed the one that was registered, left the one that wasn't).
  Zero regression; a valid subject for a separate defect row, not RC-13.
- **codegen chained-check red herring:** `npm run codegen:check` HALTs on
  `generate_registry_shims.ts` at `getStrengthCapability.input_schema.frame.description`
  (a BinaryExpression the static evaluator rejects). I reproduced the IDENTICAL
  halt on `main` — pre-existing, unrelated to RC-13 (the diff touches no descriptor).
  The RC-13-relevant leg (`generate_envelope.ts --check`) is green.

## Scope compliance (brief §J / must_not_touch) — CLEAN

`git diff --name-only main...HEAD` = 15 files: the PARIPRASHNA doc + 14
platform/platform-mcp source/test files. No FROZEN orchestrator / WriterBase /
`ga_*|bo_*|ka_*|ph_*|mi_*` writer, no `kala_*`/gochara serving semantics, no
`chart_facts` semantics, no D-4b branch is touched.

## Non-blocking observations (do NOT gate acceptance)

1. Generic `pin`/`Pin` identifiers are intentionally retained (`buildPinPatch`,
   `readPinFromState`, `computeCurrentPinValues`, `getSessionWithPin`,
   `persistActiveChartAndPin`, `pinChartId`, the `ProvenanceStampResult.pin`
   field, the `state_json.pins` key). These are not the `session_pin` token the
   brief scoped, and the storage key must stay for backward-compat. A cosmetic
   inconsistency (e.g. `getSessionWithPin` now returns a `ProvenanceStampResponse`),
   not a DONE-bar failure. The module's own audit note scopes RC-13 to "internal
   identifiers + the served JSON field," consistent with this.
2. The served JSON field visible to MCP-tool callers (recall_session / select_chart
   result, /api/mcp/session response) did change name `session_pin` →
   `provenance_stamp`. Both wire sides moved in lockstep and no external consumer
   exists, so no runtime break — this is exactly the "served-JSON-field rename"
   the brief authorized.

## Verdict

**ACCEPT.** RC-13 satisfies its §E DONE bar verbatim: rename complete + consistent
(code + PARIPRASHNA doc), full suites green with zero behavior delta proven against
the main baseline, envelope/field consumers updated and codegen-clean, old-name grep
zero outside the intentional audit note, scope clean of every must_not_touch path.
The broader D-16 storage restructuring is correctly left unexecuted and documented
as separate work — RC-13 was naming-only, per its own bar.
