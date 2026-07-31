"""
pipeline.orchestrator.writers.ga_nakshatra — L1 per-chart parallel nakshatra chart.

Heavy WriterBase: plan_substeps (5 ayanamshas + cross-ayanamsha) + run_substep.
Writes 14 fact_categories into chart_facts.
bg_nakshatra is AUTHORITY for static attrs (JOIN, cite, never restate).
"""
from __future__ import annotations
import hashlib
import time
import json
import logging
from datetime import datetime, timezone
from typing import Any

from pipeline.orchestrator.writers import WriterBase, WriterResult, SubStep, register, ContextSpec
from ga_writers._idempotency import replace_prior_chart_facts
from brahmagyan.verification_vocab import UNVERIFIED_DEFAULT, assert_legal
from ga_writers.ga_nakshatra_emitters import (
    emit_nakshatra_join, emit_kp_lords, emit_gandanta_flags,
    emit_dispositor_graph, emit_tara_bala, emit_statistics,
    PLANET_TO_SUBJECT,
)
from ga_writers.ga_nakshatra_compute import compute_cross_ayanamsha_agreement
from pyjhora_adapter.compute import compute_chart
from pyjhora_adapter.version import ENGINE_VERSION

logger = logging.getLogger(__name__)

CANONICAL_AYANAMSHAS: dict[str, str] = {
    "lahiri_chitrapaksha": "lahiri",
    "true_chitra":         "true_chitra",
    "krishnamurti":        "kp",
    "raman":               "raman",
    "surya_siddhanta_classical": "surya_siddhanta",
}

GA_NAKSHATRA_FACT_CATEGORIES = [
    "graha_nakshatra_join", "graha_pada_join", "nakshatra_lord_placement",
    "graha_kp_lords", "cusp_kp_lords", "graha_gandanta", "graha_degree_flags",
    "nakshatra_dispositor", "nakshatra_exchange", "nakshatra_conjunction",
    "nakshatra_cogravity", "graha_tara_bala", "nakshatra_statistics",
    "nakshatra_cross_ayanamsha",
]

NAK_LORD_STR_TO_BODY: dict[str, str] = {
    "Ketu": "Ketu", "Venus": "Venus", "Sun": "Sun", "Moon": "Moon",
    "Mars": "Mars", "Rahu": "Rahu", "Jupiter": "Jupiter",
    "Saturn": "Saturn", "Mercury": "Mercury",
}


def _fact_id(category: str, subject: str, key: str,
             chart_id: str, ayanamsha_id: str, build_id: str) -> str:
    raw = f"{category}|{subject}|{key}|{chart_id}|{ayanamsha_id}|{build_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


#: The (fact_category, fact_key) pairs whose VALUE is exactly the nakshatra/pada
#: attribution that `_nakshatra_pada_verdicts` re-derives. Only these rows can inherit
#: the detector's verdict; every other row this writer emits describes something the
#: detector does not check (a reference-table relay, a tara-bala step count, a
#: dispositor hop) and is therefore UNVERIFIED_DEFAULT, per §N.8.
_ATTRIBUTION_ROWS: dict[tuple[str, str], str] = {
    ("graha_nakshatra_join", "nakshatra_id_ref"): "nakshatra",
    ("graha_pada_join",      "pada_number_ref"):  "pada",
}

_NAK_ARC_DEG  = 360.0 / 27.0   # 13°20' — one nakshatra
_PADA_ARC_DEG = _NAK_ARC_DEG / 4.0  # 3°20' — one pada


def _derive_nakshatra_pada(longitude_deg: float) -> tuple[int, int]:
    """Independent 1-based (nakshatra, pada) from a sidereal longitude.

    SECOND PASS. The first pass is PyJHora's `drik.nakshatra_pada()`, reached via
    `pyjhora_adapter.positions._nakshatra_for_long` (grahas) and `drik.ascendant`
    (Lagna). This is a separate implementation of the same classical division —
    it does NOT call the library — so a boundary-convention difference, an ayanāṃśa
    mix-up, or a longitude/attribution desynchronisation inside chart_output shows up
    as a disagreement instead of passing silently.
    """
    lon = float(longitude_deg) % 360.0
    nak = int(lon // _NAK_ARC_DEG) + 1
    pada = int((lon % _NAK_ARC_DEG) // _PADA_ARC_DEG) + 1
    return nak, pada


def _nakshatra_pada_verdicts(chart_output: dict) -> dict[str, dict[str, str]]:
    """Run the second pass for every body and return {subject: {claim: status}}.

    `claim` is 'nakshatra' or 'pada'. Status is `two_pass_verified` when the engine's
    attribution and the independent re-derivation agree, `divergent_flagged` when they
    disagree (a halt-worthy inconsistency the row must carry, not hide), and
    `UNVERIFIED_DEFAULT` when the body carries no usable longitude so no second pass
    could run at all.
    """
    grahas = chart_output.get("grahas", []) or []
    asc = chart_output.get("ascendant", {}) or {}
    verdicts: dict[str, dict[str, str]] = {}

    for body_data in list(grahas) + [{"name": "Lagna", **asc}]:
        subject = PLANET_TO_SUBJECT.get(body_data.get("name", ""))
        if not subject:
            continue

        lon = body_data.get("longitude_deg", body_data.get("longitude"))
        engine_nak = body_data.get("nakshatra_id")
        engine_pada = body_data.get("pada")

        if lon is None:
            verdicts[subject] = {"nakshatra": UNVERIFIED_DEFAULT, "pada": UNVERIFIED_DEFAULT}
            continue

        derived_nak, derived_pada = _derive_nakshatra_pada(lon)
        per_claim: dict[str, str] = {}
        for claim, engine_value, derived_value in (
            ("nakshatra", engine_nak, derived_nak),
            ("pada", engine_pada, derived_pada),
        ):
            if engine_value is None:
                per_claim[claim] = UNVERIFIED_DEFAULT
                continue
            agrees = int(engine_value) == int(derived_value)
            per_claim[claim] = "two_pass_verified" if agrees else "divergent_flagged"
            if not agrees:
                logger.warning(
                    "[ga_nakshatra] second-pass DIVERGENCE for %s %s: engine=%s "
                    "independent=%s (longitude_deg=%s) — row stored as divergent_flagged",
                    subject, claim, engine_value, derived_value, lon,
                )
        verdicts[subject] = per_claim

    return verdicts


def _enrich_rows(
    rows: list[dict],
    eng_ver: str,
    computed_at: str,
    verdicts: dict[str, dict[str, str]] | None = None,
) -> list[dict]:
    """Add fact_id, citation_ref, citation_human, verification_pass_status, engine_version, computed_at.

    `verification_pass_status` is DETECTED, never asserted (CLAUDE.md §N.8). Until
    2026-07-30 this line wrote the literal `"PASS"` for every row with no verification
    logic anywhere behind it — 5,428 live chart_facts rows across three charts claiming
    a pass that never ran (SAMĀPTI A7-N8-AUDIT F-11, DVA Ruling 13). Rows whose value IS
    the nakshatra/pada attribution now inherit the real second-pass verdict from
    `_nakshatra_pada_verdicts`; every other row is `single` — honest, and excluded from
    grounding by the serve layer's settled predicate.
    """
    verdicts = verdicts or {}
    enriched = []
    for r in rows:
        chart_id    = r["chart_id"]
        ay          = r["ayanamsha_id"]
        build_id    = r["build_id"]
        category    = r["fact_category"]
        subject     = r["fact_subject"]
        key         = r["fact_key"]
        value_text  = r.get("fact_value_text")
        value_num   = r.get("fact_value_num")

        fid  = _fact_id(category, subject, key, chart_id, ay, build_id)
        cref = f"{category}.{subject}.{key}@chart={chart_id}:ay={ay}:eng={eng_ver}"
        # Simple human-readable citation
        if value_text is not None:
            chum = f"{subject} {key}: {value_text} [{category}]"
        elif value_num is not None:
            chum = f"{subject} {key}: {value_num} [{category}]"
        else:
            chum = f"{subject} {key} [{category}]"

        claim = _ATTRIBUTION_ROWS.get((category, key))
        status = (
            verdicts.get(subject, {}).get(claim, UNVERIFIED_DEFAULT)
            if claim else UNVERIFIED_DEFAULT
        )
        assert_legal(status)

        enriched.append({
            **r,
            "fact_value_jsonb":          None,
            "unit":                      None,
            "fact_id":                   fid,
            "citation_ref":              cref,
            "citation_human":            chum,
            "verification_pass_status":  status,
            "engine_version":            eng_ver,
            "computed_at":               computed_at,
        })
    return enriched


def _fetch_bg_nakshatra(conn: Any) -> tuple[dict[int, dict], dict[tuple, dict]]:
    """Fetch reference_nakshatra and reference_nakshatra_pada for JOIN."""
    import psycopg.rows as _rows
    with conn.cursor(row_factory=_rows.dict_row) as cur:
        cur.execute("""
            SELECT nakshatra_id, name_en, vimshottari_lord, presiding_deity,
                   gana, nadi, yoni_en, yoni_sex, varna, tatva, guna, pakshi,
                   shakti, motivation, symbol
            FROM reference_nakshatra
            ORDER BY nakshatra_id
        """)
        nak_rows = {r["nakshatra_id"]: dict(r) for r in cur.fetchall()}

        cur.execute("""
            SELECT nakshatra_id, pada_number, pada_akshara, pada_navamsa_sign, pada_lord
            FROM reference_nakshatra_pada
            ORDER BY nakshatra_id, pada_number
        """)
        pada_rows = {(r["nakshatra_id"], r["pada_number"]): dict(r) for r in cur.fetchall()}

    return nak_rows, pada_rows


def _check_bg_nakshatra_present(conn: Any) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM reference_nakshatra")
        row = cur.fetchone()
        count = row['count'] if isinstance(row, dict) else row[0]
        return count >= 27


def _build_nak_lord_map(grahas_plus_lagna: list[dict], nak_rows: dict) -> dict[str, str]:
    """Build {body_name: nakshatra_lord_body_name} for dispositor graph."""
    result = {}
    for body_data in grahas_plus_lagna:
        bname = body_data.get("name", "")
        if bname not in PLANET_TO_SUBJECT:
            continue
        nak_id = body_data.get("nakshatra_id")
        nak_ref = nak_rows.get(nak_id, {})
        lord_str = nak_ref.get("vimshottari_lord", "")
        lord_body = NAK_LORD_STR_TO_BODY.get(lord_str)
        if lord_body:
            result[bname] = lord_body
    return result


def _forensic_gate(chart_output: dict, ayanamsha_id: str) -> None:
    """FORENSIC: Moon must be in Purva Bhadrapada for native chart."""
    grahas = chart_output.get("grahas", [])
    moon = next((g for g in grahas if g.get("name") == "Moon"), None)
    if moon is None:
        raise RuntimeError(f"FORENSIC FAIL: Moon not found in chart_output (ay={ayanamsha_id})")
    nak_name = moon.get("nakshatra", "")
    nak_id   = moon.get("nakshatra_id")
    if nak_name != "Purva Bhadrapada" or nak_id != 25:
        raise RuntimeError(
            f"FORENSIC FAIL: Moon nakshatra expected 'Purva Bhadrapada' (id=25), "
            f"got '{nak_name}' (id={nak_id}) (ay={ayanamsha_id})"
        )


def _run_ayanamsha_pass(
    ctx: ContextSpec, canonical_id: str, adapter_id: str,
    nak_rows: dict, pada_rows: dict,
    chart_id: str, birth_params: dict,
) -> WriterResult:
    t0 = time.time()
    chart_output = compute_chart(inputs=birth_params, ayanamsha_id=adapter_id)

    # FORENSIC gate — native chart only (chart_id matches canonical native)
    NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
    if chart_id == NATIVE_CHART_ID:
        _forensic_gate(chart_output, canonical_id)

    grahas = chart_output.get("grahas", [])
    asc    = chart_output.get("ascendant", {})
    body_nak_lord = _build_nak_lord_map(grahas + [{"name": "Lagna", **asc}], nak_rows)

    build_id = ctx.build_id
    computed_at = datetime.now(timezone.utc).isoformat()

    all_rows: list[dict] = []
    all_rows += emit_nakshatra_join(chart_id, canonical_id, build_id, chart_output, nak_rows, pada_rows)
    all_rows += emit_kp_lords(chart_id, canonical_id, build_id, chart_output)
    all_rows += emit_gandanta_flags(chart_id, canonical_id, build_id, chart_output)
    all_rows += emit_dispositor_graph(chart_id, canonical_id, build_id, chart_output, body_nak_lord)
    all_rows += emit_tara_bala(chart_id, canonical_id, build_id, chart_output)
    all_rows += emit_statistics(chart_id, canonical_id, build_id, chart_output, nak_rows)

    # §N.8 real detector: independent second derivation of every body's nakshatra/pada
    # from its sidereal longitude, run BEFORE enrichment so attribution rows can inherit
    # a verdict that could genuinely have come back `divergent_flagged`.
    verdicts = _nakshatra_pada_verdicts(chart_output)
    all_rows = _enrich_rows(all_rows, ENGINE_VERSION, computed_at, verdicts)

    if ctx.dry_run:
        return WriterResult(
            asset_id="ga_nakshatra", rows_inserted=len(all_rows),
            duration_seconds=time.time() - t0,
            notes=f"DRY RUN ayanamsha={canonical_id}: {len(all_rows)} rows",
        )

    replace_prior_chart_facts(ctx.db_conn, all_rows)
    for r in all_rows:
        ctx.db_conn.execute(
            """
            INSERT INTO chart_facts
              (fact_id, chart_id, ayanamsha_id, build_id,
               fact_category, fact_subject, fact_key,
               fact_value_text, fact_value_num, fact_value_jsonb,
               unit, citation_ref, citation_human,
               source_calculation, verification_pass_status,
               engine_version, computed_at)
            VALUES
              (%(fact_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s,
               %(fact_category)s, %(fact_subject)s, %(fact_key)s,
               %(fact_value_text)s, %(fact_value_num)s, %(fact_value_jsonb)s,
               %(unit)s, %(citation_ref)s, %(citation_human)s,
               %(source_calculation)s, %(verification_pass_status)s,
               %(engine_version)s, %(computed_at)s)
            ON CONFLICT (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id)
            WHERE formula_id IS NULL
            DO UPDATE SET
              fact_id                  = EXCLUDED.fact_id,
              fact_value_text          = EXCLUDED.fact_value_text,
              fact_value_num           = EXCLUDED.fact_value_num,
              citation_ref             = EXCLUDED.citation_ref,
              citation_human           = EXCLUDED.citation_human,
              engine_version           = EXCLUDED.engine_version,
              computed_at              = EXCLUDED.computed_at
            """,
            r,
        )

    logger.info("ga_nakshatra %s: %d rows inserted", canonical_id, len(all_rows))
    return WriterResult(
        asset_id="ga_nakshatra", rows_inserted=len(all_rows),
        duration_seconds=time.time() - t0,
        notes=f"ayanamsha={canonical_id}: {len(all_rows)} rows",
    )


@register('ga_nakshatra')
class NakshatraWriter(WriterBase):
    asset_id = 'ga_nakshatra'
    has_substeps = True

    def plan_substeps(self, ctx: ContextSpec) -> list[SubStep]:
        return [
            SubStep(key=f"ayanamsha:{ay}", label=f"Nakshatra pass: {ay}")
            for ay in CANONICAL_AYANAMSHAS
        ] + [SubStep(key="cross_ayanamsha", label="Cross-ayanamsha consistency")]

    def run_substep(self, ctx: ContextSpec, step: SubStep) -> WriterResult:
        t0 = time.time()

        if not _check_bg_nakshatra_present(ctx.db_conn):
            raise RuntimeError(
                "HALT: reference_nakshatra has <27 rows — bg_nakshatra must be built first."
            )

        nak_rows, pada_rows = _fetch_bg_nakshatra(ctx.db_conn)
        chart_id    = ctx.config["chart_id"]
        birth_params = ctx.config.get("birth_params")

        if step.key.startswith("ayanamsha:"):
            canonical_id = step.key[len("ayanamsha:"):]
            adapter_id   = CANONICAL_AYANAMSHAS[canonical_id]
            return _run_ayanamsha_pass(
                ctx, canonical_id, adapter_id,
                nak_rows, pada_rows, chart_id, birth_params,
            )

        if step.key == "cross_ayanamsha":
            rows: list[dict] = []
            build_id    = ctx.build_id
            computed_at = datetime.now(timezone.utc).isoformat()

            import psycopg.rows as _rows
            with ctx.db_conn.cursor(row_factory=_rows.dict_row) as cur:
                cur.execute("""
                    SELECT fact_subject, fact_value_num
                    FROM chart_facts
                    WHERE chart_id = %s
                      AND fact_category = 'graha_nakshatra_join'
                      AND fact_key = 'nakshatra_id_ref'
                """, (chart_id,))
                results = cur.fetchall()

            body_naks: dict[str, list[float]] = {}
            for r in results:
                subj, val_num = r["fact_subject"], r["fact_value_num"]
                if val_num is not None:
                    body_naks.setdefault(subj, []).append(float(val_num))

            for body, nak_ids in body_naks.items():
                unique = set(nak_ids)
                # NAR-GA fix (P2 :289): agree_cnt previously collapsed to a
                # literal 0 the instant ANY of the 5 ayanamshas disagreed — so
                # 4/5 agreement narrated as "0 of the 5 sidereal ayanamshas"
                # via registry_bridge.ts's readCrossAyanamshaFamily, a false
                # report of zero agreement when substantial agreement existed.
                # compute_cross_ayanamsha_agreement returns the size of the
                # largest agreeing subset (the mode count), honest for both
                # the unanimous case and every partial-agreement case.
                agree_cnt, total_ay = compute_cross_ayanamsha_agreement(nak_ids)
                rows.append({
                    "chart_id": chart_id, "ayanamsha_id": "INVARIANT",
                    "build_id": build_id,
                    "fact_category": "nakshatra_cross_ayanamsha",
                    "fact_subject": body,
                    "fact_key": "nak_5ay_consistency",
                    "fact_value_text": f"{agree_cnt}/{total_ay}",
                    "fact_value_num": None,
                    "source_calculation": "ga_nakshatra:cross_ayanamsha",
                })
                if len(unique) == 1:
                    rows.append({
                        "chart_id": chart_id, "ayanamsha_id": "INVARIANT",
                        "build_id": build_id,
                        "fact_category": "nakshatra_cross_ayanamsha",
                        "fact_subject": body,
                        "fact_key": "stable_nakshatra_id",
                        "fact_value_num": list(unique)[0],
                        "fact_value_text": None,
                        "source_calculation": "ga_nakshatra:cross_ayanamsha",
                    })

            # No verdicts: the cross-ayanamsha substep reads back already-stored facts
            # rather than a chart_output, so no second derivation is available here.
            # Cross-ayanamsha AGREEMENT is not verification either — a nakshatra
            # legitimately differs between ayanāṃśas, so agreement cannot fail in a way
            # that means "wrong". These rows are honestly `single` (§N.8).
            rows = _enrich_rows(rows, ENGINE_VERSION, computed_at)

            if not ctx.dry_run and rows:
                replace_prior_chart_facts(ctx.db_conn, rows)
                for r in rows:
                    ctx.db_conn.execute(
                        """
                        INSERT INTO chart_facts
                          (fact_id, chart_id, ayanamsha_id, build_id,
                           fact_category, fact_subject, fact_key,
                           fact_value_text, fact_value_num, fact_value_jsonb,
                           unit, citation_ref, citation_human,
                           source_calculation, verification_pass_status,
                           engine_version, computed_at)
                        VALUES
                          (%(fact_id)s, %(chart_id)s, %(ayanamsha_id)s, %(build_id)s,
                           %(fact_category)s, %(fact_subject)s, %(fact_key)s,
                           %(fact_value_text)s, %(fact_value_num)s, %(fact_value_jsonb)s,
                           %(unit)s, %(citation_ref)s, %(citation_human)s,
                           %(source_calculation)s, %(verification_pass_status)s,
                           %(engine_version)s, %(computed_at)s)
                        ON CONFLICT (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key, build_id)
                        WHERE formula_id IS NULL
                        DO UPDATE SET
                          fact_id        = EXCLUDED.fact_id,
                          fact_value_text = EXCLUDED.fact_value_text,
                          fact_value_num  = EXCLUDED.fact_value_num,
                          citation_ref    = EXCLUDED.citation_ref,
                          citation_human  = EXCLUDED.citation_human,
                          engine_version  = EXCLUDED.engine_version,
                          computed_at     = EXCLUDED.computed_at
                        """,
                        r,
                    )

            return WriterResult(
                asset_id="ga_nakshatra", rows_inserted=len(rows),
                duration_seconds=time.time() - t0,
                notes=f"cross_ayanamsha: {len(rows)} rows",
            )

        raise ValueError(f"Unknown substep key: {step.key}")
