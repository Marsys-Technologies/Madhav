"""SR-VEDHA-RESIDENCE-SOURCE — the obstructors' sign residence is DERIVED AT THE INSTANT from the pinned ephemeris (surrogate ruling
2026-10-22, `DECISIONS_SURROGATE.jsonl`; defect 1a of the TR dry-run diagnosis `AR_DIAG.md`), on both sides, each with its own code (K12).

Doctrine: a favourable-house transit is nullified while a graha occupies its vedha place (Phaladīpikā XXVI.3-8, phaladeepika:PG322:C1 /
PG323:C1); Rāhu/Ketu are grahas for this purpose (ND-NODE-VEDHA (i); XXVI.2, XXVI.24); a graha is always in SOME sign, so where the sky can be
read its sign is known, and where it cannot be read the stretch is missing data, never "not in the vedha house" (B.10, N.7.6). The sky is the
campaign convention's: Lahiri sidereal, MEAN node (`convention.CONVENTION_VECTOR`, `record_store.KALA_CONVENTION_VECTOR`, `substrate.py` sky convention, `knots.py` N-4a(b″)).

Every oracle below measures the real Swiss ephemeris (`SE_EPHE_PATH`, the pinned corpus) through this module's OWN reader — a third code path,
independent of the builder's `position_at` and of the verifier's reader — and names the single reversion that must fail it:

  R-1 a Rāhu / Ketu in a sign for which NOTHING is stored yields a derived residence: the vedha is the known 0.0 (the node among the
      obstructors), never `obstructor_residence_unknown` / `node_residence_unknown`, on both sides, and no stored contact is read
      (revert: the residence is not derived — the empty residence an empty contact table used to give);
  R-2 an ingress inside a support creates a boundary within ±1 s of the Swiss crossing and the vedha state changes exactly there (entering the
      vedha house: 1.0 → 0.0; leaving it: 0.0 → 1.0), on both sides; the sweep's window peak sits on the exit boundary
      (revert: the ingress search is off — the residence stays the sign at the start of the support);
  R-3 the MEAN node is the campaign's: Rāhu's ingress is the mean node's, a day or more away from the true node's
      (revert: the verifier maps the pinned `mean` node model to Swiss's TRUE node);
  R-4 builder = verifier on 100 % of the P2 records of achievement_recognition and of bereavement (every sign-residence record of the seven
      stored grahas over a horizon of each class, every cited and uncited house): same applicability, same step function, edges within 1 s
      (revert: the verifier reads Ketu as Rāhu, without the +180°);
  R-5 where the ephemeris cannot answer (the pinned files end in 2400; beyond it Swiss serves Moshier) the planets' residence is missing data,
      named, and the overlay is never a 1.0 (revert: an unanswered stretch is read as a sign).
"""
from __future__ import annotations

import functools
import os
import pathlib
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import swisseph as swe

from services.gochara_kernel import knots
from services.gochara_kernel import vedha_source as vs
from services.gochara_kernel import vedha_verifier as vv
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel.window_sweep import SweepRecord
from services.gochara_rules import registry as reg
from services.gochara_rules import vedha_derive as vd
from services.gochara_rules.vedha import exception_for

from ._disposable_db_guard import UnsafeAdminDSN, guarded_admin_connect
from .test_a53_record_store import ADMIN_DSN, DB_PREFIX
from .test_od1_c1_vedha_provider import PAIR_ROWS, _Conn
from .test_od1_c2_vedha_verifier import FakeConn

EPHE = os.environ.get("SE_EPHE_PATH", "")
UTC = timezone.utc
CHART, GEN = "482012f1-710e-4a25-994a-93821f5871aa", "5.0"
DOC = reg.DOCTRINE_VERSION
VREF = ("vedha_attenuation", DOC)
CLASSICAL = ("Sun", "Mars", "Mercury", "Jupiter", "Venus", "Saturn")
OBSTRUCTORS = CLASSICAL + ("Rahu", "Ketu")
MICRO = timedelta(microseconds=1)
PAIRS = [(g.capitalize(), int(h), int(v)) for g, h, v, *_ in PAIR_ROWS if g.capitalize() not in vd.NODES]

# the pinned convention (WP1 §1.1): what the verifier reads from the generation's stored row
CONVENTION_ROW = ("lahiri_chitrapaksha", "mean")


# ── the oracle's own sky: direct Swiss, the campaign convention, NOT the builder's or the verifier's reader ────────────────────────────
_IDS = {"Sun": swe.SUN, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN}


def truth_lon(body: str, t: datetime, *, node=swe.MEAN_NODE) -> float:
    swe.set_ephe_path(EPHE)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ipl = node if body in ("Rahu", "Ketu") else _IDS[body]
    xx, flags = swe.calc_ut(t.timestamp() / 86400.0 + 2440587.5, ipl, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    assert flags & swe.FLG_SWIEPH, (body, t, flags)
    return (xx[0] + 180.0) % 360.0 if body == "Ketu" else xx[0] % 360.0


@functools.lru_cache(maxsize=None)
def _truth_sign(body: str, t: datetime, node: int) -> int:
    return int(truth_lon(body, t, node=node) // 30.0) + 1


def truth_sign(body: str, t: datetime, *, node=swe.MEAN_NODE) -> int:
    return _truth_sign(body, t, node)


@functools.lru_cache(maxsize=None)
def truth_ingresses(body: str, lo: datetime, hi: datetime, *, node=swe.MEAN_NODE, step=timedelta(hours=6)) -> tuple:
    """((instant to a microsecond, old sign, new sign), …) over [lo, hi): a plain scan with a bisection — no speed bound, no pruning."""
    out, t, cur = [], lo, truth_sign(body, lo, node=node)
    while t < hi:
        nxt = min(t + step, hi - MICRO)
        if nxt <= t:
            break
        if truth_sign(body, nxt, node=node) != cur:
            a, b = t, nxt
            while b - a > MICRO:
                m = a + (b - a) / 2
                a, b = (m, b) if truth_sign(body, m, node=node) == cur else (a, m)
            new = truth_sign(body, b, node=node)
            out.append((b, cur, new))
            cur = new
        t = nxt
    return tuple(out)


def truth_spans(body: str, lo: datetime, hi: datetime) -> list[tuple[int, datetime, datetime]]:
    edges = list(truth_ingresses(body, lo, hi))
    cuts = [lo] + [e[0] for e in edges] + [hi]
    signs = [truth_sign(body, lo)] + [e[2] for e in edges]
    return [(s, a, b) for s, a, b in zip(signs, cuts, cuts[1:])]


# ── what each side is handed ──────────────────────────────────────────────────────────────────────────────────────────────────────────
def writer_position_at():
    """The builder's position probe, exactly as the window substep builds it (`ka_gochara_v5._window_substep.position_at`)."""
    def position_at(body: str, t: datetime) -> float:
        lon, retflag = knots.calc_sidereal_lon(body.title(), t.timestamp() / 86400.0 + 2440587.5, EPHE)
        if not (retflag & 2):
            raise RuntimeError(f"position probe {body} @ {t.isoformat()}: retflag {retflag} lacks the Swiss bit (F-14)")
        return lon
    position_at.cache_key = ("swiss", EPHE)
    return position_at


def sign_of_house(house: int, moon_sign: int) -> int:
    return (house - 1 + moon_sign - 1) % 12 + 1


def moon_sign_for(house: int, sign: int) -> int:
    """The janma-rāśi sign that makes `sign` the `house`-th from the Moon."""
    return (sign - house) % 12 + 1


def sweep_record(rid, agent, house, moon_sign, lo, hi) -> SweepRecord:
    return SweepRecord(record_id=rid, root_id=f"root-{rid}", path_id="P2", rule_version=DOC, relation="residence", object_kind="sign_span",
                       agent=agent, operator_role="scored", admission_state="admitted", supports=((lo, hi),), house_from_frame=house,
                       canonical_target=f"span:{sign_of_house(house, moon_sign)}")


def builder_overlay(records, moon_sign):
    prov = vs.SOURCE.for_grain(_Conn(), chart_id=CHART, generation=GEN, event_class="achievement_recognition", records=records,
                               moon_sign=moon_sign, position_at=writer_position_at())
    return prov, {r.record_id: prov.overlay(r, VREF) for r in records}


def verifier_overlay(records, moon_sign, **kw):
    rows = [(r.record_id, r.agent, r.house_from_frame, r.canonical_target, lo, hi) for r in records for lo, hi in r.supports]
    return vv.derive_overlay(FakeConn(records=rows), chart_id=CHART, generation=GEN, event_class="achievement_recognition", path_id="P2",
                             rule_version=DOC, moon_sign=moon_sign, ephe_path=EPHE, **kw)


@pytest.fixture(autouse=True)
def _need_ephemeris():
    assert EPHE and pathlib.Path(EPHE).is_dir(), "SE_EPHE_PATH (the pinned corpus) is required — a stand-in sky is not an oracle (R-2026-10-15-02)"


# ── R-1 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _quiet_day_for(node: str):
    """(t0, node's sign): a 2-day stretch in 2025 when `node` is in a sign no other obstructor occupies and does not change sign."""
    day = datetime(2025, 3, 1, tzinfo=UTC)
    for k in range(120):
        t0 = day + timedelta(days=k)
        s = truth_sign(node, t0)
        if truth_sign(node, t0 + timedelta(days=2)) != s:
            continue
        others = [g for g in OBSTRUCTORS if g != node]
        if all(truth_sign(g, t0 + timedelta(hours=h)) != s for g in others for h in (0, 24, 48)):
            return t0, s
    raise AssertionError("no quiet stretch found")


@pytest.mark.parametrize("node", ["Rahu", "Ketu"])
def test_r1_a_node_in_a_sign_with_no_stored_contact_is_a_derived_residence_never_unknown(node):
    t0, sign = _quiet_day_for(node)
    pair = next(p for p in PAIRS if p[0] == "Sun")                       # the Sun's 3rd → its vedha place, the 9th
    _, house, vedha_house = pair
    m = moon_sign_for(vedha_house, sign)                                 # …is exactly the sign the node is in
    rec = sweep_record("sun", "sun", house, m, t0, t0 + timedelta(days=2))
    prov, built = builder_overlay([rec], m)                              # _Conn() refuses every statement: no stored contact is read
    seg = built["sun"].segments
    assert [(s.state, s.value, s.reason) for s in seg] == [("active", 0.0, None)] and seg[0].obstructors == (node,), seg
    verified = verifier_overlay([rec], m)("sun")                         # FakeConn refuses the contact table likewise
    assert [(s.state, s.value, s.reason) for s in verified.segments] == [("active", 0.0, None)]
    assert prov.summary()["residence_unanswered_seconds"] == {} and prov.summary()["residence_source"] == vs.RESIDENCE_SOURCE


# ── R-2 / R-3 ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _ingress_case(body: str, kind: str):
    """A real ingress of `body` after 2025-02-01 and a vedha configuration in which it is the ONLY change over a ±1-day support:
    (t_ing, rec, moon_sign, (value before, value after)). The first ingress that admits one is used."""
    lo = datetime(2025, 2, 1, tzinfo=UTC)
    for t_ing, old, new in truth_ingresses(body, lo, lo + timedelta(days=1500)):
        window = (t_ing - timedelta(days=1), t_ing + timedelta(days=1))
        sign = new if kind == "enter" else old
        probes = [window[0] + timedelta(hours=3 * k) for k in range(17)]
        for primary, house, vedha_house in PAIRS:
            if primary == body or exception_for(primary, body) != "none":
                continue
            if any(truth_sign(g, t) == sign for g in OBSTRUCTORS if g not in (body, primary) and exception_for(primary, g) == "none"
                   for t in probes):
                continue                                                 # another obstructor would also sit in the vedha house
            m = moon_sign_for(vedha_house, sign)
            rec = sweep_record("p", primary.lower(), house, m, *window)
            return t_ing, rec, m, (1.0, 0.0) if kind == "enter" else (0.0, 1.0)
    raise AssertionError(f"no configuration for {body} {kind}")


@pytest.mark.parametrize("body", list(OBSTRUCTORS))
@pytest.mark.parametrize("kind", ["enter", "exit"])
def test_r2_an_ingress_inside_the_support_is_a_boundary_within_one_second_and_the_state_changes_exactly_there(body, kind):
    t_ing, rec, m, (before, after) = _ingress_case(body, kind)
    _, built = builder_overlay([rec], m)
    sides = {"builder": built["p"], "verifier": verifier_overlay([rec], m)("p")}
    for who, ov in sides.items():
        edges = ov.boundaries(*rec.supports[0])
        assert len(edges) == 1 and abs((edges[0] - t_ing).total_seconds()) <= 1.0, (who, edges, t_ing)
        assert (ov.value_at(t_ing - timedelta(seconds=2)), ov.value_at(t_ing + timedelta(seconds=2))) == (before, after), who
    assert abs((sides["builder"].boundaries(*rec.supports[0])[0] - t_ing).total_seconds()) < 1e-3     # the builder refines to the microsecond
    if kind == "exit":   # the sweep sees the boundary: the earliest maximum of the window is the instant the obstruction ends
        prov = vs.SOURCE.for_grain(_Conn(), chart_id=CHART, generation=GEN, event_class="achievement_recognition", records=[rec], moon_sign=m,
                                   position_at=writer_position_at())
        (w,) = ws.draft_windows("achievement_recognition", [rec], ws.registry_factor_rows, vedha=prov, allow_dynamic=True)[0]
        assert w.score == 1.0 and abs((w.peak_instant - t_ing).total_seconds()) <= 1.0, (w.score, w.peak_instant, t_ing)


def test_r3_the_node_model_is_the_campaigns_mean_node_not_the_true_node():
    lo = datetime(2025, 2, 1, tzinfo=UTC)
    t_mean = truth_ingresses("Rahu", lo, lo + timedelta(days=700))[0][0]
    t_true = truth_ingresses("Rahu", lo, lo + timedelta(days=700), node=swe.TRUE_NODE)[0][0]
    assert abs((t_mean - t_true).total_seconds()) > 86400.0                         # the two models place the ingress days to weeks apart
    t_ing, rec, m, _ = _ingress_case("Rahu", "enter")
    _, built = builder_overlay([rec], m)
    for ov in (built["p"], verifier_overlay([rec], m)("p")):
        (edge,) = ov.boundaries(*rec.supports[0])
        assert abs((edge - t_ing).total_seconds()) <= 1.0 and abs((edge - t_ing).total_seconds()) < abs((edge - t_true).total_seconds())


# ── R-4: builder = verifier on 100 % of the P2 records of two classes ────────────────────────────────────────────────────────────────────
DDL = """
CREATE TABLE public.bg_transit_rules (graha text, primary_house int, vedha_house int, classical_citation text, rule_type text);
CREATE TABLE public.ka_gochara_physical_object (physical_object_id uuid PRIMARY KEY, body text, relation_kind text, canonical_target text);
CREATE TABLE public.ka_gochara_contact (chart_id uuid, generation text, contact_id uuid, physical_object_id uuid, body text,
  relation_kind text, t_in timestamptz, t_out timestamptz);
CREATE TABLE public.ka_gochara_sky_convention (convention_id text PRIMARY KEY, ayanamsha text, node_convention text);
CREATE TABLE public.ka_gochara_convention_bridge (kala_convention_id text PRIMARY KEY, sky_convention_id text);
CREATE TABLE public.kala_gochara_coverage (chart_id uuid, generation text, partition_kind text, partition_key text, completed_horizon tstzrange,
  convention_id text);
CREATE TABLE public.ka_gochara_relationship_record (record_id uuid, chart_id uuid, generation text, event_class text, path_id text,
  rule_version text, agent text, house_from_frame int, object_id uuid, temporal_support_intervals tstzmultirange,
  admission_state text, operator_role text);
"""
MOON_SIGN = 11
#: each class' horizon (three years, so the slow grahas and both nodes cross a sign boundary inside it)
HORIZONS = {"achievement_recognition": datetime(2025, 1, 1, tzinfo=UTC), "bereavement": datetime(2031, 6, 1, tzinfo=UTC)}


@pytest.fixture()
def db():
    psycopg = pytest.importorskip("psycopg")
    from psycopg.conninfo import make_conninfo
    try:
        admin = guarded_admin_connect(ADMIN_DSN, autocommit=True, connect_timeout=3)
    except UnsafeAdminDSN:
        raise
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"NOT_RUN: disposable database server unreachable ({exc})")
    name = f"{DB_PREFIX}vres_{uuid.uuid4().hex[:8]}"
    admin.execute(f'CREATE DATABASE "{name}"')
    conn = None
    try:
        conn = psycopg.connect(make_conninfo(ADMIN_DSN, dbname=name), autocommit=True, connect_timeout=3)
        conn.execute(DDL)
        for row in PAIR_ROWS:
            conn.execute("INSERT INTO public.bg_transit_rules VALUES (%s, %s, %s, %s, %s)", row)
        conn.execute("INSERT INTO public.ka_gochara_sky_convention VALUES ('s1', %s, %s)", CONVENTION_ROW)
        conn.execute("INSERT INTO public.ka_gochara_convention_bridge VALUES ('c1', 's1')")
        for cls in HORIZONS:
            conn.execute("INSERT INTO public.kala_gochara_coverage VALUES (%s, %s, 'event_class', %s, tstzrange(%s, %s), 'c1')",
                         (CHART, GEN, cls, HORIZONS[cls], HORIZONS[cls] + timedelta(days=1100)))
        yield conn
    finally:
        if conn is not None:
            conn.close()
        assert name.startswith(DB_PREFIX), name
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        admin.close()


def _class_records(conn, cls: str) -> list[SweepRecord]:
    """Every sign-residence record of the seven stored grahas (no Moon) over the class' horizon, stored in the substrate and returned as the
    builder's records: the primary's residence spans are the oracle's own (`truth_spans`)."""
    lo = HORIZONS[cls]
    out = []
    for graha in CLASSICAL:
        for k, (sign, a, b) in enumerate(truth_spans(graha, lo, lo + timedelta(days=1100))):
            house = (sign - MOON_SIGN) % 12 + 1
            oid = str(uuid.uuid4())
            conn.execute("INSERT INTO public.ka_gochara_physical_object VALUES (%s, %s, 'residence', %s)", (oid, graha.lower(), f"span:{sign}"))
            rid = str(uuid.uuid4())
            conn.execute("INSERT INTO public.ka_gochara_relationship_record VALUES (%s, %s, %s, %s, 'P2', %s, %s, %s, %s,"
                         " ('{[' || %s::text || ',' || %s::text || ')}')::tstzmultirange, 'admitted', 'scored')",
                         (rid, CHART, GEN, cls, DOC, graha.lower(), house, oid, a.isoformat(), b.isoformat()))
            out.append(SweepRecord(record_id=rid, root_id=rid, path_id="P2", rule_version=DOC, relation="residence", object_kind="sign_span",
                                   agent=graha.lower(), operator_role="scored", admission_state="admitted", supports=((a, b),),
                                   house_from_frame=house, canonical_target=f"span:{sign}"))
    return out


def _shape(applicable, segments):
    return applicable, [(s.state, s.value, s.reason, s.scope) for s in segments]


@pytest.mark.parametrize("cls", list(HORIZONS))
def test_r4_builder_and_verifier_agree_on_every_p2_record_of_the_class(db, cls):
    records = _class_records(db, cls)
    prov = vs.SOURCE.for_grain(_Conn(), chart_id=CHART, generation=GEN, event_class=cls, records=records, moon_sign=MOON_SIGN,
                               position_at=writer_position_at())
    built = {r.record_id: prov.overlay(r, VREF) for r in records}
    ov = vv.derive_overlay(db, chart_id=CHART, generation=GEN, event_class=cls, path_id="P2", rule_version=DOC, moon_sign=MOON_SIGN,
                           ephe_path=EPHE)
    assert ov.summary()["records"] == len(records) > 100 and ov.summary()["convention"] == dict(zip(("ayanamsha", "node_convention"), CONVENTION_ROW))
    disagree, with_changes = [], 0
    for r in records:
        b, v = built[r.record_id], ov(r.record_id)
        same = _shape(b.applicable, b.segments) == _shape(v.applicable, v.segments)
        if same and b.applicable:
            same = all(abs((x.t_in - y.t_in).total_seconds()) <= 1.0 and abs((x.t_out - y.t_out).total_seconds()) <= 1.0
                       for x, y in zip(b.segments, v.segments))
        if not same:
            disagree.append((r.agent, r.house_from_frame, r.supports[0][0].date().isoformat()))
        with_changes += bool(b.applicable and len(b.segments) > 1)
        assert all(s.reason is None for s in b.segments), (r.agent, r.house_from_frame)          # nothing is `*_residence_unknown` where the sky answers
    assert disagree == [], f"{len(disagree)} of {len(records)} records disagree: {disagree[:5]}"
    assert with_changes >= 5                                                                  # the comparison is not vacuous: ingresses do cut records
    assert ov.summary()["residence_unanswered_seconds"] == {} and prov.summary()["residence_unanswered_seconds"] == {}


# ── R-5 ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_r5_where_the_ephemeris_cannot_answer_the_planets_residence_is_missing_data_named_never_a_one():
    lo = datetime(2450, 3, 1, tzinfo=UTC)                                    # beyond the pinned files (1800-2400): Swiss serves Moshier there
    hi = lo + timedelta(days=40)
    node_signs = {truth_sign("Rahu", t) for t in (lo, hi)} | {truth_sign("Ketu", t) for t in (lo, hi)}          # the mean node is analytic: it answers
    sign = next(s for s in (7, 1, 2, 3, 4, 5, 6, 8) if s not in node_signs)       # a vedha place no node is in, so only the planets could settle it
    m = moon_sign_for(9, sign)                                                # the Sun's 3rd → its vedha place, the 9th, is `sign`
    rec = sweep_record("sun", "sun", 3, m, lo, hi)
    prov, built = builder_overlay([rec], m)
    verified = verifier_overlay([rec], m)("sun")
    for who, segs in (("builder", built["sun"].segments), ("verifier", verified.segments)):
        # the five other planets cannot be read: unknown, named — neither a 1.0 ("not in the vedha house") nor a guessed 0.0
        assert [(s.t_in, s.t_out, s.state, s.value, s.reason) for s in segs] == [
            (lo, hi, "unqualified", None, "obstructor_residence_unknown")], who
    assert set(prov.summary()["residence_unanswered_seconds"]) == {"Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"}     # the nodes are analytic
    assert prov.summary()["residence_unanswered_seconds"]["Mars"] == pytest.approx(40 * 86400.0)


def test_r5_a_pinned_convention_the_verifier_cannot_reproduce_is_refused_never_replaced(db):
    db.execute("UPDATE public.ka_gochara_sky_convention SET node_convention = 'true'")                  # the other model: no switch between mean and true
    cls = "achievement_recognition"
    _class_records(db, cls)
    with pytest.raises(vv.VedhaDerivationError, match="pinned sky convention"):
        vv.derive_overlay(db, chart_id=CHART, generation=GEN, event_class=cls, path_id="P2", rule_version=DOC, moon_sign=MOON_SIGN,
                          ephe_path=EPHE)


def test_the_verifiers_speed_bounds_exceed_the_swiss_speeds():
    """The leap-frog is exact only under its bound, so the bound is measured (weekly over 1990-2060, Swiss's own speed output)."""
    swe.set_ephe_path(EPHE)
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    worst: dict[str, float] = {}
    for k in range(0, 70 * 52):
        jd = swe.julday(1990, 1, 1, 0.0) + 7 * k
        for g in vv._VMAX_DPS:
            ipl = swe.MEAN_NODE if g in ("Rahu", "Ketu") else _IDS[g]
            xx, _ = swe.calc_ut(jd, ipl, swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED)
            worst[g] = max(worst.get(g, 0.0), abs(xx[3]))
    assert all(vv._VMAX_DPS[g] > 1.05 * worst[g] for g in worst), {g: (round(worst[g], 4), vv._VMAX_DPS[g]) for g in worst}
