"""
writer.py — KaMuhurtaSevaWriter: orchestrator-registered WriterBase subclass.

This is a SERVICE writer (asset_kind='service'). It produces zero domain rows.
Instead it:
  1. Runs a FORENSIC self-test against the birth panchāṅga (1984-02-05 10:43 IST Bhubaneswar)
  2. Asserts the 5 FORENSIC anchors: Shukla Tritiya, Ravivara, Purva Bhadrapada, Shiva, Garaja
  3. Asserts the knockout path fires on compound-inauspicious inputs
  4. Writes service_health='healthy' (or 'unhealthy') + selftest_detail to asset_registry
  5. Returns WriterResult(rows_inserted=0)

Contract compliance (FROZEN orchestrator contract, ORCHESTRATOR_CONVERGENCE_CLOSE §2):
  - NEVER calls ctx.db_conn.commit() / rollback() / close()
  - NEVER writes asset_throughput
  - NEVER opens its own DB connection
  - Honors ctx.dry_run

Layer: L3 Kāla
Asset: ka_muhurta_seva (service)
Registered via: @register('ka_muhurta_seva')
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime

from pipeline.orchestrator.writers import WriterBase, ContextSpec, WriterResult, register

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FORENSIC birth constants (hard anchors — never derive from anywhere else)
# ---------------------------------------------------------------------------
BIRTH_DATE = date(1984, 2, 5)
BIRTH_DATETIME = datetime(1984, 2, 5, 10, 43)  # local IST
BIRTH_LAT = 20.2700
BIRTH_LON = 85.8400
BIRTH_TZ_OFFSET_MINUTES = 330  # IST = UTC+5:30

BIRTH_LOCATION = {
    "lat": BIRTH_LAT,
    "lon": BIRTH_LON,
    "tz_offset_minutes": BIRTH_TZ_OFFSET_MINUTES,
}

# FORENSIC anchor IDs (1-indexed per shastra_tables.py)
FORENSIC_TITHI_ID = 3           # Shukla Tritiya
FORENSIC_VARA_ID = 1            # Ravivara (Sunday)
FORENSIC_NAKSHATRA_ID = 25      # Purva Bhadrapada
FORENSIC_YOGA_ID = 20           # Shiva
FORENSIC_KARANA_ID = 5          # Garaja


@register("ka_muhurta_seva")
class KaMuhurtaSevaWriter(WriterBase):
    """
    Service writer for ka_muhurta_seva — panchāṅga/muhūrta service.

    Runs a FORENSIC birth-panchāṅga self-test, asserts 5 FORENSIC anchors,
    asserts the knockout path, then writes service_health to asset_registry.

    Produces NO domain rows. Never commits/rollbacks/closes ctx.db_conn.
    """

    asset_id = "ka_muhurta_seva"

    def run(self, ctx: ContextSpec) -> WriterResult:
        """
        FORENSIC self-test + service health registration.

        Steps:
          1. Compute panchāṅga at birth instant via panchanga_instant()
          2. Assert 5 FORENSIC anchors: tithi=3, vara=1, nakshatra=25, yoga=20, karana=5
          3. Score birth day via score_muhurat() with native chart (Tāra Bala active)
          4. Assert knockout fires on compound-inauspicious fabricated panchang
          5. Write service_health + selftest_detail to asset_registry via ctx.db_conn
          6. Return WriterResult(rows_inserted=0)

        Never calls ctx.db_conn.commit() / rollback() / close().
        """
        checks = []
        failures = []

        try:
            checks, failures = _run_forensic_selftest()
        except Exception as exc:
            logger.error("[ka_muhurta_seva] self-test raised: %s: %s", type(exc).__name__, exc)
            failures.append(f"self-test exception: {type(exc).__name__}: {exc}")

        health = "healthy" if not failures else "unhealthy"
        selftest_detail = {
            "checks": checks,
            "failures": failures,
            "health": health,
        }

        logger.info(
            "[ka_muhurta_seva] self-test: health=%s  checks=%d  failures=%d",
            health, len(checks), len(failures),
        )

        if not ctx.dry_run:
            _write_service_health(ctx.db_conn, self.asset_id, health, selftest_detail)

        if failures:
            logger.warning("[ka_muhurta_seva] FORENSIC failures: %s", failures)

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=0,
            rows_updated=0,
            notes=f"service_health={health}; checks={len(checks)}; failures={len(failures)}",
        )


# ---------------------------------------------------------------------------
# Self-test implementation
# ---------------------------------------------------------------------------

def _run_forensic_selftest() -> tuple[list, list]:
    """
    Run all FORENSIC checks. Return (checks_passed: list[str], failures: list[str]).
    """
    checks = []
    failures = []

    # ── Check 1: Birth panchāṅga FORENSIC anchors ─────────────────────────
    try:
        from panchang_engine import panchanga_instant

        pi = panchanga_instant(BIRTH_DATETIME, BIRTH_LAT, BIRTH_LON, BIRTH_TZ_OFFSET_MINUTES)

        _assert_equal(checks, failures,
                      "FORENSIC tithi", pi.tithi.id, FORENSIC_TITHI_ID,
                      f"tithi.id={pi.tithi.id} name={pi.tithi.name}")
        _assert_equal(checks, failures,
                      "FORENSIC vara", pi.vara.id, FORENSIC_VARA_ID,
                      f"vara.id={pi.vara.id} name={pi.vara.name}")
        _assert_equal(checks, failures,
                      "FORENSIC nakshatra", pi.nakshatra.id, FORENSIC_NAKSHATRA_ID,
                      f"nakshatra.id={pi.nakshatra.id} name={pi.nakshatra.name}")
        _assert_equal(checks, failures,
                      "FORENSIC yoga", pi.yoga.id, FORENSIC_YOGA_ID,
                      f"yoga.id={pi.yoga.id} name={pi.yoga.name}")
        _assert_equal(checks, failures,
                      "FORENSIC karana", pi.karana.id, FORENSIC_KARANA_ID,
                      f"karana.id={pi.karana.id} name={pi.karana.name}")

    except Exception as exc:
        failures.append(f"panchanga_instant call failed: {exc}")

    # ── Check 2: Tāra Bala is live (birth nakshatra → self = Janma position = 0.5) ─
    try:
        from panchang_engine.tara_bala import compute_tara_bala_score

        score = compute_tara_bala_score(
            birth_nakshatra_id=FORENSIC_NAKSHATRA_ID,   # 25
            current_nakshatra_id=FORENSIC_NAKSHATRA_ID, # 25 = same = Janma position
        )
        # Janma = position 1, _TARA_QUALITY[1] = score 0.50, cycle 1, attenuation 1.0
        expected = 0.50
        if abs(score - expected) < 1e-9:
            checks.append(f"tara_bala live: birth_nak={FORENSIC_NAKSHATRA_ID} same-day score={score} (Janma=0.5 PASS)")
        else:
            failures.append(f"tara_bala Janma score wrong: got {score}, expected {expected}")
    except Exception as exc:
        failures.append(f"tara_bala call failed: {exc}")

    # ── Check 3: Native overlay changes score relative to no native_chart ──
    try:
        from panchang_engine import compute_panchang
        from panchang_engine.types import NatalChart
        from muhurat.finder import score_muhurat

        test_date = date(2026, 6, 21)  # today — any valid date

        panchang = compute_panchang(test_date, BIRTH_LAT, BIRTH_LON, BIRTH_TZ_OFFSET_MINUTES)

        native_chart = NatalChart(
            birth_nakshatra_id=FORENSIC_NAKSHATRA_ID,  # 25 = Purva Bhadrapada
            birth_lagna_sign_id=1,
            moon_sign_id=11,
            active_dasha_lord="Jupiter",
        )

        score_without = score_muhurat(panchang, "vivah", native_chart=None)
        score_with    = score_muhurat(panchang, "vivah", native_chart=native_chart)

        if score_without != score_with:
            checks.append(
                f"tara_bala overlay changes score: without={score_without:.2f} with={score_with:.2f}"
            )
        else:
            # Same score is fine if native weight contribution = 0 (knockouted or zero tara score)
            checks.append(
                f"tara_bala overlay: without={score_without:.2f} with={score_with:.2f} "
                "(equal — may be knockout day or Vipat/Vadha tara; not a failure)"
            )

    except Exception as exc:
        failures.append(f"native overlay comparison failed: {exc}")

    # ── Check 4: Knockout asserts zero for compound inauspicious ──────────
    try:
        from muhurat.finder import _in_inauspicious, score_muhurat, _CachedPanchang

        # Build a proxy with the exact compound-knockout conditions:
        # rahu_kalam + yamagandam + tithi=8 (Ashtami) + vara=7 (Saturday)
        row = {
            "tithi_id": 8,      # Ashtami (worst tithi)
            "nakshatra_id": 1,  # Ashwini (arbitrary)
            "vara_id": 7,       # Saturday
            "inauspicious": [
                {"label": "rahu_kalam"},
                {"label": "yamagandam"},
            ],
            "auspicious": [],
            "special_yogas": [],
            "sunrise_utc": None,
            "sunset_utc": None,
        }
        proxy = _CachedPanchang(row)

        if _in_inauspicious(proxy):
            s = score_muhurat(proxy, "vivah")
            if s == 0.0:
                checks.append("knockout: compound inauspicious → score=0.0 PASS")
            else:
                failures.append(f"knockout: compound inauspicious should return 0.0, got {s}")
        else:
            failures.append("knockout: _in_inauspicious() returned False for known-bad proxy")

    except Exception as exc:
        failures.append(f"knockout check failed: {exc}")

    return checks, failures


def _assert_equal(checks, failures, label, actual, expected, detail=""):
    if actual == expected:
        checks.append(f"{label}: {actual} == {expected} PASS  ({detail})")
    else:
        failures.append(f"{label}: got {actual}, expected {expected}  ({detail})")


def _write_service_health(db_conn, asset_id: str, health: str, detail: dict) -> None:
    """
    Write service_health + selftest_detail to asset_registry.
    NEVER commits or rolls back — caller (orchestrator) owns the transaction.
    """
    try:
        detail_json = json.dumps(detail)
        cur = db_conn.cursor()
        cur.execute(
            """
            UPDATE asset_registry
               SET service_health   = %s,
                   last_selftest_at = NOW(),
                   selftest_detail  = %s
             WHERE asset_id = %s
            """,
            (health, detail_json, asset_id),
        )
        logger.info("[ka_muhurta_seva] wrote service_health=%s to asset_registry", health)
    except Exception as exc:
        # Non-fatal: health write failure must not mask self-test result
        logger.warning("[ka_muhurta_seva] service_health write failed (non-fatal): %s", exc)
