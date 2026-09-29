"""step06a_class_context.py — class-context permission wiring (ADK-0017 carried
block 4; the E-012 closure's deferred item, owed BEFORE the native package).

Produces the `--class-context-json` document that
`step06b_windows_projection.py` consumes, from the REAL permission machinery
rather than a rehearsal-synthetic constant:

  * PERMISSION SYSTEMS — `services/gochara_intensity/permission.py`'s
    `compute_permission` (the DR-14 12-generator plurality sum: 8 live
    `chart_dashas` systems + sade_sati + guru_shani_double_transit +
    av_threshold + planetary_return), evaluated per event class at each of
    the class's candidate-contact exact instants (t_exact) from the
    `kala_gochara_contacts` ledger. A system is marked active for the class
    iff it is active at AT LEAST ONE of those instants (union semantics —
    disclosed below).
  * TARGETS — the same fetch the served engine uses:
    `gochara_grammar.resonance_map.fetch_resonance_targets` +
    `gochara_intensity.enrichment.enrich_targets`, so the wiring cannot
    drift from the production read path.
  * VALENCE — `gochara_intensity.valence.is_adverse` (live
    `brahma_event_ontology` read with its own documented fallback), feeding
    `class_valence` / `class_is_adverse`.

Union-semantics disclosure: the pinned writer algebra carries PERMISSION as
one static factor per (chart, class) (`legacy_semantics.compute_permission`
over a systems_active dict — engine.py:1241-1243). The plurality evaluation
is inherently time-varying; this wiring collapses it per class by the rule
"system licensed the class's delivery iff it fired at ≥1 of the class's own
candidate contact instants in the build horizon". A system that never fires
at any candidate instant contributes False — the weighted fraction is then
the pinned honest value, not a fabricated 1.0.

Honest-skip discipline (preserved end-to-end): a class is OMITTED from the
emitted JSON — never emitted with a fabricated context — when its targets do
not resolve (empty after fetch+enrich) or it has no usable sample instants.
`step06b_windows_projection.py` then records it in `skipped_classes` and
projects nothing for it. Omissions are listed in this script's run report
with their reasons.

Contacts with t_exact IS NULL are excluded from sampling and COUNTED
(honest-null discipline — never a fabricated instant).

Disposable-DB only via the shared step-parser DSN guard (exit 4 on a
production-pointed DSN, tranche-2 flag). Exit 3 on missing inputs (no
contacts for the chart/generation, no map rows). Read-only: SELECTs only,
nothing is written to the database.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import connect, step_parser, write_evidence  # noqa: E402

SIDECAR = Path(__file__).resolve().parents[2]
if str(SIDECAR) not in sys.path:
    sys.path.insert(0, str(SIDECAR))

from services.gochara_grammar import dasha_data as DD  # noqa: E402
from services.gochara_grammar.resonance_map import fetch_resonance_targets  # noqa: E402
from services.gochara_intensity import enrichment, valence  # noqa: E402
from services.gochara_intensity import permission as perm  # noqa: E402
from services.gochara_kernel import legacy_semantics as leg  # noqa: E402

CONTEXT_SOURCE = ("l1_permission_wiring:v1 (gochara_intensity.permission union "
                  "over the class's candidate contact t_exact instants)")


def _to_jd(ts) -> float:
    """kala_gochara_contacts timestamps are timestamptz; jd = unix/86400 +
    2440587.5 (same conversion as step06b_windows_projection.jd_of)."""
    return ts.timestamp() / 86400.0 + 2440587.5


def fetch_class_contact_instants(conn, chart_id: str, generation: str):
    """Per event class, the t_exact julian days of the class's candidate
    contacts — joined through the resonance map on (target_type, target_ref),
    the same join step06b_windows_projection.main() applies. Returns
    ({class: [jd...]}, null_t_exact_count). t_exact NULL contacts are counted
    and excluded, never sampled at a fabricated instant."""
    rows = conn.execute(
        "SELECT DISTINCT m.event_class, c.t_exact"
        " FROM kala_gochara_contacts c"
        " JOIN gochara_resonance_map m"
        "   ON m.chart_id = c.chart_id"
        "  AND m.target_type = c.target_type"
        "  AND m.target_ref = c.target_ref"
        "  AND m.target_resolution_state = 'resolved'"
        " WHERE c.chart_id = %s AND c.generation = %s",
        (chart_id, generation)).fetchall()
    by_class: dict[str, list[float]] = {}
    null_exact = 0
    for cls, t_exact in rows:
        if t_exact is None:
            null_exact += 1
            continue
        by_class.setdefault(cls, []).append(_to_jd(t_exact))
    return by_class, null_exact


def build_class_context(swe, conn, chart_id: str, event_class: str,
                        sample_jds: list[float], dasha_periods) -> dict | None:
    """One class's context entry, or None (honest omission) when the class's
    targets do not resolve. Never fabricates a permission set."""
    targets = enrichment.enrich_targets(
        conn, fetch_resonance_targets(conn, chart_id, event_class))
    if not targets:
        return None

    systems_active: set[str] = set()
    per_system_fires = {sid: 0 for sid in leg.PERMISSION_SYSTEM_IDS}
    for t_jd in sample_jds:
        _, detail = perm.compute_permission(
            swe, conn, chart_id, event_class, targets, t_jd,
            dasha_periods=dasha_periods)
        for sid in detail["systems_active"]:
            systems_active.add(sid)
            per_system_fires[sid] = per_system_fires.get(sid, 0) + 1

    adverse, cls_valence = valence.is_adverse(conn, event_class)
    permission_systems = {sid: sid in systems_active
                          for sid in leg.PERMISSION_SYSTEM_IDS}
    return {
        "permission_systems": permission_systems,
        "class_valence": cls_valence,
        "class_is_adverse": adverse,
        "context_source": CONTEXT_SOURCE,
        # provenance (the writer consumes only the four keys above; these are
        # carried for the review trail)
        "sampled_instants": len(sample_jds),
        "systems_active": sorted(systems_active),
        "per_system_fire_counts": {k: v for k, v in per_system_fires.items() if v},
        "permission_value": leg.compute_permission(permission_systems),
    }


def main(argv: list[str] | None = None) -> int:
    parser = step_parser(6, __doc__)
    parser.add_argument("--chart-id", required=True)
    parser.add_argument("--generation", default="4.0")
    parser.add_argument("--out", help="write the class-context JSON here "
                        "(default: stdout only)")
    args = parser.parse_args(argv)

    import swisseph as swe

    conn = connect(args.dsn, step=6, autocommit=True)
    try:
        by_class, null_exact = fetch_class_contact_instants(
            conn, args.chart_id, args.generation)
        if not by_class:
            print(f"ERROR: no candidate contacts joined to resolved map rows "
                  f"for chart {args.chart_id} generation {args.generation!r} "
                  "— run step06_candidate_build.py first", file=sys.stderr)
            return 3

        # autocommit: savepoint_scope is a no-op passthrough there and each
        # defensive read is its own transaction (the _dbutil docstring's
        # recommended shape for this engine's many defensive-catch queries).
        dasha_periods = DD.fetch_dasha_periods(
            conn, args.chart_id, systems=list(perm.DASHA_SYSTEM_IDS))

        contexts: dict[str, dict] = {}
        omitted: list[dict] = []
        for cls in sorted(by_class):
            entry = build_class_context(
                swe, conn, args.chart_id, cls, sorted(by_class[cls]),
                dasha_periods)
            if entry is None:
                omitted.append({
                    "event_class": cls,
                    "reason": "targets did not resolve "
                              "(fetch_resonance_targets/enrich_targets empty) "
                              "— omitted, never fabricated",
                    "candidate_instants": len(by_class[cls]),
                })
                continue
            contexts[cls] = entry
    finally:
        conn.close()

    if args.out:
        Path(args.out).write_text(json.dumps(contexts, indent=2))

    report = {
        "writer": "step06a_class_context",
        "chart_id": args.chart_id, "generation": args.generation,
        "classes_wired": sorted(contexts),
        "classes_omitted": omitted,
        "contacts_null_t_exact_excluded": null_exact,
        "context_source": CONTEXT_SOURCE,
        "union_semantics": "a system is active for a class iff it fired at "
                           ">=1 of the class's candidate contact t_exact "
                           "instants (static per-class collapse of the "
                           "time-varying DR-14 plurality — disclosed)",
        "out": args.out,
    }
    print(json.dumps(report, indent=2))
    if args.evidence:
        write_evidence(6, "CLASS-CONTEXT",
                       f"```json\n{json.dumps(report, indent=2)}\n```")
    return 0


if __name__ == "__main__":
    sys.exit(main())
