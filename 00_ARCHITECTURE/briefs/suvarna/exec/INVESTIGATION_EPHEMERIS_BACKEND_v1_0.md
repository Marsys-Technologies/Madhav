---
artifact: INVESTIGATION_EPHEMERIS_BACKEND
version: 1.0
status: DRAFT_FOR_REVIEW
date: 2026-10-01
lane: suvarna/land/TI-ephemeris-backend-001
decision: SS finding 2026-10-01 (panchang_engine set_ephe_path(None) / ka_vighnakara never resets)
mode: READ-ONLY investigation. No code, config, infrastructure, build or DB write was changed. The only non-read actions were local Python probes in a scratch directory (no repo writes) and one bounded `gcloud logging read`.
changelog:
  - "1.0 (2026-10-01): first measurement of the production Swiss Ephemeris backend, call-site inventory, image contents, DB evidence and a minimal remediation proposal."
---

# Which Swiss Ephemeris backend does production actually use?

Base: `origin/main` at `4eb40bec1`. All paths are relative to `platform/python-sidecar/` unless they start with `platform/`, `.github/` or `00_ARCHITECTURE/`.

## 0. Verdict (10 lines)

1. **Production backend is split.** L0/L3 assets that carry their own fail-closed check run on Swiss `.se1` files. Everything that relies on the ambient process state runs on whatever the last `set_ephe_path` left, which in practice is Moshier.
2. **L1 `chart_facts` (PyJHora path) = Moshier. Proven.** The stored native Moon (`graha_position MOON longitude_sidereal`, lahiri, `327.055230133129`) is reproduced to 0.000 arcsec with Moshier and differs by 0.665 arcsec from the pinned `.se1` files (section 4.2).
3. **`panchanga_daily` (`compute_panchang`) = Moshier. Proven.** Three sampled dates match Moshier to 0.000 arcsec; with the `.se1` files the same code differs by 0.2 to 0.9 arcsec on the Moon (section 4.3). The rows still cite "Swiss Ephemeris / pyswisseph".
4. **`ephemeris_daily` (bg_ephemeris) = Swiss files. Proven.** 25 of 25 sampled values match `.se1` to six decimals, and Moshier in only the two cases where the two backends coincide (the Sun on two dates) (section 4.1).
5. **Pravāha rows = Swiss files. Proven.** 138,836 `kala_gochara_contacts` rows, the convention row and both publication rows record `swieph` (retflag 65602 and 258) (section 4.4).
6. **Root cause.** The images set `SWE_EPHE_PATH`, which the Swiss C library never reads. `swe.set_ephe_path(None)` consults only `SE_EPHE_PATH`, so it falls to a default directory that does not exist, and `calc_ut` silently returns Moshier (reproduced locally, section 3.2). PyJHora also re-points the path to its own `.se1`-free wheel directory at import (`jhora/const.py:262`).
7. **Mechanism for per-asset divergence.** Swiss state is process-global, the orchestrator runs up to 4 assets as threads in one process (`pipeline/orchestrator/runner.py:101,682`), and the lock serialises calls but does not scope the path. Each call site sets the path to something different (or nothing), so the backend an unchecked asset sees is last-writer-wins and depends on thread timing.
8. **Magnitude is small but not zero.** Moon about 0.2 to 0.9 arcsec (about 1 second of Moon motion), TRUE_NODE about 25 arcsec, Sun and mean node about 0. It is a determinism and provenance defect (rows mislabelled as Swiss), not a visible astrology error, except at sign, nakshatra and tithi boundaries.
9. **No receipt, row or log records the backend** for any L1/L2/L3-non-Pravāha asset. The orchestrator receipt hashes only the asset config, and `ephemeris_version` stores the library version (`2.10.03`), not the backend.
10. **Minimal remediation:** one image `ENV SE_EPHE_PATH=/app/ephe` plus one explicit post-import `set_ephe_path` at the PyJHora import choke point and in `panchang_engine`, plus a recorded backend. It changes L1 and panchanga values at the arcsec level, so it needs a rebuild decision (section 7).

## 1. Call-site inventory (production-reachable code in `platform/python-sidecar`)

Legend for "path": **explicit** = sets a concrete `.se1` directory; **None** = `set_ephe_path(None)`; **ambient** = never sets, inherits process state. "Check" = inspects the returned flag and refuses Moshier.

### 1.1 Fail-closed, explicit path (Swiss proven)

| Site | What it sets | Check |
|---|---|---|
| `pipeline/orchestrator/writers/bg_sky_calendar.py:231-251` (`_require_swiss_file_backend`), called `:649` | explicit path, `FLG_SWIEPH\|SIDEREAL\|SPEED`, probe Sun at JD 2000-01-01 | raises if `retflag` lacks SWIEPH or has MOSEPH; digest pin `:277` |
| `bg_sky_calendar.py:444-446` (`scan_eclipses`) | `set_ephe_path(_resolve_ephe_path())`, which can be **None** if no file is found, then `FLG_SWIEPH` at `:486,528` | none at this site (covered only by the earlier `:649` check) |
| `pipeline/orchestrator/writers/bg_ephemeris.py:92-103,117` | reuses the bg_sky_calendar probe; `_compute_positions_for_date` re-sets the path on every day (`brahmagyan/l0_ephemeris.py:294`) | yes |
| `pipeline/orchestrator/writers/bg_muhurta_lattice.py:855-864` | resolve path, digest pin, backend probe | yes |
| `pipeline/orchestrator/writers/bg_cohort.py:219-254,321,339` | `set_ephe_path` per call, `FLG_SWIEPH\|SPEED` | raises on non-SWIEPH or MOSEPH (`:249`) |
| `pipeline/orchestrator/service_probes.py:431-503` (`_probe_ephemeris_engine`) | resolves `SWE_EPHE_PATH` or `SWISSEPH_PATH` or `/app/ephe`, SHA-256 of the three `.se1`, `set_ephe_path`, `FLG_SWIEPH\|SIDEREAL` | `allowed_ephemeris_backends=["swiss_ephemeris_file"]` (migrations 624, 1075). **Certifies only the process state at probe time**, not what later writers see |
| `scripts/kala_gochara_cutover/century_run_4_1.sh:31,82-88` | explicit `SWE_EPHE_PATH` or `/app/ephe` | raises on non-SWIEPH |

### 1.2 Pravāha-owned kernel (Swiss proven in data; **PRAVAHA-OWNED, do not touch**)

| Site | Behaviour |
|---|---|
| `services/gochara_kernel/knots.py:105-123` `calc_sidereal_lon` | sets the path **only if `ephe_path is not None`** (`:113`), otherwise ambient; flags `FLG_SWIEPH\|SIDEREAL` (`:35`); `_check_retflag` raises `EphemerisBackendError` on Moshier (`:92-102`); records `ephemeris_backend` from the returned flag |
| `services/ka_gochara/service.py:170-175,615-633`; `pipeline/orchestrator/writers/ka_gochara.py:262,318` (`KaGocharaService(swe)`) | `ephe_path` defaults to None, so ambient. Fails closed but does not set |
| `pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py:2054`, `services/ka_gochara_sweep/writer.py:272` | import `swe`; ambient |

### 1.3 Ambient or None, no backend check (exposed)

| Asset or module | Site | What it does |
|---|---|---|
| **panchang_engine** (`ga_panchanga`, `panchanga_daily_writer.py`, `ph_muhurta`, `ka_vighnakara` detector 2, routers) | `panchang_engine/__init__.py:71,149` (`compute_panchang`) and `:252,347` (`panchanga_instant`) | `swe.set_ephe_path(None)` at start **and again at the end**, so the call *leaves the process on the default path*. Flags `FLG_SIDEREAL\|FLG_SWIEPH` (`planets.py:23`, `angas.py:19`); `timings.py:630` `lun_eclipse_when(FLG_SWIEPH)`. Introduced `fa9857f00` (#2607) with the comment "prior request's path cannot leak" |
| **All L1 `ga_*` that go through PyJHora** (`ga_positions`, `ga_dashas`, `ga_vargas`, `ga_strength`, `ga_structural`, `ga_tajaka`, `ga_sensitive`, `ga_nakshatra`, `ga_condition`) | `pyjhora_adapter/*` never sets a path. `jhora/const.py:261-262` (site-packages, PyJHora 4.8.6) runs `swe.set_ephe_path(<wheel>/data/ephe)` **at import**; that directory holds `sefstars.txt`, `seleapsec.txt`, `seasnam.txt`, `seorbel.txt`, `ast_list.txt` and **no planetary `.se1`** | Ambient. `pyjhora_adapter/houses.py:85-88` uses `FLG_SWIEPH`. The adapter's own comments already admit the problem: `_jhora.py:26-43` ("no planetary .se1 ephemeris files ship with the wheel ... Moshier planet range") and `_isolation.py:8-18` ("swisseph fall back to a mis-ranged Moshier path") |
| `ga_sade_sati` | `ga_writers/ga_sade_sati_writer.py:366,439,1595` | `set_ephe_path(os.environ.get("SWISSEPH_EPHE_PATH", "/usr/share/ephe"))`. Neither the env var nor `/usr/share/ephe` exists in either image, so it is **explicitly pointed at a missing directory**: Moshier (inferred) |
| legacy `brahmagyan/ganita/graha_sthana_writer.py:68-71` (via `pipeline/brahma_pipeline.py:161`) | sets `SWE_EPHE_PATH` or `/app/ephe` "before importing PyJHora" | **Order inverted**: `from pyjhora_adapter.compute import ...` (`:74`) can import `jhora.const` afterwards, which re-points the path to the wheel directory |
| `ka_vighnakara` | `pipeline/orchestrator/writers/ka_vighnakara.py:149-157` `_get_sidereal_lon`: `FLG_SIDEREAL` only, no path, no check. `:704-710` calls `compute_panchang` | detector order per peak (`:553-585`): malefic_transit (ambient), panchanga_obstruction (**sets None**), gandanta, papakartari, combustion (all after the reset, so default path) |
| `ka_sangam` | `services/ka_sangam/engine.py:431` `calc_ut(..., FLG_SIDEREAL)`; `:1022-1382` swe use | ambient |
| `ka_kshetra` | `services/ka_kshetra/stage3_clocks.py:881` `FLG_SWIEPH\|SPEED`; `stage0_kinematics.py:618-660` | ambient |
| `ka_kota_chakra`, `taranga_service`, `w2g_validations/v3_spline_accuracy.py:118`, `gochara_v3/mechanisms/w26_real_eclipses.py` | swe calls, no path | ambient |
| `ka_graha_sancara` PATH-B | `services/ka_graha_sancara/engine.py:282-336` delegates to `platform/scripts/temporal/compute_transits.py:82-83` | **`FLG_MOSEPH` by default** (`moshier: bool = True`), `ephe_mode: "moshier"` (`:217`). Deliberate and labelled; PATH-A reads `ephemeris_daily` |
| `pipeline/transit_search.py:190-250` `_get_planet_pos` | `set_ephe_path(_resolved_ephemeris_path())` on every call (explicit when files exist) | no flag check; **resets the ambient path to Swiss** each time it runs |
| Sidecar HTTP routers (serving, not the job) | `routers/pyhora.py:72,140` (explicit `SWE_EPHE_PATH`), `routers/ephemeris.py:15-16,147` (`FLG_SWIEPH`, reports `swiss_ephemeris_file` vs `moshier_analytic_fallback`) | the `/ephemeris` route reports backend honestly |

`platform/scripts/temporal/compute_{vimshottari,yogini,kp,varshaphala,shadbala}.py` default to Moshier and label `ephe_mode`; they are outside the pipeline job image.

### 1.4 Order of global-state mutation

One orchestrator process (`python -m pipeline.orchestrator.main`, `Dockerfile.pipeline` ENTRYPOINT) runs assets as threads: `_WORKER_LIMIT` default 4 (`runner.py:101`), `_DaemonThreadPoolExecutor` (`:682`), "width = ORCHESTRATOR_WORKER_LIMIT, default 4" (`:1416`). The state sequence is therefore:

1. First `import jhora.const` (on first PyJHora use): path becomes `<site-packages>/jhora/data/ephe` (no planet files).
2. Any `compute_panchang` / `panchanga_instant` call: path becomes `None` (twice per call, start and end).
3. Any bg_* writer, `_probe_ephemeris_engine`, `transit_search._get_planet_pos`, `graha_sthana_writer`: path becomes `/app/ephe`.
4. `ga_sade_sati`: path becomes `/usr/share/ephe`.
5. Sidereal mode (`set_sid_mode`) is mutated the same way, by many writers.

`SWISS_STATE_LOCK` (`panchang_engine/swiss_state.py:22`) is an `RLock` held per decorated call. It prevents interleaving *inside* one call; it does not make the path a stable precondition of the *next* call. An unchecked asset therefore sees a backend decided by thread timing and by which assets ran before it. Even single-threaded, `ka_vighnakara` flips its own backend within one peak date (detector 1, then the reset in detector 2).

## 2. What the pipeline job image contains

- `Dockerfile.pipeline:13-24`: creates `/app/ephe`, downloads `sepl_18.se1`, `semo_18.se1`, `seas_18.se1`, `sefstars.txt`, `seleapsec.txt` from `https://storage.googleapis.com/madhav-ephemeris/se1`, with `curl -fsSL` and **`sha256sum -c` on the three `.se1`** (build fails on mismatch). The pinned digests are `ca1393ce...` (sepl), `1ca07bd6...` (semo), `a2cd8fc3...` (seas); the local copies used for the probes in this report match them. Coverage of `_18` files is 1800 to 2400 CE.
- `Dockerfile.pipeline:25,70`: `ENV SWE_EPHE_PATH=/app/ephe`. **`SE_EPHE_PATH` is set nowhere** (`.github/workflows/deploy.yml`, both Dockerfiles, job env).
- The serving sidecar `Dockerfile:12-30` has the same files (size-guarded rather than digest-pinned) and the same single `ENV SWE_EPHE_PATH=/app/ephe`.
- The Cloud Run job env set by CI (`.github/workflows/deploy.yml:2189-2197`) is only `GCP_PROJECT`, `PUBSUB_TOPIC`, `KA_KSHETRA_HASH_SPILL_DIR`.
- Bundled data: `pyswisseph==2.10.3.2` (`requirements.txt:8`) ships the compiled module only (no `.se1` in the wheel; confirmed in the local venv with the same pin). `PyJHora==4.8.6` (`requirements.txt:7`) ships `jhora/data/ephe` with the five helper text files and no planetary files (confirmed locally, 10 MB, no `.se1`).

So the files **are** in the image (build-time proof), and they are reachable only by code that sets `/app/ephe` explicitly. Nothing makes `/app/ephe` the default.

## 3. What the code does when files are missing

### 3.1 Per site
- Swiss C library: `set_ephe_path` never fails; `calc_ut` silently substitutes Moshier and reports it only in the returned flag. Documented in `bg_sky_calendar.py:234-239` and `service_probes.py:295-302`.
- Fail-closed: `bg_sky_calendar`, `bg_ephemeris`, `bg_muhurta_lattice`, `bg_cohort`, the ephemeris probe, the Pravāha kernel (`EphemerisBackendError`), `century_run_4_1.sh`.
- Silent: everything in section 1.3. `brahmagyan/l0_ephemeris.py:410-416` (legacy `build_ephemeris`) and `:1229-1233` (`query_ayanamsha_delta`) explicitly **fall back to `set_ephe_path(None)` with only a log warning**.
- The `bg_sky_calendar` check is correct but local: it validates the state at the moment it runs.

### 3.2 Reproduced locally (pyswisseph 2.10.3.2, the production pin; macOS/arm64)
With only `SWE_EPHE_PATH` set (as in the images) and the pinned `.se1` directory present:

| Path state | Moon 2026-06-15 retflag | Moon (sidereal Lahiri) | TRUE_NODE |
|---|---|---|---|
| explicit `.se1` dir | SWIEPH | 57.969294 | 308.062657 |
| `set_ephe_path(None)` | **MOSEPH** | 57.969101 | 308.069577 |
| PyJHora wheel dir | **MOSEPH** | 57.969101 | 308.069577 |

With `SE_EPHE_PATH=<se1 dir>` instead, `set_ephe_path(None)` returns SWIEPH (57.969294). `MEAN_NODE` reports SWIEPH under every path (analytic), which is why the probe at `service_probes.py:550` deliberately omits a backend there.

## 4. Evidence in the database (read as `suvarna_reader`)

### 4.1 `ephemeris_daily` (bg_ephemeris, computed 2026-09-04): Swiss files
25 sampled values (5 dates 1984 to 2120 by Sun, Moon, Mars, Mercury, Saturn, tropical, noon UT) recomputed locally with the pinned `.se1` and with Moshier. 25 of 25 match `.se1` to 6 decimals; 2 of 25 also match Moshier (the Sun on two dates, where the backends agree to within 5e-7 deg). Example: Moon 2026-06-15 stored `89.848966`, `.se1` `89.848966`, Moshier `89.848719`. `source_citation` says "pyswisseph + Swiss Ephemeris .se1" and is true here.

### 4.2 `chart_facts`, native chart `482012f1-...`, `graha_position`, `longitude_sidereal`, lahiri_chitrapaksha, `engine_version pyjhora/1.0.0`, computed 2026-09-07: **Moshier**
Recomputed with `pyjhora_adapter.positions.compute_positions` at the birth instant:

| Backend | Moon | vs stored `327.055230133129` | Sun | vs stored `291.962617284992` |
|---|---|---|---|---|
| pinned `.se1` | 327.055045493657 | **-0.665 arcsec** | 291.962617355555 | +0.00025 arcsec |
| Moshier (path None or PyJHora wheel dir) | 327.055230133129 | **0.000** | 291.962617284992 | -1.4e-9 |

A bit-exact match is the discriminator. Only the Moon and Sun are stored for this ayanamsha in `graha_position` (the others were not available at double precision), and only one chart was tested.

### 4.3 `panchanga_daily` (544 rows, 2026-07-09 to 2028-01-03, `computation_version 2.0.0-P2`): **Moshier**
`moon_longitude_deg` and `sun_longitude_deg` stored vs `compute_panchang(date, 20.27, 85.84, 330)` run locally:

| Date | No `SE_EPHE_PATH` (default path) | With `SE_EPHE_PATH` = pinned `.se1` |
|---|---|---|
| 2026-07-09 | 0.000 arcsec | Moon +0.223 |
| 2027-03-01 | 0.000 arcsec | Moon +0.595 |
| 2027-11-15 | 0.000 arcsec | Moon -0.873 |

`source_citation` still reads "Swiss Ephemeris / pyswisseph, sidereal Lahiri" and `ephemeris_version` is `2.10.03` for all 544 rows. That is `swe.version`, the library version (`panchang_engine/__init__.py:150,348`), not a backend.

### 4.4 Pravāha ledger: Swiss files
`kala_gochara_contacts.ephemeris_backend`: 138,836 of 138,836 rows are `{"backend":"swieph","retflag":65602,"swe_version":20230604}`. `kala_gochara_convention`: 1 row, `swieph` / `flg_swieph`. `kala_gochara_publication`: 2 rows, `{"backend":"swieph","retflag":258}`. These are the only tables that record a backend, and they do so from the returned flag, as intended.

### 4.5 Not discriminating
- `kala_obstruction` (ka_vighnakara, 747 rows, computed 2026-07-27): `obstruction_detail.source` = "swisseph/lahiri"; longitudes are rounded to 2 decimals, which is coarser than the Moshier-vs-Swiss gap, so the backend cannot be read from the data. The mechanism (section 1.3) says Moshier for detectors 3 to 5 once the reset has run (inferred, not proven).
- `ephemeris_audit_jsonb` columns (`kala_tithi_pravesha`, `l1_tajik_varsha_year_lords`, `bodha_*`) hold convergence diagnostics, not a backend.
- `asset_provenance_receipts` (98 rows): `config_digest` = digest of the asset config only (`pipeline/orchestrator/provenance.py:101`). No ephemeris path, flag or file digest enters it.
- `build_run_assets.error` mentions Moshier once: `ga_tajaka` 2026-07-16 "swisseph.calc_ut: jd -0.001010 outside Moshier planet range". JD about 0 is outside the `_18` file range as well, so Swiss would fall back to Moshier and produce the same text. Not discriminating.

## 5. Cloud Run job logs (one bounded read-only query)

`gcloud logging read` on `resource.type="cloud_run_job" AND job_name="brahma-build-pipeline-job"` with a text filter for swisseph, moshier or ephemeris, project `madhav-astrology`, `--freshness=7d --limit=20`: **allowed with the existing local credentials, no new privilege.** It returned 2 lines, both orchestrator start-up "registered writer: bg_ephemeris" messages (2026-10-01 15:01 and 17:36 UTC). No swisseph or Moshier warning exists in the window. That is expected: pyswisseph emits no log on fallback, and none of the exposed sites logs one. I made no further query.

## 6. Assets that call swisseph (grouped by exposure)

- **Backend verified in-run (fail-closed):** `bg_ephemeris`, `bg_sky_calendar`, `bg_muhurta_lattice`, `bg_cohort`, probe asset `bg_ephemeris_engine`.
- **Pravāha-owned, fail-closed, ambient path (PRAVAHA-OWNED):** `ka_gochara`, `ka_gochara_v3_century_materialize`, `ka_gochara_sweep`, and the `kala_gochara_cutover/*` scripts.
- **Exposed (ambient, explicit-wrong or None, unchecked):** `ga_positions`, `ga_dashas`, `ga_vargas`, `ga_strength`, `ga_structural`, `ga_tajaka`, `ga_sensitive`, `ga_nakshatra`, `ga_condition`, `ga_panchanga`, `ga_sade_sati`, `ka_vighnakara`, `ka_sangam`, `ka_kshetra`, `ka_kota_chakra`, `ka_graha_sancara` (PATH-B is Moshier by design), `ph_muhurta` (via `panchanga_instant`), `ka_muhurta_seva`/`muhurat.*` (via panchang_engine), `taranga_service`, `panchanga_daily_writer.py`, and the sidecar serving routes that call `compute_panchang`.

## 7. Minimal remediation proposal (not applied)

Principle: set the path explicitly and identically, never rely on ambient state, and record what ran.

| # | Change | Files | Notes |
|---|---|---|---|
| R1 | Add `ENV SE_EPHE_PATH=/app/ephe` next to `SWE_EPHE_PATH` so `set_ephe_path(None)` and the C default resolve to the pinned files | `platform/python-sidecar/Dockerfile.pipeline`, `platform/python-sidecar/Dockerfile` | One line each. Image rebuild and redeploy only. Alone it does **not** fix the PyJHora import-time override |
| R2 | One shared helper (for example `panchang_engine/swiss_state.py::ensure_swiss_backend()`) that resolves the path (same order as `l0_ephemeris._resolve_ephe_path`), sets it under `SWISS_STATE_LOCK`, runs the retflag probe and returns `{backend, path, se1_sha256}` | `panchang_engine/swiss_state.py` (new function) | Reuse `bg_sky_calendar._require_*` logic rather than a third copy |
| R3 | Replace the four `swe.set_ephe_path(None)` with the helper | `panchang_engine/__init__.py:71,149,252,347` | Removes the "leaves the process on the default path" effect |
| R4 | Re-assert the path after PyJHora import, at its single choke point | `pyjhora_adapter/_jhora.py` (after the `jhora` imports); also `ga_writers/ga_sade_sati_writer.py:366,439,1595` (use the helper instead of `/usr/share/ephe`) and `brahmagyan/ganita/graha_sthana_writer.py:68-74` (order inversion) | `_jhora.py` is the one place every `ga_*` passes through |
| R5 | For unchecked writers, call the helper at the top of the swisseph section and write the returned dict into `WriterResult.notes` (inside the frozen contract) | `ka_vighnakara.py`, `ka_sangam.py`, `ph_muhurta.py`, `ga_*` writers | Fixes "no receipt records the backend" for each asset without changing the receipt schema |
| R6 | Optional stronger form: add the backend dict to the receipt config for swisseph assets | `pipeline/orchestrator/asset_runner.py`, `pipeline/orchestrator/provenance.py` | **Frozen-orchestrator neighbour. Needs the native's explicit freeze exception.** R5 avoids it |
| R7 | CI guard modelled on `check_fact_category_pinning.py`: fail on `set_ephe_path(None)` and on swisseph modules that never call the helper; add an integration test (skipped without `.se1`) that runs `compute_panchang` then asserts `retflag & FLG_SWIEPH` | `platform/scripts/governance/` (new check), `tests/` | Earned-signal rule, CLAUDE.md section N.8 |

**Pravāha-owned, do not touch:** `services/gochara_kernel/*`, `services/ka_gochara/*`, `pipeline/orchestrator/writers/ka_gochara*.py`, `services/ka_gochara_sweep/*`, `scripts/kala_gochara_cutover/*`. The proposal needs no edit there: the kernel already fails closed and records the backend. Under R1+R2+R4 its ambient path becomes correct for free. Passing `ephe_path` explicitly from `ka_gochara.py:318` would be a Pravāha-lane follow-up if they want it.

**Consequences to decide before applying:**
- R1 to R5 change stored values. Every `ga_*` position, divisional, dasha boundary, Tajaka, sensitive point and `panchanga_daily` field moves by up to about 1 arcsec (Moon) and about 25 arcsec (TRUE_NODE where used). Sign, nakshatra and tithi-end flags can flip near boundaries. `ephemeris_daily` and the Pravāha ledger do not change. This needs a full L1 rebuild and the `chart_facts` digests will change; it is not a no-op image tweak.
- The FORENSIC 7/7 anchors are far from boundaries, so no anchor change is expected, but that has not been re-run.
- Whether the product should instead standardise on Moshier (it is deterministic and file-free) is a policy call for SS: the current state is the worst case, because the rows claim Swiss and are partly Moshier. `ka_graha_sancara` PATH-B and `platform/scripts/temporal` already treat Moshier as a declared mode.

## 8. Unverified

- The live Cloud Run job revision's image and env were not inspected (`gcloud run jobs describe` was not run; the budget was one logging query). Image contents are inferred from the Dockerfile plus its build-time digest gate; the job env is inferred from `deploy.yml`, which could have been edited out-of-band.
- Where `panchanga_daily_writer.py` and the 2026-09-07 L1 build actually ran is not proven. The bit-exact Moshier match shows "no Swiss path in effect"; a laptop without `SE_EPHE_PATH` would give the same values.
- The Swiss C-library behaviour was reproduced on macOS/arm64 with the production pyswisseph pin, not inside the Linux image.
- Only the native chart's Moon and Sun (lahiri) were tested for L1; other ayanamshas, bodies and charts, and `ga_sade_sati`, `ka_sangam`, `ka_kshetra`, `ph_muhurta` outputs were not compared against both backends (inferred from the mechanism).
- The realised thread interleaving in production runs was not observed; sections 1.4 and 6 describe what is possible and, for `ka_vighnakara`, what is deterministic within one writer.
- `ka_vighnakara` stored values cannot discriminate the backend (2-decimal rounding), so its Moshier status is inferred.
- `ga_tajaka`'s Moshier-range error text is not discriminating (section 4.5).
- No attempt was made to quantify downstream boundary flips; the arcsec-level figures are from sampled dates only.
