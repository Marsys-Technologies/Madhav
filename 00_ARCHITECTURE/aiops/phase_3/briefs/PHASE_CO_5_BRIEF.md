---
status: OPEN
session_id: AIOPS_CO_5
phase: CO.5
phase_name: "Visual design pass — typography, spacing, color, motion"
next_session: AIOPS_CO_6
authored_at: 2026-05-14
authored_by: AIOPS_PHASE_3_MASTER_PLAN_v1_0
---

# CLAUDECODE_BRIEF — AIOPS_CO_5
## AIOps Phase 3, Step 5 — Visual design pass

---

## §0 — Executor orientation

CO.5 is the visual polish pass. Per native Q7: best-in-class visual
experience is IN SCOPE. Anchor reference: Claude.ai aesthetic (closest to
existing Madhav dark-theme + reading-focused content per CO.0 UX research).

Five axes:
  1. Typography scale audit + consolidation
  2. Spacing rhythm (4/8 px grid)
  3. Color palette discipline (no new tokens; audit hardcoded hex values)
  4. Motion language (150 / 250 / 400 ms tiers)
  5. Component library audit + consolidation

This is JUDGMENT WORK. The brief specifies the targets; the executor makes
tasteful decisions within them. Bail if a choice feels arbitrary — surface
it for native review.

Behind `CONSUME_UI_V2_ENABLED`.

---

## §1 — Mandatory reads

```
1. CLAUDE.md
2. 00_ARCHITECTURE/aiops/phase_3/CONSUME_UI_SPEC_v1_0.md (component 8 — message bubble; design tokens audit)
3. 00_ARCHITECTURE/aiops/phase_3/UX_RESEARCH_v1_0.md (§3 visual aesthetic anchor)
4. 00_ARCHITECTURE/aiops/AIOPS_EXECUTION_RULES_v1_0.md
5. platform/tailwind.config.ts (or .js — design tokens source)
6. platform/src/styles/globals.css (or wherever CSS variables live)
7. platform/src/components/consume/**  (all components to audit + polish)
8. Reference: Anthropic brand-guidelines skill — `00_ARCHITECTURE` may have an existing brand audit pattern from Phase 1 CP.4 (CP4_BRAND_AUDIT.md)
```

---

## §2 — Scope

### may_touch
```
platform/src/components/consume/**                       # visual treatment
platform/src/components/chat/**                          # if shared chat primitives need updates
platform/src/components/shared/**                        # if shared primitives surface in consume UI
platform/src/styles/**                                    # design tokens + globals
platform/tailwind.config.*                                # only to ADD new safelist entries; not to add new colors
00_ARCHITECTURE/aiops/phase_3/CO5_VISUAL_AUDIT.md         # NEW report
CLAUDECODE_BRIEF.md
```

### must_not_touch
- adapters/, synthesis/, models/  (Phase 1 + 2 sealed)
- API routes (no functional changes in CO.5)
- Behavioral logic (CO.6 territory)
- New colors or fonts — anything not already in tailwind tokens

---

## §3 — Work plan

### 3.1 — Typography audit + consolidation

Walk every `text-*`, `font-*`, `leading-*`, `tracking-*` class in
consume/, chat/, shared/. Compile into a table.

Target: ≤ 6 distinct text sizes used across the consume surface. If more,
identify which to consolidate. Common scale: `text-xs`, `text-sm`,
`text-base`, `text-lg`, `text-xl`, `text-2xl`.

Font weights: ≤ 3 (normal, medium, semibold).

Author findings + decisions in `CO5_VISUAL_AUDIT.md` §1.

### 3.2 — Spacing rhythm

Walk `p-*`, `m-*`, `gap-*`, `space-*` usage. Verify all values align with
4/8 px grid (Tailwind's default).

Flag any arbitrary values (`p-[13px]` etc.) and either justify or replace
with the nearest grid value.

Author findings in `CO5_VISUAL_AUDIT.md` §2.

### 3.3 — Color discipline

Walk every hex color literal in consume/, chat/, shared/. Each one:
- If it matches a Tailwind token (semantic or palette), replace inline hex
  with the token class.
- If it's a token equivalent (e.g., `#ef4444` = `red-500`), replace.
- If it has no token equivalent, FLAG it for native review — do NOT
  introduce a new token in CO.5.

Look at the CP.4 brand audit pattern (Phase 1) for the reference approach.
Reuse if a similar audit doc exists.

Author findings in `CO5_VISUAL_AUDIT.md` §3.

### 3.4 — Motion language

Three duration tiers:
- 150ms — micro-interactions (hover, focus, toggle)
- 250ms — standard transitions (sidebar expand, panel open)
- 400ms — entry/exit (message bubble appear, modal open)

Walk all `transition-*` and `duration-*` classes. Consolidate to these
three tiers. Easing: `ease-out` for entries, `ease-in-out` for transitions,
no spring physics in v1.

Author findings in `CO5_VISUAL_AUDIT.md` §4.

### 3.5 — Component library audit

Identify duplicate UI primitives in consume/ and adjacent dirs. Examples:
- Multiple button styles (consolidate to 2-3: primary, secondary, ghost)
- Multiple card patterns (consolidate)
- Multiple badge/chip styles (likely consolidated already; verify)

For each duplicate found, pick ONE keeper and migrate the others to use
it. If a duplicate has a justified difference (e.g., audit-specific badge
vs. message-metadata badge), document the difference.

Author findings in `CO5_VISUAL_AUDIT.md` §5.

### 3.6 — Side-by-side screenshots

Take before/after screenshots of:
- `/consume` empty state
- `/consume` mid-stream (a reasoning model query)
- `/consume` completed message with metadata badge
- Sidebar collapsed + expanded
- Per-message capsule expanded

Save under `00_ARCHITECTURE/aiops/phase_3/CO5_SCREENSHOTS/` (gitignored
after review).

Acceptance: after-screenshots match Claude.ai's polish bar — no obvious
inconsistencies, no jarring color jumps, no typographic chaos.

---

## §4 — Acceptance criteria

| AC | Check | Pass |
|---|---|---|
| AC.CO5.1 | `CO5_VISUAL_AUDIT.md` exists with §1–§5 populated | grep |
| AC.CO5.2 | Typography scale ≤ 6 sizes documented + enforced | audit |
| AC.CO5.3 | Spacing values on 4/8 px grid | grep arbitrary values; 0 unflagged |
| AC.CO5.4 | All hex literals either token-replaced or flagged for native review | grep + audit |
| AC.CO5.5 | Motion durations consolidated to 150/250/400ms tiers | grep |
| AC.CO5.6 | No new colors or fonts introduced | brand audit |
| AC.CO5.7 | Side-by-side screenshots captured (≥5 views) | file count |
| AC.CO5.8 | typecheck + lint + full test suite green | exit 0 |
| AC.CO5.9 | Scope-violation grep | SCOPE_OK |

---

## §5 — Session close

Commit:
```
feat(aiops-CO.5): visual design pass — typography, spacing, color, motion

- Typography consolidated to 6 sizes + 3 weights (CO5_VISUAL_AUDIT §1)
- Spacing values verified on 4/8 px grid (§2)
- Color discipline: hex literals replaced with tokens; N hardcoded values
  flagged for native review (§3)
- Motion language: 150 / 250 / 400 ms tiers consolidated (§4)
- Component library: M duplicates consolidated; remaining differences
  documented with rationale (§5)
- Side-by-side screenshots in CO5_SCREENSHOTS/ confirm polish bar

AC summary: 9/9 PASS
```

Rotate → CO.6.

---

## §6 — BAIL OUT

- A hex literal has no token equivalent AND removing it would degrade UX
  (e.g., specific health-pip green). Flag for native review; bail.
- Component consolidation requires changes that ripple beyond consume/
  (e.g., the button primitive is used by Observatory too).
- Screenshot tooling unavailable in this environment.

---

*End of PHASE_CO_5_BRIEF.md*
