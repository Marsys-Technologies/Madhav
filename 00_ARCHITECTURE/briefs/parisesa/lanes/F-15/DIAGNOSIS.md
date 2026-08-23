---
lane: F-15
stream: S2 (MĀTRĀ)
stage: D — DIAGNOSE
status: REPRODUCES (identical mechanism to F-14; same fix closes both)
diagnosed: 2026-08-16
files_owned_this_lane: platform-mcp/src/tools/registry_bridge.ts (S2 HOT lease)
companion_lanes: F-14 (full diagnosis lives there — this is a companion, not a duplicate)
---

# F-15 DIAGNOSIS — assess_marriage never returns the W7 substance-inline reading digest

**This finding shares its full mechanism trace with F-14 (`../F-14/DIAGNOSIS.md`) — read
that document for the complete file:line trace, the three-layer defect stack (§3.1-3.4), the
sibling census (§4), and the blast radius (§5). This document covers only what is specific
to F-15: its own live reproduction and the one place its mechanism text differs from F-14's
(the internal domain key name).**

## 1. Live reproduction

**Reproduce_cmd (verbatim):**
```
mcp__marsys-jis-direct__assess_marriage({chart_id: '482012f1-710e-4a25-994a-93821f5871aa', reading_depth: 'deep_dive'})
```

Ran against the live MCP server. Raw output saved to `evidence_deep_dive.json` in this
directory. Top-level `object` keys: `{"kernel": {...}, "composition_report": {...}}` — no
`reading`, `domain_completeness`, or `completeness_directive` anywhere.
`composition_report.omitted_sections` = `["grounding", "evidence"]` (same deep_dive
budget-side-effect as F-14 — see F-14 DIAGNOSIS §3.3/§5 "NEW" item; this is not
marriage-specific).

Re-ran at default (`standard`) depth (`evidence_standard_depth.json`) to isolate the
domain-specific defect from the depth-driven budget effect: `grounding` IS present
(`included_layers: ["kernel","grounding","evidence"]`) but contains only
`orientation_context` + `orientation_ok` — no `reading` key, no `domain_completeness` key,
no `completeness_directive` key.

**Verdict: REPRODUCES**, on both budget settings tried. Not `ALREADY-FIXED`.

## 2. Claim decomposition

Same four sub-claims as F-14 (C1-C4), substituting `assess_marriage`/`relationship` for
`assess_health`/`health`. All verified TRUE by the same evidence pattern. See F-14
DIAGNOSIS.md §2 for the full table — it applies verbatim with the substitution.

## 3. Mechanism — confirmed identical to F-14, with one domain-key note

Traced the same three file:line sites as F-14:

1. **`DOMAIN_READING_FAMILIES`** (`registry_bridge.ts:1034-1037`) has no `relationship` key
   (F-14's finding text calls this out correctly — `relationship` is confirmed as
   `assess_marriage`'s internal domain key, matching `DOMAIN_DIRECT_VARGAS`'s
   `relationship: ['D9']` entry in `register_d8_assess_domain.ts:186`, the analogous map one
   layer down that already supports marriage's data computation).
2. **`attachDomainReading`'s early-return** (`registry_bridge.ts:1573`,
   `if (families_total === 0) return`) — same code path, `domain='relationship'` hits the
   same `undefined` lookup.
3. **The call sites don't exist**: `assess_marriage`'s handler
   (`registry_bridge.ts:2959-2995`) never calls `attachDomainCompleteness` or
   `attachDomainReading` — confirmed by direct read, the handler goes straight from building
   `response` (line 2989) to `buildAssessResponse(...)` (line 2990), unlike `assess_career`'s
   two extra lines (`:3030`, `:3032`).
4. **The universal `buildAssessResponse` key-mismatch** (`registry_bridge.ts:2925`,
   `response['completeness']` vs. the actual key `response['domain_completeness']`) — applies
   here too, though moot until #1-#3 are fixed (nothing sets `response['reading']` or
   `response['domain_completeness']` for marriage today regardless).

**One correction to the finding's own mechanism text**: the finding writes "same root cause
and same file as F-14 — one fix (adding health/relationship keys to
DOMAIN_READING_FAMILIES) likely closes both." This is TRUE for restoring the `reading` field,
but as F-14's DIAGNOSIS §3.3 establishes, adding the map keys alone is insufficient — the
`attachDomainCompleteness`/`attachDomainReading` call sites must ALSO be added to both
handlers (they don't exist for either domain today), and the SPEC should additionally cover
the `buildAssessResponse` key-mismatch (§3.4) if `domain_completeness`/`completeness_directive`
are to be restored for any domain, not just `reading`.

## 4. Sibling census

Identical to F-14 §4 — see that table. No marriage-specific siblings beyond what's already
covered there (the four `DOMAIN_READING_*` maps and the four-tool call-site census).

## 5. Blast radius

Identical to F-14 §5. No marriage-specific additions. **One fix (adding `relationship` +
`health` to the five `DOMAIN_READING_*` maps, wiring the two `attachDomain*` calls into both
`assess_marriage` and `assess_health` handlers, and fixing the `buildAssessResponse`
key-mismatch) closes F-14 and F-15 together** — they are the same defect at two domain
values, not two defects.
