#!/usr/bin/env python3
"""step06_candidate_build.py — WP10 runbook step 6 (plan §9): '4.0' candidate build.

Drives the ledger lifecycle for the candidate generation on ONE chart:
register_convention → publish_candidate (input generation vector recorded) →
write_contacts + write_coverage. '3.0' is never touched; the authority stays
'3.0' until step 8.

Tranche 2 (PRODUCTION_TRANCHE_2_AUTHORIZED). Sheet A-3.

Flags (remainder brief §7.A: "all §4 flags on", recorded in the input
generation vector):
    activity_shape=linear_no_box  orb_max_deg=--orb-deg (M-1 fallback 5.0°,
        since WP8 M-1's 1.0° recommendation is NOT ratified; 7.C allows the
        declared fallback)
    moon_channel=separate  nodal_drishti=removed  sade_sati_mode=testimony
    kakshya_bindu_interim=true
plus N-17/N-22 and M-8's rows as recorded vector entries.

Episodes: at tranche time the kernel pipeline enumerates them; this script
consumes that enumeration as `--episodes-json` (a list of episode dicts in the
ledger's `_normalize_episode` shape, exactly what write_contacts accepts) and
`--coverage-json` (a list of coverage partition dicts). For rehearsal,
`--rehearse-synthetic` fabricates a small synthetic episode set instead —
synthetic data only, never pointed at a real chart.

The factor-level delta report vs '3.0' (§4.11, WP8's
WP8_FACTOR_DELTA_REPORT_v1_0.md artifact) is attached to the manifest via
--delta-report; at tranche time it is REQUIRED (7.C), in rehearsal optional.

Usage:
    python3 step06_candidate_build.py --dsn postgresql://... --chart-id <uuid> \
        [--horizon-start 2020-01-01 --horizon-end 2030-01-01] \
        [--episodes-json eps.json --coverage-json cov.json | --rehearse-synthetic] \
        [--orb-deg 5.0] [--delta-report path] [--evidence]

Exit codes: 0 built; 3 cannot proceed; 4 production refusal; 6 publish refused
(published generation — a rebuild after publication is a NEW label, plan §4.7).
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import connect, step_parser, write_evidence  # noqa: E402

SIDECAR = Path(__file__).resolve().parents[2]
_LEDGER_PATH = SIDECAR / "services" / "gochara_kernel" / "ledger.py"

UTC = timezone.utc

# The candidate's input generation vector (7.C: each flag recorded). This is
# the DECLARED vector; the build records it verbatim on the manifest.
GENERATION_VECTOR_FLAGS = {
    "activity_shape": "linear_no_box",
    "moon_channel": "separate",
    "nodal_drishti": "removed",        # N-14
    "sade_sati_mode": "testimony",     # N-15
    "kakshya_bindu_interim": True,     # N-22
    "overlay_stamps": True,            # N-17 (three-consumer stamps populated)
    "vedha_exceptions": "m8_rows",     # M-8's ruled rows
}

CONVENTION_VECTOR = {
    "zodiac": "sidereal",
    "ayanamsha": "lahiri_chitrapaksha",
    "sidereal_method": "swe_flg_sidereal",
    "node_model": "mean",
    "node_source": "swiss_mean_node_flg_sidereal",
    "epoch_convention": "noon_ut_knot_abscissa",
    "time_scale": "ut_to_tt_swe_deltat",
    "house_system": "whole_sign",
    "ephemeris_mode": "flg_swieph",
    "method_version": "1.0.0",
}


def _load_ledger():
    """Load ledger.py by file path (same discipline as test_wp6_ledger.py:
    the WP3a package __init__ is a sibling workstream's surface)."""
    spec = importlib.util.spec_from_file_location("cutover_step06_ledger", _LEDGER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _synthetic_episodes() -> list[dict]:
    t = datetime(2026, 6, 15, 12, 0, 0, tzinfo=UTC)
    from datetime import timedelta
    return [{
        "independence_group": "ig-saturn-rehearsal",
        "body": "Saturn", "relation": "conjunction", "aspect_deg": 0,
        "target_type": "karaka", "target_ref": "SUN", "target_fact_id": None,
        "target_resolution_state": "resolved", "target_longitude_deg": 90.0,
        "t_in": t - timedelta(hours=2),
        "t_exact": t,
        "t_out": t + timedelta(hours=2),
        "bracket_seconds": 300, "tolerance_arcsec": 2.0,
        "truncated_at_horizon": None, "branch": "direct",
        "orb_max_deg": None,  # filled from --orb-deg below
        "orb_source": "orb_conj_slow",
        "epistemic_class": "observed_event",
        "completeness_state": "complete_resolved",
        "operator_role": "kernel", "claim_grain": "exact_instant",
        "time_basis": "event_time_utc",
        "comparable_with": "same_convention_same_inputs",
        "ephemeris_backend": {"backend": "swieph", "retflag": 258},
        "evidence_fact_ids": [],
        "classical_citation": None, "uncited_extension": True,
        "corpus_verifiable": None,
    }]


def _synthetic_coverage(horizon: str) -> list[dict]:
    return [{
        "partition_kind": "body_target", "partition_key": "saturn:karaka",
        "requested_horizon": horizon, "completed_horizon": horizon,
        "resolution": 2.0, "relations_searched": ["conjunction"],
        "targets_requested": 1,
        "target_resolution_state_counts": {"resolved": 1, "unavailable": 0,
                                           "unqualified": 0},
        "unavailable_inputs": {}, "unsearched_reason": None,
    }]


def main() -> int:
    parser = step_parser(6, __doc__)
    parser.add_argument("--chart-id", required=True)
    parser.add_argument("--generation", default="4.0")
    parser.add_argument("--horizon-start", default="2020-01-01T00:00:00+00:00")
    parser.add_argument("--horizon-end", default="2030-01-01T00:00:00+00:00")
    parser.add_argument("--episodes-json")
    parser.add_argument("--coverage-json")
    parser.add_argument("--rehearse-synthetic", action="store_true")
    parser.add_argument("--orb-deg", type=float, default=5.0,
                        help="M-1 fallback orb (no-box × 5.0°) until the native "
                             "ratifies WP8 M-1's 1.0° recommendation")
    parser.add_argument("--delta-report", help="§4.11 factor-level delta report "
                        "vs '3.0' — REQUIRED at tranche time (7.C)")
    args = parser.parse_args()

    if not (args.rehearse_synthetic or (args.episodes_json and args.coverage_json)):
        print("ERROR: provide --episodes-json + --coverage-json, or "
              "--rehearse-synthetic for rehearsal", file=sys.stderr)
        return 3

    vector = dict(GENERATION_VECTOR_FLAGS)
    vector["orb_max_deg"] = args.orb_deg
    vector["orb_ruling"] = ("M-1 fallback no-box × 5.0° (unratified)"
                            if args.orb_deg == 5.0 else "per --orb-deg")
    vector["delta_report"] = args.delta_report

    if args.rehearse_synthetic:
        episodes = _synthetic_episodes()
        for ep in episodes:
            ep["orb_max_deg"] = args.orb_deg
        horizon_text = f"[{args.horizon_start},{args.horizon_end})"
        coverage = _synthetic_coverage(horizon_text)
    else:
        episodes = json.loads(Path(args.episodes_json).read_text())
        coverage = json.loads(Path(args.coverage_json).read_text())
        horizon_text = f"[{args.horizon_start},{args.horizon_end})"

    ledger = _load_ledger()
    conn = connect(args.dsn, step=6, autocommit=False)
    build_id = f"wp10-step6-{int(time.time())}"
    try:
        cid = ledger.register_convention(conn, CONVENTION_VECTOR,
                                         {"ephemeris_backend": "swieph",
                                          "retflag": 258})
        manifest_id = ledger.publish_candidate(
            conn, args.chart_id, args.generation, cid, vector,
            {"backend": "swieph", "retflag": 258}, horizon_text)
        ids = ledger.write_contacts(conn, args.chart_id, args.generation, cid,
                                    episodes, build_id)
        n_cov = ledger.write_coverage(conn, args.chart_id, args.generation, cid,
                                      coverage, build_id)
        conn.commit()
    except ledger.PublishedGenerationRefusal as exc:
        conn.rollback()
        print(f"REFUSED: {exc}", file=sys.stderr)
        conn.close()
        return 6
    except Exception:
        conn.rollback()
        conn.close()
        raise
    conn.close()

    report = {
        "chart_id": args.chart_id, "generation": args.generation,
        "convention_id": cid, "manifest_id": manifest_id,
        "build_id": build_id, "contacts_written": len(ids),
        "coverage_rows_written": n_cov,
        "input_generation_vector": vector,
    }
    print(json.dumps(report, indent=2, default=str))
    if args.evidence:
        write_evidence(6, "GREEN",
                       f"```json\n{json.dumps(report, indent=2, default=str)}\n```")
    return 0


if __name__ == "__main__":
    sys.exit(main())
