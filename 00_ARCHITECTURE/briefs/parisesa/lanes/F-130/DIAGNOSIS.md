# F-130 DIAGNOSIS — assess_career / assess_wealth `reading[]` raw truncated JSON blobs

**Lane:** Stage-D DIAGNOSE, stream S4 VĀCA (narration fidelity), PARIŚEṢA campaign
**Tier:** TIER2-HONESTY
**Worktree:** `.claude/worktrees/par-S4-coord` (branch `par/S4-coordination`, cut from `origin/main`)
**Chart tested:** `482012f1-710e-4a25-994a-93821f5871aa` (canonical native chart)

## Live Reproduction

Called both tools live via the `mcp__marsys-jis-direct__*` bridge with
`chart_id=482012f1-710e-4a25-994a-93821f5871aa` (default ayanamsha, no overrides).

**assess_career** — `object.kernel.grounding.reading[]`:

- `family: "timing_windows"`, `status: "served"`, sentence:
  > `"10 activation window(s) in range; nearest: {\"id\":\"8106742\",\"signal_id\":\"1846a106-4424-41bf-8fe9-3e7a2c7df8c0\",\"ayanamsha_id\":\"lahiri_chitrapaksha\",\"signature_class\":\"SUBSYSTEM\",\"activation_start\":\"2027-08-18\",\"activation_end\":\"2028-01-15\",\"activation_peak_date\":\"."`

  Byte-for-byte matches the corpus's verbatim quote — cut off mid-JSON-key with a dangling period. CONFIRMED.

- `family: "contradictions_with_adjudication"`, `status: "served"`, sentence:
  > `"1 contradiction(s) tag this domain. Leading tension: {\"contradiction_id\":\"3fa9292b-46c5-4151-b273-6cd167553b77\",\"signal_a_id\":\"17ef271e-b82b-46a5-bf55-65e090b93141\",\"signal_b_id\":\"36a6e81b-9e8c-478b-a24e-3535f7ee0 — no automated adjudication hint; needs acharya-level resolution."`

  Raw truncated JSON mid-sentence. CONFIRMED.

**assess_wealth** — `object.kernel.grounding.reading[]`:

- `family: "timing_windows"`, `status: "served"`, sentence:
  > `"10 activation window(s) in range; nearest: {\"id\":\"8177250\",\"signal_id\":\"c516edf0-0f2d-410b-b876-5ed04c5fa67a\",\"ayanamsha_id\":\"lahiri_chitrapaksha\",\"signature_class\":\"YOGA\",\"activation_start\":\"2010-08-18\",\"activation_end\":\"2027-08-18\",\"activation_peak_date\":\"2019-."`

  Raw truncated JSON. CONFIRMED.

- `family: "contradictions_with_adjudication"`, `status: "empty_for_this_chart"`, sentence:
  > `"No contradictions tagged to this domain in bodha_contradictions — not_adjudicated: the contradiction corpus does not yet cover this domain, so absence of a tag is a coverage gap, not a confirmed clean reading."`

  **Does NOT currently reproduce for wealth.** For this chart, `bodha_contradictions` has zero rows tagging the wealth domain, so `readContradictionsFamily`'s `items.length === 0` branch fires and the honest-gap sentence is served instead of the truncated-JSON branch. The defective code path (line 1494, see Mechanism below) is unreached at present — not because it was fixed, but because no wealth-domain contradiction currently exists in the data to trigger it. The corpus's "reproduced identically in 2/2 tools tested" is correct for `timing_windows` (2/2) but is only conditionally true for `contradictions_with_adjudication` — **1/2 live-confirmed (career), 1/2 not currently triggered (wealth) though the same broken code serves it.**

## Claim Decomposition

4 named instances, but really **2 shared bugs, each backing a code path present in both tools**:

1. `readTimingWindowsFamily` (single function, shared by both `assess_career` and `assess_wealth` via the common `buildDomainReading`) — bug fires unconditionally whenever any activation window exists. **2/2 live-confirmed.**
2. `readContradictionsFamily` (single function, also shared) — bug fires only when `items.length > 0` AND none of `tension_label` / `label` / `description` are populated on the leading item. **1/2 live-confirmed (career); wealth's current data doesn't reach the branch, but the vulnerable code is identically present and would fire the instant a wealth-domain contradiction is tagged.**

Both are the SAME defect class (raw `JSON.stringify(...).slice(N)` interpolated into a prose sentence) in the SAME file (`registry_bridge.ts`), authored in the same family-reader pattern — one shared mechanism, not four independent bugs, confirming the corpus's mechanism claim. The severity nuance (wealth contradictions is currently silent, not fixed) is the one correction to the corpus's "identically in 2/2" framing.

## Mechanism (file:line, quoted code)

File: `platform-mcp/src/tools/registry_bridge.ts` (both `par/S4-coordination` and `ekv/a-09-sara-kernel` — identical at these lines, see Blast Radius).

**`readTimingWindowsFamily`, line 1461–1472, bug at line 1469:**

```ts
function readTimingWindowsFamily(activatingDasha: Record<string, unknown> | undefined): ReadingFamilyEntry {
  const activations = Array.isArray(activatingDasha?.['activations']) ? activatingDasha!['activations'] as Record<string, unknown>[] : []
  if (activations.length === 0) {
    return { family: 'timing_windows', label: 'Activating dasha timing windows', status: 'empty_for_this_chart', sentences: [String(activatingDasha?.['partial_failure'] ?? 'No activating dasha windows returned for this call\'s date range.')], fact_ids: [] }
  }
  const first = activations[0]!
  return {
    family: 'timing_windows', label: 'Activating dasha timing windows', status: 'served',
    sentences: [`${activations.length} activation window(s) in range; nearest: ${JSON.stringify(first).slice(0, 220)}.`],
    fact_ids: [],
  }
}
```

Line 1469 interpolates `JSON.stringify(first).slice(0, 220)` directly into the sentence instead of rendering `first`'s fields (e.g. `activation_start`, `activation_end`, `activation_peak_date`, `signature_class`) into prose. The `.slice(0, 220)` is what produces the mid-key truncation with the dangling `.` (the closing `` `.` `` in the template literal lands right after the cut).

**`readContradictionsFamily`, line 1474–1497, bug at line 1494:**

```ts
function readContradictionsFamily(contradictions: Record<string, unknown> | undefined): ReadingFamilyEntry {
  const items = Array.isArray(contradictions?.['items']) ? contradictions!['items'] as Record<string, unknown>[] : []
  const totalCount = Number(contradictions?.['total_count'] ?? items.length)
  if (items.length === 0) {
    return {
      family: 'contradictions_with_adjudication', label: 'Domain contradictions + adjudication', status: 'empty_for_this_chart',
      sentences: [totalCount === 0
        ? 'No contradictions tagged to this domain in bodha_contradictions — not_adjudicated: the contradiction corpus does not yet cover this domain, so absence of a tag is a coverage gap, not a confirmed clean reading.'
        : `${totalCount} chart-wide contradiction(s) exist but none tag this domain — not_adjudicated: domain-specific contradiction coverage may be incomplete.`],
      fact_ids: [],
    }
  }
  const first = items[0]!
  const adjudication = first['adjudication'] ?? first['resolution_hint'] ?? first['adjudication_note']
  return {
    family: 'contradictions_with_adjudication', label: 'Domain contradictions + adjudication', status: 'served',
    sentences: [`${totalCount} contradiction(s) tag this domain. Leading tension: ${String(first['tension_label'] ?? first['label'] ?? first['description'] ?? JSON.stringify(first).slice(0, 160))}${adjudication ? ` — adjudication: ${String(adjudication)}` : ' — no automated adjudication hint; needs acharya-level resolution.'}`],
    fact_ids: [],
  }
}
```

Line 1494's `??` fallback chain ends in `JSON.stringify(first).slice(0, 160)` when the contradiction item carries none of `tension_label` / `label` / `description` — which is exactly what the live `contradiction_id`/`signal_a_id`/`signal_b_id`-shaped rows in `bodha_contradictions` look like (no `tension_label`/`label`/`description` field at all), so the fallback fires every time a contradiction is actually present for a domain.

Both functions are wired into the shared `buildDomainReading(domain, chart_id, ayanamsha_id, data, principal)` (line ~1502 onward; call sites at lines 1540 and 1542), which is the single reading-digest assembler both `assess_career` and `assess_wealth` call — confirming §N.7/W7 "shared template mechanism," not independent per-tool bugs.

## Sibling Census

`buildDomainReading` composes the `reading[]` array from `DOMAIN_READING_FAMILIES` (line 1020–1037): 12 families for career, 13 for wealth, backed by 12 distinct reader functions total (some shared across domains, some domain-specific). Full source review (lines 1168–1497) of every reader function, checking specifically for the `JSON.stringify(...)` → template-literal → truncation pattern:

| Family | Reader function | Raw-JSON-in-sentence pattern? | Status |
|---|---|---|---|
| `per_varga_ashtakavarga` | `readAshtakavargaFamily` | No — renders `graha`/`pinda_sarva` fields via `.join()` | Confirmed clean (source review) |
| `divisional_D10` / `divisional_D9` / `divisional_D2` / `divisional_D11` | `readVargaFamily` | No — renders `graha`/`dignity`/`house_display` fields | Confirmed clean (source review) |
| `karakamsha_or_swamsha` | `readKarakamshaFamily` | No — renders `sign`/`atmakaraka_graha` text fields | Confirmed clean (source review) |
| `indu_lagna` | `readInduLagnaFamily` | No — renders `sign`/`sign_lord`/`house_d1`/`nakshatra` fields | Confirmed clean (source review) |
| `argala_house_2` / `argala_house_10` / `argala_house_11` | `readArgalaFamily` | No — renders numeric `net` + a derived label | Confirmed clean (source review) |
| `full_dispositor_closure` | `readDispositorClosureFamily` | No — renders `mechanism_name`/`mechanism_class`/`valence`/member count | Confirmed clean (source review) |
| `all_chart_mechanisms_and_chains` | `readMechanismsFamily` | No — renders `mechanism_name`/`mechanism_class`/`valence` via `.map()` | Confirmed clean (source review) |
| `special_lagnas` | `readSpecialLagnaFamily` | No — renders `sign` text per subject, joined | Confirmed clean (source review) |
| `cross_ayanamsha_agreement` | `readCrossAyanamshaFamily` | No — renders `fact_value_text` consistency counts | Confirmed clean (source review) |
| `timing_windows` | `readTimingWindowsFamily` | **YES — line 1469** | **BROKEN, live-confirmed both tools** |
| `remedies` | `readRemediesFamily` | No — renders `narration.lead` + named prescription fields | Confirmed clean (source review) |
| `contradictions_with_adjudication` | `readContradictionsFamily` | **YES — line 1494 (fallback branch only)** | **BROKEN, live-confirmed career; wealth's current data doesn't trigger the fallback** |

No other family in this composer shares the defect. `diagSuffix` (line 1106) also does a raw `JSON.stringify(p['__fetch_args'])`, but that is a diagnostic-only suffix appended on a genuine fetch failure (`__fetch_error` present), not part of the normal substance sentence, and is bounded/small (fetch args, not a full signal object) — out of scope for this finding but noted for completeness; it was not observed in either live call (no fetch errors occurred).

**Caveat on "confirmed clean":** the 10 clean rows above are verified by reading the full function source, not by live-sampling every family with data that would exercise every code branch (e.g., `readSpecialLagnaFamily`'s empty branch, `readMechanismsFamily`'s error branch, etc. were not separately live-triggered). The live call did exercise the `served` branch of all 12 career families and 13 wealth families for this chart (all had `status: "served"` except `divisional_D9` = `domain_block_not_served`, `contradictions_with_adjudication` on wealth = `empty_for_this_chart`), and none of the served sentences besides the two flagged contain a raw JSON fragment.

## Blast Radius

`ekv/a-09-sara-kernel` (S2's adoption branch) **does touch `platform-mcp/src/tools/registry_bridge.ts`** — confirmed via `git branch -a | grep a-09` (branch exists locally) and `git log --oneline ekv/a-09-sara-kernel -- platform-mcp/src/tools/registry_bridge.ts`, whose tip commit is:

```
ceadae8cb ekv(a-09): F-56/F-111 — sāra composition for assess_* (buildAssessResponse)
```

Diffing that branch's version of the file against this worktree's (`par/S4-coordination`, merge-base `63049a6e`) shows the two versions are byte-identical except for two added lines (both `hardFloor: true` annotations on the response-budget trimmer's `checklist.timing_hooks.current` / `checklist.timing_hooks.mahadasha_windows_by_graha` sections, around line 3595/3625 — a completely different mechanism: F-51 budget-trim floor protection for `get_dashas`-sourced dasha timing hooks, not the `reading[]` family composer).

Specifically confirmed: `readTimingWindowsFamily` and `readContradictionsFamily` are **word-for-word identical** at the same line numbers (1461, 1469, 1474, 1494) in both branches — `ekv/a-09-sara-kernel` has NOT already fixed this bug, but it HAS actively edited this same file this campaign, in the same general "assess_* response composition" area (F-56/F-111 sāra composition work).

**Per PAR-R-7 / plan §2.1: this is a potential lease conflict, not a clean S4 build.** `registry_bridge.ts` is claimed/touched by S2's `ekv/a-09-sara-kernel` branch. I have NOT edited this file. The lead should route: either (a) confirm S2's branch is not concurrently planning to touch `readTimingWindowsFamily`/`readContradictionsFamily` before S4 lands a fix here, or (b) hand this fix to S2's branch/coordination point instead of building it standalone on S4, to avoid a merge collision in a file both streams are active in.

## Verdict

**CONFIRMED-LIVE**, TIER2-HONESTY, mechanism precisely as named in the corpus: one shared reading-digest sentence composer (`registry_bridge.ts`, `buildDomainReading` and its two family-reader functions) interpolates `JSON.stringify(...).slice(N)` into `reading[]` sentences instead of rendering fields as prose, in `timing_windows` (both tools, unconditional) and `contradictions_with_adjudication` (fires only when the leading contradiction item lacks `tension_label`/`label`/`description`, which is the live case for career but not currently triggered for wealth on this chart, since wealth has zero tagged contradictions right now).

Corrections to the corpus's framing:
1. "Reproduced identically in 2/2 tools tested" is precise for `timing_windows` (2/2 live-confirmed) but should be qualified for `contradictions_with_adjudication` (1/2 live-confirmed; 2/2 same vulnerable code, but wealth's current data doesn't reach the broken branch).
2. Sibling census: exactly these 2 of 12 reader functions carry the defect; the other 10 render fields explicitly and are clean by source review.
3. **Lease conflict flagged, not resolved**: `registry_bridge.ts` is actively claimed by `ekv/a-09-sara-kernel` (S2) this campaign — ESCALATE-TO-PRATINIDHI-equivalent routing note for the stream lead before any fix PR touches this file, per PAR-R-7.

No fix was written; this is a DIAGNOSE-lane output only.
