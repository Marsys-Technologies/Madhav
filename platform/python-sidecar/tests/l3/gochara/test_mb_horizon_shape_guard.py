"""The measuring-build PR, writer side (FINAL_BUILD_SCOPE FB-1..FB-4, FB-8; steward MEASURING-BUILD, TIMEOUT-RULING, MB-ADDITIONS 1-3, 6).

No database, no ephemeris: recording fakes answer exactly the reads the writer issues.

  (a) an ABSENT config horizon is DERIVED from the raw life-event-log rows and the run's build date (never a constant), refused by name when it cannot be;
  (b) the horizon BASIS is pinned in the manifest vector beside the horizon, and a re-derivation that disagrees drifts by name;
  (c) the third slice shape `all_classes_full` (every scored class, the whole derived horizon): accepted, refused for a subset or a different horizon, and its
      plan is the whole default plan;
  (d) the state guard: one read-only SELECT at the top of every substep, refused by name when the row is present and not `building`, skip-on-absent;
  (e) the agent names the enumerators put on edges are the exact lowercase set the kernel uses.
"""
from __future__ import annotations

import dataclasses
from datetime import date, datetime, timezone

import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from pipeline.orchestrator.writers import ContextSpec, SubStep
from services.gochara_kernel import horizon as hz
from services.gochara_kernel import input_vector as iv

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
UTC = timezone.utc
# the REAL runner shape (birth_params._to_birth_params): there is no birth_date key, the birth date is the date of datetime_iso
BIRTH_PARAMS = {"datetime_iso": "1984-02-05T10:43:00", "latitude_deg": 20.2961, "longitude_deg": 85.8245, "tz_offset_hours": 5.5, "place_name": "Bhubaneswar", "subject_label": "native"}
FULL = (datetime(1998, 1, 1, tzinfo=UTC), datetime(2084, 2, 5, tzinfo=UTC))

# the raw rows the log holds (id, date, confidence, shape): the birth entry, placeholders, and the first fully dated event
def _lel(uid, lel_id, d, conf="exact", domain="other/other", shape="point", parent=None):
    """A row as the writer's SELECT returns it: event_id (uuid5), event_date, category, event_type, domain, provenance lel_id, provenance subcategory, shape,
    date_confidence, interval_start, interval_end, chain_parent_event_id, date_tightened_at."""
    return (uid, d, "other", "other", domain, lel_id, None, shape, conf, None, None, parent, None)


LEL_ROWS = [_lel("u-birth", "EVT.1984.02.05.01", date(1984, 2, 5), domain="other/birth"), _lel("u-1995", "EVT.1995.XX.XX.01", date(1995, 7, 1), "year_only"),
            _lel("u-1998", "EVT.1998.02.16.01", date(1998, 2, 16)), _lel("u-2001", "EVT.2001.03.XX.01", date(2001, 3, 1), "month_known"),
            _lel("u-2007", "EVT.2007.06.10.01", date(2007, 6, 10))]


class _Res:
    def __init__(self, rows):
        self.rows = rows

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)


class _Conn:
    """Answers the horizon derivation's reads and the guard's read; records every statement; any lifecycle call is a failure."""

    def __init__(self, lel=LEL_ROWS, created=datetime(2026, 10, 6, 3, 0, tzinfo=UTC), throughput=None, manifest=None, undefined_throughput=False):
        self.lel, self.created, self.throughput = lel, created, throughput
        self.manifest, self.undefined_throughput = manifest, undefined_throughput
        self.statements: list[tuple[str, tuple]] = []

    def execute(self, sql, params=()):
        self.statements.append((sql, params))
        if "FROM public.life_events" in sql:
            return _Res(self.lel)
        if "SELECT created_at FROM public.build_runs" in sql:
            return _Res([] if self.created is None else [(self.created,)])
        if "asset_throughput" in sql:
            if self.undefined_throughput:
                raise type("UndefinedTable", (Exception,), {})("relation does not exist")
            return _Res([] if self.throughput is None else [(self.throughput,)])
        if "FROM public.build_runs" in sql:
            return _Res([] if self.manifest is None else [(self.manifest, writer_mod._manifest_digest(self.manifest))])
        return _Res([])

    def commit(self):
        raise AssertionError("writer committed ctx.db_conn")

    def rollback(self):
        raise AssertionError("writer rolled back ctx.db_conn")

    def close(self):
        raise AssertionError("writer closed ctx.db_conn")


def _ctx(conn=None, dry_run=False, **config) -> ContextSpec:
    return ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-1", db_conn=conn if conn is not None else _Conn(),
                       config={"chart_id": CHART_ID, **config}, dry_run=dry_run)


# ── (a) derivation from the database ──────────────────────────────────────────────────────────────────────────────────────────────────

def test_an_absent_horizon_is_derived_from_the_raw_log_rows_to_the_pinned_chart_horizon_and_the_rows_are_not_pre_filtered():
    conn = _Conn()
    got = writer_mod._effective_horizon(_ctx(conn, birth_params=BIRTH_PARAMS), None)
    assert tuple(got) == FULL == tuple(writer_mod.DEFAULT_HORIZON)
    log_read = [(sql, p) for sql, p in conn.statements if "life_events" in sql]
    assert len(log_read) == 1 and log_read[0][1] == (CHART_ID,), "every raw row of the CHART is read (migration 423): the only filter is the chart"
    sql = log_read[0][0]
    assert "WHERE chart_id = %s" in sql and "WHERE chart_id = %s ORDER BY" in sql and "shape" in sql and "interval_start" in sql and "chain_parent_event_id" in sql
    assert "provenance->>'lel_id'" in sql and "provenance->>'subcategory'" in sql and "domain" in sql and "date_tightened_at" in sql and "event_type" in sql


def test_the_derivation_reports_how_many_raw_rows_it_set_aside():
    h = writer_mod._derive_horizon(_ctx(birth_params=BIRTH_PARAMS))
    assert (len(h.consumed_rows), h.excluded_not_fully_dated) == (5, 2) and h.first_event.provenance_lel_id == "EVT.1998.02.16.01" and h.birth_row.provenance_lel_id == "EVT.1984.02.05.01"


def test_the_build_date_is_the_runs_created_at_taken_as_a_utc_date():
    late = datetime(2026, 10, 5, 23, 30, tzinfo=timezone(__import__("datetime").timedelta(hours=-5)))        # 2026-10-06 04:30 UTC
    h = writer_mod._derive_horizon(_ctx(_Conn(created=late), birth_params=BIRTH_PARAMS))
    assert h.build_date == date(2026, 10, 6)


@pytest.mark.parametrize("config, conn, match", [
    ({}, None, "no birth date"),                                                                           # no birth parameters
    ({"birth_params": {"datetime_iso": ""}}, None, "no birth date"),
    ({"birth_params": {"birth_date": "1984-02-05"}}, None, "no birth date"),                              # the key the real runner does NOT pass
    ({"birth_params": {"datetime_iso": "not-a-date"}}, None, "not a date"),
    ({"birth_params": BIRTH_PARAMS}, _Conn(created=None), "no created_at"),                                  # no build date to take
])
def test_an_underivable_horizon_is_refused_by_name_never_the_constant(config, conn, match):
    with pytest.raises(writer_mod.HorizonUnderivable, match=match):
        writer_mod._effective_horizon(_ctx(conn, **config), None)


def test_a_derived_horizon_outside_the_substrate_domain_is_refused_by_name_on_both_edges():
    late_birth = {**BIRTH_PARAMS, "datetime_iso": "1990-07-01T08:00:00"}                                              # end 2090-07-01 > the domain end
    with pytest.raises(hz.HorizonOutsideSubstrateDomain, match="horizon_outside_substrate_domain"):
        writer_mod._effective_horizon(_ctx(_Conn(lel=[]), birth_params=late_birth), None)
    early = [LEL_ROWS[0], _lel("u-1990", "EVT.1990.06.06.01", date(1990, 6, 6))]                              # start 1990-01-01 < the domain start
    with pytest.raises(hz.HorizonStartBeforeSubstrateDomain, match="horizon_start_before_substrate_domain"):
        writer_mod._effective_horizon(_ctx(_Conn(lel=early), birth_params=BIRTH_PARAMS), None)


def test_an_explicit_config_horizon_is_returned_as_given_and_an_explicit_null_stays_null():
    given = (datetime(2000, 1, 1, tzinfo=UTC), datetime(2001, 1, 1, tzinfo=UTC))
    assert writer_mod._effective_horizon(_ctx(horizon=given), None) is given
    assert writer_mod._effective_horizon(_ctx(horizon=None), None) is None


def test_the_manifest_substep_refuses_a_horizon_outside_the_substrate_domain_before_it_publishes(monkeypatch):
    ctx = _ctx(horizon=(datetime(1998, 1, 1, tzinfo=UTC), datetime(2085, 1, 2, tzinfo=UTC)))                # FB-3 oracle: 2085-01-02
    monkeypatch.setattr(writer_mod, "_require_building", lambda c, ch: None)
    monkeypatch.setattr(writer_mod, "_ephe_path", lambda c: "/nonexistent")
    monkeypatch.setattr(writer_mod, "_require_pinned_chart", lambda ch: None)
    with pytest.raises(hz.HorizonOutsideSubstrateDomain, match="horizon_outside_substrate_domain"):
        writer_mod.GocharaV5Writer().run_substep(ctx, SubStep(key=writer_mod.MANIFEST_SUBSTEP, label=""))


# ── (b) the basis is pinned beside the horizon ────────────────────────────────────────────────────────────────────────────────────────

def test_the_basis_record_is_none_for_a_configured_horizon_and_the_derivation_record_otherwise():
    assert writer_mod._horizon_basis(_ctx(horizon=FULL, birth_params=BIRTH_PARAMS), None) is None
    assert writer_mod._horizon_basis(_ctx(), None) is None                                                   # no birth parameters: nothing to derive
    rec = writer_mod._horizon_basis(_ctx(birth_params=BIRTH_PARAMS), None)
    assert rec["schema"] == "horizon_basis/1" and rec["basis"] == "first_dated_event" and rec["chosen"]["lel_id"] == "EVT.1998.02.16.01" and rec["chosen"]["event_id"] == "u-1998"
    assert rec["chosen"]["event_date"] == "1998-02-16" and rec["chosen"]["date_confidence"] == "exact" and rec["build_date"] == "2026-10-06"
    assert rec["birth_row"]["event_id"] == "u-birth" and rec["birth_row"]["lel_id"] == "EVT.1984.02.05.01" and rec["birth_row"]["column_used"] == "domain"
    assert rec["excluded_not_fully_dated"] == 2 and rec["rows_total"] == 5
    assert len(rec["consumed_rows"]) == 5 and rec["birth_date"] == "1984-02-05"


def _basis():
    from tests.l3.gochara.test_horizon_derivation import _derive, _fixture
    return _derive(_fixture(), date(2026, 10, 6)).basis_record()


def test_the_vector_carries_the_basis_only_when_given_so_a_vector_without_one_is_byte_identical_to_before():
    from tests.l3.gochara.test_a53_input_vector import _mutate
    plain = iv.assemble_vector(_mutate("base"))
    rec = _basis()
    assert "horizon_basis" not in plain and iv.assemble_vector({**_mutate("base"), "horizon_basis": None}) == plain
    pinned = iv.assemble_vector({**_mutate("base"), "horizon_basis": rec})
    assert pinned["horizon_basis"] == rec and {k: v for k, v in pinned.items() if k != "horizon_basis"} == plain
    assert iv.diff_vectors(plain, pinned) == ["horizon_basis"]


def test_diff_vectors_names_horizon_basis_when_a_later_substep_re_derives_a_different_basis():
    a, b = _basis(), dict(_basis(), build_date="2026-10-07")
    assert iv.diff_vectors({"horizon_basis": a}, {"horizon_basis": b}) == ["horizon_basis.build_date"]
    assert iv.diff_vectors({"horizon_basis": a}, {}) == ["horizon_basis"], "a vector that lost its basis drifts too"
    assert iv.diff_vectors({}, {"horizon_basis": a}) == ["horizon_basis"], "and one that gained one"


# steward ruling 3 on MB-1.4: an edit of the log that CHANGES the derived horizon refuses the next substep by name; one that does not is a REPORT line, never a refusal

def test_a_log_edit_that_does_not_change_the_horizon_is_a_report_line_with_the_changed_row_ids_and_never_a_refusal(caplog):
    pinned = writer_mod._horizon_basis(_ctx(birth_params=BIRTH_PARAMS), None)
    more = LEL_ROWS + [_lel("u-2010", "EVT.2010.01.01.01", date(2010, 1, 1))]                                     # a new row after the first dated event: the horizon is unchanged
    with caplog.at_level("WARNING"):
        got = writer_mod._live_basis_for_check(_ctx(_Conn(lel=more), birth_params=BIRTH_PARAMS), None, {"horizon_basis": pinned})
    assert got == pinned, "the PINNED basis is handed to the check: no drift"
    assert any("horizon_basis_rows_changed" in r.message and "u-2010" in r.message for r in caplog.records)


def test_a_log_edit_that_changes_the_horizon_refuses_the_next_substep_by_name():
    pinned = writer_mod._horizon_basis(_ctx(birth_params=BIRTH_PARAMS), None)
    # a different pair for a chart that is NOT the pinned one (no ruling guard): the first dated event is in 2007 now
    other = {"chart_id": "00000000-0000-4000-8000-000000000001"}
    ctx_a = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-1", db_conn=_Conn(), config={**other, "birth_params": BIRTH_PARAMS})
    revised = [r for r in LEL_ROWS if r[5] != "EVT.1998.02.16.01"]
    ctx_b = ContextSpec(asset_id=writer_mod.ASSET_ID, build_id="b-1", db_conn=_Conn(lel=revised), config={**other, "birth_params": BIRTH_PARAMS})
    stored = {"horizon_basis": writer_mod._horizon_basis(ctx_a, None)}
    with pytest.raises(writer_mod.HorizonBasisHorizonChanged, match="horizon_basis_horizon_changed") as e:
        writer_mod._live_basis_for_check(ctx_b, None, stored)
    assert "2007-01-01" in str(e.value) and "1998-01-01" in str(e.value) and "u-1998" in str(e.value)
    assert pinned["horizon"][0].startswith("1998-01-01")


def test_the_ruling_guard_refuses_the_pinned_chart_whose_log_derives_another_pair_at_plan_time():
    revised = [r for r in LEL_ROWS if r[5] != "EVT.1998.02.16.01"]
    ctx = _ctx(_Conn(lel=revised), birth_params=BIRTH_PARAMS)
    with pytest.raises(hz.HorizonDerivationDisagreesWithRuling, match="horizon_derivation_disagrees_with_ruling"):
        writer_mod.GocharaV5Writer().plan_substeps(ctx)
    ok = _ctx(_Conn(), birth_params=BIRTH_PARAMS)
    assert len(writer_mod.GocharaV5Writer().plan_substeps(ok)) == 298


def test_verify_live_and_verify_replay_carry_the_stored_basis_unless_the_caller_gives_one():
    import inspect
    for fn in (iv.verify_live, iv.verify_replay):
        assert 'kw.setdefault("horizon_basis", stored.get("horizon_basis"))' in inspect.getsource(fn)


# ── (c) all_classes_full ──────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _marker(run="all_classes_full", classes=None, horizon=None):
    return {"schema": writer_mod.TEST_SLICE_SCHEMA, "run": run, "horizon": [h.isoformat() for h in (horizon or FULL)],
            "classes": list(classes if classes is not None else writer_mod.SCORED_CLASSES)}


def test_all_classes_full_is_every_scored_class_over_the_whole_horizon_and_nothing_else():
    sl = writer_mod._validate_test_slice(_marker())
    assert sl.run == "all_classes_full" and sl.horizon == FULL and set(sl.classes) == set(writer_mod.SCORED_CLASSES) and len(sl.classes) == 26
    for bad, match in [(_marker(classes=writer_mod.SCORED_CLASSES[:25]), "all 26 scored classes"),
                       (_marker(horizon=(FULL[0], datetime(2084, 2, 4, tzinfo=UTC))), "full DEFAULT_HORIZON"),
                       (_marker(horizon=(datetime(1998, 1, 2, tzinfo=UTC), FULL[1])), "full DEFAULT_HORIZON"),
                       (_marker(horizon=(FULL[0], datetime(2084, 2, 6, tzinfo=UTC))), "outside DEFAULT_HORIZON")]:
        with pytest.raises(writer_mod.TestSliceRefusal, match=match):
            writer_mod._validate_test_slice(bad)


def test_the_run_time_outer_bound_is_the_derived_horizon_so_a_full_marker_for_another_horizon_is_refused_by_name():
    derived = (datetime(1999, 1, 1, tzinfo=UTC), datetime(2084, 2, 5, tzinfo=UTC))                          # what the database would derive after a log revision
    with pytest.raises(writer_mod.TestSliceRefusal, match="outside DEFAULT_HORIZON"):                        # the staged horizon reaches before the new start
        writer_mod._validate_test_slice(_marker(), derived)
    wider = (datetime(1998, 1, 1, tzinfo=UTC), datetime(2084, 6, 1, tzinfo=UTC))                              # a derived horizon LONGER than the staged one
    with pytest.raises(writer_mod.TestSliceRefusal, match="full DEFAULT_HORIZON"):
        writer_mod._validate_test_slice(_marker(), wider)
    assert writer_mod._validate_test_slice(_marker(horizon=derived), derived).horizon == derived


def test_a_full_marker_is_checked_against_the_database_derivation_when_the_run_carries_birth_parameters():
    manifest = {writer_mod.TEST_SLICE_KEY: _marker()}
    ok = _ctx(_Conn(manifest=manifest), birth_params=BIRTH_PARAMS)
    assert writer_mod._test_slice(ok).run == "all_classes_full"
    revised = [LEL_ROWS[0], _lel("u-1999", "EVT.1999.03.03.01", date(1999, 3, 3))]
    with pytest.raises(hz.HorizonDerivationDisagreesWithRuling, match="horizon_derivation_disagrees_with_ruling"):
        writer_mod._test_slice(_ctx(_Conn(lel=revised, manifest=manifest), birth_params=BIRTH_PARAMS))     # the ruled pair guards the pinned chart before any marker is compared


def test_the_all_classes_full_plan_is_the_whole_default_plan():
    manifest = {writer_mod.TEST_SLICE_KEY: _marker()}
    sliced = [s.key for s in writer_mod.GocharaV5Writer().plan_substeps(_ctx(_Conn(manifest=manifest), horizon=FULL))]
    default = [s.key for s in writer_mod.GocharaV5Writer().plan_substeps(_ctx(_Conn(), horizon=FULL))]
    assert sliced == default and len(sliced) == 298


# ── (d) the state guard ───────────────────────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("state", ["error", "lit", "queued", "incomplete", "stale", "dormant", "mature"])
def test_a_present_row_that_is_not_building_refuses_by_name_and_writes_nothing(state):
    conn = _Conn(throughput=state)
    with pytest.raises(writer_mod.AssetNotBuilding, match=f"^asset_not_building: .* is '{state}', not 'building'"):
        writer_mod._require_building(_ctx(conn), CHART_ID)
    assert all(sql.lstrip().upper().startswith(("SELECT", "SAVEPOINT", "RELEASE", "ROLLBACK TO")) for sql, _ in conn.statements)


def test_a_building_row_passes_and_the_read_is_one_select_keyed_by_chart_and_asset():
    conn = _Conn(throughput="building")
    writer_mod._require_building(_ctx(conn), CHART_ID)
    reads = [(sql, p) for sql, p in conn.statements if "asset_throughput" in sql]
    assert len(reads) == 1 and reads[0][1] == (CHART_ID, writer_mod.ASSET_ID)
    assert reads[0][0].startswith("SELECT state FROM public.asset_throughput") and "chart_id = %s AND asset_id = %s" in reads[0][0]


def test_skip_on_absent_a_missing_row_a_missing_table_a_dry_run_and_a_missing_connection_do_not_refuse():
    writer_mod._require_building(_ctx(_Conn(throughput=None)), CHART_ID)                                     # no row (a harness drives the writer directly)
    writer_mod._require_building(_ctx(_Conn(undefined_throughput=True)), CHART_ID)                           # a schema without the table
    dry = _Conn(throughput="error")
    writer_mod._require_building(_ctx(dry, dry_run=True), CHART_ID)                                          # nothing is written in a dry run
    assert not [1 for sql, _ in dry.statements if "asset_throughput" in sql]
    writer_mod._require_building(dataclasses.replace(_ctx(), db_conn=None), CHART_ID)


def test_a_database_error_other_than_a_missing_table_is_not_swallowed():
    class Boom(_Conn):
        def execute(self, sql, params=()):
            if "asset_throughput" in sql:
                raise RuntimeError("connection lost")
            return super().execute(sql, params)
    with pytest.raises(RuntimeError, match="connection lost"):
        writer_mod._require_building(_ctx(Boom()), CHART_ID)


def test_every_substep_kind_passes_through_the_guard_before_anything_is_resolved_or_written(monkeypatch):
    """The guard sits at the top of run_substep, after only the pinned-chart check, the dry-run return and the (database-free) ephemeris resolution: a non-building
    row refuses a substep of EVERY kind (rules, convention, manifest, snapshot, body, inventory, coverage, record, window, verify) by name, before anything is written."""
    monkeypatch.setattr(writer_mod, "_require_pinned_chart", lambda ch: None)
    called = []
    monkeypatch.setattr(writer_mod, "_ephe_path", lambda c: called.append(1) or "/x")
    cls = writer_mod.SCORED_CLASSES[0]
    keys = [writer_mod.RULES_SUBSTEP, writer_mod.CONVENTION_SUBSTEP, writer_mod.MANIFEST_SUBSTEP, writer_mod.SNAPSHOT_SUBSTEP,
            f"{writer_mod.BODY_SUBSTEP_PREFIX}Sun", f"{writer_mod.INVENTORY_SUBSTEP_PREFIX}{cls}", f"{writer_mod.COVERAGE_SUBSTEP_PREFIX}{cls}",
            f"{writer_mod.RECORD_SUBSTEP_PREFIX}{cls}:P1", f"{writer_mod.WINDOW_SUBSTEP_PREFIX}{cls}:P1", f"{writer_mod.VERIFY_SUBSTEP_PREFIX}{cls}"]
    for key in keys:
        with pytest.raises(writer_mod.AssetNotBuilding):
            writer_mod.GocharaV5Writer().run_substep(_ctx(_Conn(throughput="error"), horizon=FULL), SubStep(key=key, label=""))
    assert len(called) == len(keys), "the ephemeris resolver (no database use) runs first, so a mis-provisioned job still refuses in seconds; the guard follows it"


def test_the_guard_is_the_only_reader_of_asset_throughput_and_the_writer_never_writes_it():
    import inspect
    import re
    src = inspect.getsource(writer_mod)
    assert not re.search(r"(insert\s+into|update|delete\s+from)\s+(public\.)?asset_throughput", src, re.IGNORECASE)
    assert src.count("FROM public.asset_throughput") == 1


# ── (e) agent names ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────

KERNEL_AGENTS = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"}


def test_the_agent_names_the_enumerators_write_are_the_exact_lowercase_kernel_set():
    from services.gochara_kernel import evaluator as ev
    from services.gochara_kernel.substrate import DB_BODY
    from tests.l3.gochara.test_a53_inventory import CHART
    assert {lc for _t, lc in ev._AGENTS} == KERNEL_AGENTS == set(DB_BODY.values())
    for title, lc in ev._AGENTS:
        assert lc == lc.lower() and lc == DB_BODY[title], f"{title!r} -> {lc!r}: the stored agent name is the kernel's lowercase DB body"
    # every edge any scored class enumerates on a path with an enumerator carries one of them, as its agent AND as its object's body
    seen_agents, seen_bodies, enumerated = set(), set(), 0
    for cls in writer_mod.SCORED_CLASSES:
        for path in ("P1", "P2", "P3", "P4"):
            try:
                edges = ev.enumerate_edges(cls, path, CHART)
            except Exception:                                    # a path with no enumerator for the class refuses loudly: nothing to check
                continue
            enumerated += 1
            seen_agents |= {e.agent for e in edges}
            seen_bodies |= {e.obj.body for e in edges}
    assert enumerated > 0 and seen_agents and seen_agents <= KERNEL_AGENTS and seen_bodies <= KERNEL_AGENTS
    assert all(a == a.lower() for a in seen_agents | seen_bodies)


def test_both_production_callers_pass_the_re_derived_basis_to_the_vector_builder_and_the_live_check():
    """The manifest substep PINS the basis (build_input_vector) and every later substep re-derives it and compares (verify_live): both call sites carry
    `horizon_basis=_horizon_basis(ctx, slice_)`. Behaviour is proven on a real database in test_mb_real_db; this keeps a half-applied change from passing
    without one."""
    import inspect
    manifest_src = inspect.getsource(writer_mod.GocharaV5Writer._run_inventory_phase)
    live_src = inspect.getsource(writer_mod._verify_live_inputs)
    assert "gk_input_vector.build_input_vector(" in manifest_src and "horizon_basis=_horizon_basis(ctx, slice_)" in manifest_src
    assert "gk_input_vector.verify_live(" in live_src and "horizon_basis=_live_basis_for_check(ctx, slice_, stored)" in live_src
