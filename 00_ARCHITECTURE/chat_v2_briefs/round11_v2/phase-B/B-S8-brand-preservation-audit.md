---
canonical_id: R11B_B_S8
session_id: B-S8
title: Marsys brand preservation audit — verify gold/charcoal aesthetic intact
phase: R11.B — Look-and-Feel
depends_on: [B-S7]
flag: FLAGLESS (verification only)
client_side: yes
authored: 2026-05-22
---

# B-S8 — Marsys Brand Preservation Audit

## Context

After B-S1..B-S7 land, verify that every Marsys brand element listed in `NATIVE_RULINGS §1` still renders identically to pre-R11.B. This is a verification + visual-snapshot session, not a feature session.

## Files in Scope

- `platform/tests/visual/R11B_brand_preservation.spec.ts` (new) — Playwright visual-regression test that asserts:
  - `.brand-cta` send button visible + gold-gradient
  - Gold-hairline borders on sidebar + main-pane right edge
  - `.v2-user-bubble::after` speech-tail present
  - Devanagari double-danda accent on Welcome H2 (if present)
  - Mandala-spin animation (if applicable to consume route)
  - Radial-gradient consume backdrop intact
- `platform/tests/visual/R11B_brand_preservation_baseline/` — baseline screenshots captured pre-R11.B; new screenshots compared.

## Files MUST NOT Touch

- Any production component
- Sacred components
- Provider adapters
- Phase 4C files

## Acceptance Criteria

1. Visual-regression test passes on flag=false state (baseline preserved).
2. Visual-regression test passes on flag=true state for: speech-tail, gold borders, brand-cta send button, sidebar dark surface.
3. The acceptance is that brand elements are present, not byte-identical pixels (B-S1..B-S7 do introduce visual changes per native ruling).
4. Test output documented in commit body.

## Pre-commit Gates

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavR11B/platform
test -f tests/visual/R11B_brand_preservation.spec.ts && echo "PASS"
npx playwright test tests/visual/R11B_brand_preservation.spec.ts 2>&1 | tail -10
```

## Commit Template

```
test(chat-v2): R11.B Marsys brand preservation audit (B-S8)

Visual-regression test verifies Marsys brand elements (speech-tail, gold
borders, brand-cta send, sidebar dark surface, mandala accents) remain
present after R11.B visual changes. Flagless verification session.
```

## Decision Log

*(Executor: paste Playwright report; flag any elements missing.)*
