"""
sutradhar_api/main.py
FastAPI application entry point for the Sutradhar Backend API.
Member 4: Backend, Security, Audit.

All data is synthetic. All connectors are simulated.
No real person, agency or case is represented.
"""
from __future__ import annotations

import logging
import os

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from sutradhar_api import __version__
from sutradhar_api.auth import require_auth
from sutradhar_api.config import CORS_ORIGINS, DATASET_VERSION, DEMO_TAMPER
from sutradhar_api.models import UserInfo
from sutradhar_api.routers import audit, connectors, dossier, entities, federated, graph, kumbh, review
from sutradhar_api.store import get_store

# ─────────────────────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
log = logging.getLogger("sutradhar_api")

# ─────────────────────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Sutradhar API",
    version=__version__,
    description=(
        "Multi-agency financial intelligence and entity-resolution platform. "
        "**All data is entirely synthetic.** "
        "All connectors are simulated. "
        "No real person, agency or case is represented."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ─────────────────────────────────────────────────────────────
# CORS
# ─────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────────────────────
app.include_router(entities.router)
app.include_router(review.router)
app.include_router(graph.router)
app.include_router(dossier.router)
app.include_router(federated.router)
app.include_router(audit.router)
app.include_router(kumbh.router)
app.include_router(connectors.router)

# ─────────────────────────────────────────────────────────────
# Startup
# ─────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup() -> None:
    log.info("Sutradhar API v%s starting. DATASET_VERSION=%s DEMO_TAMPER=%s", __version__, DATASET_VERSION, DEMO_TAMPER)
    store = get_store()
    store.load()
    log.info("DataStore ready.")


# ─────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
def get_health():
    """API health check. Always returns simulated: true."""
    from sutradhar_api.store import get_store as _gs
    store = _gs()
    return {
        "status": "ok",
        "simulated": True,
        "dataset_version": DATASET_VERSION,
        "recompute_status": "idle",
        "entities_loaded": len(store.entities),
        "links_loaded": len(store.links),
        "communities_loaded": len(store.communities),
        "kumbh_events_loaded": len(store.kumbh_events),
    }


# ─────────────────────────────────────────────────────────────
# Me
# ─────────────────────────────────────────────────────────────
@app.get("/me", tags=["auth"])
def get_me(user: UserInfo = Depends(require_auth)):
    """Return current demo user info."""
    return user.model_dump()


# ─────────────────────────────────────────────────────────────
# Metrics
# ─────────────────────────────────────────────────────────────
@app.get("/metrics", tags=["system"])
def get_metrics(user: UserInfo = Depends(require_auth)):
    """Return evaluation metrics from artifacts/metrics.json."""
    store = get_store()
    return store.metrics or {"message": "Metrics not yet available. Run `make eval` first."}


# ─────────────────────────────────────────────────────────────
# Global 422 handler for cleaner error format
# ─────────────────────────────────────────────────────────────
@app.exception_handler(422)
async def validation_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "VALIDATION_ERROR", "message": str(exc)}},
    )
