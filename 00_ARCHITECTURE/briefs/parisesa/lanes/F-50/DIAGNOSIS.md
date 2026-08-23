---
finding: F-50
tier: TIER3-EXPERIENCE
stream: S4 VĀCA (narration fidelity, register)
stage: D (DIAGNOSE) — DIAGNOSIS-INCOMPLETE lane, double budget
status: OPEN-mechanism-found
---

# F-50 — Diagnosis

## Live Reproduction

Chart: `482012f1-710e-4a25-994a-93821f5871aa` (Abhisek Mohanty, canonical).

1. `bodha_remedies_get(chart_id, graha='Saturn')` →
   `narration.lead`:
   > "Your Bodha remedy layer flags Saturn as your #1 remedy-priority target —
   > resonance_score 0.094032, priority class low."
   `resonance_ranked` contains exactly one entry: `{rank:1, graha:"Saturn",
   resonance_score:0.094032, weakest_rank_in_chart:8, remedy_priority_class:"low"}`.
   Raw capture: `repro_filtered.json`.

2. `bodha_remedies_get(chart_id)` (no `graha` filter) →
   `narration.lead`:
   > "Your Bodha remedy layer flags Venus as your #1 remedy-priority target —
   > resonance_score 0.173, priority class critical — followed by Ketu, Rahu, Moon."
   Full `resonance_ranked` (9 rows) places **Saturn at rank 8 of 9**
   (`resonance_score: 0.094032`, `remedy_priority_class: "low"`, `weakest_rank_in_chart: 8`)
   — identical numeric fields to what the filtered call reported. Raw capture:
   `repro_unfiltered.json`.

3. `ganita_condition_get(chart_id, facet='dignity')` → `D1_SAT` row: `dignity_state:
   "exalted"`, sign Libra, house 7 (`fact_id 355fe607160e1d76`). Confirms the claim's
   premise: Saturn is structurally one of the chart's stronger planets (D1 exaltation),
   consistent with its rock-bottom (8th-of-9, "low priority") remedy-resonance rank.
   Raw capture: `repro_dignity.json`.

**Reproduces exactly as described.** The finding is live, not stale.

## Claim Decomposition

(a) **Filtered call labels the requested graha "#1 remedy-priority target" regardless of
its actual rank.** TRUE — confirmed above. The wording is generic superlative
("#1... target") with no qualification that the ranking universe was reduced to size 1
by the `graha` filter.

(b) **Underlying numeric fields ARE honestly reported alongside** (`resonance_score`,
`remedy_priority_class: "low"`, `weakest_rank_in_chart: 8`). TRUE — confirmed: the
filtered response's single resonance row carries the exact same `weakest_rank_in_chart:
8` and `remedy_priority_class: "low"` as the unfiltered call's rank-8 row. A caller who
reads past the lead sentence into `resonance_ranked[0]` or `resonances[0]` sees the
honest rank-8/low-priority data right next to the misleading headline. This **narrows
remediation scope**: this is a narration/wording defect in one sentence, not a data
integrity or ranking-computation defect — no numeric field needs to change, only the
lead-sentence template's conditional logic.

(c) **Unfiltered call correctly ranks Saturn ~8/9.** TRUE — confirmed exactly (rank 8 of
9, by `resonance_score` descending... actually ascending score order — see mechanism
note below on directionality — either way, Saturn sits at the low/weak end, tied with
its D1 exalted dignity being irrelevant to bo_upaya's *weakness*-composite scoring,
which is a separate, legitimate design choice `bo_upaya.py` documents explicitly, see
Sibling Census).

## Mechanism (file:line)

`platform/src/lib/retrieval/registry/layers/L2_bodha/query_remedies.ts`, lines 447–460
(the "U-a verdict-first lead" block):

```ts
// ── U-a verdict-first lead ──────────────────────────────────────────────
const topRow = orderedResRows[0]
const secondaryGrahas = orderedResRows.slice(1, 4).map((r) => String(r['graha']))
const leadSentence = topRow
  ? (leverageActive
      ? `Your highest-leverage remedy target is ${String(topRow['graha'])}` +
        ` — leverage_index ${Number(levFor(topRow)?.leverage_index ?? 0).toFixed(3)}` +
        ` (domain '${String(levFor(topRow)?.leverage_domain ?? leverageInfo?.resolvedDomain ?? 'general')}'),` +
        ` resonance_score ${Number(topRow['resonance_score']).toFixed(3)}, priority class ${String(topRow['remedy_priority_class'])}` +
        (secondaryGrahas.length ? ` — followed by ${secondaryGrahas.join(', ')}.` : '.')
      : `Your Bodha remedy layer flags ${String(topRow['graha'])} as your #1 remedy-priority target` +
        ` — resonance_score ${Number(topRow['resonance_score']).toFixed(3)}, priority class ${String(topRow['remedy_priority_class'])}` +
        (secondaryGrahas.length ? ` — followed by ${secondaryGrahas.join(', ')}.` : '.'))
  : `No resonance rows found for chart ${chart_id}${graha ? ` (graha filter: ${graha})` : ''}.`
```

**Why it says "#1":** `orderedResRows` is built from `resRows`, which is the direct
result of `resonanceSql` — and the `graha` param is applied as a *SQL* filter at query
build time, not a post-hoc narrowing of an already-ranked list:

```ts
// line 337-346
const resConds = ['chart_id = $1', 'ayanamsha_id = $2']
const resParams: unknown[] = [chart_id, ayanamsha_id]
...
if (graha) { resConds.push(`LOWER(graha) = LOWER($${rp++})`); resParams.push(graha) }
```

So when `graha='Saturn'` is passed, `resRows` (and therefore `orderedResRows`) contains
**exactly one row** — Saturn's. `topRow = orderedResRows[0]` is then, trivially and
correctly, "rank 1" *of the one-row array the SQL filter produced* — but the template at
line 457 has no branch, flag, or qualifying clause for "this ranking universe was
filtered down to N=1 by the caller's own `graha` param." It emits the identical
"#1 remedy-priority target" wording it would emit for a genuine chart-wide #1
(as demonstrated by the unfiltered call correctly naming Venus, the real #1, with the
same template). The `secondaryGrahas` list (line 449) is the only per-call signal that
distinguishes a real ranking from a filtered singleton — when it's empty, that's because
`orderedResRows.slice(1,4)` had nothing to slice, but the template swallows this into a
trailing period rather than treating it as "denominator undisclosed, must not use rank
language."

Everything needed to render the sentence honestly is already present in the row
(`weakest_rank_in_chart: 8`, computed by `bo_upaya.py` — see its own explicit warning at
`platform/python-sidecar/pipeline/orchestrator/writers/bo_upaya.py:248` and `:1230`:
`"composite remedy-priority rank; do not read it as the shadbala-weakest graha"`) — the
serving layer simply never reads `weakest_rank_in_chart` into the lead sentence; it only
surfaces it inside the `resonance_ranked` / `resonances` row arrays, several fields below
the headline.

**Same defect present in the `leverageActive` branch** (line 452, "Your highest-leverage
remedy target is..."): it is driven by the identical `topRow = orderedResRows[0]`, so a
`graha`-filtered + `leverage_ranked=true` call would produce the same trivial-singleton
"highest-leverage" claim. Not separately reproduced here (out of the finding's literal
repro_cmd scope) but it is the same code path and would need the same fix.

## Sibling Census

Searched `platform/src/lib/retrieval/registry/layers/**` (all L0–L5 query/register
composers) for the same defect class — a lead/narration sentence built from `rows[0]`
of a set that a caller-supplied filter can reduce to size 1, then labeled with an
undisclosed-denominator superlative ("#1", "top", "strongest", "highest", "is your").

- Literal string `"as your #1"` / `"your #1"`: **only one hit**, `query_remedies.ts:457`
  itself.
- `leadSentence` / narration-lead constant construction exists in exactly two files
  repo-wide: `query_remedies.ts` (this finding) and
  `platform/src/lib/retrieval/registry/layers/L1_ganita/get_dashas.ts:492`. The latter's
  lead sentence ("You are in X Mahadasha -> Y Antardasha -> Z Pratyantardasha") is a
  factual current-state statement, not a ranked/filtered superlative claim — it is not
  susceptible to this defect class (no filter reduces a ranked list to a trivial
  singleton there; the dasha hierarchy is deterministic per instant, not filtered by a
  caller param).
- Broader "strongest/weakest/highest + narration lead" grep across all layers returned
  no other narration-lead constructions using superlative wording at all.

**Verdict: no sibling instance found.** This defect class (SQL-level `graha`/similar
filter collapsing a ranked set to N=1, then a superlative headline template blind to
that collapse) appears isolated to `query_remedies.ts`'s two lead-sentence branches
(non-leverage line 457, leverage line 452) — one finding, one file, two branches of the
same `topRow` construct.

## Blast Radius

- **Same file, same tool, different code path — F-116** (`brahma_remedy_corpus join by
  graha only`, per `LEDGER_S4.md`): F-116's mechanism lives in the **write path**
  (`platform/python-sidecar/pipeline/orchestrator/writers/bo_upaya.py`, joining
  `brahma_remedy_corpus`/`l0_remedy_corpus` rows into `remedy_label_human` by graha
  only) — a different layer (L2 Bodha writer, Python) touching a different field
  (`remedy_label_human` prescription text) than F-50's defect (L2 Bodha **serving**
  layer, TypeScript, the `narration.lead` headline sentence). Both bugs are reachable
  through the same `bodha_remedies_get` MCP tool call, but they do not share a
  file, a function, or a fix. A fix for F-50 (narration-lead template) will not touch or
  need coordination with a fix for F-116 (corpus-join logic), and vice versa. Confirmed
  by reading both mechanism pointers directly — no shared symbol, no shared file.
- **Within `query_remedies.ts`:** the `leverageActive` lead-sentence branch (line
  452–456) shares the identical `topRow = orderedResRows[0]` construct and needs the
  same fix applied in the same edit (see Mechanism above) — this is in-scope for one PR,
  not a separate finding.
- **Downstream consumers:** `resonance_ranked` and `resonances` arrays (which carry the
  honest `weakest_rank_in_chart` field) are unaffected — only the `narration.lead`
  string needs correction. No other tool re-derives or re-narrates
  `bodha_remedies_get`'s lead sentence (confirmed: no other file references
  `query_remedies`'s `leadSentence`/`narration.lead` output for further composition).

## Verdict

**OPEN-mechanism-found.**

Root cause: `platform/src/lib/retrieval/registry/layers/L2_bodha/query_remedies.ts`,
lines 447–460. The lead-sentence template unconditionally applies superlative framing
("#1 remedy-priority target" / "highest-leverage remedy target") to
`orderedResRows[0]` without checking whether the `graha` (or `domain`) filter reduced
the ranking universe to a single row. When it did, the sentence is trivially true
("#1 of 1") but misleading in isolation, exactly as the finding describes — while the
row's own `weakest_rank_in_chart` field (already computed and already present in the
payload, just not read into the lead sentence) honestly shows Saturn at rank 8 of 9.
Suggested fix direction (not applied — Stage D is diagnosis-only): branch the lead
sentence on `graha` (and/or `resonance_count === 1` coupled with an active filter) to
either (a) cite `weakest_rank_in_chart`/`remedy_priority_class` explicitly instead of
"#1" language, e.g. "Saturn's remedy priority is low (rank 8 of 9 chart-wide)", or (b)
append an explicit denominator clause, e.g. "— this is Saturn's own resonance data;
run the unfiltered call to see how it ranks against the other 8 grahas."
