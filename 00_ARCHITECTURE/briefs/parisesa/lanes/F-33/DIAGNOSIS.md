---
lane: F-33
stream: S3_SATYA
stage: D (DIAGNOSE) — COMPLETE
author: S3 builder (sonnet), DIAGNOSIS-INCOMPLETE lane (2x budget)
---

# F-33 — ganita_dasha_periods_get accepts pre-birth as_of_date with no structured disclosure

## 1. Live reproduction (today, 2026-08-16)

`ganita_dasha_periods_get(chart_id=482012f1-710e-4a25-994a-93821f5871aa, as_of_date='1980-01-01',
ayanamsha_id='lahiri_chitrapaksha')` — the native was born 1984-02-05, so this date is ~4 years
pre-birth. Compared against the same call with `as_of_date='2020-01-01'` (a genuinely in-range
date). Raw JSON saved to `raw_repro.json` in this lane dir.

Pre-birth call result (salient fields):
- `is_error: false`
- 3 rows returned (Maha/Antar/Pratyantar), each `"verification_pass_status":"two_pass_verified"`
- `content.narration`: *"You are in Jupiter Mahadasha (ends 1991-08-18, age ~7) -> Saturn Antardasha
  (ends 1980-04-18, age ~-4) -> Jupiter Pratyantardasha (current, ends 1980-04-18, age ~-4)."*
- No `judgment_flags` key present in the response at all (omitted entirely — the handler only emits
  the key when its internal array is non-empty).

Normal-date call result: identical shape (`is_error:false`, 3 `two_pass_verified` rows, a narration
string, no `judgment_flags`) — only the ages in the narration differ (positive: ~43/~36/~35).

**CONFIRMS REPRODUCES exactly as claimed.** The only difference between a sensible query and a
nonsensical pre-birth one is the substring `age ~-4` inside a free-text field. Nothing
machine-checkable (no `is_error`, no `judgment_flags` entry, no dedicated field) differs. Not
ALREADY-FIXED.

## 2. Claim decomposition

- **C1** — `as_of_date` values preceding the chart's own `birth_date` are accepted without any
  validation/rejection.
- **C2** — the tool nonetheless serves fully-formed, `two_pass_verified`-tier dasha rows for such a
  query (not an honest empty result).
- **C3** — the only signal anything is amiss is a negative integer inside a free-text narration
  sentence, not a structured/machine-checkable field.
- Implicit **C4** (the finding's own parenthetical) — this may be *by design* for the math (a
  Vimshottari Mahadasha's computed `start_date` legitimately precedes birth by definition — see §3),
  meaning the fix target is disclosure of a nonsensical *query*, not correction of the *data*.

## 3. Mechanism (file:line, read directly from `origin/main`)

`ganita_dasha_periods_get` is a P1 alias (`platform-mcp/src/tools/register_p1_aliases.ts:1880-1887`,
`regAlias(server, 'ganita_dasha_periods_get', ..., 'marsys://tool/L1/get_dashas', DASHA_FACET_SCHEMA,
principal)`) that delegates to the identical handler as `ganita_dashas_get`/`query_dasha_periods` —
one shared implementation:
`platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts`.

Inside that file's `execute` function:

- `containsDate` (:268) resolves `as_of_date`/`date_contains` from `args` — this is the raw caller
  value, unvalidated.
- `judgment_flags: JudgmentFlagEntry[] = []` declared at :430; the ONLY thing ever pushed onto it in
  the whole function is `system_facet_unrecognized` (:432, fires only when an unknown `system` string
  is passed) — there is no second push site anywhere in the file.
- When `containsDate && systemApplied === 'vimshottari'` (:448), the handler fetches the chart's own
  birth date directly:
  ```ts
  // :451-454
  const birthRows = await query<{ birth_date: string }>(
    `SELECT birth_date::text AS birth_date FROM charts WHERE id = $1`,
    [chartId]
  )
  const birthDate = birthRows.rows[0]?.birth_date ?? null
  ```
- `ageAtDate` (:471-479) computes `years = d.getFullYear() - b.getFullYear()` (with a month/day
  anniversary adjustment) and returns `` `age ~${years}` `` — **`years` is never floored at 0, and
  the function never compares `isoDate` against `birthDate` to short-circuit or flag the case where
  `isoDate < birthDate`.** A negative `years` is formatted and returned exactly like a positive one.
- The narration sentence (:490-495) interpolates `ageAtDate(mdEnd)`/`ageAtDate(adEnd)`/`ageAtDate(pdEnd)`
  directly into prose — this is the sole place a negative age becomes visible, and it is inside
  `content.narration`, a free-text string, not a structured field.
- The final `return` (:560-586) only attaches `judgment_flags` to the payload
  `...(judgment_flags.length > 0 ? { judgment_flags } : {})` (:585) — since nothing pushed to the
  array for this case, the key is entirely absent from the response (confirmed live: my raw JSON has
  no `judgment_flags` key at all in either call, not even an empty array).

**C4 confirmed as accurate, with the precise reason:** the `rows` themselves are not wrong data — a
Vimshottari Mahadasha's stored `start_date` is a real, correctly-computed classical anchor that
routinely precedes birth (the native's own Jupiter Mahadasha here starts 1975-08-18, nine years
before the 1984-02-05 birth — this is standard "balance of dasha at birth" math, not a bug). The
defect is specifically that the CALLER'S `as_of_date` argument (a query parameter, not a stored fact)
is never checked against `birthDate` even though `birthDate` is already fetched, in scope, and used
two lines later for age arithmetic in the very same code block — the check is a same-file, near-
zero-cost addition that was simply never written.

## 4. Sibling census

Grepped for the same shape — a handler that fetches `birth_date FROM charts WHERE id = $1` and does
plain-JS date arithmetic against a caller-supplied date, with no floor/guard:

| File | Uses `birthDate` for | Same defect class? |
|---|---|---|
| `L1_ganita/get_dashas.ts:452` (this finding) | `ageAtDate()` narration for `as_of_date` | **YES — F-33** |
| `L1_ganita/get_graha_yuddha.ts:148` | Ephemeris lookup AT the birth date itself (`ephemeris_daily(date=${birthDate}, ...)`) — birth_date is the fixed anchor being queried, not compared against a caller-supplied date | **NO — excluded.** Different use: birth_date is the point being read, not a bound being checked. No caller-suppliable date is compared against it. |
| `L1_ganita/get_tajik.ts:22-30` (`resolveVarshaYearForDate`) + call site `:180` | Resolves a caller-supplied `varsha_date` into a `varsha_year` integer via the identical arithmetic shape (`d.getUTCFullYear() - b.getUTCFullYear()` + anniversary adjustment) | **YES — genuine sibling, same missing-guard pattern.** A `varsha_date` before `birth_date` would resolve to `varsha_year <= 0`; nothing in `resolveVarshaYearForDate` or its call site checks this. Consequence differs from F-33 (a non-positive `varsha_year` most likely filters `l1_tajik_varsha_year_lords` to zero rows — an honest-empty result — rather than F-33's populated-but-nonsensical result), but the root cause (no birth_date-vs-input comparison, no structured flag) is identical. Worth a Stage S line item, possibly a shared guard helper. |

Also found, NOT a sibling of this defect but directly relevant context for Stage S / blast radius:
`evals/r5-w0a-canary/canary_runner.ts:353-362` and `evals/r5-w4-full-battery/battery_runner.ts:296`
already assert `zero_pre_birth_rows` / `pre_birth_rows_present` for `ganita_dashas_get` — but that
canary checks a *different* scenario (a **default/today** `as_of_date` accidentally surfacing a
pre-birth-dated row due to a since-fixed "P1 as_of_date-ignored" defect, i.e. window-containment
filtering). It is not checking "what happens when the caller explicitly asks for a pre-birth date,"
which is F-33's actual claim. Cite as related prior art, not as evidence this is already covered.

## 5. Blast radius

- **File-lease conflict — flagging plainly per the task brief.** The mechanism lives in
  `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts`, which plan §2 assigns to
  **S5 (MŪLA)**: *"OWNS: ... capability SQL under layers/L0_*, `L1_ganita/**`, `L2_bodha/**` query
  files."* This is squarely outside S3's OWNS list (`L4_phala/**`, `L5_mimamsa/**`, `ph_nimitta/**`,
  `muhurta.py`). The sibling in `get_tajik.ts` (§4) is in the same S5-owned directory. **S3 cannot
  build this fix under its own lease — Stage S should produce the spec and route it to S5 (or the
  conductor re-leases), the same pattern plan §2.1 prescribes for F-31/registry_bridge.ts.**
  `register_p1_aliases.ts` (the alias registration site) is also not in S3's OWNS list; per plan
  §2.1 it sits between S1 and S5's leases for other findings (CL-11 `dualOutput` sweep vs CL-03
  param plumbing) — this lane doesn't need to touch that file at all since the alias just forwards
  to `get_dashas.ts` unchanged, but noting it for completeness.
- CL-00 controls: no control in `platform/scripts/governance/` references dasha/birth_date/pre-birth
  (checked the same four scripts as F-31). The two canary/eval scripts noted in §4 are not CL-00
  controls (they live under `evals/`, not `platform/scripts/governance/`), but a fix here should be
  checked against them so it doesn't accidentally change the `bytes<=1536*1.5` gate shape those
  canaries also assert on the same tool/response.
- Other lanes sharing `get_dashas.ts`: none found named in the plan's per-stream OWNS lists beyond
  S5's general L1_ganita ownership; no other PARIŚEṢA finding in the manifest excerpt available to
  this session cites this exact file.
- This finding's fix (a `pre_birth` structured field / judgment_flags entry, likely computed right
  where `birthDate` and `containsDate` are already both in scope at :448-455) is small and local —
  once re-leased to S5, it should not require touching `registry_bridge.ts`, `response_budget.ts`,
  or any other stream's HOT files.
