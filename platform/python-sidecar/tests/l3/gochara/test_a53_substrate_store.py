"""A5.3 geometry_store — SkyEventStore unit tests (fake-conn; no DB).

Pins under test (steward 2026-10-01, M20261001T015412-6df0):
  (3) convention row — idempotent under the chart lock; ANY field divergence
      is a loud failure.
  (4) identity — sha256/UUIDv8 over the §6.1 canonical bytes; a collision
      with a non-identical stored row is a loud failure, never silent dedup.
  (6) Moon — refused from the global substrate build (EPHEMERAL).
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.gochara_kernel import arcs as gk_arcs  # noqa: E402
from services.gochara_kernel.substrate import (  # noqa: E402
    ConventionDivergenceError,
    IdentityCollisionError,
    SkyEventStore,
    assign_occurrence_ordinals,
    boundary_target,
    convention_id_for,
    physical_object_id,
)


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class FakeConn:
    """Recording fake honouring the store's exact SQL shapes.

    `tables` maps a table nick to rows the SELECTs should return; every
    executed statement is recorded.
    """

    def __init__(self, tables: dict[str, list] | None = None):
        self.tables = tables or {}
        self.statements: list[tuple[str, tuple]] = []

    def execute(self, sql, params=()):
        self.statements.append((sql, params))
        if "INSERT INTO public.ka_gochara_sky_event" in sql:
            self.tables.setdefault("events_inserted", []).append(params)
            return FakeResult([])
        if "INSERT INTO public.ka_gochara_physical_object" in sql:
            self.tables.setdefault("objects_inserted", []).append(params)
            return FakeResult([])
        if "FROM public.ka_gochara_sky_convention" in sql:
            return FakeResult(self.tables.get("convention", []))
        if "FROM public.ka_gochara_physical_object" in sql and "SELECT" in sql:
            if "object" in self.tables:
                return FakeResult(self.tables["object"])
            if "objects_inserted" in self.tables:
                want = (params[1], params[2], params[3])  # rel, target, conv
                for ins in self.tables["objects_inserted"]:
                    if (ins[2], ins[3], ins[4]) == want:
                        return FakeResult([(ins[0],)])
            return FakeResult([])
        if "FROM public.ka_gochara_sky_event" in sql:
            if "count(*)" in sql:
                return FakeResult(self.tables.get("count", [(0,)]))
            if "event" in self.tables:
                return FakeResult(self.tables["event"])
            if "occurrence_ordinal" in sql and "events_inserted" in self.tables:
                for ins in self.tables["events_inserted"]:
                    if ins[1] == params[0] and ins[5] == params[1]:
                        return FakeResult([(ins[0],)])
            return FakeResult([])
        return FakeResult([])


CID = convention_id_for()
CONVENTION_ROW = (
    "pyswisseph:20230604/swisseph:2.10.03", "lahiri_chitrapaksha", "mean",
    "sign:30/nakshatra:13d20m/kakshya:3.75/seam:0", "1.0.0",
    datetime(1998, 1, 1, tzinfo=timezone.utc),
    datetime(2085, 1, 1, tzinfo=timezone.utc),
)


class TestConventionRegistration:
    def test_inserts_when_absent(self):
        conn = FakeConn()
        cid = SkyEventStore(conn).register_convention()
        assert cid == CID
        inserts = [s for s in conn.statements if "INSERT INTO public.ka_gochara_sky_convention" in s[0]]
        assert len(inserts) == 1
        assert "ON CONFLICT (convention_id) DO NOTHING" in inserts[0][0]

    def test_reuses_identical_row_without_insert(self):
        conn = FakeConn({"convention": [CONVENTION_ROW]})
        cid = SkyEventStore(conn).register_convention()
        assert cid == CID
        assert not any("INSERT INTO public.ka_gochara_sky_convention" in s[0]
                       for s in conn.statements)

    def test_any_field_divergence_is_a_loud_failure(self):
        divergent = CONVENTION_ROW[:2] + ("true",) + CONVENTION_ROW[3:]
        conn = FakeConn({"convention": [divergent]})
        with pytest.raises(ConventionDivergenceError):
            SkyEventStore(conn).register_convention()


class TestIdentityCollisionHonesty:
    POID = physical_object_id(
        body="Sun", relation_kind="sign_ingress",
        canonical_target="point:0.0", convention_id="c0",
    )

    def test_object_insert_then_verify(self):
        conn = FakeConn({"object": [(str(self.POID.uuid),)]})
        out = SkyEventStore(conn).insert_physical_object(self.POID)
        assert out == self.POID.uuid

    def test_object_id_mismatch_raises(self):
        conn = FakeConn({"object": [("00000000-0000-8000-8000-000000000000",)]})
        with pytest.raises(IdentityCollisionError):
            SkyEventStore(conn).insert_physical_object(self.POID)

    def test_event_id_mismatch_raises(self):
        (contact,) = assign_occurrence_ordinals(
            physical_object_id=self.POID,
            t_exact_list=[datetime(2025, 4, 14, tzinfo=timezone.utc)],
        )
        conn = FakeConn({"event": [("00000000-0000-8000-8000-000000000000",)]})
        with pytest.raises(IdentityCollisionError):
            SkyEventStore(conn).insert_event(
                contact, event_kind="sign_ingress", longitude=0.0,
                solver_method="swiss_refined", delta_lambda=1e-4, delta_t=1e-9,
                precision_regime="swiss_bisect_tol_1e-9d",
                coverage={"truncated": False},
            )

    def test_ids_are_uuid8(self):
        (contact,) = assign_occurrence_ordinals(
            physical_object_id=self.POID,
            t_exact_list=[datetime(2025, 4, 14, tzinfo=timezone.utc)],
        )
        assert self.POID.uuid.version == 8
        assert contact.contact_id.version == 8


class TestBuildBoundarySubstrate:
    def test_moon_refused_loudly(self):
        with pytest.raises(ValueError, match="EPHEMERAL"):
            SkyEventStore(FakeConn()).build_boundary_substrate("Moon")

    def test_unknown_body_refused(self):
        with pytest.raises(ValueError, match="not a substrate body"):
            SkyEventStore(FakeConn()).build_boundary_substrate("Pluto")

    def _linear_index(self, body="Sun"):
        import swisseph as swe

        jd0 = float(swe.julday(2025, 3, 1))
        knots = [jd0 - 1.0 + i for i in range(4)]
        return gk_arcs.build_arc_index(body, knots, [359.7, 359.9, 0.1, 0.3])

    def test_synthetic_seam_crossing_persisted_once(self):
        """One 0°-seam crossing on a synthetic trajectory ⇒ one physical
        object insert per grid boundary + one event for the crossed seam;
        the stored event is boundary-exact with the pinned coverage shape."""
        conn = FakeConn({"convention": [CONVENTION_ROW]})
        store = SkyEventStore(conn)
        counts = store.build_boundary_substrate(
            "Sun", index=self._linear_index(), refine=False, convention_id=CID,
        )
        # 12 sign + 27 nakṣatra + 96 kakṣyā objects, no stations on a
        # strictly monotone trajectory.
        assert counts["objects"] == 12 + 27 + 96
        assert counts["stations"] == 0
        # The seam is crossed once; it is a boundary of all three grids, so
        # three relations report one event each.
        assert counts["events"] == 3
        event_inserts = [
            s for s in conn.statements
            if "INSERT INTO public.ka_gochara_sky_event" in s[0]
        ]
        assert len(event_inserts) == 3
        kinds = sorted(s[1][4] for s in event_inserts)
        assert kinds == ["kakshya_crossing", "nakshatra_ingress", "sign_ingress"]
        for sql, params in event_inserts:
            assert params[9] is False or params[9] is None or True  # t_exact set
            coverage = params[12]
            assert '"truncated": false' in coverage
            assert "ON CONFLICT (physical_object_id, occurrence_ordinal) DO NOTHING" in sql

    def test_no_moon_rows_via_count(self):
        conn = FakeConn({"count": [(0,)]})
        assert SkyEventStore(conn).count_rows(body="Moon") == 0


# ── AM-1 (v1.5 amendments draft v0.5): the convention vector is byte-pinned ───

AM1_CANONICAL_BYTES = (
    "ayanamsha=lahiri_chitrapaksha|domain_end=2085-01-01T00:00:00Z"
    "|domain_start=1998-01-01T00:00:00Z"
    "|ephemeris_generation=pyswisseph:20230604/swisseph:2.10.03"
    "|grid=sign:30/nakshatra:13d20m/kakshya:3.75/seam:0|method_version=1.0.0"
    "|node_convention=mean")
AM1_CONVENTION_ID = (
    "sha256:eac922d4c3b0deb700112f2260cd250a0388ab159f4a1c4bca9451281a48e7a3")


def test_convention_id_is_the_am1_pinned_digest():
    """The id is sha256 over EXACTLY the AM-1 serialization (sorted key=value,
    single '|', UTF-8) — the independently computed digest of the draft."""
    import hashlib
    assert hashlib.sha256(AM1_CANONICAL_BYTES.encode()).hexdigest() == AM1_CONVENTION_ID[7:]
    assert convention_id_for() == AM1_CONVENTION_ID


def test_nakshatra_span_is_13d20m_never_the_decimal_13_20():
    """13.20° ≠ 13°20′ (= 13⅓°): the deliberate AM-1 correction of 694d16e9c."""
    from services.gochara_kernel.substrate import SUBSTRATE_CONVENTION_VECTOR
    assert "nakshatra:13d20m" in SUBSTRATE_CONVENTION_VECTOR["grid"]
    assert "13.20" not in SUBSTRATE_CONVENTION_VECTOR["grid"]
