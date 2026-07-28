---
artifact: PARKED_FINDINGS_CLOSE
canonical_id: PARKED_FINDINGS_CLOSE
version: 1.0
status: COMPLETE — item 2 of 3 native-authorized parked-finding closures (this PR).
  Items 1 (migration-339) and 3 (ka_gochara_sweep) are separate PRs, tracked in
  SESSION_LOG.md.
created: 2026-07-28
chart_under_test: fixture chart (this wave's CI smoke test) + spot-checks against
  482012f1 (canonical) and 1c826d5a (operator E2E)
---

# Parked-Findings Close — item 2: `ga_structural_writer.py` L1 defect + fleet-wide vocabulary audit + fresh-chart CI smoke

Native authorization (2026-07-28, same-day follow-on to the ŚUDDHA-VĀCA close):
"(2) ga_structural_writer.py L1 defect — fix the writer, THEN run a fleet-wide
vocabulary audit ... THEN add a fresh-chart CI smoke ... so the schema-drift
class dies structurally."

## Part A — `ga_structural_writer.py` fix (VERIFIED-FIXED)

`_load_shadbala_and_bhava_fact_ids` (lines 3369/3378) selected
`graha_shadbala_total` / `house_bhava_bala_total` facts by `fact_category` alone
— no `fact_key` pin, no `ORDER BY` — the exact D1_MISSELECT shape as P0-5
(`bo_laksana.py`), against the SAME `graha_shadbala_total` category confirmed
(live DB) to carry 3 fact_key variants per graha (`rupa`, `ratio`,
`required_rupa`). Without a pin, the dict-overwrite `shadbala[subj] = (...)`
silently kept whichever row Postgres happened to return last — SUN could
resolve to `1.694` (ratio) or `8.47` (rupa) depending on physical row order.

TEST-FIRST: a new test (`test_ga_structural_shadbala_fact_key_pin.py`) proved
the defect first (MOON resolved to `0.941667` instead of `5.65` under an
unpinned query, using a fake cursor that actually parses the executed SQL's
WHERE clause rather than ignoring it). Fix: pinned `fact_key = 'rupa'` for the
shadbala query (matching the convention already established by the P0-5/
P0-1..4 fixes) and `fact_key = 'total'` for the bhava_bala query (defensively,
per the N.7 Narration Fidelity Principle §N.7.2 — only one fact_key exists for
that category today, but the pin closes the same silent-overwrite risk if a
second one is ever added). The two now-stale entries in
`fact_category_pin_allowlist.json` (lines 86-96, filed against this exact
finding) were removed — the C.7 lint no longer flags this function.

**Verification:** 4/4 new tests pass; 73/73 pre-existing `ga_structural_writer.py`
tests pass (`test_ga_structural_v6_doctrine.py`,
`test_lane1_ga_structural_modularization.py`); `check_fact_category_pinning.py`
repo scan: 0 new violations (27 pre-existing, allowlisted — down from 29). Full
`python-sidecar` suite: 5133 passed / 35 failed, all 35 in
`tests/test_l0_remedy_corpus.py` (CI's own documented TEARDOWN-EXCLUDED suite,
confirmed identical on unmodified `origin/main`) plus one confirmed
full-suite-only ordering flake in `test_has_writer_completeness.py` (passes in
isolation with and without this diff; the diff touches no `@register()` writer
or asset_id, so this flake is unrelated — see SESSION_LOG for the full
reasoning).

## Part B — Fleet-wide vocabulary audit (disposition table)

Every enum-shaped Postgres CHECK constraint on a writer-populated table (50
constraints, `kala_*`/`phala_*`/`bodha_*`/`chart_dashas`/`chart_divisionals`/
`mimamsa_*`) was cross-referenced against the writer code that populates it,
via 4 independent research passes. **47 of 50 constraints: no drift.** 3
findings, disposition below.

| # | Constraint | Writer | Finding | Severity | Disposition |
|---|---|---|---|---|---|
| 1 | `ga_structural_writer.py`'s `graha_shadbala_total`/`house_bhava_bala_total` selection (not itself a named CHECK — the P0-N1 defect the fact_key-pin lint flagged) | `ga_structural_writer.py:3369/3378` | Unpinned fact_category selection, silent overwrite | P0 | **VERIFIED-FIXED, this PR** (Part A above) |
| 2 | `kala_bhavishya.domain` (`kala_bhavishya_domain_canonical`) | `pipeline/orchestrator/writers/ka_bhavishya_lekha.py:158-190` | `_DOMAINS`/`_ALLOWED_DOMAINS`/`_DOMAIN_KEYWORDS` still use pre-migration-386 legacy words (`'finance'`, `'spiritual'`) instead of the canonical (`'wealth'`, `'spirituality'`). Two compounding effects: (a) a genuinely canonical upstream `'wealth'`/`'spirituality'` value fails this writer's own stale allowlist check and is silently replaced by a keyword-guessed domain (misclassification, not a crash); (b) when `_infer_domain()` itself returns the legacy `'finance'`/`'spiritual'` literal, the unguarded `INSERT INTO kala_bhavishya` (no try/except) raises a live `CheckViolation` and fails the `ka_bhavishya_lekha` asset build outright. | **P0 — real, confirmed, can fail a live build** | **PARKED-HONEST** — out of this PR's authorized scope (only `ga_structural_writer.py` was pre-authorized for a code fix this wave). Recommend a dedicated fix updating `ka_bhavishya_lekha.py`'s domain vocabulary to the canonical 13-domain list from migration 386, with a rebuild of any chart whose `kala_bhavishya`/`phala_anchors` rows show a legacy domain value. |
| 3 | `chart_dashas.verification_pass_status` | `ga_writers/ga_dashas_writer.py:3189,3252` (CLI-only `build_ga_dashas()`/`main()` path, NOT the production orchestrator adapter `pipeline/orchestrator/writers/ga_dashas.py`) | Two "M-22 fix" scope-cap sentinel rows hardcode `verification_pass_status='scope_cap_sentinel'`, which is not in the CHECK constraint (`migration 206`). Wrapped in `try/except Exception: logger.warning(...)` — a genuine `CheckViolation` on `COPY` is silently swallowed; the intended sentinel row is simply never written, no build failure. | P2 — silent data loss, but CLI-only, not on the production build path | **PARKED-HONEST** — real, confirmed, but the affected path is not exercised by "click Build" in production; low urgency, recommend either adding `'scope_cap_sentinel'` to the CHECK constraint or reverting the M-22 rename to a value already in the allowed set. |
| — | `mimamsa_adjudication_log`/`mimamsa_snapshot_cosign`/`mimamsa_resonance_feedback` (4 constraints) | `platform/src/app/api/clients/[id]/learning/route.ts` | **No drift.** All 4 columns validated by an explicit TypeScript whitelist, character-for-character identical to the DB CHECK, returning HTTP 400 on mismatch (never reaching the INSERT). `verdict_mapped` is doubly safe — derived from a closed lookup table keyed by the already-validated `outcome`, not raw input. | — | **CLOSED — no action needed.** (Adjacent, out-of-scope observation: `route.ts:84`'s best-effort POST to `/mimamsa/abhilekha-resync` silently fails every time — no such Python sidecar endpoint exists. Flagged for whoever owns that resync feature, not a vocabulary-drift finding.) |

**11 additional informational "dead-vocabulary" notes** (DB-legal values a writer's
code has no path to ever produce — by design, not a defect) were surfaced across
the `ka_*`/`ph_*` audit passes; none represent a live-INSERT-failure or
silent-data-loss risk (every one is either on a nullable column or the writer's
own fallback logic never reaches the unproduced value). Full per-column detail
lives in the audit transcripts (session background-agent output, summarized
above); not reproduced in full here to keep this report proportional to the 2
real findings it exists to disposition.

## Part C — Fresh-chart CI smoke test (`fresh_chart_smoke.yml`)

New scheduled (Wednesday 03:00 UTC, offset from `icr_weekly_scan.yml`'s Sunday
cadence) + `workflow_dispatch` GitHub Actions workflow. Builds ONE synthetic
("fixture", `role='fixture'`) chart through the full active asset plan (107
assets at authoring time) against a database bootstrapped from a real
production schema snapshot with the current branch's migrations applied on
top — so a schema/writer vocabulary mismatch introduced by any future PR fails
in CI, on that PR's own scheduled/dispatched run, not months later as a
hand-discovered parked finding (this wave's own origin story).

**Not wired to `push`/`pull_request`** — `ka_gochara_sweep` and `ka_sangam`
are substep-heavy enough (migration 462: `writer_timeout_seconds=21600`/6h,
measured ~300 substeps at a few per 30 minutes) that gating every PR on a
multi-hour job is not a workable CI experience. A scheduled cadence still
retires the "discovered by hand, eventually" failure mode this item exists to
close, without blocking normal development.

**Genuine architectural discovery made while building this** (documented in
the workflow's own header comment, repeated here for visibility):
`platform/scripts/migrate.ts` **cannot bootstrap a truly empty database.**
`0000_seed_legacy_applied.sql`/`0000b_seed_legacy_v2.sql` fake-mark ~80
foundational migrations — including the one creating `public.charts` — as
already-applied WITHOUT running them, because they were originally applied to
production by hand via `psql` before `migrate.ts` tracking began. An empty DB
therefore never gets those tables via `migrate.ts` alone. This is why the
smoke test starts from three targeted `pg_dump`s of production (schema-only;
the ~85 global reference tables' data; the `_migrations_applied` tracking
table's own content — the last one is required so `migrate.ts` correctly
treats history-to-date as already-done rather than trying to replay
non-idempotent historical migrations against an already-migrated schema) plus
the ~32 global `asset_throughput` rows (so L0 singletons like `bg_ephemeris`
aren't redundantly recomputed every run), never from `migrate.ts` against a
blank database.

**Local validation performed** (production access + a local fresh Postgres,
`pgvector` extension installed via Homebrew): confirmed the full
dump→restore→`migrate.ts`→build sequence runs correctly end-to-end. The local
run progressed cleanly through the full L0/L1/L2 fleet (`ga_dashas`,
`ga_vargas`, `ga_nakshatra`, `ga_transit_anchors`, and on into L2/L3) with
**zero CHECK-constraint failures observed**, reaching `ka_gochara_sweep`
(substep 8/303) before this report was written — i.e. it exercised the great
majority of the 107-asset plan, including every writer this wave's vocabulary
audit covered, cleanly against a freshly-restored schema. Caught and fixed one
real bug in the bootstrap script itself during this run — an invalid
`build_runs.scope` literal (`'full'` is not in that column's own CHECK
constraint; `'asset_set'` is) — exactly the class of defect this mechanism
exists to catch, one layer removed. The run was not left to run to full
completion locally (`ka_gochara_sweep`'s remaining ~295 substeps are a
multi-hour tail per migration 462's own measurement, and completing that
tail is not this session's job to sit through) — the first scheduled/
dispatched CI run is this mechanism's proving ground for that specific tail,
reported honestly as not yet observed to full completion, not asserted as
passing.

## Disposition summary

| Item | Status |
|---|---|
| `ga_structural_writer.py` P0-N1 fix | VERIFIED-FIXED, this PR |
| Fleet-wide vocabulary audit (50 constraints) | COMPLETE — 47 clean, 1 fixed (above), 2 new findings PARKED-HONEST |
| `ka_bhavishya_lekha.py` domain vocabulary drift | **NEW finding, PARKED-HONEST** — real, can fail a live build, needs its own authorized fix |
| `chart_dashas` CLI-only scope-cap sentinel | **NEW finding, PARKED-HONEST** — real, silent, low urgency (CLI-only path) |
| `mimamsa_*` tables | CLOSED — no drift found |
| Fresh-chart CI smoke test | Merged this PR; first full-fleet proof is its own first scheduled/dispatched run |
