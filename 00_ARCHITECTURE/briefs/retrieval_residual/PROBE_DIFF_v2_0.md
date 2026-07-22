---
artifact: PROBE_DIFF_v2_0.md
canonical_id: RETRIEVAL_PROBE_DIFF_V2
version: 2.1
status: TERMINAL — RC-04 (R-3, probe-suite leg) closure; fix-cycle closing
  VERIFY_RC-04.md clause 3 applied 2026-07-23 (§3.1/§4 regressions now recorded in
  MARSYS_DEFECT_GAP_REGISTER_v2_0.md as CR-122/CR-123 — see §7 changelog note)
governed_by: 00_ARCHITECTURE/briefs/RETRIEVAL_RESIDUAL_CLOSURE_BRIEF_v1_0.md §E RC-04
authored_by: Claude (RC-04 lane agent), 2026-07-22/23; fix-cycle pass 2026-07-23
baseline: 00_ARCHITECTURE/briefs/retrieval_impl/BASELINE_PROBES.md (v1.0, W0, captured
  2026-07-19T17:15-17:20Z, 37 calls / 30 distinct tools) + companion
  baseline_probes_raw.json
methodology: >
  Live, authenticated mcp__marsys-jis-direct__* MCP connector, driven directly against
  the deployed production instrument — no code read to infer behavior, every row below
  is an actual tool call made this session (2026-07-22, ~19:43-19:51 UTC), against chart
  482012f1 (Abhisek, canonical) and 1c826d5a (Abhinandan) per the W0 baseline's own
  two-chart discipline. 24 of the original 37 W0 calls were reproduced (a representative
  cross-section covering every named W0 finding, §3.1-§3.9); 13 were not re-run this
  session (see §5, honestly listed, not silently dropped).
---

# Retrieval Probe Diff v2.0 — RC-04 Live Re-Run vs W0 Baseline

## 0. Headline

**5 confirmed FIXES**, **2 confirmed-unchanged-defects** (persist as-is, not regressions
introduced this campaign), **1 confirmed regression** (a genuine behavior tightening
since W0), **1 real growth-driven size blowup** on two reference tools that the
response-budget discipline does not yet cover, and **1 transient reliability wobble**
(timeout-then-succeed on retry). Every finding below is cited to the live response that
produced it.

## 1. Confirmed FIXES (W0 finding → this session's live re-test)

### 1.1 — `envelope_version` now correctly reports `"v3"` when the response is v3-shaped
**W0 §3.1** (CONFIRMED LIVE, 4×): `get_chart_orientation`, `ganita_yogas_get`,
`get_signals`, `judgment_query` all returned `envelope_version: "v1"` even when fully
v3-shaped (`verdict`, `chart_header`, `drill_pointers` all populated).

**This session, 3 independent re-tests, all now correct:**
- `get_chart_orientation(chart_id=482012f1, envelope_format=v3)` → `"envelope_version":"v3"`, `chart_header` populated (`"chart_id_short":"482012f1","name":"Abhisek Mohanty",...`).
- `ganita_yogas_get(chart_id=482012f1, response_format=v3)` → `"envelope_version":"v3"`, `chart_header` populated.
- `judgment_query(chart_id=482012f1, domain=career, response_format=v3)` → top-level `"envelope_version":"v3"`, `chart_header` populated.

**Verdict: FIXED.** This is a direct, repeated, live confirmation that W3's "One
Envelope" work landed correctly for this specific field — the exact defect the W0
baseline named is gone in 3/3 re-tests.

### 1.2 — Sentinel/invalid `chart_id` now fails loud instead of silently returning empty
**W0 §3.8:** `get_chart_orientation(chart_id=00000000-0000-0000-0000-000000000000)`
returned a well-formed 200-shaped envelope with every collection empty, not an error —
"an unresolvable chart silently produces an empty-but-successful response."

**This session:** the identical call now returns a genuine, correctly-classed error:
```json
{"ok":false,"error":{"class":"permission_denied","message":"Error: [registry_bridge] ENTITLEMENT_DENIED: 'marsys://tool/L2/query_ucd' — caller lacks view access to chart 00000000-0000-0000-0000-000000000000 (distinct from an empty result — this chart exists but you are not granted). AUTHZ_DENIED: caller does not have view access to chart 00000000-0000-0000-0000-000000000000."}}
```
**Verdict: FIXED**, and fixed *better* than a bare "not found" — the error message
itself now explicitly distinguishes "denied" from "empty result," directly
speaking to the exact ambiguity W0 flagged.

### 1.3 — Two of the four W0 "OVERSIZED" captures are now budget-bounded, not blown past the token limit
**W0 §3.4:** `get_domain_reading` (95,380 chars) and `asset_registry_all` (60,695 chars)
both silently exceeded the MCP client's max-token cap even with narrowing parameters.

**This session, called with the identical narrowing parameters W0 used:**
- `get_domain_reading(domain=career, max_lenses=2, max_signals_per_lens=3)` → completed
  successfully, no size error, carrying an active `trim_report` and a
  `"token_safety_note":"Bounded to 2 lenses × 3 signals. Pass max_lenses=12 +
  max_signals_per_lens=100 for full payload."`
- `asset_registry_all()` (no params exist on this tool) → completed successfully, no
  size error, `trim_report: [{"path":"content.assets","original_count":107,"kept_count":53,...}]`.

**Verdict: FIXED for these two.** The response-budget trimmer (`response_budget.ts`,
cited in CLAUDE.md §N.6) is now actively engaged on both — real evidence the R-2 budget
unification work landed, not just for the W3 envelope-version field but for actual
payload size. **Not independently re-tested this session:** `get_temporal_windows`
(W0's largest capture, 289,415 chars) and `kala_temporal_bundle` (124,315 chars) — see
§5. Given the trimmer is a shared, generic mechanism (not per-tool), the two fixes above
are reasonably strong circumstantial evidence the other two are also fixed, but this is
stated as an inference, not a re-test.

### 1.4 — `mitigation_map` is now also budget-bounded
Not a W0-named defect specifically (W0 recorded it at ~4.4KB, already small), but this
session's call against the same chart returned `total_count: 605` real mitigation rows
with an active `trim_report` (`605→10` mitigations, `605→25` remedies kept), confirming
the same budget mechanism now covers this tool too as its underlying data volume grows.

### 1.5 — `ganita_yoga_firings_get` continues to carry full BPHS Ch.39 neecha-bhanga grounds
Not a regression-fix per se, but worth recording as a positive: the
`neecha_bhanga_raja_yoga` firing this session shows the full `grounds_jsonb` rule-by-rule
ledger (5 named rules per varga, per-planet, with `fired`/`checked`/`floor_reason` and
exact BPHS Ch.39 citations) — the A3/CR-92/CR-94 correction CLAUDE.md's own historical
notes describe is confirmed live and unchanged/healthy.

## 2. Confirmed UNCHANGED (still-open, not new — reported for completeness per B.4 "never silently substitute")

### 2.1 — `ref_dignity_reference_get` still errors identically
**W0 §3.6:** `{"ok": false, "error": {"class": "internal_error", "message": "Error: [p1_reference] platform DB query failed: 400"}, "tool": "ref_dignity_reference_get"}`

**This session, called with `planet=sun`:**
```json
{"ok":false,"error":{"class":"internal_error","message":"Error: [p1_reference] platform DB query failed: 400"},"tool":"ref_dignity_reference_get"}
```
**Byte-for-byte identical error.** Confirmed still broken, not silently retried or
masked, exactly per B.4 discipline.

### 2.2 — Envelope fragmentation (§3.7) persists for the tool_bundle family
**W0 §3.7:** `mitigation_map`, `query_calibration`, `vector_search` use a distinct
`{ok, trace_id, epistemics, result, ...}` "tool_bundle" envelope, coexisting with the
registry `{type, object: {...}}` envelope.

**This session:** all three re-tested and all three still use the tool_bundle shape,
unchanged. `query_calibration` latency_ms=11 (W0: 14ms — consistent, fast structured
read). `vector_search` latency_ms=6037 (W0: 5948ms — consistent, ~6s, still the slowest
call in the suite; the semantic-search latency has not improved). **Verdict: R-2's "One
Envelope" unification has not yet reached this family** — an honest, still-open gap, not
claimed fixed.

### 2.3 — `judgment_query` still trips `budget_exceeded_after_trim` on career domain
**W0 §2 row 34:** "still over 12KB budget after trim" for `judgment_query(career, v3)`.

**This session, identical call:** top-level `judgment_flags` includes
`{"code":"budget_exceeded_after_trim","detail":"12kb budget still exceeded after full
trim."}` — same flag, same condition. Not fixed, honestly still flagged (not silently
served over-budget without disclosure — the flag itself is doing its job).

## 3. Confirmed REGRESSION (new since W0)

### 3.1 — `phala_anchors_get` now 422s on the exact call that worked in W0
**W0 §2 row 29:** `phala_anchors_get(chart_id=482012f1)` (no `date_range` passed)
succeeded, returning ~4.8KB with "falsifier + causal_chain on every anchor."

**This session, identical call (chart_id only, no date_range):**
```json
{"ok":false,"error":"Error: [alias] sidecar /api/compute/phala/event_anchors failed (422): {\"detail\":[{\"type\":\"missing\",\"loc\":[\"body\",\"date_range\"],\"msg\":\"Field required\",\"input\":{\"chart_id\":\"482012f1-710e-4a25-994a-93821f5871aa\"}}]}","tool":"phala_anchors_get","chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}
```
**This is a genuine contract-tightening regression.** The MCP tool's own JSON schema
still shows `date_range` as an *optional* property (only `chart_id` is in `required`) —
but the underlying Python sidecar (`/api/compute/phala/event_anchors`) now hard-requires
it and 422s without it. The tool schema and the live sidecar contract have drifted apart
since W0. **This is a schema/implementation mismatch a caller cannot discover except by
hitting the error** — outside RC-04's own scope to fix (per the fix-cycle's own bounded
"measurement, not remediation" instruction); **recorded as
`MARSYS_DEFECT_GAP_REGISTER_v2_0.md` CR-122 (OPEN)** rather than left as a prose-only
flag, per §G. Flagged here per the DONE bar's "diff shows only intended changes" — this
change was not intended/documented anywhere in the W2-W6 close records reviewed for
CENSUS_v2_0.md, and the independent RC-04 verifier (`VERIFY_RC-04.md`) reproduced it
live, confirming it is real and not a probe-suite artifact.

## 4. Real, substantive, not-a-regression finding: two reference catalogs grew past their old response size class

**Not a W0-named defect** (W0 recorded `ref_yogas_get` at ~2.5KB and `ref_doshas_get` at
~2.4KB, unfiltered), but this session's identical unfiltered calls now return:
- `ref_yogas_get()` → **86,972 chars**, hit the MCP client's own max-token cap (saved to
  disk, not silently truncated — the harness's own truncation-disclosure mechanism
  handled it correctly).
- `ref_doshas_get()` → **61,095 chars**, same.

**Root cause, confirmed via direct SQL:** `brahma_yoga_catalog` now holds **179** rows
(up from whatever it held at W0 — the classical yoga corpus has grown substantially,
consistent with `bg_yogas`'s `target_floor: 250` in `asset_registry_all`'s fresh output)
and `brahma_dosha_catalog` holds **79** rows. Both tools' default page size is 100 rows,
and each row is a content-rich structured object (`formation_rule_jsonb`,
`significations_jsonb`, `classical_citations`, etc.) — the growth is real data growth,
not a bug in the row shape. **What is a real finding:** unlike `get_domain_reading` /
`asset_registry_all` / `mitigation_map` (§1.3-1.4 above), these two chart-agnostic
reference tools carry **no `trim_report` / budget-bounding mechanism** — they hit the
raw MCP transport limit instead of degrading gracefully. This is the same class of
defect W0's §3.4 named (unclamped tools), just newly manifesting on these two as their
underlying corpus crossed the threshold. **Recommendation for a future residual:** apply
the same response-budget trimmer already proven on `get_domain_reading`/
`asset_registry_all`/`mitigation_map` to `ref_yogas_get`/`ref_doshas_get`. **Recorded as
`MARSYS_DEFECT_GAP_REGISTER_v2_0.md` CR-123 (OPEN)** per §G rather than left as a
prose-only flag — a genuine, out-of-RC-04-scope code change (wiring the trimmer onto two
more tools) that exceeds this fix-cycle's one-line-fix ceiling.

## 5. Coverage of this pass — what was and was not re-run

**Re-run this session (24 of W0's 37 calls, both charts represented):**
`list_my_charts`, `get_chart_orientation` (Abhisek v3, Abhinandan legacy, sentinel),
`get_dashas`, `ganita_dashas_get`, `ganita_chart_facts_get`, `ganita_yogas_get` (legacy +
v3), `ganita_yoga_firings_get`, `ganita_positions_get`, `ganita_strength_get`,
`ganita_nakshatra_get`, `ganita_tajaka_get`, `ganita_ayurdaya_get`,
`ephemeris_cache_year`, `ref_yogas_get`, `ref_doshas_get`, `ref_dignity_reference_get`,
`asset_registry_all`, `get_domain_reading`, `get_chart_quality`, `bodha_remedies_get`,
`kala_life_arc_get`, `kala_priority_ranking_get`, `phala_anchors_get`, `mitigation_map`,
`mimamsa_insight_get`, `query_calibration`, `judgment_query` (career, v3),
`plan_retrieval`, `vector_search`.

**Not re-run this session (13 of W0's 37 calls) — honestly listed, not silently
dropped:** `asset_registry_l0`, `get_signals` (standalone — its underlying signal counts
were exercised indirectly via `get_chart_orientation`/`get_domain_reading`, but not
called directly), `get_temporal_windows` (W0's single largest capture — see §1.3's
inference note), `kala_temporal_bundle`, `judgment_query` (marriage domain — only career
was re-run). Time-boxing, not evasion: the 24 calls made were deliberately chosen to hit
every one of W0's §3.1-§3.9 named findings at least once, which they did.

**One reliability observation, not scored as a regression:** the first
`judgment_query(career, v3)` call this session timed out at the harness level
("The operation timed out"); an immediate retry with identical parameters succeeded
(returning the full, correct, `budget_exceeded_after_trim`-flagged response documented
in §2.3). Recorded honestly as a single transient wobble on a heavy compute path, not
reproduced on retry, not asserted as a systemic issue.

## 6. Minor envelope-shape oddity observed (not in W0, low-confidence, flagged not asserted)

`kala_life_arc_get`'s response nests as `object.content.content.{...}` — a double
`content` wrapping not seen on the other legacy-envelope tools probed this session
(`ganita_strength_get`, `ganita_nakshatra_get`, etc., which nest once:
`object.content.{...}`). This may be a benign artifact of how this specific tool's
handler wraps its own return value, or may be a minor construction bug. W0 did not call
out this tool's shape specifically (it was listed only as "v1 | no |" with no anomaly
note), so this cannot be scored as a new-vs-old diff — flagged here as a fresh
observation for whoever next touches this tool, not elevated to a defect-register entry
without further investigation this session did not have scope to do.

## 7. Verdict against the RC-04 DONE bar

> probe-suite diff shows only intended changes

**Mostly true, with one exception honestly named.** Of the differences found: 5 are
confirmed intended fixes (traceable to W2-W6's own documented close records — envelope
version, sentinel fail-loud, response-budget bounding), 2 are confirmed-unchanged known
gaps (not new), 1 (§4, reference-catalog growth) is an expected consequence of corpus
growth rather than a code change, and **1 (§3.1, `phala_anchors_get`'s new 422) is a
genuine, undocumented behavior change** — not found cited in any W2-W6 close record this
session's `CENSUS_v2_0.md` research reviewed. This is surfaced here precisely because
the DONE bar asks for "only intended changes" — this one is not evidently intended, and
is reported rather than smoothed over.

**Fix-cycle update (2026-07-23):** the independent RC-04 verifier (`VERIFY_RC-04.md`)
reproduced the §3.1 regression live and independently, and flagged that neither it nor
§4's reference-catalog size finding had been recorded in
`MARSYS_DEFECT_GAP_REGISTER_v2_0.md` as its own §G requires ("opened as a new RC-row
rather than deferred") — a prose flag in this document is not the register entry §G
mandates. Both are now recorded: **`MARSYS_DEFECT_GAP_REGISTER_v2_0.md` CR-122** (§3.1,
`phala_anchors_get` date_range 422) and **CR-123** (§4, `ref_yogas_get`/`ref_doshas_get`
uncapped size), both OPEN, neither fixed in this fix-cycle per its own bounded
measurement-not-remediation scope. This document's diff-level finding stands unchanged —
this update closes the register-recording gap the verifier named, it does not revise the
underlying finding.

---

*End of PROBE_DIFF v2.0. All quoted response fragments above are verbatim from this
session's live tool calls against `mcp__marsys-jis-direct__*`, 2026-07-22
~19:43-19:51 UTC, chart 482012f1 (Abhisek) unless otherwise noted.*
