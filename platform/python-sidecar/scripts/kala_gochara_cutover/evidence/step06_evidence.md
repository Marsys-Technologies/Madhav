# Step 6 evidence — '4.0' candidate build (plan §9)

Runbook step 6 (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md §9). Tranche 2
(requires `PRODUCTION_TRANCHE_2_AUTHORIZED=true`).

**Standing order acknowledged:** both flags were read from
GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md frontmatter before this step started;
no step proceeds past a red gate; a failed gate stops the tranche and
escalates.

- **What:** candidate build — ka_gochara writes '4.0' as `candidate` on the canonical chart; '3.0' untouched; authority stays '3.0'
- **Gate:** integrity contract green; row counts in manifest; storage measured; §12.9 fingerprint match recorded BEFORE the build
- **Reversal:** delete candidate under own scope (ledger rollback)
- **DSN target:** `127.0.0.1:5433/amjis` (production, cloud-sql-proxy)
- **Operator / principal:** `amjis_app`

## 2026-09-24 — NATIVE RULING recorded; step NOT RUN — HALTED at the §12.9 gate (E-018)

Ruling (verbatim): **"Approved on point number two. Go ahead to everything."**
(native, 2026-09-24 17:09 IST / 2026-09-24T11:39:01Z, via the main agent;
full text in ESCALATIONS.md). Scope (c): §7.C steps 6–10 authorized
notwithstanding the merge-state preconditions (P-1 / WP9 §5.2 / N-19 live on
this branch, PR #2731). Tranche-1-green achieved first (step 5 RESUMED GREEN,
see step05_evidence.md).

### §12.9 staleness gate — verified to exist; RED on production

- Gate tests: fresh disposable Postgres 16 containers recreated —
  `gochara-wp6-disposable` (55433) and `gochara-wp10-disposable` (55434) —
  `test_wp12_vedha_stamp_helpers.py` + `test_wp12_vedha_fingerprint.py`
  **40 passed, 0 skipped** (13 previously NOT_RUN for want of 55433 now run
  green). The §12.10b writer-honesty fix (`uncited_extension` read from the
  row's actual citation state, never a literal) is covered by these tests.
- Production gate state (`check_overlay_freshness`, read-only, as `amjis_app`):
  - chart `1c826d5a…`: house_vedha **stale** — 135 rows, 135 without a
    fingerprint, 0 mismatched; moorti **stale** — 72 rows, 72 without, 0
    mismatched; `gate_allows_overlays = False`
  - chart `482012f1…` (canonical): house_vedha **stale** — 132 rows, 132
    without, 0 mismatched; moorti **stale** — 71 rows, 71 without, 0
    mismatched; `gate_allows_overlays = False`
  - Diagnosis: all overlay rows predate migration 1082's stamp columns
    (applied earlier today under E-016), so every row carries a NULL
    `upstream_fingerprint`. The gate is working exactly as designed: a
    candidate must not be built on rows whose citation/fingerprint state is
    unverified.
- Prescribed remediation (step06's own refusal text): rebuild
  `ka_vedha_gochara` and `ka_moorti_nirnaya` for the chart with this branch's
  writers (which populate `upstream_fingerprint`, M-8 rows, and the §12.10b
  honesty fix). **Not performed this run** — see the halt reason below: with
  the build blocked independently, an isolated rewrite of live-served overlay
  rows would be a production change with no tranche outcome attached to it.

### HALT reason — the step-6 episode enumeration driver does not exist

`step06_candidate_build.py` consumes the candidate's episode set as
`--episodes-json` / `--coverage-json`: "at tranche time the kernel pipeline
enumerates them". No such enumerator exists on this branch or anywhere in the
sidecar: the only callers of `ledger.write_contacts` are tests and step06
itself; `ka_gochara/service.py::find_episodes` SERVES from the ledger and only
solves Moon episodes live (R7, never persisted); the gochara_kernel modules
(arcs/knots/contacts/episodes/coverage) are the solving library, with no
chart-level driver that resolves the chart's WP1 target set from L1 facts and
enumerates all bodies × relations × targets over the horizon. Writing that
driver is the core of the '4.0' writer itself — new engineering, not a
prepared tranche artifact, and §10 bars live-chart writes before the proof
matrix's gates have run for it ("no live chart before its gate"). Building it
ad hoc inside the tranche would be improvisation; per the standing order this
run stops instead.

### Independent downstream blocker (recorded, still in force)

E-012: the '4.0' **windows projection writer** (plan §2.2/§4.7 — ka_gochara
writing `kala_gochara_windows` rows for '4.0') does not exist. Step 7's
`windows_present` gate is RED by design without it and step 8 refuses to flip.
Even a completed step 6 could not reach the flip this run. The authority flip
therefore remains physically impossible until that writer is built and gated —
the native's authorization of steps 6–10 stands, but the artifacts the steps
operate on are missing.

### State summary

- Steps 6, 7, 8, 9, 10: **NOT RUN** (halted at step 6's precondition gate).
- Production unchanged by this step: no candidate manifest, no '4.0' contacts
  or coverage rows, generations **v1=38287 / 3.0=1830** untouched, authority
  rows both `'3.0'`, century `is_active=false`.
- Disposable DBs 55433/55434 torn down after the gate tests.
- Escalation: **E-018** (ESCALATIONS.md) — requests (i) a native decision on
  who builds the episode enumeration driver and the windows projection writer
  (E-012 owner question carried), (ii) whether the overlay fingerprint rebuild
  for the two authority charts should run now as its own reviewed change
  (branch writers are ready and gate-tested) so the §12.9 gate is green when
  step 6 is re-attempted.
