"""
Standalone runner for ga_sensitive enrichment build.
Bypasses the orchestrator watchdog by using the writer's own connection.
Run from platform/python-sidecar with enrichment branch checked out.
"""
import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

DATABASE_URL = os.environ["DATABASE_URL"]

sys.path.insert(0, os.path.dirname(__file__))

from ga_writers.ga_sensitive_writer import build_ga_sensitive

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

logging.info("Starting standalone ga_sensitive build for chart %s", CHART_ID)
result = build_ga_sensitive(
    chart_id=CHART_ID,
    build_id=None,   # standalone: writer opens its own conn, fetches birth_params
    conn=None,       # standalone mode — writer commits its own transaction
)
logging.info("ga_sensitive standalone complete: %s", result)
