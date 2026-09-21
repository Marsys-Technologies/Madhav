# Domain H — Hub and invalidation hazards

Pure static-code-reading packet (no DB access; `platform/python-sidecar` is repo root for all
paths below unless stated otherwise). Task: for each of 7 named shared modules, confirm/correct
the claimed importer set with file:line evidence, state what editing the hub invalidates, and
determine whether the campaign's environment can actually *detect* a hub edit as invalidating
dependent writers' builds — or whether that is a blind spot.

---

## 1. `pipeline/transit_search.py`

Found at `platform/python-sidecar/pipeline/transit_search.py`. Its own docstring (lines 4–7)
self-declares importers as `routers/transit_search.py`, `services/ka_gochara/service.py`,
`services/ka_gochara/writer.py`. That self-declaration is **stale**: `services/ka_gochara/writer.py`
does not exist (only `services/ka_gochara/service.py` and `services/ka_gochara/__init__.py` are
present — the actual `WriterBase` subclass for the `ka_gochara` asset lives at
`pipeline/orchestrator/writers/ka_gochara.py`, a different file). Minor doc-drift finding, not
load-bearing for the invalidation question, noted for hygiene.

| Importer file:line | Asset it belongs to |
|---|---|
| `routers/transit_search.py:16` (`from pipeline.transit_search import (...)`) | live-compute sidecar route `/api/compute/transit_search`, wired in `main.py:92-93` |
| `services/ka_gochara/service.py:29` (`from pipeline.transit_search import (...)`) | **ka_gochara** (L3) |
| `services/ka_kshetra/stage0_kinematics.py:746` (`from pipeline.transit_search import MEAN_MOTIONS`, deferred/local import) | **ka_kshetra** (L3) |
| `services/ka_sangam/engine.py:1087` (`from pipeline.transit_search import find_aspect_events`) | **ka_sangam** (L3) |
| `services/ka_sangam/engine.py:1363` (`from pipeline.transit_search import search_long_horizon`) | **ka_sangam** (L3) |
| `pipeline/orchestrator/writers/bg_sky_calendar.py:380,411,560,565,578` (`from pipeline.transit_search import find_ingress_events / find_station_events / _get_planet_pos / find_conjunction_events`) | **bg_sky_calendar** (L0, FROZEN writer) |
| `tests/test_swiss_state_boundary.py:20` | test-only, asserts the Swiss-ephemeris state-lock boundary on this exact module |

**Confirmed as claimed, all four:** Kshetra, Sangam, the gochara family (ka_gochara), and the
frozen L0 writer `bg_sky_calendar` all import `pipeline/transit_search.py` directly, with
file:line evidence above. `ka_gochara_sweep` (retired) and `ka_gochara_resonance` were checked
and do **not** import it directly.

**Editing this hub invalidates:** `ka_gochara`, `ka_kshetra`, `ka_sangam`, and `bg_sky_calendar`.
The L0 dependency is the sharpest hazard in this hub: `bg_sky_calendar` is FROZEN
(`ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md`) and sits upstream of the whole build graph, so a
transit_search change made in service of an L3 Kāla need has L0 blast radius by construction —
any edit here needs L0 re-validation, not just an L3 one.

---

## 2. `services/ka_dasha_kala/`

Found at `platform/python-sidecar/services/ka_dasha_kala/` (`service.py`, `tree_walk.py`,
`writer.py`, `eligibility.py`, `__init__.py`).

| Importer file:line | Asset it belongs to |
|---|---|
| `pipeline/orchestrator/writers/ka_dasha_kala.py:13` (`from services.ka_dasha_kala.writer import KaDashaKalaWriter`) | **ka_dasha_kala** itself (writer registration) |
| `pipeline/orchestrator/writers/ka_kshetra.py` → `services/ka_kshetra/stage0_kinematics.py`, `services/ka_kshetra/stage3_clocks.py` (both files import from `services.ka_dasha_kala`, confirmed by `grep -rln`) | **ka_kshetra** (L3) |
| `pipeline/orchestrator/writers/ka_sangam.py:35` (`from services.ka_dasha_kala.service import KaDashaKalaService`) | **ka_sangam** (L3) |
| `pipeline/orchestrator/writers/ka_taranga.py` (imports `services.ka_dasha_kala`, confirmed by `grep -rln`) | **ka_taranga** (L3) |
| `pipeline/orchestrator/writers/ka_avadhi.py:29` (`from services.ka_dasha_kala.tree_walk import ALL_DASHA_SYSTEMS`) | **ka_avadhi** (L3) |
| `services/ph_nimitta/dasha_consensus.py:106,163` (`from services.ka_dasha_kala.service import KaDashaKalaService`, both deferred/local imports) | **ph_nimitta** (**L4 Phala** — cross-layer) |
| `services/kala_permission/permission.py` (imports `services.ka_dasha_kala`, confirmed by `grep -rln`) | `kala_permission` service (consumed by `routers/permission_curve.py`) |
| `pipeline/orchestrator/service_probes.py:940-952` | orchestrator health-probe registration for `ka_dasha_kala` |

**Confirmed as claimed:** the L4 cross-layer dependency is real — `services/ph_nimitta/dasha_consensus.py`
imports `KaDashaKalaService` at two call sites (lines 106 and 163), both inside function bodies
(deferred imports). This means **`ph_nimitta` (L4, sealed-and-closed layer) has a live runtime
dependency on an L3 Kāla service module**, not merely on `ka_dasha_kala`'s DB output rows. An
edit to `services/ka_dasha_kala/service.py`'s `KaDashaKalaService` public surface can break L4
Phala even though L4 is nominally closed and L3 is the layer under active campaign elevation.

**Editing this hub invalidates:** `ka_dasha_kala` (self), `ka_kshetra`, `ka_sangam`, `ka_taranga`,
`ka_avadhi` (all L3), and **`ph_nimitta`** (L4) — the widest cross-layer blast radius of the 7
hubs audited.

---

## 3. `services/ka_temporal/`

Found at `platform/python-sidecar/services/ka_temporal/` (`date_resolver.py`, `__init__.py`).

| Importer file:line | Asset it belongs to |
|---|---|
| `pipeline/orchestrator/writers/ka_yojaka.py:41` (`from services.ka_temporal import (...)`) | **ka_yojaka** (L3) |
| `pipeline/orchestrator/writers/ka_avadhi.py` (imports `services.ka_temporal`, confirmed by `grep -rln`) | **ka_avadhi** (L3) |
| `pipeline/orchestrator/writers/ka_vighnakara.py:29` (`from services.ka_temporal import (...)`) | **ka_vighnakara** (L3) |
| `pipeline/orchestrator/writers/ka_kalasutra.py:16` (`from services.ka_temporal import (...)`) | **ka_kalasutra** (L3) |
| `pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py:702` (`from services.ka_temporal.date_resolver import resolve_birth_date`) | **ka_gochara_v3_century_materialize** (L3) |
| `services/taranga_kernel/promise.py` (imports `services.ka_temporal`, confirmed by `grep -rln`) | feeds **ka_taranga** transitively via the `taranga_kernel` hub (§7) |

**Editing this hub invalidates:** `ka_yojaka`, `ka_avadhi`, `ka_vighnakara`, `ka_kalasutra`,
`ka_gochara_v3_century_materialize` directly, plus **`ka_taranga`** transitively (via
`taranga_kernel/promise.py` → `ka_temporal`). That transitive edge means `ka_temporal` and
`taranga_kernel` are not independent hubs for blast-radius purposes — see §9.

---

## 4. `services/ka_graha_sancara/engine.py`

Found at `platform/python-sidecar/services/ka_graha_sancara/engine.py`, paired with the writer
at `pipeline/orchestrator/writers/ka_graha_sancara.py`.

| Importer file:line | Asset it belongs to |
|---|---|
| `pipeline/orchestrator/writers/ka_graha_sancara.py:108` (deferred `from services.ka_graha_sancara.engine import get_ephemeris, _EphemerisCache`) | **ka_graha_sancara** itself |
| `pipeline/orchestrator/service_probes.py:608,617` | orchestrator health-probe registration |
| `services/ka_moorti_nirnaya/writer.py:49` (`from services.ka_graha_sancara.engine import NAKSHATRAS, NAK_SIZE_DEG, SIGNS`) | **ka_moorti_nirnaya** (L3) |
| `services/ka_sudarshana_varsha/writer.py:34` (`from services.ka_graha_sancara.engine import SIGNS`) | **ka_sudarshana_varsha** (L3) |
| `services/ka_kota_chakra/writer.py:56` (`from services.ka_graha_sancara.engine import ALL_GRAHAS, NAKSHATRAS, NAK_SIZE_DEG`) | **ka_kota_chakra** (L3) |
| `services/ka_vedha_gochara/writer.py:60` (`from services.ka_graha_sancara.engine import ALL_GRAHAS, NAKSHATRAS, NAK_SIZE_DEG, SIGNS`) | **ka_vedha_gochara** (L3) |
| `pyjhora_adapter/transits.py:74` (deferred `from services.ka_graha_sancara.engine import get_ephemeris`) | external-adapter compute path, not an asset writer per se |
| `brahmagyan/phala/muhurta.py:729` (deferred `from services.ka_graha_sancara.engine import get_ephemeris`) | **L4 Phala** (`muhurta` compute path) — a second cross-layer hub edge, alongside `ka_dasha_kala`'s |

**Note:** `tests/test_migration_676_muhurta_seva_depends_on.py` documents that `ka_muhurta_seva`'s
`depends_on` array *used to* incorrectly declare `{ka_graha_sancara}` as a data dependency and
was corrected by migration 676 — i.e., there is a documented prior instance of exactly the
"is this a code-import hub or a real data DAG edge" confusion this packet is auditing. Worth
flagging: that migration fixed one declared-DAG false edge, but says nothing about the *code*
import edges enumerated above, all of which remain real and undeclared in the DAG (see §8).

**Editing this hub invalidates:** `ka_graha_sancara` (self), `ka_moorti_nirnaya`,
`ka_sudarshana_varsha`, `ka_kota_chakra`, `ka_vedha_gochara` (all L3), and the `muhurta` compute
path under `brahmagyan/phala/` (L4).

---

## 5. `services/gochara_grammar/` and `services/gochara_intensity/`

Both found under `platform/python-sidecar/services/`. Treating together since every real
importer of one is entangled with the other (both feed the gochara permission-curve machinery).

| Importer file:line | Asset it belongs to |
|---|---|
| `routers/permission_curve.py:52-55` (`from services.gochara_grammar import dasha_data, resonance_map`; `from services.gochara_intensity.enrichment import enrich_targets`; `from services.gochara_intensity.permission import (...)`) | `permission_curve` sidecar route |
| `pipeline/orchestrator/writers/ka_gochara.py:102-103` (`from services.gochara_grammar import resonance_map as RM`; `from services.gochara_intensity._dbutil import savepoint_scope`) | **ka_gochara** (L3) |
| `services/ka_gochara_sweep/sweep.py:118-124` (`from services.gochara_intensity import compute_lambda_e, compute_lambda_e_series, gather_configuration_sentences`; `from services.gochara_intensity.engine import fetch_temporal_shape`; `from services.gochara_intensity.enrichment import enrich_targets`; `from services.gochara_intensity._dbutil import savepoint_scope`) | **ka_gochara_sweep** — **RETIRED, protected history, outside the 22-identity denominator, never rebuilt** per CLAUDE.md §E. Still a live import edge in source even though the asset is frozen/retired. |
| `services/ka_vedha_gochara/writer.py:73-74` (`from services.gochara_grammar.sarvatobhadra import _vedha_pairs_from_db, opposite_nakshatra_id`; `from services.gochara_grammar import citations as C`) | **ka_vedha_gochara** (L3) |

**Explicit guard found (I2 constraint):** `pipeline/orchestrator/writers/ka_gochara_v3_century_materialize.py:238,314,898`
and its test `pipeline/orchestrator/writers/tests/test_w34_century_horizon.py:69-72` **enforce a
zero-import rule** — `ka_gochara_v3_century_materialize` (and `scripts/kala_admission/w41-w45`
weight-fitting/ablation scripts) must have **zero imports** from `gochara_grammar/*`,
`gochara_intensity/*`, or `ka_gochara_sweep/*`, with a regex-based CI test enforcing it. This is
the one hub-boundary in the whole audit that has an automated static guard against accidental
coupling — worth calling out as the positive counter-example to the rest of this packet's
findings.

**Editing `gochara_grammar` or `gochara_intensity` invalidates:** the `permission_curve` route,
**ka_gochara**, **ka_gochara_sweep** (retired but still source-coupled — a change here could
silently alter what the retired writer *would* produce if ever re-run, even though it never is),
and **ka_vedha_gochara**. `ka_gochara_v3_century_materialize` is explicitly and verifiably immune
(I2 guard).

---

## 6. `services/kala_trigger/`

Found at `platform/python-sidecar/services/kala_trigger/trigger.py`.

| Importer file:line | Asset it belongs to |
|---|---|
| `pipeline/orchestrator/writers/ka_sangam.py:38` (`from services.kala_trigger.trigger import compute_trigger_currents, compose_with_ka_sangam`) | **ka_sangam** (L3) |
| `scripts/kala_admission/currents.py:87` | admission-cycle tooling, not a live asset writer |

**Reverse-dependency note (near-miss circularity, documented in source):** `services/kala_trigger/trigger.py:57`
itself imports from `services.ka_sangam.engine`, and `services/ka_sangam/engine.py:315` contains
an explicit comment — "Structurally identical to `services.kala_trigger.trigger.house_from_moon`
... duplicated ... to avoid a reverse import (kala_trigger already imports from this module)" —
i.e. the codebase already hit the circular-import hazard here once and worked around it by
duplicating a function rather than by having `ka_sangam.engine` import back from
`kala_trigger.trigger`. This is a fragile boundary: `kala_trigger` is simultaneously a hub
consumed by `ka_sangam`'s writer AND a consumer of `ka_sangam`'s own `engine.py` — the two
files are tightly coupled in both directions, just not via an actual Python circular import.

**Editing this hub invalidates:** `ka_sangam` (the only asset writer importing it) — but because
of the reverse coupling above, an edit to `services/ka_sangam/engine.py` (not itself one of the
7 named hubs, but a de facto second hub) can equally invalidate `kala_trigger`'s own logic
(`compute_trigger_currents`, `compose_with_ka_sangam`, `guru_shani_double_transit`, etc.),
which loops back into ka_sangam. Effectively a two-hop, same-asset invalidation loop.

---

## 7. `services/taranga_kernel/`

Found at `platform/python-sidecar/services/taranga_kernel/` (`kernel.py`, `promise.py`,
`__init__.py`).

| Importer file:line | Asset it belongs to |
|---|---|
| `pipeline/orchestrator/writers/ka_taranga.py:37-39` (`from services.taranga_kernel.kernel import GRAHA_DOMAINS, harmonic_mean, month_range`) | **ka_taranga** (L3) — sole asset-writer importer |
| `tests/l3/test_taranga_kernel_extraction.py:158-160` | test literally asserts `"from services.taranga_kernel.kernel import" in src` inside the writer — i.e. CI enforces that `ka_taranga` delegates to this module rather than reimplementing it inline |

`services/taranga_kernel/promise.py` itself imports `services.ka_temporal` (confirmed in §3),
so this "hub" is single-writer today (only `ka_taranga` imports it directly) but sits in a
two-level chain: `ka_temporal` → `taranga_kernel` → `ka_taranga`.

**Editing this hub invalidates:** `ka_taranga` only, directly. Its narrowness relative to the
other 6 hubs is real — `taranga_kernel` reads more like an extraction-for-testability module for
one writer than a genuine multi-asset hub, and the CI test at `test_taranga_kernel_extraction.py`
exists specifically to keep that extraction honest (regression-guard against inlining the logic
back into the writer, which would defeat the whole reason it was pulled out).

---

## 8. `_local_import_files` / `get_writer_source_hash` closure behavior

Searched `_local_import_files` — the only definitions/call sites are in
`platform/python-sidecar/pipeline/orchestrator/asset_runner.py:335-364` (definition) and
`:390` (recursive call site inside `_writer_source_files`).

**What it actually does**, read from `asset_runner.py:335-401`:

1. `_local_import_files(path)` (`:335-364`) parses one file with `ast.parse` (no execution — pure
   static AST walk) and collects every `ast.Import` / `ast.ImportFrom` node **anywhere in the
   file**, including inside function bodies (deferred imports) — `ast.walk` recurses the whole
   tree, not just module level. For each import target, it also speculatively adds
   `f"{target}.{alias.name}"` (handles the `from package import submodule_or_symbol` pattern).
   Each candidate module string is resolved to a real file via `_local_module_path` (`:308-319`),
   which only succeeds for modules that map to an actual `.py` file or package `__init__.py`
   under `_SIDECAR_ROOT` — third-party/stdlib imports resolve to `None` and are dropped.
2. `_writer_source_files(paths)` (`:367-401`) starts from a writer's **declared** source path(s),
   then does a **breadth-first, deduplicated, transitive closure walk**: pop a file, hash-track it
   (`seen` set on resolved absolute path), and push every local import file `_local_import_files`
   found for it back onto the `pending` queue (`:390`). This repeats until the queue is empty —
   i.e. it **is** a full transitive closure over local imports, not a one-level/shallow scan, and
   it **does** follow deferred (in-function) imports because `ast.walk` finds them regardless of
   nesting.
3. `get_writer_source_hash(asset_id)` (`:404-413`) then hashes the sorted, deduplicated closure
   deterministically (path length + bytes, path content + bytes) into one SHA-256 digest.

**Confirmed against real hub examples by content, not just reading the algorithm:** for
`ka_gochara`, `_writer_source_files` starting from its declared writer path would walk into
`services/gochara_grammar` and `services/gochara_intensity` because
`pipeline/orchestrator/writers/ka_gochara.py:102-103` has literal `from services.gochara_grammar
import resonance_map` / `from services.gochara_intensity._dbutil import savepoint_scope` — both
resolve to real files under `_SIDECAR_ROOT`, so both hub files are included in `ka_gochara`'s
hash. The same reasoning applies to every import edge tabulated in §1–§7: they are all
`ast`-visible `Import`/`ImportFrom` statements (module-level or deferred), so they are all inside
this closure.

**Where the hash is actually consumed** (this is the part that determines whether detection
translates into real invalidation):

- `pipeline/orchestrator/provenance_inventory.py:23-31` builds a checked-in JSON artifact
  (`src/generated/nirmana-writer-digests.json`) mapping every registered `asset_id` to
  `get_writer_source_hash(asset_id)`. `--check` mode (`:41-49`) fails CI if the checked-in file
  doesn't match a freshly recomputed one — this **is** a real, working staleness detector: if you
  edit `pipeline/transit_search.py`, the digests for `ka_gochara`, `ka_kshetra`, `ka_sangam`, and
  `bg_sky_calendar` all change, and CI's `--check` fails until the inventory is regenerated. This
  forces a human/reviewer to notice which asset digests moved.
- `pipeline/orchestrator/runner.py:374-390` (`_verify_sidecar_code_matches_manifest`) compares, at
  dispatch time, the *live* `get_writer_source_hash(asset_id)` computed inside the running sidecar
  process against `frozen.expected_code_digests[asset_id]` baked into the dispatch manifest by the
  web planner. A mismatch raises `ValueError("sidecar code digest does not match dispatch
  manifest for asset {asset_id}")` — this is a **hard abort**, preventing a code-skewed sidecar
  image from executing a build under a stale/incorrect digest assumption.

**The precise blind spot — read exactly what these two consumers do NOT do:**

Neither `provenance_inventory.py`'s CI check nor `runner.py`'s dispatch-time skew guard **marks
any already-built DB row as stale, or schedules a rebuild of the affected asset**. They are both
*code-identity integrity* gates (is the digest the code should produce the digest that's checked
in / the digest the dispatch manifest expects), not *data-freshness* gates. Contrast this with
`compute_downstream_closure` (`asset_runner.py:118-133`), which **is** a real data-freshness
mechanism — a recursive SQL query over `asset_registry.depends_on` (`text[]`) that finds every
asset transitively downstream of a given `asset_id` and (per the `_stale_mark_lock` comment at
`:28`, "Serializes compute_downstream_closure + stale-mark UPDATE across worker threads") drives
an actual stale-mark UPDATE against those downstream assets when an upstream asset's data
changes.

**Why that matters here:** `compute_downstream_closure` only ever sees `asset_registry` rows —
i.e. it is blind to any module that is not itself a registered `asset_id` with a `depends_on`
edge. None of the 7 hubs audited in this packet (`transit_search`, `ka_dasha_kala` as a *module*,
`ka_temporal`, `ka_graha_sancara` as a *module*, `gochara_grammar`, `gochara_intensity`,
`kala_trigger`, `taranga_kernel`) are themselves registered assets with DAG edges pointing at
their consumers for a **code** change — `ka_dasha_kala` and `ka_graha_sancara` *are* registered
assets, so a **data** change to their own output rows correctly cascades via
`compute_downstream_closure`, but a **code-only** change to, say, `services/ka_dasha_kala/eligibility.py`
that doesn't happen to change `ka_dasha_kala`'s own row output has no `depends_on`-driven
propagation path to `ka_kshetra`/`ka_sangam`/`ka_taranga`/`ka_avadhi`/`ph_nimitta` at all — those
sibling writers' *existing DB rows* would sit unflagged, while only the code-digest artifact
(requiring a human to read a CI diff and manually decide to trigger rebuilds) would notice
anything changed.

**Net finding:** hub edits **are** correctly detected as a *code-identity* change (no writer can
silently ship a stale hash — the CI inventory check and the dispatch-time skew guard both close
that door), but there is **no automated bridge from "this hub's digest changed" to "these N
sibling `ka_*` assets' DB rows are now stale and should be rebuilt."** That bridge is exactly the
kind of judgment call this audit packet had to perform by hand (grep + read). The environment
correctly prevents you from *running with mismatched code*; it does not tell you, on its own,
*which already-built data needs to be re-run* after a hub edit.

---

## 9. Combined blast radius

Assets depending on 2+ of the 7 named hubs (or a hub-of-a-hub, per the transitive chains found
above):

| Asset | Hubs it depends on | Evidence |
|---|---|---|
| **ka_gochara** | `pipeline/transit_search.py` (via `services/ka_gochara/service.py:29`) + `gochara_grammar` + `gochara_intensity` (both via `pipeline/orchestrator/writers/ka_gochara.py:102-103`) | Triple-hub — the single widest same-layer blast radius found. Editing *any one* of transit_search, gochara_grammar, or gochara_intensity requires re-validating `ka_gochara`. |
| **ka_sangam** | `pipeline/transit_search.py` (`services/ka_sangam/engine.py:1087,1363`) + `services/ka_dasha_kala` (`pipeline/orchestrator/writers/ka_sangam.py:35`) + `services/kala_trigger` (`pipeline/orchestrator/writers/ka_sangam.py:38`) | Triple-hub, plus the kala_trigger↔ka_sangam.engine reverse-coupling noted in §6 makes ka_sangam a two-hop self-loop risk as well. |
| **ka_kshetra** | `pipeline/transit_search.py` (`services/ka_kshetra/stage0_kinematics.py:746`) + `services/ka_dasha_kala` (`stage0_kinematics.py`, `stage3_clocks.py`) | Two-hub. Editing either transit_search or ka_dasha_kala invalidates ka_kshetra independently. |
| **ka_avadhi** | `services/ka_dasha_kala` (`pipeline/orchestrator/writers/ka_avadhi.py:29`) + `services/ka_temporal` (imports confirmed) | Two-hub. |
| **ka_taranga** | `services/ka_dasha_kala` (imports confirmed) + `services/taranga_kernel` (`pipeline/orchestrator/writers/ka_taranga.py:37-39`) + transitively `services/ka_temporal` (via `taranga_kernel/promise.py`) | Effectively triple, once the `ka_temporal → taranga_kernel` chain is counted. |
| **ka_vedha_gochara** | `services/ka_graha_sancara` (`services/ka_vedha_gochara/writer.py:60`) + `gochara_grammar` (`writer.py:73-74`) | Two-hub. |
| **ph_nimitta (L4)** | `services/ka_dasha_kala` (`services/ph_nimitta/dasha_consensus.py:106,163`) + `services/ka_graha_sancara` (`brahmagyan/phala/muhurta.py:729`, same L4 layer, different file) | Two cross-layer hub edges land in L4 Phala independently (different files, same layer) — L4 is nominally CLOSED/sealed, but both edges mean an L3 hub edit can require L4 re-validation despite L4's seal. |

**Takeaway:** `ka_gochara` and `ka_sangam` are the two highest-risk single assets in the L3
elevation campaign purely from a hub-coupling standpoint — each depends on 3 of the 7 named
hubs, meaning roughly 3x the number of unrelated-looking commits could legitimately require
re-validating them, and neither dependency is visible in `asset_registry.depends_on` (per §8,
none of the 7 hubs are registered assets).

---

## Verdict: NEEDS DECISION

**Evidence for the verdict:**

- **What works:** the code-identity side is genuinely solid. `_local_import_files` /
  `get_writer_source_hash` (`asset_runner.py:335-413`) is a real, correctly-implemented
  transitive closure over local imports (including deferred/in-function imports), and it is
  wired into two live gates — a CI staleness check on a checked-in digest inventory
  (`provenance_inventory.py`) and a hard dispatch-time abort on code/manifest skew
  (`runner.py:374-390`). A hub edit cannot silently ship under an unchanged hash; that specific
  failure mode (§N.8 "earned signal" / a status with no real detector behind it) does **not**
  apply here — the detector is real and is exercised by CI.
- **What is missing:** there is no automated path from "hub digest changed" to "these N sibling
  `ka_*` writers' already-built DB rows are stale, go rebuild them." `compute_downstream_closure`
  (`asset_runner.py:118-133`) is the only DB-row staleness mechanism found, and it is scoped
  strictly to `asset_registry.depends_on` edges between registered assets — none of the 7 hubs
  audited here are registered assets, so none of their edit-time blast radii (§1–§7, §9) are
  visible to that mechanism at all. The bridge from code-digest-changed to data-is-stale is a
  manual, human, grep-and-read step — exactly this audit packet's method.
- Two of the 7 hubs (`ka_dasha_kala`, `ka_graha_sancara`) also *are* registered assets in their
  own right, so their **data** dependents are correctly covered by `compute_downstream_closure`
  when *their own output rows* change — but a **code-only** change to a helper file inside those
  packages (e.g. `services/ka_dasha_kala/eligibility.py`) that doesn't alter `ka_dasha_kala`'s own
  emitted rows has no `depends_on`-driven propagation to its code-importing siblings
  (`ka_kshetra`, `ka_sangam`, `ka_taranga`, `ka_avadhi`, `ph_nimitta`) either.

This is not a straightforward READY (there is a real, evidenced gap between "code-identity
detected" and "data staleness propagated") nor a flat NOT READY (the code-identity gates that do
exist are genuinely correct and CI-enforced, not theater). The decision the campaign owner needs
to make is whether the existing manual-audit discipline (this packet, and presumably its sibling
packets) is an acceptable standing substitute for an automated hub→dependent-asset staleness
bridge, or whether `asset_registry` should grow a way to declare non-asset code hubs so
`compute_downstream_closure` can see them.
