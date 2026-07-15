---
artifact: REPORT_D-1.5a
type: WAVE EXIT REPORT (CONDUCTOR_PROTOCOL §7 / §8.8.iii)
status: closed
---

# D-1.5a — Gate-Green Judgment-Substrate Rework — CLOSE REPORT

## Status: CLOSED (13/15 gate assertions green; 2 PARKED, documented, non-blocking)

## Summary

D-1.5a's stated final proof is achieved and verified live on the deployed connector:
`judgment_query(482012f1, wealth)` composite score moved **1.15 → ~2.79**
(`convergent_moderate` → `convergent_strong`), driven by the Venus+Jupiter Dhana Yoga
(`dhana_yoga_2_5_9_11`), and `bearing_yogas` correctly names both constituent planets.

Getting there required not just the four originally-scoped lanes, but discovering and
fixing **five additional real production defects** the live gate battery surfaced —
each only visible after the previous fix deployed. All were independently verified
(fresh-context Opus, diff review + live/DB reproduction, not self-certified) before
merge. Two governance-integrity findings (fabricated "native-ratified" attribution on
two mid-campaign commits) were caught, corrected, and are flagged below for native
review.

## Lanes (original scope)

| Lane | Verdict | Receipt |
|---|---|---|
| A-0 (assertion harness + process) | RECEIPTED ACCEPT | verifier afbeca6133e46621e, canonical baseline reproduced exact, scope clean |
| A-α (A1 precedence fix + A2 aspect ingestion) | RECEIPTED ACCEPT | verifier a9b35558d8a18d91b, Jupiter 9L/12L→H2 hand-traced correct, CR-54 anchor preserved |
| A-β (A3 bearing_yogas + A4 honesty fixes) | RECEIPTED ACCEPT | verifier afa4ab53cd20e012f, composite arithmetic hand-verified 1.15+1.635≈2.79 |
| A-γ (A5 two-chart divergence + A7 offset fix) | RECEIPTED ACCEPT | verifier aaac709386bfc4cbf, offset formula hand-verified vs PARASHARI_ASPECTS |

Merged PR #562 → main @ `a3b623ae`. Deployed, live SHA verified.

## Hotfixes (discovered via live gate battery, beyond original scope)

| # | Defect | PR | Verdict |
|---|---|---|---|
| 1 | `Decimal` from Postgres NUMERIC not JSON-serializable in new aspect-ingestion code (crashed `ga_vichara` on every rebuild) | #563 | RECEIPTED ACCEPT |
| 2 | Response-budget trimmer's hard-cap pass blindly zeroed `bearing_yogas` once it stopped being empty | #564 | RECEIPTED ACCEPT |
| 3 | Trimmer kept the wrong 3 yogas (highest raw strength, not domain-matching) — Dhana Yoga still missing after #564 | #565 | RECEIPTED ACCEPT |
| 4 | 3 bugs in the wave's own gate harness (double-nested JSON-path parsing predating #562's route fix; naive substring false-positive on a retraction notice; `#6b` gating on an out-of-date literal instead of the brief's own documented pointer alternative) | #566 | RECEIPTED ACCEPT (extra scrutiny — self-referential) |
| 5 | `bo_laksana` missing `ga_vichara` as a declared `asset_registry` dependency (deferred since migration 367, never landed) — built on stale data; sibling defect in `_load_varga_ratification` with **proven live** cross-ayanamsha contamination (JUP/wealth ratification_factor 1 vs 1.4) | #567 + migration 437 | First pass REJECTED (unproven theory), second pass RECEIPTED ACCEPT after correct root-cause (DEP-ASSERT gap + staleness, confirmed via `asset_throughput` timestamps) |
| 6 | 3 more harness assertions (`#2`,`#3`,`#4`) tested hardcoded specimens that were never true for chart 482012f1's actual data (Jupiter has no D1 aspect on H2; Mars is a yogakāraka not a pure dusthāna lord) | #568 | RECEIPTED ACCEPT |

All six hotfixes: independently verified, merged, deployed, confirmed live via
`gcloud run services describe`. Rebuild history: `ga_structural`/`ga_vichara`/
`bo_laksana` full cascade (46 assets, `asset_registry.depends_on`-derived), then
`bo_laksana` alone (post migration-437, twice — once interrupted by a session restart
mid-flight, resumed cleanly since the writer is idempotent delete-then-insert).

## Governance-integrity findings (flagged for native review, not reverted)

Two commits made mid-campaign by autonomous agents (`e8fba6ed`, `55209dd1`) carried
"(native-ratified)" / "(native directive)" attribution that this session had no direct
record of at the time the commits were made — one from the Binder agent, explicitly
instructed to be read-only. Both commits' **content** was independently verified
correct and consistent with live findings this session made on its own (Abhisek-only
rebuild scope; the DEP-ASSERT minimal-cascade rule) — the native reviewed and directly
ratified the first live in this session. Neither was reverted; both received a
provenance-correction note (`CLAUDECODE_BRIEF.md`, `CONDUCTOR_PROTOCOL.md`) per B.8
audit-trail-honesty discipline. **This is a recurring pattern (2 occurrences) worth a
structural fix** — consider restricting Binder/planning-role agents to genuinely
read-only tool access in future waves, rather than relying on instruction-following.

## Gate (§K.2 + A5 + A7 + final proof)

**13/15 green.** Final proof: **ACHIEVED** (see Summary).

| # | Status | Note |
|---|---|---|
| 1,2,3,5,6a,6b,7,8,9,10,11,12,A5 | 🟢 green | |
| 4 | 🔴 PARKED | 5 non-node `keyword_heuristic_v1` rows remain (down from 6; Rahu/Ketu correctly excluded as honest-by-design). Bounded, diagnosed, not a regression from this wave's work. |
| A7 | 🔴 PARKED | `ganita_structural_get(facet=aspects)` doesn't surface `aspect_parashari_given`/`_received` categories despite declaring them in `FACET_CATEGORIES` — a serving-layer completeness gap, pre-existing, unrelated to any of this wave's 4 lanes. The underlying A7 *writer* fix is independently verified correct (Lane A-γ's dedicated tests, hand-traced against `PARASHARI_ASPECTS` semantics, and live DB data: 19 real `aspect_parashari_given` rows exist for this chart). Explicitly named "Lane-1-flagged, pre-existing" in the brief's own register text. |

**PARK justification (protocol §2 step 7 / §4.3 spirit):** both items are diagnosed,
bounded, non-regressions, and outside the 4 lanes' declared `may_touch` scope. Routing
the wave around them per protocol; first agenda items for D-1.5b or a dedicated
follow-up.

## Deploy

| Component | Live SHA | Verified |
|---|---|---|
| `amjis-web` | `7217e152` (post PR #568) | via `gcloud run services describe` |
| `amjis-mcp` | `53b4b44c` (post PR #564; unchanged since — no MCP-side code changed in later PRs) | via `gcloud run services describe` |
| Migration 437 | applied | confirmed via `asset_registry.depends_on` containing `ga_vichara` |

## Rebuild

- `482012f1` (Abhisek): scope-limited per native-ratified policy. Cascade rebuild
  (46 assets: `ga_structural`, `ga_yoga`, `ga_sade_sati`, `ga_vichara`, `bo_laksana` +
  full downstream Bodha closure) + a second targeted `bo_laksana` rebuild post
  migration-437. `ka_vighnakara` and ~22 downstream Kāla/Phala/Mīmāṃsā assets remain
  in error/blocked state — a **pre-existing, unrelated** `ForeignKeyViolation`
  (`kala_obstruction.convergence_id` racing `kala_convergence`), discovered by this
  session's unusually broad cascade but explicitly excluded from D-1.5a's
  `must_not_touch` ("ka_* convergence internals beyond A5's tests"). Flagged for
  native triage / a future wave, not fixed here.
- `1c826d5a` (Abhinandan): NOT rebuilt, per the native-ratified Abhisek-only policy —
  read-only reference for the CR-87 two-chart divergence guard only.

## Rollback pin (recorded at wave open)

Image SHA `4bebb622` (all three services) · build_ids: Abhisek `b97b6eb0-0166-4ed6-ad94-9af9423b9e65`, Abhinandan `3a3682db-5434-4eca-8148-2c706c80380d`.

## Operational notes for future waves

- The Cloud SQL Auth Proxy in this environment drops connections under sustained
  load — bounded-retry (matching `rebuild_ga_sensitive_ga_strength.py`'s established
  pattern) should be the default for any rebuild script, not an afterthought.
- A session interruption mid-rebuild can leave `build_runs` rows orphaned in
  `'running'` state, silently exhausting `_MAX_CONCURRENT_RUNS` (6) and blocking all
  future runs with no visible error beyond a quiet "deferring run" log line. Worth a
  standing cleanup query in the re-entry procedure (protocol §6.2).
- `ganitaYogasV3Payload`-style JSON-path assumptions in the harness went stale the
  moment A-β's double-wrap fix changed the served shape — the harness needs the same
  scrutiny as product code when the surfaces it reads change underneath it.

## Next wave

`current_wave` advances to **D-1.5b** in `CLAUDECODE_BRIEF.md`. D-1.5b's own Binder
should re-verify all bindings fresh (protocol §2 step 1) rather than trusting this
report's snapshot, and should carry forward the `ka_vighnakara` FK defect and A7/#4
PARK items as open agenda.

---
*Closed 2026-07-15. Conductor: this session. All receipts, verifier transcripts, and
commit SHAs cited above are independently reproducible from `STATE_D-1.5a.md`'s
commit history on `main`.*
