"""
chart_reader_v4.py — PRATIJÑĀ v4 Lane B1: the Chart Reader.

The Chart Reader is a thin, deterministic, READ-ONLY selection API over
three Postgres tables — `chart_divisionals` (migration `002_ganita_
divisionals.sql`, base graha/varga/house occupancy+position data),
`chart_facts` (migration `204_chart_facts.sql`, DERIVED analytical
signals), and `chart_fact_identity` (migration TBD per ADHIṢṬHĀNA Lane A5,
the identity index over `chart_facts`). Per the campaign brief
(`00_ARCHITECTURE/briefs/pratijna_v4/PRATIJNA_V4_STATE.md`), this Reader is
the ONLY way the future v4 scoring engine (Lane B2, not built here) may
touch the database — it never computes astrology itself, only retrieves
already-computed L1 facts.

Architectural finding this module respects throughout (verified live,
`platform/scripts/probes/probe_p2_tracer.py`): `chart_facts` carries ZERO
raw occupancy/position facts. Base positional data (which graha occupies
which house, which sign a graha sits in for a given varga, which graha
rules a house) lives EXCLUSIVELY in `chart_divisionals`. `chart_facts`
(joined via `chart_fact_identity`) carries only DERIVED signals: dignity
states, ashtakavarga bindus, bhava bala components, aspects, vargottama
flags, special lagnas, Jaimini karakas, yoga firings, etc. Every function
below queries the table that actually holds the kind of answer it's
asking for — never forces a base-position question through `chart_facts`.

── Judgment call #1 — provenance for `chart_divisionals`-sourced answers ──

`chart_divisionals` has NO `fact_id` column (only its own UUID `id` primary
key) — it was never part of the "substring swamp" `chart_fact_identity`
was built to index, and was never given a `fact_id`. Rather than fabricate
a fake `fact_id`-shaped value for divisional-sourced rows (forbidden by
CLAUDE.md B.10 / R13), every provenance entry in this module is a small,
explicitly-tagged record:

    {"source_table": "chart_divisionals", "id_kind": "chart_divisionals_id", "id": <uuid str>}
    {"source_table": "chart_facts",       "id_kind": "fact_id",              "id": <fact_id str>}

Callers must branch on `id_kind`, not assume every provenance entry is a
`fact_id`. This is a genuine, disclosed judgment call (per R16), not a
default one — an alternative (minting a synthetic `fact_id`-shaped string
for divisional rows) was rejected specifically because it would let a
downstream consumer mistake a divisional-table row id for a real L1
`chart_facts.fact_id`, silently defeating the derivation-ledger discipline
(CLAUDE.md B.3) this module exists to serve.

── Judgment call #2 — extending the 5-function API with `sign_of` ──────────

The Lane B1 brief specifies five functions (`occupants`, `lord_of`,
`graha_state`, `special_points`, `aspect_between`). Rung P4's acceptance
test requires reproducing probe_p2_tracer's three tracer questions exactly,
one of which is "VEN's D9 SIGN" — a question about SIGN placement, not
house occupancy (`occupants`), house lordship (`lord_of`), or a derived
chart_facts signal (`graha_state`/`special_points`/`aspect_between`). None
of the five specified functions answer "what sign is graha X in, in varga
V" as their primary contract. Rather than force this question through
`occupants` (which answers "who is in this house", not "what sign is this
graha in") or `graha_state` (which sources DERIVED chart_facts signals,
not base sign placement), this module adds a sixth function, `sign_of`,
sourced from the same `chart_divisionals` base-position table `occupants`/
`lord_of` already use (`fact_category='varga_position'`, `fact_key='sign'`)
— genuinely new base-position retrieval, not a repackaging of an existing
function. Flagged here per the brief's instruction to justify any API
extension in the PR description.

── No dignity computation ──────────────────────────────────────────────────

This Reader never computes dignity. `graha_state`/`lord_of` read the
already-computed `dignity_state` fact L1 wrote (`chart_facts.fact_key=
'dignity_state'`, category `graha_dignity_per_varga`). The classical
dignity ladder, for context only (not re-implemented here), is
`ga_condition_writer.py`'s `DIGNITY_SCORES` (band values) and `_NAISARGIKA`
(naisargika friend/enemy table).

── Deterministic ordering ───────────────────────────────────────────────────

Every query that can return more than one row carries an explicit
`ORDER BY` over columns that are stable per-chart (never row-insertion
order). Where the underlying data genuinely contains more than one
irreducible answer for the same nominal key (see `special_points`'s
Jaimini-karaka `karaka_school` duplication, discovered live — Parashari
Rahu-excluded vs K.N. Rao Rahu-included conventions both stored under the
identical `fact_subject`/`fact_key`), this module does NOT silently pick
one and hide the other (that would be exactly the kind of fabricated
single answer B.10/R13 forbid) — it returns all of them, each with its own
provenance, ordered deterministically, and lets the caller (which has the
domain knowledge to prefer a school) decide.
"""
from __future__ import annotations

import os
from typing import Any

import psycopg
import psycopg.rows

from brahmagyan.graha_vocabulary import norm_graha, to_title

# ── Constants ────────────────────────────────────────────────────────────

DEFAULT_AYANAMSHA = "lahiri_chitrapaksha"

# Classical whole-sign rulership (BPHS) — undisputed across every Vedic
# paradigm, safe to hardcode per CLAUDE.md B.10. Mirrors
# `probe_p2_tracer.py`'s `SIGN_LORD` table verbatim (kept as a literal copy,
# not an import, because the probe is a standalone script outside the
# sidecar's package path — see `test_chart_reader_v4.py::
# test_sign_lord_matches_probe_p2_tracer` for the drift guard that keeps
# this copy honest).
SIGN_LORD: dict[int, str] = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
    7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}

# `special_points` recognized kinds -> the chart_facts.fact_category each
# maps to. A closed, explicit set (not a free-text passthrough) so an
# unrecognized kind fails loudly rather than silently returning nothing.
_SPECIAL_POINT_KINDS: dict[str, str] = {
    "upapada": "upapada_lagna",
    "special_lagna": "special_lagna",
    "karaka": "karaka_chara_position",
}


class ChartReaderError(Exception):
    """Raised for a malformed request (unrecognized kind, missing data path
    with no honest fallback, etc.) — never silently swallowed."""


def _sign_of_longitude(lon: float) -> int:
    return int(lon // 30) + 1


def get_dburl() -> str:
    if os.environ.get("DBURL"):
        return os.environ["DBURL"]
    raise RuntimeError(
        "DBURL not set — see PRATIJNA_V4_STATE.md 'DB access' section for the "
        "gcloud-secret + cloud-sql-proxy resolution recipe."
    )


def connect(dburl: str | None = None) -> psycopg.Connection:
    """Open a read-only connection. Callers own the connection's lifecycle
    (mirrors probe_p1_identity.py / probe_p2_tracer.py convention)."""
    conn = psycopg.connect(dburl or get_dburl(), row_factory=psycopg.rows.dict_row)
    conn.read_only = True
    return conn


def _prov_fact(fact_id: str) -> dict[str, str]:
    return {"source_table": "chart_facts", "id_kind": "fact_id", "id": str(fact_id)}


def _prov_divisional(row_id: str) -> dict[str, str]:
    return {"source_table": "chart_divisionals", "id_kind": "chart_divisionals_id", "id": str(row_id)}


def _prov_derived(note: str) -> dict[str, str]:
    """Provenance for an answer this Reader DERIVED from other cited facts
    (never a fabricated value — every derived answer's own inputs carry
    their own provenance entries alongside this marker)."""
    return {"source_table": "derived", "id_kind": "derivation_note", "id": note}


# ── The Reader ───────────────────────────────────────────────────────────


class ChartReaderV4:
    """The PRATIJÑĀ v4 Chart Reader. One instance per (connection,
    ayanamsha) pair — `ayanamsha` is fixed at construction because every
    caller in this campaign uses a single ayanamsha throughout
    (`lahiri_chitrapaksha`, per campaign convention) and passing it on
    every call would be pure repetition with no behavioral benefit."""

    def __init__(self, conn: psycopg.Connection, ayanamsha: str = DEFAULT_AYANAMSHA):
        self.conn = conn
        self.ayanamsha = ayanamsha

    # ── occupants ────────────────────────────────────────────────────────

    def occupants(self, chart_id: str, house: int, varga: str = "D1") -> list[dict[str, Any]]:
        """Which graha(s) occupy `house` in `varga`. Source:
        chart_divisionals, fact_category='varga_house_occupant'."""
        with self.conn.cursor() as cur:
            cur.execute(
                """SELECT id, graha, house, sign, sign_number FROM chart_divisionals
                   WHERE chart_id=%s AND ayanamsha_id=%s AND varga=%s
                     AND fact_category='varga_house_occupant' AND house=%s
                   ORDER BY graha""",
                (chart_id, self.ayanamsha, varga, house),
            )
            rows = cur.fetchall()
        return [
            {
                "graha": r["graha"],
                "house": r["house"],
                "varga": varga,
                "sign": r["sign"],
                "sign_number": r["sign_number"],
                "provenance": [_prov_divisional(r["id"])],
            }
            for r in rows
        ]

    # ── sign_of (extension — see module docstring judgment call #2) ────────

    def sign_of(self, chart_id: str, graha_code: str, varga: str = "D1") -> dict[str, Any]:
        """What sign `graha_code` occupies in `varga`. Source:
        chart_divisionals, fact_category='varga_position', fact_key='sign'
        (single deterministic row per chart/graha/varga/ayanamsha)."""
        graha_title = to_title(graha_code)
        with self.conn.cursor() as cur:
            cur.execute(
                """SELECT id, sign, sign_number FROM chart_divisionals
                   WHERE chart_id=%s AND ayanamsha_id=%s AND varga=%s AND graha=%s
                     AND fact_category='varga_position' AND fact_key='sign'
                   ORDER BY id LIMIT 1""",
                (chart_id, self.ayanamsha, varga, graha_title),
            )
            row = cur.fetchone()
        if row is None:
            raise ChartReaderError(
                f"No varga_position/sign row for chart={chart_id} graha={graha_title} varga={varga}"
            )
        return {
            "graha": graha_title,
            "varga": varga,
            "sign": row["sign"],
            "sign_number": row["sign_number"],
            "provenance": [_prov_divisional(row["id"])],
        }

    # ── lord_of ──────────────────────────────────────────────────────────

    def lord_of(self, chart_id: str, house: int, varga: str = "D1") -> dict[str, Any]:
        """The lord of `house` in `varga`: placement + dignity inputs.
        Source order: (1) chart_divisionals fact_category='varga_house_lord'
        direct row; (2) if absent (a documented chart_divisionals gap — see
        probe_p2_tracer.py), derive from the bhava-cusp longitude +
        classical whole-sign rulership, mirroring the probe's own fallback
        exactly. Attaches the L1 dignity_state fact for lord+varga from
        chart_facts via chart_fact_identity, per the explicit spec
        requirement ("placement + dignity inputs")."""
        provenance: list[dict[str, str]] = []
        with self.conn.cursor() as cur:
            cur.execute(
                """SELECT id, graha, house AS lord_own_house, sign FROM chart_divisionals
                   WHERE chart_id=%s AND ayanamsha_id=%s AND varga=%s
                     AND fact_category='varga_house_lord' AND house=%s
                   ORDER BY id LIMIT 1""",
                (chart_id, self.ayanamsha, varga, house),
            )
            lord_row = cur.fetchone()

        if lord_row is not None:
            lord = lord_row["graha"]
            lord_house = lord_row["lord_own_house"]
            source = "chart_divisionals.varga_house_lord (direct row)"
            provenance.append(_prov_divisional(lord_row["id"]))
        else:
            if varga != "D1":
                raise ChartReaderError(
                    f"No varga_house_lord row for chart={chart_id} varga={varga} house={house}, "
                    f"and the whole-sign-rulership fallback (probe_p2_tracer.py) is only defined "
                    f"for D1 bhava cusps — no honest fallback exists for varga != D1."
                )
            with self.conn.cursor() as cur:
                cur.execute(
                    """SELECT fact_id, fact_value_num FROM chart_facts
                       WHERE chart_id=%s AND ayanamsha_id=%s AND fact_category='bhava_cusps'
                         AND fact_subject=%s AND fact_key='sripati_madhya'
                       ORDER BY fact_id LIMIT 1""",
                    (chart_id, self.ayanamsha, f"BHAVA_{house:02d}"),
                )
                cusp_row = cur.fetchone()
            if cusp_row is None:
                raise ChartReaderError(
                    f"No bhava_cusps/sripati_madhya fact for chart={chart_id} house={house} "
                    f"— cannot derive lord via fallback."
                )
            h_sign = _sign_of_longitude(float(cusp_row["fact_value_num"]))
            lord = SIGN_LORD[h_sign]
            lord_house = None
            source = (
                f"DERIVED — chart_divisionals.varga_house_lord has no house={house} row; fell back "
                f"to bhava_cusps sripati_madhya={cusp_row['fact_value_num']}° -> sign {h_sign} -> "
                f"classical whole-sign lord (BPHS, hardcoded per B.10)"
            )
            provenance.append(_prov_fact(cusp_row["fact_id"]))
            provenance.append(_prov_derived("whole_sign_rulership_fallback"))

            # The fallback only tells us WHO the lord is, not where the lord
            # sits — look that up separately from chart_divisionals, same as
            # the probe does.
            with self.conn.cursor() as cur:
                cur.execute(
                    """SELECT id, house FROM chart_divisionals
                       WHERE chart_id=%s AND ayanamsha_id=%s AND varga=%s AND graha=%s
                         AND fact_category='varga_house_occupant'
                       ORDER BY id LIMIT 1""",
                    (chart_id, self.ayanamsha, varga, lord),
                )
                occ_row = cur.fetchone()
            if occ_row is not None:
                lord_house = occ_row["house"]
                provenance.append(_prov_divisional(occ_row["id"]))

        # Attach L1 dignity_state for lord+varga (chart_facts via chart_fact_identity).
        lord_code = norm_graha(lord)
        with self.conn.cursor() as cur:
            cur.execute(
                """SELECT cf.fact_id, cf.fact_value_text FROM chart_fact_identity cfi
                   JOIN chart_facts cf ON cf.fact_id = cfi.fact_id
                   WHERE cfi.chart_id=%s AND cfi.graha_code=%s AND cfi.varga_id=%s
                     AND cf.ayanamsha_id=%s AND cf.fact_category='graha_dignity_per_varga'
                     AND cf.fact_key='dignity_state'
                   ORDER BY cf.fact_id LIMIT 1""",
                (chart_id, lord_code, varga, self.ayanamsha),
            )
            dignity_row = cur.fetchone()
        dignity_state = None
        if dignity_row is not None:
            dignity_state = dignity_row["fact_value_text"]
            provenance.append(_prov_fact(dignity_row["fact_id"]))

        return {
            "house": house,
            "varga": varga,
            "lord": lord,
            "lord_own_house": lord_house,
            "dignity_state": dignity_state,
            "source": source,
            "provenance": provenance,
        }

    # ── graha_state ──────────────────────────────────────────────────────

    def graha_state(self, chart_id: str, graha_code: str, varga: str = "D1") -> dict[str, Any]:
        """DERIVED chart_facts signals for `graha_code` in `varga`
        (dignity_state at minimum, plus every other identity-tagged
        graha_in_varga signal found — never a newly-invented signal type).
        Source: chart_facts via chart_fact_identity, entity_kind=
        'graha_in_varga'."""
        code = norm_graha(graha_code)
        with self.conn.cursor() as cur:
            cur.execute(
                """SELECT cf.fact_id, cf.fact_category, cf.fact_key, cf.fact_value_text,
                          cf.fact_value_num
                   FROM chart_fact_identity cfi JOIN chart_facts cf ON cf.fact_id = cfi.fact_id
                   WHERE cfi.chart_id=%s AND cfi.entity_kind='graha_in_varga'
                     AND cfi.graha_code=%s AND cfi.varga_id=%s AND cf.ayanamsha_id=%s
                   ORDER BY cf.fact_category, cf.fact_key, cf.fact_id""",
                (chart_id, code, varga, self.ayanamsha),
            )
            rows = cur.fetchall()

        signals = [
            {
                "fact_category": r["fact_category"],
                "fact_key": r["fact_key"],
                "fact_value_text": r["fact_value_text"],
                "fact_value_num": r["fact_value_num"],
                "provenance": [_prov_fact(r["fact_id"])],
            }
            for r in rows
        ]
        dignity_state = next(
            (
                s["fact_value_text"]
                for s in signals
                if s["fact_category"] == "graha_dignity_per_varga" and s["fact_key"] == "dignity_state"
            ),
            None,
        )
        return {
            "graha": code,
            "varga": varga,
            "dignity_state": dignity_state,
            "signals": signals,
        }

    # ── special_points ───────────────────────────────────────────────────

    def special_points(self, chart_id: str, kind: str) -> list[dict[str, Any]]:
        """Special points (upapada, Jaimini char karakas, other special
        lagnas). `kind` in {'upapada', 'special_lagna', 'karaka'}. Source:
        chart_facts, identity-tagged rows keyed by fact_subject (e.g.
        UPAPADA_LAGNA, DARAKARAKA) — these subjects are recognized-but-
        dimensionless special-point/karaka-role tokens per
        fact_identity_parser.py's KNOWN_SPECIAL_POINTS/KNOWN_KARAKA_ROLES,
        so they carry NO chart_fact_identity row; this function queries
        chart_facts directly by fact_category+fact_subject instead.

        Returns RAW facts (fact_subject, fact_key, value, provenance), not
        a fabricated merged object — see module docstring on the live
        karaka_school duplication this discipline exists to handle
        honestly (two independently-computed Jaimini karaka assignments,
        Parashari-Rahu-excluded vs K.N.Rao-Rahu-included, share the same
        fact_subject/fact_key; this function surfaces both rather than
        silently picking one)."""
        if kind not in _SPECIAL_POINT_KINDS:
            raise ChartReaderError(
                f"Unrecognized special_points kind={kind!r}; known kinds: "
                f"{sorted(_SPECIAL_POINT_KINDS)}"
            )
        category = _SPECIAL_POINT_KINDS[kind]
        with self.conn.cursor() as cur:
            cur.execute(
                """SELECT fact_id, fact_subject, fact_key, fact_value_text, fact_value_num,
                          computed_at
                   FROM chart_facts
                   WHERE chart_id=%s AND ayanamsha_id=%s AND fact_category=%s
                   ORDER BY fact_subject, fact_key, computed_at, fact_id""",
                (chart_id, self.ayanamsha, category),
            )
            rows = cur.fetchall()
        return [
            {
                "kind": kind,
                "fact_subject": r["fact_subject"],
                "fact_key": r["fact_key"],
                "fact_value_text": r["fact_value_text"],
                "fact_value_num": r["fact_value_num"],
                "provenance": [_prov_fact(r["fact_id"])],
            }
            for r in rows
        ]

    # ── reference_planets (extension — see PRATIJÑĀ v4 Lane B2 PR description) ──

    def reference_planets(self, planet: str | None = None) -> list[dict[str, Any]]:
        """Static classical planetary attributes (exaltation/debilitation/
        mooltrikona/own-signs/natural_benefic), from the GLOBAL `reference_
        planets` table (BPHS, L0 Brahmagyan — not chart-scoped, no chart_id/
        ayanamsha filter, unlike every other method on this Reader).

        Judgment call (Lane B2, disclosed per the campaign brief's Reader-gap
        instruction): the five original + `sign_of` functions only ever
        answer questions about a specific chart's computed facts
        (`chart_divisionals`/`chart_facts`). `V4_RUBRIC_SPEC_v1_0.md §2.1`'s
        dignity band is instead anchored on `reference_planets`, a static L0
        reference table with no chart_id column at all — a genuinely
        different kind of question ("what IS Venus's exaltation sign",
        never "what is Venus's exaltation sign in THIS chart"). Rather than
        have the v4 engine (Lane B2) issue raw SQL against a table outside
        this Reader's stated scope, this small addition keeps 'the Reader is
        the only way the engine touches the database' true in spirit as well
        as letter, at the cost of the Reader no longer being purely
        chart-scoped. Source: `platform/migrations/ws2_l0_reference.sql`."""
        with self.conn.cursor() as cur:
            if planet is not None:
                cur.execute(
                    """SELECT planet_id, canonical_name_en, exaltation_sign, debilitation_sign,
                              mooltrikona_sign, own_signs, natural_benefic, source_citation
                       FROM reference_planets WHERE planet_id=%s""",
                    (to_title(planet).lower(),),
                )
            else:
                cur.execute(
                    """SELECT planet_id, canonical_name_en, exaltation_sign, debilitation_sign,
                              mooltrikona_sign, own_signs, natural_benefic, source_citation
                       FROM reference_planets ORDER BY planet_id"""
                )
            rows = cur.fetchall()
        return [
            {
                "planet_id": r["planet_id"],
                "graha": r["canonical_name_en"],
                "exaltation_sign": r["exaltation_sign"],
                "debilitation_sign": r["debilitation_sign"],
                "mooltrikona_sign": r["mooltrikona_sign"],
                "own_signs": list(r["own_signs"] or []),
                "natural_benefic": r["natural_benefic"],
                "provenance": [
                    {"source_table": "reference_planets", "id_kind": "planet_id", "id": r["planet_id"]}
                ],
            }
            for r in rows
        ]

    # ── aspect_between ───────────────────────────────────────────────────

    def aspect_between(
        self, chart_id: str, graha_a: str, graha_b: str, varga: str = "D1"
    ) -> dict[str, Any]:
        """Does `graha_a` aspect (classical graha-dṛṣṭi) the house
        `graha_b` occupies in `varga`? Composed from two already-computed
        L1 facts — never a fresh aspect computation:
          (1) which house graha_b occupies in varga (chart_divisionals,
              varga_house_occupant — same source as `occupants`);
          (2) whether graha_a's own identity-tagged aspect fact for that
              varga names that house (chart_facts via chart_fact_identity,
              fact_category='aspect_parashari_given' for D1 or
              'aspect_parashari_per_varga' for other vargas)."""
        code_a = norm_graha(graha_a)
        title_b = to_title(graha_b)

        with self.conn.cursor() as cur:
            cur.execute(
                """SELECT id, house FROM chart_divisionals
                   WHERE chart_id=%s AND ayanamsha_id=%s AND varga=%s AND graha=%s
                     AND fact_category='varga_house_occupant'
                   ORDER BY id LIMIT 1""",
                (chart_id, self.ayanamsha, varga, title_b),
            )
            occ_row = cur.fetchone()
        if occ_row is None:
            raise ChartReaderError(
                f"No varga_house_occupant row for chart={chart_id} graha={title_b} varga={varga} "
                f"— cannot determine which house graha_b occupies."
            )
        target_house = occ_row["house"]
        provenance = [_prov_divisional(occ_row["id"])]

        aspect_category = "aspect_parashari_given" if varga == "D1" else "aspect_parashari_per_varga"
        target_key = f"house_{target_house}"

        if varga == "D1":
            with self.conn.cursor() as cur:
                cur.execute(
                    """SELECT fact_id, fact_value_num FROM chart_facts
                       WHERE chart_id=%s AND ayanamsha_id=%s AND fact_category=%s
                         AND fact_subject=%s AND fact_key=%s
                       ORDER BY fact_id LIMIT 1""",
                    (chart_id, self.ayanamsha, aspect_category, code_a, target_key),
                )
                aspect_row = cur.fetchone()
        else:
            with self.conn.cursor() as cur:
                cur.execute(
                    """SELECT cf.fact_id, cf.fact_value_num FROM chart_fact_identity cfi
                       JOIN chart_facts cf ON cf.fact_id = cfi.fact_id
                       WHERE cfi.chart_id=%s AND cfi.entity_kind='graha_in_varga'
                         AND cfi.graha_code=%s AND cfi.varga_id=%s AND cf.ayanamsha_id=%s
                         AND cf.fact_category=%s AND cf.fact_key=%s
                       ORDER BY cf.fact_id LIMIT 1""",
                    (chart_id, code_a, varga, self.ayanamsha, aspect_category, target_key),
                )
                aspect_row = cur.fetchone()

        aspects = aspect_row is not None
        if aspect_row is not None:
            provenance.append(_prov_fact(aspect_row["fact_id"]))

        return {
            "graha_a": code_a,
            "graha_b": norm_graha(graha_b),
            "varga": varga,
            "target_house": target_house,
            "aspects": aspects,
            "provenance": provenance,
        }
