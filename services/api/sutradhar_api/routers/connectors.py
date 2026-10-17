"""
sutradhar_api/routers/connectors.py
Simulated agency connector status. All connectors are labelled simulated=true.
No real network connections are made.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from sutradhar_api.auth import require_action
from sutradhar_api.connectors import (
    SimulatedCCTNS,
    SimulatedMahaCrimeOS,
    SimulatedMahaCyber,
    SimulatedNATGRID,
)
from sutradhar_api.models import UserInfo

router = APIRouter(tags=["connectors"])

_CONNECTORS = [
    SimulatedCCTNS(),
    SimulatedMahaCrimeOS(),
    SimulatedMahaCyber(),
    SimulatedNATGRID(),
]


@router.get("/connectors/status")
def get_connectors_status(
    user: UserInfo = Depends(require_action("CONNECTORS_STATUS")),
):
    return [c.status() for c in _CONNECTORS]
