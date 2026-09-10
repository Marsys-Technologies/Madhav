---
lane: F-05
stream: S5 MŪLA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, SPEC.md (spec_version 1.0), DIAGNOSIS.md; no REVIEW_LEADS.md present.
Read source at /Users/Dev/par-night/main-ro:
- platform/python-sidecar/brahmagyan/l0_remedy_loader.py (full, 406 lines)
- platform/python-sidecar/pipeline/orchestrator/writers/bg_remedies.py (full, 75 lines)
- platform/python-sidecar/brahmagyan/remedy_corpus/tantric.yaml (full, 77 lines)
- platform/src/lib/retrieval/registry/layers/register_d7_channel.ts (lines 1665–1735)
- platform/python-sidecar/brahmagyan/l0_remedy_corpus.py (lines 44–62)

Traced all three exit tests against current source without execution (reviewer role; no worktree write access).

## Q1 — Mechanism vs. symptom

PASS. The spec targets the mechanism: load_remedies() (l0_remedy_loader.py:221) has zero production
callers — the entire YAML ingestion path is disconnected from the registered writer bg_remedies.py.
The fix wires bg_remedies.py to call load_remedies(glob='tantric.yaml') after seed_remedy_corpus(),
not a query-layer or schema workaround.

## Q2 — Diagnosis sub-claims mapped to spec elements

All sub-claims in DIAGNOSIS §2/§4/§5 map to spec elements (§7 coverage table):

- (a) Query logic correct (register_d7_channel.ts:1720) → §7: no change to file. ✓
- (b) tantric.yaml exists at remedy_corpus/tantric.yaml → §3 exit test loads it in dry_run. ✓
- (c) load_remedies() zero production callers → §2 fixes bg_remedies.py to call it. ✓
- (d) bg_remedies.py never emits 'tantric' → §2 fix + exit test asserts 'tantric' in notes. ✓
- Tantric gate must be preserved (DIAGNOSIS §5) → §6 confirms load_remedies() gate unchanged. ✓
- All YAML siblings orphaned (DIAGNOSIS §4) → §4 lists all 13, 1 wired, 12 excluded. ✓
- remedy_review_queue dependency → §6 confirms gate routes failures to queue; no bypass. ✓

## Q3 — Exit tests genuinely fail on today's code

Traced against current source. All three exit tests FAIL today:

test_tantric_yaml_produces_rows_in_dry_run:
  Calls load_remedies(YAML_DIR, conn=None, dry_run=True, glob='tantric.yaml').
  Current signature at l0_remedy_loader.py:221: def load_remedies(yaml_dir, conn=None, dry_run=False)
  — no glob parameter.
  Today: TypeError: load_remedies() got an unexpected keyword argument 'glob'. FAIL. ✓

test_bg_remedies_dry_run_includes_tantric:
  Calls RemediesWriter().run(ctx) with ctx.dry_run = True (MagicMock).
  Current dry_run path (bg_remedies.py:33–45): calls build_all_remedies(), returns
  notes = "dry_run: would insert N remedies (M live) into brahma_remedy_corpus".
  'tantric' in notes.lower() → False. Assertion fails. FAIL. ✓

test_load_remedies_has_glob_param:
  inspect.signature(l0_remedy_loader.load_remedies) → params = {yaml_dir, conn, dry_run}.
  'glob' in sig.parameters → False. Assertion fails. FAIL. ✓

Note: SPEC §3 says "Both tests fail" but the file contains 3 tests; the third also fails today.
The FAIL-today prose for test_bg_remedies_dry_run_includes_tantric uses the word "passes" ("passes
but notes contains no mention of tantric") — contradictory, since the assertion fails. The test
code is correct and the fix logic is sound; this is a description wording error only, not blocking.

## Q4 — Sibling sites covered

SPEC §4 table enumerates 13 YAML files (not 12 as stated in prose — counted from both DIAGNOSIS §4
list and SPEC §4 table: ayurvedic, behavioral, charity, gemstones, mantras, puja, supplemental,
supplemental_b, supplemental_c, tantric, vastu, vrata, yantras = 13). Prose says "12 YAML files …
1 wired, other 11 excluded" — off-by-one; the table itself is complete with 12 exclusions.

All 12 excluded YAMLs carry stated reasons:
- 8 files (ayurvedic/behavioral/charity/gemstones/mantras/puja/vrata/yantras): DB has hardcoded
  rows; overlap audit needed.
- 3 supplemental files: content/category mapping unknown.
- vastu.yaml: vastu absent from DB and outside register_d7_channel.ts query scope; flagged as
  separate lane.

All reasons substantiated by DIAGNOSIS. PASS.

## Q5 — Recurrence guard

test_load_remedies_has_glob_param asserts 'glob' in inspect.signature(load_remedies).parameters.
Directly detects the defect class: if the glob param is removed, guard fails immediately.
test_bg_remedies_dry_run_includes_tantric also fails if the bg_remedies.py call is removed.
Both guards detect mechanism, not a proxy. PASS.

## Q7 — Unverified assumptions / citation check

All file:line citations verified against /Users/Dev/par-night/main-ro:

- l0_remedy_loader.py:221 — def load_remedies(yaml_dir, conn=None, dry_run=False): confirmed. ✓
- l0_remedy_loader.py:244 — for yaml_path in sorted(yaml_dir.glob('*.yaml')): confirmed. ✓
- l0_remedy_corpus.py:49-52 — VALID_REMEDY_TYPES = {"mantra", …, "tantric", …}: confirmed. ✓
- bg_remedies.py:21 — import from l0_remedy_corpus: confirmed. ✓
- bg_remedies.py:34 — if ctx.dry_run: confirmed. ✓
- bg_remedies.py:47 — counts = seed_remedy_corpus(...): confirmed. ✓
- register_d7_channel.ts:1670 — capability definition start: confirmed. ✓
- register_d7_channel.ts:1712 — handler start: confirmed. ✓
- register_d7_channel.ts:1721 — cited for WHERE conditions array: minor off-by-one; conditions
  array (const conditions: string[]) starts at line 1720; line 1721 is const values: unknown[].
  Trivial — query logic claim is correct. ✓

writer_asset: bg_remedies and data_delta: narrow correctly declared. Light asset → rebuild after
merge per PROTOCOL rebuild policy; shadow run mandatory (writer-layer lane). SPEC §6 consistent. ✓

## Verdict: COMPLETE
