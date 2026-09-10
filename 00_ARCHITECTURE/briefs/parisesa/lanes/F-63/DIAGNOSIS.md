---
finding_id: F-63
tier: TIER3-EXPERIENCE
stream: S4-VACA (narration fidelity)
status: DIAGNOSIS-COMPLETE
verdict: OPEN-mechanism-found
---

## Live Reproduction

Both MCP calls executed live 2026-08-16 against `mcp__marsys-jis-direct__ganita_chart_facts_get`.
Raw JSON captured in this lane dir:
- `native_chart_panchanga_raw.json` (chart_id `482012f1-710e-4a25-994a-93821f5871aa`, category=panchanga)
- `comparison_chart_panchanga_raw.json` (chart_id `1c826d5a-41cb-4450-b4dc-59d440e5f75a`, category=panchanga)

**Native chart**: 38 panchanga rows returned. Row confirmed present:

```json
{"fact_subject":"YOGA_UNKNOWN","fact_category":"panchanga_special_yoga_combinations",
 "active_at_birth_flag":"true","combination_name":"unknown",
 "constituent_facts_jsonb_atomic":{"vara":"Ravivara","tithi":"Shukla Tritiya","nakshatra":"Purva Bhadrapada"}}
```

**Comparison chart** (`1c826d5a-...`): 37 panchanga rows returned. No `fact_subject=YOGA_UNKNOWN`
and no `fact_category=panchanga_special_yoga_combinations` row present anywhere in the response —
confirmed absent, not present-and-inactive.

Reproduction is CONFIRMED LIVE, exactly as the finding describes.

## Claim Decomposition

- (a) "a detector recognized SOME special combination is active" — **TRUE, and stronger than the
  claim states.** The detector (`detect_all_special_yogas` in `special_yogas.py`) determined that
  for the native's birth panchanga (vara=Ravivara/1, nakshatra=Purva Bhadrapada/25), the classical
  **Panchaka Dosha yoga** (`detect_panchaka`, `special_yogas.py:299-319`) fires: nakshatra 25 ∈
  `PANCHAKA_NAKSHATRAS {23,24,25,26,27}` AND vara 1 ∈ `PANCHAKA_VARAS {7,1,3}` (shastra_tables.py
  §21, lines 601/605). This is the only one of the 9 detectable special yogas that fires for this
  chart's birth-moment (verified by hand against all 9 tables: Sarvartha Siddhi, Amrit Siddhi, Ravi
  Pushya, Guru Pushya, Tripushkar, Dwipushkar, Siddha Yoga, Bhadra all fail to match; only Panchaka
  matches).
- (b) "it could not resolve WHICH one" — **FALSE as literally stated; the real mechanism is
  different and more specific.** The detector fully knows which yoga fired — `detect_panchaka`
  returns `_yoga_dict("panchaka", ...)` (special_yogas.py:317), i.e. the dict key `"yoga"` is
  populated with the string `"panchaka"`. The classical name is not lost upstream. It is lost at
  the consuming step (see Mechanism below), which reads the dict under keys that never exist on it.
- (c) "served the literal string 'unknown' instead of either the real classical name or an honest
  null/inactive state" — **TRUE and confirmed to file:line.**
- (d) "conditional (chart-specific), not a universal placeholder" — **TRUE, confirmed structurally.**
  `_emit_special_yoga_combinations` (ga_panchanga_writer.py:1047-1084) only emits rows at all when
  `pi.special_yogas_instant` is non-empty (line 1055-1057: `yogas = pi.special_yogas_instant or []`
  → `if not yogas: yogas = []`; the `for yoga_dict in yogas:` loop then emits nothing when the list
  is empty). For the comparison chart (vara=Shanivara/7, nakshatra=Ardra/6), none of the 9 special
  yogas fire (Ardra=6 is not in any of the vara/nakshatra tables checked, including Panchaka's
  {23,24,25,26,27}), so `special_yogas_instant` is empty and zero rows — including no `YOGA_UNKNOWN`
  — are emitted. This exactly matches the observed absence.

## Mechanism (file:line, quoted code)

**Root cause: a dict-key mismatch between producer and consumer — not a missing-mapping /
partially-implemented lookup table as the corpus's DIAGNOSIS-INCOMPLETE note speculated.**

Producer — `platform/python-sidecar/panchang_engine/special_yogas.py:68-77`:
```python
def _yoga_dict(name: str, start_utc: datetime, end_utc: datetime,
               strength: str, stars: int) -> dict:
    """Canonical special-yoga result dict."""
    return {
        "yoga": name,
        "start_utc": _ensure_utc(start_utc),
        "end_utc": _ensure_utc(end_utc),
        "strength": strength,
        "stars": stars,
    }
```
Every one of the 9 `detect_*` functions (`detect_sarvartha_siddhi`, `detect_amrit_siddhi`,
`detect_ravi_pushya`, `detect_guru_pushya`, `detect_tripushkar`, `detect_dwipushkar`,
`detect_siddha_yoga`, `detect_bhadra`, `detect_panchaka`) builds its result exclusively via this
helper. The classical name is **always** stored under the key `"yoga"`. No dict this module ever
produces carries a key called `"name"` or `"yoga_name"`.

Consumer — `platform/python-sidecar/ga_writers/ga_panchanga_writer.py:1059-1060`:
```python
for yoga_dict in yogas:
    yname = yoga_dict.get("name", yoga_dict.get("yoga_name", "unknown"))
```
This reads `yoga_dict.get("name", ...)`, falling back to `yoga_dict.get("yoga_name", ...)`, falling
back to the literal `"unknown"`. Since the real dicts never contain either `"name"` or `"yoga_name"`
(only `"yoga"`), **this fallback fires unconditionally, every single time this loop runs, for every
one of the 9 possible special-yoga types** — there is no code path today by which `yname` can ever
resolve to a real classical name. `subj = f"YOGA_{yname.upper()...}"` then always produces
`YOGA_UNKNOWN`, and `combination_name` is always written as the literal string `"unknown"`
(ga_panchanga_writer.py:1066-1069).

This is a strict key-mismatch bug, not a "detected but genuinely unmapped" partial-implementation
branch. The corpus's DIAGNOSIS-INCOMPLETE mechanism guess ("some combinations recognized and named,
this one detected-but-unmapped") does not hold — there is no per-yoga name-mapping table at all in
the consumer; every combination that ever fires hits the identical always-`"unknown"` fallback.

**Contributing factor — test coverage masks the bug.**
`platform/python-sidecar/tests/test_ga4_writer.py:176-178`:
```python
pi.special_yogas_instant = [
    {"name": "Sarvartha Siddhi Yoga", "yoga_name": "Sarvartha Siddhi Yoga"}
]
```
The test fixture invents a dict shape (`"name"`/`"yoga_name"` keys) that the real detector in
`special_yogas.py` never produces (it only ever emits `"yoga"`). The test therefore exercises a
code path that cannot occur in production and passes green while the real key (`"yoga"`) is never
read anywhere in `ga_panchanga_writer.py`. This is a §N.8 Earned-Signal-class defect: the "special
yoga name" flow has a passing test with no detector behind the actual production key shape.

## Sibling Census

Searched all of `platform/python-sidecar` for `.get(..., "unknown")` / `.get(..., "unmapped")` /
bare `= "unknown"` assignment patterns (excluding this file and tests). ~25 hits total. Manually
inspected the ones structurally similar to F-63 (a name/label pulled from a producer dict via
`.get()` with a string-literal default):

- `bo_pratijna.py:307` (`entry.get("dignity_state", "unknown")`), `mi_darshana.py:158`
  (`r.get("domain", "unknown")`), `bo_cgm_paths.py:163` (`start_node.get("node_subject",
  "unknown")`) — inspected each producer; in all three cases the key read (`dignity_state`,
  `domain`, `node_subject`) **does** genuinely appear in the producing dict/row in the normal case,
  so the `"unknown"` default is a legitimate defensive fallback for a field that can be legitimately
  absent, not a guaranteed-always-fire mismatch. These are NOT the same defect class.
- No other instance found where the fallback keys structurally never match anything the named
  producer emits. **F-63's `ga_panchanga_writer.py:1060` is the only confirmed instance of the
  "guaranteed-always-unknown" key-mismatch pattern** in this codebase as searched.
- `special_yogas.py` itself and its `_yoga_dict()` helper have exactly one consumer
  (`ga_panchanga_writer.py`'s `_emit_special_yoga_combinations`), so there is no second call site
  to independently check for the same mismatch.

**Sibling count: 0 additional instances of the same defect class confirmed; 1 total (this finding).**

## Blast Radius

- `platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py` (L2 Bodha) explicitly knows
  about this L1 fact category: `_BIRTH_MOMENT_CATS` (line 241) includes
  `"panchanga_special_yoga_combinations"`, and the domain-tagging map (line 509) tags it
  `["spirituality", "character"]`. So this category is in-scope for L2 Bodha's birth-moment
  signal/domain-relevance machinery for the native's `spirituality`/`character` reads.
- Searched the rest of the repo (`grep -rn "combination_name"`) — no other file references
  `combination_name` specifically, so no confirmed hardcoded narration template is caught quoting
  the literal `"unknown"` string verbatim today. The concrete downstream exposure is: any generic
  fact-to-signal path in `bo_laksana.py` (or later) that surfaces raw `chart_facts` rows for the
  `panchanga_special_yoga_combinations` category for this chart would surface a spirituality/
  character-tagged row whose value is the literal string `"unknown"` — an N.7-class narration-
  fidelity defect if/when it is ever narrated, though no such narration template was found to exist
  yet. Flagging as a plausible but unconfirmed downstream leak, not a proven one.
- **No overlap with `ekv/b-01-dignity-oracle-fix`.** Checked `git diff main...ekv/b-01-dignity-
  oracle-fix --stat`: that branch touches `dignity_oracle.py`, `ga_structural_writer.py`,
  `ga_vargas_writer.py`, `bo_pratijna_v4_engine.py`, and test files for those — none of
  `ga_panchanga_writer.py`, `special_yogas.py`, or `test_ga4_writer.py`. The two fixes are in
  disjoint files with no shared code path.

## Verdict

**OPEN-mechanism-found.**

Root cause fully traced to file:line: `ga_panchanga_writer.py:1060`'s
`yoga_dict.get("name", yoga_dict.get("yoga_name", "unknown"))` reads keys that
`special_yogas.py:_yoga_dict()` (lines 68-77) never produces — every `detect_*` function stores the
classical yoga name under the key `"yoga"` only. The fallback to the literal string `"unknown"`
therefore fires unconditionally for every special-yoga combination ever detected across all 9
classical yoga types, for any chart. The correct classical name for the native's specific firing
(Panchaka Dosha, per `nakshatra=Purva Bhadrapada(25) × vara=Ravivara(1)` matching
`PANCHAKA_NAKSHATRAS ∩ PANCHAKA_VARAS`, `special_yogas.py:299-319`, `shastra_tables.py:594-605`) is
already present in the dict the writer receives — it is simply read under the wrong key name. A
one-line fix (read `.get("yoga", ...)` instead of `.get("name", yoga_dict.get("yoga_name", ...))`,
or better, fix the fallback default from `"unknown"` to `None` per §N.7 item 6's "honest null beats
an invented judgment") resolves it. The test fixture at `test_ga4_writer.py:176-178` must also be
corrected to match the real producer's dict shape (`{"yoga": ..., "start_utc": ..., "end_utc": ...,
"strength": ..., "stars": ...}`) or it will continue to pass green without ever exercising the real
code path.
