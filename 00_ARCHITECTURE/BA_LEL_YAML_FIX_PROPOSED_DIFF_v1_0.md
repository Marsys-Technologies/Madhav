---
artifact: BA_LEL_YAML_FIX_PROPOSED_DIFF_v1_0.md
canonical_id: BA_LEL_YAML_FIX_PROPOSED_DIFF
version: 1.0
status: PROPOSED — awaiting native sign-off; NOT applied to the canonical LEL markdown
created: 2026-07-05
scope: BA_FULL_ASSET_AUDIT Phase 1 item #12 (mi_jivanaghatana LEL content defect)
---

# LEL YAML parse-failure fix — proposed diff (native sign-off required)

## Why this exists

`mi_jivanaghatana` (L5 Mīmāṃsā LEL root asset) parses YAML event blocks out of
`01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md`. Per CLAUDE.md §C hard rule, this file is
a canonical fact artifact — it may **not** be edited without native sign-off + a
version bump (B.8). This session found the parse-failure root cause and prepared
a mechanical, content-preserving fix, but has **not** applied it.

## Root cause (confirmed by direct parse, 2026-07-05)

Of 63 total ` ```yaml ` blocks in the file, **29 fail to parse** as valid YAML.
Every failure has the same shape: a plain (unquoted) YAML scalar value —
typically `description`, `native_reflection`, `notes`, or `retrodictive_reasoning`
— contains a literal `: ` (colon + space) or a trailing `:` inside ordinary
narrative prose (e.g. `retrodictive_reasoning: Per doc: "Worked at Cognizant..."`).
YAML's block-mapping parser treats that embedded colon as the start of a new
key, which breaks the surrounding mapping. This is a pure YAML-quoting defect —
**no factual content is wrong**, the file just doesn't quote prose that happens
to contain a colon.

The writer's parser (`platform/python-sidecar/pipeline/orchestrator/writers/
mi_jivanaghatana.py::_parse_lel_markdown`) already does the right thing on the
code side (per commit d8dc7ed0): it logs each skipped block individually with
the parse exception rather than silently swallowing it. The remaining problem
is purely in the markdown content.

## Proposed fix (mechanical, content-preserving)

A script wrapped every offending scalar value in double quotes (escaping any
embedded double quotes), leaving flow collections (`[...]`), block scalars
(`|`, `>`), and already-quoted values untouched. **No narrative text, dates,
signal ids, or field structure was changed — only quoting was added** so YAML
parses the existing prose correctly.

Result: parseable blocks went from **34/63 → 48/63** (26 lines touched, all
pure quoting). The full unified diff is saved alongside this report at
`00_ARCHITECTURE/BA_LEL_YAML_FIX_PROPOSED_DIFF_v1_0.patch` for native review —
**it has not been applied to `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md`.**

## Remaining 15 blocks NOT fixed by the mechanical pass (need manual native review)

These have a harder shape the automated single-line quoting couldn't safely
resolve (mostly: a plain scalar value that wraps across multiple physical
lines without YAML block-scalar markup, or a flow-sequence `[...]` entry that
itself contains an unescaped colon inside a parenthetical):

| # | EVT / block id |
|---|---|
| 1 | `EVT.2000.XX.XX.01` |
| 2 | `EVT.2004.01.XX.01` |
| 3 | `EVT.2007.XX.XX.03` |
| 4 | `EVT.2011.06.XX.01` |
| 5 | `EVT.2013.XX.XX.01` |
| 6 | `EVT.2013.12.11.01` |
| 7 | `EVT.2018.11.28.01` |
| 8 | `EVT.2019.05.XX.01` |
| 9 | `EVT.2021.01.XX.01` |
| 10 | `EVT.2025.05.XX.01` |
| 11 | `PATTERN.SPORTS_LUCK.01` |
| 12 | `PATTERN.SLEEP_IRREGULARITY.01` |
| 13 | `PATTERN.COMPUTER_APTITUDE.01` |
| 14 | `GAP.TEPPER.DATES.01` |
| 15 | a stray version-history block (`v1.0 (2026-04-17, superseded same-session by v1.1)`) matched by the block-extraction regex but is not an event block at all — likely a changelog fragment inside a ` ```yaml ` fence by mistake; worth checking whether it should be a plain code fence instead.

These 15 need either (a) converting the offending scalar to a YAML block
scalar (`notes: |` style) so embedded colons/quotes are never an issue again,
or (b) native review of the exact intended text before mechanically quoting it
(a few of these have nested flow-sequences with parenthetical asides that a
naive quote-wrap would mangle).

## What this session did NOT do

- Did not touch `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md`.
- Did not bump the LEL version.
- Did not silently "fix" the remaining 15 blocks with a guess.

## Recommended next step

Native reviews the `.patch` file, confirms no narrative meaning changed for
the 34 blocks it touches, and either (a) approves applying it verbatim with a
version bump to `LIFE_EVENT_LOG_v1_3.md` (or a `v1.2.1` patch note per B.8
changelog discipline), or (b) requests changes. The remaining 15 blocks should
be queued as a follow-up pass once the block-scalar convention is settled.
