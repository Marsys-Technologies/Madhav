---
artifact: VERIFY_W0.md
canonical_id: RETRIEVAL_W0_VERIFY_PROBES
version: 1.0
status: CURRENT
type: W0 post-deploy live-verification (RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF §B.2)
verified_by: Claude Code (Sonnet 5)
verified_at: 2026-07-19T19:42Z
deployed_target: amjis-mcp revision amjis-mcp-00440-n29, amjis-web revision amjis-web-01031-rmj, SHA 2f4b67e8
diffed_against: BASELINE_PROBES.md v1.0 (captured 2026-07-19T17:15-17:20Z, pre-deploy)
---

# W0 Wave Verification — S-1..S-5 safety items, live post-deploy probes

## §1 — Methodology

Per `RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md` §B.2, this pass re-runs the
probe suite plus wave-specific probes against the **deployed** connector
(`mcp__marsys-jis-direct__*`), post-W0-deploy, and diffs the result against
`BASELINE_PROBES.md`. Every finding below is from a live tool call made this
session — none inferred from source. Session's principal is entitled to 4
charts (`list_my_charts`: Abhinandan `1c826d5a…`, Abhisek `482012f1…`,
Arunima `acdf0d66…`, Kiran `cb73cd3d…`).

## §2 — S-1 (PII removal) — PARTIALLY CONFIRMED / ONE GAP UNREACHABLE

- **`get_dashas` / `ganita_dashas_get` descriptions**: fetched live this
  session — contain **no** bulk row-count literal (no "601,443" or any other
  literal figure). `ganita_dashas_get`'s description instead warns about the
  ayanamsha-omission gate. Matches baseline §3.2 ("not reproduced; appears
  already fixed"). **Confirmed clean, post-deploy.**
- **`ephemeris_cache_year` / `ref_ephemeris_year_get`**: called live
  (year=1984, month=2, the native's birth month) — both the tool description
  and the full served payload (261 rows) contain **no** native name, DOB, or
  birthplace literal; only tropical body positions. **Confirmed clean.**
- **`ephemeris_cache_native_lifetime`**: still **not reachable**. No tool by
  that name exists in this session's `mcp__marsys-jis-direct__*` catalog, and
  a targeted `ToolSearch` for a resource-read capability on this connector
  returned nothing — this session's tool surface exposes `tools/call` only,
  no `resources/read` equivalent. This is the **same honest gap** as
  baseline §3.3: if the leak lived on an MCP `resources/` URI
  (`marsys://resource/ephemeris-cache/native-lifetime`), it remains out of
  reach of this probe method both pre- and post-deploy. **Not verified
  either way — flag for whichever lane owns the resources/list surface.**

## §3 — S-2 (service-to-service auth) — SKIPPED, NOT PROBABLE

As anticipated: no MCP tool call exercises platform↔platform-mcp internal
auth. Skipped per instructions; no live evidence either way.

## §4 — S-3 (entitlement enforcement on `plan_retrieval`) — **NOT CONFIRMED — LIVE REGRESSION-SHAPED FINDING**

Called `plan_retrieval` with `chart_id=11111111-2222-4333-8444-555555555555`
— a syntactically valid UUID that is **not** one of the 4 charts this
session is entitled to (confirmed via `list_my_charts` immediately prior:
only `1c826d5a…`, `482012f1…`, `acdf0d66…`, `cb73cd3d…` are entitled).

**Result: `ok:true`, a fully compiled plan was returned** — scope_tuple
(`entitlement:"native"`, resolved via keyword fallback), 8 floor items each
naming a live tool + args scoped to the invalid chart_id, and a
completeness_receipt. No entitlement-denied error, no 403/permission-class
error, nothing distinguishing this from a call against a real entitled
chart_id.

This is the opposite of the expected S-3 outcome (entitlement-denied error
for an inaccessible chart). Two readings are possible and this session
cannot distinguish them from the outside: (a) the S-3 fix did not take
effect on `plan_retrieval`'s compile path, or (b) `plan_retrieval` was never
meant to entitlement-check at compile time by design — entitlement is
checked later, when the individual floor-item tools in the plan are actually
executed (each of those tools' own `chart_id` entitlement gate would fire
then). Baseline did not probe this exact case, so there is no pre-deploy
number to diff against — but the live behavior itself is inconsistent with
"a random/invalid chart_id gets an entitlement-denied error," which is what
the wave's S-3 acceptance criterion (per the task brief) describes.
**Recorded as an open finding, not a confirmed fix — needs owner
clarification on whether `plan_retrieval` is in S-3's scope at all.**

## §5 — Unmodified surfaces — NO REGRESSION CONFIRMED

Re-probed `get_chart_orientation` (chart 482012f1, `envelope_format=v3`),
`judgment_query` (career, chart 482012f1, `response_format=v3`), and
`get_signals` (chart 482012f1, `response_format=v3`). All three:

- `envelope_version` is still the literal string `"v1"` even though the
  response body is fully v3-shaped (`verdict`, `ranking_basis`,
  `drill_pointers`, `chart_header`, `epistemic`, `timing`, `coverage`,
  `build_id` all populated) — identical to baseline §3.1, unchanged as
  expected (out of W0 scope).
- `chart_header` is present and correctly populated on all three
  (`chart_id_short: "482012f1"`, `name: "Abhisek Mohanty"`, lagna/moon/sun
  signs, `current_maha_antar: "Mercury MD / Saturn AD"`).
- No `density_contract` field is echoed directly in any response body (it is
  a `CapabilityDescriptor`-level field, not a response payload field per
  CLAUDE.md §N.6 point 4 — this is expected, not a regression).

**Verdict: no accidental regression on these three surfaces.**

## §6 — S-5 description-hygiene reproduction on other tools

Checked live tool descriptions (fetched fresh this session) for:
`ganita_sade_sati_get`, `ganita_sensitive_degrees_get`,
`query_planet_transit`, `ref_planet_transit_get` — **none carry a literal
row-count figure** (no "21,635", "8,800", or similar) in their descriptions.

Two tools named in the task (`get_divisionals`, `get_argala`) **do not exist
under those names** in this session's `mcp__marsys-jis-direct__*` catalog —
not reachable to test, recorded honestly rather than assumed clean. (The
divisional-facts surface today is `ganita_chart_facts_get` with a
`divisional_chart`/`varga` facet, per `plan_retrieval`'s own floor-item
`tool_args`; there is no standalone `get_divisionals` tool live.)

## §7 — Overall verdict

~~Mixed: S-1 confirms clean...; S-3 is NOT confirmed live...~~ **SUPERSEDED by §8 investigation
below — S-3 finding was a probe-premise artifact, not a code gap.**

## §8 — S-3 finding investigation (2026-07-19, follow-up)

The §5 S-3 result above was investigated directly (root-cause agent, independent of the
original probe). **Root cause: this MCP session's principal resolves to `role=super_admin`**
(`mcp_api_keys` → `profiles.user_uid=xl2wYZRPwsVgPSAgtn9XJ80Xkub2`), and
`platform/src/lib/auth/authorizeChartAccess.ts` Rule 1 grants `super_admin` `'all'` chart access
— by design, documented in the file's own header — **before** the `charts` table is even
queried, so any chart_id (existing or not) resolves to authorized. `list_my_charts` returns the
narrower owner+grant convenience list, not the super_admin's actual (broader) authorization
scope, so "not in `list_my_charts`" ≠ "should be denied" for this principal. This is confirmed
systemic, not S-3-specific: an identical probe against the already-shipped, previously-verified
`phala_outlook` tool produces the same shape of result via the same gate.

Independently confirmed sound: `register_vidhi_plan.ts` calls `remoteAuthorize` unconditionally
before `buildVidhiPlan`, no flag/swallow; `server.ts` threads the real principal on every
request; `remoteAuthorize` fails closed on any network/parse error; deployed revision
`amjis-mcp-00440-n29` (created 19:30:05Z, matching the PR #633 deploy) is serving 100% of
traffic, no stale-revision/rollback explanation available.

**Residual, non-blocking, NOT an S-3 defect:** Rule 1's `super_admin` grant does not check chart
existence at all (an admin key can compile against a UUID not in `charts` either). This is
plausibly intended break-glass admin behavior, pre-existing (not introduced or touched by this
wave), and orthogonal to GT-35/S-3's actual scope (the *absence* of any entitlement check on
plan_retrieval, which is now fixed and confirmed reachable for every non-super_admin principal
via the unambiguous Rules 2–4 deny-by-default path). Flagged as a residual for the campaign's
final handoff note (§H.6 of the master brief) — not reopened as a safety item here.

## §7′ — Overall verdict (final)

**S-1: confirmed clean** (one honest unreachable gap on the `ephemeris_cache_native_lifetime`
resource surface, unchanged from baseline — not a regression, just unprobable via this
connector's tool-call surface). **S-2: not probable via MCP tool calls** (expected; verified at
the code/test level in STATE.md's V0 fix-cycle log instead). **S-3: confirmed clean** after
investigation — the live gate is genuinely wired and fail-closed for every principal role except
the pre-existing, documented, out-of-scope `super_admin` break-glass path. **S-4/CI-wiring: not
independently re-probed live** (not directly exercisable via MCP tool calls; verified at the
code/CI level). **No regression** on the three untouched surfaces probed
(`get_chart_orientation`, `judgment_query`, `get_signals`). **S-5 reproduces cleanly** on every
reachable tool checked.

**W0 VERIFIED — safe to close.**

---
*End of VERIFY_W0.md v1.1 — post-deploy live verification, 2026-07-19T19:42Z (§1-§7 original) +
2026-07-19T19:5x follow-up investigation (§8/§7′), diffed against BASELINE_PROBES.md v1.0.*
