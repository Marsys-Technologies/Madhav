"""A5.4 resonance_rebuild_R1_R6 — disposable-DB rehearsal of the WP3c (R-1..R-6)
resonance-map rebuild (FABLE_ASTROLOGICAL_REVIEW_GOCHARA_v3_0 T0-12, finding #9).

NEVER production. The DSN must name a loopback disposable database (the
gochara-wp6-disposable PG16 container convention); anything else exits 4.

What this does, on a FRESH disposable database:
  1. Applies the REAL migrations for the served table verbatim:
     platform/migrations/459_gochara_resonance_map.sql and
     platform/migrations/1080_nirmana_l3_gochara_resonance_target_resolution_state.sql
     (with minimal faithful DDL for the writer's input tables — chart_facts,
     brahma_event_ontology, bg_transit_rules, ga_yoga_firings, chart_dashas,
     reference_signs, and an asset_registry stub so 459 applies verbatim).
  2. Seeds a synthetic canonical-chart fixture (chart_id
     482012f1-710e-4a25-994a-93821f5871aa) that reproduces the finding-#9
     production shape: 176 sensitive-degree check facts, 154 of them
     negative-result (not_fired / not_gandanta / not_pushkara / none), plus a
     pre-WP3c legacy gochara_resonance_map partition whose 176
     sensitive_degree targets key those facts (the "before" state).
  3. Runs the REAL writer — KaGocharaResonanceWriter.run(ctx) — against the
     disposable DB (the harness owns the connection and commits; the writer
     never commits, per its contract).
  4. Prints the verification block: negative-result sensitive targets after
     the rebuild (must be 0), per-target_type before/after counts,
     target_resolution_state coverage, arudha sign-level typing, yoga
     live-validation + dropped_since_prior_build, lord states, and the
     writer's own WP3c build notes (WriterResult.notes JSON).

Usage:
  python3 resonance_rebuild_disposable_rehearsal.py \
      --dsn postgresql://wp6:local@127.0.0.1:55435/resonance_a54
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from urllib.parse import urlparse

SIDECAR = Path(__file__).resolve().parents[2]
MIGRATIONS = SIDECAR.parent / "migrations"
sys.path.insert(0, str(SIDECAR))

LOOPBACK = {"localhost", "127.0.0.1", "::1"}

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
AYANAMSHA = "lahiri_chitrapaksha"

NEGATIVE_VALUES = ["not_fired", "not_gandanta", "not_pushkara", "none"]
POSITIVE_VALUES = ["fired", "gandanta", "papa_kartari", "shubha_kartari", "pushkara"]
SENSITIVE_KEYS = ["mrityu_bhaga", "gandanta", "kartari", "pushkara"]

# (subject, sign_num) — graha_sign_attributes; LAGNA anchors whole-sign houses.
SIGN_NUMS = {
    "LAGNA": 1, "SUN": 5, "MOON": 4, "MAR": 8, "MER": 6, "JUP": 9,
    "VEN": 7, "SAT": 10, "RAH_MEAN": 11, "KET_MEAN": 5,
}

# Mirrors COVERAGE_QUALITY_NOTES in services/ka_gochara_resonance/writer.py —
# synthetic rehearsal signature models, same shapes as the seeded ontology.
SIGNATURE_MODELS = {
    "marriage": ([7, 2], ["7L"], ["Venus"]),
    "major_gain": ([2, 11], ["2L", "11L"], ["Jupiter", "Mercury"]),
    "career_advancement": ([10, 11], ["10L", "11L"], ["Sun"]),
    "illness_acute": ([6, 8], ["6L", "8L"], ["Mars", "Saturn"]),
    "chronic_onset": ([6, 8], ["6L", "8L"], ["Saturn"]),
    "surgery": ([6, 8], ["6L", "8L"], ["Mars"]),
    "career_entry": ([10, 6, 1], ["10L", "6L"], ["Sun", "Saturn"]),
    "career_change": ([10, 3, 9], ["10L"], ["Rahu"]),
    "career_setback": ([10, 6, 8, 12], ["10L afflicted"], ["Saturn", "Rahu"]),
    "business_launch": ([7, 10, 11], ["7L", "10L", "11L"], ["Mercury", "Jupiter"]),
    "education_milestone": ([4, 5, 9], ["4L", "5L", "9L"], ["Mercury", "Jupiter"]),
    "exam_outcome": ([5, 9], ["5L"], ["Mercury"]),
    "romantic_start": ([5, 7], ["5L", "7L"], ["Venus"]),
    "separation": ([6, 8, 12], ["7L afflicted"], ["Rahu", "Saturn", "Mars"]),
    "childbirth": ([5, 1], ["5L"], ["Jupiter"]),
    "parental_event": ([4, 9], ["4L", "9L"], ["Moon", "Sun"]),
    "bereavement": ([8, 12, 2], ["8L", "maraka lords (2L/7L)"], ["Saturn", "Ketu"]),
    "major_loss": ([2, 11, 12], ["2L/11L afflicted", "12L"], ["Saturn", "Rahu"]),
    "property_acquisition": ([4], ["4L"], ["Mars"]),
    "relocation": ([4, 3, 12], ["4L", "3L"], ["Moon", "Rahu"]),
    "foreign_settlement": ([12, 9, 7], ["12L", "9L"], ["Rahu"]),
    "spiritual_turn": ([9, 12, 5], ["9L", "12L"], ["Jupiter", "Ketu"]),
    "achievement_recognition": ([10, 11, 5], ["10L", "11L", "5L"], ["Sun", "Mercury"]),
    "financial_deception": ([2, 11, 12], ["2L/11L afflicted", "12L"], ["Rahu", "Saturn"]),
    "psychological_arc": ([1, 6, 12], ["1L", "6L"], ["Moon", "Mercury", "Saturn"]),
    "travel_event": ([3, 9, 12], ["3L", "9L"], ["Moon"]),
}

STUB_DDL = """
CREATE TABLE IF NOT EXISTS asset_registry (
    asset_id TEXT PRIMARY KEY, layer TEXT, sort_order INT,
    sanskrit_name TEXT, english_name TEXT, english_description TEXT,
    storage_type TEXT, target_table TEXT, count_sql TEXT, size_sql TEXT,
    target_floor INT, scope TEXT, is_active BOOLEAN, has_writer BOOLEAN,
    layer_name TEXT, layer_index TEXT, catalog_status TEXT, depends_on TEXT[]
);
CREATE TABLE IF NOT EXISTS brahma_event_ontology (
    event_class_id TEXT PRIMARY KEY,
    signature_model JSONB,
    citations JSONB
);
CREATE TABLE IF NOT EXISTS bg_transit_rules (
    id SERIAL PRIMARY KEY,
    rule_type TEXT NOT NULL,
    graha TEXT NOT NULL,
    primary_house INT NOT NULL,
    classical_citation TEXT
);
CREATE TABLE IF NOT EXISTS chart_facts (
    fact_id UUID PRIMARY KEY,
    chart_id UUID NOT NULL,
    ayanamsha_id TEXT NOT NULL,
    fact_category TEXT NOT NULL,
    fact_subject TEXT NOT NULL,
    fact_key TEXT NOT NULL,
    fact_value_text TEXT,
    fact_value_num NUMERIC
);
CREATE TABLE IF NOT EXISTS ga_yoga_firings (
    chart_id UUID NOT NULL,
    ayanamsha_id TEXT NOT NULL,
    yoga_canonical_id TEXT NOT NULL,
    fired BOOLEAN NOT NULL,
    constituent_fact_ids JSONB,
    constituent_planets JSONB,
    constituent_houses JSONB,
    bhanga_active BOOLEAN
);
CREATE TABLE IF NOT EXISTS chart_dashas (
    chart_id UUID NOT NULL,
    ayanamsha_id TEXT NOT NULL,
    system_id TEXT NOT NULL,
    level_n INT NOT NULL,
    lord_graha TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reference_signs (
    sign_id INT PRIMARY KEY,
    lord TEXT NOT NULL
);
"""

SIGN_LORDS = [
    (1, "Mars"), (2, "Venus"), (3, "Mercury"), (4, "Moon"), (5, "Sun"),
    (6, "Mercury"), (7, "Venus"), (8, "Mars"), (9, "Jupiter"), (10, "Saturn"),
    (11, "Saturn"), (12, "Jupiter"),
]


def _apply_migration_file(cur, name: str) -> None:
    sql = (MIGRATIONS / name).read_text()
    cur.execute(sql)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsn", required=True)
    args = parser.parse_args()

    parsed = urlparse(args.dsn)
    if (parsed.hostname or "") not in LOOPBACK or parsed.port == 5433:
        print(f"REFUSED: DSN {args.dsn!r} is not a loopback disposable database.", file=sys.stderr)
        return 4

    import psycopg
    import psycopg.rows

    from services.ka_gochara_resonance.writer import (
        TARGET_EVENT_CLASSES, KaGocharaResonanceWriter,
    )

    conn = psycopg.connect(args.dsn, autocommit=False)
    cur = conn.cursor()

    # ── 1. schema: stub inputs + REAL migrations 459 + 1080 ─────────────────
    cur.execute(STUB_DDL)
    _apply_migration_file(cur, "459_gochara_resonance_map.sql")
    _apply_migration_file(cur, "1080_nirmana_l3_gochara_resonance_target_resolution_state.sql")

    # ── 2. seed the synthetic canonical chart ───────────────────────────────
    for event_class, (houses, lords, karakas) in SIGNATURE_MODELS.items():
        cur.execute(
            "INSERT INTO brahma_event_ontology (event_class_id, signature_model, citations)"
            " VALUES (%s, %s::jsonb, %s::jsonb)",
            (event_class,
             json.dumps({"houses": houses, "lords": lords, "karakas": karakas}),
             json.dumps(["BPHS synthetic rehearsal citation (disposable fixture)"])),
        )
    missing = set(TARGET_EVENT_CLASSES) - set(SIGNATURE_MODELS)
    assert not missing, f"fixture missing ontology rows for {missing}"

    cur.executemany(
        "INSERT INTO bg_transit_rules (rule_type, graha, primary_house, classical_citation)"
        " VALUES (%s, %s, %s, %s)",
        [("favourable", "venus", 7, "BPHS ch.29 (synthetic rehearsal)"),
         ("favourable", "jupiter", 11, "BPHS ch.29 (synthetic rehearsal)"),
         ("unfavourable", "saturn", 8, "Phaladeepika ch.26 (synthetic rehearsal)")],
    )
    cur.executemany("INSERT INTO reference_signs (sign_id, lord) VALUES (%s, %s)", SIGN_LORDS)

    fact_rows = []

    def add_fact(category, subject, key, text=None, num=None):
        fid = uuid.uuid4()
        fact_rows.append((str(fid), CHART_ID, AYANAMSHA, category, subject, key, text, num))
        return fid

    for subject, sign_num in SIGN_NUMS.items():
        add_fact("graha_sign_attributes", subject, "sign_num", num=sign_num)
        add_fact("graha_position", subject, "longitude_sidereal",
                 num=(sign_num - 1) * 30 + 12.3456)

    # Finding-#9 shape: 176 sensitive-degree checks, 154 negative-result.
    subjects = [s for s in SIGN_NUMS if s != "LAGNA"]
    sensitive_fact_ids: list[tuple[str, str]] = []  # (fact_id, value)
    for i in range(176):
        subject = subjects[i % len(subjects)]
        key = SENSITIVE_KEYS[i % len(SENSITIVE_KEYS)]
        value = NEGATIVE_VALUES[i % len(NEGATIVE_VALUES)] if i < 154 \
            else POSITIVE_VALUES[i % len(POSITIVE_VALUES)]
        # kartari's positive vocabulary excludes 'fired'/'gandanta' etc. —
        # pair each value with a key whose vocabulary contains it.
        vocab = {"mrityu_bhaga": ("fired", "not_fired"),
                 "gandanta": ("gandanta", "not_gandanta"),
                 "kartari": ("papa_kartari", "none"),
                 "pushkara": ("pushkara", "not_pushkara")}
        pos, neg = vocab[key]
        value = neg if i < 154 else pos
        fid = add_fact("sensitive_degree_check", subject, key, text=value)
        sensitive_fact_ids.append((str(fid), value))

    for h in range(1, 13):
        sign_name = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                     "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius",
                     "not_a_sign"][h - 1]  # A12 deliberately invalid (R-2 honesty)
        add_fact("arudha_pada", f"ARUDHA_A{h}", "sign", text=sign_name)

    add_fact("sensitive_point_gulika_mandi", "MANDI", "sign", text="Aries")
    add_fact("sensitive_point_gulika_mandi", "GULIKA", "sign", text="Taurus")
    add_fact("sensitive_point_gulika_mandi", "YAMAKANTAKA", "sign", text="Gemini")
    add_fact("panchanga_nakshatra_moon", "NAKSHATRA_MOON_BIRTH", "number", num=4)

    cur.executemany(
        "INSERT INTO chart_facts (fact_id, chart_id, ayanamsha_id, fact_category,"
        " fact_subject, fact_key, fact_value_text, fact_value_num)"
        " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        fact_rows,
    )

    cur.executemany(
        "INSERT INTO ga_yoga_firings (chart_id, ayanamsha_id, yoga_canonical_id, fired,"
        " constituent_fact_ids, constituent_planets, constituent_houses, bhanga_active)"
        " VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s)",
        [(CHART_ID, AYANAMSHA, "yoga_demo_gajakesari", True, '["f1","f2"]',
          '["venus","jupiter"]', "[7, 11]", False),
         (CHART_ID, AYANAMSHA, "yoga_demo_bhanga", True, '["f3"]',
          '["sun"]', "[10]", True),
         (CHART_ID, AYANAMSHA, "yoga_demo_stopped", False, '["f4"]',
          '["moon"]', "[4]", False)],
    )
    cur.executemany(
        "INSERT INTO chart_dashas (chart_id, ayanamsha_id, system_id, level_n, lord_graha)"
        " VALUES (%s, %s, 'vimshottari', 1, %s)",
        [(CHART_ID, AYANAMSHA, lord) for lord in
         ("venus", "jupiter", "saturn", "sun", "moon", "mars", "mercury", "rahu", "ketu")],
    )

    # ── 3. the BEFORE partition (pre-WP3c legacy map, finding #9 verbatim shape)
    for fid, _value in sensitive_fact_ids:
        cur.execute(
            "INSERT INTO gochara_resonance_map (chart_id, event_class, target_type,"
            " target_ref, weight, classical_citation, uncited_extension)"
            " VALUES (%s, 'marriage', 'sensitive_degree', %s, 0.5, NULL, TRUE)",
            (CHART_ID, fid),
        )
    # A prior-build yoga id that no longer fires (R-3 drift surfacing).
    cur.execute(
        "INSERT INTO gochara_resonance_map (chart_id, event_class, target_type,"
        " target_ref, weight, classical_citation, uncited_extension)"
        " VALUES (%s, 'marriage', 'yoga_constituent', 'yoga_demo_stopped', 0.7, NULL, TRUE)",
        (CHART_ID,),
    )
    conn.commit()

    def counts(label):
        out = {"label": label}
        out["total"] = cur.execute(
            "SELECT COUNT(*) FROM gochara_resonance_map WHERE chart_id=%s", (CHART_ID,)).fetchone()[0]
        out["by_type"] = dict(cur.execute(
            "SELECT target_type, COUNT(*) FROM gochara_resonance_map WHERE chart_id=%s"
            " GROUP BY target_type ORDER BY target_type", (CHART_ID,)).fetchall())
        out["sensitive_negative"] = cur.execute(
            "SELECT COUNT(*) FROM gochara_resonance_map m JOIN chart_facts f"
            " ON f.fact_id = m.target_ref::uuid"
            " WHERE m.chart_id=%s AND m.target_type='sensitive_degree'"
            " AND f.fact_category='sensitive_degree_check'"
            " AND f.fact_value_text = ANY(%s)",
            (CHART_ID, NEGATIVE_VALUES)).fetchone()[0]
        out["sensitive_total"] = out["by_type"].get("sensitive_degree", 0)
        return out

    before = counts("before_rebuild")

    # ── 4. run the REAL writer against the disposable DB ────────────────────
    from pipeline.orchestrator.writers import ContextSpec  # noqa: E402

    ctx = ContextSpec.__new__(ContextSpec)
    ctx.db_conn = conn
    ctx.config = {"chart_id": CHART_ID}
    ctx.dry_run = False
    result = KaGocharaResonanceWriter().run(ctx)
    conn.commit()  # the harness owns commit; the writer never does

    after = counts("after_rebuild")

    # ── 5. verification block ───────────────────────────────────────────────
    ver: dict = {"before": before, "after": after}
    ver["rows_missing_or_bad_resolution_state"] = cur.execute(
        "SELECT COUNT(*) FROM gochara_resonance_map WHERE chart_id=%s"
        " AND (target_resolution_state IS NULL"
        "      OR target_resolution_state NOT IN ('resolved','unavailable','unqualified'))",
        (CHART_ID,)).fetchone()[0]
    ver["resolution_state_counts"] = dict(cur.execute(
        "SELECT target_resolution_state, COUNT(*) FROM gochara_resonance_map"
        " WHERE chart_id=%s GROUP BY 1 ORDER BY 1", (CHART_ID,)).fetchall())
    ver["arudha_all_keyed_to_sign_facts"] = cur.execute(
        "SELECT COUNT(*) = (SELECT COUNT(*) FROM gochara_resonance_map"
        "  WHERE chart_id=%s AND target_type='arudha')"
        " FROM gochara_resonance_map m JOIN chart_facts f ON f.fact_id = m.target_ref::uuid"
        " WHERE m.chart_id=%s AND m.target_type='arudha' AND f.fact_key='sign'",
        (CHART_ID, CHART_ID)).fetchone()[0]
    ver["yoga_refs_not_live_fired"] = cur.execute(
        "SELECT COUNT(*) FROM gochara_resonance_map m"
        " WHERE m.chart_id=%s AND m.target_type='yoga_constituent'"
        " AND NOT EXISTS (SELECT 1 FROM ga_yoga_firings y"
        "   WHERE y.chart_id=m.chart_id AND y.ayanamsha_id=%s"
        "   AND y.yoga_canonical_id=m.target_ref AND y.fired)",
        (CHART_ID, AYANAMSHA)).fetchone()[0]
    ver["lord_states"] = dict(cur.execute(
        "SELECT target_resolution_state, COUNT(*) FROM gochara_resonance_map"
        " WHERE chart_id=%s AND target_type='lord' GROUP BY 1 ORDER BY 1", (CHART_ID,)).fetchall())
    ver["afflicted_qualifier_rows"] = cur.execute(
        "SELECT COUNT(*) FROM gochara_resonance_map WHERE chart_id=%s"
        " AND target_type='lord' AND target_qualifier='afflicted'", (CHART_ID,)).fetchone()[0]
    ver["writer_rows_inserted"] = result.rows_inserted
    ver["writer_notes"] = json.loads(result.notes)

    print(json.dumps(ver, indent=2, sort_keys=True, default=str))
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
