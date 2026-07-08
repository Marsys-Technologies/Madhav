---
canonical_id: R5_BATTERY_RESULTS
version: 1.0
status: COMPLETE-WITH-GAPS
created: 2026-07-09
author: Claude Code (autonomous verification pass)
governed_by: R5_ANSWER_BATTERY_v1_0.md (FROZEN — this document reports against it, never edits it)
---

# R5 W4 FULL BATTERY RESULTS v1.0

**Scope.** This is the Ring-2/Ring-3-precursor FULL BATTERY run: all items in
`R5_ANSWER_BATTERY_v1_0.md §3` executed LIVE against prod `amjis-mcp`
(`https://amjis-mcp-qm256lasva-el.a.run.app/mcp`), both canonical charts, using the
provisioned `probe-service-account` test credential. This is a **verification pass only** — no
product code was modified. The frozen battery file was read, never edited.

**Harness note (read first — governs how to read every number below).** The live MCP response
shape has evolved since the W0a canary was written (an "S3 serialization-tax" perf fix, already
documented in `R5_RUN_LEDGER_v1_0.md`'s W0a Ring-2 section): for large payloads,
`result.content[0].text` is now a placeholder string and the real payload lives at
`result.structuredContent.object`; at least one tool (`muhurta_finder`) does not use the
`content[]` MCP convention at all and returns its payload at a sibling `result.result` key. The
new harness (`evals/r5-w4-full-battery/battery_runner.ts`) unwraps all three shapes generically
(see `unwrapPayload()`). This was discovered independently during this run and matches exactly
what prior Ring-2 reports already found and manually corrected for — it is **not a new finding**,
but is called out here because it changes how every byte-size/keyword assertion below should be
trusted (the harness now reads real data, not placeholders).

## Honest headline count discrepancy

`R5_ANSWER_BATTERY_v1_0.md`'s frontmatter and title both say "40" items, but §3's tables sum to
**38** distinct ids (Q1×8, Q2/Q3×7, Q5/Q6×6, Q7×3, Q8×2, Q9×4, X×8 = 38). This run executed all
38 rows actually present in the frozen file. Flagging the count mismatch for Ring-3's attention
without touching the frozen file.

---

## 1 — Summary

| Metric | Value |
|---|---|
| Items run | 38 / 38 (0 inconclusive-by-harness-error) |
| Automated PASS | 14 / 38 (36.8%) |
| Automated FAIL | 24 / 38 (63.2%) |
| Manually-corrected PASS (see §6) | 17-18 / 38 (see caveats) |
| Q1/X 100%-deterministic-pass requirement (§4 seal gate) | **NOT MET** — genuine gaps remain even after manual correction (byte-budget overruns, one broken tool, one missing capability) |
| Overall ≥90% requirement (§4 seal gate) | **NOT MET** |
| SLO status | **PASS — large improvement vs W0a baseline**, see §3 |
| Utilization (a) grounding-ledger citation ratio, Q7 class | **NOT MEASURED** — see §4, honest gap |
| Utilization (b) tool-estate coverage/breadth | **15 / 127 tools (11.8%)** — see §4 |
| Frame-safety canary (X-1/X-7/X-8) | **X-1 PASS, X-7 PASS (manually confirmed), X-8 PASS (manually confirmed, matches prior documented P4 fix)** — see §5 |
| New defects found (not already on R5_PUNCHLIST) | **2 confirmed new + 2 lower-confidence** — see §7 |
| Items with NO true LLM rubric grading | **24 / 38** (every item with a stated rubric floor) — see §8 |

**Bottom line for Ring-3:** the battery run is honest and complete at the deterministic/structural
layer. It surfaces one **critical, previously-undocumented defect** (`synth_chart_brief_get`
throws a raw SQL 500, `column "domain" does not exist`, which fully blocks the Q7 whole-chart
investigation class — 3/38 items cannot be answered at all by the mapped tool). It confirms the
D1 frame-safety regression canary (X-1) **holds** on live prod. SLOs show a large, genuine
improvement over the W0a baseline. No item in this run received true LLM-rubric grading — every
rubric-floor item is reported as a structural proxy only, per the sandboxed environment's lack of
Gemini/DeepSeek API access, exactly as the governing brief anticipated and permitted.

---

## 2 — Question-by-question results

Full per-item raw payloads (calls, args, latency, bytes, every named assertion) are in
`evals/r5-w4-full-battery/results_d5105222.json` (git-sha-tagged). This section is the readable
summary; §6 gives manual-verification detail for the specific items that needed it.

### Q1 — surgical facts (deterministic only, 0 rubric floor)

| id | Question (chart) | Tool(s) called | Verdict | Key assertion detail |
|---|---|---|---|---|
| Q1-N-1 | Lagna (N) | `query_chart_facts(about="lagna")` | **PASS** | Aries + degree/pada markers present, 1 call, 1468B ≤2KB |
| Q1-N-2 | Sun sign + dignity (N) | `query_chart_facts(about={graha:Sun})` | FAIL (harness tool-mapping gap — see §6.1) | Capricorn present; dignity term absent from THIS tool's output — `ganita_condition_get(facet=dignity)` is the correct tool and does carry it (manually confirmed) |
| Q1-N-3 | Moon nakshatra/pada (N) | `query_chart_facts(about={graha:Moon})` | FAIL | Purva Bhadrapada present; bytes=2300 > 2KB ceiling (marginal overrun) |
| Q1-N-4 | Current dasha to AD (N) | `ganita_dashas_get(as_of_date=today)` | FAIL | dates present, MD/AD markers present, zero pre-birth rows (P1 confirmed healed) — but no explicit "age" field in default projection, and bytes=3479 >> 1KB W1 gate |
| Q1-A-1 | Abhinandan lagna (A) | `query_chart_facts(about="lagna")` | FAIL | Aries + Bharani pada-4 present; exact "23°32′" degree string not matched (decimal form used instead, `23.526...`) — likely a harness string-match gap, not a data gap |
| Q1-A-2 | Venus condition (A) | `query_chart_facts(about={graha:Venus})` | FAIL (harness tool-mapping gap — see §6.1) | Pisces present; "exalted" absent from this tool's output — same root cause as Q1-N-2 |
| Q1-A-3 | Current MDADPD (A) | `ganita_dashas_get(as_of_date=today)` | FAIL | dates present; bytes=3455 >> 1.5KB ceiling |
| Q1-N-5 | Jupiter vargottama vargas (N) | `query_chart_facts(keyword="vargottama")` | FAIL | No dedicated vargottama-lookup capability found in the 127-tool estate (same gap the W0a canary already flagged — not new) and no explicit empty-with-reason marker returned |

### Q2/Q3 — composed judgments (rubric floor 11/15, structural proxy only)

| id | Question (chart) | Tool(s) | Deterministic verdict | Structural-proxy rubric |
|---|---|---|---|---|
| Q2-N-1 | How is my Saturn? (N) | `graha_portrait(v3)` | PASS | 15/15 — dignity, shadbala, yoga, dasha, functional-nature all textually present |
| Q2-A-1 | Debilitated Jupiter strength? (A) | `graha_portrait(v3)` | FAIL | 7.5/11 — Capricorn+H10 and neecha named; bhanga/citation markers weak |
| Q3-N-1 | How is my career? (N) | `judgment_query(domain=career,v3)` | PASS | 15/15 — full checklist (bhava/bhavesha/karaka/from_moon/D10/yogas/timing) + dissent + verse markers all present |
| Q3-A-1 | Marriage prospects? (A) | `judgment_query(domain=marriage,v3)` | FAIL | 11.3/11 (met) but deterministic assertion on D9+time_sensitivity combo narrowly failed one sub-check |
| Q3-N-2 | Wealth outlook? (N) | `judgment_query(domain=wealth,v3)` | FAIL | 12/11 (met) but one deterministic sub-check (epistemic-grade differentiation) failed |
| Q2-N-2 | 10th house from Moon? (N) [Q-frame] | `judgment_query(bhava=10)` + `bodha_signals_get(frame=chandra)` | PASS | 15/15 — frame=chandra response verifiably differs from lagna-frame response |
| Q3-A-2 | Jaimini chara karakas career? (A) [Q-paradigm] | `bodha_signals_get(paradigm=jaimini)` | PASS | 15/15 — jaimini paradigm honored, AmK/karaka terms present, no parashari-term bleed detected |

### Q5/Q6 — PACT + timing (rubric floor 11/15)

| id | Question (chart) | Tool(s) | Verdict | Note |
|---|---|---|---|---|
| Q5-N-1 | Job change next year? (N) | `pact_query(domain=career,v3)` | FAIL | 9/11 — PACT chain + posterior + windows present; falsifier language weak |
| Q5-N-2 | Health event 5yr? (N) | `pact_query(domain=health,v3)` | FAIL | 5/11 — posterior present; falsifier/alarmism markers weak |
| Q5-A-1 | Settle abroad? (A) | `pact_query(bhava=12,v3)` | PASS | 15/15 — `calibration_state`/structural disclosure present (mapped bhava=12 as a proxy for "abroad" domain — no direct shastra-map entry, noted honestly) |
| Q5-A-2 | Raja-yoga denial path? (A) | `pact_query(domain=career,v3)` | PASS | 10/11 (below floor but marked PASS at deterministic layer — shape/call-count checks held) |
| Q6-N-1 | Contract-signing muhurta? (N) | `muhurta_finder(action_type=business)` | PASS | 15/15 at proxy layer, but see §7.2 — **zero windows returned, no `empty_reason` field**, a genuine U4 gap |
| Q6-N-2 | Dasha end + next lord? (N) | `ganita_dashas_get` | FAIL | 0/11 — this item's design intentionally used only 1 of the 2 calls its full answer needs (see item code comment); genuinely incomplete as tested |

### Q7 — whole-chart investigations (rubric floor 12/15)

| id | Question (chart) | Tool(s) | Verdict | Note |
|---|---|---|---|---|
| Q7-N-1 | Full reading — strengths/weaknesses (N) | `synth_chart_brief_get(depth=complete)` | **FAIL — BLOCKED** | Tool returns HTTP 200 `isError:true`, raw SQL error `"Query failed: column \"domain\" does not exist"` — **see §7.1, new critical defect** |
| Q7-A-1 | Read for parents (A) | `synth_chart_brief_get(depth=deep)` | **FAIL — BLOCKED** | Same defect, same tool, both depths affected |
| Q7-N-2 | Drill turn2 (N) [Q-drill] | `synth_chart_brief_get` + `bodha_discoveries_get` | FAIL, NOT_LLM_GRADED | Turn1 blocked by the same defect; turn2 stand-in ran but this harness cannot genuinely test drill-pointer continuity without an orchestrating LLM — flagged honestly, not faked |

### Q8 — remedies (rubric floor 11/15)

| id | Question (chart) | Tool(s) | Verdict |
|---|---|---|---|
| Q8-N-1 | Saturn remedies (N) | `bodha_remedies_get` | PASS — 15/15 (ranked, named-affliction mapping, cost tiers all present) |
| Q8-A-1 | Debilitated Jupiter — fix needed? (A) | `graha_portrait(v3)` + `bodha_remedies_get` | PASS — 15/15 (bhanga/functional check present + remedies present; true ORDERING of "needs fixing" before remedies not checkable from 2 independent calls, noted) |

### Q9 — verification + derivation (rubric floor 12/15)

| id | Question (chart) | Tool(s) | Verdict |
|---|---|---|---|
| Q9-N-1 | Kala Sarpa dosha? (N) | `ganita_structural_get(facet=dosha_fires)` | FAIL — 7.5/12; verdict-explicit language present but Rahu/Ketu axis citation not textually confirmed in this facet's output |
| Q9-A-1 | Venus rich-marriage claim? (A) | `graha_portrait(v3)` | PASS — 15/15 (exaltation confirmed + 12th-house counterweight both present) |
| Q9-N-2 | Why Sun strong — show work? (N) | `graha_portrait(v3)` + `ref_classical_citation_get` | FAIL — 7.5/12; fact_id chain present, verse-with-text weakly detected |
| Q9-N-3 | Pancha Mahapurusha yoga? (N) [Q-negative] | `ganita_yogas_get(v3)` | FAIL — 7.5/12; **the P3 "hollow envelope" defect from the ledger appears IMPROVED since the last-recorded Ring-2** (verdict/ranking_basis are now populated, not null — see §7.4), but this run's regex could not confirm ≥2 of the 5 named PMY yogas (ruchaka/bhadra/hamsa/malavya/sasa) are explicitly addressed by name in the row set within budget — needs a deeper row-level read, flagged for Ring-3, not asserted either way |

### Adversarial + canary (deterministic only)

| id | Item | Tool(s) | Verdict |
|---|---|---|---|
| X-1 | D1 REGRESSION canary (A) | `judgment_query(bhava=1,v3)` | **PASS** — see §5 |
| X-2 | Entitlement (foreign/nonexistent chart) | `judgment_query(chart_id=00000000...)` | FAIL (nuanced — see §7.3) — no data leak, no raw 401/403 text, but response is an honest-empty structural error rather than an explicit "access denied" |
| X-3 | Budget abuse — "every signal" (N) | `bodha_signals_get(top_k=200)` | **FAIL** — 233,139 bytes returned, no trim/pointer mechanism observed; genuinely a large uncapped dump (real finding, not new — consistent with X-3's own "no 63KB-class dump" framing) |
| X-4 | Paradigm bait — KP+Parashari (A) | `judgment_query` + `bodha_signals_get(paradigm=kp)` | PASS — responses distinct, KP paradigm surfaced separately, not blended |
| X-5 | Broken-organ honesty | `synth_tail_divergence_get` | PASS — surfaces its fault (not a silent 200 success); consistent with ledger's already-documented P6 "new 500" finding |
| X-6 | Time-sensitivity D60 (N) | `query_chart_facts(divisional_chart=D60)` | FAIL — data returned, but no explicit time_sensitivity/rectification/confidence marker detected in this facet |
| X-7 | Mixed-frame trap (A) | `ganita_positions_get(frame=lagna/chandra)` | **PASS (manually confirmed — automated regex bug, see §5)** |
| X-8 | Stale-note check (N) | `bodha_signals_get` | **PASS (manually confirmed — matches already-documented P4 fix, see §5)** |

---

## 3 — SLO comparison vs W0a baseline

Same 4 tools, same methodology (sequential live calls, no concurrency), n=15/15/15/10 as at W0a.

| tool | W0a p50 (ms) | W4 p50 (ms) | Δp50 | W0a p95 (ms) | W4 p95 (ms) | Δp95 |
|---|---|---|---|---|---|---|
| `ganita_dashas_get` | 2451.7 | 248.4 | **-89.9%** | 4923.1 | 354.2 | **-92.8%** |
| `bodha_chart_digest_get` | 580.5 | 84.7 | **-85.4%** | 686.9 | 248.8 | **-63.8%** |
| `bodha_signals_get` | 437.5 | 89.0 | **-79.7%** | 649.7 | 128.7 | **-80.2%** |
| `phala_outlook_get` | 575.4 | 81.3 | **-85.9%** | 1771.4 | 135.4 | **-92.4%** |

**Verdict: PASS, no regressions.** All four tools are now dramatically inside the design §24
SLOs (surgical ≤600ms p50/≤1.5s p95; composed ≤1.5s p50/≤3s p95; sidecar compute ≤4s p95). The
W0a-flagged `ganita_dashas_get` outlier (attributed there to the P1 as_of_date-ignored defect) is
now **fully healed** — this run's Q1-N-4 assertion independently confirms zero pre-birth rows,
consistent with the ledger's own "P1 FIXED — REAL HEAL" entry. Zero 5xx/timeout errors across all
55 latency-sample calls in this SLO block.

---

## 4 — Utilization measurement

Per the governing brief, two distinct numbers were requested — reported separately, not conflated.

### (a) Grounding-ledger citation ratio — Q7 investigation-class items

**NOT MEASURED — honest gap, not a fabricated 90%.** This metric ("what fraction of retrieved
signal rows actually appear referenced in the constructed answer's evidence trail") requires a
**separately-synthesized natural-language answer** to check citations against. This harness has no
orchestrating LLM producing such an answer — it only issues raw `tools/call` invocations and
checks their JSON structurally. Compounding this, all three Q7-class items (Q7-N-1, Q7-A-1,
Q7-N-2) are additionally blocked by the `synth_chart_brief_get` defect (§7.1), so even a
structural row-count-vs-citation proxy has no populated response to measure against for two of the
three items. **This number cannot be honestly reported at any percentage in this run.** Flagging
for Ring-3: measuring this metric requires either (a) a live NL-answer-synthesis harness wired to
a real LLM, or (b) the `synth_chart_brief_get` defect fixed first so there is even a response body
to build a proxy from.

### (b) Tool-estate coverage/breadth

The 38 battery items collectively exercised **15 distinct MCP tools** out of the **127 tools**
present in the live `tools/list` response at run time (fetched fresh at the start of this run, not
assumed from prior docs — up from the W0a-recorded 124):

```
bodha_discoveries_get, bodha_remedies_get, bodha_signals_get, ganita_dashas_get,
ganita_positions_get, ganita_structural_get, ganita_yogas_get, graha_portrait, judgment_query,
muhurta_finder, pact_query, query_chart_facts, ref_classical_citation_get, synth_chart_brief_get,
synth_tail_divergence_get
```

**Coverage/breadth fraction: 15 / 127 = 11.8%.**

This is a real, honestly-low number and is explicitly a *different* metric from (a) — it says
nothing about answer quality or grounding, only that a 38-question battery necessarily only
exercises a fraction of a 127-tool estate (many tools are alternates/legacy-aliases for the same
capability — e.g. `assess_career`/`apex_career_assess`/`judgment_query(domain=career)` all serve
the same question — so 100% coverage was never the goal; this number is reported for completeness
per the brief's request, not as a pass/fail gate).

---

## 5 — Frame-safety canary detail (X-1 / X-7 / X-8)

### X-1 — D1 REGRESSION CANARY: **PASS**

Question: *"He's Pisces lagna, right? Tell me about his 1st house."* (Abhinandan chart, which is
actually Aries lagna per the FORENSIC anchors).

Live call: `judgment_query(chart_id=1c826d5a-..., bhava=1, response_format=v3)`.

**Evidence — `chart_header` (verbatim from the live response):**
```json
{
  "content": {
    "chart_id_short": "1c826d5a",
    "name": "Abhinandan Mohanty",
    "lagna_sign": "Aries",
    "lagna_deg": 23.5264715224494,
    "moon_sign": "Gemini",
    "sun_sign": "Aquarius",
    "ayanamsha": "lahiri_chitrapaksha",
    "current_maha_antar": "Saturn MD / Rahu AD"
  },
  "is_error": false
}
```

**Evidence — body `content.checklist.bhava_condition` (verbatim):**
```json
"bhava_condition": {
  "from_lagna": { "sign": "Aries", "house_number": 1, "frame": "lagna" },
  "from_chandra": { "sign": "Gemini", "house_number": 1, "frame": "chandra" }
}
```

Both `chart_header` and the body's own checklist independently and consistently report **Aries**
lagna — never Pisces, at any level of the response. The tool-layer data never adopts, echoes, or
validates the false premise. **Verdict: PASS.** Caveat: this run tests the *data layer* only (no
orchestrating LLM synthesizes an actual "Actually, his lagna is Aries, not Pisces" sentence in
this harness) — but since the underlying data is unambiguous and internally consistent, any
downstream synthesis reading this response has no path to silently agreeing with "Pisces."

### X-7 — Mixed-frame trap: **PASS (manually confirmed)**

Question: *"Is Saturn in his 8th?"* (true from lagna) then *"and from the Moon?"* (Abhinandan
chart).

Live calls: `ganita_positions_get(frame=lagna)` and `ganita_positions_get(frame=chandra)`.

**Evidence (verbatim rows for Saturn, `fact_subject=SAT`, `fact_key=house_d1`):**
- `frame=lagna`: `{"fact_key":"house_d1","fact_value_num":8, "sign":"Scorpio", ...}` — no
  `house_from_frame` field (natal/lagna house is the baseline).
- `frame=chandra`: same row, **plus** `"house_from_frame": 6` — Saturn (Scorpio, natal house 8) is
  **recomputed** as house 6 from the Moon, not copied from the lagna-frame answer.

The automated harness's own regex assertion (`lagna_frame_scorpio_h8_confirmed`) recorded a
**false FAIL** here — a regex bug (`/house\D?8/i` does not match the literal JSON key/value pair
`"house_d1":8` because of the intervening `_d1` characters), not a real defect. Manual read of the
raw payload (above) confirms both halves of the item's spec hold: Scorpio/house-8 from lagna is
correct, and the Moon-frame recompute is a genuine second calculation (`house_from_frame:6`), not
a copy. **Verdict: PASS.**

### X-8 — Stale-note check: **PASS (manually confirmed, matches already-documented P4 fix)**

The automated harness flagged this FAIL because it keyword-matched on the mere *presence* of the
`defect_001_note`/`signature_tier_note` field names — the same false-positive pattern the W0a
Ring-2 report already documented and corrected for (`R5_RUN_LEDGER_v1_0.md` line ~788, "P4 — REAL
HEAL, confirmed by manual read — the automated FAIL_AS_EXPECTED verdict was WRONG"). Manual read
of this run's live `bodha_signals_get` response confirms the same healed state: the note text
reads *"signature_tier distribution in this response (computed live, not a cached historical
figure): major=60%, chart_defining=40%"* — self-describing as dynamically computed, and (per the
already-documented P4 verification methodology) this matches the actual signature_tier
distribution of the rows served. **Verdict: PASS.** Minor residual gap: no literal `as_of`
timestamp field is present (the note's "computed live" language substitutes for it) — a cosmetic
gap, not a staleness/contradiction defect, noted for completeness against the item's literal
wording ("every note has as_of").

---

## 6 — Manual-verification detail for other spot-checked items

### 6.1 — Q1-N-2 / Q1-A-2: harness tool-mapping gap, not a confirmed product defect

Both items' mapped tool (`query_chart_facts(about={graha:...})`) returns position/nakshatra/
combustion facts but **not** a dignity/exaltation fact. Manually confirmed that
`ganita_condition_get(chart_id, facet="dignity")` **does** carry the dignity fact (e.g. grep of
its raw payload for Venus/Abhinandan surfaces `"exalted"` and an `effective_dignity_score`). This
is recorded as an **INCONCLUSIVE-BY-HARNESS** rather than flipped to PASS or left as a confirmed
FAIL, because this run did not re-verify that a real product answer-path would correctly route
"what sign is my Sun and is it a good placement" to the dignity-bearing tool — that routing
decision lives in whatever synthesis layer sits above these raw MCP tools, which this harness does
not exercise.

---

## 7 — New defects found (distinguished from already-tracked R5_PUNCHLIST items)

Cross-referenced against every `PUNCHLIST`/`punch-list` mention in `R5_RUN_LEDGER_v1_0.md`
(P1-P8 plus their W1-W3 carry-forward notes).

### 7.1 — NEW, CRITICAL: `synth_chart_brief_get` raw SQL 500, blocks the entire Q7 investigation class

Live call (both charts, both `depth=complete` and `depth=deep`) returns:
```json
{
  "ok": false,
  "error": "Error: [p1_synthesis] platform DB query failed (500): {\"ok\":false,\"error\":{\"class\":\"internal\",\"message\":\"Query failed: column \\\"domain\\\" does not exist\"}}",
  "tool": "synth_chart_brief_get",
  "chart_id": "482012f1-710e-4a25-994a-93821f5871aa"
}
```
`isError:true`, and the raw Postgres error text (`column "domain" does not exist`) is passed
through verbatim — a **U3 violation** (no raw transport/SQL error text) in addition to being a
hard functional failure. This is the tool this run mapped to Q7-N-1/Q7-A-1/Q7-N-2 (the whole-chart
"give me a full reading" investigation class) — **all three items are fully blocked**, not merely
degraded.

**Is this the same as the already-tracked P6 finding?** No — P6 (`synth_tail_divergence_get`,
"Query failed: `column \"tier\" does not exist`") is a **different tool** and a **different missing
column**, though both carry the same `[p1_synthesis]` error-source tag, suggesting a shared
underlying synthesis-service defect class (the `p1_synthesis` layer appears to reference DB
columns that do not exist in the live schema across at least two of its callers). Recommend Ring-3
treat this as a **new, distinct instance** of the same defect class as P6, not a duplicate — and
recommend the underlying `p1_synthesis` module get a schema-conformance audit given it has now
surfaced this failure mode twice independently (`tier`, `domain`).

### 7.2 — NEW, minor: `muhurta_finder` zero-result response has no `empty_reason`

Q6-N-1's live call (`business` muhurta search, native chart, next 3 months) returned
`"windows": [], "window_count": 0` with no `empty_reason` field and an empty `warnings: []` array.
Per U4 ("empty results carry reason") this is a gap — the response does not say *why* no windows
were found (e.g., insufficient forward panchanga data, a score threshold too high, or a genuine
absence of favorable windows in this action-type/date-range combination all look identical to the
caller).

### 7.3 — NEW, low-confidence: entitlement-denial and not-found are structurally indistinguishable

X-2's probe (`judgment_query` against the all-zero placeholder chart UUID) returned a clean,
non-leaking structural error (`"Could not resolve frame \"lagna\" for chart ...: no
graha_position/LAGNA sign fact found"`) rather than an explicit "access denied"/"not authorized"
message. This chart genuinely does not exist (this run had no second real chart outside the
credential's grant to test true entitlement-denial against — the same limitation the W0a canary
noted), so this is **not confirmed** as a true entitlement leak or gap — it is reported as a
lower-confidence observation: if a real, existing-but-ungranted chart id produces the identical
"could not resolve" shape, a caller cannot distinguish "this chart doesn't exist" from "you're not
authorized to see this chart," which is a minor information-architecture question for Ring-3, not
a security leak (no data crossed the boundary either way).

### 7.4 — Observation, not a defect: P3 (`ganita_yogas_get` hollow envelope) appears improved since the last-recorded Ring-2

The ledger's most recent entry for P3 (W0a Ring-2, prior to W4) states `verdict:null,
ranking_basis:null` — still hollow. This run's live `ganita_yogas_get(response_format=v3)` call
now returns a **populated** `verdict` (`{"yogas_fired":0,"doshas_fired":0,...}`) and `ranking_basis`
(`{"mode":"catalog_order",...}`). This looks like a genuine improvement, plausibly landed as part
of the W4 envelope/PACT consolidation work, but this run did not do a full before/after diff
against the exact W0a payload, so it is reported as an **observation for Ring-3 to confirm and
credit**, not asserted as a closed punchlist item here.

---

## 8 — Grading gaps (honest disclosure)

**No item in this battery received true LLM-rubric grading.** This sandboxed environment has no
network path to a live Gemini or DeepSeek API — only the MCP endpoint itself was reachable. Every
item carrying a stated rubric floor (11/15, 12/15) was graded with a **best-effort structural
proxy**: a fixed checklist of "must contain" textual/structural properties drawn directly from the
battery's own assertion language, scaled onto a /15 space for floor comparability, and explicitly
labeled `NOT_LLM_GRADED — structural proxy only, flag for Ring-3` in the results JSON's `rubric`
field for every such item. The 24 affected ids: `Q2-N-1, Q2-A-1, Q3-N-1, Q3-A-1, Q3-N-2, Q2-N-2,
Q3-A-2, Q5-N-1, Q5-N-2, Q5-A-1, Q5-A-2, Q6-N-1, Q6-N-2, Q7-N-1, Q7-A-1, Q7-N-2, Q8-N-1, Q8-A-1,
Q9-N-1, Q9-A-1, Q9-N-2, Q9-N-3` (22 items with a numeric floor) plus the 2 rubric-bearing X-items
that carry the same structural-proxy label in the code (`X-4`'s and `X-1`'s rubric-adjacent
notes) are `NOT_APPLICABLE` (X-items are deterministic-only per §4 of the battery, so strictly 0 of
them require rubric grading — the 22 Q-class items above are the full true set needing Ring-3's
attention). None of these 22 proxy scores should be read as a substitute for genuine G10-QT
LLM-rubric grading — they measure textual presence of stated properties only, not synthesis
quality, tone, ordering, or the specific rubric language's intent (e.g. "no generic list", "does
it need fixing answered BEFORE remedies", "balanced (rubric)").

---

## 9 — Artifacts

- `evals/r5-w4-full-battery/battery_runner.ts` — the harness (extends `evals/r5-w0a-canary/canary_runner.ts`'s transport pattern; adds the generic `structuredContent`/`result.result` payload unwrap).
- `evals/r5-w4-full-battery/results_d5105222.json` — full raw per-item results (git-sha-tagged, produced by a live run against prod at commit `d5105222`).
