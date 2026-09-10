# F-130 SPEC — assess_career / assess_wealth `reading[]` raw-JSON prose sentences

**Lane:** F-130  **Stage:** S (SPEC)  **Tier:** TIER2-HONESTY

---

## 1. Root-cause statement

`readTimingWindowsFamily` (line 1469) and `readContradictionsFamily` (line 1494 fallback) in `platform-mcp/src/tools/registry_bridge.ts` interpolate `JSON.stringify(obj).slice(N)` directly into prose `sentences[]` entries instead of rendering the object's named fields as text, producing mid-key-truncated JSON fragments in every `assess_career` and `assess_wealth` `reading[]` response.

---

## 2. Files to change

### `platform-mcp/src/tools/registry_bridge.ts`

**Fix A — `readTimingWindowsFamily`, line 1469**

Replace:
```ts
sentences: [`${activations.length} activation window(s) in range; nearest: ${JSON.stringify(first).slice(0, 220)}.`],
```
With (render `signature_class`, `activation_start`, `activation_end`, `activation_peak_date` as prose):
```ts
sentences: [`${activations.length} activation window(s) in range; nearest: ${String(first['signature_class'] ?? 'window')} from ${String(first['activation_start'] ?? '?')} to ${String(first['activation_end'] ?? '?')}${first['activation_peak_date'] ? `, peak ${String(first['activation_peak_date'])}` : ''}.`],
```
Why: these four fields are always present on live activation objects (confirmed from the live sentence fragments in DIAGNOSIS); they carry the human-relevant meaning. No JSON fragment possible.

**Fix B — `readContradictionsFamily`, line 1494 `??` fallback**

Replace the final fallback in the `??` chain:
```ts
?? JSON.stringify(first).slice(0, 160)
```
With:
```ts
?? `unresolved tension (id: ${String(first['contradiction_id'] ?? first['id'] ?? 'unknown')})`
```
Why: live contradiction rows carry `contradiction_id` but never `tension_label`/`label`/`description`; the fix renders the stable identifier field rather than a raw JSON dump. Both `readTimingWindowsFamily` and `readContradictionsFamily` must also gain `export` modifier (add `export` keyword before `function`) to enable direct unit-testing without jest module mocking of `fetchReadingSupplements`.

---

## 3. Exit test

**File:** `platform-mcp/src/tools/__tests__/f130_json_prose_fix.test.ts`

**Command:** `npx jest --testPathPattern=f130_json_prose_fix --no-coverage` (run from `platform-mcp/`)

**FAIL on today's code:** The sentences produced by `readTimingWindowsFamily` and `readContradictionsFamily` contain `{` (opening JSON brace), so `expect(sentence).not.toMatch(/{/)` throws.

**PASS after fix:** Sentences contain only prose-rendered field values; no `{` present.

**Test bodies (builder writes these exactly):**

```ts
import { readTimingWindowsFamily, readContradictionsFamily } from '../registry_bridge'

const MOCK_ACTIVATION = {
  id: '8106742',
  signal_id: 'abc',
  ayanamsha_id: 'lahiri_chitrapaksha',
  signature_class: 'SUBSYSTEM',
  activation_start: '2027-08-18',
  activation_end: '2028-01-15',
  activation_peak_date: '2027-10-01',
}

const MOCK_CONTRADICTION = {
  contradiction_id: '3fa9292b',
  signal_a_id: 'aaa',
  signal_b_id: 'bbb',
  // NOTE: no tension_label / label / description — matches live data shape
}

describe('F-130 — no raw JSON in reading[] sentences', () => {
  it('readTimingWindowsFamily: sentence is prose, not JSON', () => {
    const result = readTimingWindowsFamily({ activations: [MOCK_ACTIVATION] })
    expect(result.status).toBe('served')
    const sentence = result.sentences[0]!
    expect(sentence).not.toMatch(/{/)   // FAILS on current code (JSON.stringify)
    expect(sentence).toContain('SUBSYSTEM')
    expect(sentence).toContain('2027-08-18')
  })

  it('readContradictionsFamily: fallback sentence is prose, not JSON', () => {
    const result = readContradictionsFamily({
      total_count: 1,
      items: [MOCK_CONTRADICTION],
    })
    expect(result.status).toBe('served')
    const sentence = result.sentences[0]!
    expect(sentence).not.toMatch(/{/)   // FAILS on current code (JSON.stringify fallback)
    expect(sentence).toContain('3fa9292b')
  })
})
```

---

## 4. Sibling sites covered

The DIAGNOSIS performed a full source review of all 12 reader functions wired into `buildDomainReading` (lines 1168–1497). Coverage:

| Reader function | Line(s) | Fix in this lane? | Reason |
|---|---|---|---|
| `readTimingWindowsFamily` | 1469 | **YES — Fix A** | Raw `JSON.stringify(first).slice(0, 220)` confirmed |
| `readContradictionsFamily` | 1494 | **YES — Fix B** | Raw `JSON.stringify(first).slice(0, 160)` fallback confirmed |
| `readAshtakavargaFamily` | — | No | Renders `graha`/`pinda_sarva` via `.join()`, confirmed clean by source review |
| `readVargaFamily` | — | No | Renders `graha`/`dignity`/`house_display` text fields, confirmed clean |
| `readKarakamshaFamily` | — | No | Renders `sign`/`atmakaraka_graha` text fields, confirmed clean |
| `readInduLagnaFamily` | — | No | Renders `sign`/`sign_lord`/`house_d1`/`nakshatra` fields, confirmed clean |
| `readArgalaFamily` | — | No | Renders numeric `net` + derived label, confirmed clean |
| `readDispositorClosureFamily` | — | No | Renders `mechanism_name`/`mechanism_class`/`valence`/count, confirmed clean |
| `readMechanismsFamily` | — | No | Renders `mechanism_name`/`mechanism_class`/`valence` via `.map()`, confirmed clean |
| `readSpecialLagnaFamily` | — | No | Renders `sign` text per subject, confirmed clean |
| `readCrossAyanamshaFamily` | — | No | Renders `fact_value_text` consistency counts, confirmed clean |
| `readRemediesFamily` | — | No | Renders `narration.lead` + named prescription fields, confirmed clean |
| `diagSuffix` (line 1106) | — | **Excluded** | Diagnostic-only suffix on `__fetch_error` path; not part of normal substance; bounded/small fetch args; not observed in live calls; out of scope per DIAGNOSIS |

Both `assess_career` and `assess_wealth` are covered: they share `buildDomainReading` → `readTimingWindowsFamily` / `readContradictionsFamily`. No additional per-tool changes needed.

---

## 5. Recurrence guard

Add a grep-based lint check in `platform-mcp/package.json` scripts (or CI) that fails if `JSON.stringify` appears in a template literal inside any `readXxxFamily` function:

```
# In CI / pre-commit:
if grep -nE 'JSON\.stringify\([^)]+\)\.slice' platform-mcp/src/tools/registry_bridge.ts; then
  echo 'FAIL: raw JSON.stringify().slice in registry_bridge.ts — use field-by-field prose rendering'; exit 1
fi
```

Alternatively, add a `// @no-json-stringify-in-sentences` eslint comment block around lines 1461–1497 with a custom eslint rule (if the project has custom rules). The grep check is sufficient as a minimum recurrence guard.

---

## 6. Dependencies and rollback

**Lease conflict (ESCALATE before build):** `registry_bridge.ts` is actively modified by `ekv/a-09-sara-kernel` (S2 branch, tip commit `ceadae8cb` — F-56/F-111 sāra composition). The S2 changes are at lines 3595/3625 (response-budget trimmer), word-for-word identical at lines 1461–1497 per the DIAGNOSIS diff. No functional conflict at those specific lines, but the builder MUST rebase/merge against `ekv/a-09-sara-kernel` before submitting to avoid a conflict in a file both streams are touching. Route to stream lead / conductor for go-ahead per PAR-R-7 before any PR is opened.

**Other lanes:** F-14/F-15 also touch `registry_bridge.ts` (assess_* reading/completeness). Confirm those lanes' changes are not at lines 1461–1497.

**No migration required.** The fix is pure TypeScript rendering logic; no DB schema changes, no data changes.

**Rollback:** Revert the two sentence-template lines to their prior `JSON.stringify(...).slice(...)` forms. No state to undo.

---

## 7. Coverage table (DIAGNOSIS sub-claims → SPEC)

| DIAGNOSIS claim | SPEC coverage |
|---|---|
| `readTimingWindowsFamily` line 1469: `JSON.stringify(first).slice(0, 220)` in template | §2 Fix A + §3 exit test assertion 1 |
| `readContradictionsFamily` line 1494: `??  JSON.stringify(first).slice(0, 160)` fallback | §2 Fix B + §3 exit test assertion 2 |
| `timing_windows` 2/2 live-confirmed (career + wealth) | §2 Fix A covers both via shared `buildDomainReading` |
| `contradictions_with_adjudication` 1/2 live-confirmed (career); wealth same code | §2 Fix B covers both tools; wealth protected when data triggers path |
| 10 other family readers confirmed clean by source review | §4 table, excluded with reason |
| `diagSuffix` `JSON.stringify` noted but out of scope | §4 excluded with reason |
| `buildDomainReading` is the single shared wiring point (lines 1540, 1542) | §1 root cause + §4 coverage |
| `ekv/a-09-sara-kernel` lease conflict at `registry_bridge.ts` | §6 dependencies (ESCALATE) |
| 4 named instances = 2 shared defects | §1 one root-cause sentence, §2 two fixes |
| DIAGNOSIS correction: wealth contradictions not currently triggered | §4 note: fix protects both tools; wealth coverage is latent until data triggers branch |
