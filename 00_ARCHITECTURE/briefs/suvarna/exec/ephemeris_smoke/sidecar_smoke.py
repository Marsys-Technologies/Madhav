#!/usr/bin/env python3
"""Post-deploy smoke for the amjis-sidecar ephemeris backend (TI-ephemeris-fix-001).

READ-ONLY: every call below is a pure compute POST/GET (no DB write, no cache refresh,
no prashna cast). Excluded on purpose because they WRITE: POST /api/compute/panchanga/refresh
(panchanga_daily), POST /api/compute/prashna/cast (chart_facts-like rows). Excluded because
they need a real chart + build ids: POST /api/compute/yoga_formation_band (DB read).

Auth: the sidecar is publicly invokable at the Cloud Run layer (allUsers run.invoker) and
authenticated at the app layer by the `x-api-key` header == secret PYTHON_SIDECAR_API_KEY
(Secret Manager, version 1; main.py verify_api_key).  The key is read from the environment
or a file, NEVER from argv:

    export PYTHON_SIDECAR_API_KEY="$(gcloud secrets versions access latest \\
        --secret=PYTHON_SIDECAR_API_KEY --project=madhav-astrology)"      # needs secretAccessor
    python3 sidecar_smoke.py --base-url https://amjis-sidecar-938361928218.asia-south1.run.app
    # or: --key-file /path/with/the/key   (file contents only; mode 600)
    # a zero-traffic candidate works too: --base-url https://<tag>---amjis-sidecar-....run.app

Checks: HTTP 200 + shape for every affected endpoint, PLUS three value discriminators that
a Moshier fallback cannot pass.  Reference values were computed locally from the
SHA-pinned corpus (sepl_18 ca1393ce..., semo_18 1ca07bd6..., seas_18 a2cd8fc3...) with the
fixed code; the Moshier values differ by >= 1.8e-4 deg (Moon, 2026-06-15 / 1984-02-05), the
tolerances below are 2e-5 deg or tighter:

  * POST /api/pyhora/compute (native 1984-02-05 10:43 IST, lahiri): Moon 327.055045  (Moshier 327.055230)
  * POST /api/compute/ephemeris_at_t 2026-06-15T12:00Z: Moon 65.6203 (Moshier 65.62004) and
    service_context.ephemeris_backends_observed == ["swiss_ephemeris_file"]
  * POST /api/compute/panchanga 2026-06-15 Bhubaneswar: Moon 57.71916715 (tolerance 5e-6)

Exit code 0 only if every check passes.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

BASE_DEFAULT = "https://amjis-sidecar-938361928218.asia-south1.run.app"
LOC = {"lat": 20.27, "lon": 85.84, "tz_offset_minutes": 330}


def _key(args: argparse.Namespace) -> str:
    if args.key_file:
        with open(args.key_file, encoding="utf-8") as fh:
            return fh.read().strip()
    key = os.environ.get("PYTHON_SIDECAR_API_KEY", "").strip()
    if not key:
        sys.exit("PYTHON_SIDECAR_API_KEY is not set (and no --key-file); see the docstring")
    return key


def call(base: str, key: str, method: str, path: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers={"content-type": "application/json", "x-api-key": key})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as exc:
        return exc.code, {"_error": exc.read().decode("utf-8", "replace")[:300]}
    except urllib.error.URLError as exc:
        return 0, {"_error": str(exc.reason)}


def near(value, expected, tol):
    return isinstance(value, (int, float)) and abs(value - expected) <= tol


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=BASE_DEFAULT)
    ap.add_argument("--key-file", default=None)
    args = ap.parse_args()
    base, key = args.base_url.rstrip("/"), _key(args)
    results: list[tuple[str, bool, str]] = []

    def check(name, status, payload, predicate=None):
        ok = status == 200 and (predicate is None or bool(predicate(payload)))
        detail = f"HTTP {status}" if status != 200 else "HTTP 200"
        if status != 200:
            detail += f" {payload.get('_error', '')[:160]}"
        results.append((name, ok, detail))

    s, j = call(base, key, "GET", "/api/pyhora/smoke")
    check("GET  /api/pyhora/smoke (Capricorn / Purva Bhadrapada)", s, j, lambda p: p.get("status") == "pass")

    s, j = call(base, key, "POST", "/api/pyhora/compute", {
        "datetime_iso": "1984-02-05T10:43:00", "latitude_deg": 20.2735, "longitude_deg": 85.8334,
        "tz_offset_hours": 5.5})
    check("POST /api/pyhora/compute (native Moon 327.055045 +-2e-5)", s, j, lambda p: near(
        next(g for g in p["graha_sthana"] if g["name"] == "Moon")["longitude_deg"], 327.055045, 2e-5))

    s, j = call(base, key, "POST", "/api/compute/panchanga", {"date": "2026-06-15", **LOC})
    check("POST /api/compute/panchanga (Moon 57.71916715 +-5e-6)", s, j, lambda p: near(
        p["panchang"]["planets"]["moon"]["longitude_sidereal"], 57.71916715, 5e-6))

    s, j = call(base, key, "POST", "/api/compute/panchanga/range",
                {"date_from": "2026-06-15", "date_to": "2026-06-17", **LOC})
    check("POST /api/compute/panchanga/range (3 days)", s, j, lambda p: p.get("ok") and p.get("count") == 3)

    s, j = call(base, key, "GET", "/api/compute/panchanga_get?date=2026-06-15")
    check("GET  /api/compute/panchanga_get", s, j, lambda p: p.get("ok") and p.get("angas"))

    s, j = call(base, key, "POST", "/api/compute/muhurat", {
        "event": "vivah", "date_from": "2026-06-15", "date_to": "2026-06-20", "top_n": 3, **LOC})
    check("POST /api/compute/muhurat", s, j, lambda p: p.get("ok") and "windows" in p)

    s, j = call(base, key, "POST", "/api/compute/muhurta_score",
                {"datetime_utc": "2026-06-15T12:00:00Z", "event_class": "vivah"})
    check("POST /api/compute/muhurta_score", s, j, lambda p: isinstance(p.get("score"), (int, float)))

    s, j = call(base, key, "POST", "/api/compute/ephemeris_at_t", {"datetime_utc": "2026-06-15T12:00:00Z"})
    check("POST /api/compute/ephemeris_at_t (backend swiss_ephemeris_file; Moon 65.6203 +-5e-5)", s, j,
          lambda p: p["service_context"]["ephemeris_backends_observed"] == ["swiss_ephemeris_file"]
          and near(next(x for x in p["positions"] if x["planet"] == "Moon")["longitude"], 65.6203, 5e-5))

    s, j = call(base, key, "POST", "/api/brahmagyan/almanac/query", {
        "date_from": "2026-06-15", "date_to": "2026-06-15",
        "location": {"lat": 20.27, "lon": 85.84, "tz_name": "Asia/Kolkata"}})
    check("POST /api/brahmagyan/almanac/query", s, j, lambda p: p.get("ok") and p.get("count") == 1)

    s, j = call(base, key, "GET", "/api/brahmagyan/almanac/health")
    check("GET  /api/brahmagyan/almanac/health", s, j, lambda p: p.get("ok"))

    width = max(len(n) for n, _, _ in results)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name.ljust(width)}  {detail}")
    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
