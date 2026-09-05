---
artifact: L4_W6_CLOSE_REPORT_v1_0.md
canonical_id: NIRMANA_V21_L4_W6_CLOSE_REPORT
version: "1.0-DRAFT"
status: SCAFFOLD — W4/W5/W6 have not run; this is C8.5 productive-wait prep, not a submitted
  capsule. Sections below are filled from W1–W3's actual, verified work; the W4/W5/W6-specific
  sections (build results, capsule refs, freeze event) are placeholders pending the E-gate
  opening for `ph_nimitta` (currently 37/46 ancestors unfrozen).
produced_on: 2026-09-06 (drafted mid-campaign; will be finalized and re-dated at actual W6)
owner: L4 session (this file is mine alone — charter C5; not Conductor-owned)
---

# L4 — Phala — W6 Close Report (DRAFT SCAFFOLD)

Per `NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md` §4: *"the close report is the whole W6 ceremony"*
(standing default, no additional native requirement recorded). This document is drafted now,
ahead of W4/W5/W6, per the founding session prompt's C8.5 guidance for the smallest layer:
*"pre-write W5 verification scripts... draft close-report scaffolding... so held W3 items land
within hours of their capability unlocking."* Everything below reflects **verified, shipped**
work as of this draft; nothing is asserted ahead of evidence.

## 1. Assets and routes taken

All 9 `ph_*` assets route **`changed`** (W2 DECIDE, `L4_W2_DECIDE_v1_0.md`, PR #1735 merged).
No `rebuild_only`, no `verified_reuse`, no `probe`/`producer_covered`/`static`/`empty`/`retired`.
Every asset carried at least one MUST-tier correctness finding at W1, so a rebuild of the code
as it stood at W1 would have faithfully reproduced the defect (D-L4-11) — routing the cleanest
asset `rebuild_only` to look cheaper was explicitly declined.

| asset_id | W2 route | W3 MUST findings closed | remaining |
|---|---|---|---|
| `ph_nimitta` | changed | M-31 (deterministic `anchor_id`, D-CND-04) + 2 favourable-defaults (§N.7 item 6) | 5 pre-existing MUSTs from W1 not yet re-triaged post-fix; canary, awaits E-gate |
| `ph_muhurta` | changed | verdict-can-only-read-`mediocre` (JL-016 honest null) | `rows_written` over-report (collision-count) — not yet picked up |
| `ph_pratikara` | changed | F-3.4 (degenerate anchor), F-3/F-4/F-5 (hard-floor citation fabrication), F-6-partial (`source_id`) — 4 of 5 real MUSTs | F-2 (rerun after fix; blocked on E-gate, not a code item) |
| `ph_rectification` | changed | F3 (`load_bearing` on a non-discriminating fit) — 1 of 1 MUST | none (traced to root: current scoring method structurally cannot discriminate; K-6/later scope for the ranking method itself) |
| `ph_sankrama` | changed | both MUSTs (stale domain map destroying 250 rows; fabricated `trajectory`) — shipped earlier this session, #1788 | none |
| `ph_sodhana` | changed | F-10 (severity-inverting sort, #1783), F-14 (LEAKAGE-FIREWALL blind spot), F-13 (ceiling-inputs degeneracy detector), F-12 (`ayanamsha_robustness` falsy-zero coercion, #1870) | none — first L4 asset to reach zero open findings |
| `ph_suddha_sodhana` | changed | F-16 (silent classify-clean on read failure) | C12 registry-contract NULLs (closed via #1761, all nine assets) |
| `ph_pramana` | changed | F2 (domain vocabulary mismatch; `detector_unavailable` disposition added, migration 684) | none |
| `ph_phaladesa` | changed | F-4.2 (headline anchor ignoring purification verdict) | **F1 (zero MCP consumers) — deferred, see §5** |

## 2. Findings triage ledger (consolidated)

**MUST (correctness, gates the capsule) — shipped this session:**

| PR | Asset | Finding | Verified impact |
|---|---|---|---|
| #1754/#1799 | `ph_nimitta` | M-31: `phala_anchors.anchor_id` non-deterministic (D-CND-04) | 191 anchors remapped, 4,980 child refs, 0 dangling; trigger live in production |
| #1791 | `ph_muhurta` | verdict structurally pinned at `mediocre` | 0/134→honest-null when Moon strength unmeasured (placeholder source) |
| #1783 | `ph_sodhana`, `ph_pratikara` | severity-inverting sorts | canonical top-50 anchor page: 0→3 of 3 major anomalies now surfaced first |
| #1788 | `ph_sankrama` | stale domain map + fabricated `trajectory` | +250 rows recovered (canonical chart), `trajectory` now honest `None` when ungrounded |
| #1808 | `ph_nimitta` | two favourable defaults asserted on no evidence | 1.75× posterior lift from nothing → 1.0×; discovery-sourced `direction` `elevated`→`mixed` (7 anchors) |
| #1831 | `ph_pratikara` | F-3.4: `linked_anchor_id` a single constant across 536 rows | 512/536 obstructions now honest `NULL` instead of one wrong anchor |
| #1834 | `ph_rectification` | F3: `load_bearing:true` on win_margin=0 | traced to structural root (scoring method design), not a data artifact |
| #1839 | `ph_phaladesa` | F-4.2: headline anchor ignores purification verdict | 4 of 6 previously-flagged domains now lead with a clean anchor |
| #1842 | `ph_pramana` | F2: domain vocabulary mismatch → `life_event_match` unreachable | root cause was reading the wrong DB column entirely (`domain` vs `category`); migration 684 |
| #1845 | `ph_sodhana` | F-14: LEAKAGE-FIREWALL NULL/empty blind spot | verified live-safe (100% of anchors already canonical) before shipping |
| #1849 | `ph_suddha_sodhana` | F-16: silent classify-clean on read failure | matched the `ph_pratikara` "bug pattern" fix (F-173) already in the codebase |
| #1854 | `ph_pratikara` | F-3/F-4/F-5: hard-floor citation fabrication | 100% of 1,277 rows were serving an invented citation; F-4 self-corrected once F-3 landed |
| #1870 | `ph_sodhana` | F-12: `ayanamsha_robustness=0` silently coerced to default 3 | asymmetric fix — `n_independent`'s clamp floor (1) already absorbed its zero case; robustness's floor (0) did not, so real zero-robustness measurements were masked |

**NOW (in-layer improvement, admitted by clear value):**

| PR | Asset | Finding |
|---|---|---|
| #1857 | `ph_sodhana` | F-13: added `detect_ceiling_inputs_degenerate`, a corruption class the existing detector structurally could not see |
| #1864 | `ph_pratikara` | F-6 (partial): propagated `classical_sources_jsonb.source_id`; the finding's other named claim (`estimated_time_minutes`/`phase_duration`) verified to have no real data behind it on any chart — correctly not attempted |

**NEVER/LATER (logged, closed):**

- `ph_pratikara` F-2 — the empty-programme rerun: code already fixed upstream (`5f097e738`);
  blocked purely on E-gate/dispatch, not a code item.

**Correction (this cycle, D-CND-16):** an earlier draft of this scaffold listed `ph_sodhana`
F-12 here as "left open as the smallest item in the layer" — stale as of PR #1870, which shipped
it two cycles ago. `_g_ladder_ceiling`'s `ayanamsha_robustness` clamp floor is 0 (not 1, like
`n_independent`'s), so `0 or 3` was silently substituting a more lenient default for a genuine
zero-robustness measurement — a real correctness fix, not the numerically-inert cosmetic tweak
the original NOW-tier grading assumed. Moved to the MUST-shipped table above (§1, §2); this
scaffold's own staleness is exactly the kind of drift these close-report updates exist to catch
before an actual W6 submission repeats it.

**Deferred, not started — the layer's one remaining genuine code item:**

- **F1 (`ph_phaladesa`) — zero MCP consumers for `query_domain_result` / `query_falsifiers`.**
  W1's own framing: *"the single highest-leverage W2 item in L4."* Investigated across three
  cycles; traced the exact root cause (both capabilities are fully defined and registered in the
  TS retrieval registry, but have no entry in `canonical_faces.json`, and — critically —
  `canonical_faces.test.ts` hard-asserts the canonical∪deprecated union equals exactly 145,
  meaning the canonical-face list is a **derived census of what is actually registered as an MCP
  tool**, not a place to declare new tools ahead of building them). The real first step is
  authoring a new `platform-mcp/src/tools/*.ts` handler (~300-400 lines, matching either the
  `callPlatformPrimitive` pattern or the direct-sidecar-HTTP pattern — two different conventions
  coexist in this codebase and the right one needs establishing) plus `server.ts` registration,
  *then* regenerating the derived census/projection files. Deliberately not attempted
  autonomously: this environment has no way to build/run the MCP server to verify a new tool
  actually works end-to-end, unlike every other fix this session (each verified via direct SQL
  + unit tests). Left as the layer's explicit backlog item for a session with that verification
  capability, or for native review before landing.

## 3. Pillar movement (per the five doctrines, plan §5 L4 mandate)

- **D-SYNTHESIS** (one agreement line + strongest śruti quote per verdict) — **HELD, unheld
  items unaddressed this session.** This item was declared HELD on L2's consensus/grounding
  capabilities landing (charter C6); no `## CAPABILITIES LANDED` announcement for the relevant
  L2 capability was observed on `origin/main`'s `L2_STATE.md` as of this draft. Not moved.
- **D-GROUNDING** — **moved substantially.** The hard-floor citation-fabrication fix (F-3/F-4/F-5,
  #1854) is the layer's largest single grounding-honesty correction: 100% of `phala_mitigation`
  rows previously served an invented classical source; now an honest `None` when nothing was
  actually prescribed, with the serving layer's own `assignEfficacyTier` self-correcting for
  free. `source_id` propagation (#1864) adds a genuine source-identifier field for the first
  time. `ph_muhurta`'s honest-null verdict (#1791) and `ph_rectification`'s discrimination gate
  (#1834) are the same pattern applied to different fields — never claim empirical grounding a
  detector cannot back.
- **D-SALIENCE** (`tail_watch` in outlooks) — **HELD** on L2's tail-capability landing (same
  charter C6 mechanism as D-SYNTHESIS above); not moved this session. Adjacent work did land:
  `ph_phaladesa`'s headline-anchor fix (#1839) and the severity-sort fixes (#1783) are both
  salience-correctness work in the same spirit (the densest/most-consequential row must not be
  the one a trim or a naive sort discards first) even though they predate the formal
  `tail_watch` capability.
- **Honest probability surfaces** — moved on every MUST fix this session by construction: each
  one replaced a fabricated or unearned value with either a genuine computation or an honest
  null (§N.7 item 6 is the single most-cited doctrine across this session's 15 PRs).
- **Prediction provenance hygiene (parked-P7 seam)** — **verified untouched**, as the mandate
  requires. #1739/#1771 (severed the hand-authored-anchor seed path, D-CND-08) is the one
  P7-adjacent action taken, and it was a Conductor-granted, ruling-scoped removal, not new P7
  construction.

## 4. Cost actuals (measured, not forecast)

See `L4_STATE.md` "Cost ledger" for the full per-lane breakdown. Summary: bootstrap + W1 fan-out
+ W2 DECIDE ≈ 2 hours wall-clock before any code landed. W3 IMPLEMENT: 15 PRs shipped as of this
draft (#1754/#1761/#1763/#1771/#1783/#1784/#1788/#1791/#1799/#1802/#1808/#1818(N/A—L2)/#1831/
#1834/#1839/#1842/#1845/#1849/#1854/#1857/#1864 — L4's own subset), each following the same
proven cycle: root-cause investigation → local verification (Python/TS unit tests + live
read-only SQL, never a live write outside a rolled-back transaction) → governance-gate
regeneration (writer digest + analysis-layer pin) → PR → auto-merge arm. No W4/W5 cost data
exists yet (E-gate not open for any L4 asset — `ph_nimitta` at 37/46 unfrozen ancestors as of
this draft).

## 5. Backlog handed forward

1. **F1** (§2 above) — the layer's one remaining code item, explicitly scoped and explicitly
   not attempted autonomously; needs either a session with MCP-server verification capability
   or native review before landing.
2. **`ph_sodhana` F-12** — NOW-tier, smallest item in the layer; narration honesty +
   falsy-zero coercion in `_g_ladder_ceiling`, no live behavioral impact (the `max(...,1)` clamp
   already floors the numeric result identically either way) but a real §N.7 item 1/6 instance.
3. **D-SYNTHESIS / D-SALIENCE HELD items** — waiting on L2's consensus/grounding/tail
   capabilities; polling `L2_STATE.md`'s `## CAPABILITIES LANDED` section each cycle per charter
   C6. Not L4's to unblock.
4. **`ph_pratikara` F-2 rerun** and the layer's whole W4 EXECUTE wave — blocked on the E-gate;
   `ph_nimitta` is the derived canary (D-L4-01) and will open the layer's build wave once its
   46-ancestor closure completes campaign-wide.
5. **Cross-layer handoffs already filed** (not re-listed here in full; see `L4_STATE.md` §"Handed
   across to other sessions") — L2's `bo_laksana` non-deterministic `signal_id`, L2's
   `bodha_contradictions` orphan-registry gap, L3's `kala_convergence`/`kala_bhavishya`
   `bigserial` identity churn (the same D-CND-04 class L4 already fixed for its own anchors).

---

*This scaffold will be revised in place (not superseded) as W4/W5/W6 actually run — per
`ONGOING_HYGIENE_POLICIES_v1_0.md`'s archival-retain-in-place discipline, the version number
advances (1.0-DRAFT → 1.0) rather than a new file being created.*
