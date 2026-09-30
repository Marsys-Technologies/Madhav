#!/bin/sh
# Pravaha A2.5 — narrowed generation '4.1' CANDIDATE build for chart 482012f1.
#
# Native ruling (steward M20260930T135600-d63b, 2026-09-30): the '4.1' build is
# NARROWED to the scored horizon of the evaluation protocol and runs with the
# existing reviewed enumeration + candidate-build path as a Cloud Run job.
# Candidate rows only; nothing here flips or publishes a generation (the ledger
# refuses a published generation; step07/step08 are never invoked).
#
# Vehicle: Cloud Run job brahma-gochara-century-job (deploy.yml, image
# brahma-pipeline:$DEPLOY_SHA). Entrypoint override is NOT possible on a job
# execution (Jobs API ContainerOverride carries args/env only, and the pipeline
# image's ENTRYPOINT is `python -m pipeline.orchestrator.main`), so the chain
# lives in this committed, reviewable script and the job's container command is
# `/bin/sh <this file>`.
#
# Exit codes propagate per step: 7 = §12.9 stale-overlay refusal (STOP — do not
# force, report), 6 = published-generation refusal (the candidate-only guard),
# 5 = ADK-0020 dedupe refusal, 4 = production-tranche flag missing, 3 = usage.
set -eu

# Pinned by the ruling — deliberately NOT env-overridable.
CHART_ID="482012f1-710e-4a25-994a-93821f5871aa"
GENERATION="4.1"
BASELINE_GENERATION="3.0"
# Scored horizon, event_registry_v2_3: start 1998-01-01, end 2026-04-17
# inclusive — H = 10,334 days ⇒ end-EXCLUSIVE bound 2026-04-18T00:00:00Z.
HORIZON_START="1998-01-01T00:00:00+00:00"
HORIZON_END="2026-04-18T00:00:00+00:00"

EPHE_PATH="${SWE_EPHE_PATH:-/app/ephe}"
WORK="/tmp/century_4_1"
mkdir -p "$WORK"

SIDECAR_DIR="/app/platform/python-sidecar"
cd "$SIDECAR_DIR"

if [ "${PRODUCTION_TRANCHE_2_AUTHORIZED:-}" != "true" ]; then
  echo "REFUSED: PRODUCTION_TRANCHE_2_AUTHORIZED must be 'true' for the" >&2
  echo "governed production candidate build (common.py refuse_production," >&2
  echo "step 6 / tranche 2). Pass it via --update-env-vars at execute time." >&2
  exit 4
fi

echo "[century-4.1] chart=$CHART_ID generation=$GENERATION horizon=[$HORIZON_START,$HORIZON_END) ephe=$EPHE_PATH"

echo "[century-4.1] step 0/3: ephemeris verification (fail closed)"
EPHE_PATH_ENV="$EPHE_PATH" python - <<'PYEOF'
import hashlib
import os
import sys

EPHE = os.environ["EPHE_PATH_ENV"]

# sha256 pins from Dockerfile.pipeline (the image build verifies the same pins;
# re-verified here so a tampered or fallback layer fails closed before any solve).
PINS = {
    "sepl_18.se1": "ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66",
    "semo_18.se1": "1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7",
    "seas_18.se1": "a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2",
}
# Size-verified only at image build (no upstream pin); presence + floor here.
SIZE_FLOORS = {"sefstars.txt": 1024, "seleapsec.txt": 1024}

for name, want in PINS.items():
    path = os.path.join(EPHE, name)
    if not os.path.exists(path):
        print(f"[ephe] REFUSED: missing {path}", file=sys.stderr)
        sys.exit(1)
    got = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if got != want:
        print(f"[ephe] REFUSED: {name} sha256 {got} != pinned {want}", file=sys.stderr)
        sys.exit(1)
for name, floor in SIZE_FLOORS.items():
    path = os.path.join(EPHE, name)
    if not os.path.exists(path) or os.path.getsize(path) < floor:
        print(f"[ephe] REFUSED: {name} missing or below size floor", file=sys.stderr)
        sys.exit(1)

import swisseph as swe

swe.set_ephe_path(EPHE)
# Fixed instant (J2000) — the backend bit in the returned retflag is what is
# asserted (F-14 convention: never trust the requested flag).
_jd = swe.julday(2000, 1, 1, 12.0)
for body, label in ((swe.SUN, "Sun"), (swe.MOON, "Moon"), (swe.SATURN, "Saturn")):
    _xx, retflag = swe.calc_ut(_jd, body, swe.FLG_SWIEPH | swe.FLG_SPEED)
    if not (retflag & swe.FLG_SWIEPH) or (retflag & swe.FLG_MOSEPH):
        print(f"[ephe] REFUSED: {label} computed via fallback backend "
              f"(retflag={retflag}) — not the pinned .se1 set", file=sys.stderr)
        sys.exit(1)
print("[ephe] OK: 3 .se1 sha256 pins match, aux files present, SWIEPH backend confirmed")
PYEOF

echo "[century-4.1] step 1/3: enumerate episodes (all PERSISTED_BODIES)"
python scripts/kala_gochara_cutover/step06_enumerate_episodes.py \
  --chart-id "$CHART_ID" \
  --generation "$GENERATION" \
  --horizon-start "$HORIZON_START" \
  --horizon-end "$HORIZON_END" \
  --ephe-path "$EPHE_PATH" \
  --episodes-out "$WORK/episodes.json" \
  --coverage-out "$WORK/coverage.json"

echo "[century-4.1] step 2/3: candidate build (single transaction, publish_candidate)"
python scripts/kala_gochara_cutover/step06_candidate_build.py \
  --chart-id "$CHART_ID" \
  --generation "$GENERATION" \
  --horizon-start "$HORIZON_START" \
  --horizon-end "$HORIZON_END" \
  --episodes-json "$WORK/episodes.json" \
  --coverage-json "$WORK/coverage.json" \
  --delta-report "$WORK/delta_report.md"

echo "[century-4.1] step 3/3: windows projection for the candidate generation"
python scripts/kala_gochara_cutover/step06b_windows_projection.py \
  --chart-id "$CHART_ID" \
  --generation "$GENERATION" \
  --baseline-generation "$BASELINE_GENERATION" \
  --horizon-start "$HORIZON_START" \
  --horizon-end "$HORIZON_END" \
  --delta-report-out "$WORK/windows_delta_report.md"

echo "[century-4.1] post-run completeness check (episodes JSON vs persisted rows)"
python - "$WORK/episodes.json" <<'PYEOF'
import json
import os
import sys
from collections import Counter

import psycopg

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
GENERATION = "4.1"

episodes = json.load(open(sys.argv[1]))
by_body = Counter(e["body"] for e in episodes)
by_relation = Counter(e["relation"] for e in episodes)

with psycopg.connect(os.environ["DATABASE_URL"]) as conn, conn.cursor() as cur:
    cur.execute(
        "SELECT body, relation, count(*) FROM kala_gochara_contacts "
        "WHERE chart_id = %s AND generation = %s GROUP BY 1, 2",
        (CHART_ID, GENERATION),
    )
    rows = cur.fetchall()
    cur.execute(
        "SELECT status, row_counts FROM kala_gochara_publication "
        "WHERE chart_id = %s AND generation = %s",
        (CHART_ID, GENERATION),
    )
    manifest = cur.fetchone()
    cur.execute(
        "SELECT count(*) FROM kala_gochara_coverage "
        "WHERE chart_id = %s AND generation = %s",
        (CHART_ID, GENERATION),
    )
    n_coverage = cur.fetchone()[0]

db_total = sum(r[2] for r in rows)
db_by_body = Counter()
db_by_relation = Counter()
for body, relation, n in rows:
    db_by_body[body] += n
    db_by_relation[relation] += n

print(f"[completeness] episodes_json={len(episodes)} contacts_rows={db_total} "
      f"coverage_rows={n_coverage} manifest_status={manifest[0] if manifest else None} "
      f"manifest_row_counts={manifest[1] if manifest else None}")
if manifest is None or manifest[0] != "candidate":
    print(f"[completeness] REFUSAL: manifest status must be 'candidate', got "
          f"{manifest[0] if manifest else None} — candidate-only violated", file=sys.stderr)
    sys.exit(1)
for label, mine, db in (("body", by_body, db_by_body), ("relation", by_relation, db_by_relation)):
    keys = sorted(set(mine) | set(db))
    mismatches = [(k, mine.get(k, 0), db.get(k, 0)) for k in keys if mine.get(k, 0) != db.get(k, 0)]
    if mismatches:
        print(f"[completeness] {label} MISMATCH (json, db): {mismatches}", file=sys.stderr)
        sys.exit(1)
if db_total != len(episodes):
    print(f"[completeness] total mismatch: json={len(episodes)} db={db_total}", file=sys.stderr)
    sys.exit(1)
print("[completeness] OK: per-body and per-relation counts match; manifest is candidate (never published)")
PYEOF

echo "[century-4.1] DONE — candidate generation '4.1' built; artifacts under $WORK (ephemeral)"
