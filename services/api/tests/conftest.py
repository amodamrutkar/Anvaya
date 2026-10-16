"""
tests/conftest.py
Shared pytest fixtures for sutradhar_api tests.
Uses httpx.AsyncClient with ASGITransport — no real network calls.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from sutradhar_api.main import app
from sutradhar_api.store import get_store

ANALYST_HEADERS = {"X-Demo-User": "analyst1"}
INSPECTOR_HEADERS = {"X-Demo-User": "inspector1"}
OFFICER_HEADERS = {"X-Demo-User": "officer1"}
AUDITOR_HEADERS = {"X-Demo-User": "auditor1"}
LIAISON_HEADERS = {"X-Demo-User": "liaison1"}
NO_HEADERS: dict = {}


@pytest.fixture(scope="session", autouse=True)
def preload_store():
    """Load the data store once for the test session."""
    store = get_store()
    store.load()
    return store


@pytest.fixture
async def client():
    """Async test client."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
