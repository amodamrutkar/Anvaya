"""
sutradhar_api/connectors/simulated.py
Mock connectors for agency data feeds:
- SimulatedCCTNS
- SimulatedMahaCrimeOS
- SimulatedMahaCyber
- SimulatedNATGRID

ALL DATA IS SYNTHETIC. ALL CONNECTORS ARE SIMULATED.
No live external network requests are ever made.
"""

from __future__ import annotations

from typing import Any


class BaseSimulatedConnector:
    connector_id: str
    agency: str
    description: str

    def __init__(self) -> None:
        self.simulated = True
        self._online = True

    def status(self) -> dict[str, Any]:
        return {
            "connector_id": self.connector_id,
            "agency": self.agency,
            "description": self.description,
            "simulated": True,
            "status": "ONLINE" if self._online else "OFFLINE",
        }


class SimulatedCCTNS(BaseSimulatedConnector):
    connector_id = "SimulatedCCTNS"
    agency = "CENTRAL_AGENCY"
    description = "Simulated CCTNS connector (Crime and Criminal Tracking Network & Systems)"

    def fetch_fir(self, fir_number: str) -> dict[str, Any]:
        return {
            "connector": self.connector_id,
            "simulated": True,
            "fir_number": fir_number,
            "status": "RECORD_FOUND",
            "agency": self.agency,
            "disclaimer": "Simulated data only. Not a live CCTNS connection.",
        }

    def query_identifier(self, id_type: str, val: str) -> dict[str, Any]:
        return {
            "connector": self.connector_id,
            "simulated": True,
            "query": {"type": id_type, "val": val},
            "status": "QUERY_COMPLETED",
            "agency": self.agency,
        }


class SimulatedMahaCrimeOS(BaseSimulatedConnector):
    connector_id = "SimulatedMahaCrimeOS"
    agency = "STATE_POLICE"
    description = "Simulated MahaCrimeOS connector (Maharashtra Police Case Management System)"

    def fetch_record(self, record_id: str) -> dict[str, Any]:
        return {
            "connector": self.connector_id,
            "simulated": True,
            "record_id": record_id,
            "status": "RECORD_FOUND",
            "agency": self.agency,
            "disclaimer": "Simulated data only. Not a live police system.",
        }


class SimulatedMahaCyber(BaseSimulatedConnector):
    connector_id = "SimulatedMahaCyber"
    agency = "MAHA_CYBER"
    description = "Simulated Maharashtra Cyber connector (Cyber Crime Incident & Mule Tracking)"

    def fetch_complaint(self, complaint_id: str) -> dict[str, Any]:
        return {
            "connector": self.connector_id,
            "simulated": True,
            "complaint_id": complaint_id,
            "status": "COMPLAINT_FOUND",
            "agency": self.agency,
        }

    def fetch_account(self, account_number: str) -> dict[str, Any]:
        return {
            "connector": self.connector_id,
            "simulated": True,
            "account_number": account_number,
            "status": "ACCOUNT_FOUND",
            "agency": self.agency,
        }


class SimulatedNATGRID(BaseSimulatedConnector):
    connector_id = "SimulatedNATGRID"
    agency = "CENTRAL_AGENCY"
    description = "Simulated NATGRID federated query connector"

    def query_identifier(self, id_type: str, val: str) -> dict[str, Any]:
        return {
            "connector": self.connector_id,
            "simulated": True,
            "query": {"type": id_type, "val": val},
            "status": "QUERY_COMPLETED",
            "agency": self.agency,
        }
