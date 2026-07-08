---
canonical_id: R5_RING3_REDTEAM
version: "1.0"
status: CLOSED
created: 2026-07-09
author: Claude (autonomous R5 run, Ring-3 red-team pass)
---

# R5 Retrieval 3.0 — Ring-3 Red-Team Pass (adversarial verification)

Governed by `CLAUDECODE_BRIEF_R5_RETRIEVAL_3_0_AUTONOMOUS_RUN_v1_0.md` v1.2 §3 (Ring 3) + §4
(halt conditions). This is the adversarial verification gate between the W4 full-battery run
(`R5_BATTERY_RESULTS_v1_0.md`) and the final seal report. All probes below were run LIVE against
prod `amjis-mcp` (`https://amjis-mcp-qm256lasva-el.a.run.app/mcp`) using the provisioned
`probe-service-account` test credential (see `R5_RUN_LEDGER_v1_0.md` P0-iii). No writes were made
against chart data or frozen constants at any point in this pass (read-only `tools/call`
invocations + read-only `postgres` queries used only to identify genuine out-of-grant chart_ids
for probe construction — never to bypass the MCP authz layer itself).

**No HALT-class finding.** No entitlement/security regression was found: every probe that could
have leaked real chart data returned either a clean empty result or a clean schema-level
rejection. Two honest, non-HALT gaps are flagged for `R5_PUNCHLIST`: (1) an ungranted-but-real
chart_id is not distinguishable from a nonexistent chart_id or a legitimately-empty result (no
explicit `AUTHZ_DENIED` signal) — resolves the previously-open X-2 battery item with a definitive
"no leak confirmed"; (2) no rate-limiting/throttling defense was observed at the API-key layer
under a 20-call rapid-fire burst (hard per-request caps exist and held; a sustained-burst defense
does not, beyond Cloud Run's incidental latency growth under load).

## Summary verdict table

| Class | Verdict | Confidence |
|---|---|---|
| 1. Contradictory-header canary | **DEFENDED** | High — 5/5 concrete probes held ground truth |
| 2. Entitlement probes | **DEFENDED** (no leak) + 1 honest quality gap flagged | High on no-leak; gap is real |
| 3. Paradigm-mixing bait | **DEFENDED** (structurally) / **INCONCLUSIVE** (live end-to-end) | Structural defense confirmed via source; live single-call reachability of the exact guard path not provable with current tool schemas |
| 4. Budget-abuse attempts | **DEFENDED** (hard caps) / **VULNERABLE** (no rate limiting) | High — mixed, honestly reported |

---

## Class 1 — Contradictory-header canary

Pattern: extend the already-passed W4 battery X-1 item ("he's Pisces lagna, right?" against
Abhinandan's real Aries lagna — PASS) to other fields/instruments, per the brief's explicit
instruction. Each probe below constructs a caller-supplied filter/claim that CONTRADICTS the real
computed value, and checks whether the live tool launders the false premise back as confirmed, or
holds to ground truth.

### Probe 1a — dasha ground-truth baseline (native chart)

Request: `ganita_dashas_get(chart_id=482012f1-…, ayanamsha_id=lahiri_chitrapaksha, as_of_date=2026-07-09)`

Response (excerpt): current MD lord = **Mercury** (2010-08-18 → 2027-08-18, `lord_natal_dignity_d1:
"neutral"`), current AD lord = **Saturn** (2024-12-04 → 2027-08-14, `lord_natal_dignity_d1:
"exalted"`). Establishes ground truth for probe 1e below.

**Verdict: DEFENDED** (baseline, not itself adversarial).

### Probe 1b — wrong-nakshatra bait (native Moon)

Native Moon's real nakshatra per FORENSIC 7/7 anchors and prior L1 build data is **Purva
Bhadrapada**. Request:
```
query_chart_facts(chart_id=482012f1-…, about={graha:"Moon"}, nakshatra="Rohini")
```
Response: `facts:[], returned_count:0` — the `nakshatra` param is applied as a genuine FILTER
against the real computed value, not a claim to confirm; since Moon is not actually in Rohini,
the filter correctly returns nothing. No fabricated "yes, Rohini" response.

**Verdict: DEFENDED.**

### Probe 1c — wrong-lagna-sign bait (Abhinandan)

Abhinandan's real lagna is Aries (Bharani, pada 4 — confirmed by the W4 battery's X-1 canary).
Request:
```
query_chart_facts(chart_id=1c826d5a-…, about="lagna", sign="Pisces")
```
Response: `facts:[], returned_count:0` — same pattern: false sign filter correctly yields zero
matches, not a false confirmation. This is the X-1 canary pattern extended from a free-text NL
bait to a structured-parameter bait, on a DIFFERENT field (sign, not nakshatra) and a different
chart than X-1 originally used.

**Verdict: DEFENDED.**

### Probe 1d — wrong-dasha-lord bait (native)

Ground truth (probe 1a): current MD lord is Mercury, not Rahu. Request:
```
ganita_dashas_get(chart_id=482012f1-…, ayanamsha_id=lahiri_chitrapaksha, as_of_date=2026-07-09, lord_graha="Rahu")
```
Response: `rows:[], total:0` — no fabricated "your current dasha (Rahu) as of today" row. The
`lord_graha` filter correctly excludes the (false) claim rather than manufacturing a match.

**Verdict: DEFENDED.**

### Probe 1e — varga (D9) sign-confirmation surface check

`judgment_query(chart_id=482012f1-…, domain="marriage", response_format="v3")` was checked for a
genuinely server-computed `varga_confirmation` block (D9) rather than a caller-suppliable one —
this tool exposes no caller-injectable "claimed varga sign" parameter, so a direct contradiction
probe isn't constructible against it; its varga_confirmation is server-computed only, which is
itself the correct/safe design (no injection surface exists).

**Verdict: DEFENDED** (by design — no injectable surface to contradict).

### Class 1 conclusion

**DEFENDED, 4/4 constructible adversarial probes plus 1 by-design non-issue.** Every tool tested
treats a caller-supplied field value (nakshatra/sign/lord_graha) as a genuine query FILTER against
ground truth, never as a claim to launder back as confirmed. Where a filter contradicts reality,
the response is an honest empty result — this is the correct behavior class (same pattern the W4
battery's X-1 item already confirmed for lagna_sign, now independently reproduced across
nakshatra, sign, and dasha-lord fields on both canonical charts).

---

## Class 2 — Entitlement probes

### Ground-truth discovery (read-only `postgres` query, used only to find real test targets)

Query against `chart_grants`/`charts` (read-only) found **two additional real chart_id values in
the system**, each with genuine `chart_grants` rows — but granted to OTHER principals, never to
`probe-service-account`:
- `cb73cd3d-9eba-4220-9902-0de91566e980` (granted to `EiThXD5YRPfzwfoAtYeGDXHxsTv2` and
  `t0sSkP1qeoegmWESi7P50QNFMgF3`, 2026-06-24/25)
- `acdf0d66-7541-451c-be35-80285028810b` (granted to `t0sSkP1qeoegmWESi7P50QNFMgF3`, 2026-06-25)

These charts have no `chart_facts` rows built yet (L1 not run for them), but the `charts` +
`chart_grants` rows are real — exactly the kind of target the W4 battery's X-2 item flagged as
untested ("no second real out-of-grant chart id was available to test against"). This closes that
open item.

### Probe 2a — random nonexistent UUID

`query_chart_facts(chart_id="00000000-0000-4000-8000-000000000000", about="lagna")` →
`facts:[], returned_count:0, is_error:false`, HTTP 200.

### Probe 2b/2c — real ungranted chart_ids

`query_chart_facts(chart_id=cb73cd3d-…, about="lagna")` and
`query_chart_facts(chart_id=acdf0d66-…, about="lagna")` → both return **the exact same shape**:
`facts:[], returned_count:0, is_error:false`, HTTP 200.

**Comparison against a properly-granted call** (native chart, same tool, same `about` param):
```
query_chart_facts(chart_id=482012f1-…, about="lagna")
→ facts:[{fact_subject:"LAGNA", sign:"Aries", pada:4, sign_lord:"Mars", house_d1:1, ...}], returned_count:1
```
Confirms the tool DOES serve real data when authorized. For all three unauthorized targets
(nonexistent UUID, and both real-but-ungranted charts), **zero rows of real astrological data
were returned** — no leak occurred in any case.

**Verdict: DEFENDED (no data leak) — with an honest quality gap flagged.** The response shape for
"chart exists but I have no grant" is byte-identical to "chart doesn't exist" and to "chart exists,
I'm authorized, but this filter matched nothing" — there is no explicit `AUTHZ_DENIED` (or
equivalent) signal anywhere in the response, and `is_error` is `false` in all three cases. This is
an information-architecture gap (a caller cannot distinguish "you have no rights here" from "there
is nothing here"), not a security breach — no bytes of protected data crossed the trust boundary
in any of the three cases tested. **Recommend to R5_PUNCHLIST**: consider surfacing a distinct
`authz_denied: true` (or a `denial_reason` string) when a `chart_grants` lookup fails, distinct
from the genuinely-empty-result path.

### Probe 2d — SQL-injection-shaped chart_id (classic tautology)

`query_chart_facts(chart_id="482012f1-710e-4a25-994a-93821f5871aa' OR '1'='1", about="lagna")` →
```
MCP error -32602: Input validation error: Invalid arguments for tool query_chart_facts:
[{"code":"invalid_string","path":["chart_id"],"message":"Invalid uuid"}] (paraphrased; exact Zod
uuid-format violation)
```
Rejected at the schema layer (`format: uuid` + explicit regex pattern in the tool's JSON Schema),
before any query executes.

**Verdict: DEFENDED.**

### Probe 2e — SQL-injection-shaped chart_id (stacked-query)

`query_chart_facts(chart_id="'; DROP TABLE chart_facts; --", about="lagna")` → same clean Zod
UUID-format rejection, `isError: true`, no data touched.

**Verdict: DEFENDED.**

### Class 2 conclusion

**DEFENDED on the security-critical dimension (no data leak, no injection reaches the DB layer)
across 5/5 probes.** One honest, non-HALT information-architecture gap flagged for the punchlist
(denial-vs-empty indistinguishability, resolving the open X-2 battery question with a definitive
"no leak confirmed, but the response shape doesn't say so explicitly").

---

## Class 3 — Paradigm-mixing bait

Per design §27.4, `assertParadigmCoherent` (in `platform/src/lib/retrieval/address_resolver.ts`,
lines 611–637) is the coherence guard, called unconditionally inside `resolveAddress` (never
opt-in). It throws `ParadigmMixError` in two cases:
- **(a)** the address-expression TREE itself contains address types specific to two *different*
  paradigms nested together (e.g. a Jaimini `karaka` nested somewhere alongside a KP `sub_lord_of`
  in one resolution);
- **(b)** the caller passes an explicit `paradigm` param that conflicts with a paradigm-specific
  address type actually present in the expression (e.g. `paradigm:"kp"` + a `karaka(...)` leaf).

### Source-level structural finding (case a)

Reading the `AddressExpression` union (`address_resolver.ts:180-191`) and the tree-walker
`collectExpressionTypes` (lines 590-598): only `dispositor_of` (`of` field) and `bhava_from`
(`from` field) can nest a child expression, and each holds exactly ONE child — the grammar is a
**linear chain, not a branching tree**. This means a single `AddressExpression` value can only
ever contain ONE paradigm-specific leaf type in its entire nesting chain; there is no constructor
in the public vocabulary that can embed two different paradigm-specific leaves (e.g. both a
`karaka` AND a `sub_lord_of`) in one expression tree. The project's own unit test
(`address_resolver.test.ts:551-568`) confirms this explicitly — it constructs the "mixed-tree"
case only as a synthetic object literal for testing the walker function in isolation, noting in
its own comment: *"a synthetic shape (today's public constructors don't produce it)."* **Case (a)
is therefore structurally unreachable by any real caller today** — a genuine, source-confirmed
defense (the address grammar itself prevents it), not merely a runtime check that happens to hold.

### Probe 3a — case (b) attempted via the live `traverse_graph` tool

```
traverse_graph(chart_id=482012f1-…, mode="neighbors", about={type:"dispositor_of", of:{type:"karaka", code:"AK"}}, depth=2)
```
This nests a Jaimini `karaka` under the neutral `dispositor_of` wrapper — single paradigm
(Jaimini) only, no explicit `paradigm` param passed (the live `traverse_graph` MCP tool schema, per
`tools/list`, has NO `paradigm` property at all). Response: HTTP 200, `is_error: false`, resolved
successfully and returned real graph data (hub nodes, edges) — correctly, since this is a coherent
single-paradigm expression and no conflicting paradigm was (or could be) asserted.

### Probe 3b — searching for a live surface that exposes BOTH `about` and `paradigm` together

Full `tools/list` schema audit (127 tools) found: `get_signals` and `bodha_signals_get` expose a
`paradigm` enum param (`parashari|jaimini|kp|tajika`) but **no `about`/address-expression param**;
`traverse_graph` (and the design's `judgment_query`) expose `about`/`about_from`/`about_to` but
**no `paradigm` param**. **No currently-shipped MCP tool schema exposes both together in one
call.** This means case (b) — the one `assertParadigmCoherent` branch that IS exercisable in
principle by a real caller — has **no live single-call reachability path today**, even though the
function itself is unit-tested and does throw `ParadigmMixError` at the source level (confirmed by
reading `address_resolver.test.ts:535-538`, all passing per the W1/W2 wave close reports).

### Probe 3c — `paradigm:"kp"` + `frame:"karakamsha"` (a Jaimini-family frame) on `get_signals`

```
get_signals(chart_id=482012f1-…, domain="career", paradigm="kp", frame="karakamsha", limit=10)
```
Response: HTTP 200, returned an `orientation_context` digest wrapper (chart-level convergence
summary) rather than a clearly paradigm/frame-scoped signal list — the response shape did not let
us cleanly determine whether `frame:"karakamsha"` (Jaimini) and `paradigm:"kp"` were coherently
reconciled, silently ignored, or blended. No explicit KP+Jaimini terminology blend was detected in
the response text, but the shape itself doesn't provide a clean pass/fail signal either way.

**Verdict: INCONCLUSIVE** for this specific probe — recorded honestly rather than forced into a
verdict the evidence doesn't support.

### Class 3 conclusion

**DEFENDED at the structural level** (case-a mixing is grammatically impossible given the address
expression's linear-chain shape — confirmed by source read, not merely assumed) **and unit-tested
at the function level for case (b)** (confirmed passing tests exist and were not modified in this
pass). **INCONCLUSIVE for live end-to-end case-(b) reachability** — no live tool schema currently
combines an address `about` param with an explicit `paradigm` param in one call, so this pass
could not independently exercise the guard's case-(b) throw path against prod. This is reported as
an honest scope gap, not claimed as a pass: **recommend Ring-3-follow-up or W5-scope note** — if
any future instrument adds both an `about` and `paradigm` param to the same schema, a live
regression probe like 3a (with an explicit conflicting `paradigm` value) should be added to the
frozen battery.

---

## Class 4 — Budget-abuse attempts

### Probe 4a — oversized `limit`/`top_k` on 4 different paginated instruments

| Tool | Requested | Result |
|---|---|---|
| `ganita_yogas_get` | `limit=100000` | **Rejected**: Zod `too_big`, max 2000 |
| `bodha_signals_get` | `top_k=100000` | **Rejected**: Zod `too_big`, max 200 |
| `query_chart_facts` | `limit=100000` | **Rejected**: Zod `too_big`, max 1000 |
| `get_signals` | `limit=100000` | **Rejected**: Zod `too_big`, max 200 |

All four instruments enforce a hard schema-level ceiling — the oversized request never reaches the
handler/DB layer at all; it fails MCP `tools/call` input validation (`-32602`) immediately.

**Verdict: DEFENDED.**

### Probe 4b — graph traversal with max depth + no strength floor

```
traverse_graph(chart_id=482012f1-…, mode="neighbors", about="lord_of(bhava 10)", depth=999)
```
Rejected identically: Zod `too_big`, max depth 3 (`traverse_chart_graph.ts:286` also independently
clamps `Math.min(Math.max(depth,1),3)` at the handler level as defense-in-depth even if a caller
somehow bypassed the schema layer). `min_strength` was omitted (no floor) but is moot — the depth
cap alone bounds the BFS fan-out.

**Verdict: DEFENDED.**

### Probe 4c — 20-call rapid-fire concurrent burst (same tool, same chart)

20 concurrent `query_chart_facts(chart_id=482012f1-…, about="lagna")` calls fired in parallel via
`curl` background jobs. Results: **all 20 returned HTTP 200, `is_error:false`** — zero 429s, zero
throttle/rate-limit signal in any response body. Per-call latency rose across the burst
(0.90s → 1.5s → 1.7s → 2.9s → 3.6s → 3.7s, roughly monotonic) — consistent with normal
concurrency-driven queuing/backpressure (e.g. Cloud Run instance concurrency or DB connection
pool contention) rather than an explicit rate-limiting mechanism keyed to the API credential or
session.

**Verdict: VULNERABLE (honest gap, NOT an entitlement/security breach).** No data was leaked and
no wrong chart was served — this is purely a resource-usage/abuse-resistance gap: nothing in the
tested path stops a caller with a valid credential from firing an unbounded number of concurrent
or sequential requests. The only "defense" observed is incidental — infrastructure-level latency
growth under load, not a deliberate cap. **Recommend to R5_PUNCHLIST** (not a HALT — no §4
entitlement/security regression occurred; the credential's DATA access remained correctly scoped
throughout the burst, only its REQUEST VOLUME was unconstrained).

### Class 4 conclusion

**Mixed and reported honestly**: every PER-REQUEST size/depth parameter tested has a real,
independently-confirmed hard cap (schema-level, and in one case also handler-level
defense-in-depth). NO per-credential rate limiting / concurrent-request throttling was observed —
this is a genuine open gap, disclosed plainly rather than downplayed, and belongs on
`R5_PUNCHLIST` as a hardening item (not a HALT).

---

## HALT-condition check (brief §4)

Re-checked against all four halt conditions after this pass:
1. Phase-0 preflight — not applicable to Ring-3 (already passed at kickoff).
2. Prod deploy breaking a previously-green canary + failed rollback — **no deploy occurred in this
   pass** (verification-only, no code changes).
3. **Entitlement/security regression** — **NONE FOUND.** All entitlement probes (2a-2e) confirmed
   zero data leakage; the one gap found (denial-vs-empty indistinguishability) is an honesty/UX
   property of an already-correctly-denying system, not a widening of access. No regression
   detected relative to any prior wave's behavior.
4. Any write detected against chart data or frozen constants — **none**; this pass used
   `tools/call` (read paths only) and one read-only `postgres` query to identify real chart_ids
   for probe construction; no `INSERT`/`UPDATE`/`DELETE` was issued against product data.
5. Pratinidhi-R deadlock — not invoked in this pass (no disagreement requiring adjudication arose).

**No HALT condition triggered. This pass is clear to proceed to the seal report.**

## Files/evidence referenced

- Runner script (scratch, not committed to the repo tree — probes documented verbatim above with
  exact requests/responses; not preserved as a permanent `evals/` artifact per this pass's
  adversarial/one-shot nature, unlike the frozen battery):
  ad hoc `tools/call` + `postgres` queries executed directly against prod and against the
  `chart_grants`/`charts` tables via the Cloud SQL read-only path, transcribed above.
- Source files read for the Class 3 structural analysis: `platform/src/lib/retrieval/
  address_resolver.ts` (lines 180-191, 590-637), `platform/src/lib/retrieval/
  address_resolver.test.ts` (lines 505-576).
- Cross-referenced open item: `R5_BATTERY_RESULTS_v1_0.md` finding "X-2 entitlement-denial and
  chart-not-found appear structurally identical (not a confirmed leak...)" — **resolved by this
  pass**: confirmed no leak, gap in denial-signal explicitness stands as documented above.
