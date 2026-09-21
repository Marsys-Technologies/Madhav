---
artifact: KALA_ENVIRONMENT_READINESS_AUDIT
version: "1.1"
changelog:
  - "1.1 (2026-09-22): addendum C-1/C-2 — F2 re-scoped to the 48 upstream ancestors (7 frozen under t3, 41 superseded-only, 0 never); server_reconstructed corrected as the verifier-certified source kind. Body unchanged."
  - "1.0 (2026-09-22): first issue (audit cycles 7-8)."
status: CURRENT
date: 2026-09-22
canonical_id: KALA_ENVIRONMENT_READINESS_AUDIT
scope: >
  PROMPT_0_ENVIRONMENT_AND_ARCHITECTURE_AUDIT.md §3 (findings F1-F8) + §4 (domains A-J) —
  deliverable #5 of the KĀLA READINESS AUDIT. This document is a mechanical compilation of
  cycles 1-7's per-finding and per-domain evidence packets under
  `l3_autonomous/audit/_work/`, plus material from the cycle-6-promoted deliverables
  `KALA_EXECUTION_DESIGN_v1_0.md`, `KALA_CAMPAIGN_RUNBOOK_v1_0.md`, and
  `_work/DATA_LOSS_DIAGNOSIS.md`. It synthesizes and cross-references; it does not re-adjudicate
  any domain's READY/NOT READY/NEEDS DECISION verdict — those are carried forward from the
  source packets verbatim. One correction is applied to Domain F's reproducing commands (see
  §Domain F addendum), supplied by the cycle-7 conductor commissioning this compilation. Cycle 8
  is the one exception to "does not re-adjudicate": decision-list item 18 explicitly required
  re-running `capsule_audit.sql` under its now-fixed scoping before Domain A's verdict could be
  cited as current, so cycle 8 did exactly that live and updated Domain A's verdict + item 1 + item
  18 in place (see the Domain A addendum and the conductor spot-verification log's cycle-8 entry).
produced_by: L3 Kāla readiness audit (autonomous, Claude Code), read-only compilation subagent, cycle 7
inputs_cited: >
  _work/F2.md, F3.md, F4.md, F5.md, F6.md, F7.md, F8.md (F1 has no _work file — resolved via
  PR #2706, cited from KALA_CAMPAIGN_RUNBOOK_v1_0.md §1); _work/DOMAIN_A.md through DOMAIN_J.md;
  KALA_DAG_RECONCILIATION_v1_0.md (F3 promoted); KALA_EXECUTION_DESIGN_v1_0.md;
  KALA_CAMPAIGN_RUNBOOK_v1_0.md; _work/DATA_LOSS_DIAGNOSIS.md; the governing prompt
  `discussion_prompts/PROMPT_0_ENVIRONMENT_AND_ARCHITECTURE_AUDIT.md`.
---

# KĀLA ENVIRONMENT READINESS AUDIT — Findings F1-F8 and Domains A-J

**Read this document as a compiled ledger, not a fresh investigation.** Every finding/domain
section below cites its source packet; the exact reproducing commands, table names, line numbers
and confidence caveats are carried forward from that packet, not re-derived here. Where a source
packet flagged something as `COULD NOT VERIFY`, that flag is preserved, not resolved. This
document's compilation sections (F1-F8, A-J) do not themselves issue an overall GO/NO-GO — that
judgment is rendered separately, by a different (opus-tier) agent over the full corpus, in the
"Readiness verdict and native decision list" section appended at the end of this document.

---

## Summary table

| ID | Item | Verdict/status | Severity | Owner | One-line reason |
|---|---|---|---|---|---|
| F1 | `egate.sql` admits superseded evidence | **RESOLVED** (PR #2706, merged, confirmed on this branch) | CRITICAL (was) | nirmana tooling owner | `definition_revision` filter added; sibling sweep confirms `capsule_audit.sql` fixed same PR, `nrec`/`l1_integrity_check_dry_run.sql` never had the defect |
| F2 | t3 inheritance question | **OPEN — BLOCKING, NATIVE DECISION** | BLOCKING | native | Under t3, 0 L3 events exist for any asset; three tiers (12 `asset_frozen`/7 mid-pipeline/3 zero-evidence) need a native ruling on Option A/B/C1-C3 |
| F3 | DAG four-way (five-way) reconciliation disagreement | **RECONCILED** (documentation/identity defects found, no live build defect) | MEDIUM (worst: `ka_gochara` identity reuse in stale MIG345) | DAG/registry owner | SEED-TS/LIVE/FROZEN agree on all 23 identities; MIG345 is stale and covers only 12; `ka_muhurta_seva`/`ka_vighnakara` seed-vs-live divergences confirmed deliberate-but-undetectable by `dag_edge_guard.py` |
| F4 | `data_plane_builder` privilege coverage | **OPEN — confirmed build-blocking** | CRITICAL | data-plane grants owner | `ka_moorti_nirnaya` and `ka_kshetra` (stage3) hard-fail today on unguarded reads of `bg_transit_moorti`/`phala_rectification`; `ka_bhavishya_lekha` fails on rebuild only |
| F5 | Consumer-path divergence, all 23 identities | **OPEN — 3 confirmed real gaps** | MEDIUM-HIGH | L3 writer/consumer owners | `call_ephemeris_at_t` and `call_dasha_eligibility` confirmed divergent (as suspected); plus 2 new NOT-FOUND findings (`ka_tulana`, `ka_dasha_kala` — consumer reads a different asset's/layer's table) |
| F6 | Builder-image deployment lag | **READY, conditionally** | LOW (as measured) | deploy/release owner | Builder/MCP/sidecar 5 commits behind `main`, but none touch L3 writer paths; the one substantively critical commit (migration 1070 grants fix) already applied in prod independent of image staleness |
| F7 | Physical data census (not a clean slate) | **OPEN — informational, feeds F2/rebuild-order design** | MEDIUM | data-plane / L3 conductor | 9 of 37 `kala_*` tables are 0 rows for canonical chart despite being non-empty globally; `kala_field` (not `kala_field_snapshots`) is the real 8.57M-row table; 79/50,678 MSR-ref mismatches in `kala_activation_predicates` |
| F8 | PR #2695 (dispatcher digest path + ayanamsha default) unmerged | **OPEN — unsafe to dispatch unpatched** | HIGH | L3 / Pūrṇa baseline owner | Both defects confirmed live on `main`; PR is textually mergeable but blocked by one Pūrṇa-owned CI check (`Unit Tests`, `BEYOND_ACARYA_ACCEPTANCE_v4→v5.json` / golden-stream baseline divergence), unrelated to PR's own content |
| A | Campaign evidence integrity | **NOT READY** | HIGH | nirmana tooling owner | `capsule_audit.sql` §1/§3 share F1's exact defect class (no `definition_revision` scoping); 111 `asset_frozen` events across 98 "frozen" assets in current manifest — cannot distinguish "verified under t3" from "verified ever" |
| B | Acceptance machinery | **READY** (one open, non-blocking verification item) | — | — | HTTP route + DB trigger fail closed on every checked branch; `nrec` hardcodes `--include-email`; live IAM grant state not independently re-verified (flagged, not a defect) |
| C | Orchestrator and build path | **READY** | — | — | 141/141 unit tests + live disposable-Postgres proof of advisory-lock mutual exclusion; SATYA-DĪPA no-op-completion fix verified in code; one vestigial dead-code note (`service_ok` never written) |
| D | Generation / W1 substrate | **NEEDS DECISION** | — | native / data-plane architecture owner | 1035/1036 substrate is real and correctly gated but scoped to L1/L2 only (self-declared), zero generations ever opened for either layer, and no L3 equivalent exists — unclear if L3 needs to adopt it |
| E | Release and delivery | **READY** | — | — | Deploy-gate reads live deployed SHA (not a stale marker); `PIPELINE_PATTERN` covers `ga_writers/`; `deployment-outcome` gate is a real tested detector; merge queue ruleset confirmed `enforcement: active` |
| F | Consumer surfaces | **NOT READY** | HIGH | L3 consumer-surface owner | `kala_timeline.ts`/`kala_timeline` table fully DARK (never registered, not whitelisted, no writer) while a second file (`kala_temporal.ts`) claims the same asset id and serves it via a different table; only 5/11 U-items have both a live path and verified behavior — see addendum below for a repro-command correction |
| G | Cross-campaign safety | **NEEDS DECISION** | MEDIUM | native / campaign coordination owner | No blocking safety defect found, but 6 stale `ACTIVE`-labeled Pūrṇa lease rows create a real misread risk, and the `L3-REQ`/`PA-REQ` interlock + migration-range partition have no CI enforcement, only convention |
| H | Hub and invalidation hazards | **NEEDS DECISION** | MEDIUM | campaign owner / DAG registry owner | Code-identity detection (CI digest check + dispatch-time skew guard) is real and solid; no automated bridge exists from "hub code changed" to "these sibling `ka_*` writers' DB rows are now stale" — `ka_gochara`/`ka_sangam` are triple-hub-coupled |
| I | Source inventory (unmerged branches) | **No formal verdict stated by source packet** (see note) | — | — | "~113" branch claim off by ~9.4x (actual 1059 total, 137 L3-naming-matched); of 15 sampled branches, 14 DELIVERED + 1 STALE, 0 GENUINELY_UNDELIVERED — content genuinely absorbed via PR #2607 and smaller PRs, not lost |
| J | Session and tooling | **NOT READY** | MEDIUM-HIGH | campaign tooling / governance owner | Stream worktrees + credential routes READY; transcript-persistence hazard, permissions (no technical enforcement, only `dangerouslySkipPermissions: true`), and backup/restore (PITR unexecuted for `kala_*` tables) all NOT READY |

---

# Part 1 — Findings F1-F8

## F1 — `egate.sql` admits superseded evidence (CRITICAL · was OPEN, now RESOLVED)

**What was checked:** whether `platform/scripts/nirmana/egate.sql`'s `frozen`/`route` CTEs filter
`nirmana_elevation_campaign_events` by `definition_revision`, and whether the same defect class
appears in `capsule_audit.sql`, `l1_integrity_check_dry_run.sql`, `nrec`, or any dispatcher gate
read.

**Reproducing commands (cited from `KALA_CAMPAIGN_RUNBOOK_v1_0.md` §1, cycle 6, independently
re-run by the cycle-6 conductor):**
```
$ git log --oneline -- platform/scripts/nirmana/egate.sql
9b3c3b219 fix(nirmana): scope egate.sql and capsule_audit.sql to the frozen definition_revision (F1) (#2706)
45f06e68b feat(nirmana): shared read-only E-gate batch-eligibility tool (charter C2/C10) (#1722)

$ grep -c definition_revision platform/scripts/nirmana/egate.sql
4
```
`9b3c3b219` is confirmed an ancestor of this branch's HEAD (`008c49e80`).

**Sibling sweep result:**

| Sibling | Same defect class? | Evidence |
|---|---|---|
| `capsule_audit.sql` | No — already fixed, same PR #2706 | Every read of the events table (lines 34, 85, 107) is paired with `AND definition_revision = (SELECT definition_revision FROM frozen_def)`; in-file comment at line 29 states "F1-class fix" explicitly |
| `l1_integrity_check_dry_run.sql` | N/A — never reads the events table | `grep -n "nirmana_elevation_campaign_events\|definition_revision"` → zero matches |
| `nrec` | N/A — never reads the events table | Same grep → zero matches; it is a submission-side CLI, not an eligibility reader |
| dispatcher gate reads | Confirmed same two files above; no third reader | `grep -rln "nirmana_elevation_campaign_events" platform/scripts/nirmana/ platform/pipeline` → exactly `egate.sql` + `capsule_audit.sql` |

**Result / current status:** **RESOLVED.** Both files that ever read the events table for
eligibility are fixed and merged into this branch. `nrec` and `l1_integrity_check_dry_run.sql`
never had the defect. **Note:** the same defect class had re-appeared, independently, inside
`capsule_audit.sql` §1/§3's *own aggregation logic* (not the query this PR fixed) — see **Domain A**
below, which found this as a NOT READY finding distinct from the PR #2706 fix, then (cycle 8)
independently re-ran the now-fixed instrument live and confirmed it is genuinely scoped —
**READY** — while surfacing a materially more severe true campaign-position reading underneath.

**Severity:** CRITICAL (as originally found). **Owner:** nirmana tooling owner (per charter C5).

---

## F2 — The t3 inheritance question (BLOCKING · NATIVE DECISION — OPEN)

**What was checked:** the definition-lineage schema (`nirmana_elevation_campaign_definitions`,
`nirmana_elevation_campaign_events`), whether any ancestor definition's evidence can be treated as
admissible under the current frozen definition `t3-2026-09-11-8b884eac`, and quantified cost/risk
per inheritance option.

**Reproducing commands (`_work/F2.md`):**
```sql
SELECT campaign_id, definition_revision, definition_status, created_at, superseded_at
FROM nirmana_evidence.nirmana_elevation_campaign_definitions ORDER BY created_at;
```
→ six revisions, single linear chain (`campaign_id='nirmana-elevation'`), no branching structure;
five superseded (`t0-2026-08-25`, `t0-2026-08-26`, `t0-2026-09-01`, `t1-2026-09-08`,
`t2-2026-09-10`), one frozen (`t3-2026-09-11-8b884eac`).

```sql
SELECT entity_id, string_agg(DISTINCT definition_revision, ',' ORDER BY definition_revision) revs,
       count(DISTINCT definition_revision) n_defs, count(*) n_events
FROM nirmana_evidence.nirmana_elevation_campaign_events
WHERE entity_type='asset' AND entity_id LIKE 'ka_%' GROUP BY entity_id ORDER BY entity_id;
```

**Result:** structural fact — `definition_status` records only current state, not history, so
"ancestor definitions frozen" is 0 for every asset by construction. The real differentiator is
**ancestor evidence depth**, which partitions the 22 active identities into three tiers:

- **12 assets** reached an ancestor `asset_frozen` event (`ka_dasha_kala, ka_gochara,
  ka_gochara_resonance, ka_graha_sancara, ka_kota_chakra, ka_moorti_nirnaya, ka_muhurta_seva,
  ka_sudarshana_varsha, ka_tithi_pravesha, ka_tulana, ka_vedha_gochara, ka_yojaka`) — matches
  CLAUDE.md §E's historical "12/12 buildable" original close set exactly.
- **7 assets** have mid-pipeline evidence only, never `asset_frozen` (`ka_avadhi,
  ka_bhavishya_lekha, ka_jivana_parva, ka_kala_darshana, ka_kshetra, ka_sangam, ka_taranga`).
- **3 assets** have zero campaign evidence in any generation (`ka_gochara_v`, `ka_kalasutra`,
  `ka_vighnakara`) — the assets added when the roster expanded 12→22.

Under t3 itself: **zero L3 events of any type exist for any asset** — essentially none can satisfy
what the audit charter calls "C2.1" (confirmed to be F2's own ancestor-freeze condition, not a
separate documented criterion — no standalone "C2.1" artifact was found).

**Options presented (F2 does not choose — native decision required):**

| Option | Summary | Cost | Risk |
|---|---|---|---|
| A — re-freeze every ancestor under t3 | Full pipeline re-run for all 22, tiered by current evidence depth | Highest event-count cost; ~30% of L3 ancestor evidence is `source_kind=server_reconstructed` (not a live build receipt) — a defensible re-freeze needs an actual re-run for that fraction | Lowest evidentiary risk (freshest evidence) |
| B — native ruling naming admissible ancestor evidence, no re-run | Governance action only, for the 12 `asset_frozen` assets | Near-zero compute cost | Staleness risk (12 events are 11-17+ days old at t3 freeze, 11 further days stale now); does not help the other 10 assets at all |
| C1 — tiered: inherit the 12, run A in full for the other 10 | Schema-supported middle ground | Option A's cost for 10 assets only | Option B's staleness risk, scoped to the strongest-evidence tier |
| C2 — re-verify (not rebuild) the 12 | Lightweight `integrity_verified`-equivalent check per asset | Middle cost | Contingent on an unverified assumption (does a lightweight verifier exist separately from the full build path? — COULD NOT VERIFY) |
| C3 — binary scope: only the 12 inherit, the other 10 earn from scratch, no selective admissibility | Removes Option B's ambiguity risk | Same as C1 | Same as C1 |

**Load-bearing caveat applying to every option:** none of A/B/C1-C3 touch F13's `consumed →
effect_traceable → served → value_evaluated` rungs — `CONSUMER_INTEGRATED`/`VALUE_EVALUATED` have
**zero admissible event types** in the current schema (independently confirmed by
`KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md`/T3). Whichever option the native picks can only move an
asset to `DATA_ACCEPTED` at best.

**Status:** **OPEN — BLOCKING, NATIVE DECISION.** Per the audit charter and `KALA_EXECUTION_DESIGN_v1_0.md`
§5, this is the single largest velocity lever in the campaign and should be first in the native's
decision queue.

**Severity:** BLOCKING. **Owner:** native.

---

## F3 — Three sources disagree on the DAG (RECONCILED — see `KALA_DAG_RECONCILIATION_v1_0.md`)

**What was checked:** a four-way (actually five-way) reconciliation of `depends_on` across
MIG345 (stale migration), SEED-TS (`asset_registry_seed.ts`), LIVE (`asset_registry` table),
FROZEN (`build_runs.plan_manifest` snapshots), and CODE (writer import/read grep), for all 23
identities.

**Reproducing commands (`_work/F3.md` §0-1):**
```
find platform -iname '*asset_registry*' -path '*migrat*'
grep -n "'ka_" platform/scripts/seed/asset_registry_seed.ts
source /Users/Dev/madhav-l3/dbenv.sh; psql -Atq -F'|' -c "SELECT asset_id, depends_on, ... FROM asset_registry WHERE asset_id LIKE 'ka_%' ORDER BY asset_id"
grep -rn "frozen.*manifest" platform/python-sidecar/pipeline   # → runner.py's validate_frozen_run_manifest
grep -oP "from services\.\K[a-z0-9_]+"  # per writer file, to build the CODE column
```

**Result:** SEED-TS, LIVE, and CODE all independently enumerate the same 23 identities and agree
with each other in every case checked (23/23 rows, no CODE-vs-LIVE mismatch found). MIG345 only
ever covered the original 12 and was never re-run/extended.

**Re-verification of the 4 previously-known discrepancies:**
- `ka_muhurta_seva` (seed 1 vs live 0): **CONFIRMED, deliberate.** Migration 676 corrected LIVE
  after verifying the writer touches no producer table; migration's own text says re-syncing
  SEED-TS is a separate, deliberately-skipped question.
- `ka_vighnakara` (seed 4 vs live 5): **CONFIRMED, understated.** Migration 730 didn't just add
  one edge — it removed a fictional `ka_gochara` edge and added two real, different ones
  (`bg_dignity_reference`, `ka_yojaka`). SEED-TS and LIVE share only 3 of their combined 4/5
  members.
- `ka_sangam` (seed "0" vs live 10): **NOT SUPPORTED BY ANY REAL SOURCE.** MIG345=4, SEED-TS=10
  (matches LIVE). The literal "0" traces to `dag_edge_guard.py`'s synthetic, DB-free CI self-test
  fixture — its own docstring says it "proves NOTHING about the live registry." Corrected finding:
  MIG345=4 vs LIVE=10, both real.
- `ka_kalasutra` (seed "0" vs live 3): same class of error — MIG345=2, SEED-TS=3 (matches LIVE).
  No source anywhere shows 0 deps.

**Highest-severity individual finding:** `platform/migrations/563_utkarsha_w64_asset_rename.sql`
performed an **identity transplant**: it deleted the original `ka_gochara` (a global-scope,
on-demand service) and reassigned the `ka_gochara` asset_id to what was previously
`ka_gochara_v2_materialize` (a per_chart data writer, target_table `kala_gochara_windows`, wrong
scope/storage_type/deps entirely if read from MIG345). MIG345 predates 563 and was never
corrected — its `ON CONFLICT DO NOTHING` makes it inert against the live DB but a stale identity
trap for any future reader who treats MIG345 as valid history.

**Frozen-manifest coverage gap:** only 11 of 23 identities have ever been captured by a
`plan_manifest` snapshot; the other 12 — including `ka_sangam` ("THE VALUABLE CORE") — have never
been dispatched through a run whose manifest survived. The freeze-and-verify protection has never
actually fired for over half the L3 Kāla DAG.

**`dag_edge_guard.py` blind spot:** it has never run as a per-commit CI gate against the live DB
(its only DB-connected test is `skipif(not DATABASE_URL)`, and CI supplies no DB). It also
structurally cannot catch either confirmed discrepancy, because both are seed-file-vs-live drift,
not code-vs-live drift, and the guard never reads `asset_registry_seed.ts` or MIG345.

**Minor/soft finding:** `ka_avadhi.py:29` imports `ALL_DASHA_SYSTEMS` from `ka_dasha_kala` without
`ka_dasha_kala` appearing in any declared `depends_on` for `ka_avadhi`, in any source — invisible
to `dag_edge_guard.py` by construction (Python import ≠ table read; `ka_dasha_kala` has no
`target_table`).

**Status: RECONCILED as a documentation/live-registry problem** (SEED-TS/LIVE/CODE agree and are
correct today); **open governance-hygiene risk** that nothing stops the seed layer (MIG345, or a
future TS-seed-only bootstrap) from silently resurrecting stale/fictional edges, since
`dag_edge_guard` only ever inspects whatever ends up live.

**Severity:** MEDIUM (documentation/identity-integrity risk; not a currently-live build defect).
**Owner:** DAG/asset-registry owner.

---

## F4 — Builder privilege coverage is partial (CRITICAL — OPEN, confirmed build-blocking)

**What was checked:** re-measured `data_plane_builder`'s actual grants (via `has_table_privilege`,
tested as the role itself, not inferred) across all 431 `public`-schema relations, then built the
full Python import closure of all 22 active `ka_*` writers and cross-referenced privilege coverage
against every table the closure touches.

**Reproducing commands (`_work/F4.md` §1, §5):**
```sql
-- via source /Users/Dev/madhav-l3/dbenv_builder.sh (confirmed current_user = data_plane_builder)
SELECT prefix, count(*) total,
  count(*) FILTER (WHERE has_table_privilege('data_plane_builder','public.'||table_name,'SELECT')) sel
FROM (SELECT c.relname table_name, CASE WHEN c.relname LIKE 'kala\_%' THEN 'kala_' ... END prefix
      FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
      WHERE n.nspname='public' AND c.relkind IN ('r','p','v','m')) rels
GROUP BY prefix;
```

**Result:** `kala_* 39/41`, `bodha_* 28/36`, `chart_* 4/15`, `mimamsa_* 0/37`, `phala_* 0/20` all
match the cited charter figures exactly. **Correction to the charter's "258/431 inaccessible"
headline:** the exact re-measured count is **253/431 inaccessible** (drifted by 5, improved, since
whatever snapshot produced "258" — same direction, corrected number).

The 2 inaccessible `kala_*` relations are one-off snapshot/archive tables
(`kala_gochara_windows__ssv_20260728c`, `kala_gochara_windows_archive_20260805`) — no active
writer touches either; not a build risk. The 11 inaccessible `chart_*` relations are all
consent/deletion/panchanga-cache tables outside the L3 import closure — not L3's problem.

**8 of 68 closure-touched tables are fully inaccessible.** Of these, three are correctly guarded
(named `SAVEPOINT` + classical fallback, or not actually queried yet). **Three are confirmed
build-blocking with zero exception handling:**

| Asset | Table | Where | Status |
|---|---|---|---|
| `ka_moorti_nirnaya` | `bg_transit_moorti` | `writer.py`, `_fetch_moorti_table`, called unconditionally from `run()` | **CONFIRMED HARD FAIL** — no try/except anywhere; a LIGHT writer with no substep boundary to isolate the failure |
| `ka_kshetra` | `phala_rectification` | `services/ka_kshetra/uncertainty.py:fetch_sigma_t_days`, called unconditionally from `stage3_clocks.py:1012` | **CONFIRMED HARD FAIL** — mandatory substep, no try/except |
| `ka_kshetra` | `bg_synthetic_cohort`/`bg_synthetic_cohort_md` | `cohort_client.py`, stage6 | **Looks handled, isn't** — has a `try/except` but no `SAVEPOINT`, so the transaction poisons and the *next* statement fails with a confusing, unrelated-looking error |
| `ka_bhavishya_lekha` | `phala_anchors` | `writers/ka_bhavishya_lekha.py:249-287` | **Safe on first build, fails on rebuild** — guard is `to_regclass()` (existence, not privilege); fires only when `existing_ids` is non-empty |

**Status: OPEN.** Migration 1070's restoration of core orchestrator privileges did not extend to
`bg_transit_moorti`, `phala_rectification`, `bg_synthetic_cohort`, or `bg_synthetic_cohort_md` —
all four need `SELECT` granted to `data_plane_builder` before `ka_moorti_nirnaya`/`ka_kshetra` are
build-safe. The `ka_kshetra` cohort-path savepoint gap is a real fix independent of the grant.

**Severity:** CRITICAL (two confirmed build-blocking assets today). **Owner:** data-plane
grants/privilege owner (non-L3 gaps — `mimamsa_*`, `phala_*` writ large, most of `chart_*` — are
reported to their owners, not L3's to fix).

---

## F5 — Divergent implementations at the consumer boundary (UNVERIFIED → confirmed + expanded)

**What was checked:** the two specifically-reported divergences (`call_ephemeris_at_t`,
`call_dasha_eligibility`), then traced all 23 identities' writer-to-consumer wiring.

**Reproducing commands (`_work/F5.md`):**
```
grep -n "ka_graha_sancara" platform/python-sidecar/routers/ephemeris.py
# → zero import/call hits, only a naming comment
```
`call_ephemeris_at_t`'s handler fetches the sidecar's own `/api/compute/ephemeris_at_t` route,
which does `import swisseph as swe` directly and explicitly states in-file it does this "rather
than a second swisseph integration" — deliberately not importing
`services/ka_graha_sancara/engine.py`. **Verdict: CONFIRMED, high confidence.**

`call_dasha_eligibility`'s handler runs a raw `SELECT ... FROM chart_dashas WHERE chart_id = $1
AND ayanamsha_id = $2 ...` — no `KaDashaKalaService` import anywhere. **Verdict: CONFIRMED, high
confidence.**

**Full 23-identity trace result:** 20/23 show same-code wiring (11 high-confidence table-name
matches, 9 medium/surface-level asset_id co-occurrence checks — table not independently
re-verified for all given budget). 1 retired (`ka_gochara_sweep`) confirmed correctly inert.

**3 real divergence/gap findings, none hypothetical:**
1. `ka_gochara` writer targets `kala_gochara_windows_v2`, but the live consumer surface
   (`register_gochara_windows.ts`'s `buildSourceCitation()`) reads and cites the un-suffixed
   `kala_gochara_windows`, labeling it as the current materializer's output — corroborates F3's
   table-identity finding from the serving side.
2. **`ka_tulana` — NOT-FOUND (new finding).** Its consumer wrapper's SQL selects from
   `kala_activation` — the table `ka_kalasutra` owns, not `ka_tulana`. `grep
   target_table\|INSERT INTO` on `ka_tulana/writer.py` found no hits. Genuinely unresolved:
   could not confirm whether this is an intentional co-writer design or a silent substitution.
3. **`ka_dasha_kala` — NOT-FOUND (new finding).** Its consumer wrapper reads L1 `chart_dashas`
   directly, not any `kala_*` table. Same open-gap class as #2.

**Reachability implication:** for `ka_tulana`/`ka_dasha_kala`, if their writers genuinely have no
consumer reading their own output, `CONSUMER_INTEGRATED` is not currently reachable under the
registered writer without either discovering an undiscovered real consumer or documenting the
neighbor-table read as an intentional shared design.

**Status: OPEN.** 3 confirmed divergence/gap findings across 23 identities.

**Severity:** MEDIUM-HIGH (affects D8/`CONSUMER_INTEGRATED` reachability for at least 2 assets,
plus a table-identity confusion for a third). **Owner:** respective writer/consumer-surface owners.

---

## F6 — Deployment lag (READY, conditionally)

**What was checked:** deployed SHA per surface (web, MCP, sidecar, builder/pipeline job) live from
Cloud Run, the commit delta behind `origin/main`, whether that delta touches any L3-relevant path,
the deploy-gate's path-detection logic, and whether the one substantively critical commit in the
delta had already taken effect independent of image staleness.

**Reproducing commands (`_work/F6.md` §1-5):**
```
git fetch origin && git rev-parse origin/main
gcloud run services describe amjis-web|amjis-mcp|amjis-sidecar --region=asia-south1 --format=json
gcloud run jobs describe brahma-build-pipeline-job --region=asia-south1 --format=json
git log 09d998940069e00a4f09df60a03c3d07d6536ecf..origin/main --oneline
git diff --name-only 09d99894..origin/main
gh run view 35500092042 --log   # deploy gate's own "Gate & detect changed paths" job output
gh run view 35491906460 --log   # migration-apply job log
```

**Result:** web is current (`20f4d02dc`, exactly `origin/main` HEAD). MCP, sidecar, and the
builder/pipeline image are all pinned to `09d998940` — **5 commits behind**. Diffing that delta's
7 changed files against the L3-relevant globs (`platform/**/ka_*`, `pipeline/**`,
`registry/layers/L3_kala/**`, `platform-mcp/src/tools/kala_views/**`, nirmana briefs) — **none
match**. All 5 commits are Pūrṇa Anveṣaṇa collection-evidence fixes plus one data-plane grants
migration.

**The one commit that mattered substantively:** `d9070900d` / migration
`1070_data_plane_builder_orchestrator_grants.sql` — its own message: "Every build run of every
asset, for any chart, currently fails" (the `data_plane_builder` role held zero grants on
orchestrator metadata tables after a 2026-09-18 ownership cutover). Confirmed independently applied
in production via a live deploy-run log (`Applied: 1070_...sql`, job `success`), behind a
fail-closed self-check (`RAISE EXCEPTION` if grants didn't take). Because this is a `GRANT` (DB
privilege change), it took effect the moment `migrate` ran — it does **not** require the builder
image to be redeployed.

**Deploy-gate confirmed self-correcting, not blind:** `PIPELINE_PATTERN` includes `.../pipeline/`
and `.../services/`, which cover all `ka_*` writer source. A change limited to L3 writer code
**would** trigger a pipeline rebuild — live confirmation from the actual deploy run:
`web=true sidecar=false mcp=false pipeline=false` — correct, since none of the 5 pending commits
touch those paths.

**Status: READY, conditionally.** The image staleness is real but the specific hazard (does the
pending delta touch anything the builder image executes?) is confirmed negative.

**What would flip this to NOT READY:** (a) a live `has_*_privilege` re-check against prod coming
back false despite the "success" log (blocked in that session — no DB proxy reachable, **COULD NOT
VERIFY**); (b) a future commit touching pipeline/services paths merging without a subsequent
deploy; (c) MCP/sidecar staleness mattering for some surface not covered by their own patterns
(not exhaustively checked).

**Severity:** LOW as measured (no live-blocking exposure found). **Owner:** deploy/release owner.

---

## F7 — Data is not a clean slate (physical census — OPEN, informational)

**What was checked:** per-table row census for the canonical chart across all 37 `kala_*` tables,
generation/build-identity distribution, and re-verification of four specific reported facts.

**Reproducing commands (`_work/F7.md`):**
```sql
SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'kala_%' ORDER BY 1;  -- → 37
SELECT count(*), min(<ts_col>), max(<ts_col>) FROM <table> WHERE chart_id='482012f1-710e-4a25-994a-93821f5871aa';
```

**Result — 4 specific facts re-verified:**
- `kala_activation_predicates` ≈ 50,678: **CONFIRMED exact.** MSR ref-resolution check found
  **79 of 50,678 (0.156%)** rows whose `signal_id` does not resolve against `bodha_msr_signals`
  for the same chart — a real, small, nonzero unresolved-reference population.
- `ka_kshetra`'s ~8.6M-row table: **CORRECTED-IDENTITY.** The table is `kala_field`
  (8,570,075 rows, single generation `v0_classical`), not `kala_field_snapshots` (which is 0 rows
  for canonical, 1 row total globally, belonging to a different chart).
- `kala_field_snapshots` reported 0 rows: **CONFIRMED for canonical**, with nuance — table is not
  globally empty (1 row total, chart `1c826d5a-…`).
- `ganita_dashas_get` placeholder claim: **COULD NOT VERIFY** (live API response string, not a DB
  row). Indirect signal: `chart_dashas` holds 483,870 rows for the canonical chart — rules out
  "table is empty" as the cause but does not confirm/refute the API-layer claim.

**Broader finding:** 9 of 37 `kala_*` tables (`kala_activation`, `kala_bhavishya`,
`kala_convergence`, `kala_darshana`, `kala_field_salience`,
`kala_gochara_windows__ssv_20260728c`, `kala_insights`, `kala_obstruction`,
`kala_timeline_spec`) are 0 rows for the canonical chart despite being non-empty globally — every
row belongs to a different chart (`1c826d5a-…` and, for 3 tables, `cb73cd3d-…`). This is the raw
data underlying **F2's t3-inheritance question and the CASCADE root cause diagnosed separately in
`DATA_LOSS_DIAGNOSIS.md`** (see cross-reference below).

**Cross-reference — root cause for `kala_activation`/`kala_convergence` = 0 rows, from
`DATA_LOSS_DIAGNOSIS.md` (cited here, not re-derived):** these tables were not deleted by a writer
bug or a manual purge. `platform/supabase/migrations/403_kala_signal_fk_cascade.sql` deliberately
added `ON DELETE CASCADE` from `kala_activation.signal_id`/`kala_convergence.signal_id` (and 3
other `kala_*` tables) to `bodha_msr_signals.signal_id`. Because L2's `bo_laksana`/
`bo_laksana_rerank` mints fresh `signal_id` UUIDs on every rebuild (CLAUDE.md §N.3), an L2 rebuild
that runs *after* an L3 build silently cascade-deletes the L3 rows that reference the old
signal_ids. For the canonical chart, `bo_laksana` rebuilt 2026-09-08 and `bo_laksana_rerank`
2026-09-11 — both after `ka_kalasutra` (2026-08-13) and `ka_sangam` (2026-08-13) last ran, with
100% signal-set turnover in between. Proven with a decisive join on a second chart
(`cb73cd3d-…`): 100% of surviving `kala_activation` rows resolve to the pre-rebuild MSR generation,
0% to the post-rebuild one. The migration's own comment assumed lockstep L3-after-L2 rebuilding
that "nothing actually enforces" — the `state='stale'` flag fires correctly but is purely
informational; nothing currently escalates "stale AND empty" as distinct from ordinary staleness.
Practical exposure: at minimum `ka_kalasutra`, `ka_sangam`, plus (per the migration, unverified for
data state) `kala_bhavishya`, `kala_darshana`, `kala_obstruction`.

**Status: OPEN.** Informational/diagnostic; feeds directly into F2 (an asset with 0 canonical-chart
rows despite a "successful" historical build cannot honestly claim `DATA_ACCEPTED`) and into the
execution design's rebuild-order sequencing requirement (`KALA_EXECUTION_DESIGN_v1_0.md` §3).

**Severity:** MEDIUM (the census itself); the CASCADE root cause it surfaces is a real,
reproducible, recurring hazard, not a one-off. **Owner:** data-plane / L3 conductor (rebuild
sequencing) and the migration-403 owner (CASCADE remediation, not actioned by this audit).

---

## F8 — PR #2695 open defect fixes not landed (OPEN — unsafe to dispatch unpatched)

**What was checked:** PR #2695's live state, what its failing CI check actually asserts, whether
both defects it fixes are still live on `main`, and whether `dispatch_frozen_rebuild.py` would
produce a false provenance receipt if run unpatched today.

**Reproducing commands (`_work/F8.md`):**
```
gh pr view 2695            # state OPEN, mergeable MERGEABLE, mergeStateStatus BLOCKED
gh run view 35492082231 --log-failed
```

**Result:** the sole blocking check is `Unit Tests` under `CI — Ganga Quality Gate`, failing on a
hash/receipt mismatch against `BEYOND_ACARYA_ACCEPTANCE_v{4,5}.json` and
`tests/pariprashna/route_ports/baseline/*` — both **Pūrṇa-owned** artifacts PR #2695 does not
touch and does not own.

**Both defects confirmed live, unpatched, on current `main`:**
1. `platform/scripts/dispatch_frozen_rebuild.py`'s `WRITER_DIGESTS_PATH` is hardcoded to
   `/Users/Dev/nirmana-s/l3/platform/src/generated/nirmana-writer-digests.json` — a
   developer-machine-absolute path outside the repo. Confirmed this stale file exists on this
   machine (mtime 2026-09-10) and diverges from the real repo-tracked file (every writer digest
   differs). PR #2695's fix resolves the path relative to the script's own location.
2. `call_dasha_eligibility` in `call_service_wrappers.ts` defaults `ayanamsha_id` to the literal
   `'lahiri'`, not the canonical `DEFAULT_AYANAMSHA` (`'lahiri_chitrapaksha'`) that the other 4
   wrappers in the same file already use — a caller omitting `ayanamsha_id` gets a
   non-string-matching default against the real `kala_*`/`bodha_*`/`phala_*` convention.

**§N.8 analysis:** dispatching `dispatch_frozen_rebuild.py` unpatched, on a machine where the
stale digest file happens to exist, would commit a provenance receipt asserting an
`expected_code_digest` that does not correspond to the code that actually ran — a genuine
earned-signal violation, not hypothetical.

**Status: OPEN — not currently safe to dispatch through `main` unpatched.** PR #2695's own fix is
correct and complete for both defects; it is blocked only by an unrelated, Pūrṇa-owned baseline
regeneration. Either that baseline lands (its own track) so `Unit Tests` goes green, or
native/governance grants an explicit scoped override to merge #2695 despite the one unrelated
failing check.

**Severity:** HIGH (a live dispatch today would produce a falsified provenance receipt; the
ayanamsha default bug silently mismatches production data conventions). **Owner:** L3 (both fixes)
/ Pūrṇa (blocking baseline).

---

# Part 2 — Domains A-J

## Domain A — Campaign evidence integrity: **READY** (re-run cycle 8; see addendum below — the instrument is now sound, but its correct output is a severe campaign-position finding)

**What was checked:** definition lineage integrity, `definition_superseded_mid_campaign` event
completeness, whether any evidence-integrity tool besides `egate.sql` admits stale evidence, and
whether `capsule_audit.sql` §1/§2 can genuinely fail.

**Reproducing commands (`_work/DOMAIN_A.md`):**
```sql
SELECT definition_revision, definition_status, created_at, superseded_at
FROM nirmana_evidence.nirmana_elevation_campaign_definitions;
grep -n "definition_revision" platform/scripts/nirmana/capsule_audit.sql   -- zero matches
```

**Result:** lineage itself is internally consistent (6 definitions, no gaps/overlaps in the
created_at/superseded_at chain), but the two earliest superseded definitions have **zero events**
traceable to them at all — a 6-day evidence-lineage gap, non-blocking but noted.

**The core finding — `capsule_audit.sql` shares F1's exact defect class, in a different query.**
Despite its own header claiming it exists "so the campaign's terminal claims are checked as they
are made" and that "a PASS requires a real absence of violations," `capsule_audit.sql` §1
(incomplete-evidence-chain check) and §3 (per-layer position) have **zero `definition_revision`
scoping** — they `GROUP BY entity_id` across the entire history of every superseded definition an
asset has ever passed through. Concretely: `asset_frozen` fired **111 times** across the table
while §3's own rollup reports **98 total frozen assets** in the current manifest — at least 13
entities were frozen more than once under more than one definition. Because §1/§3 never filter,
an asset frozen under `t3` today can have its acceptance booleans satisfied by events logged
against a superseded definition. Running it live: §1 = 0 rows (PASS), §2 = 0 crossings (PASS), §3
= L3 23 assets, 13 frozen, 7 routed-not-frozen, 3 unrouted. **The "0 rows" PASS is genuine evidence
of "no violation ever logged," not evidence that the current 98 frozen assets have a complete
`t3`-scoped chain** — the tool cannot currently distinguish the two claims.

§2 (identity-separation check) is less exposed — it is a per-event structural check, not a
cross-revision aggregation — and its PASS is more trustworthy.

**Original verdict (pre-fix, superseded below): NOT READY.** What would need to be true for READY:
§1 and §3 (ideally §2 too, for defense in depth) scoped to `WHERE definition_revision = (SELECT
definition_revision FROM nirmana_elevation_campaign_definitions WHERE definition_status='frozen')`,
and the "0 rows"/"98 frozen, complete" results re-verified under that scoping.

**Secondary, non-blocking finding:** the two earliest superseded definitions have no traceable
events at all — a footnote for whatever record closes this audit, not campaign-blocking.

**ADDENDUM (cycle 8, conductor, live re-run) — decision-list item 18 discharged.** All three
sections now carry the scoping this domain's original verdict required (confirmed by direct file
read: §1 line ~34, §2 line ~85, §3 line ~107, each joining `WHERE definition_revision = (SELECT
definition_revision FROM frozen_def)`). Ran the fixed instrument live, read-only, via
`psql -f platform/scripts/nirmana/capsule_audit.sql` (role `amjis_app`,
`default_transaction_read_only=on`):

```
§1 (incomplete evidence chain): 0 rows        -- PASS, now genuinely t3-scoped
§2 (identity separation): 11 rows, all 'ok'   -- PASS, no crossings, now t3-scoped too
§3 (per-layer position, t3-scoped):
 layer | assets | frozen | routed_not_frozen | unrouted | pct_frozen
 L0    |     40 |      0 |                 0 |       40 |        0.0
 L1    |     19 |      0 |                 0 |       19 |        0.0
 L2    |     22 |      8 |                 0 |       14 |       36.4
 L3    |     23 |      0 |                 0 |       23 |        0.0
 L4    |      9 |      0 |                 0 |        9 |        0.0
 L5    |     15 |      0 |                 0 |       15 |        0.0
       |    128 |      8 |                 0 |      120 |        6.3
```

**Instrument verdict: READY.** §1/§2/§3 are now genuinely scoped to the frozen definition and their
PASS/output is trustworthy evidence about `t3-2026-09-11-8b884eac` specifically, not about "ever,
under any definition." This closes decision-list item 18.

**But the correctly-scoped output is itself a severe, independent finding, not a clean bill of
health.** Under the old (buggy, unscoped) aggregation, §3 read L3 as "13 frozen, 7 routed-not-
frozen, 3 unrouted (56.5% frozen)" — a picture of real campaign progress. Under the now-correctly-
t3-scoped aggregation, **L3 shows 0 of 23 assets frozen, 0 routed-not-frozen, 23 unrouted (0.0%)**.
All 8 of the campaign's total `asset_frozen` events under `t3-2026-09-11-8b884eac` belong to L2;
none belong to L3. Every prior appearance of "13 frozen L3 assets" in this campaign's own
self-reporting was cross-definition contamination — evidence logged against `t0`/`t1`/`t2` being
misread as evidence for `t3`. This is independent corroboration, from a completely different
instrument and query shape, of F2's and the readiness query's own finding (decision-list item 1:
22/23 rows read `NOT_READY-BLOCKED-ANCESTORS`, 0 READY-shaped rows) — it is not a new defect on top
of F2, it is the same true position, reached a second way, which raises confidence that "0/22
genuinely accepted under `t3`" is the correct current headline, not an artifact of one query's
construction. Folded into decision-list item 1 as corroborating evidence, not a new numbered item.

---

## Domain B — Acceptance machinery: **READY** (one open, non-blocking verification item)

**What was checked:** `nrec` CLI, the HTTP route's `requiredPrincipalFor` split, the DB trigger
`nirmana_elevation_guard_server_reconstructed_insert`, and the credential-holder runbook.

**Reproducing commands (`_work/DOMAIN_B.md`):**
```sql
SELECT pg_get_functiondef(oid) FROM pg_proc WHERE proname = 'nirmana_elevation_guard_server_reconstructed_insert';
SELECT tgname, tgrelid::regclass, pg_get_triggerdef(oid) FROM pg_trigger WHERE tgfoid = '...'::regproc;
```

**Result:** `nrec` hardcodes `--include-email` unconditionally (cannot be omitted by a caller using
the sanctioned tool) and refuses `--as`/derived-identity mismatches before minting or sending
anything. The HTTP route (`route.ts`) fails closed on every branch checked: missing/malformed
auth → 401; bad token or non-allowlisted identity → 403; malformed body → 400; principal mismatch
→ 403 — never a silent pass-through. The DB trigger enforces role-gated writes with hard
`RAISE EXCEPTION`s and **stamps `writer_identity` from `session_user`**, not a self-reported field
— matching the §N.8 doctrine that the claim and the detector must be the same mechanism.

**Silent-403 hazard (the brief's named suspicion):** confirmed real as a **diagnosability** issue
(a caller who mints a token without `nrec` and omits `--include-email` gets a generic,
indistinguishable-from-other-causes 403), but confirmed **not a security defect** — the failure
mode is always "reject a legitimate caller," never "accept an illegitimate one." Downgraded from a
possible defect to a documented, mitigated footgun.

**Separation-of-duties residual (self-disclosed in code, not hidden):** the executor and verifier
GCP identities are both impersonable by the same human principal (the native) — the HTTP+DB
controls enforce "no single call wears both hats" but not "no single human can act as both across
two calls." The actual implementer≠certifier guarantee rests partly on procedural discipline
(fresh-context verification), not full access-control disjointness.

**Verdict: READY.** What would have flipped it: a silent-403 that granted access rather than
denied it (did not happen); a DB trigger that trusted a self-reported identity field (it doesn't —
`session_user`-stamped); live IAM grant state contradicting the documented design (not
independently re-verified — **the one open item**, a single `gcloud iam service-accounts
get-iam-policy` call per SA, skipped this pass per the brief's caution against unverified-fast
commands in a non-interactive context).

---

## Domain C — Orchestrator and build path: **READY**

**What was checked:** per-chart advisory lock, fleet cap, `build_runs`/`build_run_assets`/
`asset_throughput` lifecycle, `_verify_registry_still_matches_manifest`,
`_verify_sidecar_code_matches_manifest`, writer registration, substep plans — proved end-to-end on
a disposable local Postgres instance plus the project's real unit-test suite.

**Reproducing commands (`_work/DOMAIN_C.md`):**
```
# Disposable Postgres 15, mutual-exclusion proof:
psql -c "SELECT pg_try_advisory_lock(hashtext('482012f1-...')) AS session_a_got_lock; SELECT pg_sleep(4);" &
psql -c "SELECT pg_try_advisory_lock(hashtext('482012f1-...')) AS session_b_got_same_chart_lock;"  # → f
psql -c "SELECT pg_try_advisory_lock(hashtext('11111111-...')) AS session_c_got_other_chart_lock;" # → t
# (after A's connection closes) psql -c "... session_d_got_lock_after_a_released;"                  # → t

cd platform/python-sidecar && python3 -m pytest tests/test_orchestrator_substeps.py ... -v   # 105 passed
python3 -m pytest pipeline/orchestrator/tests/test_run_claim_and_global_lock.py ... -v        # 36 passed
python3 -c "from pipeline.orchestrator.writers import discover_all, list_writers; ..."        # 22 ka_* writers
```

**Result:** the advisory lock is a real Postgres session-level primitive (`f`/`t`/`t` exactly as
predicted: blocked on same chart, succeeded on different chart, succeeded after release). Fleet
cap defaults to 6 concurrent runs, enforced before the chart lock, self-excludes the retrying run's
own `run_id`. `build_runs` lifecycle (`planned → running → {completed|stopped|failed}`, `paused`
intermediate) confirmed live: 429 failed + 369 completed + 19 stopped, 0 running at audit time.
Both preflight verify functions (`_verify_registry_still_matches_manifest`,
`_verify_sidecar_code_matches_manifest`) are called unconditionally before any lock/writer runs,
and fail closed (`_terminalize_preflight_failure`, run marked `failed`, exit non-zero) on any
mismatch. Writer registration: live count = 22 `ka_*` writers registered (matches CLAUDE.md
exactly); `ka_gochara_sweep.py` exists on disk but does not register — confirmed retired.

**SATYA-DĪPA no-op-completion fix verified directly in code** (`asset_runner.py:1100-1186`): the
promotion-to-`lit` path re-invokes the writer's own `plan_substeps(ctx)` inside a savepoint and
only promotes if the plan agrees nothing remains — otherwise lands `'incomplete'`, which does not
satisfy the `state IN ('lit','service_ok')` dependency-satisfied check.

**Total: 141/141 unit tests passed, 0 failures, 0 skips** across both suite locations.

**One vestigial, non-blocking finding:** `'service_ok'` is checked in three read locations
(`runner.py:707`, `staleness.py:83,138`) but **never written anywhere** — every real service asset
actually reaches `'lit'` via the `zero_rows_is_complete` path instead (confirmed live:
`asset_throughput` state distribution has zero rows in any non-CHECK-constraint state). Harmless
today (a superset allowlist including an unused member, not a subset excluding a used one) but
dead code across 3 files worth a cleanup.

**Verdict: READY.** Scope explicitly limited to build-path mechanics — not a verdict on data
completeness (F7), DAG correctness (F3), or privilege coverage (F4).

---

## Domain D — Generation / W1 substrate: **NEEDS DECISION**

**What was checked:** what migrations 1035/1036 actually install, whether
`session_user = 'data_plane_builder'`/`data_plane_migrator` gating is genuinely enforced, real
head-table existence/row counts, first-ever-generation rollback semantics, and whether an
L3-specific generation-head table exists.

**Reproducing commands (`_work/DOMAIN_D.md`):**
```
grep -rln "session_user" --include="*.sql" platform/supabase/migrations/
SELECT tablename FROM pg_tables WHERE tablename LIKE '%generation_heads%';
SELECT 'l1', count(*) FROM public.l1_data_plane_generation_heads UNION ALL SELECT 'l2', count(*) FROM public.l2_data_plane_generation_heads;
SELECT tablename FROM pg_tables WHERE tablename LIKE '%l3%generation%' OR tablename LIKE '%kala%generation%';  -- empty
```

**Result:** 1035 (L1) and 1036 (L2) install a full exact-context, append-only, immutable
snapshot/replay/rollback substrate — not a simple counter-bump. The `session_user =
'data_plane_builder'` gate on open/capture/complete functions, and the separate
`data_plane_migrator` gate on rollback, are confirmed present verbatim at cited line numbers in
both migration files — real `SECURITY DEFINER` role checks, not decorative. **But both head tables
are live-empty**: `l1_data_plane_generation_heads` = 0, `l2_data_plane_generation_heads` = 0, and
all four generation-tracking tables checked = 0 — not one generation has ever been opened, let
alone completed, for any chart/asset in either layer on this environment.

**First-ever-generation rollback:** the head row is only inserted at full partition completion, so
a first-ever generation that aborts mid-build never creates a head row — `rollback_*` is literally
unusable in that exact scenario (`'asset % has no selected generation'`). Not dangerous from a
"wrong data served" standpoint (every consumer path filters on `status='complete'`, so partial
data is never served), but there is no explicit "abandon generation" function — the design
compensates via resumability, not rollback, and orphaned partial state (if abandoned rather than
resumed) is retained forever with no reclaim path found.

**No L3-specific generation-head table exists.** 1036's own header comment self-declares this is
intentional/current scope: "no L3 activation authority is introduced." A separate,
older, unrelated `*_gochara_generation*` mechanism exists (the retired `ka_gochara_sweep`'s own
bespoke transit-sweep versioning) — must not be conflated with an "L3 generation head."

**Verdict: NEEDS DECISION.** The gate is intact and no L3 table exists — neither of the two
failure conditions that would force a clean READY or clean NOT READY is present. What remains is
an honest "no evidence either way" gap: is this substrate dormant/unused scaffolding, or simply
not yet wired for L3's build activity? This audit cannot distinguish the two from schema + row
counts alone. **What would flip to READY:** live proof of at least one `status='complete'`
generation row for the canonical chart (L1 or L2). **What would flip to NOT READY:** a broken
role-gate, or a live L3 head table with rows disagreeing with this schema — neither found.

---

## Domain E — Release and delivery: **READY**

**What was checked:** deploy-gate path patterns, the `deployment-outcome` earned-signal job,
pipeline-image rebuild triggers, migration ranges, merge queue enforcement, and the
generated-artifact regeneration protocol.

**Reproducing commands (`_work/DOMAIN_E.md`):**
```
grep -n "PIPELINE_PATTERN=" .github/workflows/deploy.yml
gh api repos/Marsys-Technologies/Madhav/rulesets/20141220
ls platform/migrations/ | grep -E '^(10[7-9][0-9]|11[01][0-9])_'   -- empty
git log --oneline -8 -- platform/src/generated/
```

**Result:** the `changes` job computes each component's diff against its **live deployed SHA**
(read from Cloud Run itself), not a stale "last successful run" record — explicitly the fix for a
prior self-diff defect (#2169/#2172, 3.5h of silently-skipped rebuilds across 17 green runs). The
gate is fail-open (any resolution failure forces a rebuild, never a silent skip). `PIPELINE_PATTERN`
covers `ga_writers/`, `pipeline/`, `services/` — all L3 writer source paths — so any L3 writer edit
triggers an automatic pipeline rebuild, no `force_all_services` needed.

**`deployment-outcome` gate is a real tested detector, not a proxy:** its `required` map is built
from the **same** `changed.*` booleans the `changes` job emits (themselves grounded in production's
own diff), and a required-but-`skipped`/`failure` job triggers a hard exit. Unit-tested; a second
test asserts the job step literally invokes the real script. Campaign docs record it catching 4
real live failures.

**Migration ranges:** the "1033-1070 applied" framing checks out — `platform/migrations/` runs
1000→1042 then jumps to 1070 (1043-1069 is Pūrṇa's documented range, not files in this checkout);
nothing above 1070 exists yet; 1071-1119 is genuinely open. **Not independently verified:** whether
1043-1069 are truly applied in production (only 1070 has direct live-log confirmation via F6) —
flagged, not asserted.

**Merge queue:** the classic branch-protection API returns 404 (misleading if taken at face value —
this repo uses the newer rulesets system). `gh api .../rulesets` confirms one active-enforcement
ruleset (`enforcement: "active"`, `current_user_can_bypass: "never"`) with a real `merge_queue`
config (squash, `grouping_strategy: ALLGREEN`) — genuinely in effect, confirmed via the live API
object, not a markdown description.

**Generated-artifact regeneration:** two load-bearing generated artifacts
(`capability_estate_census.json`, `capability_knowledge.snapshot.json`) both have `:check` CI
variants and a confirmed track record of Pūrṇa PRs regenerating them, not hand-editing. No L3
(`ka_*`) commit has touched them yet in the checked log window — meaning any L3 writer that
changes catalog descriptors will need the same regeneration step before merge.

**Verdict: READY.** What would have flipped it: `PIPELINE_PATTERN` excluding `ga_writers/` (it
doesn't); the deployment-outcome gate using a hardcoded required-jobs list (it doesn't); the
migration range already partially claimed (it isn't); the ruleset showing `enforcement: disabled`
(it doesn't); taking the classic 404 at face value without checking rulesets (would have been a
false NOT-READY — avoided).

---

## Domain F — Consumer surfaces: **NOT READY**

**What was checked:** the MCP tool-surface inventory for L3 Kāla (registered tools, live/dark/
divergent classification per table), channel parity across Portal Paripraśna / managed MCP
`prashna_ask` / raw MCP, and testability of U01-U11.

**Reproducing commands and result summary (`_work/DOMAIN_F.md`, built on F5's trace):** 9
`kala_views` tools confirmed wired into the actual server bootstrap
(`registerAllKalaViews` imported and called in `registry_bridge.ts`). Most consumer files trace to
a live, same-code writer per F5.

**The confirmed DARK finding — `kala_timeline.ts` / `kala_timeline` table.** Three independent
confirmations were reported by the source packet: (1) `registerKalaTimeline` is never called from
`platform-mcp/src/server.ts` despite the file's own docstring claiming it is; (2)
`MCP_TO_RETRIEVAL_TOOL` has no `kala_timeline` entry, so the primitives-route whitelist would 400
the call even if it were registered; (3) the writer trees carry no writer targeting a
`kala_timeline` table. **Meanwhile a second file, `kala_temporal.ts`, claims the same asset id**
("KA-3-1 kala.timeline") and genuinely serves it — but via `ka_avadhi`/`query_dasha_dossier`, a
completely different table. Two non-reconciled implementations of the same declared asset: one
dead, one live under a different name.

### Addendum — correction to Domain F's reproducing commands for finding (3) above

`DOMAIN_F.md`'s claim that `grep -rln kala_timeline` over `pipeline/` and `services/` returns zero
hits is **imprecise**: those bare paths do not exist at the repo root (the actual trees are
`platform/python-sidecar/pipeline/` and `platform/python-sidecar/services/`). Independently
re-verified this cycle (2026-09-22, cycle 7 conductor) with the corrected prefix:

```
grep -rln kala_timeline platform/python-sidecar/pipeline/ platform/python-sidecar/services/
```

This **does** find 3 hits, not zero:
- `platform/python-sidecar/pipeline/brahma_pipeline.py` — a `counts["kala_timeline"] = n`
  bookkeeping line inside a `_l3_kala()` function that calls
  `brahmagyan.kala.timeline.seed(chart_id)`.
- Two files under `platform/python-sidecar/services/ka_kshetra/` (`stage8_spec.py`, `writer.py`) —
  but these target a **differently-named table, `kala_timeline_spec`** (not `kala_timeline`),
  which **is** live and written by the active `ka_kshetra` writer
  (`INSERT INTO kala_timeline_spec (...)` at `writer.py:1469`).

Further re-verification: `brahma_pipeline.py`'s `_l3_kala()` function (and the
`brahmagyan.kala.timeline` module it calls) is **never imported anywhere in the codebase** —
`grep -rln "from pipeline.brahma_pipeline\|from pipeline import brahma_pipeline\|import
brahma_pipeline" platform/python-sidecar/` returns zero hits. It is dead/orphaned legacy code that
predates the FROZEN per-writer orchestrator (`pipeline/__init__.py` itself says "Entry point:
brahma_pipeline (replaces deleted build_chart)" — i.e. it is itself a superseded entry point).

**Corrected conclusion:** Domain F's DARK verdict on the `kala_timeline` table **stands** (no LIVE
writer under the current orchestrator targets it) — but (a) the original reproducing command
needed the `platform/python-sidecar/` path prefix to actually reproduce, and (b) a
near-identically-named but **distinct** table, `kala_timeline_spec`, is live and actively written
by `ka_kshetra`. Future audits/campaign sessions must not conflate the two names.

**Process finding (governance-hygiene, not technical):** `DOMAIN_F.md` existed on disk since cycle
3 (~2026-09-22 01:33) but was never entered into `AUDIT_STATE.md`'s packet table in any of cycles
3-6 — an orphaned packet, structurally identical to cycle 4's orphaned Domain C, just never caught
until this compilation pass.

**Channel parity:** Portal Paripraśna and managed-MCP `prashna_ask` are architecturally identical
(confirmed: `prashna_ask_bridge.ts` explicitly states the real engine invocation lives on the
`platform` side; `platform-mcp` has no import path to it — both channels hit the exact same route
by construction). Raw MCP (e.g. `kala_windows_get`) is a **documented, intentional** bypass of the
planner/floor/NO-LEAKAGE layer (the RS-4 carve-out already recorded in CLAUDE.md §I) — same
underlying table reached, but without planner-level gating guarantees.

**U01-U11 testability:** only 5/11 (U01, U03, U05, U06, U04-with-caveat) have both a live code path
and enough in-code disclosure to trust behavior; U07 shows only a drill-pointer reference, not real
data fusion; U08 and U10 could not be traced at all within budget.

**Verdict: NOT READY.** Two concrete defects independent of F5's three: (1) the `kala_timeline`
dual-implementation gap; (2) combined with F5's three divergences, a raw-MCP caller today can
retrieve L3 data through at least 4 distinct paths where the served table does not match what
governance artifacts or the asset's own docstring claim. What could flip this: if
`registerKalaTimeline` is called from a bootstrap path not searched this pass (would soften but
not eliminate the finding); if U07/U08/U10's fusion logic exists outside the searched directories.

---

## Domain G — Cross-campaign safety: **NEEDS DECISION**

**What was checked:** Pūrṇa's territory/cadence, the lease protocol on
`origin/campaign-coordination`, the five shared-surface partition rules, the `L3-REQ`/`PA-REQ`
interlock, and whether Pūrṇa's live acceptance genuinely depends on L3 receipts.

**Reproducing commands (`_work/DOMAIN_G.md`):**
```
git fetch origin campaign-coordination:refs/remotes/origin/campaign-coordination
git show origin/campaign-coordination:00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md
grep -rn "L3-REQ\|PA-REQ" --include="*.md" .
```

**Result:** Pūrṇa owns a large, well-marked, disjoint surface (BEYOND_ACARYA_ACCEPTANCE
artifacts, `pariprashna/**`). Deploy/rebuild cadence is event-driven (path-gated CI), not a fixed
interval; the only time-based cadence found is a reporting convention ("at least daily" strategy
check), not mechanical scheduling.

**The lease protocol is optimistic-concurrency-by-git, not a real lock** — push-and-hope, with
non-fast-forward rejection as the only collision guard. **"ACTIVE unexpired" is not mechanically
checked**: the rule text requires the *next reader* to manually compare the `expiry (IST)` column
against wall-clock time. **This is empirically confirmed, not just inferred**: the live table
contains **at least six rows whose `status` still literally reads `ACTIVE`** despite being
hours-to-days expired and superseded on the same day (2026-09-19). Any tool/agent that greps for
the literal string `ACTIVE` without parsing expiry will misread these as currently-held leases.
**Currently held lease (as of last fetch):** the topmost row, `MADHAV-L3-KALA-W1-DISPATCH-20260920`,
is `RELEASED` (the dispatch failed structurally on `InsufficientPrivilege`, confirmed by direct
privilege introspection, no partial write). **No lease is currently ACTIVE by either campaign**
(confirmed by timestamp comparison, not string match).

**Shared surfaces:** five partition rules confirmed, with one concrete code-level bridge found:
`source_query_availability.ts` lines 3097-3100/3160-3162 contain live SQL joining
`build_run_assets`/`build_runs` filtered on `bra.asset_id = 'ka_bhavishya_lekha'` — Pūrṇa's own
served-availability logic directly reads L3's build/asset-state tables (read-only, confirmed no
write).

**`L3-REQ`/`PA-REQ` interlock:** a documentation/process convention, not mechanically enforced —
no CI check found that blocks a PR for a missing/ignored interlock entry. The migration-number
partition (1042-1069 Pūrṇa / 1070-1119 L3 / 1120+ cross-cutting) is the one interlock with real
mechanical teeth-equivalent (a numeric collision would be visible at migration-apply time), but no
CI guard enforcing the partition itself was found.

**Pūrṇa's live acceptance genuinely depends on L3 receipts — confirmed with file:line citation.**
The `build_observation` CTE cited above is the strongest evidence: Pūrṇa's served-availability
logic is structurally coupled to L3's build state. **Dependency direction: Pūrṇa depends on L3, not
the reverse.**

**Verdict: NEEDS DECISION.** No blocking safety defect found in the mechanism itself (the last
actual lease interaction was handled correctly per protocol). Two items need a native/PB-3
decision before L3 resumes production-touching work: (1) the stale `ACTIVE` rows are a live
misread risk — recommend always computing "most recent row by position → read expiry → compare to
wall-clock" rather than string-matching; (2) the interlock/migration-partition conventions have no
CI enforcement, relying entirely on both campaigns' conductors reading the same markdown file.

---

## Domain H — Hub and invalidation hazards: **NEEDS DECISION**

**What was checked:** the confirmed importer set (with file:line evidence) for 7 named shared
modules, what editing each hub invalidates, and whether the environment can actually *detect* a
hub edit as invalidating dependent writers' already-built data.

**Reproducing commands (`_work/DOMAIN_H.md`, per-hub grep pattern):**
```
grep -n "from pipeline.transit_search import" platform/python-sidecar/services/ka_gochara/service.py
grep -rln "services.ka_dasha_kala" platform/python-sidecar/ --include='*.py'
grep -n "_local_import_files\|get_writer_source_hash" platform/python-sidecar/pipeline/orchestrator/asset_runner.py
```

**Result, per hub, confirmed importer sets:**
- `pipeline/transit_search.py` → `ka_gochara`, `ka_kshetra`, `ka_sangam`, and the **FROZEN L0
  writer `bg_sky_calendar`** (L0 blast radius by construction for any L3-motivated edit).
- `services/ka_dasha_kala/` → `ka_kshetra`, `ka_sangam`, `ka_taranga`, `ka_avadhi` (all L3), plus
  **`ph_nimitta` (L4, sealed)** via `services/ph_nimitta/dasha_consensus.py:106,163` — the widest
  cross-layer blast radius of the 7 hubs.
- `services/ka_temporal/` → `ka_yojaka`, `ka_avadhi`, `ka_vighnakara`, `ka_kalasutra`,
  `ka_gochara_v3_century_materialize`, plus transitively `ka_taranga` (via
  `taranga_kernel/promise.py`).
- `services/ka_graha_sancara/engine.py` → `ka_moorti_nirnaya`, `ka_sudarshana_varsha`,
  `ka_kota_chakra`, `ka_vedha_gochara`, plus the `muhurta` compute path under
  `brahmagyan/phala/` (**L4**, a second cross-layer edge).
- `services/gochara_grammar/`+`services/gochara_intensity/` → `permission_curve` route,
  `ka_gochara`, `ka_gochara_sweep` (retired but still source-coupled), `ka_vedha_gochara`.
  `ka_gochara_v3_century_materialize` is explicitly and verifiably **immune** — a regex-based CI
  test (`test_w34_century_horizon.py:69-72`) enforces a zero-import rule against this hub family,
  the one automated hub-boundary guard found in the whole audit.
- `services/kala_trigger/` → `ka_sangam` (sole writer importer), with a documented near-circular
  reverse coupling to `ka_sangam.engine.py` itself.
- `services/taranga_kernel/` → `ka_taranga` only (narrowest hub — reads more like an
  extraction-for-testability module, with its own CI regression guard against re-inlining).

**Combined blast radius:** `ka_gochara` and `ka_sangam` each depend on 3 of the 7 named hubs —
the two highest-risk single assets purely from hub-coupling.

**The precise blind spot, confirmed by reading `_local_import_files`/`get_writer_source_hash`
(`asset_runner.py:335-413`) directly:** this **is** a real, correctly-implemented transitive
closure over local imports (including deferred/in-function imports), wired into two live gates —
a CI staleness check (`provenance_inventory.py --check`) and a hard dispatch-time abort
(`_verify_sidecar_code_matches_manifest`). **A hub edit cannot silently ship under an unchanged
hash** — that specific §N.8 failure mode does not apply here. **But neither gate marks any
already-built DB row as stale or schedules a rebuild.** `compute_downstream_closure` is the only
DB-row staleness mechanism found, and it is scoped strictly to `asset_registry.depends_on` edges
between *registered* assets — none of the 7 hubs are themselves registered assets, so none of
their edit-time blast radii are visible to it at all. The bridge from "hub digest changed" to
"these N sibling writers' data needs rebuilding" is a manual, human, grep-and-read step (exactly
this audit packet's own method).

**Verdict: NEEDS DECISION.** Not a straightforward READY (a real, evidenced gap exists between
code-identity detection and data-staleness propagation) nor a flat NOT READY (the code-identity
gates that do exist are genuinely correct and CI-enforced, not theater). The decision needed: is
the existing manual-audit discipline an acceptable standing substitute for an automated
hub→dependent-asset staleness bridge, or should `asset_registry` grow a way to declare non-asset
code hubs so `compute_downstream_closure` can see them?

---

## Domain I — Source inventory (unmerged branches): **no formal READY/NOT READY/NEEDS DECISION verdict stated by the source packet**

**Note on this compilation:** unlike every other domain, `_work/DOMAIN_I.md` does not conclude
with one of the three required verdict labels. It reports a content-level delivery classification
instead. Carried forward as-is below; flagged here rather than assigned a verdict by this
compilation (per instructions, this document compiles, it does not re-adjudicate).

**What was checked:** total unmerged branch count vs. the "~113" campaign framing claim, and a
content-level (not ancestry-level) diff of 15 sampled branches — prioritized toward
kshetra/sangam/gochara/kala — against `origin/main`.

**Reproducing commands (`_work/DOMAIN_I.md`):**
```
git fetch --unshallow origin   # the audit worktree's .git was shallow; this is a prerequisite
git rev-parse --is-shallow-repository   # → false, after unshallow
git branch -r | wc -l    # → 1059
git branch -r | grep -iE 'l3|kala|ka_|gochara|kshetra|sangam' | wc -l   # → 137
git diff origin/main origin/<branch> -- <specific-file>   # per sampled branch, full-file content diff
```

**Result:** the "~113" figure is **wrong by roughly an order of magnitude** — total remote
branches = 1059 (off by ~9.4x). Branches matching the L3-naming heuristic = 137 (closer, but still
undercounts by ~21% if "~113" was meant to approximate this subset).

**Sample result: 14 of 15 = DELIVERED, 1 of 15 = STALE, 0 = GENUINELY_UNDELIVERED.** PR #2607
(`fa9857f00`, "deliver governed L0-L3 source execution") is the real, large squash-delivery event
behind most "already delivered" verdicts, landing one day after the `codex/l3-kshetra-*` branches'
last commits. The one STALE branch (`codex/nirmana-l3-w3-m12-gochara-orphans`) predates a
since-landed correctness fix (F-KOTA-3) elsewhere in the same file family — evidence of an old
snapshot, not evidence its own orphan-row-disposal concern was independently resolved (that would
need a live DB check, not attempted).

**What this domain does not establish:** whether the same pattern holds across the 122 unsampled
L3-naming-matched branches or the ~922 unsampled non-L3-named branches. The consistent pattern
across all 15 samples is *suggestive* the campaign process genuinely absorbs branch work rather
than losing it, but 15/137 is not enough to certify that for the full population.

---

## Domain J — Session and tooling: **NOT READY**

**What was checked:** stream worktrees, the `CLAUDE_CODE_FORCE_SESSION_PERSISTENCE` /
`CLAUDE_CODE_CHILD_SESSION` transcript-persistence hazard, `.claude/settings.json` permission
enforcement, credential routes (`dbenv.sh`/`dbenv_builder.sh`), and backup/restore.

**Reproducing commands (`_work/DOMAIN_J.md`):**
```
git worktree list
grep -rn "CLAUDE_CODE_FORCE_SESSION_PERSISTENCE\|CLAUDE_CODE_CHILD_SESSION" --include="*.sh" --include="*.md" --include="*.json" .
find . -name "settings*.json" -path "*.claude*" -not -path "*/node_modules/*"
test -f /Users/Dev/madhav-l3/dbenv.sh && echo EXISTS
find 00_ARCHITECTURE -iname "*backup*" -o -iname "*rollback*"
```

**Per-item results:**

| Item | Verdict | Evidence |
|---|---|---|
| 1. Stream worktrees | **READY** | The two worktree facts the governing plan actually commits to — integration worktree at `/Users/Dev/madhav-l3/integration` on `codex/madhav-l3-claude-code`, and the 8 (actually 9, one extra) preservation branches pushed to `origin` — both independently confirmed live. The plan does not mandate a fixed worktree-per-stream pool, so its absence is not a gap. |
| 2. Transcript persistence hazard | **NOT READY** | The hazard is named exactly once in the entire repo — inside the audit's own prompt file (`PROMPT_0...md:257-258`) — not in any launcher script, `settings.json`, or CI workflow. No mechanical enforcement exists; a nested session today would silently become non-resumable unless a human manually exports the variable. |
| 3. Permissions | **NOT READY** | `.claude/settings.local.json` in this worktree contains exactly `{"dangerouslySkipPermissions": true}` — no allowlist, no denylist, no scoping. Every constraint this audit operated under (read-only, no git mutation, no credential printing) is enforced only at the prompt/instruction level, not by any technical control. |
| 4. Credential routes | **READY** | `dbenv.sh`/`dbenv_builder.sh` both exist, both structurally route through `gcloud secrets` (1 ref each) rather than hardcoding values, both export 3 `PG*` variables. No secret value was read or printed during verification. |
| 5. Backup/restore | **NOT READY** | A real, current, honestly-labeled DR runbook (`G1_E_DURABILITY_DR_RUNBOOK_v1_0.md`) scopes all `kala_*` tables into its 24h RPO/RTO tier, but its own frontmatter states PITR is disabled in production and no restore drill has ever been executed. A separate, tested logical-export mechanism (`export_irreplaceable_tables.sh`) covers a different, narrower table set (conversations, prediction/outcome/audit ledger), not `kala_*`. |

**Verdict: NOT READY overall**, on the strength of items 2, 3, and 5. In every failing case there is
a real, named, honestly-labeled artifact acknowledging the gap — none is a fabricated PASS. Per
CLAUDE.md §N.8, a documented risk is not a mitigated risk.

**What would flip each to READY:** item 2 — a launcher script/hook/settings entry that
mechanically sets `CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1`; item 3 — an actual
`permissions.allow`/`permissions.deny` list scoping tool access, harness-enforced rather than
prompt-instructed; item 5 — either PITR enabled with at least one executed restore drill against
`kala_*` tables, or an explicit native ruling that the orchestrator-rebuild path is the intended
primary recovery mechanism for this tier.

---

---

## Readiness verdict (deliverable #11) and native decision list (deliverable #12)

Rendered by a separate cycle-7 opus-tier judgment agent over the full domain/finding corpus above,
plus `KALA_STRATEGY_TRACEABILITY_MATRIX_v1_0.md`, `KALA_PROVING_JOURNEYS_BASELINE_v1_0.md`,
`KALA_ACCEPTANCE_REGIME_MAPPING_v1_0.md`, `KALA_BRIEF_CONFORMANCE_v1_0.md`,
`KALA_EXECUTION_DESIGN_v1_0.md`, `KALA_CAMPAIGN_RUNBOOK_v1_0.md`, `_work/T5.md`, `_work/T6.md`, and
`_work/DATA_LOSS_DIAGNOSIS.md`. The conductor independently spot-verified the three highest-stakes
new claims below before integrating (see verification log at the end of this section).

### 1. Strategy implementability — **GO-WITH-CONDITIONS**

The check that could have made this NO-GO: whether a material share of the 22 identities carry
strategic obligations with no implementation path, or the campaign's work is end-to-end gated on
decisions outside its control. Both checked negative — T1 produced a complete 23-row traceability
chain with no orphaned row, and C2.2 analysis/route work, all D1/D2 contract work, and
disposable-DB proofs are confirmed never-gated (Domain C proved the build path end-to-end,
141/141 tests). The strategy decomposes; it is not vapor.

The checks that could have made this a clean GO, and failed:

1. **No admissible receipt exists for the strategy's own delivery target.** T3 established that all
   17 event types in `nirmana_elevation_campaign_events` are producer-side/campaign-internal/
   governance bookkeeping. `CONSUMER_INTEGRATED` and `VALUE_EVALUATED` have **zero** admissible
   event types (`grep -rn "CONSUMER_INTEGRATED\|VALUE_EVALUATED" platform/scripts/nirmana/` → no
   matches); `DEPLOYED_ACCEPTED` has no per-asset type. The execution brief's delivery target is
   `LAYER_DATA_ACCEPTED + CONSUMER_INTEGRATED + DEPLOYED_ACCEPTED + VALUE_EVALUATED` — the maximum
   truthfully claimable state under the current vocabulary is `DATA_ACCEPTED`, two states short.
   `Accepted N/22` cannot move past 0/22 by two independent routes: no L3 asset has any `t3` event
   at all (F2), and even a perfectly-evidenced asset hits a ceiling below the stated target. This is
   a definitional incoherence between the strategy's target and the campaign's instrumentation.
2. **No per-asset admission authority exists today.** The only native-authored asset brief is
   `GOCHARA_FAMILY_ELEVATION_PLAN_v0_3.md`, frontmatter `status: PROPOSAL_FOR_NATIVE_RULING`,
   `does_not_authorize: any production code change, build, migration, registry edit, lifecycle
   change or hold release`. Kshetra and Sangam briefs are confirmed absent (T4). The layer brief is
   missing contract §4/§5/§6 — the §6 disposition table is populated for `ka_gochara_sweep` only,
   leaving 21 of 22 identities with no disposition anywhere. Formally, zero assets are authorized
   to start today.
3. **The governing documents disagree about what at least one asset produces, and it is
   load-bearing.** T5 Tension 1 is a five-way disagreement on `ka_gochara`'s output table/generation
   (`kala_gochara_windows_v2`/2.0 per strategy+writer+migration-1018-digest vs. `kala_gochara_windows`
   /3.0 per live seed+live consumer citation). An asset whose two acceptance instruments disagree
   about which rows are its output cannot be honestly accepted under any regime.

Also weighed: T2 found all three proving journeys — the campaign's declared north star — fail at
the identical F02 link (temporal mechanism), for the identical reason (`kala_activation`/
`kala_convergence` at 0 rows, fallback `kala_bhavishya` also 0). T6 found F16 (knowledge-time) has
no code or schema at all, and F17 is application-level only with no DB constraint.

**Conditions (native/strategy-owner, none executable by the campaign):**
- **S1.** Design receipts for `CONSUMER_INTEGRATED`, per-asset `DEPLOYED_ACCEPTED`, and
  `VALUE_EVALUATED` — or formally amend the delivery target to what the vocabulary can evidence
  (`DATA_ACCEPTED`) and restate the headline metric. Without S1 the campaign can execute flawlessly
  and still report 0/22.
- **S2.** Rule on per-asset admission authority (ratify or supersede Gochara v0.3; decide whether
  Kshetra/Sangam briefs must precede W2/W3; decide whether layer-brief §4/§5/§6 legitimately defer
  to W0).
- **S3.** Settle the `ka_gochara` family's table/generation identity so both acceptance instruments
  count the same rows.
- **S4.** Rule whether the contribution register's per-asset objections (first-domain-only,
  missing-dignity→0.5, global top-750, truncation family) are elevation requirements or aspirations.
- **S5.** Dispose of T1's orphan work/orphan obligations — assign a U-id obligation or retire/park.
- **S6.** Reconcile the two exit-gate vocabularies (T4 Q4) — the same mismatch underlying S1.

### 2. Environment readiness — **split verdict**

#### 2a. NO-GO — build dispatch, rebuild, and acceptance minting against the canonical chart

Four defects, present-tense and reproducible, none inside L3's unilateral authority to clear:

| # | Defect | Evidence | Effect |
|---|---|---|---|
| E-1 | `data_plane_builder` lacks SELECT on `bg_transit_moorti`, `phala_rectification`, `bg_synthetic_cohort`, `bg_synthetic_cohort_md` | `has_table_privilege(...)` → `f\|f` | `ka_moorti_nirnaya`/`ka_kshetra` hard-fail on their next build (unguarded reads, no substep isolation); `ka_bhavishya_lekha` fails on rebuild only |
| E-2 | PR #2695 unmerged; both its defects live on `main` | Hardcoded dev-absolute digest path resolves to a stale file where every digest differs; `call_dasha_eligibility` defaults `'lahiri'` vs canonical `'lahiri_chitrapaksha'` | `dispatch_frozen_rebuild.py` would commit a provenance receipt asserting code identity that never ran (§N.8 unearned signal) |
| E-3 | `ON DELETE CASCADE` from `kala_*.signal_id` → `bodha_msr_signals.signal_id` (migration 403), 5 tables | `confdeltype='c'`; decisive join on a second chart shows 100% of surviving rows resolve only to the original signal generation | Any rebuild of `ka_sangam`/`ka_kalasutra`/`kala_bhavishya`/`kala_darshana`/`kala_obstruction` is silently erased on the next L2 Bodha rebuild; already destroyed 335,403+14,868 rows on the canonical chart |
| E-4 | `ka_gochara_v3_century_materialize` `state='error'`, live BUILD-PROTECTED guard | Conductor's own live `kala_readiness_query_v2.sql` run reproduced the verbatim "PARISHKARA MR-06" refusal | Cannot be rebuilt without a native override — the guard is working, do not weaken it |

#### 2b. GO — everything that does not mutate production

F1 is genuinely fixed and present (conductor re-verified: `egate.sql` 4 `definition_revision` refs,
`capsule_audit.sql` 7 refs across all three sections with two `F1-class fix`/`F1 fix` comments —
**this supersedes Domain A's original NOT READY verdict above**, which rested on `capsule_audit.sql`
having zero such references; cycle 8 re-ran the now-fixed instrument live and confirmed it — Domain
A is now **READY** as an instrument, see the addendum above; decision-list item 18 is discharged).
Domain C is
READY (advisory lock proven per-chart on a disposable instance, 141/141 tests). Domain E is READY
(deploy gate diffs against production's own deployed SHA). Domain B is READY. F6 is conditionally
READY. Domain I found 0 of 15 sampled branches genuinely undelivered. The readiness query itself
works and can fail — it returned 22 `NOT_READY-BLOCKED-ANCESTORS` + 1
`NOT_READY-BLOCKED-NO-ROUTE`, zero READY-shaped rows, reproduced live twice independently.

Not GO but not blocking the non-mutating path (gates scaling up, not starting): Domain J NOT READY
(no mechanical `CLAUDE_CODE_FORCE_SESSION_PERSISTENCE`, no real `permissions.allow/deny` scope, PITR
disabled with no restore drill for `kala_*`); Domain F NOT READY (dark `kala_timeline`, 4 divergent
consumer paths); Domains D, G, H NEEDS DECISION.

### 3. Ordered native decision list

Ordered by work unblocked; reconciles and supersedes AUDIT_STATE.md's prior 13-item list (T5's 9
tensions are dissolved as a standalone item and distributed onto the decisions they actually attach
to, per the mapping below).

1. **F2 — t3 definition inheritance.** Only open decision with all-22 reach as a start gate; the
   live readiness query returns `NOT_READY-BLOCKED-ANCESTORS` for 22/23 rows and one ruling flips
   that column for all of them simultaneously. Precision correction to the record: the 12 ancestor
   freezes are not all under `t0` — 9 under `t0-09-01`, 1 (`ka_gochara`) under `t1`, 2 (`ka_tulana`,
   `ka_yojaka`) under `t2`; the 3 zero-evidence assets are `ka_kalasutra`, `ka_vighnakara`, and the
   century materialiser. **Independently corroborated cycle 8** via the separately-fixed
   `capsule_audit.sql` (item 18): under correct `t3` scoping, its §3 per-layer rollup shows L3 at
   **0 of 23 assets frozen** (all 8 of the campaign's `t3`-scoped `asset_frozen` events belong to
   L2) — a second instrument, a different query shape, the same true position. The prior "13 L3
   frozen" figure that had circulated in this campaign's own self-reporting was cross-definition
   contamination, not real progress.
2. **Design the missing acceptance receipts, or amend the delivery target.** Promoted from prior
   rank 9 — it caps the campaign's terminal outcome regardless of execution quality and needs design
   lead time. Absorbs T4 Q4 (the two exit-gate vocabularies).
3. **Per-asset admission authority** (new). Rule on Gochara v0.3; decide whether Kshetra/Sangam
   briefs must exist before W2/W3; decide whether layer-brief §4/§5/§6 legitimately defer to W0.
4. **The `kala_*` CASCADE data-loss remediation.** Demoted from prior rank 2 by *reach* (5 assets,
   not 22) but is the highest-severity item on the list — root cause of T2's first failing boundary
   for all three proving journeys, and it destroys work silently and retroactively.
5. **F8 / PR #2695 — land it or grant a scoped override.** Poisons the evidence of every dispatched
   build. Re-confirmed this cycle: still `OPEN`, `mergeStateStatus: UNKNOWN`, unmerged.
6. **F4 — grant SELECT on 4 named tables.** Small reach (3 assets) but a ten-minute decision — take
   in the same sitting as items 1-5. Plus: `ka_kshetra`'s cohort path lacks a `SAVEPOINT`, unlike the
   correct pattern already used for `bg_transit_av_gates`.
7. **The `ka_gochara` family knot — one ruling, six open items.** Merges prior items 3+6, T5
   Tensions 1/2/7/8, and elevation-plan Q1: the BUILD-PROTECTED guard, the five-way table/generation
   dispute, the century materialiser's closed loop, and `ka_sangam`'s edge resolving to an
   unregistered namesake service.
8. **Q4 — is `ka_kshetra`'s continuous-field model the right abstraction to preserve?** Merges T5
   Tension 3. 14.1M+ LOC/rows read by no verified consumer (PARK-5 hard-codes "field empty"); off
   the critical-path chokepoint chain so deciding late costs the critical path nothing but costs
   Stream C everything.
9. **Q8 + the register-objection class.** Merges elevation-plan Q8 + T5 Tensions 4/5 — six assets'
   truncation caps, `ka_sangam`'s first-domain-only selection, the still-unremediated `LIMIT 750`.
10. **Q3 — what counts as an independent witness?** T5 Tension 6 — `ka_sangam`'s de-correlation
    detector is blind to asset provenance and no downstream integrator inherits it;
    `ka_bhavishya_lekha` triple-counts.
11. **Consumer-path divergences.** `ka_tulana`/`ka_dasha_kala` wrapper mismatches (subsumed
    partly by item 7 for `ka_gochara`); `kala_timeline` DARK verdict stands, `kala_timeline_spec`
    is a live, distinct table written by `ka_kshetra` — do not conflate the two.
12. **Safety-exclusion coverage on served L3 surfaces** (new — conductor-verified this cycle):
    `detectMortalityExclusion` is wired into only `elect.ts` and `ritual.ts` of the 9
    `register_all.ts`-registered `kala_views` tools. Conductor confirmed directly: `ahead.ts`,
    `now.ts`, `story.ts`, and `upaya.ts` all accept the identical `question_frame.intent_verb`/
    `.stakes` free-text vector the detector exists to catch, and none call it (`grep -rn
    detectMortalityExclusion platform-mcp/src/tools/kala_views/` → only `elect.ts`/`ritual.ts`
    among tool files). Ranked 12th by work unblocked; by severity this belongs in the top five — a
    live binding-boundary gap (Product P07/P24/§13) on deployed surfaces.
13. **Domain D — does L3 adopt the 1035/1036 generation substrate?** No L3 head table exists; the
    substrate is entirely unexercised (zero generations ever opened for L1 or L2 either); a
    first-ever generation aborted mid-build has no rollback path.
14. **Domain H — is manual hub discipline an acceptable standing substitute?** Code-identity
    detection is solid; no automated bridge exists from "hub code changed" to "sibling `ka_*`
    writers' DB rows are now stale." Two hub edges reach into sealed L4 `ph_nimitta`.
15. **Domain G — coordination hygiene.** Six Pūrṇa lease rows still literally read `ACTIVE` while
    expired; no CI enforcement found for the `L3-REQ`/`PA-REQ` interlock or migration-range
    partition (convention only).
16. **Domain J — session/permission/DR posture** (new). (a) mechanically mandate
    `CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1`; (b) replace `dangerouslySkipPermissions: true` with a
    real allow/deny scope; (c) rule on DR — PITR disabled, no restore drill ever run for `kala_*`.
17. **F3 — dispatch `ka_sangam` once through a manifest-capturing run before relying on it.** Only
    11/23 identities have ever been captured by a surviving `build_runs.plan_manifest` — `ka_sangam`,
    the campaign's own chokepoint, is not among them despite 522 build_runs on the canonical chart.
18. **DISCHARGED cycle 8 — `capsule_audit.sql` re-run under the now-correct scoping.** Domain A's
    original NOT READY verdict is superseded by the F1 sibling-sweep fix; cycle 8 ran the fixed
    instrument live (read-only, `amjis_app`) and confirmed §1 = 0 rows, §2 = 11 rows all `ok`, §3 =
    L3 0/23 frozen under `t3`. Domain A is now READY as an instrument; its corrected output is
    folded into decision-list item 1 as independent corroboration, not left here as an open item.
19. **Governance-hygiene residue.** T5 Tension 9 (REG line-anchor drift, 3/23 checked); T4's
    remaining conformance questions; the vestigial `'service_ok'` state.
20. **Not L3's to fix, report to owners:** `mimamsa_* 0/37`, `phala_* 0/20`, `chart_* 4/15`
    inaccessible to `data_plane_builder` (corrected count: 253/431, not 258/431).

**Pointer retained, not duplicated:** `KALA_EXECUTION_DESIGN_v1_0.md` §5's ruling queue
(F2 → Q4 → Q1 → Q8 → Q3 → Q2 → Q7 → Q6 → Q5) remains authoritative for the elevation plan's own
Q-numbered questions; Q2/Q5/Q6/Q7 stay at their stated ranks there and are not restated here.

**Process fix (not a native decision):** a packet-table completeness check at every cycle close
(`ls _work/*.md` diffed against the packet table; any file not listed is a finding) would have
caught Domain F's four-cycle invisibility sooner — see the cycle-7 note in AUDIT_STATE.md.

### Conductor's spot-verification log for this section (independent of both authoring subagents)

- `grep -c definition_revision platform/scripts/nirmana/{egate,capsule_audit}.sql` → egate **4**
  (matches prior cycles), capsule_audit **7** (new measurement this cycle) — confirms the F1
  sibling-sweep claim. **Correction to the authoring agent's own citation:** it cited "F1-class fix
  comments at lines 29 and 60"; the actual second comment is at **line 102** ("F1 fix: same scoping
  as §1"), not line 60 — a minor line-number error that does not affect the substance of the claim
  (both `capsule_audit.sql` §1 and §3 are confirmed scoped by `frozen_def`/`definition_revision`
  filters; §2, lines 64-85, is also scoped via the same `frozen_def` CTE pattern though without its
  own inline comment).
- `grep -rn detectMortalityExclusion platform-mcp/src/tools/kala_views/*.ts` → only `elect.ts` and
  `ritual.ts` among the 9 registered tool files; `ahead.ts`/`now.ts`/`story.ts`/`upaya.ts` each
  independently confirmed (via direct `grep -n "question_frame\|intent_verb\|stakes"`) to accept
  the same `question_frame.intent_verb`/`.stakes` fields in their zod schemas. Claim CONFIRMED.
- `kala_readiness_query_v2.sql` existence and cycle-6's live-run result were not re-run a third
  time this cycle (already independently reproduced twice: once by the authoring subagent this
  cycle, once by the cycle-6 conductor) — accepted on that standing double-verification.

No headline claim in this section failed spot-verification. One citation-precision error (line 60
vs. 102) was found and corrected in place.

**Cycle-8 addendum (conductor, done directly, not delegated):** discharged decision-list item 18.
Read `capsule_audit.sql` in full to confirm all three sections (§1 line ~34, §2 line ~85, §3 line
~107) now join on `WHERE definition_revision = (SELECT definition_revision FROM frozen_def)`, then
ran it live via `psql -f platform/scripts/nirmana/capsule_audit.sql` (role `amjis_app`, read-only).
Result: §1 = 0 rows, §2 = 11 rows all `ok`, §3 shows L3 at 0/23 frozen under `t3` (all 8 of the
campaign's `t3`-scoped `asset_frozen` events belong to L2). Updated Domain A's verdict (NOT
READY → READY, as an instrument), decision-list item 1 (added this as independent corroboration
of the 22/23 `NOT_READY-BLOCKED-ANCESTORS` reading), and item 18 (closed). Command output pasted
verbatim into the Domain A addendum above; also appended to `_work/DOMAIN_A.md`.

---

*End of KALA_ENVIRONMENT_READINESS_AUDIT_v1.0. This document is a compilation of cycles 1-7's
per-finding and per-domain evidence packets, plus the cycle-7 readiness verdict and native decision
list (deliverables #11 and #12), with one cycle-8 re-run (Domain A / decision-list item 18) applied
in place per that item's own instruction. Every reproducing command, table name, and confidence
caveat above is carried forward from its cited source packet or independently verified by the
cycle-7/cycle-8 conductor as noted.*

---

# Addendum (v1.1, 2026-09-22) — two corrections from the strategic session's independent re-measurement

Both concern F2 and both change how the native's inheritance ruling should be framed. The body above
is left as written (audit trail); read F2 together with this addendum. Full treatment:
`../KALA_NATIVE_RULING_SHEET_v1_0.md`.

## C-1. F2's scope is the 48 upstream ancestors, not Kāla's own 12 old freezes

F2 quantified the `ka_*` assets' *own* superseded evidence (12 / 7 / 3). The readiness gate does not
block on that — `NOT_READY-BLOCKED-ANCESTORS` is about the assets Kāla depends on. Reproducing query
(read-only, recursive closure of `asset_registry.depends_on` from every `ka_*`, non-`ka_*` members
only, joined to `asset_frozen` events by definition):

| Upstream layer | Ancestors | Frozen under t3 | Frozen only under a superseded definition | Never frozen |
|---|---|---|---|---|
| `bg_*` | 22 | 0 | 22 | 0 |
| `ga_*` | 13 | 0 | 13 | 0 |
| `bo_*` | 13 | 7 | 6 | 0 |
| **Total** | **48** | **7** | **41** | **0** |

Also measured: `max(observed_at)` over the whole event ledger is `2026-09-11 17:25:48` — **zero
events of any kind in the 11 days since**. No session is re-freezing L0 or L1 under t3. The options
table in F2 (A / B / C1–C3) must therefore be read as applying to these 41 upstream freezes first;
inheriting Kāla's own 12 does not by itself open any gate.

## C-2. `source_kind = server_reconstructed` is the certified path, not a weaker one

F2 (and `KALA_EXECUTION_DESIGN_v1_0.md` §4, Option A row) argue that ~30% of ancestor evidence being
`server_reconstructed`, "not a live build receipt", means a defensible re-freeze needs a re-run. That
misreads the vocabulary. `platform/scripts/nirmana/README.md` §"The identity split it enforces" and the
trigger `nirmana_elevation_guard_server_reconstructed_insert` (migration 632) define
`server_reconstructed` as the source kind reserved for the **verifier** service account: it is how
every `integrity_verified`, `asset_frozen`, `probe_accepted`, `stage_transition_accepted` and
`foundation_lane_accepted` event is minted, by design. All 8 of L2's t3 freezes carry it. It is
evidence of independent certification, not of a missing build. **The staleness argument against
inheritance stands; the source-kind argument does not.**
