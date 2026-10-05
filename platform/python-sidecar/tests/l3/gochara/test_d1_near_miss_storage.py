"""ND-P2-20261005 rules 1-2, BUILDER side — the near-miss kind through the REAL writer on the real migration chain (migration 1308).

The world is the A5.5 replace-chain harness (the writer's own substeps, the pinned Swiss corpus, the stubbed L1 of the test database's
stand-in chart), cloned twice: WITHOUT migration 1308 (the layer is OFF: today's behaviour) and WITH it (the layer is ON).

The near-miss is a REAL one of the stand-in chart: Jupiter's retrograde loop of 2003-12-15 to 2004-01-23 stays inside the one-degree band of
its aspect ray to the stand-in Venus (point:265.39, ray level 145.39), comes as close as 0.396 degrees and never reaches it.

What is pinned:
  * layer OFF, full build: the near-miss is REFUSED at verify exactly as before (so every test below that completes fails without the change);
  * layer ON: it is STORED with the right bounds, as exactly ONE standalone UNSCORED interval (score NULL, near_miss_unscored, standing near_miss);
  * NONINTERFERENCE: every scored table (contacts, identities, records, prerequisites, windows, memberships, coverage, the inventory) is
    byte-identical with the layer on and off — on a horizon WITH the near-miss and on one WITHOUT;
  * a rebuild REPLACES (same row once, never twice; a horizon without it leaves none), with stable ids;
  * each horizon edge (clipped at the start, clipped at the end): the whole stretch is stored, same id;
  * the in-build cross-check: a near-miss the certifier finds and the builder did not store is refused by name;
  * a validated test slice keeps the interim (reported, nothing stored) even with the storage present;
  * the table refuses a score, an UPDATE, a TRUNCATE, and any write once the generation is sealed."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import near_miss as nm

from . import test_a53_inventory as base
from .test_a53_record_store import MIGRATIONS
from .test_a55_replace_chain import FULLL, _World, template  # noqa: F401
from .test_c46_slice_transitions import _SliceWorld

UTC = timezone.utc
GEN = writer_mod.GENERATION
CLS = "marriage"
MIGRATION_1308 = MIGRATIONS / "1308_gochara_near_miss_storage.sql"
D = lambda y, m, d: datetime(y, m, d, tzinfo=UTC)          # noqa: E731
NEAR = (D(2003, 11, 1), D(2004, 3, 1))                     # holds the whole Jupiter stretch
CLIP_START = (D(2004, 1, 1), D(2004, 3, 1))                # the horizon starts inside it
CLIP_END = (D(2003, 11, 1), D(2004, 1, 15))                # the horizon ends inside it (after the AD boundary, so every stub row is consumed)
KEY = ("jupiter", "aspect", "point:265.39")

#: everything the scored path stores for the generation — the tables a near-miss must never change
SCORED_TABLES = ("ka_gochara_contact", "ka_gochara_relationship_record", "ka_gochara_record_prerequisite", "ka_gochara_eval_window",
                 "ka_gochara_eval_window_record", "kala_gochara_coverage", "ka_gochara_search_inventory", "ka_gochara_search_obligation",
                 "ka_gochara_search_interval", "ka_gochara_search_path_pin", "ka_gochara_search_input_snapshot",
                 "ka_gochara_contact_identity", "ka_gochara_physical_object")


#: daśā rows for 2003-2004 added to the stubbed L1 of BOTH templates (the harness's own rows cover 2024-2026 only, and P1 cannot be verified
#: over a horizon with no running period). An AD boundary falls on 2004-01-10, INSIDE the Jupiter stretch: the junction field has something to find.
AD_BOUNDARY = D(2004, 1, 10)
EXTRA_DASHA = [  # (id, level, parent, lord, start, end)
    (101, 1, None, "Saturn", D(2003, 6, 1), D(2004, 6, 1)),
    (102, 2, 101, "Venus", D(2003, 6, 1), AD_BOUNDARY), (103, 2, 101, "Sun", AD_BOUNDARY, D(2004, 6, 1)),
    (104, 3, 102, "Mars", D(2003, 6, 1), AD_BOUNDARY), (105, 3, 103, "Rahu", AD_BOUNDARY, D(2004, 6, 1)),
]


def _clone(admin, source, dsn, tag, prepare):
    import psycopg
    from psycopg.conninfo import make_conninfo
    name = f"{base.DB_PREFIX}{tag}_{uuid.uuid4().hex[:8]}"
    assert name.startswith(base.DB_PREFIX)
    admin.execute(f'CREATE DATABASE "{name}" TEMPLATE "{source}"')
    new_dsn = make_conninfo(dsn, dbname=name)
    try:
        conn = psycopg.connect(new_dsn, autocommit=True, connect_timeout=3)
        try:
            with conn.transaction():
                prepare(conn)
        finally:
            conn.close()
    except BaseException:
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        raise
    return name, new_dsn


@pytest.fixture(scope="module")
def template_off(template):         # noqa: F811
    """The A5.5 template plus the 2003-2004 daśā rows. NO migration 1308: the near-miss layer is OFF."""
    admin, tpl, dsn = template

    def prepare(conn):
        for i, level, parent, lord, start, end in EXTRA_DASHA:
            conn.execute(
                "INSERT INTO public.chart_dashas (dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, parent_row_id, lord_graha,"
                " start_iso, end_iso, build_id, verification_pass_status) VALUES (%s, %s, 'lahiri_chitrapaksha', 'vimshottari', %s, %s, %s, %s,"
                " %s, %s, 'two_pass_verified')",
                (str(uuid.UUID(int=i)), base.CHART_ID, level, None if parent is None else str(uuid.UUID(int=parent)), lord, start, end,
                 base.PINNED_BUILD))
    name, new_dsn = _clone(admin, tpl, dsn, "d1off", prepare)
    try:
        yield admin, name, new_dsn
    finally:
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


@pytest.fixture(scope="module")
def template_nm(template_off):
    """`template_off` plus migration 1308 (the REAL file, applied as the migration runner applies it: in one transaction). The layer is ON."""
    admin, tpl, dsn = template_off
    name, new_dsn = _clone(admin, tpl, dsn, "d1on", lambda conn: conn.execute(MIGRATION_1308.read_text()))
    try:
        yield admin, name, new_dsn
    finally:
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


def _records_and_windows(w, horizon, cls=CLS):
    """The plan's head and the class chain up to, not including, verify."""
    w.step(writer_mod.MANIFEST_SUBSTEP, horizon)
    w.step(writer_mod.SNAPSHOT_SUBSTEP, horizon)
    w.step(f"inventory:{cls}", horizon)
    w.step(f"coverage:{cls}", horizon)
    notes = []
    for p in writer_mod.RECORD_PATHS:
        notes.append(w.step(f"record:{cls}:{p}", horizon).notes)
    for p in writer_mod.WINDOW_PATHS:
        w.step(f"window:{cls}:{p}", horizon)
    return notes


def _build(w, horizon, cls=CLS):
    notes = _records_and_windows(w, horizon, cls)
    return notes, w.step(f"verify:{cls}", horizon)


#: wall-clock stamps of WHEN a row was written — the only columns left out of the byte comparison (they differ between any two builds)
CLOCKS = ("created_at", "computed_at", "updated_at", "finalized_at")


def _scored(w) -> dict:
    """Every scored table of the world, row for row, as canonical text, minus the wall-clock stamps in `CLOCKS` and nothing else."""
    strip = "".join(f" - '{c}'" for c in CLOCKS)
    return {t: [r[0] for r in w.conn.execute(f"SELECT (to_jsonb(x){strip})::text FROM public.{t} x ORDER BY 1").fetchall()]
            for t in SCORED_TABLES}


def _near_misses(w):
    return w.conn.execute(
        "SELECT o.body, o.relation_kind, o.canonical_target, n.near_miss_id::text, n.ordinal, n.t_in, n.t_out, n.t_closest, n.clearance_deg,"
        " n.proximity, n.standing, n.score, n.score_reason, n.coverage, n.junction, n.junction_complete, n.level_deg, n.solver_method"
        " FROM public.ka_gochara_near_miss n JOIN public.ka_gochara_near_miss_object o USING (near_miss_object_id)"
        " WHERE n.generation = %s ORDER BY n.t_in", (GEN,)).fetchall()


def _searches(w):
    return w.conn.execute(
        "SELECT o.body, o.relation_kind, o.canonical_target, s.near_miss_count, lower(s.horizon), upper(s.horizon), s.searched_complete,"
        " s.layer_version FROM public.ka_gochara_near_miss_search s JOIN public.ka_gochara_near_miss_object o USING (near_miss_object_id)"
        " WHERE s.generation = %s ORDER BY 1, 2, 3", (GEN,)).fetchall()


@pytest.fixture()
def off(template_off):
    w = _World(template_off)
    try:
        yield w
    finally:
        w.close()


@pytest.fixture()
def on(template_nm):
    w = _World(template_nm)
    try:
        yield w
    finally:
        w.close()


@pytest.fixture(scope="module")
def built_on(template_nm):
    """ONE layer-on build over the horizon that holds the near-miss, shared by the read-only assertions."""
    w = _World(template_nm)
    try:
        notes, verify = _build(w, NEAR)
        yield w, notes, verify
    finally:
        w.close()


# ── layer OFF: nothing changed ───────────────────────────────────────────────────────────────────────────────────────────────

def test_without_the_storage_a_full_build_still_refuses_the_near_miss_at_verify(off):
    assert not nm.NearMissStore(off.conn).layer_present()
    notes = _records_and_windows(off, NEAR)
    assert not any("near-miss layer" in n for n in notes)
    with pytest.raises(RuntimeError, match=r"contact geometry certification failed marriage: jupiter aspect point:265\.39: expected contact "
                                           r"\[2003-12-15.*is not in the ledger"):
        off.step(f"verify:{CLS}", NEAR)


# ── layer ON: stored, as one unscored interval ──────────────────────────────────────────────────────────────────────────────

def test_the_near_miss_is_stored_with_its_bounds_and_the_build_completes(built_on):
    w, notes, verify = built_on
    assert nm.NearMissStore(w.conn).layer_present()
    rows = _near_misses(w)
    assert len(rows) == 1, rows
    (body, rel, target, _id, ordinal, t_in, t_out, t_closest, clearance, proximity, _st, _sc, _sr, coverage, _j, _jc, level, method) = rows[0]
    assert (body, rel, target) == KEY and abs(level - 145.39) < 1e-9
    assert t_in.date().isoformat() == "2003-12-15" and t_out.date().isoformat() == "2004-01-23"                # 39 days, the WHOLE stretch
    assert t_closest.date().isoformat() in ("2004-01-03", "2004-01-04") and abs(clearance - 0.396) < 0.005
    assert abs(proximity - (1.0 - clearance)) < 1e-12 and method == "swiss_refined_extremum"
    assert "clipped_by_horizon" not in coverage and coverage["stations"] == 1
    assert "near-miss(es) stored as standalone unscored intervals" in " ".join(notes)
    assert "NEAR-MISSES: 1 certified and stored" in verify.notes and "GRAZES REPORTED" not in verify.notes


def test_the_stored_bounds_equal_the_independent_reconstruction_from_the_ephemeris(built_on):
    from services.gochara_kernel import contact_certify as cc
    from services.gochara_kernel.knots import calc_sidereal_lon
    from .conftest import EPHE_PATH
    w, _notes, _verify = built_on

    def real(body, t):
        lon, flag = calc_sidereal_lon(body.title(), t.timestamp() / 86400.0 + 2440587.5, EPHE_PATH)
        assert flag & 2
        return lon
    ((a, b),) = cc.expected_intervals(real, *KEY, *NEAR)
    row = _near_misses(w)[0]
    assert abs((row[5] - a).total_seconds()) < 600 and abs((row[6] - b).total_seconds()) < 600, (row[5], a, row[6], b)
    g = cc.classify_graze(real, *KEY, (a, b), *NEAR)
    assert abs(g["closest_approach_deg"] - row[8]) < 1e-3


def test_it_opens_exactly_one_interval_and_that_interval_is_unscored_and_of_lower_standing(built_on):
    w, _notes, _verify = built_on
    rows = _near_misses(w)
    assert [(r[10], r[11], r[12]) for r in rows] == [("near_miss", None, "near_miss_unscored")]
    assert w.conn.execute("SELECT count(*), count(score) FROM public.ka_gochara_near_miss WHERE generation = %s", (GEN,)).fetchone() == (1, 0)
    # it is NOT a contact, a record, a window or a window member: nothing on the scored path carries its interval or its id
    t_in, t_out, near_id = rows[0][5], rows[0][6], rows[0][3]
    assert w.conn.execute(
        "SELECT count(*) FROM public.ka_gochara_contact c JOIN public.ka_gochara_physical_object o USING (physical_object_id)"
        " WHERE c.generation = %s AND (o.body, o.relation_kind, o.canonical_target) = (%s, %s, %s) AND c.t_in < %s AND c.t_out > %s",
        (GEN, *KEY, t_out, t_in)).fetchone()[0] == 0
    for table, col in (("ka_gochara_contact", "contact_id"), ("ka_gochara_contact_identity", "contact_id"),
                       ("ka_gochara_relationship_record", "record_id"), ("ka_gochara_eval_window", "window_id")):
        assert w.conn.execute(f"SELECT count(*) FROM public.{table} WHERE {col}::text = %s", (near_id,)).fetchone()[0] == 0, table


def test_every_point_object_of_the_class_has_a_search_row_so_empty_is_a_verified_empty(built_on):
    w, _notes, _verify = built_on
    searches = _searches(w)
    keys = writer_mod.GocharaV5Writer._near_miss_obligation_keys(
        type("C", (), {"db_conn": w.conn})(), base.CHART_ID, CLS)
    assert keys and {tuple(s[:3]) for s in searches} >= set(keys)
    by_key = {tuple(s[:3]): s for s in searches}
    assert by_key[KEY][3] == 1 and sum(s[3] for s in searches) == 1                                # one near-miss in all; the rest verified empty
    assert all(s[4] == NEAR[0] and s[5] == NEAR[1] and s[6] is True and s[7] == nm.LAYER_VERSION for s in searches)


def test_the_junction_field_is_stored_and_says_what_is_not_known(built_on):
    w, _notes, _verify = built_on
    junction, complete = _near_misses(w)[0][14], _near_misses(w)[0][15]
    assert set(junction) >= {"sign_ingress", "nakshatra_ingress", "dasha_boundary", "contains_junction", "interval_rule"}
    assert junction["sign_ingress"]["state"] == "complete" and junction["nakshatra_ingress"]["state"] == "complete"     # the substrate covers it
    assert junction["sign_ingress"]["events"] == [] and junction["nakshatra_ingress"]["events"] == []                   # Jupiter near 145.39: no ingress
    # the AD boundary of 2004-01-10 falls inside [t_in, t_out): listed with the daśā row it comes from
    dasha = junction["dasha_boundary"]
    assert dasha["state"] == "complete" and [(e["level"], e["t"]) for e in dasha["events"]] == [("AD", AD_BOUNDARY.isoformat())]
    assert dasha["events"][0]["dasha_row_id"] in (str(uuid.UUID(int=102)), str(uuid.UUID(int=103)))
    assert complete is True and junction["contains_junction"] is True


# ── NONINTERFERENCE: the scored output is byte-identical with the layer on and off ──────────────────────────────────────────

def test_on_a_horizon_WITH_the_near_miss_every_scored_table_is_byte_identical_with_the_layer_on_and_off(off, built_on):
    w, _notes, _verify = built_on
    _records_and_windows(off, NEAR)                   # the layer-off build cannot verify (refused above); verify writes none of these tables
    a, b = _scored(off), _scored(w)
    assert sum(len(v) for v in a.values()) > 50, {k: len(v) for k, v in a.items()}                 # the comparison is not vacuous
    # every other timestamp column of a scored table IS compared: the data instants (t_in, t_out, t_exact, supports) are in the bytes
    assert '"t_in"' in a["ka_gochara_contact"][0] and '"t_exact"' in a["ka_gochara_contact"][0]
    for t in SCORED_TABLES:
        assert a[t] == b[t], f"{t}: the near-miss layer changed a scored table"
    assert len(a["ka_gochara_eval_window"]) > 0 and len(a["ka_gochara_contact"]) > 0


def test_on_a_horizon_WITHOUT_a_near_miss_everything_is_byte_identical_and_nothing_is_stored(off, on):
    _notes_off, verify_off = _build(off, FULLL)
    _notes_on, verify_on = _build(on, FULLL)
    a, b = _scored(off), _scored(on)
    assert sum(len(v) for v in a.values()) > 50
    for t in SCORED_TABLES:
        assert a[t] == b[t], f"{t}: the near-miss layer changed a scored table"
    assert _near_misses(on) == [] and _searches(on) and all(s[3] == 0 for s in _searches(on))
    assert "NEAR-MISSES: 0 certified and stored" in verify_on.notes and "NEAR-MISS" not in verify_off.notes
    assert verify_on.notes.replace(verify_on.notes[verify_on.notes.index("; NEAR-MISSES"):verify_on.notes.index("; verification NOT persisted")], "") \
        == verify_off.notes                                                                         # the verify result is otherwise the same text


# ── a rebuild REPLACES ───────────────────────────────────────────────────────────────────────────────────────────────────────

def test_a_rebuild_replaces_the_near_miss_rows_and_never_accretes(on):
    _build(on, NEAR)
    first, first_searches = _near_misses(on), _searches(on)
    assert len(first) == 1
    _build(on, NEAR)                                   # the same build again
    assert _near_misses(on) == first and _searches(on) == first_searches
    snap = on.step(writer_mod.MANIFEST_SUBSTEP, FULLL)  # a horizon that does NOT hold it: the row goes
    assert snap is not None
    note = on.step(writer_mod.SNAPSHOT_SUBSTEP, FULLL).notes
    assert f"near-miss layer replaced (near-misses 1, searches {len(first_searches)})" in note
    assert _near_misses(on) == [] and _searches(on) == []
    _build(on, NEAR)                                   # and back: the SAME identity
    assert [r[3] for r in _near_misses(on)] == [first[0][3]]


def test_two_classes_that_share_the_object_store_it_once(on):
    _records_and_windows(on, NEAR, "marriage")
    before = _near_misses(on)
    assert len(before) == 1
    for step in ("inventory", "coverage"):
        on.step(f"{step}:romantic_start", NEAR)
    notes = [on.step(f"record:romantic_start:{p}", NEAR).notes for p in writer_mod.RECORD_PATHS]
    assert _near_misses(on) == before                                                              # no second row for a shared object
    assert any("already stored by another grain" in n for n in notes) or all("near-miss layer" not in n for n in notes)


# ── each horizon edge ────────────────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("horizon, clipped", [(CLIP_START, ["start"]), (CLIP_END, ["end"])])
def test_a_near_miss_cut_by_a_horizon_edge_is_stored_whole_with_the_same_identity(on, built_on, horizon, clipped):
    whole = _near_misses(built_on[0])[0]
    _notes, verify = _build(on, horizon)
    (row,) = _near_misses(on)
    assert row[3] == whole[3] and row[4] == whole[4]                                               # same id, same ordinal: a horizon never renumbers
    assert (row[5], row[6]) == (whole[5], whole[6])                                                # the WHOLE stretch, not the horizon part
    assert row[13]["clipped_by_horizon"] == clipped
    lo, hi = (datetime.fromisoformat(x) for x in row[13]["horizon_interval"])
    assert lo == max(whole[5], horizon[0]) and hi == min(whole[6], horizon[1])
    assert (row[11], row[12]) == (None, "near_miss_unscored") and "NEAR-MISSES: 1 certified and stored" in verify.notes
    # the stretch runs outside the build horizon, so the daśā rows the snapshot consumed do not cover it: NOT KNOWN — the boundary found is listed
    assert row[14]["dasha_boundary"]["state"] == "unknown" and row[15] is False


# ── the in-build cross-check ─────────────────────────────────────────────────────────────────────────────────────────────────

def test_a_near_miss_the_certifier_finds_and_the_builder_did_not_store_is_refused_by_name(on):
    _records_and_windows(on, NEAR)
    with on.conn.transaction():
        on.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (base.CHART_ID,))
        on.conn.execute("DELETE FROM public.ka_gochara_near_miss WHERE generation = %s", (GEN,))
    with pytest.raises(RuntimeError, match=r"near-miss certification failed marriage: near_miss_reported_but_unstored: jupiter aspect point:265\.39"):
        on.step(f"verify:{CLS}", NEAR)


def test_an_object_with_no_search_row_is_refused_by_name(on):
    _records_and_windows(on, FULLL)
    with on.conn.transaction():
        on.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (base.CHART_ID,))
        on.conn.execute("DELETE FROM public.ka_gochara_near_miss_search WHERE generation = %s", (GEN,))
    with pytest.raises(RuntimeError, match="near-miss certification failed marriage: near_miss_unsearched"):
        on.step(f"verify:{CLS}", FULLL)


# ── a validated test slice keeps the interim, storage present or not ────────────────────────────────────────────────────────

def test_under_a_test_slice_the_near_miss_is_reported_and_nothing_is_stored_even_with_the_storage_present(template_nm):
    sliced = _SliceWorld(template_nm)
    try:
        rid = sliced.run_id(sliced.marker_for(NEAR))
        sliced.step_as(writer_mod.MANIFEST_SUBSTEP, rid)
        sliced.step_as(writer_mod.SNAPSHOT_SUBSTEP, rid)
        sliced.step_as(f"inventory:{CLS}", rid)
        sliced.step_as(f"coverage:{CLS}", rid)
        for p in writer_mod.RECORD_PATHS:
            assert "near-miss layer" not in sliced.step_as(f"record:{CLS}:{p}", rid).notes
        for p in writer_mod.WINDOW_PATHS:
            sliced.step_as(f"window:{CLS}:{p}", rid)
        result = sliced.step_as(f"verify:{CLS}", rid)
        assert "GRAZES REPORTED, NOT RAISED (validated test slice; 1)" in result.notes and "jupiter aspect point:265.39" in result.notes
        assert _near_misses(sliced) == [] and _searches(sliced) == []
        assert sliced.conn.execute("SELECT count(*) FROM public.ka_gochara_near_miss_object").fetchone()[0] == 0
    finally:
        sliced.close()


# ── the table's own walls ────────────────────────────────────────────────────────────────────────────────────────────────────

def _one_row_sql(score="NULL", reason="'near_miss_unscored'", standing="'near_miss'", clearance="0.3"):
    return ("INSERT INTO public.ka_gochara_near_miss (chart_id, generation, near_miss_id, near_miss_object_id, ordinal, level_deg, t_in, t_out,"
            " t_closest, closest_state, clearance_deg, orb_deg, proximity, standing, score, score_reason, junction, junction_complete, coverage,"
            " solver_method, delta_t, precision_regime) SELECT chart_id, generation, gen_random_uuid(), near_miss_object_id, 99, level_deg, t_in,"
            f" t_out, t_closest, closest_state, {clearance}, orb_deg, proximity, {standing}, {score}, {reason}, junction, junction_complete,"
            " coverage, solver_method, delta_t, precision_regime FROM public.ka_gochara_near_miss LIMIT 1")


@pytest.mark.parametrize("kw, constraint", [({"score": "0.5"}, "kgnm_unscored_ck"), ({"reason": "'scored'"}, "kgnm_score_reason_ck"),
                                             ({"standing": "'contact'"}, "kgnm_standing_ck"), ({"clearance": "0"}, "kgnm_clearance_positive_ck"),
                                             ({"clearance": "1.0"}, "kgnm_clearance_positive_ck")])
def test_the_table_refuses_a_score_another_standing_and_a_non_positive_clearance(built_on, kw, constraint):
    import psycopg
    w = built_on[0]
    with pytest.raises(psycopg.errors.CheckViolation, match=constraint):
        with w.conn.transaction():
            w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (base.CHART_ID,))
            w.conn.execute(_one_row_sql(**kw))


def test_the_rows_cannot_be_updated_or_truncated(built_on):
    import psycopg
    w = built_on[0]
    for table in ("ka_gochara_near_miss", "ka_gochara_near_miss_search"):
        with pytest.raises(psycopg.errors.RaiseException, match="UPDATE refused"):
            with w.conn.transaction():
                w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (base.CHART_ID,))
                w.conn.execute(f"UPDATE public.{table} SET created_at = now()")
    for table in nm.TABLES:
        with pytest.raises(psycopg.errors.RaiseException, match="TRUNCATE refused"):
            w.conn.execute(f"TRUNCATE public.{table} CASCADE")
    with pytest.raises(psycopg.errors.RaiseException, match="insert-only"):
        with w.conn.transaction():
            w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (base.CHART_ID,))
            w.conn.execute("DELETE FROM public.ka_gochara_near_miss_object")
    assert len(_near_misses(w)) == 1


def test_migration_1308_is_idempotent_and_changes_no_existing_object(template_nm):
    """Applied a second time it is a no-op; and it creates no function and alters no table that existed before it (additive only)."""
    w = _World(template_nm)
    try:
        def catalog():
            return (w.conn.execute("SELECT p.oid::regprocedure::text, md5(pg_get_functiondef(p.oid)) FROM pg_proc p JOIN pg_namespace n"
                                   " ON n.oid = p.pronamespace WHERE n.nspname = 'public' AND p.prokind = 'f' ORDER BY 1").fetchall(),
                    w.conn.execute("SELECT table_name, column_name, data_type, is_nullable FROM information_schema.columns"
                                   " WHERE table_schema = 'public' ORDER BY 1, 2").fetchall(),
                    w.conn.execute("SELECT tgrelid::regclass::text, tgname FROM pg_trigger WHERE NOT tgisinternal ORDER BY 1, 2").fetchall())
        before = catalog()
        with w.conn.transaction():
            w.conn.execute(MIGRATION_1308.read_text())
        assert catalog() == before
    finally:
        w.close()


def test_migration_1308_adds_exactly_three_tables_and_their_triggers(template_off, template_nm):
    off_w, on_w = _World(template_off), _World(template_nm)
    try:
        def funcs(w):
            return w.conn.execute("SELECT p.oid::regprocedure::text, md5(pg_get_functiondef(p.oid)) FROM pg_proc p JOIN pg_namespace n"
                                  " ON n.oid = p.pronamespace WHERE n.nspname = 'public' AND p.prokind = 'f' ORDER BY 1").fetchall()

        def tables(w):
            return {r[0] for r in w.conn.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'").fetchall()}

        def cols(w, skip):
            return [r for r in w.conn.execute("SELECT table_name, column_name, data_type, is_nullable, column_default FROM"
                                              " information_schema.columns WHERE table_schema = 'public' ORDER BY 1, 2").fetchall()
                    if r[0] not in skip]

        def triggers(w, skip):
            return [r for r in w.conn.execute("SELECT tgrelid::regclass::text, tgname FROM pg_trigger WHERE NOT tgisinternal"
                                              " ORDER BY 1, 2").fetchall() if r[0] not in skip]
        assert funcs(off_w) == funcs(on_w)                                          # no function created, none replaced
        assert tables(on_w) - tables(off_w) == set(nm.TABLES) and tables(off_w) <= tables(on_w)
        assert cols(off_w, nm.TABLES) == cols(on_w, nm.TABLES)                      # no existing table altered
        assert triggers(off_w, nm.TABLES) == triggers(on_w, nm.TABLES)              # no trigger added to an existing table
    finally:
        off_w.close()
        on_w.close()
