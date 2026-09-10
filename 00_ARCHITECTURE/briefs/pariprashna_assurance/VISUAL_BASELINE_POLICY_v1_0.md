---
artifact: PARIPRASHNA_VISUAL_BASELINE_POLICY
version: "1.0"
status: CURRENT
date: 2026-08-28
author: S2 (Conversation & Reading Experience) coverage-completion pass
relates_to:
  - platform/tests/pariprashna/gates/g-transmute.spec.ts
  - platform/tests/pariprashna/playwright.config.ts
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_1.md (§5.0/§8.1)
---

# Paripraśna — Visual Regression Baseline Policy v1.0

## What this resolves

Test plan §5.0 named "Baseline screenshot store + diff policy" as
"Not yet established" — a listed blocking prerequisite before the §8.1
visual-regression battery can run. This document, plus the baseline PNGs
it points at, resolves that.

## Where the baseline store lives (the existing, project-native mechanism —
not a new one)

`platform/tests/pariprashna/gates/g-transmute.spec.ts`'s "G-TRANSMUTE
(soft, informational) — visual snapshots per progress checkpoint" suite
already existed, pre-authored, gated behind `MARSYS_UPDATE_VISUALS=1`
(never run because "no baselines exist yet" — its own comment). This
pass generated the first baseline set using Playwright's own
`toHaveScreenshot()` mechanism (the SAME mechanism already used
project-wide for the legacy Consume/chat-v2 surface's
`__visuals__/*.spec.ts-snapshots/` directories — this is not a new
pattern, just the first Pariprashna-surface use of it):

```
platform/tests/pariprashna/gates/g-transmute.spec.ts-snapshots/
  adaptive-3-pass-25pct-chromium-darwin.png
  adaptive-3-pass-50pct-chromium-darwin.png
  adaptive-3-pass-75pct-chromium-darwin.png
  adaptive-3-pass-100pct-chromium-darwin.png
  adaptive-3-pass-25pct-mobile-390x844-darwin.png
  adaptive-3-pass-50pct-mobile-390x844-darwin.png
  adaptive-3-pass-75pct-mobile-390x844-darwin.png
  adaptive-3-pass-100pct-mobile-390x844-darwin.png
```

8 baselines: one fixture (`adaptive-3-pass`, the harness's standard
multi-pass reading fixture) × 4 progress checkpoints (25/50/75/100%) × 2
viewport projects (chromium desktop, mobile-390x844) — captured
2026-08-28 against the replay-fixture harness (`scripts/replay/server.ts`),
NOT the live deployed site (this is a deterministic-fixture-replay
baseline, appropriate for pixel-diffing; the DEPLOYED-site visual state is
covered separately by this same session's LIVE screenshots in
`.playwright-mcp/s2-scratch/`, which are evidence artifacts, not a
pixel-diff baseline).

## Diff policy

- **Threshold:** `maxDiffPixels: 200` (already set in the spec, unchanged
  by this pass) — a small, deliberate tolerance for anti-aliasing/font
  hinting noise, not a loose threshold that would hide a real regression.
- **Re-run:** `MARSYS_UPDATE_VISUALS=1 npm run pariprashna:gates -- --grep "screenshot at each progress checkpoint"`
  (no `--update-snapshots`) diffs the CURRENT render against these
  baselines and fails on any pixel delta beyond the threshold. This pass
  ran that exact command immediately after generating the baselines and
  confirmed a clean 2/2 pass (0-diff self-comparison) — the mechanism is
  proven working, not merely configured.
- **Re-baselining:** intentional visual changes re-run with
  `--update-snapshots` (still requiring `MARSYS_UPDATE_VISUALS=1`) and the
  new PNGs are reviewed in the PR diff like any other committed asset —
  a reviewer sees the before/after images directly in the GitHub PR UI.
- **Scope of this pass:** only the ONE pre-existing soft/informational
  suite (`adaptive-3-pass` fixture) was activated. The other fixtures the
  gate suite already exercises behaviorally (`giant-table`,
  `citation-dense`, `honest-gap`, `1-byte-trickle`, `gemini-slabs`) do NOT
  yet have pixel baselines — extending `MARSYS_UPDATE_VISUALS` coverage to
  those fixtures, and to more Portal states (empty, thinking, error,
  reconnecting — test plan §8.1's full state list), is real follow-up
  work, not completed here. This pass unblocks the mechanism and proves
  it works; it does not claim full §8.1 state coverage yet.

## Relationship to the other G-gates (why a literal pixel baseline is the
narrower, secondary check here — by the suite's own design)

The G-TRANSMUTE *hard* gate (already passing, RED-proof verified, no
baseline needed) already proves the stronger, more general claim
byte-identically: a committed block's DOM never changes shape after
commit, across every progress checkpoint, for FIVE fixture types
(`adaptive-3-pass`, `giant-table`, `citation-dense`, plus G-CLS's
`honest-gap`, G-CARET's `1-byte-trickle`/`gemini-slabs`). G-CLS, G-VIEWPORT,
G-CARET, and G-PILL similarly prove settled-block-stability, height
stability, caret containment, and scroll-follow behavior as BEHAVIORAL
invariants with demonstrated-can-fail red-proofs — a stronger and more
maintainable check than a raw pixel diff, which is why the pixel-snapshot
suite is marked "soft, informational" in the source rather than a hard
gate: it catches visual drift a behavioral assertion wouldn't (font
rendering, color, spacing), but the behavioral gates are the primary,
load-bearing proof.
