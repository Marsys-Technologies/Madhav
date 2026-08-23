"""
Per-asset plan-of-action derivation for the Nirmāṇa elevation programme.

One function, `derive(asset_row, facts) -> AssetPlan`, turns grounded measurements into a
specific three-dimension plan for ONE asset:

  1. correctness   — what makes this asset's data correct and complete, and how we prove it
  2. rebuild_time  — how its rebuild gets faster / interruption-safe
  3. architecture  — how it is re-architected and aligned to the catalogue contract

plus a quantified `benefit`. The rules are deliberately data-driven: every sentence is keyed
off a measured fact about *this* asset (rows vs floor, runtime, substep key, fan-out, tier,
consumers, violations), never a tier template alone. Used by build_asset_control_workbook.py
for both the workbook and the plan file, so the two cannot disagree.
"""
from __future__ import annotations

import dataclasses
import json
import pathlib

# --------------------------------------------------------------------- §19 profile ledger
# NIRMANA_ELEVATION_PLAN_v4_0.md §19.4 step 1 — "no measured hotspot, no optimization" —
# and §15's named correction: an asset that has not actually been profiled must read as
# UNKNOWN, not as fine. The profiling / output-identity harness is M3 (§14.1); until it
# runs, nothing here is profiled and every §19 field below is an honest NULL.
# Binding: ADHIKARIN ruling D-8; CHARTER H4; CLAUDE.md §N.8 (earned signal).
#
# This is a real detector, not a stub. M3 writes one record per profiled asset into
# `asset_profiles.json` beside this file, and EVERY §19 field is read from that record.
# The file is absent today, so the detector's verdict is "not profiled" for every asset —
# a verdict it produces from a missing record, not a default it assumes. The moment M3
# writes a record, the same code path emits the measured value instead.
#
# Record shape (M3 writes it; any key omitted stays null):
#   "<asset_id>": {
#     "profiled_at":        ISO8601 — when the profile run happened
#     "profile_evidence":   what was instrumented (run id, EXPLAIN ANALYZE, substep timings)
#     "bound_class":        round-trip | I/O | CPU | algorithmic | not-a-build  (§19.4 step 3)
#     "hotspot":            the measured dominant cost, named                   (§15)
#     "rows":               rows the profiled run actually produced
#     "seconds":            wall clock of the profiled run
#     "rows_per_sec":       measured rows/sec (omit to derive from rows / seconds)
#     "technique_proposed": from §19.5's catalogue
#     "technique_applied":  from §19.5's catalogue
#     "target":             derived from what the hotspot could plausibly become (§19.6)
#     "speedup_achieved":   measured delta, or "examined: already efficient" + its measurement
#     "identity_proof":     digest-equal | tolerance-equal(declared) | sorted-digest-equal |
#                           none                                                (I18, §19.3)
#     "timeout_derived_from_telemetry": true when this asset's writer_timeout_seconds was
#                           derived from measured runtime (§8.6 stage 2) rather than hand-set
#   }
PROFILE_PATH = pathlib.Path(__file__).resolve().parent / 'asset_profiles.json'

#: The literal this programme uses for "no detector produced a value here". Rendered as-is
#: in both the workbook and the plan markdown so a null can never be mistaken for a blank
#: cell that someone forgot to fill in.
NULL = 'null'


def load_profiles(path=None) -> dict:
    """Read the M3 profile ledger. Absent file -> {} -> every §19 field reads null."""
    p = pathlib.Path(path) if path else PROFILE_PATH
    if not p.exists():
        return {}
    try:
        d = json.loads(p.read_text())
    except (ValueError, OSError):
        return {}
    return {k: v for k, v in d.items() if isinstance(v, dict) and not k.startswith('_')}


PROFILES = load_profiles()

# Substep partition key per writer, read from the writers' plan_substeps (2026-08-23 survey).
PARTITION_KEY = {
    'bg_reference': '{system}:{ayanamsha}',
    'bg_gochara_arcs': 'body',
    'bg_muhurta_lattice': 'year:{year}',
    'bo_laksana': 'aya_{ayanamsha}',
    'bo_laksana_rerank': 'aya_{ayanamsha}',
    'bo_samskara': 'aya_{ayanamsha}',
    'ga_ayurdaya': 'ayanamsha_{aya}', 'ga_dashas': '{system}:{aya}', 'ga_nakshatra': 'ayanamsha:{ay} + cross_ayanamsha',
    'ga_condition': 'ayanamsha_{id}', 'ga_sensitive_degree': 'ayanamsha_{aya}', 'ga_structural': 'ayanamsha_{id}',
    'ga_transit_anchors': 'ayanamsha_{aya}', 'ga_sensitive': 'ayanamsha:{aya}', 'ga_vastu': 'ayanamsha_{id}',
    'ga_medical': 'ayanamsha_{aya}', 'ga_yoga': 'ayanamsha_{a}', 'ga_prashna': 'ayanamsha_{id}',
    'ga_vichara': 'ayanamsha_{a}', 'ga_vargas': 'ayanamsha',
    'ka_gochara': 'event_class', 'ka_gochara_v3_century_materialize': '{event_class}::{decade}',
    'ka_sangam': 'near + lifetime:{i}', 'ka_kshetra': 'stage{n}:{event_class}:{slice}',
    'ka_gochara_sweep': '{event_class}:year:{idx}',
    'mi_darshana': 'insight_units | embeddings', 'mi_pariksha': 'retrodiction | control_windows | …(7)',
    'mi_pramana': 'match | score | …(3)',
}
# Assets whose output is prose / narration and therefore falls under §N.7 (narration fidelity).
NARRATIVE = {'ka_bhavishya_lekha', 'ka_kala_darshana', 'ph_phaladesa', 'mi_darshana', 'bo_chart_gestalt',
             'bo_cdlm_summary', 'ka_jivana_parva', 'bo_samvada', 'ph_pratikara', 'ph_nimitta'}
# Writers that produce embeddings (deterministic transform — permitted by §N.4).
EMBEDDING = {'bg_texts', 'bo_samskara', 'mi_darshana', 'bg_text_index'}
# Shared target tables with legitimate co-writers (table -> writer count). §3.3 of the plan.
CO_WRITTEN = {'bodha_msr_signals': 7, 'chart_facts': 5, 'brahma_class_priors': 2, 'classical_text_chunks': 2}

LAYER_PREFIX = {'L0': 'bg_', 'L1': 'ga_', 'L2': 'bo_', 'L3': 'ka_', 'L4': 'ph_', 'L5': 'mi_'}

# Layer -> rung, per plan §8.4. Rung follows LAYER, not domain — the two shared L5 assets
# (mi_kula, mi_vistara) are domain=shared but rung=R5 (§8.4's own callout; §3's own note).
RUNG_BY_LAYER = {'L0': 'R0', 'L1': 'R1', 'L2': 'R2', 'L3': 'R3', 'L4': 'R4', 'L5': 'R5'}


def _timeout_source(value, column_default, prof) -> tuple:
    """
    §15 vocabulary: `registered` | `telemetry-derived` | `default`.

    PARIKSAKA verdict V-2: the previous rule was `value is not None -> 'registered'`, and
    because `asset_registry.writer_timeout_seconds` is NOT NULL DEFAULT 600, that made the
    field a constant — 128/128 'registered', with 'default' and 'telemetry-derived'
    unreachable. A constant wearing the clothes of a measurement (H4 / §N.8).

    The detector now distinguishes the three cases on evidence:

      default          — the value is NULL, or it EQUALS the column default. The column
                         default (600) is also the runner's own fallback
                         (`runner.py:89 _WRITER_TIMEOUT_SECONDS = 600`), so an asset at 600
                         gets exactly the budget it would get if the column had never been
                         written: the two states are indistinguishable at both layers, and
                         calling it 'registered' claims a deliberate act nothing evidences.
                         Migration 529's own header records this happening
                         (`INSERT passed writer_timeout_seconds = NULL, but that column is
                         NOT NULL (default 600)`).
      registered       — the value differs from the column default, so something set it.
      telemetry-derived— the profile ledger records that the value was derived from measured
                         runtime (§8.6 stage 2 will write this). No such record exists today,
                         so this branch emits nothing yet; it is wired, not decorative.

    Returns (value, basis) — the basis is the evidence the verdict rests on.
    """
    if prof.get('timeout_derived_from_telemetry'):
        return 'telemetry-derived', (
            f"profile ledger records derivation from measured runtime "
            f"({prof.get('profiled_at', 'no timestamp')})")
    if value is None:
        return 'default', 'writer_timeout_seconds is NULL — runner falls back to WRITER_TIMEOUT_SECONDS'
    if column_default is not None and int(value) == int(column_default):
        return 'default', (
            f'{int(value)}s equals the asset_registry column default and the runner fallback '
            f'(_WRITER_TIMEOUT_SECONDS) — indistinguishable from never set')
    if column_default is None:
        return 'registered', f'{int(value)}s set; column default unknown'
    return 'registered', f'{int(value)}s differs from the column default ({int(column_default)}s)'


def _bound_class(is_service: bool, has_writer: bool, prof: dict) -> tuple:
    """
    §19.4 step 3 vocabulary: round-trip | I/O | CPU | algorithmic | not-a-build.

    Classifying the ceiling is a profiling result — EXCEPT `not-a-build`, which D-8 rules is
    "legitimately true for a service asset" and is derivable structurally without profiling.
    Two structural detectors produce it: the asset is a service probe (nothing builds), or no
    writer is registered for it (nothing can build it). Everything else is null until profiled.

    `has_writer` REACHING THIS FUNCTION IS CODE-DERIVED (D-25 part 2a, M0-T22). The logic below
    was always sound; its INPUT used to be `asset_registry.has_writer`, which was wrong on two
    R0 assets, and `not-a-build` EXEMPTS an asset from the §8.3 item 5 efficiency pass
    altogether — so a false `has_writer` walked a genuinely-built asset through the campaign's
    first freeze gate unexamined. The caller now passes the AST @register census's verdict.
    """
    if prof.get('bound_class'):
        return prof['bound_class'], f"profiled {prof.get('profiled_at', 'no timestamp')}"
    if is_service:
        return 'not-a-build', 'service probe — there is no build to measure (structural)'
    if not has_writer:
        return 'not-a-build', 'no registered writer — nothing builds this asset (structural)'
    return NULL, 'not profiled — §19.4 step 1: no measured hotspot, no classification'


def _rows_per_sec(prof: dict) -> tuple:
    """
    §19.4's rows/sec is a measurement of a profiled run, and it is NOT derivable from what
    exists today: `build_run_assets` carries no row count and no chart_id (verified against
    information_schema, 2026-08-23), so the only available quotient would be this chart's
    current table rows over a median taken across every chart that ever built the asset.
    That is an inference, not a measurement, so it stays null.
    """
    if prof.get('rows_per_sec') is not None:
        return prof['rows_per_sec'], f"profiled {prof.get('profiled_at', 'no timestamp')}"
    rows, secs = prof.get('rows'), prof.get('seconds')
    if rows is not None and secs:
        return round(float(rows) / float(secs), 1), (
            f"profiled {prof.get('profiled_at', 'no timestamp')} — {rows} rows / {secs}s")
    return NULL, ('no per-run row count exists (build_run_assets has no rows column) and p50 '
                  'spans all charts — not derivable from current telemetry; M3 profile supplies it')


def derive_v41_columns(aid: str, layer: str, scope: str, tier_letter: str,
                        reg_sub: bool, code_sub: bool, writer_timeout_seconds,
                        med_s, p90_s, wave, has_writer: bool = True,
                        timeout_column_default=None, polluted: bool = False,
                        max_s=None) -> dict:
    """
    NIRMANA_ELEVATION_PLAN_v4_0.md §15 — the per-asset fields, single-chart scope.
    Pure function of facts build_asset_control_workbook.py already gathers (registry row,
    scan_code() signal, build_run_assets timing, the intra-layer wave CTE, the M3 profile
    ledger) — no hardcoded per-asset table, matching the data-driven style of derive() below.

      domain              — shared | chart, from asset_registry.scope
      rung                — R0-R5, from layer (§8.4)
      within-rung wave     — intra-layer topological wave (§8.5), passed in pre-computed
      continuation class   — probe-only (tier S) | resumable-substep (has_substeps, either
                              signal) | restartable-light (single-shot, no substep plan)
      rehearsal partition  — PARTITION_KEY entry if declared; else an explicit n/a reason
      timeout source        — registered | telemetry-derived | default   (V-2 fix, see above)

    and the five §19 ledger fields V-1 found had no emitter at all. Each is read from the M3
    profile record for this asset; with no record they are honest NULLs, which is exactly
    what M0 owes (D-8: "§15 does not ask M0 for measured values; it asks for HONEST NULLS"):

      bound class          — §19.4 step 3; structurally `not-a-build` where that is true
      hotspot              — the measured dominant cost, NULL UNTIL PROFILED (§15, verbatim)
      technique            — §19.5 catalogue, proposed / applied
      target               — §19.6, derived from what the hotspot could plausibly become
      speedup achieved     — measured delta, or "examined: already efficient" + measurement
      identity proof       — I18 / §19.3
      p50 / p90 / rows/sec — the build-cost baseline (§19.4)
    """
    domain = 'shared' if scope == 'global' else 'chart'
    rung = RUNG_BY_LAYER.get(layer, '—')
    is_service = tier_letter == 'S'
    prof = PROFILES.get(aid, {})

    if is_service:
        cont_class = 'probe-only'
    elif reg_sub or code_sub:
        cont_class = 'resumable-substep'
    else:
        cont_class = 'restartable-light'

    pkey = PARTITION_KEY.get(aid)
    if pkey:
        partition = pkey
    elif is_service:
        partition = 'n/a — service probe'
    else:
        partition = 'n/a — single-shot, whole-asset is the unit'

    timeout_src, timeout_basis = _timeout_source(writer_timeout_seconds, timeout_column_default, prof)
    bound, bound_basis = _bound_class(is_service, has_writer, prof)
    rps, rps_basis = _rows_per_sec(prof)

    profiled = 'yes' if prof.get('profiled_at') else 'no'
    hotspot = prof.get('hotspot') or NULL
    tech_p, tech_a = prof.get('technique_proposed'), prof.get('technique_applied')
    if tech_p or tech_a:
        technique = ' / '.join([f"proposed: {tech_p}" if tech_p else 'proposed: ' + NULL,
                                f"applied: {tech_a}" if tech_a else 'applied: ' + NULL])
    else:
        technique = NULL
    target = prof.get('target') or NULL
    achieved = prof.get('speedup_achieved') or NULL
    identity = prof.get('identity_proof') or NULL

    # The basis column is the §N.8 receipt: for every null, WHY it is null; for every value,
    # which detector produced it. A ledger of nulls with no stated reason is the same
    # unearned signal one layer along.
    if profiled == 'yes':
        basis = (f"profiled {prof['profiled_at']}"
                 + (f" — {prof['profile_evidence']}" if prof.get('profile_evidence') else ''))
    else:
        basis = ('NOT PROFILED — the §19 profiling/output-identity harness is M3 (§14.1); '
                 'hotspot, technique, target, achieved and identity proof are null until it runs '
                 '(§19.4 step 1, §15). ')
        basis += f'bound class: {bound_basis}. rows/sec: {rps_basis}.'
    if polluted:
        basis += ' p50/p90 read from telemetry flagged POLLUTED (D-13, unclosed run rows).'

    return {
        'Domain': domain,
        'Rung': rung,
        'Within-Rung Wave': wave,
        'Continuation Class': cont_class,
        'Rehearsal Partition': partition,
        'Timeout Source': timeout_src,
        'Timeout Source Basis': timeout_basis,
        # ---- §19 ledger (V-1: these had no emitter at all) ----
        'p50': _dur(med_s) if med_s is not None else NULL,
        'p90': _dur(p90_s) if p90_s is not None else NULL,
        'p_worst': _dur(max_s) if max_s is not None else NULL,   # distinct key: rec['Worst'] is the Asset Register's own column
        'Rows/sec': rps,
        'Bound Class': bound,
        'Hotspot': hotspot,
        'Technique': technique,
        'Target': target,
        'Speedup Achieved': achieved,
        'Identity Proof': identity,
        'Profiled': profiled,
        'Efficiency Basis': basis,
    }


@dataclasses.dataclass
class AssetPlan:
    correctness: list
    rebuild_time: list
    architecture: list
    benefit: list
    now: str            # one-line "where it stands" summary
    what: str           # one-line description


def _fmt(n):
    return f'{n:,}' if isinstance(n, int) else ('—' if n is None else str(n))


def _dur(s):
    if s is None:
        return ''
    s = float(s)
    return f'{s:.0f}s' if s < 90 else (f'{s/60:.0f}m' if s < 5400 else f'{s/3600:.1f}h')


def derive(a: dict, m: dict) -> AssetPlan:
    """
    a: the assembled asset record (from build_asset_control_workbook.build_rows, pre-plan)
    m: measurement record for this asset from asset_measurements.json (may be empty)
    """
    aid = a['Asset ID']
    lx = a['Layer']
    tier = a['Tier'][0]
    is_service = tier == 'S'
    is_global = a['Scope'] == 'global'
    life = a['Lifecycle']
    viol = set(v for v in (a['Contract Violations'] or '').split('; ') if v)
    cons = int(a['Consumers'] or 0)
    down = int(a['Downstream'] or 0)
    deps = int(a['Deps'] or 0)
    code_sub = a['Substeps (code)'] == 'yes'
    has_writer = bool(a.get('_has_writer', True))
    resume = a['Resume']
    med_s, max_s, p90_s = a.get('_med_s'), a.get('_max_s'), a.get('_p90_s')
    polluted = bool(max_s) and max_s > 48 * 3600   # unclosed run rows — telemetry artefact (D-13)
    succ = a.get('Success %')
    runs = a.get('Runs') or 0
    rows_n = m.get('actual_rows_native')
    rows_a = m.get('actual_rows_abhinandan')
    rows_3 = m.get('actual_rows_chart3')
    floor = m.get('target_floor')
    has_integrity = bool(m.get('integrity_check_sql'))
    tbl = a['Target Table'] or ''
    pkey = PARTITION_KEY.get(aid)
    desc = (m.get('english_description') or a.get('English') or '').strip()
    what = desc.split('. ')[0][:160] if desc else a.get('English', '')

    C, R, A, B = [], [], [], []

    # ---------------------------------------------------------------- NOW
    parts = []
    if is_service:
        parts.append(f"service · global state {a['Global']}")
    elif is_global:
        parts.append(f"global · {a['Global']} · {_fmt(rows_n)} rows" + (f' / floor {_fmt(floor)}' if floor else ''))
    else:
        parts.append(f"native {a['Abhisek (native)']} · abhinandan {a['Abhinandan']} · chart3 {a['Chart 3']}")
        if rows_n is not None:
            parts.append(f'rows {_fmt(rows_n)} / {_fmt(rows_a)} / {_fmt(rows_3)}' + (f' (floor {_fmt(floor)})' if floor else ''))
    if med_s is not None:
        if polluted:
            parts.append(f'median {_dur(med_s)}, p90 {_dur(p90_s)} (recorded worst {_dur(max_s)} is an unclosed-run artefact — D-13)')
        else:
            parts.append(f'median {_dur(med_s)}, worst {_dur(max_s)}')
    if succ is not None and runs >= 10:
        parts.append(f'{succ}% of {runs} attempts complete')
    now = ' · '.join(parts)

    # ---------------------------------------------------------------- 1. CORRECTNESS & COMPLETENESS
    if is_service:
        C.append('Real liveness + correctness probe with an SLO (not just "responds"): exercise one known-answer '
                 'query and compare against a pinned expected value; alert on drift or timeout.')
        if a['Global'] == 'error':
            C.append(f'Currently in error — repair first (Phase 1), then the probe becomes the regression guard.')
    else:
        # integrity check — none exist anywhere today
        if not has_integrity:
            inv = ('row count ≥ floor AND no duplicate natural keys per chart' if not is_global
                   else 'row count = expected volume formula AND no duplicate natural keys')
            if tbl == 'chart_facts':
                inv = 'exactly one row per (chart_id, fact_key) across build_ids; verification_pass_status populated'
            elif tbl == 'bodha_msr_signals':
                inv = 'every constituent_facts_array id resolves to chart_facts.fact_id (§N.5); one row per signal_id per chart'
            elif aid.startswith('ka_gochara') or tbl.startswith('kala_gochara'):
                inv = 'one authoritative generation per chart via kala_gochara_authority; no window with end < start'
            C.append(f'Add `integrity_check_sql` (none exists on any asset today): `{inv}`. Run it as the post-build gate so `lit` is earned, not assumed (§N.8).')
        # floors
        if floor is None and rows_n:
            C.append(f'Set `target_floor` = {_fmt(rows_n)} (achieved on native; floors are aspirational, never fabricated — §N.4).')
        elif floor and rows_n is not None and rows_n < floor:
            C.append(f'Below floor: {_fmt(rows_n)} of {_fmt(floor)} ({100*rows_n/floor:.0f}%). Either the floor is stale (re-measure and reset) or the build is incomplete — decide explicitly, never let the gap sit.')
        # cross-chart completeness
        if not is_global and rows_n is not None and rows_a is not None:
            if rows_n and rows_a and (rows_n / rows_a > 3 or rows_a / rows_n > 3):
                C.append(f'Cross-chart asymmetry ({_fmt(rows_n)} vs {_fmt(rows_a)}): confirm it is chart-driven, not a partial build on one chart.')
            if rows_3 == 0 and (rows_n or 0) > 0:
                C.append('Chart 3 holds zero rows — the rehearsal chart is incomplete for this asset; rebuild there first (Phase 1) so it can serve as the test subject.')
        if rows_n == 0 and not is_global:
            lit_states = [s for s in (a['Abhisek (native)'], a['Abhinandan'], a['Chart 3']) if s == 'lit']
            if lit_states:
                C.append(f'**Unearned `lit`:** throughput says lit on {len(lit_states)} chart(s) while the table holds zero rows — a live §N.8 specimen. The integrity gate (§4.1) must fail this; then decide: empty by design (record in `volume_explanation`, floor 0) or never built (rebuild).')
            else:
                C.append('Zero rows on the native chart. Either the asset is empty by design (record it in `volume_explanation`) or it has never been built — the cockpit must not render this as lit.')
        # layer-specific correctness
        if lx == 'L1' and tbl == 'chart_facts':
            C.append('Verification tier: 80.7% of native chart_facts are `single` (unverified). Add a second derivation path for this writer\'s fact categories so rows earn `two_pass_verified`; emit tiers only via `verification_vocab` constants.')
            C.append('Accretion guard: 15 fact_keys already exist under two build_ids on the native chart. Make the delete-then-insert scope (chart_id × this writer\'s fact_keys) explicit and assert single-row-per-key in the integrity check.')
        if lx == 'L2' and tbl == 'bodha_msr_signals':
            C.append('§N.5: every signal must reference L1 `fact_id`s, never restate values — keep the constituent-facts resolution check (100% on sample today) as a blocking integrity gate. Declare this writer\'s natural-key partition of the shared table so co-writers cannot overwrite each other.')
        if lx in ('L3', 'L4', 'L5') and deps >= 4:
            C.append(f'Derivation ledger: {deps} declared inputs — record which upstream digests each output row was built from (partition receipt) so a wrong answer is traceable to the input that produced it.')
        if aid in NARRATIVE:
            C.append('§N.7 narration fidelity: every sentence restates a cited fact_id it reads, never re-derives; add a golden-value test for the narration layer (verified fact ≠ verified prose).')
        if aid in EMBEDDING:
            C.append('Embeddings are a deterministic transform (permitted). Pin the model id + dimension in the output digest so a model change invalidates correctly.')
        if aid.startswith('ka_gochara_v3') or aid == 'ka_gochara':
            C.append('F-52 consequence: every materialized v2 row is stale under the live scoring signature and no rebuild has been dispatched — rematerialize under the determinism harness, or mark stale honestly in the UI.')
        if aid == 'ka_gochara_sweep':
            C.append('RETIRED and unrebuildable: no registered writer. Correctness = the verified 2026-08-23 snapshot; chart 3 still serves these v1 rows (no authority row). Record `data_disposition = RETAINED_AS_CAPITAL`.')
        if aid == 'ka_kshetra':
            C.append('DHARA engine (analytic) replaced the sampled engine mid-August; `_RESUME_VERSION` is at 7. Add a build-twice determinism check at the stage level — the content hash (F-149) already exists, so compare digests across two clean builds.')
        if aid == 'bg_ephemeris_engine':
            C.append('Red since 2026-06-18: missing Swiss Ephemeris file in the container image. Fix the image, then the probe above guards it.')
        if aid in ('mi_seva', 'mi_vistara') and rows_n == 0:
            C.append('Structural-mode L5 asset: zero rows is by design until outcome data accrues. Record that in `volume_explanation` and set `target_floor = 0` so the cockpit renders "0 rows (by design)" rather than dormant.')

    # ---------------------------------------------------------------- 2. REBUILD TIME
    if is_service:
        R.append('Not a build; nothing to speed up. Exclude from build plans and ETA math.')
    elif is_global:
        R.append('Built once, reused by every chart. Publish `substrate_version` + output digest; per-chart consumers record the version they read, so a no-op rebuild here never cascades.')
        if code_sub and pkey:
            R.append(f'Substep key `{pkey}`: add per-substep input digests so a partial substrate change re-runs only the affected partition.')
    else:
        # heavy
        if tier == 'H':
            if not code_sub:
                R.append(f'Single-shot writer (no substep plan) with p90 {_dur(p90_s)}: add a `plan_substeps` partition'
                         + (' by ayanamsha' if lx in ('L1', 'L2') else '') +
                         ' so it becomes resumable and receipt-bearing; until then any interruption is a total loss.')
            elif resume == 'none':
                R.append(f'No resume today — a {_dur(p90_s if polluted else max_s)} run is lost entirely on interruption. Adopt the shared `ResumableWriter` mixin (Phase 4) so committed substeps survive.')
            elif resume == 'substep_fingerprint':
                R.append('Private resume copy with a hand-bumped `_RESUME_VERSION`: migrate to the shared mixin and replace the whole-build fingerprint with per-substep INPUT digests, so a mismatch replans only the changed partitions instead of everything.')
            else:
                R.append('Already delta-fingerprinted (skip-on-unchanged proven byte-identical). Keep it; move onto the shared mixin so the pattern is inherited by every other heavy writer.')
            if pkey:
                R.append(f'Partition key `{pkey}`: record the digest of the inputs each partition consumed. A rule/config change then re-runs only the partitions that read it.')
            if code_sub:
                R.append('Persist the substep plan total at plan time so progress has a real denominator and the watchdog a true liveness signal.')
            if (p90_s or 0) > 1800 or (max_s and not polluted and max_s > 3600):
                R.append(f'Watchdog: the `NOW()` heartbeat defect reaps long substeps; switch to `clock_timestamp()` before the next full rebuild (Phase 2). Classify transient failures for auto-retry — {succ}% completion today.')
        else:
            if code_sub and pkey:
                R.append(f'Has a substep plan (`{pkey}`) but runs in {_dur(med_s)} — resumption is irrelevant here; per-substep input digests still matter because they give partition-scoped early cutoff downstream.')
            elif pkey and 'ayanamsha' in pkey:
                R.append(f'Partitioned by ayanamsha (`{pkey}`, 5 substeps). Per-substep input digests mean an ephemeris or single-ayanamsha change re-runs one partition, not five.')
            # V-1 / D-8: the two sentences that used to stand here — "Fast (median Ns): no
            # bespoke speed work" and "profile only if it stays on the critical path" — were
            # both findings about speed work that no profiler produced. They are removed. What
            # survives is the structural fact about content addressing, which is true of every
            # asset regardless of its cost and needs no profile to assert; the §19 ledger line
            # appended below carries the honest unprofiled state.
            if med_s is not None or p90_s is not None:
                R.append('Early cutoff is the structural win: when this asset\'s output digest is unchanged, nothing downstream rebuilds. That is content addressing (Phase 3), not a finding about this writer\'s speed.')
            else:
                R.append('No completed-run telemetry: p50 and p90 are both unmeasured, so even the §19.4 build-cost baseline is null here — measure before planning anything.')
        if down >= 5:
            R.append(f'Fan-out {down}: content addressing pays back most here — today any rebuild of this asset, even a no-op, invalidates all {down} dependants.')
        if succ is not None and runs >= 20 and succ < 50:
            R.append(f'Only {succ}% of {runs} attempts complete — most wall-clock is human re-dispatch. Error taxonomy + retry (Phase 4) is the fix, not faster code.')
    if a.get('DAG Depth') is not None and int(a['DAG Depth']) >= 12 and not is_service:
        R.append(f'DAG depth {a["DAG Depth"]}: sits in the serial tail. Audit its {deps} declared edges for ones never actually read (Phase 5) — every removed edge is pure wall-clock.')
    # ---- §19 ledger line (D-8 item 3; §15's named correction) -------------------------
    # Every non-service asset states its profiling status explicitly. An unprofiled asset
    # reads as UNKNOWN, never as fine. Services keep "Not a build; nothing to speed up" —
    # D-8: not-a-build is one of §15's own bound classes and is true without profiling.
    if not is_service:
        prof = PROFILES.get(aid, {})
        if prof.get('hotspot'):
            bits = [f"§19 profile ({prof.get('profiled_at', 'no timestamp')}): hotspot `{prof['hotspot']}`"]
            if prof.get('bound_class'):
                bits.append(f", {prof['bound_class']}-bound")
            if prof.get('technique_proposed'):
                bits.append(f". Technique proposed: {prof['technique_proposed']}")
            if prof.get('identity_proof'):
                bits.append(f". Identity proof: {prof['identity_proof']} (I18)")
            R.append(''.join(bits) + '.')
        elif not has_writer:
            R.append('No registered writer: nothing builds this asset, so there is no build cost to '
                     'profile. Bound class `not-a-build` (§19.4 step 3) — hotspot is null by structure, '
                     'not by omission.')
        else:
            base = ' · '.join(filter(None, [
                f'p50 {_dur(med_s)}' if med_s is not None else 'p50 unmeasured',
                f'p90 {_dur(p90_s)}' if p90_s is not None else None,
                (f'worst {_dur(max_s)}' if not polluted else f'recorded worst {_dur(max_s)} is a D-13 unclosed-run artefact')
                if max_s is not None else None,
                f'{runs} run(s)' if runs else None]))
            where = ('§19.6 names this among the ten heavy assets where the efficiency pass concentrates'
                     if tier == 'H' else
                     '§19.6 places this in the long tail, which receives the systemic sweep (indexes, '
                     'batching, set-based rewrites) rather than a bespoke investigation — a scope '
                     'decision from the plan, not a finding that it is already fast')
            R.append(f'**Not profiled.** Measured baseline only: {base}. Hotspot, bound class, technique, '
                     f'target, achieved and identity proof are NULL in the §19 ledger — §19.4 step 1 (no '
                     f'measured hotspot, no optimization) and §15 (an unprofiled asset reads as unknown, '
                     f'not as fine). The profiling harness is M3. {where}.')

    # ---------------------------------------------------------------- 3. RE-ARCHITECTURE & ALIGNMENT
    if 'has_substeps false negative' in viol:
        A.append('`has_substeps` is false in the registry while the writer plans substeps: derive the flag from the writer class (Phase 0.6a). Until then the §N.8 completeness gate is silently disabled for this asset.')
    if any(v.startswith('no layer_index') or v.startswith('layer_index format') for v in viol):
        A.append(f'Layer position: set `layer_index = {lx}`, derive `layer_name` from the locked lexicon (Phase 0.5a).')
    if 'prefix ≠ layer' in viol:
        A.append('Reclassify as `SOURCE` outside L0–L5 (Phase 0.5b) — ingested data, not a built asset.')
    if 'kind/type/storage disagree' in viol:
        A.append('Collapse `asset_type`/`asset_kind`/`storage_type` to one authoritative `asset_kind` (Phase 0.6b).')
    if 'no target_table' in viol:
        A.append('Declare `target_table` (or `clear_tables` if it writes several) so clear/rebuild and size reporting stop guessing from `count_sql`.')
    if 'DRAFT but built and served' in viol:
        A.append(f'Promote to CURRENT or record why it remains DRAFT (Phase 0.8b) — it is built and read by {cons} serving surface(s), so it is authoritative in practice.')
    if 'never built on any chart' in viol:
        A.append('Registered but never built: provision a writer, demote to DRAFT, or retire with a disposition (Phase 0.8a).')
    if life in ('RETIRED', 'SUPERSEDED_BY'):
        A.append('Lifecycle: execute the supported retire operation — clear residual throughput rows, set `superseded_by` and `data_disposition`; never DELETE the registry row (I6).')
    if tbl in CO_WRITTEN:
        A.append(f'`{tbl}` has {CO_WRITTEN[tbl]} co-writers: declare this writer\'s natural-key partition in the registry so the (table × generation × partition) uniqueness invariant is checkable (§3.3).')
    if aid.startswith('ka_gochara'):
        A.append('Generation-bearing: model generation + per-chart authority as first-class registry/UI concepts; one count and one freshness per generation (Phase 2).')
    if is_global:
        A.append('Keep out of per-chart plans but expose completion to the per-chart readiness gate uniformly (the migration-563 class of bug, made structural).')
    if is_service:
        A.append('Move to the service lane with `health_probe` + `provides_apis`; `count_sql` must be null.')
    if cons == 0 and tbl and life == 'CURRENT' and not is_service:
        A.append('No detected serving consumer (Phase 0.8c): record the missing consumer or retire with a disposition.')
    if not is_service and life == 'CURRENT':
        A.append('Output content digest at commit (Phase 3); `built_against_*` re-pointed from timestamps to upstream digests; graded staleness.')
    if not A:
        A.append('Contract-conformant. Inherits the platform-wide changes: content digest, graded staleness, shared resumability.')

    # ---------------------------------------------------------------- BENEFIT
    if is_service:
        B.append('A degraded service surfaces in minutes, not months (one sat red for 66 days).')
    else:
        if not has_integrity:
            B.append('`lit` becomes an earned signal with a real detector behind it.')
        if down:
            B.append(f'{down} direct dependant(s) stop invalidating when this asset rebuilds to identical content.')
        if tier == 'H' and (p90_s or max_s):
            B.append(f'Interruption stops costing up to {_dur(max_s if not polluted else p90_s)} of committed work.')
        if succ is not None and runs >= 20 and succ < 50:
            B.append(f'Completion rate rises from {succ}% as transient failures self-heal.')
        if lx == 'L1' and tbl == 'chart_facts':
            B.append('Facts move from `single` toward `two_pass_verified`; downstream narration inherits a verified base.')
        if 'has_substeps false negative' in viol:
            B.append('A partial build can no longer be promoted to green.')
        if not B:
            B.append('Correct layer placement, honest status, and participation in content-addressed freshness.')

    return AssetPlan(C, R, A, B, now, what)
