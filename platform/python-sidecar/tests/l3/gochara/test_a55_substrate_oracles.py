"""A5.5 frozen test oracles — sky-event substrate (GOCHARA_DESIGN_SPECS v1.4
§6, §6.1, §7).

Six oracles with literal inputs:

  O-SS-2  §6    — 0° seam boundary search, both directions (REAL: pure
                  synthetic trajectories through gochara_kernel.arcs/contacts;
                  Aries ingress found, Pisces re-entry found through the UPPER
                  boundary, one interior root each, δt < 60 s).
  O-SS-1  §6    — Sun boundary counts 2025: exactly 12 sign / 27 nakṣatra /
                  96 kakṣyā crossings, each stored once (REAL: Swiss knots
                  under the conftest F-14 gate, spline stage refine=False).
  O-SS-3  §6    — off-horizon exact centre retained as a TRUNCATED span
                  (REAL: kernel episode + residence-span geometry, synthetic,
                  literal span [2025-12-15, 2026-02-15], horizon
                  [2025-01-01, 2026-01-01)); the §6.1 persistence-identity leg
                  (coverage.truncated=true on the stored sky_event row) is
                  deferred to O-RX-1's xfail — A5.2 substrate not built.
  O-SS-4  §6    — Moon-on-demand: live solve for exactly the requested
                  30-day window, contact_id=None (never persisted), one
                  moon_on_demand coverage row (REAL, Swiss-gated). The
                  global-substrate count(*)=0 predicate is a separate xfail —
                  the sky_event store (A5.2) does not exist yet.
  O-RX-1  §6.1  — occurrence-ordinal contact identity (XFAIL: the A5.2
                  substrate identity layer — physical_object_id,
                  occurrence_ordinal, §6.1 serialization — is not built;
                  services/gochara_kernel/ids.py still carries the WP1 §3.2
                  floored-minute t_exact hash that v1.4 §6.1 forbids).
  O-SM-3  §7    — every station event solver_method='swiss_refined' with a
                  count(*)>0 positive control (XFAIL: no station sky_event
                  store carrying solver_method exists yet).

XFAIL policy: the xfail tests import the frozen expected interface INSIDE the
test body so they fail (ModuleNotFoundError / ImportError) today and become
real assertions the moment the A5.2/A5.3 substrate lands. strict=False per
the campaign brief; each xfail names the exact missing symbol.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import sys

import pytest
import swisseph as swe

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.gochara_kernel import arcs as gk_arcs  # noqa: E402
from services.gochara_kernel import contacts as gk_contacts  # noqa: E402
from services.gochara_kernel import episodes as gk_episodes  # noqa: E402
from services.ka_gochara.service import (  # noqa: E402
    GocharaTransitService,
    Horizon,
    TargetRef,
)

from .conftest import EPHE_PATH, requires_swieph  # noqa: E402

SECONDS_PER_DAY = 86400.0
DT_60S = 60.0 / SECONDS_PER_DAY  # O-SS-2 tolerance: δt < 60 s


def _jd(y: int, m: int, d: int, hour: float = 0.0) -> float:
    return float(swe.julday(y, m, d, hour))


def _parse_iso_z(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


# ── O-SS-2 (§6): 0° seam boundary search, both directions ────────────────────

class TestOSS2SeamBoundarySearch:
    """Synthetic literal trajectories (oracle O-SS-2, defects #14/N2/NK-7).

    Case 1: direct 359.9° → 0.1° over [2025-03-01T00:00Z, 2025-03-02T00:00Z]
    — the Aries ingress (0°) root must be found at 2025-03-01T12:00Z.
    Case 2: retrograde 0.1° → 359.9° over [2025-09-01T00:00Z, 2025-09-02T00:00Z]
    — the Pisces re-entry through the UPPER boundary must be found at
    2025-09-01T12:00Z, on a direction=-1 arc.

    Mutation that must fail: dropping the 0° seam from boundary_degrees
    (the pre-#14 grid) yields zero roots in both cases; fabricating the root
    at the horizon edge instead of the interior instant breaks the δt < 60 s
    and interior assertions.
    """

    def _seam_roots(self, jd_mid: float, lons: list[float]):
        knots = [jd_mid - 1.0, jd_mid, jd_mid + 1.0, jd_mid + 2.0]
        index = gk_arcs.build_arc_index("Sun", knots, lons)
        roots = gk_contacts.find_boundary_roots(
            index, "Sun", "sign_ingress", refine=False
        )
        return index, [r for r in roots if r.level_deg == 0.0]

    def test_case1_direct_aries_ingress_root_found(self):
        jd0 = _jd(2025, 3, 1)
        index, roots = self._seam_roots(jd0, [359.7, 359.9, 0.1, 0.3])
        assert len(roots) == 1, (
            f"expected exactly one 0° seam root, got {len(roots)}: {roots}"
        )
        root = roots[0]
        expected = jd0 + 0.5  # linear 359.9 → 360.1 over one day
        assert abs(root.exact_jd - expected) < DT_60S, (
            f"root {root.exact_jd} not within 60 s of {expected}"
        )
        # Interior — never fabricated at the horizon/knot edge.
        assert jd0 < root.exact_jd < jd0 + 1.0
        assert root.arc.direction == 1

    def test_case1_episode_is_honestly_exact(self):
        jd0 = _jd(2025, 3, 1)
        knots = [jd0 - 1.0, jd0, jd0 + 1.0, jd0 + 2.0]
        index = gk_arcs.build_arc_index("Sun", knots, [359.7, 359.9, 0.1, 0.3])
        eps = gk_episodes.solve_boundary_episodes(
            index, "Sun", "sign_ingress", (jd0 - 1.0, jd0 + 2.0), refine=False
        )
        seam = [e for e in eps if e.level_deg == 0.0]
        assert len(seam) == 1
        ep = seam[0]
        assert ep.exact_crossing is True
        assert ep.t_in == ep.t_exact == ep.t_out
        assert abs(ep.t_exact - (jd0 + 0.5)) < DT_60S

    def test_case2_retrograde_pisces_reentry_through_upper_boundary(self):
        jd1 = _jd(2025, 9, 1)
        index, roots = self._seam_roots(jd1, [0.3, 0.1, 359.9, 359.7])
        assert len(roots) == 1, (
            f"expected exactly one 0° seam root, got {len(roots)}: {roots}"
        )
        root = roots[0]
        expected = jd1 + 0.5  # linear 0.1 → -0.1 (≡359.9) over one day
        assert abs(root.exact_jd - expected) < DT_60S, (
            f"root {root.exact_jd} not within 60 s of {expected}"
        )
        assert jd1 < root.exact_jd < jd1 + 1.0
        # Re-entry through the UPPER boundary: the owning arc falls (N2).
        assert root.arc.direction == -1


# ── O-SS-1 (§6): Sun boundary counts over 2025 ───────────────────────────────

@requires_swieph
class TestOSS1SunBoundaryCounts2025:
    """Sun over 2025-01-01 → 2026-01-01 UTC, Swiss/Lahiri pinned backend
    (conftest F-14 gate): exactly 12 sign, 27 nakṣatra, 96 kakṣyā crossings,
    each enumerated once per body (label-independent — defect #27/E1).

    Mutation that must fail: removing the 0° seam from the sign grid
    (pre-#14) drops the count to 11; per-target enumeration multiplies the
    counts by the target count — both break the exact 12/27/96 assertion.
    """

    EXPECTED = {
        "sign_ingress": 12,
        "nakshatra_ingress": 27,
        "kakshya_cell_crossing": 96,
    }

    @pytest.fixture(scope="class")
    def sun_index(self):
        from services.gochara_kernel.knots import sample_knots

        ks = sample_knots("Sun", date(2025, 1, 1), date(2026, 1, 1), EPHE_PATH)
        return gk_arcs.build_arc_index("Sun", ks.knot_jds, ks.longitudes_deg)

    @pytest.mark.parametrize(
        "relation,expected",
        list(EXPECTED.items()),
        ids=list(EXPECTED),
    )
    def test_boundary_count_exact(self, sun_index, relation, expected):
        roots = gk_contacts.find_boundary_roots(
            sun_index, "Sun", relation, refine=False
        )
        assert len(roots) == expected, (
            f"{relation}: {len(roots)} roots != pinned {expected}"
        )
        # Each event stored once: no two roots of one relation at one instant.
        instants = [round(r.exact_jd, 6) for r in roots]
        assert len(set(instants)) == len(instants), (
            f"{relation}: duplicate instants — per-target/label duplication"
        )


# ── O-SS-3 (§6): off-horizon exact centre retained as truncated span ─────────

class TestOSS3OffHorizonCentreTruncated:
    """Literal span [2025-12-15T00:00Z, 2026-02-15T00:00Z], exact centre
    2026-01-15T00:00Z, horizon [2025-01-01T00:00Z, 2026-01-01T00:00Z)
    (oracle O-SS-3, defects N3/NK-7).

    The contact must be RETAINED as a truncated span — never dropped, and no
    t_exact may be fabricated (the true centre/exit lies beyond the fitted
    knots and the horizon). Residence-clipping and degree-contact-centre-
    clipping are asserted separately, per the oracle.

    Mutation that must fail: dropping no-exact episodes/spans (empty result)
    or stamping t_exact at the clip edge (exact_crossing=True / t_exact ==
    horizon end) both fail these assertions.
    """

    H0 = _jd(2025, 1, 1)
    H1 = _jd(2026, 1, 1)
    T_ENTER = _jd(2025, 12, 15)
    T_EXIT_TRUE = _jd(2026, 2, 15)
    T_CENTRE = _jd(2026, 1, 15)

    def _linear_index(self, body: str, lon_at, jd_start: float, jd_end: float):
        """Daily knots on a strictly linear synthetic trajectory; the cubic
        spline reproduces it exactly, so refine=False instants are exact."""
        n = int(round(jd_end - jd_start)) + 1
        knots = [jd_start + i for i in range(n)]
        lons = [lon_at(jd) % 360.0 for jd in knots]
        return gk_arcs.build_arc_index(body, knots, lons)

    def test_degree_contact_centre_off_horizon_kept_without_fabricated_exact(self):
        # Conjunction with target 10.0°: λ = 10 + 0.1·(jd − centre) ⇒ in-orb
        # (orb 3.1°) over exactly [2025-12-15, 2026-02-15], centre 2026-01-15
        # — outside the fitted knots (which end at the horizon) and the
        # horizon.
        rate = 0.1
        orb = rate * 31.0  # 3.1° — entry 2025-12-15, true exit 2026-02-15
        index = self._linear_index(
            "Sun", lambda jd: 10.0 + rate * (jd - self.T_CENTRE),
            _jd(2025, 12, 1), self.H1,
        )
        eps = gk_episodes.solve_episodes(
            index, "Sun", "conjunction", 10.0, (self.H0, self.H1),
            orb_source="orb_conj_slow", refine=False, orb_override_deg=orb,
        )
        assert len(eps) == 1, f"truncated contact dropped or split: {eps}"
        ep = eps[0]
        # NOT dropped; clipped to the horizon end — the true exit
        # (2026-02-15) must NOT appear.
        assert ep.truncated_at_horizon == "end"
        assert ep.t_out == self.H1
        assert abs(ep.t_in - self.T_ENTER) < DT_60S
        # NO fabricated t_exact: the centre 2026-01-15 is off-horizon.
        assert ep.t_exact is None
        assert ep.exact_crossing is False
        # Honest about the unresolved root count at the knot edge — never a
        # silent 'applied'.
        assert ep.completeness_state == "unqualified"

    def test_residence_span_clipped_at_horizon_end_kept(self):
        # Residence in the Pisces whole-sign span (330°, 360°): entry at the
        # 330° edge on 2025-12-15, true exit (360°) on 2026-02-15 — past the
        # horizon end 2026-01-01.
        width = 30.0
        rate = width / (self.T_EXIT_TRUE - self.T_ENTER)  # °/day
        index = self._linear_index(
            "Sun", lambda jd: 330.0 + rate * (jd - self.T_ENTER),
            _jd(2025, 12, 1), self.H1,
        )
        spans = gk_episodes.residence_spans(
            index, "Sun", (330.0, 360.0), (self.H0, self.H1),
            target_type="sign", refine=False,
        )
        assert len(spans) == 1, f"truncated residence dropped or split: {spans}"
        span = spans[0]
        # NOT dropped; stored as a truncated span clipped to the horizon.
        assert span.truncated_at_horizon == "end"
        assert span.t_exit == self.H1
        assert span.t_exit != self.T_EXIT_TRUE
        assert abs(span.t_enter - self.T_ENTER) < DT_60S
        # The ingress is genuinely observed inside the horizon (entry
        # 2025-12-15) — exact, at the true instant, never re-stamped to the
        # clip edge.
        ing = span.ingress_episode
        assert ing.exact_crossing is True
        assert ing.t_exact is not None and abs(ing.t_exact - self.T_ENTER) < DT_60S
        assert ing.target_deg == 330.0


# ── O-SS-4 (§6): Moon on demand ──────────────────────────────────────────────

@requires_swieph
class TestOSS4MoonOnDemand:
    """30-day window [2026-03-01, 2026-03-31]: Moon boundary events generated
    on demand for exactly that window; every returned episode carries
    contact_id=None (live-computed, NEVER persisted) and exactly one
    moon_on_demand coverage row records the searched horizon (defect
    Moon-on-demand).

    Mutation that must fail: minting a contact_id (i.e. persisting/
    pre-materialising Moon rows) or omitting the moon_on_demand coverage
    partition both fail; episodes outside the requested window fail the
    window-containment assertion.
    """

    W0 = datetime(2026, 3, 1, tzinfo=timezone.utc)
    W1 = datetime(2026, 3, 31, tzinfo=timezone.utc)

    @pytest.fixture(scope="class")
    def moon_batch(self):
        svc = GocharaTransitService(swe, ephe_path=EPHE_PATH)
        horizon = Horizon(
            start_jd=_jd(2026, 3, 1), end_jd=_jd(2026, 3, 31)
        )
        targets = [TargetRef("graha", "graha:mars", longitude_deg=198.52)]
        return svc._moon_on_demand(
            targets, horizon, ["sign_ingress", "conjunction"]
        )

    def test_moon_episodes_live_only_with_coverage_row(self, moon_batch):
        episodes, coverage = moon_batch
        # POSITIVE CONTROL: the Moon crosses ~13 sign boundaries in 30 days;
        # an empty answer cannot vacuously pass.
        sign_eps = [e for e in episodes if e.relation == "sign_ingress"]
        assert len(sign_eps) >= 3, (
            f"expected several Moon sign ingresses in 30 days, got {len(sign_eps)}"
        )
        assert episodes, "no Moon episodes generated on demand"
        for ep in episodes:
            assert ep.body == "Moon"
            assert ep.contact_id is None, (
                "Moon on-demand episode carries a contact_id — "
                "pre-materialised/persisted Moon rows are forbidden"
            )
        assert coverage.partition_kind == "moon_on_demand"
        assert coverage.requested_horizon == coverage.completed_horizon
        assert coverage.targets_resolved == 1
        assert coverage.unsearched_reason is None

    def test_moon_episodes_confined_to_requested_window(self, moon_batch):
        episodes, _ = moon_batch
        for ep in episodes:
            t_in = _parse_iso_z(ep.t_in)
            assert self.W0 <= t_in <= self.W1 + timedelta(minutes=1), (
                f"{ep.relation} episode at {ep.t_in} outside the requested "
                "window [2026-03-01, 2026-03-31]"
            )
        # Boundary episodes are boundary-exact: t_in = t_exact = t_out.
        for ep in episodes:
            if ep.relation == "sign_ingress":
                assert ep.t_in == ep.t_exact == ep.t_out

    def test_global_substrate_holds_no_materialised_moon_rows(self):
        """count(*) = 0 predicate over the materialised sky_event substrate
        (oracle O-SS-4's second leg). A5.2 substrate not built: the frozen
        expectation is a `SkyEventStore` over the §6 `sky_event` table with a
        per-body row count; there is currently NO such store (only the WP6
        kala_gochara_contacts ledger, which is not the §6 substrate)."""
        from services.gochara_kernel.substrate import SkyEventStore  # noqa: F401

        store = SkyEventStore.from_env()
        assert store.count_rows(body="Moon") == 0, (
            "materialised Moon rows in the global substrate — Moon events "
            "must be generated on demand only"
        )

    test_global_substrate_holds_no_materialised_moon_rows = pytest.mark.xfail(
        reason="A5.2 substrate not built: services.gochara_kernel.substrate.SkyEventStore",
        strict=False,
    )(test_global_substrate_holds_no_materialised_moon_rows)


# ── O-RX-1 (§6.1): occurrence-ordinal contact identity ───────────────────────

class TestORX1OccurrenceOrdinalIdentity:
    """One physical tuple — Mars | conjunction | point:198.52 (natal Mars) |
    convention c0 (domain 2025-01-01T00:00Z → 2026-01-01T00:00Z) — crossed
    three times: t1 = 2025-03-10 (direct), t2 = 2025-06-15 (retrograde
    re-crossing), t3 = 2025-08-20 (direct re-crossing). Partition extension
    inside c0 reveals t4 = 2025-11-05 ⇒ ordinal 4; ordinals 1–3 and their
    published contact ids never change (oracle O-RX-1, defects NK-2 /
    R3-amendment-1).

    Canonical identity bytes (spec §6.1):
        'Mars|conjunction|point:198.52|c0|1' … '|2' … '|3' … '|4'
    under ONE physical_object_id = hash(body, relation_kind,
    canonical_target, convention_id).

    Deferred mutation (checked at the A5.5 rehearsal): an identity tuple
    without the occurrence component collapses t2/t3 into t1 or splits them
    into separate objects; hashing a rounded t_exact (day-grain) to
    distinguish them (forbidden); renumbering published ids on partition
    extension.
    """

    T_CROSSINGS = [
        datetime(2025, 3, 10, tzinfo=timezone.utc),   # t1 direct
        datetime(2025, 6, 15, tzinfo=timezone.utc),   # t2 retrograde
        datetime(2025, 8, 20, tzinfo=timezone.utc),   # t3 direct
    ]
    T4 = datetime(2025, 11, 5, tzinfo=timezone.utc)

    def test_occurrence_ordinals_under_one_physical_object(self):
        # Frozen expected interface (spec v1.4 §6.1) — NOT YET BUILT.
        # services/gochara_kernel/ids.py:contact_id is the WP1 §3.2 scheme
        # (floored-minute t_exact inside the hash), which §6.1 explicitly
        # forbids; the §6.1 identity layer has no implementation.
        from services.gochara_kernel.substrate import (  # noqa: F401
            assign_occurrence_ordinals,
            contact_identity_bytes,
            physical_object_id,
        )

        poid = physical_object_id(
            body="Mars", relation_kind="conjunction",
            canonical_target="point:198.52", convention_id="c0",
        )
        contacts = assign_occurrence_ordinals(
            physical_object_id=poid, t_exact_list=self.T_CROSSINGS,
        )
        # Exactly three rows, ONE physical object, ordinals in solved-t_exact
        # order, canonical serialization per §6.1.
        assert len(contacts) == 3
        assert {c.physical_object_id for c in contacts} == {poid}
        assert [c.occurrence_ordinal for c in contacts] == [1, 2, 3]
        assert [contact_identity_bytes(c) for c in contacts] == [
            "Mars|conjunction|point:198.52|c0|1",
            "Mars|conjunction|point:198.52|c0|2",
            "Mars|conjunction|point:198.52|c0|3",
        ]
        published_ids = [c.contact_id for c in contacts]

        # PARTITION EXTENSION inside c0's domain: t4 appends as ordinal 4;
        # ordinals 1–3 and their published ids are unchanged (append-only,
        # never renumbered, never reused).
        extended = assign_occurrence_ordinals(
            physical_object_id=poid,
            t_exact_list=[*self.T_CROSSINGS, self.T4],
        )
        assert len(extended) == 4
        assert [c.contact_id for c in extended[:3]] == published_ids
        assert extended[3].occurrence_ordinal == 4
        assert (
            contact_identity_bytes(extended[3])
            == "Mars|conjunction|point:198.52|c0|4"
        )


# ── O-SM-3 (§7): every station event swiss_refined ───────────────────────────

class TestOSM3StationSolverMethodAudit:
    """Every station event in the built substrate has
    solver_method = 'swiss_refined' (spec §7.1: stations are ALWAYS
    Swiss-refined — δt ≈ δλ/|λ̇| is unstable near a station). POSITIVE
    CONTROL per R2-S06: at least one station event must exist — an empty
    substrate may not vacuously pass (oracle O-SM-3).

    Deferred mutation (checked at the A5.5 rehearsal): any
    arc_index_bracket station row, or a vacuous pass on zero station rows,
    fails.
    """

    def test_every_station_swiss_refined_with_positive_control(self):
        # Frozen expected interface (spec v1.4 §6/§7.1) — NOT YET BUILT: no
        # station sky_event store carrying solver_method exists.
        from services.gochara_kernel.substrate import SkyEventStore  # noqa: F401

        store = SkyEventStore.from_env()
        stations = store.events(event_kind="station")
        # POSITIVE CONTROL first (R2-S06).
        assert len(stations) > 0, (
            "zero station events in the substrate — a vacuous pass is forbidden"
        )
        violations = [s for s in stations if s.solver_method != "swiss_refined"]
        assert violations == [], (
            f"{len(violations)} station event(s) not swiss_refined: "
            f"{violations[:3]}"
        )

    test_every_station_swiss_refined_with_positive_control = pytest.mark.xfail(
        reason="A5.2 substrate not built: services.gochara_kernel.substrate.SkyEventStore "
        "(station sky events carrying solver_method)",
        strict=False,
    )(test_every_station_swiss_refined_with_positive_control)
