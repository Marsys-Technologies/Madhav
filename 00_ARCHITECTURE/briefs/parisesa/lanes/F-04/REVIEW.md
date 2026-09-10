---
lane: F-04
stream: S5 MŪLA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-2
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, F-04/SPEC.md, F-04/DIAGNOSIS.md (no REVIEW_LEADS.md present). Verified against `/Users/Dev/par-night/main-ro` (clean origin/main checkout).

Source files read/grepped:
- `platform-mcp/src/tools/register_p1_reference.ts` lines 405-449 — confirmed handler lines and strings verbatim
- `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/` directory listing — confirmed no `query_nakshatra_catalog.ts` exists, only `query_nakshatra_medical.ts`
- `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_nakshatra_medical.ts` — confirmed wraps `bg_nakshatra_medical` (body-part-only, 27 rows), NOT `reference_nakshatra`
- `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/query_dasha_systems.ts` — confirmed mirror template: 88 lines, ~60-line CapabilityDescriptor body, same structural pattern
- `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/__tests__/query_dasha_systems.test.ts` — confirmed test pattern the spec says to mirror
- `platform/src/lib/retrieval/registry/layers/L0_brahmagyan/index.ts` — confirmed registration pattern: import at line 60, array entry at line 125, named export at line 192
- `platform/supabase/migrations/238_bg_nakshatra_tables.sql` — confirmed `reference_nakshatra` table schema with all claimed columns
- `platform-mcp/src/tools/` listing — confirmed no `__tests__/` subdirectory exists there currently (co-located test pattern in use); F-22/SPEC.md uses the same `__tests__/` path, consistent between sibling lanes
- F-22/SPEC.md — read to verify the sibling cross-reference and ensure F-04 doesn't duplicate or conflict
- Migration directory listing — noted migration numbers 302 and 306 are absent (gap 251-329); squash sentinel accounts for only 057-157 range, so 302/306 are simply missing files

## Q1 — Mechanism vs symptom

COMPLETE. The spec addresses all three components of the mechanism:
1. **Capability gap** (no `query_nakshatra_catalog` exists) → §2.1 creates the new file mirroring `query_dasha_systems.ts`
2. **Registration gap** (new capability would be unreachable until registered) → §2.2 adds import + array entry + named export to `index.ts`
3. **Handler defect** (unconditional `query_classical_texts` call + false `fallback_reason`) → §2.4 repoints to new URI, inverts honesty fields, deletes false string at line 442 and inline comment at lines 429-434

This is not a symptom-only fix.

## Q2 — Sub-claim coverage

All four DIAGNOSIS sub-claims mapped explicitly in SPEC §7:

| Diagnosis claim | SPEC element | Verified |
|---|---|---|
| (a) description promises structured fields | §2.1 new capability returns exactly those fields | ✓ |
| (b) always routes through classical-text search | §2.4 repoint | ✓ |
| (c) fallback_reason/comment assert false absence (§N.7) | §2.4 inverted on success, false string deleted | ✓ |
| (d) structured table real, populated, L1 authority | §2.1 now queried | ✓ |

DIAGNOSIS §4 also flagged `register_p1_aliases.ts:990` as a `query_classical_texts` call site outside scope. SPEC §4 does not address it, correctly noting it's out of this lane's scope (alias-tool, different pattern). Not an unmapped deficiency.

No unmapped claims found.

## Q3 — Exit test fails on current code

YES — by line-trace:

- Assertion `structured_filter_applied: true` → line 441 hardcodes `false` unconditionally → FAIL
- Assertions for `vimshottari_lord: 'jupiter'`, `presiding_deity: 'Aja Ekapada'`, `nakshatra_gender: 'Male'`, `gana: 'Manushya'` → lines 436-438 call `query_classical_texts`, which returns citation-object rows from muhurta_chintamani/brihat_samhita/bphs — none of these fields appear in those rows → FAIL
- OCR-junk assertion ("no garbled fragments") → DIAGNOSIS §1 confirms two junk rows (`brihat_samhita:PG1005:C2`, `bphs:PG513:C2`) are present in current classical-text results → FAIL
- Regression assertion (unrecognized nakshatra degrades gracefully) → current code already routes everything to `query_classical_texts` so the degradation "works" in the wrong direction; after the fix this assertion confirms the fallback path is preserved — this part would PASS on current code, but that's correct (regression guards a behavior that must survive the fix).

Net: exit test would produce clear red output on today's source. No simulation required beyond line-trace.

## Q4 — Sibling sites covered

SPEC §4 identifies two candidates:
- **F-22** (`ref_dasha_systems_get`) — kept as own spec, justified: F-22 is a pure repoint (capability already exists), F-04 requires a new capability file first — different build effort. Both cross-reference each other. Reasonable split per lane discipline.
- **`ref_dignity_reference_get`** — correctly excluded: DIAGNOSIS §4 confirms it already implements the structured-first pattern correctly (partial fallback, real `information_schema`-backed behavior). Not part of the defect class.

The only uncovered mention is `register_p1_aliases.ts:990` — the DIAGNOSIS explicitly flagged it as out-of-F-04 scope. Correct exclusion.

## Q5 — Recurrence guard

SPEC §5 defers to F-22/SPEC.md §5 (identical recommendation filed once for both lanes). The guard is a lint/CI check for `fallback_reason` strings containing "no structured... table exists" or "confirmed absent" without a real `information_schema` check. This targets the exact defect class — a hardcoded false-absence assertion in a honesty field — not a weak proxy. Deduplication is appropriate since both lanes share the same §N.7 defect pattern.

## Q7 — Verified assumptions / file:line citations

| Claim | Verification result |
|---|---|
| Handler at lines 412-449 in `register_p1_reference.ts` | VERIFIED exactly — server.tool block at 413, false fallback_reason at 442, end at 449 |
| `query_classical_texts` call at line 436 | VERIFIED |
| `fallback_reason` string text at line 442 | VERIFIED verbatim |
| No `query_nakshatra_catalog.ts` in `L0_brahmagyan/` | VERIFIED — only `query_nakshatra_medical.ts` present |
| `query_nakshatra_medical.ts` targets `bg_nakshatra_medical` (different, narrower table) | VERIFIED — wraps `bg_nakshatra_medical`, 27 rows, body-part only |
| `reference_nakshatra` has columns: vimshottari_lord, presiding_deity, nakshatra_gender, gana, varna, nadi, body_part, symbol | VERIFIED against migration 238 lines 35, 36, 50, 41, 46, 42, 65, 59 |
| `reference_nakshatra_pada` exists for pada lords | VERIFIED — migration 238 line 92 |
| `query_dasha_systems.ts` mirror template (~60 lines) | VERIFIED — 88 lines total, ~72 for the CapabilityDescriptor body |
| `index.ts` registration pattern (import + array + export) | VERIFIED — lines 60, 125, 192 |
| Migration 302 (canonical) and 306 (body_part fix) | NOT VERIFIABLE — migration numbers 251-329 absent from directory; squash sentinel only covers 057-157. Table and schema are confirmed correct via migration 238; the 28-row data claim is from live DB verification in DIAGNOSIS (not checkable from source). This is background context, not a prescription the builder must act on — not a material deficiency. |
| No rebuild required (serving-layer only) | VERIFIED — no writer files touched, `reference_nakshatra` is pre-existing data |

One minor note: `platform-mcp/src/tools/__tests__/` does not currently exist (tests are co-located in `src/tools/`). F-22/SPEC.md uses the same `__tests__/` path convention; both F-04 and F-22 builders will create this directory. The `__tests__` pattern is used elsewhere in platform-mcp (`src/__tests__`, `src/lib/__tests__`, `src/resources/__tests__`), so this is a reasonable choice — the builder must create the directory. Not a deficiency.

## Named deficiencies

None.

## Verdict: COMPLETE

Spec is precise, mechanism-rooted, all DIAGNOSIS sub-claims mapped, exit test will fail cleanly on current code, sibling coverage is justified, recurrence guard targets the exact defect class, and all material `file:line` citations check out against current source. The migration-number citations (302, 306) are unverifiable but are background context only — the table and schema are confirmed by migration 238. Ready for builder.
