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
    disclosed below). NOTE (FABLE #2/#3, T0-6 repair): this union is now
    PROVENANCE / STATIC FALLBACK only — see "Per-instant permission" below.
  * TARGETS — the same fetch the served engine uses:
    `gochara_grammar.resonance_map.fetch_resonance_targets` +
    `gochara_intensity.enrichment.enrich_targets`, so the wiring cannot
    drift from the production read path.
  * VALENCE — `gochara_intensity.valence.is_adverse` (live
    `brahma_event_ontology` read with its own documented fallback), feeding
    `class_valence` / `class_is_adverse`. T0-7 (FABLE #11/#12, §3): each
    class entry additionally carries the explicit `class_polarity`
    declaration block (same single declaration, named as such) and
    `valence_unresolved_operands` — the O-TV-3 probe: when the chart has no
    ashtakavarga_bindu_contributor rows the AV donor-matrix operand is
    declared unresolved, so step06b's three-field valence evaluates those
    rows 'unqualified' with the operand named, never a favourable default.
  * DASHA PERIODS — `dasha_data.fetch_dasha_periods_multilevel` (MD/AD/PD,
    levels 1-3, tier `two_pass_verified`, GOCHARA_DESIGN_SPECS_v1_4 §4.0
    duplicate rules enforced), emitted once as the document's top-level
    `_dasha_periods` payload so `step06b_windows_projection.py` can evaluate
    permission AT EACH PROJECTION INSTANT instead of consuming the unioned
    constant. AD/PD rows carry `parent_row_id` (§4.0 parent linkage).

Per-instant permission (FABLE #2/#3, T0-6): the plurality evaluation is
inherently time-varying; the pre-repair wiring collapsed it per class by the
rule "system licensed the class's delivery iff it fired at ≥1 of the class's
own candidate contact instants in the build horizon" and served that
constant at every instant of every window. The emitted document now carries
`_permission_mode: "per_instant_md_ad_pd"` plus the multi-level period rows;
step06b evaluates `compute_permission` per instant (memoized per
class × UTC day) from those rows. The unioned `permission_systems` map is
RETAINED per class as the documented static fallback (old JSON documents and
`--rehearse-synthetic` have no `_dasha_periods`; step06b then behaves
exactly as pre-repair) and as the review-trail provenance record. A system
that never fires at any candidate instant contributes False — the weighted
fraction is then the pinned honest value, not a fabricated 1.0.

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
import logging
import sys
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import connect, step_parser, write_evidence  # noqa: E402

SIDECAR = Path(__file__).resolve().parents[2]
if str(SIDECAR) not in sys.path:
    sys.path.insert(0, str(SIDECAR))

from services.gochara_grammar import dasha_data as DD  # noqa: E402
from services.gochara_grammar import read_tier_policy as RTP  # noqa: E402
from services.gochara_grammar.resonance_map import fetch_resonance_targets  # noqa: E402
from services.gochara_intensity import enrichment, valence  # noqa: E402
from services.gochara_intensity import permission as perm  # noqa: E402
from services.gochara_intensity._dbutil import savepoint_scope  # noqa: E402
from services.gochara_kernel import legacy_semantics as leg  # noqa: E402

CONTEXT_SOURCE = ("l1_permission_wiring:v2 (per-instant compute_permission "
                  "over MD/AD/PD periods; union over t_exact instants kept as "
                  "static-fallback provenance)")
PERMISSION_MODE = "per_instant_md_ad_pd"

# T0-7 (FABLE #11/#12, GOCHARA_DESIGN_SPECS_v1_4 §3): the context document
# declares each class's polarity explicitly (the SAME declaration
# gochara_intensity.valence already reads — brahma_event_ontology
# evidence_requirements->>'valence' — reused, never a second source) plus
# the valence operands left unresolved at context-build time. O-TV-3's
# operand is the AV donor matrix: when the chart has no
# ashtakavarga_bindu_contributor rows (the current chart state pending the
# native-authorised ga_strength rebuild — gochara_v3/context.py:145-156
# documents that key scheme), the donor-matrix operand is UNRESOLVED and
# every window row's outcome must be 'unqualified' with the operand named,
# never a favourable default.
AV_DONOR_OPERAND = "av_donor_matrix"
AV_DONOR_AYANAMSHA = "lahiri_chitrapaksha"


def fetch_av_donor_matrix(conn, chart_id: str,
                          ayanamsha_id: str = AV_DONOR_AYANAMSHA) -> dict:
    """The P5c per-contributor BAV matrix as the context document carries it
    (D-SPECS C4 / ASTRA P1-4): the SET of writer-scheme keys
    '{GRAHA}-CONTRIBUTOR_{DONOR}-SIGN_{N}' present for the chart under the
    named ayanāṃśa, resolved PER KEY by step06b on kakṣyā-crossing contacts
    only. This replaces the chart-wide `LIMIT 1` probe, which (a) declared
    every window of every class 'unqualified' when the matrix was absent —
    disqualifying paths that consume no P5c operand — and (b) would have
    resolved every operand from one unrelated row once any row existed.

    A DB-shape surprise yields available_keys [] with the error recorded
    (an unreadable matrix resolves nothing — never silently treated as
    present). Duplicate keys with DIFFERENT values are a conflict: such a
    key is excluded from available_keys and listed in `conflicts` (never
    row-order picked)."""
    out = {"probe": "per_key", "ayanamsha_id": ayanamsha_id,
           "fact_category": "ashtakavarga_bindu_contributor",
           "available_keys": [], "row_count": 0, "conflicts": [],
           "error": None}
    try:
        with savepoint_scope(conn, "av_donor_matrix"):
            rows = conn.execute(
                "SELECT fact_subject, fact_value_num FROM chart_facts"
                " WHERE chart_id = %s AND ayanamsha_id = %s"
                "   AND fact_category = 'ashtakavarga_bindu_contributor'"
                "   AND fact_key = 'bindus'",
                [chart_id, ayanamsha_id]).fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.info("[step06a] AV donor-matrix read failed for chart %s — "
                    "no key resolves: %s", chart_id, exc)
        out["error"] = str(exc)
        return out
    values: dict[str, set] = {}
    for row in rows:
        subj, val = (row["fact_subject"], row["fact_value_num"]) \
            if isinstance(row, dict) else (row[0], row[1])
        if val is None:
            continue
        values.setdefault(str(subj), set()).add(float(val))
    out["row_count"] = len(rows)
    out["conflicts"] = sorted(k for k, v in values.items() if len(v) > 1)
    out["available_keys"] = sorted(k for k, v in values.items() if len(v) == 1)
    return out


# ── frozen C5 chart operands + daśā read contract (ASTRA P1-2) ───────────────

NATAL_SUBJECTS = ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT",
                  "RAH_MEAN", "KET_MEAN")


def fetch_chart_operands(conn, chart_id: str,
                         ayanamsha_id: str = AV_DONOR_AYANAMSHA) -> dict:
    """The chart dict the frozen C5 evaluator consumes
    (services.gochara_rules.permission: {lagna_deg, natal{Title: λ},
    day_birth, paksha}), read from L1 chart_facts: graha_position/
    longitude_sidereal (the nine grahas + LAGNA), panchanga_tithi/paksha,
    saham_position/day_birth. Missing operands are NAMED in
    `operands_missing` — never defaulted."""
    from brahmagyan.graha_vocabulary import to_title
    out = {"chart_id": chart_id, "ayanamsha_id": ayanamsha_id,
           "lagna_deg": None, "natal": {}, "paksha": None, "day_birth": None,
           "operands_missing": [], "source": "L1 chart_facts"}
    try:
        with savepoint_scope(conn, "c5_chart_operands"):
            rows = conn.execute(
                "SELECT fact_category, fact_subject, fact_key,"
                " fact_value_text, fact_value_num FROM chart_facts"
                " WHERE chart_id = %s AND ayanamsha_id = %s AND ("
                "  (fact_category = 'graha_position'"
                "   AND fact_key = 'longitude_sidereal')"
                "  OR (fact_category = 'panchanga_tithi' AND fact_key = 'paksha')"
                "  OR (fact_category = 'saham_position' AND fact_key = 'day_birth'))",
                [chart_id, ayanamsha_id]).fetchall()
    except Exception as exc:  # noqa: BLE001
        logger.info("[step06a] chart operand read failed for chart %s: %s",
                    chart_id, exc)
        out["operands_missing"] = ["chart_facts:unreadable"]
        out["error"] = str(exc)
        return out
    seen_lon: dict[str, set] = {}
    for row in rows:
        cat, subj, key, txt, num = (
            (row["fact_category"], row["fact_subject"], row["fact_key"],
             row["fact_value_text"], row["fact_value_num"])
            if isinstance(row, dict) else row)
        if cat == "graha_position" and num is not None:
            seen_lon.setdefault(str(subj), set()).add(float(num))
        elif cat == "panchanga_tithi" and txt:
            out["paksha"] = str(txt).strip().title()
        elif cat == "saham_position" and (txt is not None or num is not None):
            val = str(txt).strip().lower() if txt is not None else str(num)
            out["day_birth"] = val in ("true", "t", "1", "1.0", "day", "yes")
    for subj, vals in seen_lon.items():
        if len(vals) != 1:
            out["operands_missing"].append(f"graha_position:{subj}:conflict")
            continue
        (lon,) = tuple(vals)
        if subj == "LAGNA":
            out["lagna_deg"] = lon
        elif subj in NATAL_SUBJECTS:
            out["natal"][to_title(subj)] = lon
    if out["lagna_deg"] is None:
        out["operands_missing"].append("graha_position:LAGNA")
    for subj in NATAL_SUBJECTS:
        if to_title(subj) not in out["natal"]:
            out["operands_missing"].append(f"graha_position:{subj}")
    if out["paksha"] is None:
        out["operands_missing"].append("panchanga_tithi:paksha")
    if out["day_birth"] is None:
        out["operands_missing"].append("saham_position:day_birth")
    return out


def select_dasha_read_contract(chart_id: str, dasha_periods: list[dict]) -> dict:
    """The §4.0 pin step06b reads Vimśottarī rows under: the frozen contract's
    build for the canonical chart when present; else the single build the
    tier-filtered rows carry; several builds ⇒ a conflict — refuse (raise),
    never row-order pick; no Vimśottarī rows ⇒ build None (disclosed)."""
    from services.gochara_rules.permission import DASHA_READ_CONTRACT
    vim = [p for p in dasha_periods if p.get("system_id") == "vimshottari"]
    null_build = sum(1 for p in vim if p.get("build_id") is None)
    builds = sorted({str(p.get("build_id")) for p in vim if p.get("build_id") is not None})
    pinned = DASHA_READ_CONTRACT["build_id"]
    if str(chart_id) == DASHA_READ_CONTRACT["chart_id"]:
        # the canonical chart is PINNED by the frozen contract: any other
        # sole build is a wrong build, never accepted (ASTRA v1.1 P1-2)
        if pinned not in builds:
            raise DD.DashaReadConflict(
                f"chart_dashas §4.0: the frozen read contract pins build {pinned} "
                f"for chart {chart_id}, but the two_pass_verified vimshottari rows "
                f"carry {builds or 'no build'} — refusing an unpinned read")
        build = pinned
        basis = "GOCHARA_DESIGN_SPECS_v1_4 §4.0 pinned build"
    elif null_build:
        raise DD.DashaReadConflict(
            f"chart_dashas §4.0: {null_build} two_pass_verified vimshottari rows "
            f"for chart {chart_id} carry a NULL build_id — unpinnable, refusing")
    elif len(builds) == 1:
        build = builds[0]
        basis = "single two_pass_verified build present"
    elif not builds:
        build = None
        basis = "no vimshottari rows at the read tier"
    else:
        raise DD.DashaReadConflict(
            f"chart_dashas §4.0: several two_pass_verified vimshottari builds "
            f"{builds} for chart {chart_id} — an unpinned read is a defect; "
            "refusing to pick by row order")
    return {"system_id": "vimshottari", "build_id": build,
            "tier": DD.READ_CONTRACT_TIER, "ayanamsha_id": AV_DONOR_AYANAMSHA,
            "basis": basis, "builds_seen": builds}


def load_pinned_dasha_periods(conn, chart_id: str, systems: list[str]) -> tuple[list[dict], dict]:
    """The §4.0 read as main() performs it (ASTRA v1.2 P1-1): (1) a RAW,
    non-canonicalized read of the tier-pinned Vimśottarī rows selects the
    build pin (select_dasha_read_contract); (2) the Vimśottarī rows are then
    fetched PINNED to that build and canonicalized — a foreign build's
    overlapping rows never enter the duplicate/conflict pass; (3) the other
    DR-14 systems (legacy generators) are fetched and canonicalized on their
    own. Returns (periods, contract)."""
    raw_vim = DD.fetch_dasha_periods_multilevel(
        conn, chart_id, systems=["vimshottari"], canonicalize=False)
    contract = select_dasha_read_contract(chart_id, raw_vim)
    contract["raw_vimshottari_rows"] = len(raw_vim)
    if contract["build_id"] is not None:
        vim = DD.fetch_dasha_periods_multilevel(
            conn, chart_id, systems=["vimshottari"], build_id=contract["build_id"])
    else:
        vim = []
    contract["rows_excluded_by_build_pin"] = len(raw_vim) - len(
        [r for r in raw_vim if str(r.get("build_id")) == str(contract["build_id"])])
    others = [s for s in systems if s != "vimshottari"]
    # the non-pinned DR-14 systems only VOTE in the plurality: they are read at
    # any honestly emitted computed tier (each row keeps its own tier and
    # carries it to the permission detail); floored / divergent / pending /
    # unknown stay refused. The vimshottari reads above stay STRICT (§4.0).
    rest = (DD.fetch_dasha_periods_multilevel(
        conn, chart_id, systems=others, accept_tiers=RTP.HONEST_COMPUTED_TIERS)
        if others else [])
    return list(vim) + list(rest), contract


def _jsonable_period(p: dict) -> dict:
    """chart_dashas rows carry datetimes/UUIDs; the class-context document is
    JSON. ISO strings round-trip through DD.period_contains."""
    out = {}
    for k, v in p.items():
        if isinstance(v, datetime):
            out[k] = v.isoformat()
        elif isinstance(v, (list, tuple)):
            out[k] = [str(x) for x in v]
        elif v is None or isinstance(v, (str, int, float, bool)):
            out[k] = v
        else:
            out[k] = str(v)
    return out


def _rows_by_system_tier(periods: list[dict]) -> dict:
    """{system_id: {tier: n}} of the rows actually emitted — a system absent
    here had NO readable row (the consumer reports it inactive); the tier of
    each emitted row is stated, never implied verified."""
    out: dict[str, dict[str, int]] = {}
    for p in periods:
        t = p.get("verification_pass_status")
        d = out.setdefault(str(p.get("system_id")), {})
        d[str(t)] = d.get(str(t), 0) + 1
    return {k: dict(sorted(v.items())) for k, v in sorted(out.items())}


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
    for row in rows:
        # dict/tuple row agnostic (ASTRA v1.1 A1): the runner hands dict rows
        cls, t_exact = ((row["event_class"], row["t_exact"])
                        if isinstance(row, dict) else (row[0], row[1]))
        if t_exact is None:
            null_exact += 1
            continue
        by_class.setdefault(cls, []).append(_to_jd(t_exact))
    return by_class, null_exact


def build_class_context(swe, conn, chart_id: str, event_class: str,
                        sample_jds: list[float], dasha_periods,
                        unresolved_valence_operands=()) -> dict | None:
    """One class's context entry, or None (honest omission) when the class's
    targets do not resolve. Never fabricates a permission set. The unioned
    `permission_systems` map is the STATIC FALLBACK / provenance record
    (T0-6): step06b evaluates permission per instant from the document's
    top-level `_dasha_periods` when present; this map is what old documents
    and rehearsal mode still consume. `dasha_periods` here is the
    MULTI-LEVEL (MD/AD/PD) row set used for the provenance evaluation."""
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
        # T0-7 (FABLE #11/#12, §3): the class-polarity declaration made
        # EXPLICIT on the document — the single declaration
        # (brahma_event_ontology evidence_requirements->>'valence', read via
        # gochara_intensity.valence.is_adverse with its documented VALENCE_MAP
        # fallback) that step06b's three_field_valence interprets the signed
        # channels relative to. Not a second polarity source.
        "class_polarity": {
            "class_valence": cls_valence,
            "class_is_adverse": adverse,
            "declaration_source": "brahma_event_ontology."
                                  "evidence_requirements->>'valence' via "
                                  "gochara_intensity.valence "
                                  "(VALENCE_MAP fixture fallback)",
            "contract": "three_field_valence:v1 "
                        "(GOCHARA_DESIGN_SPECS_v1_4 §3)",
        },
        # O-TV-3: operands unresolved at context-build time (the AV donor
        # matrix pending the ga_strength rebuild). step06b makes every such
        # operand's valence contribution 'unqualified' and names it.
        "valence_unresolved_operands": list(unresolved_valence_operands),
        "context_source": CONTEXT_SOURCE,
        # provenance (the writer consumes only the four keys above; these are
        # carried for the review trail)
        "sampled_instants": len(sample_jds),
        "systems_active": sorted(systems_active),
        "per_system_fire_counts": {k: v for k, v in per_system_fires.items() if v},
        "permission_value": leg.compute_permission(permission_systems),
    }


class NoContactsError(Exception):
    """No candidate contacts joined to resolved map rows (exit 3 at the CLI)."""


def build_all_class_contexts(swe, conn, chart_id: str, generation: str):
    """The whole class-context pass on a CALLER-SUPPLIED connection: per event
    class, the union-semantics permission context the windows projection
    consumes. Returns (contexts, omitted, null_exact). READ-ONLY — never
    commits/rolls back/closes `conn`, never opens its own. Raises
    NoContactsError when no candidate contacts join (the CLI's exit 3)."""
    by_class, null_exact = fetch_class_contact_instants(
        conn, chart_id, generation)
    if not by_class:
        raise NoContactsError(
            f"no candidate contacts joined to resolved map rows "
            f"for chart {chart_id} generation {generation!r} "
            "— run step06_candidate_build.py first")

    # The caller's transaction mode governs: under the CLI's autocommit
    # connection savepoint_scope is a no-op passthrough (the _dbutil
    # docstring's recommended shape for this engine's many defensive-catch
    # queries); under the governed writer the orchestrator's per-substep
    # transaction carries them.
    # T0-6: MD/AD/PD (levels 1-3) at the §4.0 contract tier; a duplicate
    # CONFLICT raises loudly (DashaReadConflict propagates — never
    # silently served), a DB-shape surprise yields the honest [].
    # ASTRA v1.2 P1-1: the build pin is selected from a RAW read and
    # applied BEFORE canonicalization (load_pinned_dasha_periods).
    dasha_periods, dasha_contract = load_pinned_dasha_periods(
        conn, chart_id, list(perm.DASHA_SYSTEM_IDS))

    # T0-7 / O-TV-3 / D-SPECS C4: the AV donor matrix is read once as a
    # per-key set and emitted at the document's top level; it is NOT a
    # class-level unresolved operand (P5c alone consumes it).
    av_donor_matrix = fetch_av_donor_matrix(conn, chart_id)
    unresolved_valence: list[str] = []
    # ASTRA P1-2: the frozen C5 licence needs the chart operands and the
    # §4.0 read pin; both are read once and emitted at the top level.
    chart_operands = fetch_chart_operands(conn, chart_id)

    contexts: dict[str, dict] = {}
    omitted: list[dict] = []
    for cls in sorted(by_class):
        entry = build_class_context(
            swe, conn, chart_id, cls, sorted(by_class[cls]),
            dasha_periods, unresolved_valence)
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
    # The per-instant payload step06b consumes (T0-6): chart-level rows,
    # emitted once; per-class entries stay self-describing otherwise.
    contexts["_permission_mode"] = PERMISSION_MODE
    contexts["_dasha_periods"] = [_jsonable_period(p) for p in dasha_periods]
    contexts["_av_donor_matrix"] = av_donor_matrix
    contexts["_chart"] = chart_operands
    contexts["_dasha_read_contract"] = dasha_contract
    return contexts, omitted, null_exact


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
        # autocommit: savepoint_scope is a no-op passthrough there and each
        # defensive read is its own transaction (the _dbutil docstring's
        # recommended shape for this engine's many defensive-catch queries).
        try:
            contexts, omitted, null_exact = build_all_class_contexts(
                swe, conn, args.chart_id, args.generation)
        except NoContactsError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 3
        # The chart-level payloads live on the document's top level (the
        # core emits them); the CLI report reads them back out.
        wired_classes = sorted(k for k in contexts if not k.startswith("_"))
        dasha_contract = contexts["_dasha_read_contract"]
        chart_operands = contexts["_chart"]
        av_donor_matrix = contexts["_av_donor_matrix"]
        unresolved_valence = sorted({
            op for cls, entry in contexts.items() if not cls.startswith("_")
            for op in entry.get("valence_unresolved_operands", [])})
    finally:
        conn.close()

    if args.out:
        Path(args.out).write_text(json.dumps(contexts, indent=2))

    report = {
        "writer": "step06a_class_context",
        "chart_id": args.chart_id, "generation": args.generation,
        "classes_wired": wired_classes,
        "classes_omitted": omitted,
        "contacts_null_t_exact_excluded": null_exact,
        "context_source": CONTEXT_SOURCE,
        "permission_mode": PERMISSION_MODE,
        "dasha_periods_emitted": len(contexts.get("_dasha_periods", [])),
        "dasha_levels": list(DD.DEFAULT_LEVELS),
        "dasha_read_tier": DD.READ_CONTRACT_TIER,
        "dasha_read_tier_policy": {
            "pinned_system(vimshottari)": sorted(RTP.STRICT_TIERS),
            "other_systems": sorted(RTP.HONEST_COMPUTED_TIERS)},
        "dasha_rows_by_system_tier": _rows_by_system_tier(
            contexts.get("_dasha_periods", [])),
        "dasha_read_contract": dasha_contract,
        "chart_operands_missing": chart_operands["operands_missing"],
        "valence_unresolved_operands": unresolved_valence,
        "av_donor_matrix": {k: v for k, v in av_donor_matrix.items()
                            if k != "available_keys"} | {
            "available_key_count": len(av_donor_matrix["available_keys"])},
        "valence_contract": "three_field_valence:v1 "
                            "(GOCHARA_DESIGN_SPECS_v1_4 §3; T0-7, FABLE "
                            "#11/#12)",
        "union_semantics": "RETAINED AS STATIC FALLBACK / provenance only: "
                           "a system is active for a class iff it fired at "
                           ">=1 of the class's candidate contact t_exact "
                           "instants. step06b evaluates permission per "
                           "instant from _dasha_periods (T0-6); the union is "
                           "consumed only by old documents / rehearsal.",
        "out": args.out,
    }
    print(json.dumps(report, indent=2))
    if args.evidence:
        write_evidence(6, "CLASS-CONTEXT",
                       f"```json\n{json.dumps(report, indent=2)}\n```")
    return 0


if __name__ == "__main__":
    sys.exit(main())
