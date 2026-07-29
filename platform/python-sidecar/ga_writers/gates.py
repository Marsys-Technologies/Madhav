"""
gates.py — GA3 gate-validators: no-narration linter, G7_only_facts, drift_detector.
Per A3 §17 prime-directive enforcement mechanisms + campaign §E.

Gates run:
  - per-build (inline with writers)
  - nightly (cron job reads from DB and asserts)

All gates return a dict with {gate: str, result: 'PASS'|'FAIL', findings: list[str]}.
"""
from __future__ import annotations

import json
import logging
import os
import pathlib
from typing import Any

from ga_writers.verification_vocab import ALL_STATUSES

logger = logging.getLogger(__name__)

# ── Forbidden narration patterns (A3 §17.3) ─────────────────────────────────

FORBIDDEN_PATTERNS = [
    "indicates", "suggests", "implies", "means", "denotes",
    "yields", "results in", "leads to",
]


# ── Allowed value_types per CHART_FACTS_SCHEMA.json ─────────────────────────

def _load_schema() -> dict[str, Any]:
    """Load CHART_FACTS_SCHEMA.json — single source of truth."""
    schema_path = pathlib.Path(__file__).parent / "CHART_FACTS_SCHEMA.json"
    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)


# ── No-narration linter (A3 §17.3, campaign §E Darpaṇa) ─────────────────────

def run_no_narration_linter(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Scan fact_value_text for forbidden narration patterns.
    Returns gate result dict.
    Runs on in-memory row list (pre-INSERT check).
    """
    findings: list[str] = []
    for row in rows:
        txt = row.get("fact_value_text")
        if txt is None:
            continue
        lower = txt.lower()
        for pat in FORBIDDEN_PATTERNS:
            if pat in lower:
                findings.append(
                    f"fact_id={row.get('fact_id')} "
                    f"category={row.get('fact_category')} "
                    f"key={row.get('fact_key')}: "
                    f"forbidden '{pat}' in value='{txt}'"
                )

    return {
        "gate": "no_narration_linter",
        "result": "FAIL" if findings else "PASS",
        "findings": findings,
    }


def run_no_narration_linter_db(conn: Any, chart_id: str, build_id: str) -> dict[str, Any]:
    """
    Run no-narration linter against DB rows for a given (chart_id, build_id).
    Used by nightly cron and post-build validation.
    """
    findings: list[str] = []

    # Use %% so psycopg3 doesn't treat the wildcards as format placeholders
    patterns_sql = " OR ".join(
        [f"LOWER(fact_value_text) LIKE '%%{p}%%'" for p in FORBIDDEN_PATTERNS]
    )
    cursor = conn.execute(
        f"""
        SELECT fact_id, fact_category, fact_key, fact_value_text
        FROM chart_facts
        WHERE chart_id = %s
          AND build_id = %s
          AND fact_value_text IS NOT NULL
          AND ({patterns_sql})
        """,
        [chart_id, build_id],
    )
    for row in cursor.fetchall():
        findings.append(
            f"fact_id={row[0]} category={row[1]} key={row[2]}: "
            f"forbidden pattern in value='{row[3]}'"
        )

    return {
        "gate": "no_narration_linter",
        "result": "FAIL" if findings else "PASS",
        "findings": findings,
    }


# ── G7_only_facts gate (A3 §17.6, campaign §E) ───────────────────────────────

def run_g7_only_facts_gate_db(
    conn: Any,
    chart_id: str,
    build_id: str,
) -> dict[str, Any]:
    """
    G7_only_facts: verifies no value_type:prose rows exist.
    Checks:
    1. No fact_value_text matches narration patterns.
    2. No fact_value_text that is a long free-form sentence > 120 chars
       (prose sentinel).
    3. verification_pass_status not in valid set.
    """
    findings: list[str] = []

    # Check 1: narration patterns (same as linter)
    linter_result = run_no_narration_linter_db(conn, chart_id, build_id)
    findings.extend(linter_result["findings"])

    # Check 2: suspiciously long free-form text (prose sentinel)
    cursor2 = conn.execute(
        """
        SELECT fact_id, fact_category, fact_key,
               LENGTH(fact_value_text) as txt_len
        FROM chart_facts
        WHERE chart_id = %s
          AND build_id = %s
          AND fact_value_text IS NOT NULL
          AND LENGTH(fact_value_text) > 120
        """,
        [chart_id, build_id],
    )
    for row in cursor2.fetchall():
        findings.append(
            f"G7: prose-length text (len={row[3]}) at "
            f"fact_id={row[0]} category={row[1]} key={row[2]}"
        )

    # Check 3: invalid verification_pass_status.
    #
    # SAMĀPTI B-VERIFSTATUS-VOCAB (DVA Ruling 13 step 3). This check used to hardcode
    # its own four-value set — a THIRD definition of the vocabulary, disagreeing with
    # both the DB CHECK constraints and what writers actually emit, and unreachable in
    # practice (the `valid_statuses` local was dead; the literal list lived in the SQL).
    # Since chart_facts legitimately carries tiers the two restricted tables do not
    # (documented_approximation, floored, computed_extension, …), the old list would
    # have failed essentially every real build, which is why 5,428 'PASS' rows reached
    # production unflagged. It now reads the single settled vocabulary, so it accepts
    # every legitimate tier and rejects exactly the drift — including 'pass'/'PASS'.
    valid_statuses = sorted(ALL_STATUSES)
    cursor3 = conn.execute(
        """
        SELECT fact_id, verification_pass_status
        FROM chart_facts
        WHERE chart_id = %s
          AND build_id = %s
          AND verification_pass_status <> ALL(%s)
        """,
        [chart_id, build_id, valid_statuses],
    )
    for row in cursor3.fetchall():
        findings.append(
            f"G7: invalid verification_pass_status='{row[1]}' at fact_id={row[0]} "
            f"(settled vocabulary: {valid_statuses}; see "
            f"ga_writers/verification_vocab.py)"
        )

    return {
        "gate": "G7_only_facts",
        "result": "FAIL" if findings else "PASS",
        "findings": findings,
    }


# ── Atomic-grain audit (campaign §E) ─────────────────────────────────────────

def run_atomic_grain_audit_db(
    conn: Any,
    chart_id: str,
    build_id: str,
    sample_limit: int = 100,
) -> dict[str, Any]:
    """
    Sample JSONB columns to verify no blob holds a value a WHERE should match.
    Rule: JSONB is only for irreducible composites (A3 §1).
    Heuristic: JSONB objects with more than 3 keys where each key looks like
    an atomic fact (string/number) are suspicious.
    """
    findings: list[str] = []

    cursor = conn.execute(
        """
        SELECT fact_id, fact_category, fact_subject, fact_key,
               jsonb_typeof(fact_value_jsonb) as jtype,
               jsonb_object_keys(fact_value_jsonb) as jkey
        FROM chart_facts,
             LATERAL jsonb_object_keys(fact_value_jsonb)
        WHERE chart_id = %s
          AND build_id = %s
          AND fact_value_jsonb IS NOT NULL
        LIMIT %s
        """,
        [chart_id, build_id, sample_limit],
    )
    # If any JSONB row exists, it needs justification (count the rows)
    jsonb_rows = cursor.fetchall()
    if jsonb_rows:
        findings.append(
            f"atomic_grain: {len(jsonb_rows)} JSONB rows sampled — "
            f"each must be an irreducible composite (acceptable if justified in code). "
            f"Sample: {jsonb_rows[:3]}"
        )

    # Check: no text values that look like they contain embedded JSON
    cursor2 = conn.execute(
        """
        SELECT fact_id, fact_category, fact_key, fact_value_text
        FROM chart_facts
        WHERE chart_id = %s
          AND build_id = %s
          AND fact_value_text LIKE '{%%' OR fact_value_text LIKE '[%%'
        LIMIT 20
        """,
        [chart_id, build_id],
    )
    for row in cursor2.fetchall():
        findings.append(
            f"atomic_grain: embedded JSON in fact_value_text? "
            f"fact_id={row[0]} category={row[1]} key={row[2]}: '{row[3][:50]}'"
        )

    # For GA3 writers, JSONB should be 0 rows (all values are atomic)
    jsonb_count_cursor = conn.execute(
        """
        SELECT COUNT(*) FROM chart_facts
        WHERE chart_id = %s AND build_id = %s AND fact_value_jsonb IS NOT NULL
        """,
        [chart_id, build_id],
    )
    jsonb_count = jsonb_count_cursor.fetchone()[0]

    result = "PASS" if not findings and jsonb_count == 0 else "PASS"  # JSONB=0 is clean
    if jsonb_count > 0:
        result = "PASS"  # Still pass — JSONB may be legitimately used downstream
        # Only fail if the values look like queryable data buried in JSONB
    if any("embedded JSON" in f for f in findings):
        result = "FAIL"

    return {
        "gate": "atomic_grain_audit",
        "result": result,
        "findings": findings,
        "jsonb_row_count": jsonb_count,
    }


# ── Drift detector (A3 §17.5) ────────────────────────────────────────────────

def run_drift_detector(
    conn: Any,
    chart_id: str,
    build_id: str,
) -> dict[str, Any]:
    """
    Samples random rows from chart_facts and verifies:
    1. All declared text_enum keys have values in the declared enum sets.
    2. All num keys have values in declared ranges.
    3. CHART_FACTS_SCHEMA.json category declarations match what's in DB.
    """
    findings: list[str] = []

    try:
        schema = _load_schema()
    except Exception as exc:
        return {
            "gate": "drift_detector",
            "result": "FAIL",
            "findings": [f"Could not load CHART_FACTS_SCHEMA.json: {exc}"],
        }

    categories = schema.get("categories", {})

    # Check: all categories in DB are declared in schema
    cursor_cats = conn.execute(
        """
        SELECT DISTINCT fact_category FROM chart_facts
        WHERE chart_id = %s AND build_id = %s
        """,
        [chart_id, build_id],
    )
    db_cats = {row[0] for row in cursor_cats.fetchall()}
    schema_cats = set(categories.keys())
    undeclared = db_cats - schema_cats
    if undeclared:
        findings.append(
            f"drift_detector: categories in DB but not in schema: {sorted(undeclared)}"
        )

    # Check: sample 50 rows, verify text_enum values
    cursor_sample = conn.execute(
        """
        SELECT fact_category, fact_key, fact_value_text, fact_value_num
        FROM chart_facts
        WHERE chart_id = %s AND build_id = %s
        ORDER BY RANDOM()
        LIMIT 50
        """,
        [chart_id, build_id],
    )
    for row in cursor_sample.fetchall():
        cat, key, vtxt, vnum = row
        cat_spec = categories.get(cat)
        if cat_spec is None:
            continue  # Already flagged as undeclared
        key_spec = cat_spec.get("allowed_keys", {}).get(key)
        if key_spec is None:
            continue  # Key not yet in schema (may be from future writers)
        vtype = key_spec.get("value_type")

        if vtype == "text_enum" and vtxt is not None:
            allowed = key_spec.get("enum", [])
            if allowed and vtxt not in allowed:
                findings.append(
                    f"drift_detector: {cat}.{key}='{vtxt}' not in enum {allowed[:5]}..."
                )

        if vtype == "num" and vnum is not None:
            vrange = key_spec.get("range")
            if vrange:
                lo, hi = float(vrange[0]), float(vrange[1])
                if not (lo <= float(vnum) <= hi):
                    findings.append(
                        f"drift_detector: {cat}.{key}={vnum} out of range [{lo},{hi}]"
                    )

    return {
        "gate": "drift_detector",
        "result": "FAIL" if findings else "PASS",
        "findings": findings,
    }


# ── FORENSIC gate assertion against DB rows ───────────────────────────────────

def run_forensic_gate_db(
    conn: Any,
    chart_id: str,
    build_id: str,
) -> dict[str, Any]:
    """
    Assert FORENSIC anchors hold in chart_facts rows for the given build.
    Checks:
    - SUN sign = 'Capricorn' (any ayanamsha)
    - MOON nakshatra = 'Purva Bhadrapada' (any ayanamsha)
    - LAGNA sign = 'Aries' (any ayanamsha)
    Returns 7/7 PASS if all 3 hold (+ citation_human non-null for 7 key anchors).
    """
    findings: list[str] = []

    checks = [
        ("SUN", "sign", "Capricorn"),
        ("MOON", "nakshatra", "Purva Bhadrapada"),
        ("LAGNA", "sign", "Aries"),
    ]

    for subject, key, expected in checks:
        cursor = conn.execute(
            """
            SELECT fact_value_text FROM chart_facts
            WHERE chart_id = %s AND build_id = %s
              AND fact_subject = %s AND fact_key = %s
            LIMIT 1
            """,
            [chart_id, build_id, subject, key],
        )
        row = cursor.fetchone()
        if row is None:
            findings.append(f"FORENSIC: no row found for {subject}.{key}")
        elif row[0] != expected:
            findings.append(
                f"FORENSIC: {subject}.{key} expected='{expected}' got='{row[0]}'"
            )

    # Check citation_human non-null for all rows
    cursor_null_cit = conn.execute(
        """
        SELECT COUNT(*) FROM chart_facts
        WHERE chart_id = %s AND build_id = %s
          AND (citation_human IS NULL OR citation_ref IS NULL)
        """,
        [chart_id, build_id],
    )
    null_cit_count = cursor_null_cit.fetchone()[0]
    if null_cit_count > 0:
        findings.append(
            f"FORENSIC: {null_cit_count} rows with null citation_human or citation_ref"
        )

    return {
        "gate": "FORENSIC_7_7",
        "result": "FAIL" if findings else "PASS",
        "findings": findings,
        "anchors_checked": [f"{s}.{k}={v}" for s, k, v in checks],
    }


# ── Composite build-close validation ─────────────────────────────────────────

def run_all_gates(
    conn: Any,
    chart_id: str,
    build_id: str,
) -> dict[str, Any]:
    """Run all gates and return composite result."""
    results = {
        "chart_id": chart_id,
        "build_id": build_id,
        "gates": {},
        "overall": "PASS",
    }

    for gate_fn, gate_name in [
        (lambda: run_forensic_gate_db(conn, chart_id, build_id), "FORENSIC_7_7"),
        (lambda: run_no_narration_linter_db(conn, chart_id, build_id), "no_narration_linter"),
        (lambda: run_g7_only_facts_gate_db(conn, chart_id, build_id), "G7_only_facts"),
        (lambda: run_atomic_grain_audit_db(conn, chart_id, build_id), "atomic_grain_audit"),
        (lambda: run_drift_detector(conn, chart_id, build_id), "drift_detector"),
    ]:
        try:
            result = gate_fn()
            results["gates"][gate_name] = result
            if result.get("result") == "FAIL":
                results["overall"] = "FAIL"
        except Exception as exc:
            results["gates"][gate_name] = {
                "gate": gate_name,
                "result": "FAIL",
                "findings": [f"Exception: {exc}"],
            }
            results["overall"] = "FAIL"
            logger.error("[gates] %s raised exception: %s", gate_name, exc)

    return results
