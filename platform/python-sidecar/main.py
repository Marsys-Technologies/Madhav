from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from routers import ephemeris, events, eclipses, retrogrades, sade_sati, jaimini, v7_additions, dasha_chain
from routers import panchang as panchang_router
from routers import muhurat as muhurat_router
from routers import brahmagyan_almanac as almanac_router
from rag.routers.rag_retrieve import router as rag_retrieve_router
from rag.routers.rag_router import router as rag_router_router
from rag.routers.rag_synthesize import router as rag_synthesize_router

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
app.include_router(eclipses.router, prefix="/eclipses", dependencies=[Depends(verify_api_key)])
app.include_router(retrogrades.router, prefix="/retrogrades", dependencies=[Depends(verify_api_key)])
app.include_router(sade_sati.router, prefix="/sade_sati", dependencies=[Depends(verify_api_key)])
app.include_router(jaimini.router, prefix="/jaimini_drishti", dependencies=[Depends(verify_api_key)])
app.include_router(v7_additions.router, prefix="/v7_additions", dependencies=[Depends(verify_api_key)])
app.include_router(dasha_chain.router, dependencies=[Depends(verify_api_key)])
# transit_search router removed — pipeline.transit_search torn down (teardown arc)
app.include_router(rag_retrieve_router, prefix="/rag", dependencies=[Depends(verify_api_key)])
app.include_router(rag_router_router, prefix="/rag", dependencies=[Depends(verify_api_key)])
app.include_router(rag_synthesize_router, prefix="/rag", dependencies=[Depends(verify_api_key)])

# Phase 4C-3 — Panchang compute endpoints (engine-direct; 4C-2 will add cache layer)
app.include_router(panchang_router.router, prefix="/api/compute", dependencies=[Depends(verify_api_key)])

# Phase 4C-6 — Muhurat Finder endpoint
app.include_router(muhurat_router.router, prefix="/api/compute", dependencies=[Depends(verify_api_key)])

# Brahmagyan L0 Wave-2 — Daily Almanac (BG-0-8) [BRAHMA-BG-0-8]
app.include_router(almanac_router.router, prefix="/api/brahmagyan/almanac", dependencies=[Depends(verify_api_key)])


@app.get("/health")
def health():
    return {"status": "ok"}
