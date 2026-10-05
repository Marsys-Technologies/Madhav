"""W1 — the serving reader over a SEALED governed generation (`gochara_kernel.serving_reader.read_v5`).

Every test runs on the A5.3 throwaway database (the real migration chain, L1 tables stubbed) with a generation built by
the real writer steps, published through the ledger and then sealed. Each claim is checked against what the database
itself holds, so it fails if the reader invents, drops or reorders anything:

  named refusals (unknown / unpublished / superseded / unsealed / wrongly sealed / test slice — never an empty list);
  the horizon is the MANIFEST's (entirely before, entirely after, a clip on each side, an inverted range);
  the all-NULL policy returns stored nulls, `chronological_only`, and no invented field; numbers, when the manifest's
  policy allows them, are passed through as stored;
  a zero-window class reads "searched, complete, none" vs "not searched" vs "unverified";
  the near-miss layer is absent / present / not built / mis-shaped, separate, and never counted with windows;
  the order is total and repeatable; the scored edge is the manifest's pin or null with a reason; the module holds no
  literal date and writes nothing.
"""
from __future__ import annotations

import ast
import inspect
import json
import re
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import scope_response as sr
from services.gochara_kernel import serving_reader as rd

from .test_a53_inventory import CHART_ID, H0, H1
from .test_a53_p1_support import GEN
from .test_a53_scope_completeness import _complete_world
from .test_a53_window_verification_gate import CLS, _boot_p3, _consistent_sky, _windows, world  # noqa: F401

UTC = timezone.utc
FORBIDDEN_WINDOW_KEYS = {"valence", "is_adverse", "adverse", "signed_intensity", "raw_intensity", "intensity", "rank",
                         "peak", "peak_date", "strength", "favourable", "recommendation"}


def _t(m, d):
    return datetime(2025, m, d, tzinfo=UTC)


def _iso(t):
    return t.astimezone(UTC).isoformat()


def _seal(w, manifest_id=None):
    """Mark the generation sealed (the seal PATH is not under test here; precedent: test_c48a_sealed_staleness)."""
    with w.conn.transaction():
        if manifest_id is None:
            manifest_id = w.conn.execute(
                "SELECT manifest_id FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = %s",
                (CHART_ID, GEN)).fetchone()[0]
        w.conn.execute("ALTER TABLE public.ka_gochara_generation_seal DISABLE TRIGGER USER")
        w.conn.execute("INSERT INTO public.ka_gochara_generation_seal (chart_id, generation, manifest_id)"
                       " VALUES (%s, %s, %s)", (CHART_ID, GEN, manifest_id))
        w.conn.execute("ALTER TABLE public.ka_gochara_generation_seal ENABLE TRIGGER USER")


def _sealed(w):
    _complete_world(w)
    _seal(w)
    return w


def _unguarded(w, table, sql, params=()):
    """One statement on `table` with its user triggers off (the sealed-generation guards would refuse it)."""
    with w.conn.transaction():
        w.conn.execute(f"ALTER TABLE public.{table} DISABLE TRIGGER USER")
        w.conn.execute(sql, params)
        w.conn.execute(f"ALTER TABLE public.{table} ENABLE TRIGGER USER")


def _set_vector(w, patch_sql, params=()):
    _unguarded(w, "kala_gochara_publication",
               f"UPDATE public.kala_gochara_publication SET input_generation_vector = {patch_sql}"
               " WHERE chart_id = %s AND generation = %s", tuple(params) + (CHART_ID, GEN))


def _read(w, **kw):
    return rd.read_v5(w.conn, CHART_ID, GEN, **kw)


def _stored_window(w):
    return w.conn.execute(
        "SELECT window_id::text, lower(interval), upper(interval), path_id, rule_version, score, evidence_for,"
        " evidence_against, severity, peak_instant, outcome_valence_for_native, objective, objective_value, qualification"
        " FROM public.ka_gochara_eval_window WHERE chart_id = %s AND generation = %s", (CHART_ID, GEN)).fetchall()


def _assert_refused(env, code):
    assert env["refusal"] is not None and env["refusal"]["code"] == code, env["refusal"]
    assert env["refusal"]["detail"]
    # a refusal is never an empty answer: nothing that could be read as "no windows"
    assert env["windows"] is None and env["classes"] is None and env["counts"] is None
    assert "near_miss_intervals" not in env
    json.dumps(env)


# ── the served answer ────────────────────────────────────────────────────────────────────────────────────

def test_a_sealed_published_generation_is_served_with_its_manifest_seal_horizon_and_members(world):
    w = _sealed(world)
    env = _read(w, event_classes=[CLS])
    assert env["refusal"] is None and env["schema"] == rd.ENVELOPE_SCHEMA
    manifest_id, lo, hi = w.conn.execute(
        "SELECT manifest_id::text, lower(horizon), upper(horizon) FROM public.kala_gochara_publication"
        " WHERE chart_id = %s AND generation = %s", (CHART_ID, GEN)).fetchone()
    assert env["generation"] == GEN and env["chart_id"] == CHART_ID
    assert env["manifest_id"] == manifest_id and env["manifest_status"] == "published"
    assert env["seal"]["manifest_id"] == manifest_id and env["seal"]["sealed_at"]
    assert env["seal"]["brief_digest"] is None and env["seal"]["brief_digest_reason"] == "no_approval_receipt"
    assert env["served_horizon"] == {"start": _iso(lo), "end": _iso(hi)} == {"start": _iso(H0), "end": _iso(H1)}
    assert env["stored_scope"] == "stored_non_moon" and env["horizon_clipped"] is None

    stored = _stored_window(w)
    assert len(stored) == 1 and len(env["windows"]) == 1
    win = env["windows"][0]
    assert win["window_id"] == stored[0][0] and win["event_class"] == CLS and win["path_id"] == "P3"
    assert win["interval"] == {"start": _iso(stored[0][1]), "end": _iso(stored[0][2]), "bounds": "[)"}

    # the member is the stored record, joined to ITS contact and physical object
    rec = w.conn.execute(
        "SELECT r.record_id::text, r.agent, r.relation, r.object_role, o.canonical_target, r.contact_id::text,"
        " c.t_in, c.t_exact, c.t_out FROM public.ka_gochara_eval_window_record m"
        " JOIN public.ka_gochara_relationship_record r ON r.record_id = m.record_id"
        " JOIN public.ka_gochara_physical_object o ON o.physical_object_id = r.object_id"
        " JOIN public.ka_gochara_contact c ON c.contact_id = r.contact_id AND c.generation = r.generation"
        " WHERE m.window_id = %s", (win["window_id"],)).fetchall()
    assert len(rec) == 1 == win["member_count"] == len(win["members"])
    m = win["members"][0]
    assert (m["record_id"], m["agent"], m["relation"], m["object_role"], m["target"], m["contact_id"]) == rec[0][:6]
    assert (m["agent"], m["relation"], m["target"]) == ("saturn", "residence", "span:7")
    assert m["t_in"] == _iso(rec[0][6]) == _iso(_t(1, 10)) and m["t_out"] == _iso(rec[0][8]) == _iso(_t(2, 20))
    assert m["t_exact"] == (None if rec[0][7] is None else _iso(rec[0][7]))
    assert m["timing_reason"] is None and m["contact_id"] is not None

    cls = env["classes"]
    assert [c["event_class"] for c in cls] == [CLS]
    assert cls[0]["completeness"] == sr.COMPLETE == cls[0]["coverage"]["completeness"]
    assert cls[0]["windows_matched"] == 1 == cls[0]["windows_returned"] and cls[0]["zero_window_reading"] is None
    assert {l["name"] for l in cls[0]["coverage"]["named_limits"]} >= {"contact_geometry_guarantee", "boundary_tolerance"}
    assert env["counts"]["windows_matched"] == 1 == env["counts"]["windows_returned"]
    assert env["counts"]["windows_truncated"] is False
    json.dumps(env)                                               # a plain JSON-serialisable dict


def test_the_mandatory_constructor_is_called_once_per_class_with_the_effective_horizon(world, monkeypatch):
    w = _sealed(world)
    calls = []
    real = sr.coverage_response

    def spy(conn, **kw):
        calls.append(kw)
        return real(conn, **kw)
    monkeypatch.setattr(sr, "coverage_response", spy)
    env = _read(w, event_classes=[CLS, "career_entry"], date_from=_t(1, 5), date_to=_t(2, 25))
    assert [(c["event_class"], c["horizon"]) for c in calls] == [
        ("career_entry", (_t(1, 5), _t(2, 25))), (CLS, (_t(1, 5), _t(2, 25)))]
    wid = env["windows"][0]["window_id"]
    assert [c["windows"] for c in calls] == [[], [{"window_id": wid}]]
    # and its verdict is carried, not re-decided: breaking the constructor breaks the answer
    monkeypatch.setattr(sr, "coverage_response", lambda conn, **kw: {"completeness": "sentinel_state", "windows": []})
    again = _read(w, event_classes=[CLS])
    assert again["classes"][0]["completeness"] == "sentinel_state"
    assert again["windows"][0]["qualification"] is None
    assert again["windows"][0]["qualification_reason"] == "not_provided_by_coverage_constructor"
    src = inspect.getsource(rd)
    assert '"complete_within_scope"' not in src and "sr.coverage_response(" in src


def test_without_event_classes_the_answer_speaks_for_every_class_the_generation_searched(world):
    w = _sealed(world)
    env = _read(w)
    assert env["classes_source"] == "generation_search_inventory"
    assert [c["event_class"] for c in env["classes"]] == [CLS] and len(env["windows"]) == 1
    assert _read(w, event_classes=[CLS])["classes_source"] == "request"


# ── named refusals: never an empty list ──────────────────────────────────────────────────────────────────

def test_an_unknown_generation_is_refused_by_name(world):
    w = _sealed(world)
    env = rd.read_v5(w.conn, CHART_ID, "9.9", event_classes=[CLS])
    _assert_refused(env, "unknown_generation")
    assert env["manifest_id"] is None and env["seal"] is None and env["served_horizon"] is None
    other_chart = rd.read_v5(w.conn, str(uuid.UUID(int=7)), GEN)
    _assert_refused(other_chart, "unknown_generation")


def test_a_candidate_that_was_never_published_is_refused_by_name(world):
    w = world
    _boot_p3(w)
    _windows(w)
    assert _stored_window(w)                                       # the windows ARE there — and are not served
    env = _read(w, event_classes=[CLS])
    _assert_refused(env, "not_published")
    assert env["refusal"]["manifest_status"] == "candidate" == env["manifest_status"]


@pytest.mark.parametrize("status", ["superseded", "rolled_back"])
def test_a_withdrawn_generation_is_not_served_even_with_its_seal(world, status):
    w = _sealed(world)
    assert _read(w)["refusal"] is None
    _unguarded(w, "kala_gochara_publication",
               "UPDATE public.kala_gochara_publication SET status = %s, superseded_at = now()"
               " WHERE chart_id = %s AND generation = %s", (status, CHART_ID, GEN))
    env = _read(w)
    _assert_refused(env, "not_published")
    assert env["refusal"]["manifest_status"] == status


def test_a_published_generation_without_a_seal_is_refused_by_name(world):
    w = world
    _complete_world(w)                                             # published, verified, complete — but never sealed
    env = _read(w, event_classes=[CLS])
    _assert_refused(env, "not_sealed")
    assert env["manifest_id"] is not None and env["seal"] is None
    _seal(w)
    assert _read(w, event_classes=[CLS])["refusal"] is None        # the seal row is what changed the answer


def test_a_seal_that_names_another_manifest_does_not_serve_this_one(world):
    w = world
    _complete_world(w)
    other = str(uuid.UUID(int=99))
    _seal(w, manifest_id=other)
    env = _read(w)
    _assert_refused(env, "not_sealed")
    assert env["refusal"]["seal_manifest_id"] == other


@pytest.mark.parametrize("patch", [
    "input_generation_vector || '{\"stored_scope\": \"test_slice\"}'::jsonb",
    "input_generation_vector || '{\"test_slice\": {\"classes\": [\"marriage\"]}}'::jsonb"])
def test_a_test_slice_is_refused_by_name_whichever_marker_it_carries(world, patch):
    w = _sealed(world)
    assert _read(w)["refusal"] is None
    _set_vector(w, patch)                                          # even published AND sealed: a slice is never served
    env = _read(w, event_classes=[CLS])
    _assert_refused(env, "test_slice_candidate")


def test_a_manifest_with_no_known_result_policy_is_refused_not_defaulted(world):
    w = _sealed(world)
    _set_vector(w, "input_generation_vector - 'result_policy'")
    env = _read(w)
    _assert_refused(env, "result_policy_unbound")
    assert env["result_policy"] is None and env["numbers_disclosure"] is None


@pytest.mark.parametrize("kw, code", [
    ({"date_from": datetime(2025, 2, 1, tzinfo=UTC), "date_to": datetime(2025, 1, 1, tzinfo=UTC)}, "invalid_range"),
    ({"date_from": datetime(2025, 2, 1, tzinfo=UTC), "date_to": datetime(2025, 2, 1, tzinfo=UTC)}, "invalid_range"),
    ({"date_from": datetime(2025, 2, 1)}, "invalid_request"),                                   # no offset
    ({"at_instant": datetime(2025, 2, 1, tzinfo=UTC), "date_to": datetime(2025, 2, 2, tzinfo=UTC)}, "invalid_request"),
    ({"event_classes": []}, "invalid_request"),
    ({"limit": 0}, "invalid_request")])
def test_a_request_that_makes_no_sense_is_refused_by_name(world, kw, code):
    w = _sealed(world)
    _assert_refused(_read(w, **kw), code)


# ── the horizon is the manifest's ────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("kw, side", [
    ({"date_from": datetime(1990, 1, 1, tzinfo=UTC), "date_to": datetime(1990, 6, 1, tzinfo=UTC)}, "before"),
    ({"date_to": H0}, "before"),                                   # half-open: a range ending AT the start is outside
    ({"date_from": datetime(2031, 1, 1, tzinfo=UTC), "date_to": datetime(2031, 6, 1, tzinfo=UTC)}, "after"),
    ({"date_from": H1}, "after"),
    ({"at_instant": H0 - timedelta(seconds=1)}, "before"),
    ({"at_instant": H1}, "after")])
def test_a_request_entirely_outside_the_served_horizon_is_refused_by_name(world, kw, side):
    w = _sealed(world)
    env = _read(w, event_classes=[CLS], **kw)
    _assert_refused(env, "outside_served_horizon")
    assert env["refusal"]["side"] == side
    assert env["refusal"]["served_horizon"] == {"start": _iso(H0), "end": _iso(H1)} == env["served_horizon"]
    requested = env["refusal"]["requested"]
    if "at_instant" in kw:
        assert requested == {"at_instant": _iso(kw["at_instant"])}
    else:
        assert requested == {"start": _iso(kw["date_from"]) if "date_from" in kw else None,
                             "end": _iso(kw["date_to"]) if "date_to" in kw else None}


@pytest.mark.parametrize("kw, side, effective", [
    ({"date_from": datetime(2024, 11, 1, tzinfo=UTC), "date_to": datetime(2025, 2, 1, tzinfo=UTC)}, "start",
     (H0, datetime(2025, 2, 1, tzinfo=UTC))),
    ({"date_from": datetime(2025, 2, 1, tzinfo=UTC), "date_to": datetime(2025, 6, 1, tzinfo=UTC)}, "end",
     (datetime(2025, 2, 1, tzinfo=UTC), H1)),
    ({"date_from": datetime(2020, 1, 1, tzinfo=UTC), "date_to": datetime(2030, 1, 1, tzinfo=UTC)}, "both", (H0, H1))])
def test_a_partial_overlap_is_clipped_and_says_which_side(world, kw, side, effective):
    w = _sealed(world)
    env = _read(w, event_classes=[CLS], **kw)
    assert env["refusal"] is None
    assert env["horizon_clipped"] == {"side": side,
                                      "requested": {"start": _iso(kw["date_from"]), "end": _iso(kw["date_to"])},
                                      "served_horizon": {"start": _iso(H0), "end": _iso(H1)}}
    assert env["effective_range"] == {"start": _iso(effective[0]), "end": _iso(effective[1]), "kind": "half_open_range"}
    assert len(env["windows"]) == 1
    # completeness is asked for the CLIPPED range, which the search covered — never for the unserved part
    assert env["classes"][0]["completeness"] == sr.COMPLETE


def test_a_request_inside_the_horizon_is_not_marked_clipped_and_the_edges_are_inclusive_exclusive(world):
    w = _sealed(world)
    env = _read(w, date_from=H0, date_to=H1)
    assert env["refusal"] is None and env["horizon_clipped"] is None
    assert _read(w, at_instant=H0)["refusal"] is None             # the start instant is inside


def test_the_horizon_comes_from_the_manifest_row_not_from_the_code(world):
    w = _sealed(world)
    probe = {"date_from": _t(1, 2), "date_to": _t(1, 8)}
    assert _read(w, **probe)["refusal"] is None
    _unguarded(w, "kala_gochara_publication",
               "UPDATE public.kala_gochara_publication SET horizon = tstzrange(%s, %s, '[)')"
               " WHERE chart_id = %s AND generation = %s", (_t(1, 15), _t(2, 15), CHART_ID, GEN))
    env = _read(w, **probe)                                        # same request, different manifest → different answer
    _assert_refused(env, "outside_served_horizon")
    assert env["served_horizon"] == {"start": _iso(_t(1, 15)), "end": _iso(_t(2, 15))}
    clipped = _read(w, date_from=_t(1, 2), date_to=_t(2, 1))
    assert clipped["horizon_clipped"]["side"] == "start" and clipped["effective_range"]["start"] == _iso(_t(1, 15))


def test_an_unbounded_or_closed_manifest_horizon_is_refused_not_guessed(world):
    w = _sealed(world)
    _unguarded(w, "kala_gochara_publication",
               "UPDATE public.kala_gochara_publication SET horizon = tstzrange(%s, %s, '[]')"
               " WHERE chart_id = %s AND generation = %s", (H0, H1, CHART_ID, GEN))
    _assert_refused(_read(w), "served_horizon_not_stated")


def test_the_modules_hold_no_literal_date_for_the_horizon_or_the_scored_edge():
    from routers import gochara_v5
    for mod in (rd, gochara_v5):
        src = inspect.getsource(mod)
        assert not re.search(r"(?<![0-9.])(1[89]|20|21)[0-9]{2}(?![0-9])", src), mod.__name__   # no year-like token
        assert not re.search(r"[0-9]{4}-[0-9]{2}", src), mod.__name__
        for node in ast.walk(ast.parse(src)):                      # and no date built from numbers
            if isinstance(node, ast.Call):
                name = getattr(node.func, "id", getattr(node.func, "attr", ""))
                if name in ("datetime", "date", "timedelta") and node.args:
                    raise AssertionError(f"{mod.__name__}: {name}(...) built from literals at line {node.lineno}")


# ── numbers: the manifest's policy, stored values, nothing invented ──────────────────────────────────────

def test_under_the_all_null_policy_every_number_is_null_the_order_is_chronological_and_nothing_is_invented(world):
    w = _sealed(world)
    env = _read(w, event_classes=[CLS])
    policy = w.conn.execute("SELECT input_generation_vector ->> 'result_policy' FROM public.kala_gochara_publication"
                            " WHERE chart_id = %s AND generation = %s", (CHART_ID, GEN)).fetchone()[0]
    assert env["result_policy"] == policy == "all_null_candidate/1"
    assert env["ranking"] == "chronological_only" and "all_null_candidate/1" in env["numbers_disclosure"]
    assert "interval start" in env["ordering"]
    win, stored = env["windows"][0], _stored_window(w)[0]
    for key in ("score", "evidence_for", "evidence_against", "severity", "peak_instant", "objective_value"):
        assert key in win and win[key] is None, key               # present AND null: a null, not a missing key or a 0
    assert stored[5:10] == (None, None, None, None, None)          # ... because that is what is stored
    assert win["outcome_valence_for_native"] == stored[10] == "unqualified"
    assert win["objective"] == stored[11] and win["qualification"] == stored[13]
    assert win["qualification"]["unqualified_reason"] == "all_null_candidate_policy"
    assert win["qualification_reason"] is None
    assert not FORBIDDEN_WINDOW_KEYS & set(win), FORBIDDEN_WINDOW_KEYS & set(win)
    assert not FORBIDDEN_WINDOW_KEYS & set(env)
    for m in win["members"]:                                       # no record-level number is served either
        assert not {k for k in m if "evidence" in k or "valence" in k or "severity" in k or "score" in k}


def test_the_policy_is_read_from_the_manifest_and_stored_numbers_pass_through_unchanged(world):
    w = world
    w.result_policy = "window_qualification/1"                     # the manifest step binds what the world carries
    _sealed(w)
    env = _read(w, event_classes=[CLS])
    assert env["result_policy"] == "window_qualification/1" and env["ranking"] == "chronological_only"
    assert "window_qualification/1" in env["numbers_disclosure"]
    assert env["numbers_disclosure"] != rd.NUMBERS_DISCLOSURE["all_null_candidate/1"]
    stored = _stored_window(w)[0]
    win = env["windows"][0]
    assert (win["score"], win["evidence_for"], win["evidence_against"], win["severity"]) == stored[5:9]
    # give the stored window numbers (as a numbers-enabled build would): the reader returns exactly those
    peak = stored[1] + (stored[2] - stored[1]) / 2
    _unguarded(w, "ka_gochara_eval_window",
               "UPDATE public.ka_gochara_eval_window SET score = 0.25, evidence_for = 1.5, evidence_against = 0.5,"
               " objective_value = 0.75, peak_instant = %s, outcome_valence_for_native = 'mixed',"
               " qualification = jsonb_set(qualification, '{unqualified_reason}', 'null'::jsonb)"
               " WHERE window_id = %s", (peak, stored[0]))
    win = _read(w, event_classes=[CLS])["windows"][0]
    assert (win["score"], win["evidence_for"], win["evidence_against"], win["objective_value"]) == (0.25, 1.5, 0.5, 0.75)
    assert win["peak_instant"] == _iso(peak) and win["outcome_valence_for_native"] == "mixed"
    assert win["severity"] is None                                 # still null where the store holds null
    assert not FORBIDDEN_WINDOW_KEYS & set(win)


# ── the scored edge: the manifest's pin, or null with a reason ───────────────────────────────────────────

def test_without_a_pinned_scored_edge_the_status_is_null_with_the_reason(world):
    w = _sealed(world)
    env = _read(w, event_classes=[CLS])
    assert env["scored_until"] is None and env["scored_until_reason"] == "scored_until_not_pinned"
    assert env["windows"][0]["scoring_status"] is None
    assert env["windows"][0]["scoring_status_reason"] == "scored_until_not_pinned"


@pytest.mark.parametrize("pin, status", [
    ("2025-03-01T00:00:00+00:00", "scored_horizon"),               # the window ends before the edge
    ("2025-02-20T00:00:00+00:00", "scored_horizon"),               # ... or exactly at it (half-open)
    ("2025-02-01T00:00:00+00:00", "straddles_scored_edge"),
    ("2025-01-10T00:00:00+00:00", "served_not_scored"),            # the window starts at the edge
    ("2025-01-05T05:30:00+05:30", "served_not_scored")])
def test_the_scoring_status_follows_the_edge_the_manifest_pins(world, pin, status):
    w = _sealed(world)
    _set_vector(w, "input_generation_vector || jsonb_build_object(%s::text, %s::text)",
                (rd.SCORED_UNTIL_VECTOR_KEY, pin))
    env = _read(w, event_classes=[CLS])
    win = env["windows"][0]
    assert win["interval"]["start"] == _iso(_t(1, 10)) and win["interval"]["end"] == _iso(_t(2, 20))
    assert env["scored_until"] == _iso(datetime.fromisoformat(pin)) and env["scored_until_reason"] is None
    assert win["scoring_status"] == status and win["scoring_status_reason"] is None
    assert status in rd.SCORING_STATUSES


@pytest.mark.parametrize("pin", ["2025-02-01", "2025-02-01T00:00:00", "soon"])
def test_a_pin_that_is_not_an_instant_is_null_with_its_own_reason_never_a_guess(world, pin):
    w = _sealed(world)
    _set_vector(w, "input_generation_vector || jsonb_build_object(%s::text, %s::text)",
                (rd.SCORED_UNTIL_VECTOR_KEY, pin))
    env = _read(w, event_classes=[CLS])
    assert env["scored_until"] is None and env["scored_until_reason"] == "scored_until_not_an_instant"
    assert env["windows"][0]["scoring_status"] is None
    assert env["windows"][0]["scoring_status_reason"] == "scored_until_not_an_instant"


# ── a class with no window: searched-complete-none vs not searched vs unverified ─────────────────────────

def test_a_zero_window_class_reads_differently_in_each_completeness_state(world):
    w = _sealed(world)
    quiet = {"date_from": _t(1, 2), "date_to": _t(1, 8)}           # inside the horizon, before the only window
    env = _read(w, event_classes=[CLS, "career_entry"], **quiet)
    assert env["refusal"] is None and env["windows"] == [] and env["counts"]["windows_matched"] == 0
    by = {c["event_class"]: c for c in env["classes"]}
    assert by[CLS]["completeness"] == sr.COMPLETE and by[CLS]["zero_window_reading"] == "searched_complete_none"
    assert by[CLS]["coverage"]["completeness_reasons"] == [] and by[CLS]["coverage"]["named_limits"]
    assert by["career_entry"]["completeness"] == "class_not_searched"
    assert by["career_entry"]["zero_window_reading"] == "not_searched"
    assert by["career_entry"]["coverage"]["completeness_reasons"][0]["code"] == "no_inventory_for_class"

    with w.conn.transaction():                                     # now the same class, no longer verified
        w.conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        w.conn.execute("ALTER TABLE public.ka_gochara_eval_window_verification DISABLE TRIGGER USER")
        w.conn.execute("DELETE FROM public.ka_gochara_eval_window_verification WHERE path_id = 'P3'")
        w.conn.execute("ALTER TABLE public.ka_gochara_eval_window_verification ENABLE TRIGGER USER")
    unverified = {c["event_class"]: c for c in _read(w, event_classes=[CLS], **quiet)["classes"]}[CLS]
    assert unverified["windows_matched"] == 0 and unverified["completeness"] == "unverified"
    assert unverified["zero_window_reading"] == "not_established:unverified"
    assert [r["code"] for r in unverified["coverage"]["completeness_reasons"]] == ["window_verification_missing"]
    assert len({by[CLS]["zero_window_reading"], by["career_entry"]["zero_window_reading"],
                unverified["zero_window_reading"]}) == 3
    # a POSITIVE answer carries the same honesty: the window is returned, the class is not called complete
    positive = _read(w, event_classes=[CLS])
    assert len(positive["windows"]) == 1 and positive["classes"][0]["completeness"] == "unverified"
    assert positive["classes"][0]["zero_window_reading"] is None


def test_an_instant_inside_a_window_finds_it_and_one_outside_finds_none(world):
    w = _sealed(world)
    inside = _read(w, event_classes=[CLS], at_instant=_t(1, 15))
    assert [x["window_id"] for x in inside["windows"]] == [_stored_window(w)[0][0]]
    assert inside["effective_range"]["kind"] == "instant" and inside["classes"][0]["completeness"] == sr.COMPLETE
    assert _read(w, event_classes=[CLS], at_instant=_t(1, 10))["counts"]["windows_matched"] == 1     # start included
    assert _read(w, event_classes=[CLS], at_instant=_t(2, 20))["counts"]["windows_matched"] == 0     # end excluded
    outside = _read(w, event_classes=[CLS], at_instant=_t(1, 5))
    assert outside["windows"] == [] and outside["classes"][0]["zero_window_reading"] == "searched_complete_none"


# ── deterministic total order, and paging that says it truncated ─────────────────────────────────────────

def _extra_windows(w):
    """Five more windows cloned from the stored one (different intervals, two sharing a start and an end), inserted in
    a scrambled physical order. Returns every stored window as the expected total order."""
    base = _stored_window(w)[0][0]
    spans = [(_t(2, 3), _t(2, 9)), (_t(1, 4), _t(1, 6)), (_t(1, 20), _t(1, 28)), (_t(1, 20), _t(1, 22)),
             (_t(1, 20), _t(1, 28))]
    ids = [str(uuid.UUID(int=n)) for n in (50, 40, 30, 20, 10)]
    with w.conn.transaction():
        w.conn.execute("ALTER TABLE public.ka_gochara_eval_window DISABLE TRIGGER USER")
        for wid, (a, b) in zip(ids, spans):
            w.conn.execute(
                "INSERT INTO public.ka_gochara_eval_window (window_id, chart_id, event_class, generation, path_id,"
                " rule_version, interval, outcome_valence_for_native, coverage_partition_kind, coverage_partition_key,"
                " coverage_facts, null_states_used, objective, qualification)"
                " SELECT %s, chart_id, event_class, generation, path_id, rule_version, tstzrange(%s, %s, '[)'),"
                " outcome_valence_for_native, coverage_partition_kind, coverage_partition_key, coverage_facts,"
                " null_states_used, objective, qualification FROM public.ka_gochara_eval_window WHERE window_id = %s",
                (wid, a, b, base))
        w.conn.execute("ALTER TABLE public.ka_gochara_eval_window ENABLE TRIGGER USER")
    rows = w.conn.execute("SELECT window_id::text, lower(interval), upper(interval), event_class, path_id, rule_version"
                          " FROM public.ka_gochara_eval_window").fetchall()
    return [r[0] for r in sorted(rows, key=lambda r: (r[1], r[2], r[3], r[4], r[5], uuid.UUID(r[0])))]


def test_the_order_is_chronological_total_and_identical_on_every_read(world):
    w = _sealed(world)
    expected = _extra_windows(w)
    assert len(expected) == 6
    first = [x["window_id"] for x in _read(w, event_classes=[CLS])["windows"]]
    assert first == expected
    # the tie (same start, same end, same class/path/version) is broken by window_id — the last key, ascending
    tied = [str(uuid.UUID(int=10)), str(uuid.UUID(int=30))]
    assert [i for i in first if i in tied] == tied
    for _ in range(3):
        assert [x["window_id"] for x in _read(w, event_classes=[CLS])["windows"]] == expected
    starts = [x["interval"]["start"] for x in _read(w, event_classes=[CLS])["windows"]]
    assert starts == sorted(starts)


def test_a_limit_returns_the_head_of_the_same_order_and_says_it_truncated(world):
    w = _sealed(world)
    expected = _extra_windows(w)
    env = _read(w, event_classes=[CLS], limit=2)
    assert [x["window_id"] for x in env["windows"]] == expected[:2]
    assert env["counts"]["windows_matched"] == 6 and env["counts"]["windows_returned"] == 2
    assert env["counts"]["windows_truncated"] is True
    assert env["classes"][0]["windows_matched"] == 6 and env["classes"][0]["windows_returned"] == 2
    whole = _read(w, event_classes=[CLS], limit=6)
    assert whole["counts"]["windows_truncated"] is False and [x["window_id"] for x in whole["windows"]] == expected
    # windows the verifier never saw are NOT called complete just because they are stored
    assert whole["classes"][0]["completeness"] == "unverified"


# ── the near-miss layer: separate, never counted with windows ────────────────────────────────────────────

def _near_miss_tables(w, drop_column=None):
    """The MINIMAL near-miss tables, named by the reader's own mapping (the migration that creates them is not on
    main): just the columns the reader selects."""
    occ, obj = rd.NEAR_MISS_SCHEMA["occurrence_table"], rd.NEAR_MISS_SCHEMA["object_table"]
    oc, ob = rd.NEAR_MISS_SCHEMA["occurrence_columns"], rd.NEAR_MISS_SCHEMA["object_columns"]
    types = {"chart_id": "uuid", "generation": "text", "near_miss_id": "uuid PRIMARY KEY", "object_id": "uuid",
             "ordinal": "integer", "t_in": "timestamptz", "t_out": "timestamptz", "t_closest": "timestamptz",
             "closest_state": "text", "clearance_deg": "double precision", "orb_deg": "double precision",
             "proximity": "double precision", "standing": "text CHECK (standing = 'near_miss')",
             "score": "real CHECK (score IS NULL)", "junction": "jsonb", "junction_complete": "boolean"}
    obj_types = {"object_id": "uuid PRIMARY KEY", "body": "text", "relation": "text", "target": "text",
                 "orb_policy_id": "text"}
    w.conn.execute(f"CREATE TABLE public.{obj} ("
                   + ", ".join(f"{ob[k]} {t}" for k, t in obj_types.items()) + ")")
    w.conn.execute(f"CREATE TABLE public.{occ} ("
                   + ", ".join(f"{oc[k]} {t}" for k, t in types.items() if k != drop_column) + ")")
    return occ, obj


def _near_miss_rows(w, occ, obj, spans):
    object_id = str(uuid.UUID(int=700))
    w.conn.execute(f"INSERT INTO public.{obj} VALUES (%s, 'mars', 'aspect', 'point:123.5', 'orb/1')", (object_id,))
    ids = []
    for n, (a, b) in enumerate(spans, start=1):
        nid = str(uuid.UUID(int=800 - n))                          # descending ids: the order must come from t_in
        ids.append(nid)
        w.conn.execute(
            f"INSERT INTO public.{occ} (chart_id, generation, near_miss_id, object_id, ordinal, t_in, t_out, t_closest,"
            " closest_state, clearance_deg, orb_deg, proximity, standing, score, junction, junction_complete)"
            " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'placed', 0.2, 1.0, 0.8, 'near_miss', NULL,"
            " '{\"kinds\": [\"sign_ingress\"]}'::jsonb, true)",
            (CHART_ID, GEN, nid, object_id, n, a, b, a + (b - a) / 2))
    return ids


def test_without_the_near_miss_tables_the_layer_is_absent_and_no_array_is_returned(world):
    w = _sealed(world)
    assert w.conn.execute("SELECT to_regclass(%s) IS NULL",
                          ("public." + rd.NEAR_MISS_SCHEMA["occurrence_table"],)).fetchone()[0]
    env = _read(w, event_classes=[CLS])
    assert env["near_miss_layer"] == "absent" and "near_miss_intervals" not in env
    assert env["counts"]["near_miss_matched"] is None and env["counts"]["near_miss_returned"] is None
    assert env["counts"]["windows_matched"] == 1


def test_a_present_near_miss_layer_is_a_separate_array_never_merged_or_counted_with_windows(world):
    w = _sealed(world)
    before = _read(w, event_classes=[CLS])
    occ, obj = _near_miss_tables(w)
    ids = _near_miss_rows(w, occ, obj, [(_t(1, 3), _t(1, 6)), (_t(2, 22), _t(2, 26)), (_t(1, 12), _t(1, 14))])
    env = _read(w, event_classes=[CLS])
    assert env["near_miss_layer"] == "present"
    near = env["near_miss_intervals"]
    assert [n["near_miss_id"] for n in near] == [ids[0], ids[2], ids[1]]                # chronological, by entry
    for n in near:
        assert n["standing"] == "near_miss" and n["score"] is None and n["score_reason"] == "near_miss_unscored"
        assert n["proximity"] == 0.8 and n["body"] == "mars" and n["target"] == "point:123.5"
        assert n["junction"] == {"kinds": ["sign_ingress"]} and n["junction_complete"] is True
    assert near[0]["interval"] == {"start": _iso(_t(1, 3)), "end": _iso(_t(1, 6))}
    # never merged, never counted with windows: the window side is byte-for-byte what it was without the layer
    assert env["windows"] == before["windows"] and env["classes"] == before["classes"]
    assert env["counts"]["windows_matched"] == 1 == env["counts"]["windows_returned"]
    assert env["counts"]["near_miss_matched"] == 3 == env["counts"]["near_miss_returned"]
    assert not {n["near_miss_id"] for n in near} & {x["window_id"] for x in env["windows"]}
    assert all("standing" not in x for x in env["windows"])
    assert env["near_miss_completeness"] is None
    assert env["near_miss_completeness_reason"] == "near_miss_search_coverage_not_read"

    # a near-miss is shown even where NO contact window exists, and the range filter applies to it on its own
    quiet = _read(w, event_classes=[CLS], date_from=_t(1, 2), date_to=_t(1, 8))
    assert quiet["windows"] == [] and quiet["counts"]["windows_matched"] == 0
    assert [n["near_miss_id"] for n in quiet["near_miss_intervals"]] == [ids[0]]
    assert quiet["counts"]["near_miss_matched"] == 1
    assert quiet["classes"][0]["zero_window_reading"] == "searched_complete_none"
    at = _read(w, event_classes=[CLS], at_instant=_t(1, 13))
    assert [n["near_miss_id"] for n in at["near_miss_intervals"]] == [ids[2]] and len(at["windows"]) == 1
    limited = _read(w, event_classes=[CLS], limit=1)
    assert limited["counts"]["near_miss_matched"] == 3 and limited["counts"]["near_miss_returned"] == 1
    assert limited["counts"]["near_miss_truncated"] is True and limited["counts"]["windows_truncated"] is False


def test_near_miss_tables_holding_nothing_for_an_unpinned_generation_are_not_built_not_empty(world):
    w = _sealed(world)
    occ, obj = _near_miss_tables(w)
    env = _read(w, event_classes=[CLS])
    assert env["near_miss_layer"] == "not_built_for_generation" and "near_miss_intervals" not in env
    assert env["counts"]["near_miss_matched"] is None
    # once the manifest pins the layer's version, an empty result is an (unverified) empty array, and says so
    _set_vector(w, "input_generation_vector || jsonb_build_object(%s::text, '1'::text)",
                (rd.NEAR_MISS_SCHEMA["layer_version_vector_key"],))
    pinned = _read(w, event_classes=[CLS])
    assert pinned["near_miss_layer"] == "present" and pinned["near_miss_intervals"] == []
    assert pinned["near_miss_layer_version"] == "1" and pinned["counts"]["near_miss_matched"] == 0
    assert pinned["near_miss_completeness"] is None


def test_near_miss_tables_of_another_shape_are_a_named_mismatch_never_a_guess(world):
    w = _sealed(world)
    _near_miss_tables(w, drop_column="proximity")
    env = _read(w, event_classes=[CLS])
    assert env["near_miss_layer"] == "schema_mismatch" and "near_miss_intervals" not in env
    assert env["near_miss_layer_detail"]["missing_columns"] == [
        rd.NEAR_MISS_SCHEMA["occurrence_table"] + "." + rd.NEAR_MISS_SCHEMA["occurrence_columns"]["proximity"]]
    assert len(env["windows"]) == 1                                # the window answer does not depend on the layer


# ── read-only, and the schema it needs ───────────────────────────────────────────────────────────────────

def test_the_reader_runs_inside_a_read_only_transaction_and_holds_no_write_statement(world):
    import psycopg
    w = _sealed(world)
    with psycopg.connect(w.dsn, connect_timeout=3) as ro:
        ro.read_only = True
        env = rd.read_v5(ro, CHART_ID, GEN, event_classes=[CLS, "career_entry"])
        assert env["refusal"] is None and len(env["windows"]) == 1
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):         # the transaction really is read-only
            ro.execute("CREATE TABLE public.w1_must_not_exist (x int)")
        ro.rollback()
    src = inspect.getsource(rd)
    assert not re.search(r"\b(INSERT|UPDATE|DELETE|TRUNCATE|CREATE|ALTER|DROP|GRANT|LOCK)\b", src)
    assert ".commit(" not in src and ".close(" not in src and "autocommit" not in src


def test_a_database_without_the_serving_tables_is_a_named_fault_not_an_answer(world):
    import psycopg
    from psycopg.conninfo import make_conninfo
    w = world
    with psycopg.connect(make_conninfo(w.dsn, dbname="postgres"), connect_timeout=3) as bare:
        with pytest.raises(rd.ServingSchemaMissing) as exc:
            rd.read_v5(bare, CHART_ID, GEN)
        bare.rollback()
    assert "ka_gochara_eval_window" in str(exc.value)


def test_dict_rows_and_tuple_rows_give_the_same_envelope(world):
    import psycopg
    import psycopg.rows
    w = _sealed(world)
    occ, obj = _near_miss_tables(w)                                # every query of the reader, both layers
    _near_miss_rows(w, occ, obj, [(_t(1, 3), _t(1, 6)), (_t(1, 12), _t(1, 14))])
    with psycopg.connect(w.dsn, connect_timeout=3, row_factory=psycopg.rows.dict_row) as dconn:
        as_dict = rd.read_v5(dconn, CHART_ID, GEN, event_classes=[CLS, "career_entry"])
        dconn.rollback()
    as_tuple = _read(w, event_classes=[CLS, "career_entry"])
    assert as_dict == as_tuple
    assert as_tuple["windows"][0]["members"][0]["contact_truncated"] is False      # a positional slip would move this
    assert as_tuple["windows"][0]["members"][0]["solver_method"] and len(as_tuple["near_miss_intervals"]) == 2
