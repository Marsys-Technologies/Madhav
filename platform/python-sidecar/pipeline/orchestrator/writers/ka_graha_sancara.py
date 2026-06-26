"""
pipeline/orchestrator/writers/ka_graha_sancara.py
L3 Kāla K1 — ka_graha_sancara self-test writer.

This is a SERVICE-KIND asset.  The writer does NOT insert domain rows.
Its sole job is:
  1. Run the FORENSIC self-test (ephemeris for 1984-02-05 10:43 IST, native birth):
       - 9 grahas present, speeds non-null
       - natal Moon sign = Aquarius  (FORENSIC anchor, CLAUDE.md §B)
  2. Write service_health='healthy' + last_selftest_at=NOW() to asset_registry
     via ctx.db_conn (which the orchestrator will commit — we never commit).
  3. Return WriterResult(rows_inserted=0).

Conforms to FROZEN WriterBase contract (ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2):
  - uses ctx.db_conn exclusively (never commits, never closes it)
  - returns WriterResult with rows_inserted=0 (service produces NO domain rows)
  - honours ctx.dry_run
  - NEVER writes asset_throughput

Per CLAUDE.md §N.2: DO NOT modify this contract.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone, timedelta

from pipeline.orchestrator.writers import (
    ContextSpec,
    WriterBase,
    WriterResult,
    register,
)

logger = logging.getLogger(__name__)

# FORENSIC birth parameters (CLAUDE.md §B, FORENSIC 7/7 PASS)
# _BIRTH_LAT and _BIRTH_LON removed: never loaded (only stored); latent contamination trap.
# Coordinates are sourced from ctx.config['birth_params'] at runtime via the orchestrator.
_BIRTH_DT_ISO = "1984-02-05T10:43:00"
_IST = timezone(timedelta(hours=5, minutes=30))

# FORENSIC anchor: Moon must be in Aquarius (sidereal Lahiri)
_FORENSIC_MOON_SIGN = "Aquarius"


@register("ka_graha_sancara")
class KaGrahaSancaraWriter(WriterBase):
    """
    Self-test writer for the ka_graha_sancara ephemeris service.

    Asset kind: service (no domain rows emitted).
    Self-test: run get_ephemeris() for the native's birth instant;
               assert 9 grahas, speeds non-null, Moon=Aquarius.
    Writes:    service_health + last_selftest_at to asset_registry.
    """

    asset_id = "ka_graha_sancara"

    def run(self, ctx: ContextSpec) -> WriterResult:
        if ctx.dry_run:
            logger.info("[ka_graha_sancara] dry_run=True — skipping self-test")
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes="dry_run",
            )

        health = "unhealthy"
        detail: dict = {"checks": [], "errors": []}

        try:
            health, detail = self._run_selftest(ctx)
        except Exception as exc:
            logger.error("[ka_graha_sancara] self-test raised: %s", exc)
            detail["errors"].append(str(exc))
            health = "unhealthy"

        # Write service_health to asset_registry (orchestrator commits)
        self._write_health(ctx, health, detail)

        status = "success" if health == "healthy" else "error"
        notes = f"self-test: {health}; checks={len(detail.get('checks', []))}"
        logger.info("[ka_graha_sancara] %s", notes)

        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=0,
            notes=notes,
        )

    # ── Self-test implementation ──────────────────────────────────────────────

    def _run_selftest(self, ctx: ContextSpec) -> tuple[str, dict]:
        from services.ka_graha_sancara.engine import get_ephemeris, _EphemerisCache

        checks: list[dict] = []
        errors: list[str] = []

        birth_dt = datetime.fromisoformat(_BIRTH_DT_ISO).replace(tzinfo=_IST)

        # Use a shared cache to verify single-compute (I-9)
        cache = _EphemerisCache()

        # ── Check 1: ephemeris computes without error ──
        try:
            result = get_ephemeris(
                dt=birth_dt,
                ayanamsha="lahiri",
                db_conn=ctx.db_conn,
                _cache=cache,
            )
            checks.append({"check": "ephemeris_computes", "passed": True})
        except Exception as exc:
            checks.append({"check": "ephemeris_computes", "passed": False, "error": str(exc)})
            errors.append(f"ephemeris computation failed: {exc}")
            return "unhealthy", {"checks": checks, "errors": errors}

        # ── Check 2: 9 grahas present ──
        graha_names = list(result.grahas.keys())
        expected_9 = {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"}
        missing = expected_9 - set(graha_names)
        if missing:
            checks.append({"check": "9_grahas_present", "passed": False, "missing": sorted(missing)})
            errors.append(f"missing grahas: {sorted(missing)}")
        else:
            checks.append({"check": "9_grahas_present", "passed": True, "count": len(graha_names)})

        # ── Check 3: all speeds non-null and numeric ──
        speed_errors = []
        for name, gs in result.grahas.items():
            if gs.speed_dps is None:
                speed_errors.append(name)
        if speed_errors:
            checks.append({"check": "speeds_non_null", "passed": False, "null_speeds": speed_errors})
            errors.append(f"null speeds for: {speed_errors}")
        else:
            checks.append({"check": "speeds_non_null", "passed": True})

        # ── Check 4: FORENSIC Moon = Aquarius ──
        moon_sign = result.grahas.get("Moon", None)
        moon_sign_name = moon_sign.sign if moon_sign else "MISSING"
        forensic_ok = moon_sign_name == _FORENSIC_MOON_SIGN
        checks.append({
            "check": "forensic_moon_sign",
            "passed": forensic_ok,
            "expected": _FORENSIC_MOON_SIGN,
            "got": moon_sign_name,
        })
        if not forensic_ok:
            errors.append(
                f"FORENSIC FAIL: Moon sign expected={_FORENSIC_MOON_SIGN}, got={moon_sign_name}"
            )

        # ── Check 5: cache single-compute (I-9) — second call hits cache ──
        try:
            result2 = get_ephemeris(
                dt=birth_dt,
                ayanamsha="lahiri",
                db_conn=ctx.db_conn,
                _cache=cache,
            )
            cache_hit = cache.stats["hits"] >= 1
            checks.append({
                "check": "cache_single_compute",
                "passed": cache_hit,
                "cache_stats": cache.stats,
            })
            if not cache_hit:
                errors.append("cache hit not recorded on repeated query")
        except Exception as exc:
            checks.append({"check": "cache_single_compute", "passed": False, "error": str(exc)})
            errors.append(f"cache check failed: {exc}")

        health = "healthy" if not errors else "unhealthy"
        return health, {"checks": checks, "errors": errors}

    def _write_health(self, ctx: ContextSpec, health: str, detail: dict) -> None:
        """Update asset_registry.service_health for this asset (no commit — orchestrator owns)."""
        try:
            with ctx.db_conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE asset_registry
                       SET service_health    = %s,
                           last_selftest_at  = NOW(),
                           selftest_detail   = %s
                     WHERE asset_id = %s
                    """,
                    (health, json.dumps(detail), self.asset_id),
                )
        except Exception as exc:
            logger.error("[ka_graha_sancara] failed to write service_health: %s", exc)
