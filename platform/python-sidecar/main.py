from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from routers import ephemeris, events, sade_sati, jaimini, v7_additions
from routers import panchang as panchang_router
from routers import pyhora as pyhora_router
from routers import prashna as prashna_router
from routers import brahmagyan_almanac as almanac_router
load_dotenv()

app = FastAPI(title="MARSYS-JIS Compute Sidecar", version="1.0.0")

# SIDECAR_ALLOWED_ORIGINS: comma-separated list of allowed origins.
# In production (Cloud Run service-to-service), CORS is not needed — set to
# the frontend Cloud Run URL. For local dev, http://localhost:3000 is sufficient.
_raw_origins = os.environ.get("SIDECAR_ALLOWED_ORIGINS", "http://localhost:3000")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)

API_KEY = os.environ.get("PYTHON_SIDECAR_API_KEY", "")


def verify_api_key(x_api_key: str = Header(default="")):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


app.include_router(ephemeris.router, prefix="/ephemeris", dependencies=[Depends(verify_api_key)])
app.include_router(events.router, prefix="/event_chart_states", dependencies=[Depends(verify_api_key)])
app.include_router(sade_sati.router, prefix="/sade_sati", dependencies=[Depends(verify_api_key)])
app.include_router(jaimini.router, prefix="/jaimini_drishti", dependencies=[Depends(verify_api_key)])
app.include_router(v7_additions.router, prefix="/v7_additions", dependencies=[Depends(verify_api_key)])

# Phase 4C-3 — Panchang compute endpoints (engine-direct; 4C-2 will add cache layer)
app.include_router(panchang_router.router, prefix="/api/compute", dependencies=[Depends(verify_api_key)])

# BRAHMA PH-4-4 — phala.muhurta electional finder (inverts Phala prediction engine)
from brahmagyan.phala.muhurta import router as phala_muhurta_router
app.include_router(phala_muhurta_router, prefix="/api/compute", dependencies=[Depends(verify_api_key)])

# BRAHMA L4 Phala — event anchors (PH-4-1) + composite outlook (PH-4-5)
from brahmagyan.phala.anchors import router as phala_anchors_router
from brahmagyan.phala.outlook import router as phala_outlook_router
app.include_router(phala_anchors_router, prefix="/api/compute", dependencies=[Depends(verify_api_key)])
app.include_router(phala_outlook_router, prefix="/api/compute", dependencies=[Depends(verify_api_key)])

# BRAHMA MI-5-2 — Mīmāṃsā L5 prediction ledger (log_prediction + record_outcome)
from brahmagyan.mimamsa.prediction_ledger import router as mimamsa_prediction_router
app.include_router(mimamsa_prediction_router, prefix="/api/brahma", dependencies=[Depends(verify_api_key)])

# BRAHMA MI-5-1 — Mīmāṃsā L5 LEL intake query (lel_query → /brahma/mimamsa/lel_query)
# Resolves Phase 4 audit CHECK 5: MCP tool mimamsa_lel_intake.ts forwards chart_id
# to POST /brahma/mimamsa/lel_query — this route was missing, causing a 404.
# Route: POST /brahma/mimamsa/lel_query (full path after prefix)
from brahmagyan.mimamsa.lel_intake import router as mimamsa_lel_router
if mimamsa_lel_router is not None:
    app.include_router(mimamsa_lel_router, prefix="/brahma/mimamsa", dependencies=[Depends(verify_api_key)])

# BRAHMA Stream G — PyHora natal computation (graha_sthana, vimshottari_dasha, special_lagnas)
app.include_router(pyhora_router.router, prefix="/api/pyhora", dependencies=[Depends(verify_api_key)])

# L1 Prashna — horary cast + judgment (namespace-isolated, never writes to native natal stream)
app.include_router(prashna_router.router, prefix="/api/compute/prashna", dependencies=[Depends(verify_api_key)])

# Brahmagyan L0 Wave-2 — Daily Almanac (BG-0-8) [BRAHMA-BG-0-8]
app.include_router(almanac_router.router, prefix="/api/brahmagyan/almanac", dependencies=[Depends(verify_api_key)])

# BRAHMA L0FR Stream B — Ephemeris query endpoints (planet_position, transit, aspects, retrograde_periods,
#   all_bodies_range, native_lifetime_meta); data source: ephemeris_daily (1900-2150, 9 bodies).
from brahmagyan.ephemeris_routes import router as ephemeris_brahmagyan_router
app.include_router(ephemeris_brahmagyan_router, prefix="/brahmagyan/ephemeris", dependencies=[Depends(verify_api_key)])

# BRAHMA L0 Stream D — Sūtravali pattern extraction capabilities (SQL-only, ZERO LLM)
from routers import sutravali as sutravali_router
app.include_router(sutravali_router.router, prefix="/api/brahma", dependencies=[Depends(verify_api_key)])

# L3 Kāla — Transit search (ka_gochara, aspect + conjunction live compute)
# Retrieval call_transit_search capability calls /api/compute/transit_search
from routers import transit_search as transit_search_router
app.include_router(transit_search_router.router, prefix="/api/compute", dependencies=[Depends(verify_api_key)])

# W2 dark-set wiring — ka_graha_sancara (GT-50): live graha positions at an
# arbitrary UTC instant. Retrieval call_ephemeris_at_t capability calls
# /api/compute/ephemeris_at_t. See routers/ephemeris.py's compute_router
# (separate from `ephemeris.router`, which stays mounted at /ephemeris above
# for the birth-params natal-chart endpoint).
app.include_router(ephemeris.compute_router, prefix="/api/compute", dependencies=[Depends(verify_api_key)])

# W2 dark-set wiring — ka_muhurta_seva (DARK_SET_WIRING_PLAN_v1_0 §W2 scope):
# raw per-datetime muhurta score (tithi/nakshatra/vara/yoga-based), distinct
# from the already-served ph_muhurta electional finder (muhurta_finder /
# kala_muhurta_get). Retrieval call_muhurta_score capability calls
# /api/compute/muhurta_score.
from routers import muhurta_score as muhurta_score_router
app.include_router(muhurta_score_router.router, prefix="/api/compute", dependencies=[Depends(verify_api_key)])

# BRAHMA MI-5-3 — Mīmāṃsā L5 outcome scoring + calibration query + acceptance gate
# Routes: POST /api/compute/mimamsa/record_outcome
#         POST /api/compute/mimamsa/query_calibration
#         GET  /api/compute/mimamsa/acceptance_gate/{chart_id}
#         GET  /api/compute/mimamsa/acceptance_gate
from brahmagyan.mimamsa.outcome import router as mimamsa_outcome_router
app.include_router(mimamsa_outcome_router, prefix="/api/compute", dependencies=[Depends(verify_api_key)])

# L3 Kāla Taraṅga — stateless temporal-convolution service (D-3 Lane T-2)
from routers import taranga as taranga_router
app.include_router(taranga_router.router, prefix="/api/compute/taranga", dependencies=[Depends(verify_api_key)])

# D-4b permission-bridge lane (wave/D-4b/permission-bridge) — read-only curve-servable
# wrap of the EXISTING gochara_intensity.permission.compute_permission()'s per-system
# decomposition (12 PERMISSION generators), for the a3_scoring_harness B-1 bakeoff bridge.
# Does not modify compute_permission's internal computation. Route: POST
# /api/compute/permission_curve.
from routers import permission_curve as permission_curve_router
app.include_router(permission_curve_router.router, prefix="/api/compute", dependencies=[Depends(verify_api_key)])

# BRAHMA L2 Bodha — holistic bundle (bo_2-8; filename uses hyphen, import via importlib)
# Route: POST /api/compute/brahma/holistic_bundle
import importlib as _importlib
_bodha_bundle = _importlib.import_module("brahmagyan.bodha.bo_2-8")
app.include_router(_bodha_bundle.router, prefix="/api/compute/brahma", dependencies=[Depends(verify_api_key)])


@app.get("/health")
def health():
    return {"status": "ok"}
