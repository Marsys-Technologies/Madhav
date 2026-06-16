---
canonical_id: PHASE_5_FOLLOWUP_YOGINI_CHARA_BRIEF
version: 1.0
status: AUTHORED_READY_TO_EXECUTE
campaign: PHASE_5_DASHA_CORRECTNESS (post-close follow-up)
authored_on: 2026-05-19
estimated_sessions: 1
two_stream_branch: analysis/backend-data-pipeline-perf-audit
depends_on: §5A (67b36de), §5B (8649aae), §5C (PR #96 merged 2026-05-19T17:51:59Z)
campaign_role: POST-CLOSE EXTENSION — extends checkpoint_dasha to cover Yogini + Chara systems per locked decision §6.4 carry-forward
---

# Phase 5 Follow-up — Yogini + Chara Validator Extension

## §1 Scope

The Phase 5 campaign closed with `checkpoint_dasha.ts` validating **Vimshottari claims only** (per locked decision §6.4). The §5C brief explicitly noted:

> "Yogini / Chara validator coverage — Vimshottari-only initially per locked decision §6.4. The regex framework is generic; the cross-check table is filterable by `system`; multi-system extension is mechanical and queued as follow-up."

This brief is that mechanical extension. Three of the four campaign artifacts already cover all three systems from day one — `query_dasha_periods` accepts `system: vimshottari|yogini|chara`, the `DASHA_DISCIPLINE_GATE` mentions `DSH.V.NNN / DSH.Y.NNN / DSH.C.NNN`, and `chart_facts` has all three categories populated. Only the validator's regex + cross-check is single-system. After this extension, the validator catches wrong claims across all three systems uniformly.

What ships:

1. **Extended `checkpoint_dasha.ts`** — system detection heuristic + 3 regex passes (Vimshottari = existing, Yogini = new, Chara = new) + cross-check that filters `chart_facts` by category based on detected system.
2. **Constants for Yogini + Chara** — 8 Yogini lord names + their graha rulers (so claims like "Bhramari yogini" OR "Mars yogini" both extract); 12 Jaimini Chara signs.
3. **Unit-test extensions** — ~10 new tests in `checkpoint_dasha.test.ts` covering Yogini extraction, Chara extraction, system detection edges, mixed-system claims, citation cross-check against the right category.
4. **Optional fixture extensions** — 2 fixtures in `fixtures.json` exercising Yogini and Chara claims if the suite doesn't already have them.

What does NOT ship:

- New retrieval tools (already shipped — query_dasha_periods covers all three systems).
- New planner rules (R-DA already fires for Yogini and Chara terminology).
- New synthesis prompt gates (DASHA_DISCIPLINE_GATE already covers all three).
- Migration changes (chart_facts categories already exist).
- PHASE_5_CLOSE_v1_0.md amendments (campaign is sealed; this is a follow-up commit on top).

## §2 What you must NOT do

- **No branch other than `analysis/backend-data-pipeline-perf-audit`** (or a fresh feature branch off main if the operator prefers to ship this as a discrete PR — see §6 for both options).
- **No Chat V2 files**.
- **No autonomous `npm run answer:eval`** — eval discipline holds; this is a small code-only extension.
- **No new retrieval tools or planner rules** — those are already in place.
- **No campaign re-opening** — Phase 5 is sealed. This is a follow-up commit, not §5D.

## §3 Data shape (confirmed from chart_facts inspection)

### §3.1 Yogini (17 rows · DSH.Y.001 through DSH.Y.017 · 1984-02-05 → 2057-12-22)

`value_json` per row:

```json
{
  "yogini": "Bhramari",
  "ruler": "Mars",
  "duration_label": "5 years",
  "start_date": "1985-12-22",
  "end_date": "1990-12-22"
}
```

8 distinct Yogini lords with classical graha rulers:

| Yogini | Graha ruler |
|---|---|
| Mangala | Moon |
| Pingala | Sun |
| Dhanya | Jupiter |
| Bhramari | Mars |
| Bhadrika | Mercury |
| Ulka | Saturn |
| Siddha | Venus |
| Sankata | Rahu |

(Note: this dataset stores **MD-level only** — no antar-yogini rows. Validator extension treats Yogini as single-level for now.)

### §3.2 Chara (144 rows · DSH.C.001 through DSH.C.144 · 1984-02-05 → 2059-02-05)

`value_json` per row:

```json
{
  "md_sign": "Aries",
  "ad_sign": "Taurus",
  "start_date": "1984-02-05",
  "end_date": "1984-08-05"
}
```

12 standard Jaimini Chara sign-MDs (one row per MD/AD pair across the full chart life span). Each row has `md_sign` + `ad_sign` from the 12 zodiac signs.

## §4 Implementation

### §4.1 Extend `platform/src/lib/checkpoints/checkpoint_dasha.ts`

Add constants near the existing Vimshottari lord list:

```ts
// §4.1 Vimshottari (existing — kept)
const VIMSHOTTARI_LORDS = [
  'Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter',
  'Venus', 'Saturn', 'Rahu', 'Ketu',
] as const

// §4.1 Yogini (new — 8 lords + classical graha rulers)
const YOGINI_LORDS = [
  'Mangala', 'Pingala', 'Dhanya', 'Bhramari',
  'Bhadrika', 'Ulka', 'Siddha', 'Sankata',
] as const
const YOGINI_RULERS = [
  'Moon', 'Sun', 'Jupiter', 'Mars',
  'Mercury', 'Saturn', 'Venus', 'Rahu',
] as const  // index-aligned with YOGINI_LORDS

// §4.1 Chara (new — 12 standard zodiac signs)
const CHARA_SIGNS = [
  'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
  'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces',
] as const
```

### §4.2 System detection heuristic

```ts
type DashaSystem = 'vimshottari' | 'yogini' | 'chara'

function detectSystem(span: string, lord: string): DashaSystem {
  const lower = span.toLowerCase()

  // Explicit system mention wins
  if (/\byogini\b/i.test(span)) return 'yogini'
  if (/\bchara\b|\bjaimini\b/i.test(span)) return 'chara'

  // Lord name lookup — Yogini-specific names disambiguate
  const yoginiLordMatch = YOGINI_LORDS.find(l => l.toLowerCase() === lord.toLowerCase())
  if (yoginiLordMatch) return 'yogini'

  // Chara MD signs override generic graha pattern when "MD" follows a sign
  const charaSignMatch = CHARA_SIGNS.find(s => s.toLowerCase() === lord.toLowerCase())
  if (charaSignMatch) return 'chara'

  // Default — Vimshottari
  return 'vimshottari'
}
```

Note: when synthesis says "Bhramari Yogini (Mars)" the regex catches "Bhramari" via the Yogini-lord branch AND "Mars" via the Vimshottari branch. The system-detection heuristic above prioritizes the Yogini match because "Yogini" is in the span. If the span is just "Mars yogini dasha" (no explicit Yogini name), the explicit `\byogini\b` keyword wins → system='yogini', and the cross-check confirms against `dasha_yogini` rows where `ruler='Mars'`.

### §4.3 Extended regex extractor

Two changes to the existing `extractDashaClaims`:

1. **Add Yogini regex** alongside the existing Vimshottari regex:

```ts
// Yogini regex — matches "Bhramari Yogini", "Mars Yogini dasha", "Yogini Mangala", etc.
const YOGINI_CLAIM_RE = new RegExp(
  String.raw`\b(current|next|upcoming|previous|past|future|present)?\s*` +
  String.raw`(?:'s|s')?\s*` +
  String.raw`(?:yogini|yog\.)\s+(?:lord|of|dasha|is|was|will be)?\s*` +
  String.raw`(${YOGINI_LORDS.join('|')}|${YOGINI_RULERS.join('|')})` +
  String.raw`|\b(${YOGINI_LORDS.join('|')})(?:'s|s')?\s+yogini`,
  'gi',
)
```

2. **Add Chara regex** for sign-based claims:

```ts
const CHARA_CLAIM_RE = new RegExp(
  String.raw`\b(current|next|upcoming|previous)?\s*` +
  String.raw`(?:chara|jaimini|sign-period|sign period)\s+` +
  String.raw`(?:dasha\s+of\s+)?(${CHARA_SIGNS.join('|')})` +
  String.raw`|\b(${CHARA_SIGNS.join('|')})\s+(?:sign-)?(?:dasha|chara|MD)`,
  'gi',
)
```

The extractor runs all three regex passes and dedupes overlapping spans (Yogini "Mars" should not also match Vimshottari "Mars MD" when the Yogini regex captured it first; deduplication by `[start, end]` overlap suffices).

### §4.4 Cross-check extension

Update `validateClaimsAgainstChartFacts` to switch category based on detected system:

```ts
const CATEGORY_BY_SYSTEM: Record<DashaSystem, string> = {
  vimshottari: 'dasha_vimshottari',
  yogini: 'dasha_yogini',
  chara: 'dasha_chara',
}

const FACT_ID_PREFIX: Record<DashaSystem, string> = {
  vimshottari: 'DSH.V.',
  yogini: 'DSH.Y.',
  chara: 'DSH.C.',
}

async function validateClaimsAgainstChartFacts(
  claims: DashaClaim[],
  storageClient: StorageClient,
): Promise<ValidationResult[]> {
  const results: ValidationResult[] = []

  for (const claim of claims) {
    const category = CATEGORY_BY_SYSTEM[claim.system]
    const expectedPrefix = FACT_ID_PREFIX[claim.system]

    // ... existing citation-presence check ...

    if (claim.has_citation) {
      // Verify citation prefix matches detected system
      if (!claim.cited_fact_id?.startsWith(expectedPrefix)) {
        results.push({
          claim,
          verdict: 'violation',
          reason: `${claim.system} claim cited ${claim.cited_fact_id} (wrong prefix; expected ${expectedPrefix})`,
        })
        continue
      }

      // Existing chart_facts cross-check, but category-aware:
      const row = await storageClient.query(
        `SELECT value_json FROM chart_facts WHERE category = $1 AND fact_id = $2 AND is_stale = false`,
        [category, claim.cited_fact_id],
      )
      // ... compare row.value_json.md_lord (or ruler, or md_sign) against claim.lord ...
    }
  }

  return results
}
```

Field name to compare against `claim.lord` varies by system:

| System | chart_facts field |
|---|---|
| vimshottari | `md_lord` (or `ad_lord` if claim.level=AD) |
| yogini | `yogini` OR `ruler` (both accept; synthesis may cite either name) |
| chara | `md_sign` (or `ad_sign` if claim.level=AD; case-insensitive sign name match) |

### §4.5 Remediation prompt update

The §5C remediation prompt template at `platform/src/lib/prompts/checkpoints/checkpoint_dasha.md` already mentions all three systems in the gate text (DSH.V.NNN / DSH.Y.NNN / DSH.C.NNN) — no update needed. But the canonical_dasha_snippet builder in `single_model_strategy.ts` should also pull yogini + chara rows when the violation involves those systems:

```ts
async function buildRemediationSnippet(
  violations: ValidationResult[],
): Promise<string> {
  // Group violations by system
  const systemsViolated = new Set(violations.map(v => v.claim.system))

  // For each violated system, fetch the canonical schedule via query_dasha_periods
  let snippet = ''
  for (const system of systemsViolated) {
    const tool = getTool('query_dasha_periods')
    const result = await tool.retrieve(plan, { system, next_count: 3 })
    snippet += `\n\n${system.toUpperCase()} canonical schedule:\n${formatToolResult(result)}`
  }
  return snippet
}
```

(The original §5C builder only pulled Vimshottari. Extending to pull whichever system(s) were violated is mechanical.)

### §4.6 Heuristic gate update

The §5C `detectDashaRelevance` regex covers Vimshottari terminology + tool-name detection. Extend to also catch Yogini + Chara:

```ts
const DASHA_RELEVANCE_RE = /\b(
  mahadasha|antardasha|pratyantardasha|sookshma|prana|
  vimshottari|MD|AD|PD|
  yogini|yog\.|
  chara|jaimini|sign[- ]period
)\b/i
```

If the query mentions "Yogini" or "Chara" terminology even without a Vimshottari keyword, the validator now runs.

## §5 Test coverage (~10 new tests)

Append to `platform/src/lib/checkpoints/__tests__/checkpoint_dasha.test.ts`:

1. `extractDashaClaims captures "Bhramari yogini" as yogini-system claim`
2. `extractDashaClaims captures "Mars yogini dasha" as yogini-system (ruler-based)`
3. `extractDashaClaims captures "Aries chara MD" as chara-system claim`
4. `extractDashaClaims captures "Pisces sign-period" as chara-system`
5. `detectSystem returns "yogini" when span contains "Yogini"`
6. `detectSystem returns "chara" when span contains "Jaimini" or "Chara"`
7. `detectSystem defaults to "vimshottari" for "Saturn MD"`
8. `validateClaimsAgainstChartFacts checks dasha_yogini category for yogini claims`
9. `validateClaimsAgainstChartFacts checks dasha_chara category for chara claims`
10. `validateClaimsAgainstChartFacts flags wrong-prefix citation (yogini claim cited DSH.V.NNN) as violation`
11. `validateClaimsAgainstChartFacts accepts Yogini citation referencing either yogini name or ruler graha`
12. `validateClaimsAgainstChartFacts accepts case-insensitive Chara sign match`

## §6 Verification gates (pre-commit)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-dasha-5a  # or whichever worktree is convenient

# G1: TypeScript compiles
npx tsc --noEmit

# G2: Extended checkpoint tests pass + regression
npx vitest run src/lib/checkpoints/__tests__/checkpoint_dasha.test.ts
npx vitest run src/lib/checkpoints/__tests__/

# G3: Synthesis regression (the retry-loop integration shouldn't regress)
npx vitest run src/lib/synthesis/__tests__/single_model_strategy.test.ts

# G4: Full src/lib/ regression
npx vitest run src/lib/

# G5: planner_regression_gate (validator extension should not affect planner output)
npx vitest run tests/eval/planner_regression_gate.test.ts
```

## §7 Commit + push options

The Phase 5 campaign is sealed (PR #96 merged); this follow-up can ship via either path:

**Option A — direct PR to main** (recommended; clean isolated change):

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-dasha-5a
git checkout main
git pull origin main
git checkout -b feat/dasha-validator-yogini-chara

# ... apply changes ...

git add platform/src/lib/checkpoints/checkpoint_dasha.ts \
        platform/src/lib/checkpoints/__tests__/checkpoint_dasha.test.ts \
        platform/src/lib/synthesis/single_model_strategy.ts   # if remediation builder extended

git commit -m "feat(checkpoint_dasha): extend validator to Yogini + Chara systems

Phase 5 follow-up — closes the locked-decision §6.4 carry-forward.
checkpoint_dasha.ts now validates Vimshottari (existing) + Yogini (new) +
Chara (new) claims uniformly. Pattern:

  - 8 Yogini lord names (Bhramari, Bhadrika, ...) + their classical graha
    rulers (Mars, Mercury, ...); synthesis can cite either name
  - 12 Jaimini Chara MD signs
  - System detection heuristic: explicit 'yogini'/'chara'/'jaimini'
    keywords win; lord-name lookup for ambiguous spans
  - Cross-check filters chart_facts by category (dasha_vimshottari /
    dasha_yogini / dasha_chara) based on detected system
  - Fact-id prefix check (DSH.V/DSH.Y/DSH.C) catches wrong-prefix
    citations
  - Remediation snippet builder pulls per-violated-system schedules via
    query_dasha_periods (already multi-system from day one)
  - Heuristic gate extended to fire on Yogini/Chara terminology

No new tools, no new planner rules, no new synthesis gates. All four
upstream layers (R-DA, DASHA_DISCIPLINE_GATE, query_dasha_periods,
chart_facts) already covered all three systems from day one — only the
validator's regex + cross-check were single-system.

Test coverage: ~10 new tests in checkpoint_dasha.test.ts; full src/lib/
regression green; planner_regression_gate green.

Data verified: chart_facts has 17 dasha_yogini rows (DSH.Y.001-017,
1984-2057, 8 lords) + 144 dasha_chara rows (DSH.C.001-144, 1984-2059,
12-sign Jaimini structure).

Refs: 00_ARCHITECTURE/briefs/PHASE_5_FOLLOWUP_YOGINI_CHARA_BRIEF_v1_0.md
Closes: §5C locked-decision §6.4 carry-forward"

git push origin feat/dasha-validator-yogini-chara

gh pr create \
  --base main \
  --head feat/dasha-validator-yogini-chara \
  --title "feat(checkpoint_dasha): Yogini + Chara validator extension (Phase 5 follow-up)" \
  --body "<see body in commit message>"

gh pr merge feat/dasha-validator-yogini-chara --merge --auto
```

**Option B — direct commit to analysis branch** (if you prefer to bundle with other queued analysis-stream work later):

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-dasha-5a
git checkout analysis/backend-data-pipeline-perf-audit
git pull origin main  # absorb any post-PR-96 commits
# ... apply changes + same commit message ...
git push origin analysis/backend-data-pipeline-perf-audit
```

Option A is cleaner — small isolated PR, easy to review + auto-merge.

## §8 Acceptance criteria

- [ ] `checkpoint_dasha.ts` extended with `YOGINI_LORDS`, `YOGINI_RULERS`, `CHARA_SIGNS` constants
- [ ] `detectSystem` helper added with explicit-keyword priority + lord-name fallback
- [ ] `extractDashaClaims` runs all three regex passes with dedupe by overlap
- [ ] `validateClaimsAgainstChartFacts` switches category + fact_id prefix per system
- [ ] Yogini citation acceptable as either name (Bhramari) or ruler (Mars)
- [ ] Chara citation matches sign name case-insensitive
- [ ] Wrong-prefix citation (e.g., DSH.V.024 cited for a "yogini" claim) → violation
- [ ] `detectDashaRelevance` heuristic gate triggers on Yogini/Chara terminology
- [ ] Remediation snippet builder pulls per-violated-system canonical rows
- [ ] ~10 new unit tests pass
- [ ] `tsc --noEmit` clean
- [ ] Full `src/lib/` regression green
- [ ] `planner_regression_gate` green
- [ ] Commit lands per Option A or B; PR merged if Option A

## §9 Report back

When complete:

1. Closing commit SHA + `git log --oneline -3`.
2. Test counts (existing + 10+ new).
3. PR URL if Option A.
4. Confirmation that all three systems now validated.
5. Any surprises (e.g., regex false-positives on ambiguous spans).

Phase 5 then formally closes the locked-decision §6.4 carry-forward.
