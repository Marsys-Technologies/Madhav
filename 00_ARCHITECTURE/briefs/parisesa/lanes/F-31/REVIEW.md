---
lane: F-31
stream: S3_SATYA
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: INCOMPLETE-RETURN
ratified_by: ratifier-1
ratified_by: ratifier-2
---

## Method

Read PROTOCOL.md, DIAGNOSIS.md, SPEC.md, DEDUP_NOTE.md, S2_RESPONSE.md for lane F-31. Read source at `/Users/Dev/par-night/main-ro/platform-mcp/src/tools/registry_bridge.ts` (lines 835–874, 1034–1043, 1502–1506, 2955–2995, 3020–3077, 3100–3119) and `/Users/Dev/par-night/main-ro/platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts` (DOMAIN_DIRECT_VARGAS at :184-188, assess_marriage handler at :1294-1359). Read F-14 SPEC.md for cross-lane conflict check.

Exit test traced line-by-line against current source (no runner available in read-only mirror; full trace below).

## Q1 — Mechanism or symptom?

Mechanism. Change A modifies `attachDomainCompleteness` at its null-case root (:837), not a symptom surface. Changes B/D add the missing wiring calls. Change C adds the missing DOMAIN_READING_FAMILIES entries. All four target root causes, not observable symptoms.

## Q2 — Diagnosis sub-claims vs spec elements

| Diagnosis claim | Spec element |
|---|---|
| C1 — assess_health omits reading/domain_completeness/completeness_directive | Changes B + C wire the calls |
| C2 — no judgment_flag discloses the omission | Change A (null-case block) + Change B (call site) |
| C3 — disclosure mechanism lives in career/wealth; health is a wiring gap | Confirmed by source read; Changes B/D close gap symmetrically |
| Second-order — no health_*/marriage_* dossier slice exists | Change A emits domain_accounting_unavailable flag instead of silently no-oping |
| Sibling — assess_marriage has identical omission | Change D + contract test |
| judgment_query on health — not a wiring gap | Correctly excluded with stated reason |
| attachDomainCompleteness null-case is itself a silent instance | Change A fixes it globally |

All sub-claims mapped. No unmapped diagnosis claim found.

## Q3 — Exit test genuinely fails today?

YES — traced:
1. Test calls `attachDomainCompleteness(response, 'health', '482012f1-...')` (verified export at :835).
2. → `assembleDomainCompleteness('health', '482012f1-...')` → `runDossier({domain:'health', ...})` → no `health_482012f1.json` in `dossier_slices/` → returns null.
3. Current :837: `if (!completeness) return` → response untouched, `judgment_flags` undefined.
4. Test asserts `Array.isArray(flags)` → **FAILS** (flags is undefined). Confirmed fail today.
5. After Change A: null-case pushes `domain_accounting_unavailable:...` onto `judgment_flags` → both test assertions pass.

Second test (career regression guard): career_482012f1.json exists → assembleDomainCompleteness returns non-null → Change A block not reached → `judgment_flags` contains only `complete_domain_accounting_attached`/`domain_accounting_incomplete`, not `domain_accounting_unavailable` → passes today and after fix.

No mock routing issue; test imports `attachDomainCompleteness` directly and uses the real dossier_slices/ filesystem state. Sound design.

## Q4 — Sibling sites covered?

Yes. assess_career (:3030/3032) and assess_wealth (:3112/3114) are fully wired — confirmed by source read. assess_health and assess_marriage covered by Changes B/D. judgment_query excluded with stated reason (wiring is correct; source at :3600ff confirmed it calls buildDomainCompletenessPointer generically). All exclusions have stated reasons.

## Q5 — Recurrence guard detects the defect class?

The contract test (§5) reads `registry_bridge.ts` source and asserts regex `attachDomainCompleteness\(response,\s*'${domain}'` for each domain in `['career', 'wealth', 'health', 'marriage']`. Fails today for health and marriage, passes after the fix.

**However, this test has a domain key error (see Named deficiencies #2 below).** The regex checks for `'marriage'` but the canonical domain key for assess_marriage is `'relationship'` per `register_d8_assess_domain.ts:187` (`DOMAIN_DIRECT_VARGAS['relationship']`) and :1359 (`runAssessDomain(args, { domain: 'relationship', ... })`). If F-14 lands with the correct `'relationship'` key and Change D is corrected, the contract test must check `'relationship'` not `'marriage'` — otherwise it would fail perpetually for a correctly-built codebase.

## Q7 — Unverified assumptions / citation accuracy?

**All major citations verified:**
- `attachDomainCompleteness` at :835 → CONFIRMED (line 835 in source)
- `if (!completeness) return` at :837 → CONFIRMED (line 837 in source)
- `DOMAIN_READING_FAMILIES` at :1034-1037 → CONFIRMED (lines 1034-1037, wealth+career keys only)
- Companion maps at :1038-1043 → CONFIRMED
- assess_marriage server.tool at :2959-2960, 'assess_marriage' string at :2961 → CONFIRMED
- assess_career call sites at :3030/:3032 → CONFIRMED
- assess_health handler at :3041 → CONFIRMED
- `const response = ...` at :3071 → CONFIRMED (SPEC's change B insertion point exact)
- assess_wealth call sites at :3112/:3114 → CONFIRMED
- `attachDomainReading` defined at :1569 → CONFIRMED

**One citation error found:** SPEC §2C states `buildDomainReading early-returns empty at :1578`. Actual: `buildDomainReading` is defined at line 1502; its early-return `if (!families) return { reading: [], ... }` is at line **1506**, not 1578. Mechanism is correctly described; only the line number is off.

**rs_class: RS-A in frontmatter vs. 'Rebuild: None' in body** — noted but not blocking; §6 body reasoning (TypeScript wiring only, no ga_*/bo_* asset touched) is sound and consistent with PROTOCOL.md rebuild policy.

## Named deficiencies (INCOMPLETE-RETURN)

**D1 — CRITICAL: F-14 absent from §6 dependency list; F-14 explicitly closes F-31 and says 'do not build separately'**

`lanes/F-14/SPEC.md` frontmatter declares it closes F-31 alongside F-14/F-15/F-124. F-14 §0 states: *"Do not build F-31 separately from this spec — if S3's own SPEC.md for F-31 lands first or differs, the two must be reconciled by the conductor/VERIFIER into one build, not built twice against the same lines of registry_bridge.ts."* F-14 also owns Changes A-equivalent (§2d: null-case disclosure), Changes B-equivalent (§2b: call sites), and Change C-equivalent (§2a: DOMAIN_READING_FAMILIES keys).

F-31 SPEC §6 lists F-13, F-28, F-56, F-111, F-12, F-36, F-37, F-45, F-44 — but NOT F-14. A builder dispatched on F-31 without this context would apply all four changes against the same lines F-14 has already modified, producing a merge conflict or double-application.

Fix: Add F-14 to §6 dependency list. Note: conductor must confirm whether F-31 is subsumed by F-14's build scope or is a separate build that must sequence after F-14 lands. The spec writer may intend the judgment_flags approach (Change A) as the canonical fix and F-14's `domain_completeness_empty_reason` field approach as a complementary mechanism — if so, §6 must say so explicitly and explain that the two builds are additive, not conflicting.

File: `lanes/F-31/SPEC.md:173-186` (§6 Dependencies block)

**D2 — MATERIAL: Wrong domain key 'marriage' for assess_marriage — canonical key is 'relationship'**

`register_d8_assess_domain.ts:184-188` shows `DOMAIN_DIRECT_VARGAS = { ..., relationship: ['D9'], health: ['D6'] }`. Line 1359 of the same file confirms: `runAssessDomain(args, { domain: 'relationship', ... })` — the assess_marriage capability handler internally uses `'relationship'`, not `'marriage'`.

F-14 SPEC §2a and §2b note (explicitly): `'relationship'` is the canonical domain key for assess_marriage (matching `DOMAIN_DIRECT_VARGAS['relationship']`) and use `'relationship'` throughout. F-31's Change D uses `'marriage'` in both the call sites and the proposed DOMAIN_READING_FAMILIES addition. F-31's §5 contract test also checks `'marriage'`. If built as written:
- `DOMAIN_READING_FAMILIES['marriage']` and `DOMAIN_READING_FAMILIES['relationship']` would be two different keys; if F-14 lands with `'relationship'`, the `attachDomainReading(response, 'marriage', ...)` call in Change D would look up the wrong key and silently serve no reading families.
- The contract test regex for `'marriage'` would pass for a broken wiring (the regex matches Change D's string) but fail to validate the correct `'relationship'` key F-14's build installs.
- Future dossier_slices for the marriage domain would be ambiguously named `marriage_*.json` vs `relationship_*.json`.

Fix: Replace `'marriage'` with `'relationship'` in Change D's two call sites and in the DOMAIN_READING_FAMILIES/companion-maps additions. Update §5 contract test domain array from `['career', 'wealth', 'health', 'marriage']` to `['career', 'wealth', 'health', 'relationship']`.

File: `lanes/F-31/SPEC.md:79-88` (Change D) and `:162-168` (§5 contract test domain array)

**D3 — MINOR: buildDomainReading early-return line citation off**

SPEC §2C: `buildDomainReading early-returns empty at :1578` — actual early-return `if (!families) return { ... }` is at line **1506** (`registry_bridge.ts:1506`). Mechanism is correct; just the line number is wrong. Fix: update :1578 → :1506 in §2C rationale text.

File: `lanes/F-31/SPEC.md:77` (line citation in §2C *Why* block)

## Verdict: INCOMPLETE-RETURN

D1 is a hard blocker: F-14 explicitly forbids building F-31 independently, and the spec gives a builder no indication of this constraint. D2 is a material domain-key error that would produce a silently broken wiring (wrong DOMAIN_READING_FAMILIES key for assess_marriage) and a permanently failing recurrence guard. Both are cheap to fix in the spec text. D3 is informational only.
