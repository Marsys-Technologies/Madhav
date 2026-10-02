"""A5.3 — Codex round 9, R9-10 (Stream B's real-sky rehearsal on 58ce55523).

`record_verifier.expected_p1_contacts` reconstructed P1 contacts for EVERY graha — the Moon included — although the
generation's manifest declares `stored_scope: stored_non_moon` (AM-14: the Moon is never a stored transiting agent).
On the real ephemeris the Moon crosses signs every ~2.3 days, so the builder's own record phase rejected a CORRECT
ledger ('expected contact moon span:2 … not in the ledger'). The synthetic sky holds the Moon fixed and hid it.

The expected bodies now come from the manifest's scope (`inventory_verifier.bound_excluded_agents`) in every place
that enumerates transiting bodies: the expected P1 contact set and the expected P2/P3/P4 obligation set. These tests
run on the REAL .se1 ephemeris (skipped, never passed, when the pinned files are absent)."""
from __future__ import annotations

import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import inventory_verifier as iv
from services.gochara_kernel import record_verifier as rv

from .conftest import _PROBLEMS, EPHE_PATH
from .test_a53_inventory import CHART_ID, H0, H1
from .test_a53_p1_support import GEN, world  # noqa: F401
from .test_a53_version_selection import VCHART

pytestmark = pytest.mark.skipif(bool(_PROBLEMS), reason="NOT_RUN: pinned .se1 ephemeris files missing or mismatched")

BODIES = ("Sun", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu")


def _real_position_at():
    from datetime import timezone
    from services.gochara_kernel.knots import calc_sidereal_lon

    def position_at(body, t):
        jd = t.astimezone(timezone.utc).timestamp() / 86400.0 + 2440587.5
        lon, ret = calc_sidereal_lon(body.title(), jd, EPHE_PATH)
        return lon
    return position_at


@pytest.fixture()
def real_class(world, monkeypatch):          # noqa: F811
    """A P1 class built end to end by the BUILDER's own substeps over a short REAL horizon (its own record phase
    runs `verify_p1_anchors` against the real ephemeris — the call that rejected a correct ledger)."""
    from services.gochara_kernel.knots import calc_sidereal_lon
    monkeypatch.setattr(writer_mod, "calc_sidereal_lon", calc_sidereal_lon)
    w = world
    keys = [writer_mod.RULES_SUBSTEP, writer_mod.CONVENTION_SUBSTEP,
            *[f"{writer_mod.BODY_SUBSTEP_PREFIX}{b}" for b in writer_mod.SUBSTRATE_BODIES],
            writer_mod.MANIFEST_SUBSTEP, writer_mod.SNAPSHOT_SUBSTEP, "inventory:marriage", "coverage:marriage",
            *[f"{writer_mod.RECORD_SUBSTEP_PREFIX}marriage:{p}" for p in ("P1", "P2", "P3", "P4")],
            *[f"{writer_mod.WINDOW_SUBSTEP_PREFIX}marriage:{p}" for p in ("P1", "P2", "P3", "P4")],
            f"{writer_mod.VERIFY_SUBSTEP_PREFIX}marriage"]
    for k in keys:
        w.step(k)
    return w


def test_real_sky_scope_from_the_manifest_builder_and_verifier_agree_and_an_omission_is_caught(real_class):
    """ONE real build (~80 s): agreement, scope-from-manifest, then the negative."""
    w = real_class
    out = rv.verify_p1_anchors(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage",
                               position_at=_real_position_at())
    assert out["contacts"] >= 1
    bodies = {r[0] for r in w.conn.execute(
        "SELECT DISTINCT c.body FROM public.ka_gochara_contact c JOIN public.ka_gochara_physical_object o"
        " ON o.physical_object_id = c.physical_object_id WHERE c.generation = %s AND c.relation_kind = 'residence'"
        " AND o.canonical_target LIKE 'span:%%'", (GEN,)).fetchall()}
    assert bodies and "moon" not in {b.lower() for b in bodies}        # the stored tier holds no Moon contact

    # the expected bodies are the manifest's scope, not a hard-coded exclusion
    pos = _real_position_at()
    lo, hi = H0, H1
    assert iv.bound_excluded_agents(w.conn, CHART_ID, GEN) == ("moon",)
    excl = iv.bound_excluded_agents(w.conn, CHART_ID, GEN)
    non_moon = rv.expected_p1_contacts(pos, lo, hi, excluded_agents=excl)
    assert non_moon and "moon" not in {c["agent"] for c in non_moon}
    # a scope that excluded nothing WOULD expect Moon contacts (every ~2.3 days on the real sky): the exclusion
    # is the declared scope's, read from the manifest — remove it and the Moon is expected again
    with_moon = rv.expected_p1_contacts(pos, lo, hi, excluded_agents=())
    assert {"moon"} == {c["agent"] for c in with_moon} - {c["agent"] for c in non_moon}
    # the Moon as an ANCHOR lord of another agent's period stays (Sun/Jupiter entering Taurus: XX.38)
    assert ("moon", "ad") in rv.expected_p1_anchors("sun", 1) and ("moon", "ad") in rv.expected_p1_anchors("jupiter", 1)
    # an unknown scope is not guessed
    w.conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector ="
                   " input_generation_vector || '{\"stored_scope\": \"stored_everything\"}'::jsonb")
    with pytest.raises(iv.Unverifiable, match="not a scope this verifier knows"):
        iv.bound_excluded_agents(w.conn, CHART_ID, GEN)
    w.conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector ="
                   " input_generation_vector - 'stored_scope'")
    with pytest.raises(iv.Unverifiable, match="states no stored_scope"):
        iv.bound_excluded_agents(w.conn, CHART_ID, GEN)
    w.conn.execute("UPDATE public.kala_gochara_publication SET input_generation_vector ="
                   " input_generation_vector || '{\"stored_scope\": \"stored_non_moon\"}'::jsonb")

    # the negative: a real omitted NON-Moon contact is still caught
    victim = w.conn.execute(
        "SELECT c.contact_id::text FROM public.ka_gochara_contact c JOIN public.ka_gochara_physical_object o"
        " ON o.physical_object_id = c.physical_object_id WHERE c.generation = %s AND c.relation_kind = 'residence'"
        " AND o.canonical_target LIKE 'span:%%' ORDER BY c.t_in LIMIT 1", (GEN,)).fetchone()[0]
    w.conn.execute("DELETE FROM public.ka_gochara_relationship_record WHERE contact_id = %s::uuid", (victim,))
    w.conn.execute("ALTER TABLE public.ka_gochara_contact DISABLE TRIGGER USER")
    w.conn.execute("DELETE FROM public.ka_gochara_contact WHERE contact_id = %s::uuid", (victim,))
    w.conn.execute("ALTER TABLE public.ka_gochara_contact ENABLE TRIGGER USER")
    with pytest.raises(RuntimeError, match="not in the ledger"):
        rv.verify_p1_anchors(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage", position_at=pos)


def test_the_expected_obligation_set_takes_its_agents_from_the_scope_too():
    chart = VCHART
    kw = dict(path_exclusions={}, h_unknown_exclusion=None)
    with_moon_excluded = iv.derive_path_pin("marriage", chart, "P3", "1.0.0", excluded_agents=("moon",), **kw)
    nothing_excluded = iv.derive_path_pin("marriage", chart, "P3", "1.0.0", excluded_agents=(), **kw)
    agents = lambda pin: {o.split("|")[3] for o in pin["obligations"]}      # noqa: E731
    assert "moon" not in agents(with_moon_excluded) and "moon" in agents(nothing_excluded)
